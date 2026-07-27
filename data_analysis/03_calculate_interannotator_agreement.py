#!/usr/bin/env python3
"""Calculate binary subword inter-annotator agreement."""

import argparse
import json
import re
import statistics
from itertools import combinations
from pathlib import Path


HERE = Path(__file__).resolve().parent
INPUT_DIR = HERE / "jsons" / "participant_data_evaluation"
OUTPUT_DIR = HERE / "results"
TASK = "speaker_and_accent_similarity"
PUNCTUATION_ONLY = re.compile(r"""^[,.!?;:'"“”‘’\-–—]+$""")


def is_selectable(segment):
    return any(
        part and not part.isspace() and not PUNCTUATION_ONLY.fullmatch(part)
        for part in re.split(r"(\s+)", segment)
    )


def annotation_indices(trial):
    value = trial.get("annotation", "")
    return {int(index) for index in str(value).split("|") if index}


def load_responses():
    participants = {}
    for path in sorted(INPUT_DIR.rglob("*.json")):
        response = json.loads(path.read_text(encoding="utf-8"))
        participant_id = response.get("participant", {}).get(
            "prolific_pid",
            response.get("participant", {}).get("participant_id", path.stem),
        )
        trials = {
            trial["question_id"]: trial
            for trial in response.get("data", [])
            if trial.get("task") == TASK
        }
        participants[participant_id] = {
            "target_speaker": response.get("participant", {}).get(
                "target_speaker", ""
            ),
            "audio_speaker_ids": {
                trial.get("audio_speaker_id")
                for trial in trials.values()
                if trial.get("audio_speaker_id")
            },
            "trials": trials,
        }
    return participants


def cohens_kappa(first, second):
    observed = sum(a == b for a, b in zip(first, second)) / len(first)
    first_positive = statistics.fmean(first)
    second_positive = statistics.fmean(second)
    expected = (
        first_positive * second_positive
        + (1 - first_positive) * (1 - second_positive)
    )
    return (observed - expected) / (1 - expected) if expected != 1 else 1.0


def calculate(participants, selected_ids):
    question_sets = [
        set(participants[participant]["trials"]) for participant in selected_ids
    ]
    questions = sorted(set.intersection(*question_sets))
    decisions = {participant: [] for participant in selected_ids}

    for question in questions:
        trials = [
            participants[participant]["trials"][question]
            for participant in selected_ids
        ]
        segmentations = {trial["segmented_text"] for trial in trials}
        if len(segmentations) != 1:
            raise ValueError(f"Participants saw different segmentation for {question}")

        segments = segmentations.pop().split("|")
        selected_by_participant = {
            participant: annotation_indices(
                participants[participant]["trials"][question]
            )
            for participant in selected_ids
        }
        for index, segment in enumerate(segments):
            if is_selectable(segment):
                for participant in selected_ids:
                    decisions[participant].append(
                        int(index in selected_by_participant[participant])
                    )

    item_count = len(next(iter(decisions.values())))
    rater_count = len(selected_ids)
    positive_counts = [
        sum(decisions[participant][item] for participant in selected_ids)
        for item in range(item_count)
    ]

    observed = statistics.fmean(
        (
            positive * (positive - 1)
            + (rater_count - positive) * (rater_count - positive - 1)
        )
        / (rater_count * (rater_count - 1))
        for positive in positive_counts
    )
    positive_rate = sum(positive_counts) / (item_count * rater_count)
    expected = positive_rate**2 + (1 - positive_rate) ** 2
    fleiss_kappa = (observed - expected) / (1 - expected)
    uniform_expected = 0.5
    free_marginal_kappa = (
        (observed - uniform_expected) / (1 - uniform_expected)
    )
    total_decisions = item_count * rater_count
    positive_decisions = sum(positive_counts)
    negative_decisions = total_decisions - positive_decisions
    observed_disagreement = 1 - observed
    expected_disagreement = (
        2 * positive_decisions * negative_decisions
        / (total_decisions * (total_decisions - 1))
    )
    krippendorff_alpha = 1 - observed_disagreement / expected_disagreement

    pairwise = []
    for first, second in combinations(selected_ids, 2):
        shared_positive = sum(
            a == 1 and b == 1
            for a, b in zip(decisions[first], decisions[second])
        )
        first_positive = sum(decisions[first])
        second_positive = sum(decisions[second])
        positive_union = first_positive + second_positive - shared_positive
        pairwise.append(
            {
                "participant_1": first,
                "participant_2": second,
                "observed_agreement": sum(
                    a == b
                    for a, b in zip(decisions[first], decisions[second])
                )
                / item_count,
                "cohens_kappa": cohens_kappa(
                    decisions[first], decisions[second]
                ),
                "dice_positive_agreement": (
                    2 * shared_positive / (first_positive + second_positive)
                    if first_positive + second_positive
                    else 1.0
                ),
                "jaccard_annotated": (
                    shared_positive / positive_union
                    if positive_union
                    else 1.0
                ),
            }
        )

    participant_summaries = [
        {
            "participant": participant,
            "annotated_subwords": sum(decisions[participant]),
            "annotation_rate": statistics.fmean(decisions[participant]),
        }
        for participant in selected_ids
    ]

    return {
        "participants": selected_ids,
        "participant_count": rater_count,
        "question_count": len(questions),
        "binary_items_per_participant": item_count,
        "annotated_rate": positive_rate,
        "observed_agreement": observed,
        "expected_agreement": expected,
        "fleiss_kappa": fleiss_kappa,
        "uniform_prior_expected_agreement": uniform_expected,
        "free_marginal_kappa": free_marginal_kappa,
        "krippendorff_alpha_nominal": krippendorff_alpha,
        "participant_summaries": participant_summaries,
        "mean_pairwise_cohens_kappa": statistics.fmean(
            pair["cohens_kappa"] for pair in pairwise
        ),
        "mean_pairwise_dice_positive_agreement": statistics.fmean(
            pair["dice_positive_agreement"] for pair in pairwise
        ),
        "mean_pairwise_jaccard_annotated": statistics.fmean(
            pair["jaccard_annotated"] for pair in pairwise
        ),
        "pairwise": pairwise,
    }


