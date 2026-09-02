"""Deterministic stratified sampling for a human-labelled reference set.

Mission 1.26 §3 to §6. **No model output touches this module.** Not a
prediction, not a confidence, not an explanation, not the fact that a pair was
predicted at all. The sampler reads the frozen candidate features and nothing
else, and a test asserts the module imports no gateway, no classifier and no run
artifact.

**Why that matters more than it sounds.** The obvious way to build a second
reference set is to show the reviewer the pairs V1 got wrong. That produces a
dataset which can measure nothing afterwards: every future classifier would be
scored on a sample selected by an earlier classifier's mistakes. The set built
here is usable for evaluation precisely because it was chosen blind to V1.

**Strata are sampling mechanisms, never expected labels.** A pair in the
high-specificity stratum is not expected to be a family; it is expected to be a
*different kind of question* for the reviewer than one in the wrapper stratum.
The names describe deterministic features, and the reviewer's answer is
unconstrained by them.

**The result is an ENRICHED sample and is not prevalence-representative.** The
low-similarity stratum holds 275 of the 711 available pairs and contributes 8 of
40; the wrapper stratum holds 2 and contributes both. Nothing derived from this
set may be read as *how often problem families occur in Stack Exchange*.
`ENRICHMENT_WARNING` carries that sentence so a report cannot omit it by
forgetting.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum

from .candidates import CandidatePair, CandidateSet

__all__ = [
    "SAMPLING_VERSION",
    "SPLIT_VERSION",
    "SAMPLING_SEED",
    "SPLIT_SEED",
    "BATCH_SIZE",
    "DEVELOPMENT_SIZE",
    "HOLDOUT_SIZE",
    "ENRICHMENT_WARNING",
    "Stratum",
    "STRATUM_QUOTAS",
    "SampledPair",
    "ReferenceBatch",
    "classify_stratum",
    "sample_reference_batch",
]

SAMPLING_VERSION = "problem-family-human-reference-sampling@1.0.0"
SPLIT_VERSION = "problem-family-human-reference-split@1.0.0"

# Fixed before any pair was drawn. Named constants rather than literals so the
# recorded provenance and the code cannot disagree about what produced the set.
SAMPLING_SEED = "mission-1.26/problem-family-human-reference"
SPLIT_SEED = "mission-1.26/problem-family-human-reference-split"

BATCH_SIZE = 40
DEVELOPMENT_SIZE = 24
HOLDOUT_SIZE = 16

ENRICHMENT_WARNING = (
    "This 40-pair set is an EVALUATION-ORIENTED ENRICHED SAMPLE. Strata were "
    "sampled at deliberately unequal rates -- the low-similarity stratum holds 275 "
    "of the 711 available pairs and contributes 8, the wrapper stratum holds 2 and "
    "contributes both -- so the proportion of any label in it is NOT an estimate of "
    "how often that label occurs among Docker Stack Exchange pairs. It may be used "
    "to develop and evaluate a classifier. It may never be used to state a "
    "prevalence."
)


class Stratum(StrEnum):
    """Deterministic feature bands. NOT expected labels.

    Each is defined by candidate features that already exist under the frozen
    eligibility rule; none involves a semantic judgement made here.
    """

    #: A shared site tag carried by at most about six of the 89 observations.
    #: The most specific thing two questions can share without any model.
    HIGH_SPECIFICITY = "A_HIGH_SPECIFICITY"

    #: A shared tag of middling frequency.
    MEDIUM_SPECIFICITY = "B_MEDIUM_SPECIFICITY"

    #: A shared tag common enough to say little. Eligible, and weak.
    LOW_SPECIFICITY = "C_LOW_SPECIFICITY"

    #: The pair shares a diagnostic fragment. Mission 1.20's canonical
    #: superficially-similar shape, and the corpus holds very few.
    DIAGNOSTIC_WRAPPER = "D_DIAGNOSTIC_WRAPPER"

    #: No shared tag at all: eligible only through overlapping title tokens.
    #: Different technology, and the frozen rule surfaced it anyway.
    DIFFERENT_TAGS_SHARED_TOKENS = "E_DIFFERENT_TAGS_SHARED_TOKENS"


# Quotas summing to BATCH_SIZE. Chosen for REVIEWER INFORMATIVENESS, not for
# expected labels: A and E are the bands where a shared concern and a
# cross-technology goal could plausibly appear, D takes every pair that exists
# because the shape is the canonical hard negative, and C is deliberately
# undersampled because it is the largest and weakest band. That deliberate
# imbalance is exactly why `ENRICHMENT_WARNING` exists.
STRATUM_QUOTAS: dict[Stratum, int] = {
    Stratum.HIGH_SPECIFICITY: 10,
    Stratum.MEDIUM_SPECIFICITY: 8,
    Stratum.LOW_SPECIFICITY: 8,
    Stratum.DIAGNOSTIC_WRAPPER: 2,
    Stratum.DIFFERENT_TAGS_SHARED_TOKENS: 12,
}

# Rarity boundaries, in the same log(N / count) units the family generator uses.
# 2.7 is about six observations in 89; 1.9 is about thirteen.
HIGH_RARITY = 2.7
MEDIUM_RARITY = 1.9


def _digest(seed: str, pair_id: str) -> str:
    """sha256 rather than `hash()`: Python's string hash is salted per process,
    so an ordering built on it would differ between the run that recorded a
    dataset and the run that checked it."""
    return hashlib.sha256(f"{seed}|{pair_id}".encode()).hexdigest()


def classify_stratum(pair: CandidatePair, rarity: dict[str, float]) -> Stratum:
    """Which band a pair falls in, from candidate features alone.

    Order matters and is deliberate: a pair sharing a diagnostic fragment is
    classified by that first, because the wrapper shape is what makes it
    interesting to a reviewer whatever else it shares.
    """
    if pair.longest_shared_diagnostic:
        return Stratum.DIAGNOSTIC_WRAPPER
    if not pair.shared_tags:
        return Stratum.DIFFERENT_TAGS_SHARED_TOKENS
    rarest = max(rarity.get(tag, 0.0) for tag in pair.shared_tags)
    if rarest >= HIGH_RARITY:
        return Stratum.HIGH_SPECIFICITY
    if rarest >= MEDIUM_RARITY:
        return Stratum.MEDIUM_SPECIFICITY
    return Stratum.LOW_SPECIFICITY


@dataclass(frozen=True)
class SampledPair:
    """One pair as the reference set records it. **No label and no prediction.**"""

    pair_id: str
    a_question_id: str
    b_question_id: str
    a_observation_key: str
    b_observation_key: str
    candidate_rank: int
    stratum: Stratum
    split: str
    shared_tags: tuple[str, ...]
    shared_title_tokens: tuple[str, ...]
    shared_diagnostic: str
    rarest_shared_tag: str
    rarest_shared_tag_rarity: float
    eligibility_reasons: tuple[str, ...]

    def to_json(self) -> dict[str, object]:
        return {
            "pair_id": self.pair_id,
            "a_question_id": self.a_question_id,
            "b_question_id": self.b_question_id,
            "a_observation_key": self.a_observation_key,
            "b_observation_key": self.b_observation_key,
            "candidate_rank": self.candidate_rank,
            "stratum": self.stratum.value,
            "split": self.split,
            "deterministic_features": {
                "shared_tags": list(self.shared_tags),
                "shared_title_tokens": list(self.shared_title_tokens),
                "shared_diagnostic": self.shared_diagnostic,
                "rarest_shared_tag": self.rarest_shared_tag,
                "rarest_shared_tag_rarity": round(self.rarest_shared_tag_rarity, 3),
                "eligibility_reasons": list(self.eligibility_reasons),
            },
        }


@dataclass(frozen=True)
class ReferenceBatch:
    sampling_version: str
    split_version: str
    rubric_version: str
    candidate_generator_version: str
    corpus_size: int
    eligible_pairs: int
    excluded_prior_pairs: int
    available_pairs: int
    pairs: tuple[SampledPair, ...]
    stratum_populations: dict[str, int]
    selection_rules: tuple[str, ...]

    @property
    def development(self) -> tuple[SampledPair, ...]:
        return tuple(p for p in self.pairs if p.split == "DEVELOPMENT")

    @property
    def holdout(self) -> tuple[SampledPair, ...]:
        return tuple(p for p in self.pairs if p.split == "HOLDOUT")

    def to_json(self) -> dict[str, object]:
        return {
            "dataset_id": "problem-family-human-reference-v1",
            "relation": "SAME_PROBLEM_FAMILY",
            "sampling_version": self.sampling_version,
            "split_version": self.split_version,
            "rubric_version": self.rubric_version,
            "candidate_generator_version": self.candidate_generator_version,
            "reference_origin_expected": "HUMAN_OPERATOR",
            "human_ground_truth_established": False,
            "labels_present": False,
            "corpus_size": self.corpus_size,
            "eligible_pairs": self.eligible_pairs,
            "excluded_prior_pairs": self.excluded_prior_pairs,
            "available_pairs": self.available_pairs,
            "counts": {
                "total": len(self.pairs),
                "development": len(self.development),
                "holdout": len(self.holdout),
                "by_stratum": {
                    s.value: sum(1 for p in self.pairs if p.stratum is s) for s in Stratum
                },
                "by_stratum_and_split": {
                    s.value: {
                        "DEVELOPMENT": sum(1 for p in self.development if p.stratum is s),
                        "HOLDOUT": sum(1 for p in self.holdout if p.stratum is s),
                    }
                    for s in Stratum
                },
            },
            "stratum_populations_available": self.stratum_populations,
            "enrichment_warning": ENRICHMENT_WARNING,
            "selection_rules": list(self.selection_rules),
            "pairs": [p.to_json() for p in self.pairs],
        }


def sample_reference_batch(
    candidates: CandidateSet,
    rarity: dict[str, float],
    *,
    excluded_pair_ids: frozenset[str],
    rubric_version: str,
    quotas: dict[Stratum, int] | None = None,
) -> ReferenceBatch:
    """Draw the batch. Deterministic, reproducible, and blind to every model.

    Within a stratum, pairs are ordered by `sha256(seed | pair_id)` rather than
    by candidate rank. Taking the top of each band by rank would reproduce the
    family ordering inside every stratum, which is the thing the strata exist to
    break up.
    """
    # `quotas` exists so a test can exercise the ordering and the split on a
    # small synthetic corpus. Production passes nothing and gets
    # STRATUM_QUOTAS; a caller that supplied its own would be visible in a diff,
    # which is the only protection a seam like this needs.
    quotas = quotas or STRATUM_QUOTAS
    production = quotas == STRATUM_QUOTAS
    total = sum(quotas.values())

    ranked = [(rank, p) for rank, p in enumerate(candidates.pairs, start=1)]
    available = [(rank, p) for rank, p in ranked if p.pair_id not in excluded_pair_ids]

    banded: dict[Stratum, list[tuple[int, CandidatePair]]] = {s: [] for s in Stratum}
    for rank, pair in available:
        banded[classify_stratum(pair, rarity)].append((rank, pair))

    populations = {s.value: len(banded[s]) for s in Stratum}

    selected: list[SampledPair] = []
    for stratum in Stratum:
        members = sorted(banded[stratum], key=lambda item: _digest(SAMPLING_SEED, item[1].pair_id))
        quota = quotas[stratum]
        if len(members) < quota:
            raise ValueError(
                f"stratum {stratum.value} holds {len(members)} available pairs and the "
                f"quota is {quota}. A quota is not silently reduced: the batch composition "
                "was declared before sampling and shrinking it here would change the "
                "dataset without changing its recorded version"
            )
        chosen = members[:quota]

        # The split is assigned WITHIN the stratum, so both partitions carry the
        # same mix of question shapes. A global hash split would leave one
        # partition short of a band, and §10's composition gates are applied per
        # split.
        ordered = sorted(chosen, key=lambda item: _digest(SPLIT_SEED, item[1].pair_id))
        holdout_count = round(len(ordered) * HOLDOUT_SIZE / BATCH_SIZE)
        for index, (rank, pair) in enumerate(ordered):
            rarest = (
                max(pair.shared_tags, key=lambda t: rarity.get(t, 0.0)) if pair.shared_tags else ""
            )
            selected.append(
                SampledPair(
                    pair_id=pair.pair_id,
                    a_question_id=pair.a_question_id,
                    b_question_id=pair.b_question_id,
                    a_observation_key=pair.a_key,
                    b_observation_key=pair.b_key,
                    candidate_rank=rank,
                    stratum=stratum,
                    split="HOLDOUT" if index < holdout_count else "DEVELOPMENT",
                    shared_tags=pair.shared_tags,
                    shared_title_tokens=pair.shared_title_tokens,
                    shared_diagnostic=pair.longest_shared_diagnostic,
                    rarest_shared_tag=rarest,
                    rarest_shared_tag_rarity=rarity.get(rarest, 0.0),
                    eligibility_reasons=pair.reasons,
                )
            )

    selected.sort(key=lambda p: (p.stratum.value, p.pair_id))
    batch = ReferenceBatch(
        sampling_version=SAMPLING_VERSION,
        split_version=SPLIT_VERSION,
        rubric_version=rubric_version,
        candidate_generator_version=candidates.generator_version,
        corpus_size=candidates.corpus_size,
        eligible_pairs=candidates.considered_pairs,
        excluded_prior_pairs=len(excluded_pair_ids),
        available_pairs=len(available),
        pairs=tuple(selected),
        stratum_populations=populations,
        selection_rules=(
            "eligibility is the FROZEN Mission 1.25 rule, imported unchanged; this module "
            "adds no eligibility criterion of its own",
            f"every pair labelled in Mission 1.25 is excluded by canonical unordered "
            f"pair id ({len(excluded_pair_ids)} pairs)",
            "strata are deterministic feature bands, never expected labels: a shared "
            "diagnostic fragment first, then no-shared-tag, then the rarest shared tag "
            f"at >= {HIGH_RARITY}, >= {MEDIUM_RARITY}, or below",
            f"quotas {', '.join(f'{s.value}={q}' for s, q in STRATUM_QUOTAS.items())}, "
            f"summing to {BATCH_SIZE}, declared before any pair was drawn",
            "within a stratum, pairs are ordered by sha256(sampling seed | pair id) and "
            "the quota is taken from the front. NOT by candidate rank, which would "
            "reproduce the family ordering inside every band",
            "the split is assigned WITHIN each stratum by sha256(split seed | pair id), "
            f"so both partitions carry the same mix of shapes, totalling "
            f"{DEVELOPMENT_SIZE} development and {HOLDOUT_SIZE} holdout",
            "NO model output of any kind enters this: not a prediction, a confidence, an "
            "explanation, or the fact that a pair was ever predicted",
        ),
    )
    if len(batch.pairs) != total:
        raise ValueError(f"expected {total} pairs, drew {len(batch.pairs)}")
    # The 24/16 shape is asserted only for the PRODUCTION quotas. Per-stratum
    # rounding sums to the global target for those figures and need not for an
    # arbitrary set, so asserting it unconditionally would be asserting an
    # invariant that is not one.
    if production and (
        len(batch.development) != DEVELOPMENT_SIZE or len(batch.holdout) != HOLDOUT_SIZE
    ):
        raise ValueError(
            f"the production split must be {DEVELOPMENT_SIZE}/{HOLDOUT_SIZE}, got "
            f"{len(batch.development)}/{len(batch.holdout)}"
        )
    return batch
