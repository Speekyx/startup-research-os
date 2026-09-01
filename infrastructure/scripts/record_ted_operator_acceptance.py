"""Replay ONE already-made operator decision onto a second local deployment.

**This is not a `decide` verb, and it must never become one.** Mission 1.15.6
refused to ship a command that records a human decision, and that refusal
stands: a decision that is routine to record is not a decision. What this script
does is narrower, and the difference is the whole reason it may exist.

    a `decide` verb   records ANY decision a caller supplies, for any condition
    this script       replays ONE decision, already made and already documented,
                      whose subject, wording and verdict are literals below

It cannot record a new acceptance. It cannot clear another condition. It cannot
be pointed at another source, another profile or another review version -- and
where it could have trusted an identifier, it looks the subject up instead and
refuses when the deployment disagrees with the document.

**Why it exists.** The operator works on two machines. The registry catalog
travels by git and `sros-source load` reproduces it exactly; the human decision
does not travel by anything, because it lives only in
`registry.source_condition_verifications`. The alternative to this script is
retyping a 1683-character legal acknowledgement by hand on the second machine,
which is a worse guarantee of the thing the row exists to preserve: that the
words accepted are exactly the words reviewed.

**What the operator is asserting by running it.** Not "a script said so". That
the acceptance printed below is theirs, that it is still true of THIS machine,
and that this machine is the same local, private, single-operator deployment the
acceptance was written about. It prints the full text and requires an explicit
typed confirmation before writing, because reading it is the act.

Usage:

    python infrastructure/scripts/record_ted_operator_acceptance.py            # dry run
    python infrastructure/scripts/record_ted_operator_acceptance.py --apply

Related: `docs/data/ted-eu-operator-risk-acceptance-v1.md` (the decision),
`docs/data/ted-eu-authorization-bootstrap-v1.md` §6.2 (the statement),
`docs/architecture/mission-1.15.6.1-report.md` §C (how it was first recorded).
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from datetime import UTC, datetime

# Everything this script may write, as literals. Nothing here is a parameter,
# because a parameter is how a replay becomes a `decide` verb.
SOURCE_ID = "ted-eu"
USE_PROFILE = "local-private-research-v1"
REVIEW_VERSION = 2
CONDITION_KEY = "ted-database-right-residual-exposure-accepted"
VERIFIER = "local-operator"
VERIFIER_VERSION = "acknowledgement-v1"
RESULT = "SATISFIED"
REFERENCE = "docs/data/ted-eu-operator-risk-acceptance-v1.md"

# The acknowledgement, VERBATIM and in the language it was written in. It is a
# literal rather than a file read, so a later edit to the document cannot
# silently change what a second machine records as having been accepted. If the
# document and this string ever disagree, that is a finding, not a merge.
REASON = "J’ai lu intégralement `ted-eu-local-official-route-readiness-v1.md` et\n`ted-eu-authorization-bootstrap-v1.md`.\n\nJe comprends que H-36A est `NOT ESTABLISHED` : rien ne détermine actuellement si\nun droit sui generis sur la base TED existe, ni qui pourrait en être titulaire.\n\nJe comprends que H-36B est `NOT ADDRESSED` pour l’extraction large du corpus :\nrien n’établit qu’un tel droit, s’il existe, a été accordé ou abandonné.\n\nJe comprends que l’autorisation locale de `ted-eu` est volontairement limitée.\nElle repose sur la décision 2011/833/UE, la notice légale TED/SIMAP, les\nmétadonnées `COM_REUSE` et l’usage publié par l’Office des publications pour les\nroutes officielles, et qu’aucun de ces éléments ne constitue à lui seul une\nconcession explicite d’un droit de base de données.\n\nJe comprends que cette acceptation repose également sur des requêtes bornées et\nciblées, sur la minimisation des champs dès l’acquisition et sur l’absence de\nredistribution. Si l’une de ces conditions cesse d’être vraie, cette acceptation\ncesse de s’appliquer.\n\nJe comprends qu’il ne s’agit pas d’une validation juridique, qu’aucun avocat n’a\nvalidé cette analyse et que cette acceptation ne résout ni H-36A ni H-36B.\n\nJ’accepte le risque résiduel et non résolu lié aux droits de base de données pour\n`ted-eu`, uniquement sous `local-private-research-v1`, review version 2, et pour\nrien d’autre.\n\nCette acceptation ne s’étend pas à\n`commercial-multi-tenant-research-v1`, à une future utilisation publique, vendue,\npar abonnement, orientée client ou multi-tenant, aux packages Bulk XML, au\ndataset historique `ted-csv`, à une autre source ou à une future review TED\nsubstantiellement différente."

CONFIRMATION = "j'accepte"


def _fail(message: str) -> int:
    print(f"REFUSED: {message}", file=sys.stderr)
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the row. Without it, nothing is written and the plan is printed.",
    )
    args = parser.parse_args()

    url = os.environ.get("DATABASE_URL")
    if not url:
        return _fail("DATABASE_URL is not set. This writes to a deployment, not to the tree.")

    import psycopg

    with psycopg.connect(url) as conn:
        # 1. The condition must exist in THIS deployment, under THIS profile and
        #    THIS review version. Looked up rather than hard-coded: a machine
        #    whose catalog is behind carries a different review, and attaching a
        #    v2 acceptance to a v1 condition would be recording a decision about
        #    a document nobody read.
        rows = conn.execute(
            """SELECT c.id, c.verification, r.review_version, r.assessed_use_profile,
                      r.approval_state
                 FROM registry.source_review_conditions c
                 JOIN registry.source_policy_reviews r ON r.id = c.review_id
                WHERE c.source_id = %s AND c.condition_key = %s
                  AND r.assessed_use_profile = %s AND r.superseded_at IS NULL""",
            (SOURCE_ID, CONDITION_KEY, USE_PROFILE),
        ).fetchall()

        if len(rows) != 1:
            return _fail(
                f"expected exactly one current {CONDITION_KEY!r} condition for "
                f"{SOURCE_ID!r} under {USE_PROFILE!r}; found {len(rows)}. Run "
                "`sros-source load` first, and if it is still not one, this "
                "deployment's catalog is not the one this acceptance was written about."
            )

        condition_id, verification, review_version, profile, approval = rows[0]

        if int(review_version) != REVIEW_VERSION:
            return _fail(
                f"this deployment carries review v{review_version} and the acceptance was "
                f"written about v{REVIEW_VERSION}. `git pull` does not load the catalog; "
                "run `sros-source load`. If the catalog really has moved on, the "
                "acceptance has to be made again by a person, not replayed."
            )

        if verification != "HUMAN_CONFIRMATION":
            return _fail(
                f"the condition's verification kind is {verification!r}, not "
                "HUMAN_CONFIRMATION. This script records a HUMAN decision; a condition a "
                "machine can verify must be cleared by `sros-source verify --apply`."
            )

        # 2. Exactly one row, ever. A second acceptance of one decision would
        #    read as two people accepting, or as one person accepting twice
        #    after something changed. Neither happened.
        existing = conn.execute(
            """SELECT verifier, verified_at FROM registry.source_condition_verifications
                WHERE source_id = %s AND condition_key = %s AND verifier = %s""",
            (SOURCE_ID, CONDITION_KEY, VERIFIER),
        ).fetchall()
        if existing:
            print(f"already recorded on this deployment: {existing[0][0]} at {existing[0][1]}")
            print("nothing to do. The acceptance is per DEPLOYMENT and this one has it.")
            return 0

        print(f"deployment   : {url.rsplit('@', 1)[-1]}")
        print(f"source       : {SOURCE_ID}")
        print(f"profile      : {profile}  review v{review_version}  {approval}")
        print(f"condition    : {CONDITION_KEY}")
        print(f"verifier     : {VERIFIER}@{VERIFIER_VERSION}  ->  {RESULT}")
        print(f"reference    : {REFERENCE}")
        print()
        print("THE ACCEPTANCE THAT WOULD BE RECORDED, VERBATIM:")
        print("-" * 76)
        print(REASON)
        print("-" * 76)
        print()

        if not args.apply:
            print("DRY RUN. Nothing was written. Re-run with --apply to record it.")
            return 0

        print("Recording this states that the text above is YOUR acceptance, that it is")
        print("still true of THIS machine, and that this machine is the same local,")
        print("private, single-operator deployment it was written about.")
        print()
        try:
            typed = input(f"Type {CONFIRMATION!r} to record it, anything else to abort: ")
        except EOFError:
            return _fail("no terminal to confirm on. This is not a step a pipeline runs.")
        if typed.strip().lower() != CONFIRMATION:
            print("aborted. Nothing was written.")
            return 1

        # The id is DERIVED from the decision rather than generated, so every
        # machine that replays this acceptance converges on one identity instead
        # of inventing a fresh uuid4 each time. `condition_id` is itself
        # deterministic -- `sros-source load` reproduces the catalog exactly --
        # so the derivation is stable across deployments.
        #
        # The machine where the acceptance was FIRST recorded, in Mission
        # 1.15.6.1, keeps its own historical id: that row predates this script
        # and is not rewritten to match. Two ids for one decision across two
        # machines is the honest record of how each row got there.
        row_id = uuid.uuid5(
            uuid.UUID(str(condition_id)),
            f"{SOURCE_ID}|{CONDITION_KEY}|{VERIFIER}|{VERIFIER_VERSION}",
        )
        conn.execute(
            """INSERT INTO registry.source_condition_verifications
                   (id, condition_id, source_id, condition_key, verifier, verifier_version,
                    result, reason, reference, verified_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                str(row_id),
                condition_id,
                SOURCE_ID,
                CONDITION_KEY,
                VERIFIER,
                VERIFIER_VERSION,
                RESULT,
                REASON,
                REFERENCE,
                datetime.now(UTC),
            ),
        )
        conn.commit()
        print(f"recorded. one row, id {row_id}")
        print()
        print("Next: `sros-source --use-profile local-private-research-v1 conditions ted-eu`")
        print("should now show four conditions of four satisfied.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
