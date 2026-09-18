"""An interactive terminal form for a human annotator (N08-B follow-up).

Filling 400 JSON cells by hand is where honest annotators make format mistakes. This module asks the
questions one at a time, checks a pasted quote against the surface immediately, and writes the working
pack after every record. It decides nothing: every state, quote, subject and note comes from what the
person types. It never proposes an answer, never pre-fills a cell and never reads anything but the
annotator's own working pack and the rendered surface files next to it.

The prompts are in French because the first operator annotates in French; the stored values are the
contract's own identifiers.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import datetime
from typing import Any

from .annotation import ATTESTATION_FLAGS
from .finding import MAX_QUOTE, MIN_QUOTE, locate_quote
from .labels import LABELS, LabelStatus
from .surface import MARKERS, marker_regions

__all__ = ["QUESTIONS", "SessionQuit", "run_session"]

Ask = Callable[[str], str]
Say = Callable[[str], None]
Save = Callable[[dict[str, Any]], None]

QUESTIONS: dict[str, str] = {
    "REPORTED_FAILED_ATTEMPT": "L'auteur dit-il avoir essayé quelque chose de précis qui n'a PAS marché (erreur, mauvais résultat, aucun effet) ?",
    "NEGATIVE_EVALUATION_OF_NAMED_SOLUTION": "L'auteur critique-t-il lui-même, dans sa prose, un outil/produit NOMMÉ dans le texte (pas juste un message d'erreur) ?",
    "SUCCESSFUL_WORKAROUND": "L'auteur dit-il qu'un contournement qu'il utilise FONCTIONNE ?",
    "EXPLICIT_FEATURE_REQUEST": "L'auteur demande-t-il qu'un outil nommé AJOUTE une fonction qui lui manque ?",
    "REPEATED_DIFFICULTY_SAME_AUTHOR": "L'auteur dit-il que cette même difficulté lui arrive À RÉPÉTITION ?",
    "SWITCHING_INTENT": "L'auteur dit-il vouloir REMPLACER un outil nommé par un autre ?",
    "STATED_HYPOTHETICAL_PAYMENT": "L'auteur dit-il qu'il PAIERAIT pour quelque chose ?",
    "STATED_PAST_PAYMENT": "L'auteur dit-il AVOIR PAYÉ un produit ou service nommé ?",
}

REMINDER = "Seul compte ce que l'auteur affirme lui-même : une citation d'un tiers, une négation ou une hypothèse = non."


class SessionQuit(Exception):  # noqa: N818 - stopping is not an error
    """The annotator asked to stop; everything answered so far is already saved."""


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _read(ask: Ask, prompt: str, allowed: set[str]) -> str:
    while True:
        answer = ask(prompt).strip().lower()
        if answer == "q":
            raise SessionQuit
        if answer in allowed:
            return answer


def _text(ask: Ask, prompt: str) -> str:
    answer = ask(prompt)
    if answer.strip().lower() == "q":
        raise SessionQuit
    return answer


def _quote(ask: Ask, say: Say, surface: str, *, subject: bool, forbid_code: bool) -> dict[str, Any]:
    min_len, max_len = (2, 120) if subject else (MIN_QUOTE, MAX_QUOTE)
    what = "le NOM EXACT de l'outil" if subject else "la phrase exacte (sur une seule ligne)"
    regions = marker_regions(surface)
    while True:
        quote = _text(
            ask, f"  Colle {what}, copiée depuis le texte ({min_len}-{max_len} caractères) : "
        )
        quote = quote.strip("\r\n")
        if any(marker in quote for marker in MARKERS):
            say(
                "  -> Ne copie pas les marqueurs [CODE], [/CODE], [QUOTE], [/QUOTE] ou [IMAGE]. Recommence."
            )
            continue
        count = surface.count(quote) if quote else 0
        if not (min_len <= len(quote) <= max_len):
            say(
                f"  -> Longueur {len(quote)} : il faut entre {min_len} et {max_len} caractères. Recommence."
            )
            continue
        if count == 0:
            say(
                "  -> Ce texte n'existe pas exactement dans la question (espaces, ponctuation ?). Recommence."
            )
            continue
        occurrence = 1
        if count > 1:
            choice = _read(
                ask,
                f"  Ce texte apparaît {count} fois. Laquelle (1-{count}) ? ",
                {str(i) for i in range(1, count + 1)},
            )
            occurrence = int(choice)
        located = locate_quote(surface, quote, occurrence, min_len=min_len, max_len=max_len)
        if not isinstance(located, tuple):
            say(f"  -> Refusé ({located}). Recommence.")
            continue
        start, end = located
        if any(k == "QUOTE" and start < b and a < end for k, a, b in regions):
            say(
                "  -> Ce passage est dans un bloc [QUOTE] (texte cité d'un tiers) : il ne compte pas. Choisis autre chose ou réponds non."
            )
            continue
        if (forbid_code or subject) and any(
            k == "CODE" and start < b and a < end for k, a, b in regions
        ):
            say(
                "  -> Ce passage est dans un bloc [CODE] : pour ce label il doit venir de la prose. Choisis autre chose ou réponds non."
            )
            continue
        return {"quote": quote, "occurrence": occurrence}


def _cell(
    ask: Ask,
    say: Say,
    label_id: str,
    extractable: bool,
    requires_subject: bool,
    forbid_code: bool,
    surface: str,
) -> dict[str, Any]:
    say("")
    say(f"[{label_id}]")
    say(QUESTIONS[label_id])
    answer = _read(
        ask,
        "  o = oui, n = non, ? = je ne sais pas, t = relire le texte, q = quitter : ",
        {"o", "n", "?", "t"},
    )
    while answer == "t":
        say(surface)
        answer = _read(
            ask, "  o = oui, n = non, ? = je ne sais pas, q = quitter : ", {"o", "n", "?"}
        )
    if answer == "?":
        note = ""
        while not note.strip():
            note = _text(ask, "  Explique en quelques mots pourquoi tu hésites : ")
        return (
            {"state": "UNCERTAIN", "evidence": [], "subject": None, "note": note}
            if extractable
            else {"state": "UNCERTAIN", "note": note}
        )
    if answer == "n" or not extractable:
        state = "PRESENT" if answer == "o" else "ABSENT"
        return (
            {"state": state, "evidence": [], "subject": None, "note": None}
            if extractable
            else {"state": state, "note": None}
        )
    evidence = [_quote(ask, say, surface, subject=False, forbid_code=forbid_code)]
    while _read(ask, "  Ajouter une autre phrase comme preuve ? (o/n) : ", {"o", "n"}) == "o":
        evidence.append(_quote(ask, say, surface, subject=False, forbid_code=forbid_code))
    subject = (
        _quote(ask, say, surface, subject=True, forbid_code=True) if requires_subject else None
    )
    return {"state": "PRESENT", "evidence": evidence, "subject": subject, "note": None}


def run_session(
    pack: dict[str, Any],
    surfaces: dict[str, str],
    ask: Ask,
    say: Say,
    save: Save,
    *,
    label_ids: tuple[str, ...] | None = None,
    attestation_wording: dict[str, str] | None = None,
) -> str:
    """Annotate every record that still has an UNLABELLED cell, saving after each record.

    `surfaces` maps normalized_record_id to the rendered surface; the caller has checked each digest.
    Returns COMPLETE, or raises SessionQuit after saving.

    Mission 1.85.15: `label_ids` limits the questions to those labels (default: every label, as before), and
    `attestation_wording` replaces the attestation questions (default: the blind annotation's four flags).
    """
    labels = {
        label.label_id: label
        for label in LABELS
        if label.status is not LabelStatus.NOT_SAFE
        and (label_ids is None or label.label_id in label_ids)
    }
    by_id = {record["normalized_record_id"]: record for record in pack["records"]}
    order = pack["record_order"]
    if not pack.get("annotation_started_at"):
        pack["annotation_started_at"] = _now()
        save(pack)
    say(REMINDER)
    for position, rid in enumerate(order, start=1):
        record = by_id[rid]
        if all(cell.get("state") != "UNLABELLED" for cell in record["labels"].values()):
            continue
        surface = surfaces[rid]
        while True:
            say("")
            say("=" * 78)
            say(f"QUESTION {position}/{len(order)}   (fichier surfaces/{position:03d}-{rid}.txt)")
            say("=" * 78)
            say(surface)
            say("=" * 78)
            answers = {}
            for label_id, label in labels.items():
                answers[label_id] = _cell(
                    ask,
                    say,
                    label_id,
                    label.status is LabelStatus.EXTRACTABLE,
                    label.requires_subject,
                    not label.evidence_may_be_in_code,
                    surface,
                )
            say("")
            say("Récapitulatif : " + ", ".join(f"{k}={v['state']}" for k, v in answers.items()))
            if (
                _read(
                    ask,
                    "Enregistrer ce record ? (o = oui, r = recommencer ce record) : ",
                    {"o", "r"},
                )
                == "o"
            ):
                break
        record["labels"] = answers
        save(pack)
        say(f"Record {position} enregistré.")
    say("")
    say("Tous les records sont remplis. Attestation (réponds o uniquement si c'est vrai) :")
    wording = attestation_wording or {
        "no_model_output_seen": "Je n'ai vu aucune sortie d'un modèle d'IA sur ces questions.",
        "no_model_assistance_used": "Je n'ai utilisé aucune assistance d'IA pour décider ou rédiger mes réponses.",
        "did_not_see_other_annotators_labels": "Je n'ai pas vu les réponses d'un autre annotateur.",
        "labelled_from_rendered_surface_only": "J'ai répondu uniquement à partir du texte affiché.",
    }
    attestation = dict(pack.get("attestation") or {})
    for flag in wording if attestation_wording else ATTESTATION_FLAGS:
        attestation[flag] = _read(ask, f"  {wording[flag]} (o/n) : ", {"o", "n"}) == "o"
    now = _now()
    attestation["attested_at"] = now
    pack["attestation"] = attestation
    pack["annotation_completed_at"] = now
    save(pack)
    return "COMPLETE"


def surface_matches(surface: str, expected_sha256: str) -> bool:
    return hashlib.sha256(surface.encode("utf-8")).hexdigest() == expected_sha256


def dumps(pack: dict[str, Any]) -> str:
    return json.dumps(pack, indent=1, ensure_ascii=False) + "\n"
