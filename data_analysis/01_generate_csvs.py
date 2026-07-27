#!/usr/bin/env python3
"""Create Stage 2 rating, annotation, and demographics CSV files."""

import argparse
import csv
import json
import statistics
from pathlib import Path


HERE = Path(__file__).resolve().parent
EVALUATION_DIR = HERE / "jsons" / "participant_data_evaluation"
RECORDING_DIR = HERE / "jsons" / "participant_data_recording"
OUTPUT_DIR = HERE / "results"
TASK = "speaker_and_accent_similarity"
ATTENTION_TASK = "attention_check"
ATTENTION_COLUMNS = [
    "attention_identical_audio",
    "attention_testparticipant_reference_target_candidate",
]


def stimulus_sort_key(stimulus):
    prefix, separator, number = stimulus.rpartition("_")
    return (prefix, int(number)) if separator and number.isdigit() else (stimulus, 0)


def read_participants(target_speaker=None):
    participants = {}
    for path in sorted(EVALUATION_DIR.rglob("*.json")):
        response = json.loads(path.read_text(encoding="utf-8"))
        participant_id = response.get("participant", {}).get(
            "prolific_pid",
            response.get("participant", {}).get("participant_id", path.stem),
        )
        experimental = {
            trial["question_id"]: trial
            for trial in response.get("data", [])
            if trial.get("task") == TASK
        }
        attention = {
            f"attention_{trial['attention_check_type']}": trial
            for trial in response.get("data", [])
            if trial.get("task") == ATTENTION_TASK
        }
        audio_speakers = {
            trial.get("audio_speaker_id")
            for trial in experimental.values()
            if trial.get("audio_speaker_id")
        }
        if target_speaker and target_speaker not in audio_speakers:
            continue
        raw_target = response.get("participant", {}).get("target_speaker", "")
        resolved_target = raw_target or (
            next(iter(audio_speakers)) if len(audio_speakers) == 1 else ""
        )
        background = next(
            (
                trial.get("response", {})
                for trial in response.get("data", [])
                if trial.get("task") == "background_questions"
            ),
            {},
        )
        feedback = next(
            (
                trial
                for trial in response.get("data", [])
                if trial.get("task") == "final_task_feedback"
            ),
            {},
        )
        if participant_id in participants:
            raise ValueError(f"More than one evaluation file found for {participant_id}")
        participants[participant_id] = {
            "target_speaker": resolved_target,
            "demographics": background,
            "feedback": feedback,
            "experimental": experimental,
            "attention": attention,
        }

    if not participants:
        raise ValueError(f"No evaluation files found below {EVALUATION_DIR}")

    for path in sorted(RECORDING_DIR.rglob("*.json")):
        response = json.loads(path.read_text(encoding="utf-8"))
        participant_id = response.get("participant", {}).get(
            "prolific_pid",
            response.get("participant", {}).get("participant_id", path.stem),
        )
        if participant_id not in participants:
            continue
        background = next(
            (
                trial.get("response", {})
                for trial in response.get("data", [])
                if trial.get("task") == "background_questions"
            ),
            {},
        )
        if background:
            participants[participant_id]["demographics"] = background
    return participants


def all_stimuli(participants):
    return sorted(
        {
            stimulus
            for participant in participants.values()
            for stimulus in participant["experimental"]
        },
        key=stimulus_sort_key,
    )


def rating_value(trial, field):
    value = trial.get(field)
    if value in (None, ""):
        value = trial.get("response", {}).get(field)
    return float(value) if value not in (None, "") else None


def annotation_value(trial):
    value = trial.get("annotation")
    if value in (None, ""):
        indices = [
            key.removeprefix("accent_clue_")
            for key in trial.get("response", {})
            if key.startswith("accent_clue_")
        ]
        value = "|".join(sorted(indices, key=int))
    return str(value or "")


