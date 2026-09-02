"""Loading the human reference set, one split at a time.

Mission 1.26 §6.7 and §11. **Holdout isolation is structural, not a convention.**

The labels for each split live in a **separate file**, and the loader takes the
split as a required argument with no default. Development code calling
`load_development()` cannot reach a holdout label, because the holdout labels are
not in the file it opened. A single labelled dataset with a `split` column would
put both a metre apart and rely on every future caller filtering correctly --
which is a rule, and rules get forgotten by the person in a hurry.

    problem-family-human-reference-batch-v1.json          pairs and splits, NO labels
    problem-family-human-reference-labels-development.json   development labels only
    problem-family-human-reference-labels-holdout.json        holdout labels only

**Provenance is mandatory and has no safe default.** `reference_origin` is
required on load and validated against `ReferenceOrigin`; a file without it is
refused rather than assumed human. That is the Mission 1.25 §0 lesson written
into the loader: the repository once described AI-assisted labels as human ground
truth, and no field existed that could have contradicted it.

**The Mission 1.25 dataset stays separately queryable.** Nothing here reads,
merges or supersedes it. It is `problem-family-evaluation-v1` with its own rubric
version, sampling, label origins and predictions; this is
`problem-family-human-reference-v1`. Merging them would lose mission origin,
sampling version and the association between a label and the prediction it was
scored against.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass

from .evaluation import LabelSet, ReferenceDecision, ReferenceLabel, ReferenceOrigin, Split

__all__ = [
    "DATASET_ID",
    "PRIOR_DATASET_ID",
    "HoldoutAccessError",
    "ReferenceDatasetPaths",
    "load_reference_labels",
    "load_development_labels",
    "load_holdout_labels",
]

DATASET_ID = "problem-family-human-reference-v1"

# Mission 1.25's dataset, named so this module can assert it is never the thing
# being loaded here. Kept separately queryable by §11.
PRIOR_DATASET_ID = "problem-family-evaluation-v1"

# The family relation's answer vocabulary, mapped to the relation-neutral
# reference decisions the scorer uses. Declared here rather than inferred, so a
# file using the wrong vocabulary fails loudly.
_FAMILY_DECISIONS = {
    "SAME_FAMILY": ReferenceDecision.SAME,
    "DIFFERENT_FAMILY": ReferenceDecision.DIFFERENT,
    "UNCERTAIN": ReferenceDecision.UNCERTAIN,
}


class HoldoutAccessError(RuntimeError):
    """Raised when holdout labels are reached through a development path.

    An exception rather than an empty result: a development routine that
    silently received nothing would carry on and report a score over zero
    holdout pairs, which looks like a passing evaluation.
    """


@dataclass(frozen=True)
class ReferenceDatasetPaths:
    """Where the three files live. Separate by design, not by accident."""

    directory: pathlib.Path

    @property
    def batch(self) -> pathlib.Path:
        return self.directory / "problem-family-human-reference-batch-v1.json"

    def labels(self, split: Split) -> pathlib.Path:
        return (
            self.directory / f"problem-family-human-reference-labels-{split.value.lower()}-v1.json"
        )


def load_reference_labels(
    paths: ReferenceDatasetPaths,
    split: Split,
    *,
    expected_origin: ReferenceOrigin | None = None,
) -> LabelSet:
    """Load one split's labels. The split is required and never defaulted.

    `expected_origin` is checked when supplied. It is not defaulted to
    `HUMAN_OPERATOR`: a caller that assumed human provenance and got AI-assisted
    labels would be the Mission 1.25 error repeating itself, and a default is
    exactly how an assumption gets made once and inherited forever.
    """
    path = paths.labels(split)
    if not path.exists():
        raise FileNotFoundError(
            f"no {split.value} labels at {path}. The splits are stored in separate files "
            "so that development code cannot reach holdout labels; an absent file means "
            "that split has not been labelled, never that it is empty"
        )
    raw = json.loads(path.read_text(encoding="utf-8"))

    if raw.get("dataset_id") != DATASET_ID:
        raise ValueError(
            f"{path} declares dataset {raw.get('dataset_id')!r}, expected {DATASET_ID!r}. "
            f"Mission 1.25's set is {PRIOR_DATASET_ID!r} and is never loaded through here"
        )
    if raw.get("split") != split.value:
        raise HoldoutAccessError(
            f"{path} contains {raw.get('split')!r} labels and was opened as {split.value!r}. "
            "The file name and its content must agree, or the split boundary is decorative"
        )

    origin_value = raw.get("reference_origin")
    if not origin_value:
        raise ValueError(
            f"{path} declares no reference_origin. Provenance is mandatory and has no "
            "default: a set whose origin nobody recorded must never be read as human"
        )
    origin = ReferenceOrigin(origin_value)
    if expected_origin is not None and origin is not expected_origin:
        raise ValueError(
            f"{path} carries origin {origin.value}, and the caller required {expected_origin.value}"
        )

    labels = tuple(
        ReferenceLabel(
            pair_id=row["pair_id"],
            a_question_id=row["a_question_id"],
            b_question_id=row["b_question_id"],
            reviewer=row["reviewer"],
            origin=origin,
            decision=_FAMILY_DECISIONS[row["decision_as_supplied"]],
            labelled_at=row["labelled_at"],
            split=split,
            rubric_version=row.get("rubric_version", ""),
        )
        for row in raw["labels"]
    )
    wrong_split = [label.pair_id for label in labels if label.split is not split]
    if wrong_split:
        raise HoldoutAccessError(f"{path} carries rows for another split: {wrong_split}")
    return LabelSet(labels)


def load_development_labels(
    paths: ReferenceDatasetPaths, *, expected_origin: ReferenceOrigin | None = None
) -> LabelSet:
    """The interface classifier development uses. It cannot reach the holdout."""
    return load_reference_labels(paths, Split.DEVELOPMENT, expected_origin=expected_origin)


def load_holdout_labels(
    paths: ReferenceDatasetPaths, *, expected_origin: ReferenceOrigin | None = None
) -> LabelSet:
    """The interface a FINAL evaluation uses, and nothing else should.

    Deliberately a different function name from the development one. A call to
    it is visible in a diff, which is the point: reaching the holdout should be
    a decision somebody can see being made.
    """
    return load_reference_labels(paths, Split.HOLDOUT, expected_origin=expected_origin)