def target_speaker_result(responses, target_speaker, selected_ids=None):
    cohort = sorted(
        selected_ids
        if selected_ids is not None
        else [
            participant
            for participant, response in responses.items()
            if target_speaker in response["audio_speaker_ids"]
        ]
    )
    donor = target_speaker if target_speaker in cohort else None
    listeners = [participant for participant in cohort if participant != donor]

    if len(listeners) >= 2:
        among_listeners = {
            "status": "available",
            **calculate(responses, listeners),
        }
    else:
        among_listeners = {
            "status": "insufficient_listeners",
            "required_listener_count": 2,
            "available_listener_count": len(listeners),
        }

    if donor and listeners:
        combined = calculate(responses, [donor, *listeners])
        donor_pairs = [
            {
                "listener": (
                    pair["participant_2"]
                    if pair["participant_1"] == donor
                    else pair["participant_1"]
                ),
                **{
                    key: value
                    for key, value in pair.items()
                    if key not in ("participant_1", "participant_2")
                },
            }
            for pair in combined["pairwise"]
            if donor in (pair["participant_1"], pair["participant_2"])
        ]
        between_donor_and_listeners = {
            "status": "available",
            "voice_donor": donor,
            "listener_count": len(listeners),
            "mean_observed_agreement": statistics.fmean(
                pair["observed_agreement"] for pair in donor_pairs
            ),
            "mean_cohens_kappa": statistics.fmean(
                pair["cohens_kappa"] for pair in donor_pairs
            ),
            "mean_dice_positive_agreement": statistics.fmean(
                pair["dice_positive_agreement"] for pair in donor_pairs
            ),
            "mean_jaccard_annotated": statistics.fmean(
                pair["jaccard_annotated"] for pair in donor_pairs
            ),
            "pairwise": donor_pairs,
        }
    else:
        between_donor_and_listeners = {
            "status": "insufficient_listeners",
            "voice_donor": donor,
            "available_listener_count": len(listeners),
        }

    return {
        "TAR_VOICE": target_speaker,
        "voice_donor": donor,
        "listeners": listeners,
        "listener_count": len(listeners),
        "agreement_among_listeners": among_listeners,
        "agreement_between_voice_donor_and_listeners": (
            between_donor_and_listeners
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--participants",
        nargs="+",
        help="Prolific IDs to include; overrides --target-speaker",
    )
    parser.add_argument(
        "--target-speaker",
        help="Generate only this target voice; default: generate every target voice",
    )
    args = parser.parse_args()

    responses = load_responses()
    missing = sorted(set(args.participants or []) - set(responses))
    if missing:
        parser.error(f"Response data not found for: {', '.join(missing)}")

    if args.participants and not args.target_speaker:
        parser.error("--participants requires --target-speaker")

    target_speakers = (
        [args.target_speaker]
        if args.target_speaker
        else sorted(
            participant
            for participant, response in responses.items()
            if participant in response["audio_speaker_ids"]
        )
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    old_output = OUTPUT_DIR / "interannotator_agreement.json"
    if old_output.exists():
        old_output.unlink()

    for target_speaker in target_speakers:
        result = target_speaker_result(
            responses,
            target_speaker,
            args.participants,
        )
        output_file = (
            OUTPUT_DIR
            / f"interannotator_agreement_{target_speaker}.json"
        )
        output_file.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(
            f"{target_speaker}: {result['listener_count']} listener(s) -> "
            f"{output_file}"
        )


if __name__ == "__main__":
    main()
