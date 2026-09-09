"""Render and validate the Wikimedia measurement-scope binding decision (Mission 1.77).

Two records: the decision (hand-written, authoritative) and the diagnostic (measured from
the deployment by `report_reliability_resource_binding.py`). This gate holds them to each
other and to the code, and refuses the shapes section 23 lists:

    A RESOURCE IS READ FROM LINEAGE OR IT IS NOT A RESOURCE. Every resolved row's scope
    resource equals the one distinct resource its RawRecords carry; an ambiguous or absent
    lineage builds no scope; the rule module and the diagnostic name no source and no
    resource, and import nothing that reads current collector or registry configuration.

    THE SCOPE IS EXACT. The resolver's signature is unchanged, the scope has five parts,
    and every binding's assessment scope equals the row's scope on all five -- so a closest
    match, a wildcard, a proposition fallback, a swapped value between the two Wikimedia
    kinds, or a Wikimedia value on a Stack Exchange row is refused.

    NOTHING WAS WRITTEN. Counters before and after are equal, no reliability was written to
    an Evidence row, no assessment, no independence group, no score, no revision.

    THE STALE LIMITATION IS REPORTED, NOT EDITED. The canonical revision-1 limitation is
    recorded as stale with the assessments that postdate it, the action is STOP, and the
    predecessors that carried the false lineage sentence carry a forward pointer and still
    carry the sentence.

    THE RUNNERS RESOLVE LATE. Both Opportunity runners call the lineage rule and neither
    derives a reliability status from the stored column or hard-codes the eligibility a
    citation is written with.

    uv run python infrastructure/scripts/render_wikimedia_scope_binding.py
    uv run python infrastructure/scripts/render_wikimedia_scope_binding.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import ast
import inspect
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"
SCRIPTS = ROOT / "infrastructure" / "scripts"
for package in ("evidence-reliability", "contracts"):
    sys.path.insert(0, str(ROOT / "packages" / package / "python"))

DECISION = DATA / "wikimedia-measurement-scope-binding-v1.json"
DIAGNOSTIC = DATA / "reliability-resource-binding-diagnostic-v1.json"
RENDERED_DECISION = DATA / "wikimedia-measurement-scope-binding-v1.md"
RENDERED_DIAGNOSTIC = DATA / "reliability-resource-binding-diagnostic-v1.md"

RULE_MODULE = (
    ROOT
    / "packages"
    / "evidence-reliability"
    / "python"
    / "sros_evidence_reliability"
    / "lineage.py"
)
MODEL_MODULE = RULE_MODULE.with_name("model.py")
DIAGNOSTIC_SCRIPT = SCRIPTS / "report_reliability_resource_binding.py"
RUNNERS = (SCRIPTS / "run_opportunity_preparation.py", SCRIPTS / "run_opportunity_synthesis.py")

SELECTED_CLASS = DATA / "selected-quantity-class-v1.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v4.json"
V2_DECISION = DATA / "v2-vantage-class-decision-v1.json"
PREDECESSORS = (
    DATA / "evidence-completion-candidate-moves-v1.json",
    DATA / "opportunity-evidence-breadth-audit-v1.json",
    DATA / "opportunity-synthesis-run-v1.1.json",
)

OUTCOMES = (
    "WIKIMEDIA_MEASUREMENT_SCOPE_BINDING_REPAIRED",
    "HISTORICAL_MEASUREMENT_RESOURCE_NOT_DETERMINISTICALLY_RECOVERABLE",
    "RESOURCE_BINDING_ARCHITECTURE_DECISION_REQUIRED",
    "RELIABILITY_APPLICABILITY_ROOT_CAUSE_REVISED",
)
SCOPE_FIELDS = ("source_id", "resource_id", "record_kind_id", "claim_type", "proposition_kind")
BANNER = ("UNCALIBRATED", "DIAGNOSTIC_ONLY", "NOT_AN_OPPORTUNITY_SCORE")
EXPLICIT = "EXPLICIT_PERSISTED_RESOURCE"
INSUFFICIENT_BASES = (
    "only one likely resource",
    "ReliabilityAssessment names the resource",
    "collector name",
    "URL shape",
    "record kind",
    "all records are",
    "old report",
    "no alternative resource",
)
# Modules whose import would make the rule read something that can change after acquisition.
MUTABLE_CONFIG_MODULES = ("sros_acquisition", "sros_source")
NETWORK_MODULES = ("httpx", "requests", "urllib", "aiohttp", "socket")
FALSE_LINEAGE_SENTENCE = "absent from the whole acquisition lineage"


class ValidationError(Exception):
    pass


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _literals(tree: ast.AST) -> set[str]:
    """Every string literal outside docstrings, so the paragraph explaining a rule cannot break it."""
    doc_nodes = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
            and node.body
            and isinstance(node.body[0], ast.Expr)
        ):
            value = node.body[0].value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                doc_nodes.add(id(value))
    out = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in doc_nodes
        ):
            out.add(node.value)
    return out


def _compared_literals(tree: ast.AST) -> set[str]:
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for side in (node.left, *node.comparators):
                if isinstance(side, ast.Constant) and isinstance(side.value, str):
                    out.add(side.value)
    return out


def _imports(tree: ast.AST) -> set[str]:
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module.split(".")[0])
    return out


# ------------------------------------------------------------------------- checks


def _check_the_rule_names_no_source(diagnostic: dict) -> None:
    inventory = diagnostic["lineage_audit"]["raw_record_resources"]
    names = {e["source_id"] for e in inventory} | {e["resource_id"] for e in inventory}
    names |= {a["scope"]["source_id"] for a in diagnostic["current_assessments"]}
    names |= {a["scope"]["resource_id"] for a in diagnostic["current_assessments"]}
    for path in (RULE_MODULE, DIAGNOSTIC_SCRIPT):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        named = sorted(_literals(tree) & names)
        if named:
            raise ValidationError(f"{path.name} names {named}; the rule must not know a source")
        touched = _imports(tree) & set(MUTABLE_CONFIG_MODULES)
        if touched:
            raise ValidationError(
                f"{path.name} imports {sorted(touched)}, which reads current mutable configuration"
            )
        net = _imports(tree) & set(NETWORK_MODULES)
        if net:
            raise ValidationError(
                f"{path.name} imports {sorted(net)}; nothing here may reach a network"
            )
    for path in RUNNERS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        branched = sorted(_compared_literals(tree) & names)
        if branched:
            raise ValidationError(
                f"{path.name} compares against {branched}; a source-specific branch is the "
                "hard-coded exception section 10 forbids"
            )
    construction = diagnostic["scope_construction"]
    if construction["reads_current_collector_or_registry_configuration"]:
        raise ValidationError("the diagnostic reads current collector or registry configuration")
    if construction["source_specific_branches"] != 0:
        raise ValidationError("the diagnostic records source-specific branches")
    if construction["resource_bases_admitted"] != [EXPLICIT]:
        raise ValidationError(
            f"the diagnostic admits resource bases {construction['resource_bases_admitted']}; "
            f"only {EXPLICIT} may build a scope"
        )


def _check_the_scope_is_exact() -> None:
    """Asserted over the resolver's SOURCE, so an edit is seen on the next run rather than
    whenever the interpreter happens to re-import the package."""
    tree = ast.parse(MODEL_MODULE.read_text(encoding="utf-8"))
    resolver = next(
        (
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name == "resolve_reliability"
        ),
        None,
    )
    if resolver is None:
        raise ValidationError("resolve_reliability is not defined in the model module")
    params = tuple(a.arg for a in resolver.args.kwonlyargs)
    positional = tuple(a.arg for a in resolver.args.args + resolver.args.posonlyargs)
    if (
        params != ("scope", "candidates", "supplied")
        or positional
        or resolver.args.vararg
        or resolver.args.kwarg
    ):
        raise ValidationError(
            f"resolve_reliability takes {positional + params}; the resolver's signature was changed"
        )
    scope = next(
        (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "ReliabilityScope"),
        None,
    )
    if scope is None:
        raise ValidationError("ReliabilityScope is not defined in the model module")
    fields = tuple(
        n.target.id
        for n in scope.body
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
    )
    if fields != SCOPE_FIELDS:
        raise ValidationError(f"ReliabilityScope carries {fields}; the five-part scope was changed")
    from sros_evidence_reliability import ReliabilityScope, resolve_reliability

    live = tuple(inspect.signature(resolve_reliability).parameters)
    if live != params or tuple(ReliabilityScope.__dataclass_fields__) != SCOPE_FIELDS:
        raise ValidationError("the imported resolver disagrees with its source")


def _check_every_resolution_is_exact(diagnostic: dict) -> None:
    assessments = {a["id"]: a for a in diagnostic["current_assessments"]}
    for row in diagnostic["rows"]:
        lineage = row["lineage"]
        scope = row["scope"]
        resolution = row["resolution_via_lineage"]
        eid = row["evidence_id"][:8]
        if lineage["distinct_resource_count"] != len(lineage["resources"]):
            raise ValidationError(f"{eid}: the distinct resource count disagrees with the list")
        if lineage["distinct_resource_count"] != 1 and (
            scope is not None or row["resource_basis"] == EXPLICIT
        ):
            raise ValidationError(
                f"{eid}: {lineage['distinct_resource_count']} lineage resources and a scope "
                "was still built; ambiguity was silently resolved"
            )
        if scope is None:
            if resolution["outcome"] == "RESOLVED":
                raise ValidationError(f"{eid}: resolved with no scope")
            continue
        if row["resource_basis"] != EXPLICIT:
            raise ValidationError(f"{eid}: a scope built on basis {row['resource_basis']!r}")
        if not scope["resource_id"] or scope["resource_id"] in ("*", "%"):
            raise ValidationError(f"{eid}: a wildcard or empty resource in the scope")
        if scope["resource_id"] != lineage["resources"][0]:
            raise ValidationError(
                f"{eid}: scope resource {scope['resource_id']!r} is not the lineage resource "
                f"{lineage['resources'][0]!r}; the resource came from somewhere else"
            )
        if (
            scope["source_id"] != row["source_id"]
            or scope["proposition_kind"] != row["proposition_kind"]
        ):
            raise ValidationError(f"{eid}: the scope does not describe the row")
        if resolution["outcome"] != "RESOLVED":
            if resolution["reliability"] is not None or resolution["assessment_id"]:
                raise ValidationError(f"{eid}: a value with no resolution")
            continue
        assessment = assessments.get(resolution["assessment_id"])
        if assessment is None:
            raise ValidationError(f"{eid}: bound to an assessment that is not current")
        if resolution["assessment_scope"] != scope:
            raise ValidationError(
                f"{eid}: bound to an assessment whose scope differs from the row's on "
                f"{sorted(k for k in SCOPE_FIELDS if resolution['assessment_scope'].get(k) != scope[k])}"
            )
        if assessment["scope"] != scope:
            raise ValidationError(f"{eid}: the inventory scope for the bound assessment differs")
        if resolution["reliability"] != assessment["reliability"]:
            raise ValidationError(
                f"{eid}: reliability {resolution['reliability']} is not the bound assessment's "
                f"{assessment['reliability']}"
            )
        if not row["scorable_via_lineage"]:
            raise ValidationError(f"{eid}: resolved and still reported non-scorable")


def _per_scope(diagnostic: dict) -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = {}
    for row in diagnostic["rows"]:
        bucket = out.setdefault(
            (row["source_id"], row["proposition_kind"]),
            {
                "rows": 0,
                "on_opportunity": 0,
                "before": 0,
                "after": 0,
                "reliability": set(),
                "ids": set(),
            },
        )
        bucket["rows"] += 1
        bucket["on_opportunity"] += int(row["on_opportunity"])
        bucket["before"] += int(row["resolution_via_claim_facts"]["outcome"] == "RESOLVED")
        bucket["after"] += int(row["resolution_via_lineage"]["outcome"] == "RESOLVED")
        if row["resolution_via_lineage"]["outcome"] == "RESOLVED":
            bucket["reliability"].add(row["resolution_via_lineage"]["reliability"])
            bucket["ids"].add(row["resolution_via_lineage"]["assessment_id"])
    return out


def _check_the_controls_match_the_diagnostic(decision: dict, diagnostic: dict) -> None:
    scopes = _per_scope(diagnostic)
    controls = decision["controls"]

    def scope_of(control: dict) -> dict:
        key = (control["scope"]["source_id"], control["scope"]["proposition_kind"])
        if key not in scopes:
            raise ValidationError(f"no diagnostic rows for {key}")
        return scopes[key]

    for name, prefix in (
        ("detailed_wikimedia", "DETAILED"),
        ("convergent_wikimedia", "CONVERGENT"),
    ):
        control = controls[name]
        measured = scope_of(control)
        expected = {
            f"{prefix}_ROWS_TOTAL": measured["rows"],
            f"{prefix}_RESOLVED_BEFORE": measured["before"],
            f"{prefix}_RESOLVED_AFTER": measured["after"],
        }
        for key, value in expected.items():
            if control[key] != value:
                raise ValidationError(f"{name}.{key} is {control[key]}, measured {value}")
        if control["on_opportunity"] != measured["on_opportunity"]:
            raise ValidationError(f"{name}.on_opportunity disagrees with the diagnostic")
        if measured["after"] != measured["rows"]:
            raise ValidationError(f"{name}: {measured['after']} of {measured['rows']} rows resolve")
        if measured["reliability"] != {control[f"{prefix}_RELIABILITY"]}:
            raise ValidationError(f"{name}: reliability {measured['reliability']} measured")
        if measured["ids"] != {control[f"{prefix}_ASSESSMENT_ID"]}:
            raise ValidationError(f"{name}: assessment ids {measured['ids']} measured")
    detailed = controls["detailed_wikimedia"]
    convergent = controls["convergent_wikimedia"]
    if detailed["DETAILED_ASSESSMENT_ID"] == convergent["CONVERGENT_ASSESSMENT_ID"]:
        raise ValidationError("the detailed and convergent kinds resolved the same assessment")
    for k in ("source_id", "resource_id", "record_kind_id", "claim_type"):
        if detailed["scope"][k] != convergent["scope"][k]:
            raise ValidationError(f"the two Wikimedia scopes differ on {k}, not only on the kind")

    se = controls["stack_exchange"]
    se_rows = [r for r in diagnostic["rows"] if r["source_id"] == "stack-exchange"]
    if (
        len(se_rows) != se["rows"]
        or sum(r["on_opportunity"] for r in se_rows) != se["on_opportunity"]
    ):
        raise ValidationError("the Stack Exchange control counts disagree with the diagnostic")
    for row in se_rows:
        for path in ("resolution_via_claim_facts", "resolution_via_lineage"):
            if row[path]["outcome"] != se["STACK_EXCHANGE_RESULT_AFTER"] and path.endswith(
                "lineage"
            ):
                raise ValidationError("a Stack Exchange row resolved differently from its control")
            if row[path]["outcome"] != se["STACK_EXCHANGE_RESULT_BEFORE"] and path.endswith(
                "facts"
            ):
                raise ValidationError(
                    "a Stack Exchange row's before-state differs from its control"
                )
    if se["STACK_EXCHANGE_RESULT_AFTER"] == "RESOLVED":
        ids = {
            a["id"]
            for a in diagnostic["current_assessments"]
            if a["scope"]["source_id"] == "stack-exchange"
        }
        if not ids:
            raise ValidationError(
                "Stack Exchange resolved with no Stack Exchange assessment in the inventory"
            )

    ted = controls["ted"]
    ted_rows = [r for r in diagnostic["rows"] if r["source_id"] == "ted-eu"]
    before = sum(r["resolution_via_claim_facts"]["outcome"] == "RESOLVED" for r in ted_rows)
    after = sum(r["resolution_via_lineage"]["outcome"] == "RESOLVED" for r in ted_rows)
    if (len(ted_rows), before, after) != (
        ted["TED_CONTROL_ROWS"],
        ted["resolved_before"],
        ted["resolved_after"],
    ):
        raise ValidationError("the TED control disagrees with the diagnostic")
    if after < before or after == 0:
        raise ValidationError(
            f"TED resolution went from {before} to {after}; the regression control failed"
        )
    if ted["modified"]:
        raise ValidationError("TED was modified")

    m = decision["measurements"]
    d = diagnostic["measurements"]
    pairs = {
        "WIKIMEDIA_OPPORTUNITY_EVIDENCE_ROWS": sum(
            1
            for r in diagnostic["rows"]
            if r["on_opportunity"] and r["source_id"] == "wikimedia-pageviews"
        ),
        "STACK_EXCHANGE_OPPORTUNITY_ROWS": se["on_opportunity"],
        "TED_CONTROL_ROWS": len(ted_rows),
        "SCORABLE_EVIDENCE_BEFORE": d["scorable_via_stored_column"],
        "SCORABLE_EVIDENCE_AFTER": d["scorable_via_lineage"],
        "SCORABLE_OPPORTUNITY_LINKED_EVIDENCE_BEFORE": d[
            "opportunity_linked_scorable_via_stored_column"
        ],
        "SCORABLE_OPPORTUNITY_LINKED_EVIDENCE_AFTER": d["opportunity_linked_scorable_via_lineage"],
        "DETAILED_RESOLVED_AFTER": detailed["DETAILED_RESOLVED_AFTER"],
        "CONVERGENT_RESOLVED_AFTER": convergent["CONVERGENT_RESOLVED_AFTER"],
    }
    for key, value in pairs.items():
        if m[key] != value:
            raise ValidationError(f"measurements.{key} is {m[key]}, measured {value}")
    if d["scorable_via_lineage"] != d["resolved_via_lineage"]:
        raise ValidationError("scorable and resolved disagree; a value was written somewhere else")
    if d["resolved_rows_whose_resource_basis_is_explicit"] != d["resolved_via_lineage"]:
        raise ValidationError(
            "a row resolved on a basis other than the explicit persisted resource"
        )
    scorability = decision["scorability"]
    if scorability["SCORABLE_EVIDENCE_AFTER"] != d["scorable_via_lineage"]:
        raise ValidationError("the scorability block disagrees with the diagnostic")
    if scorability["reliability_written_to_evidence"] != 0:
        raise ValidationError("a reliability was written to an Evidence row")


def _check_nothing_was_written(decision: dict, diagnostic: dict) -> None:
    before = diagnostic["counters"]["before"]
    after = diagnostic["counters"]["after"]
    if before != after:
        raise ValidationError(
            f"counters moved: {sorted(k for k in before if before[k] != after.get(k))}"
        )
    if after["evidence_reliability_written"] != 0:
        raise ValidationError("evidence.reliability is written on a row")
    if after["scores_table"] != "ABSENT":
        raise ValidationError("a scores table exists")
    m = decision["measurements"]
    for key, counter in (
        ("RELIABILITY_ASSESSMENTS_BEFORE", "reliability_assessments"),
        ("RELIABILITY_ASSESSMENTS_AFTER", "reliability_assessments"),
        ("RELIABILITY_BASIS_ROWS_BEFORE", "reliability_assessment_basis_rows"),
        ("RELIABILITY_BASIS_ROWS_AFTER", "reliability_assessment_basis_rows"),
        ("INDEPENDENCE_GROUPS_BEFORE", "independence_groups"),
        ("INDEPENDENCE_GROUPS_AFTER", "independence_groups"),
        ("PERSISTED_SCORES_BEFORE", "scores_table"),
        ("PERSISTED_SCORES_AFTER", "scores_table"),
    ):
        if m[key] != after[counter]:
            raise ValidationError(
                f"measurements.{key} is {m[key]}, the deployment says {after[counter]}"
            )
    if m["RELIABILITY_ASSESSMENTS_AFTER"] != len(diagnostic["current_assessments"]):
        raise ValidationError("the assessment inventory does not match the counter")
    baseline = decision["canonical_baseline"]
    for key in (
        "raw_records",
        "normalized_records",
        "signals",
        "claims",
        "claim_revisions",
        "evidence",
        "reliability_assessments",
        "independence_groups",
        "opportunities",
        "opportunity_revisions",
        "opportunity_evidence_links",
        "threshold_registrations",
        "claim_derivations",
        "proposition_evaluation_refusals",
        "embeddings",
        "scores_table",
    ):
        if baseline[key] != after[key]:
            raise ValidationError(
                f"canonical_baseline.{key} is {baseline[key]}, measured {after[key]}"
            )
    if not baseline["unchanged_before_and_after"]:
        raise ValidationError("the baseline records a change")
    accounting = decision["mission_accounting"]
    hot = sorted(k for k, v in accounting.items() if v != 0)
    if hot:
        raise ValidationError(f"mission accounting is not zero on {hot}")
    scorability = decision["scorability"]
    if not scorability["SCORE_IS_PERSISTED"].startswith("NO"):
        raise ValidationError("a score is recorded as persisted")


def _check_the_limitation_is_reported_not_edited(decision: dict, diagnostic: dict) -> None:
    limitation = decision["opportunity_limitation"]
    measured = diagnostic["opportunity_limitation"]
    if measured is None:
        raise ValidationError("the diagnostic did not read the Opportunity revision")
    if (
        limitation["revision_id"] != measured["revision_id"]
        or limitation["created_at"] != measured["created_at"]
    ):
        raise ValidationError("the decision names a different revision than the diagnostic read")
    if limitation["limitation_text"] != measured["limitation_text"]:
        raise ValidationError("the recorded limitation text is not the canonical one")
    if measured["revisions_before"] != measured["revisions_after"]:
        raise ValidationError("an Opportunity revision was written")
    if limitation["historical_revision_edited"] or limitation["revision_2_created"]:
        raise ValidationError("the canonical Opportunity was changed")
    if (
        limitation["action"] != "STOP"
        or limitation["code"] != "OPPORTUNITY_LIMITATION_RECONCILIATION_REQUIRED"
    ):
        raise ValidationError("the stale limitation is not reported as requiring reconciliation")
    stale_by_measurement = measured["opportunity_linked_rows_resolving_via_lineage"] > 0 and bool(
        measured["assessments_created_after_the_revision"]
    )
    if limitation["stale"] != stale_by_measurement:
        raise ValidationError(
            f"the limitation is recorded stale={limitation['stale']} and the measurement says "
            f"{stale_by_measurement}"
        )
    if not limitation["true_when_written"]:
        raise ValidationError("revision 1 is recorded as false when written; it was true then")


def _check_the_aggregation_is_diagnostic_only(decision: dict, diagnostic: dict) -> None:
    measured = diagnostic["aggregation_diagnostic"]
    recorded = decision["aggregation_diagnostic"]
    for block in (measured, recorded):
        if tuple(block["$banner"]) != BANNER:
            raise ValidationError(f"the aggregation banner reads {block['$banner']}")
        if block["persisted"]:
            raise ValidationError("the aggregation diagnostic was persisted")
    if measured["calibration"] != "UNCALIBRATED" or recorded["profile_status"] != "UNCALIBRATED":
        raise ValidationError("REFERENCE_PROFILE_V1 is not recorded UNCALIBRATED")
    claims = measured["claims"]
    if recorded["claims_aggregated"] != len(claims):
        raise ValidationError("the decision counts a different number of aggregated claims")
    if recorded["opportunity_linked_claims_aggregated"] != sum(
        1 for c in claims if c["on_opportunity"]
    ):
        raise ValidationError("the Opportunity-linked claim count disagrees")
    differs = measured["claims_where_full_aggregator_differs_from_pass_through"]
    if recorded["claims_where_full_aggregator_differs_from_pass_through"] != differs:
        raise ValidationError("the pass-through comparison disagrees with the diagnostic")
    independent = measured["claims_with_established_independence"]
    if recorded["claims_with_established_independence"] != independent:
        raise ValidationError("the independence count disagrees with the diagnostic")
    if diagnostic["counters"]["after"]["independence_groups"] == 0 and independent != 0:
        raise ValidationError("established independence reported with zero independence groups")
    if recorded["max_members_received"] != max(
        (c["max_members_received"] for c in claims), default=0
    ):
        raise ValidationError("max_members_received disagrees with the diagnostic")
    for claim in claims:
        if claim["support_group_count"] > 1 and claim["established_independence_groups"] == 0:
            raise ValidationError(
                f"claim {claim['claim_id'][:8]} has {claim['support_group_count']} support groups "
                "and no established independence; unknown provenance forms ONE group"
            )


def _check_the_binding_basis(decision: dict, diagnostic: dict) -> None:
    identity = decision["resource_identity"]
    if identity["binding_basis"] != EXPLICIT:
        raise ValidationError(f"binding basis {identity['binding_basis']!r}")
    if identity["RESOURCE_BINDING_DEPENDS_ON_CURRENT_MUTABLE_CONFIG"] != "NO":
        raise ValidationError("the binding depends on current mutable configuration")
    if identity["explicit_or_derived"] != "EXPLICIT":
        raise ValidationError("the resource is recorded as derived")
    listed = " ".join(identity["insufficient_bases_not_relied_on"])
    missing = [b for b in INSUFFICIENT_BASES if b.lower() not in listed.lower()]
    if missing:
        raise ValidationError(f"the insufficient bases no longer list {missing}")
    target = identity["verification_target"]
    if target["matched"] != (target["expected"] == target["re_derived_from_lineage"]):
        raise ValidationError("the verification target's match flag disagrees with its strings")
    if target["used_as_implementation_authority"]:
        raise ValidationError("the expected resource string was used as implementation authority")
    detailed = decision["controls"]["detailed_wikimedia"]["scope"]["resource_id"]
    if target["re_derived_from_lineage"] != detailed:
        raise ValidationError(
            "the re-derived resource is not the one the detailed rows resolve with"
        )
    ambiguity = identity["could_multiple_resources_fit"]
    if (
        ambiguity["answer"] == "NO"
        and diagnostic["measurements"]["rows_with_ambiguous_lineage_resource"] != 0
    ):
        raise ValidationError("ambiguous lineages exist and the record says none could")
    layers = {(e["table"], e["identifier"]): e for e in diagnostic["lineage_audit"]["layers"]}
    raw = layers[("acquisition.raw_records", "provenance.resource_id")]
    if raw["rows_carrying_it"] != raw["rows"]:
        raise ValidationError(
            "not every RawRecord carries a resource; the explicit basis is not universal"
        )


def _check_the_outcome(decision: dict) -> None:
    outcome = decision["primary_outcome"]
    if outcome not in OUTCOMES:
        raise ValidationError(f"primary outcome {outcome!r} is not one of the four")
    criteria = decision["repaired_criteria_section_27"]
    keys = [k for k in criteria if k[0].isdigit()]
    if len(keys) != 17 or any(not isinstance(criteria[k], bool) for k in keys):
        raise ValidationError(
            "the seventeen section-27 criteria are not each recorded as a boolean"
        )
    if criteria["all_met"] != all(criteria[k] for k in keys):
        raise ValidationError("all_met disagrees with the criteria")
    if outcome == OUTCOMES[0] and not criteria["all_met"]:
        raise ValidationError("REPAIRED with a failing criterion is forced")
    if outcome != OUTCOMES[0] and not str(decision["why_not_REPAIRED"]).strip():
        raise ValidationError("a non-REPAIRED outcome must say why")
    selected = [k for k, v in decision["options"].items() if v["verdict"] == "SELECTED"]
    if selected != [decision["selected_option"]]:
        raise ValidationError(f"selected option {decision['selected_option']} against {selected}")
    for key, option in decision["options"].items():
        if not str(option["why"]).strip():
            raise ValidationError(f"option {key} carries no reason")
    implementation = decision["implementation"]
    if (
        implementation["hard_coded_source_exception"]
        or implementation["source_specific_branches"] != 0
    ):
        raise ValidationError("the implementation records a source-specific exception")
    if implementation["forbidden_mappings_used"]:
        raise ValidationError("a forbidden mapping was used")
    if (
        not decision["scope_exactness"]["five_part_scope_unchanged"]
        or decision["scope_exactness"]["resolver_modified"]
    ):
        raise ValidationError("the scope or the resolver was changed")


def _check_the_parked_arc(decision: dict) -> None:
    parked = decision["parked_states_preserved"]
    if parked["changed_by_this_mission"]:
        raise ValidationError("the parked arc was changed")
    states = _load(SELECTED_CLASS)["states_kept_apart"]
    for key in ("CLASS_SELECTED", "CONSTRUCT_SELECTED", "RUN_AUTHORIZED"):
        if states[key] != parked["q1"][key]:
            raise ValidationError(
                f"Q1 {key} reads {states[key]} and the record says {parked['q1'][key]}"
            )
    if not states["CLASS_SELECTED"] or states["CONSTRUCT_SELECTED"] or states["RUN_AUTHORIZED"]:
        raise ValidationError("Q1 is no longer selected-without-construct-or-run")
    qualification = _load(QUALIFICATION)
    tally = {k: qualification["tally"][k] for k in ("PASS", "PARTIAL", "FAIL")}
    if tally != {k: parked["globalping"][k] for k in ("PASS", "PARTIAL", "FAIL")}:
        raise ValidationError(f"the Globalping tally reads {tally}")
    if qualification["verdict"] != parked["globalping"]["verdict"]:
        raise ValidationError("the Globalping verdict moved")
    v2 = _load(V2_DECISION)
    if v2["primary_outcome"] != parked["v2"]["primary_outcome"]:
        raise ValidationError("the V2 outcome moved")
    if v2["corpus_frozen"] or v2["measurements_executed"] != 0:
        raise ValidationError("a corpus was frozen or a measurement executed")
    if (DATA / "selected-construct-v1.json").exists():
        raise ValidationError("a construct artifact exists")


def _check_the_predecessors_point_forward(decision: dict) -> None:
    carriers = decision["opportunity_limitation"]["derived_carriers_given_forward_pointers"]
    if sorted(carriers) != sorted(f"docs/data/{p.name}" for p in PREDECESSORS):
        raise ValidationError("the recorded carriers are not the three predecessors")
    for path in PREDECESSORS:
        record = _load(path)
        pointer = record.get("forward_pointer")
        if not pointer:
            raise ValidationError(f"{path.name} carries no forward pointer")
        if pointer["superseded_by"] != f"docs/data/{DECISION.name}":
            raise ValidationError(f"{path.name} points somewhere other than this record")
        if pointer["appended_by_mission"] != decision["mission"]:
            raise ValidationError(f"{path.name} names another mission as the appender")
        if pointer["record_edited"] or record.get("mission") == decision["mission"]:
            raise ValidationError(f"{path.name} was edited or reattributed")
    moves = _load(PREDECESSORS[0])
    m1 = next(c for c in moves["candidates"] if c["candidate_id"] == "M1")
    if not any(FALSE_LINEAGE_SENTENCE in b for b in m1["known_blockers"]):
        raise ValidationError(
            "the false lineage sentence was removed from the 1.76 record; history was edited"
        )
    audit = _load(PREDECESSORS[1])
    if sum(row["with_reliability"] for row in audit["evidence_lineages"]) != 0:
        raise ValidationError("the 1.76 audit's stored-column counts were rewritten")
    run = _load(PREDECESSORS[2])
    if run["persisted"]["revision_id"] != decision["opportunity_limitation"]["revision_id"]:
        raise ValidationError("the synthesis run record names a different revision")


def _check_the_runners_resolve_late() -> None:
    stored_column = re.compile(
        r"ReliabilityStatus\.RESOLVED\s*\n\s*if row\[\"reliability\"\] is not None"
    )
    for path in RUNNERS:
        text = path.read_text(encoding="utf-8")
        if stored_column.search(text):
            raise ValidationError(
                f"{path.name} still derives the reliability status from the stored column"
            )
        if "scope_from_lineage" not in text or "_resolve_late(" not in text:
            raise ValidationError(f"{path.name} does not resolve reliability late from lineage")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and getattr(node.func, "id", None) == "_persist"
                and any(
                    isinstance(a, ast.Constant) and a.value == "ELIGIBLE_CONTEXT" for a in node.args
                )
            ):
                raise ValidationError(
                    f"{path.name} hard-codes the eligibility a citation is written with"
                )


def validate() -> tuple[dict, dict]:
    decision = _load(DECISION)
    diagnostic = _load(DIAGNOSTIC)
    try:
        _check_the_rule_names_no_source(diagnostic)
        _check_the_scope_is_exact()
        _check_every_resolution_is_exact(diagnostic)
        _check_the_controls_match_the_diagnostic(decision, diagnostic)
        _check_nothing_was_written(decision, diagnostic)
        _check_the_limitation_is_reported_not_edited(decision, diagnostic)
        _check_the_aggregation_is_diagnostic_only(decision, diagnostic)
        _check_the_binding_basis(decision, diagnostic)
        _check_the_outcome(decision)
        _check_the_parked_arc(decision)
        _check_the_predecessors_point_forward(decision)
        _check_the_runners_resolve_late()
    except (KeyError, TypeError, IndexError, StopIteration) as error:
        raise ValidationError(f"the records do not carry {error!r}") from error
    except SyntaxError as error:
        raise ValidationError(f"a checked module does not parse: {error}") from error
    return decision, diagnostic


# ------------------------------------------------------------------------ renderers


def render_decision(decision: dict) -> str:
    identity = decision["resource_identity"]
    contradiction = decision["historical_apparent_contradiction"]
    failure = decision["production_failure_frozen"]
    controls = decision["controls"]
    m = decision["measurements"]
    limitation = decision["opportunity_limitation"]
    lines = [
        "# Wikimedia measurement scope binding — the resource was there all along",
        "",
        f"Generated from `{DECISION.name}`. Do not edit by hand.",
        "",
        f"**{decision['primary_outcome']}**",
        "",
        decision["why_this_outcome"],
        "",
        "## The production failure, frozen",
        "",
        "| | |",
        "|---|---|",
        f"| PRODUCTION_SCOPE_BEFORE | {failure['PRODUCTION_SCOPE_BEFORE']} |",
        f"| RESOLVER_RESULT_BEFORE | {failure['RESOLVER_RESULT_BEFORE']} |",
        f"| MISSING_SCOPE_FACT | {failure['MISSING_SCOPE_FACT']} |",
        "",
        "## The apparent contradiction",
        "",
        "| | |",
        "|---|---|",
        f"| HISTORICAL_RESOLUTION_PATH | `{contradiction['HISTORICAL_RESOLUTION_PATH']}` |",
        f"| CURRENT_PRODUCTION_RESOLUTION_PATH | `{contradiction['CURRENT_PRODUCTION_RESOLUTION_PATH']}` |",
        f"| PATH_DIFFERENCE | {contradiction['PATH_DIFFERENCE']} |",
        f"| ROOT_CAUSE | {contradiction['ROOT_CAUSE']} |",
        "",
        "## Where the resource lives",
        "",
        f"**{identity['answer']}** — `{identity['location']}`, {identity['explicit_or_derived']}, "
        f"binding basis `{identity['binding_basis']}`, depends on current mutable configuration: "
        f"**{identity['RESOURCE_BINDING_DEPENDS_ON_CURRENT_MUTABLE_CONFIG']}**.",
        "",
        "| layer | resource identity | immutable |",
        "|---|---|---|",
    ]
    for layer in decision["lineage_audit"]:
        lines.append(
            f"| `{layer['layer']}` | {layer['resource_identity']} | {layer['immutable']} |"
        )
    lines += [
        "",
        "## Options",
        "",
        "| option | verdict | why |",
        "|---|---|---|",
    ]
    for key, option in decision["options"].items():
        lines.append(f"| {key}. {option['name']} | `{option['verdict']}` | {option['why']} |")
    lines += [
        "",
        "## Controls, through the real resolver",
        "",
        "| scope | rows | before | after | reliability | assessment |",
        "|---|---|---|---|---|---|",
        f"| Wikimedia detailed | {controls['detailed_wikimedia']['DETAILED_ROWS_TOTAL']} "
        f"| {controls['detailed_wikimedia']['DETAILED_RESOLVED_BEFORE']} "
        f"| {controls['detailed_wikimedia']['DETAILED_RESOLVED_AFTER']} "
        f"| {controls['detailed_wikimedia']['DETAILED_RELIABILITY']} "
        f"| `{controls['detailed_wikimedia']['DETAILED_ASSESSMENT_ID'][:8]}` |",
        f"| Wikimedia convergent | {controls['convergent_wikimedia']['CONVERGENT_ROWS_TOTAL']} "
        f"| {controls['convergent_wikimedia']['CONVERGENT_RESOLVED_BEFORE']} "
        f"| {controls['convergent_wikimedia']['CONVERGENT_RESOLVED_AFTER']} "
        f"| {controls['convergent_wikimedia']['CONVERGENT_RELIABILITY']} "
        f"| `{controls['convergent_wikimedia']['CONVERGENT_ASSESSMENT_ID'][:8]}` |",
        f"| Stack Exchange | {controls['stack_exchange']['rows']} | `{controls['stack_exchange']['STACK_EXCHANGE_RESULT_BEFORE']}` "
        f"| `{controls['stack_exchange']['STACK_EXCHANGE_RESULT_AFTER']}` | — | — |",
        f"| TED | {controls['ted']['TED_CONTROL_ROWS']} | {controls['ted']['resolved_before']} "
        f"| {controls['ted']['resolved_after']} | 0.5 / 0.55 | unchanged |",
        "",
        "## Scorability, kept apart",
        "",
        "| | |",
        "|---|---|",
    ]
    for key in (
        "ASSESSMENT_EXISTS",
        "ASSESSMENT_APPLIES",
        "EVIDENCE_IS_SCORABLE",
        "AGGREGATION_CAN_RUN",
        "SCORE_IS_PERSISTED",
    ):
        lines.append(f"| {key} | {decision['scorability'][key]} |")
    lines += [
        "",
        f"Scorable Evidence {m['SCORABLE_EVIDENCE_BEFORE']} → {m['SCORABLE_EVIDENCE_AFTER']}; "
        f"Opportunity-linked {m['SCORABLE_OPPORTUNITY_LINKED_EVIDENCE_BEFORE']} → "
        f"{m['SCORABLE_OPPORTUNITY_LINKED_EVIDENCE_AFTER']}. Assessments "
        f"{m['RELIABILITY_ASSESSMENTS_BEFORE']} → {m['RELIABILITY_ASSESSMENTS_AFTER']}, independence groups "
        f"{m['INDEPENDENCE_GROUPS_BEFORE']} → {m['INDEPENDENCE_GROUPS_AFTER']}, scores "
        f"{m['PERSISTED_SCORES_BEFORE']} → {m['PERSISTED_SCORES_AFTER']}.",
        "",
        "## The stale limitation",
        "",
        f"**{limitation['code']}.** Revision {limitation['revision']} of `{limitation['opportunity_id'][:8]}` "
        f"still reads: *{limitation['limitation_text']}* {limitation['why_stale']}. "
        f"Action: **{limitation['action']}**; the historical revision was not edited.",
        "",
        f"**Remaining limitation.** {decision['remaining_limitation']}",
        "",
        f"**Next: {decision['recommended_next_mission']['title']}.** "
        f"{decision['recommended_next_mission']['shape']}",
        "",
    ]
    return "\n".join(lines)


def render_diagnostic(diagnostic: dict) -> str:
    m = diagnostic["measurements"]
    agg = diagnostic["aggregation_diagnostic"]
    lines = [
        "# Which registered resource produced this measurement?",
        "",
        f"Generated from `{DIAGNOSTIC.name}`. Do not edit by hand.",
        "",
        "**" + " · ".join(diagnostic["$banner"]) + "**",
        "",
        f"Measured {diagnostic['measured_at']} by `{diagnostic['generated_by']}`, nothing written.",
        "",
        "## The rule",
        "",
        f"- resource: {diagnostic['scope_construction']['resource_id']}",
        f"- record kind: {diagnostic['scope_construction']['record_kind_id']}",
        f"- ambiguity: {diagnostic['scope_construction']['ambiguity_rule']}",
        "",
        "## Where identifiers are persisted",
        "",
        "| table | identifier | rows carrying it | rows |",
        "|---|---|---|---|",
    ]
    for layer in diagnostic["lineage_audit"]["layers"]:
        lines.append(
            f"| `{layer['table']}` | `{layer['identifier']}` | {layer['rows_carrying_it']} | {layer['rows']} |"
        )
    lines += [
        "",
        "## Per scope, the real resolver twice",
        "",
        "| source | proposition kind | rows | on Opportunity | via claim facts | via lineage | reliability |",
        "|---|---|---|---|---|---|---|",
    ]
    for scope in diagnostic["scopes"]:
        rel = ", ".join(str(r) for r in scope["reliability_via_lineage"]) or "—"
        lines.append(
            f"| `{scope['source_id']}` | `{scope['proposition_kind']}` | {scope['rows']} "
            f"| {scope['on_opportunity_rows']} | {scope['resolved_via_claim_facts']} "
            f"| {scope['resolved_via_lineage']} | {rel} |"
        )
    lines += [
        "",
        f"Rows {m['evidence_rows']}, exactly one lineage resource on {m['rows_with_exactly_one_lineage_resource']}, "
        f"ambiguous {m['rows_with_ambiguous_lineage_resource']}, absent {m['rows_with_no_lineage_resource']}. "
        f"Resolved via claim facts {m['resolved_via_claim_facts']}, via lineage {m['resolved_via_lineage']}; "
        f"Opportunity-linked {m['opportunity_linked_resolved_via_claim_facts']} → "
        f"{m['opportunity_linked_resolved_via_lineage']}.",
        "",
        "## Aggregation, read-only",
        "",
        f"Profile `{agg['profile']}` ({agg['calibration']}), {len(agg['claims'])} Claims, "
        f"{agg['claims_where_full_aggregator_differs_from_pass_through']} differing from reliability "
        f"pass-through, {agg['claims_with_established_independence']} with established independence, "
        f"persisted: {agg['persisted']}.",
        "",
        "## Counters",
        "",
        "| counter | before | after |",
        "|---|---|---|",
    ]
    for key, value in diagnostic["counters"]["before"].items():
        lines.append(f"| {key} | {value} | {diagnostic['counters']['after'][key]} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        decision, diagnostic = validate()
    except ValidationError as error:
        print(f"REFUSED  Wikimedia scope binding: {error}")
        return 1

    rendered = {
        RENDERED_DECISION: render_decision(decision),
        RENDERED_DIAGNOSTIC: render_diagnostic(diagnostic),
    }
    if args.check:
        for path, text in rendered.items():
            if not path.exists():
                print(f"DRIFT    {path.name} does not exist")
                return 1
            if path.read_text(encoding="utf-8") != text:
                print(f"DRIFT    {path.name} does not match its record")
                return 1
        print("ok       the Wikimedia scope binding matches its records")
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {decision['primary_outcome']}")
    print(
        f"scorable {decision['measurements']['SCORABLE_EVIDENCE_BEFORE']} -> {decision['measurements']['SCORABLE_EVIDENCE_AFTER']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