def write_rating_table(participants, field, filename, include_target=False):
    stimuli = all_stimuli(participants)
    identity = ["prolific_pid", *(["TAR_SPK"] if include_target else [])]
    columns = [
        *identity,
        *ATTENTION_COLUMNS,
        *stimuli,
        "mean",
        "std_dev",
        "min",
        "max",
        "n",
    ]
    with (OUTPUT_DIR / filename).open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        for participant_id, participant in sorted(participants.items()):
            row = {"prolific_pid": participant_id}
            if include_target:
                row["TAR_SPK"] = participant["target_speaker"]
            ratings = []
            for column in ATTENTION_COLUMNS:
                value = rating_value(participant["attention"].get(column, {}), field)
                row[column] = "" if value is None else int(value)
            for stimulus in stimuli:
                value = rating_value(
                    participant["experimental"].get(stimulus, {}), field
                )
                row[stimulus] = "" if value is None else int(value)
                if value is not None:
                    ratings.append(value)
            row.update(
                mean=statistics.fmean(ratings) if ratings else "",
                std_dev=statistics.stdev(ratings) if len(ratings) > 1 else "",
                min=min(ratings) if ratings else "",
                max=max(ratings) if ratings else "",
                n=len(ratings),
            )
            writer.writerow(row)


def write_annotations(participants):
    stimuli = all_stimuli(participants)
    columns = [
        "prolific_pid",
        "TAR_SPK",
        *ATTENTION_COLUMNS,
        *stimuli,
        "mean",
        "std_dev",
        "min",
        "max",
        "n",
    ]
    with (OUTPUT_DIR / "accent_clues_annotations.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        for participant_id, participant in sorted(participants.items()):
            row = {
                "prolific_pid": participant_id,
                "TAR_SPK": participant["target_speaker"],
            }
            for column in ATTENTION_COLUMNS:
                row[column] = annotation_value(
                    participant["attention"].get(column, {})
                )
            counts = []
            for stimulus in stimuli:
                annotation = annotation_value(
                    participant["experimental"].get(stimulus, {})
                )
                row[stimulus] = annotation
                counts.append(0 if not annotation else len(annotation.split("|")))
            row.update(
                mean=statistics.fmean(counts),
                std_dev=statistics.stdev(counts),
                min=min(counts),
                max=max(counts),
                n=len(counts),
            )
            writer.writerow(row)


def write_demographics(participants):
    demographic_columns = [
        "age",
        "gender",
        "ethnicity",
        "first_native_language",
        "other_languages",
        "english_accent_description",
        "current_area_residence",
        "area_most_time_spent_before_adulthood",
        "area_most_time_spent_after_adulthood",
        "other_areas_stayed",
        "recording_device",
        "recording_device_detail",
    ]
    columns = ["prolific_pid", "TAR_SPK", *demographic_columns]
    with (OUTPUT_DIR / "demographics.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        for participant_id, participant in sorted(participants.items()):
            writer.writerow(
                {
                    "prolific_pid": participant_id,
                    "TAR_SPK": participant["target_speaker"],
                    **{
                        column: participant["demographics"].get(column, "")
                        for column in demographic_columns
                    },
                }
            )


def write_post_survey_feedback(participants):
    """Write the mandatory final task feedback fields for each participant."""
    columns = [
        "prolific_pid",
        "TAR_SPK",
        "similarity_task_difficulty",
        "annotation_task_difficulty",
        "task_comments",
    ]
    with (OUTPUT_DIR / "post_survey_feedback.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        for participant_id, participant in sorted(participants.items()):
            feedback = participant["feedback"]
            response = feedback.get("response", {})
            writer.writerow(
                {
                    "prolific_pid": participant_id,
                    "TAR_SPK": participant["target_speaker"],
                    "similarity_task_difficulty": feedback.get(
                        "similarity_task_difficulty",
                        response.get("similarity_task_difficulty", ""),
                    ),
                    "annotation_task_difficulty": feedback.get(
                        "annotation_task_difficulty",
                        response.get("annotation_task_difficulty", ""),
                    ),
                    "task_comments": feedback.get(
                        "task_comments",
                        response.get("task_comments", ""),
                    ),
                }
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target-speaker",
        help="Optionally restrict generated CSVs to one audio speaker",
    )
    args = parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    participants = read_participants(args.target_speaker)
    write_rating_table(
        participants,
        "accent_rating",
        "accent_similarity_ratings.csv",
        include_target=True,
    )
    write_rating_table(
        participants,
        "speaker_rating",
        "speaker_similarity_ratings.csv",
    )
    write_annotations(participants)
    write_demographics(participants)
    write_post_survey_feedback(participants)
    print(f"Wrote five CSV files for {len(participants)} participants to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
