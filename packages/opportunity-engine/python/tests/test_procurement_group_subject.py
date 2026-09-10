"""Mission 1.81. A procurement Signal keyed on a CPV group names the group as its subject.

The division packet and the group packet coexist: a Signal whose scope carries no level,
or the level `division`, keys exactly as it did under grouping 1.2.0; a Signal whose
scope says `group` keys on the group code, and the reviewed scope rules type it CATEGORY.
"""

from __future__ import annotations

import pathlib

from sros_opportunity import SubjectScopeType
from sros_opportunity.grouping import GROUPING_PROCEDURE_VERSION, subject_key
from sros_opportunity.scope_resolution import load_scope_rules

DOCS = pathlib.Path(__file__).resolve().parents[4] / "docs" / "data"
SCOPE_RULES = DOCS / "observation-scope-rules-v1.json"

DIVISION_SCOPE = {
    "source_ids": ["ted-eu"],
    "amount_types": ["TOTAL_VALUE"],
    "currencies": ["EUR"],
    "notice_classes": ["CONTRACT_NOTICE"],
    "classification_scheme": "CPV",
    "classification_codes": ["92500000", "92610000"],
}


def test_the_grouping_version_moved():
    assert GROUPING_PROCEDURE_VERSION == "source-native-subject-grouping@1.3.0"


def test_a_scope_with_no_level_keys_at_the_division_as_before():
    key = subject_key("ted-eu", "procurement_value_contrast", DIVISION_SCOPE)
    assert str(key) == "ted-eu:CPV-division:92"


def test_a_scope_stating_the_division_level_keys_at_the_division():
    scope = {
        **DIVISION_SCOPE,
        "classification_level": "division",
        "classification_level_code": "92",
    }
    assert (
        str(subject_key("ted-eu", "procurement_value_contrast", scope)) == "ted-eu:CPV-division:92"
    )


def test_a_group_scope_keys_on_the_group_code():
    scope = {
        **DIVISION_SCOPE,
        "classification_codes": ["92512000", "92521000"],
        "classification_level": "group",
        "classification_level_code": "925",
    }
    assert str(subject_key("ted-eu", "procurement_value_contrast", scope)) == "ted-eu:CPV-group:925"


def test_two_groups_are_two_subjects_and_neither_is_the_division():
    keys = {
        str(
            subject_key(
                "ted-eu",
                "procurement_value_contrast",
                {
                    **DIVISION_SCOPE,
                    "classification_codes": [f"{code}12000"],
                    "classification_level": "group",
                    "classification_level_code": code,
                },
            )
        )
        for code in ("925", "926")
    }
    assert keys == {"ted-eu:CPV-group:925", "ted-eu:CPV-group:926"}
    assert "ted-eu:CPV-division:92" not in keys


def test_the_group_scheme_has_a_reviewed_category_rule():
    rules = load_scope_rules(SCOPE_RULES)
    rule = rules.rule_for("ted-eu", "CPV-group")
    assert rule is not None
    assert rule.scope_type is SubjectScopeType.CATEGORY
    assert rules.rule_for("ted-eu", "CPV-division").scope_type is SubjectScopeType.CATEGORY
    # Mission 1.82 registered the class rule, so a test asserting its absence asserted that
    # the vocabulary may never gain a level. What this line defends is the match rule: a
    # scheme is looked up by EXACT equality, so an unregistered one resolves to nothing.
    assert rules.rule_for("ted-eu", "CPV-class").scope_type is SubjectScopeType.CATEGORY
    assert rules.rule_for("ted-eu", "CPV-category") is None
    assert rules.rule_for("ted-eu", "CPV") is None
