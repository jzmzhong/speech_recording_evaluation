#!/usr/bin/env python3
"""Create Stage 2 rating, annotation, and demographics CSV files."""

import argparse
import csv
import json
import statistics
from pathlib import Path


BATCH = "batch_3_australian"
EVAL_BATCHES = ["participant_data_evaluation_own_voice"]
RESULTS_FILE = "results_own_voice"


HERE = Path(__file__).resolve().parent
EVAL_DIRS = [HERE / "jsons" / BATCH / eval_batch for eval_batch in EVAL_BATCHES]
RECORD_DIR = HERE / "jsons" / BATCH / "participant_data_recording"
OUTPUT_DIR = HERE / "results" / BATCH / RESULTS_FILE
TASK = "speaker_and_accent_similarity"
ATTENTION_TASK = "attention_check"
ATTENTION_COLUMNS = [
    # "attention_identical_audio",
    # "attention_testparticipant_reference_target_candidate",
    "attention_cross_speaker_comma_004",
    "attention_cross_speaker_comma_005"
]


def stimulus_sort_key(stimulus):
    prefix, separator, number = stimulus.rpartition("_")
    return (prefix, int(number)) if separator and number.isdigit() else (stimulus, 0)


def read_participants(target_speaker=None):
    participants = {}
    for eval_dir in EVAL_DIRS:
        for path in sorted(eval_dir.rglob("*.json")):
            response = json.loads(path.read_text(encoding="utf-8"))
            participant_id = response.get("participant", {}).get(
                "prolific_pid",
                response.get("participant", {}).get("participant_id", path.stem),
            )
            experimental = {
                trial["trial_id"]: trial
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
                raise ValueError(
                    f"More than one evaluation file found for {participant_id}"
                )
            participants[participant_id] = {
                "evaluated": True,
                "target_speaker": resolved_target,
                "demographics": background,
                "feedback": feedback,
                "experimental": experimental,
                "attention": attention,
            }

    if not participants:
        raise ValueError(f"No evaluation files found below {EVAL_DIRS}")

    # Include participant directories even when their recording JSON has not yet
    # been copied locally. Their demographics row will be completed automatically
    # once the JSON appears in the directory.
    for participant_dir in sorted(path for path in RECORD_DIR.iterdir() if path.is_dir()):
        participant_id = participant_dir.name
        participants.setdefault(
            participant_id,
            {
                "evaluated": False,
                "target_speaker": participant_id,
                "demographics": {},
                "feedback": {},
                "experimental": {},
                "attention": {},
            },
        )

    for path in sorted(RECORD_DIR.rglob("*.json")):
        response = json.loads(path.read_text(encoding="utf-8"))
        participant_id = response.get("participant", {}).get(
            "prolific_pid",
            response.get("participant", {}).get("participant_id", path.stem),
        )
        participant = participants.setdefault(
            participant_id,
            {
                "evaluated": False,
                "target_speaker": participant_id,
                "demographics": {},
                "feedback": {},
                "experimental": {},
                "attention": {},
            },
        )
        background = next(
            (
                trial.get("response", {})
                for trial in response.get("data", [])
                if trial.get("task") == "background_questions"
            ),
            {},
        )
        if background:
            participant["demographics"] = background
    return participants


def evaluated_participants(participants):
    return {
        participant_id: participant
        for participant_id, participant in participants.items()
        if participant["evaluated"]
    }


def all_stimuli(participants):
    return sorted(
        {
            stimulus
            for participant in participants.values()
            for stimulus in participant["experimental"]
        },
        key=stimulus_sort_key,
    )


def trial_suffix(trial_id):
    return trial_id.split("_")[-1]


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
    participants = evaluated_participants(participants)
    stimuli = all_stimuli(participants)
    suffixes = sorted({trial_suffix(stimulus) for stimulus in stimuli})
    identity = ["prolific_pid", *(["TAR_SPK"] if include_target else [])]
    columns = [
        *identity,
        *ATTENTION_COLUMNS,
        *stimuli,
        *(f"mean_{suffix}" for suffix in suffixes),
        *(f"std_dev_{suffix}" for suffix in suffixes),
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
            ratings_by_suffix = {suffix: [] for suffix in suffixes}
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
                    ratings_by_suffix[trial_suffix(stimulus)].append(value)
            for suffix, suffix_ratings in ratings_by_suffix.items():
                row[f"mean_{suffix}"] = (
                    statistics.fmean(suffix_ratings) if suffix_ratings else ""
                )
                row[f"std_dev_{suffix}"] = (
                    statistics.stdev(suffix_ratings)
                    if len(suffix_ratings) > 1
                    else ""
                )
            row.update(
                mean=statistics.fmean(ratings) if ratings else "",
                std_dev=statistics.stdev(ratings) if len(ratings) > 1 else "",
                min=min(ratings) if ratings else "",
                max=max(ratings) if ratings else "",
                n=len(ratings),
            )
            writer.writerow(row)


def mean_std_text(values):
    if not values:
        return ""
    mean = statistics.fmean(values)
    std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
    return f"{mean:.2f}±{std_dev:.2f}"


def annotation_count(trial):
    annotation = annotation_value(trial)
    return 0 if not annotation else len(annotation.split("|"))


def write_summary(participants):
    """Write participant-level mean±SD ratings and annotations by system."""
    participants = evaluated_participants(participants)
    stimuli = all_stimuli(participants)
    suffixes = sorted({trial_suffix(stimulus) for stimulus in stimuli})
    summary_groups = [
        ("accent similarity", lambda trial: rating_value(trial, "accent_rating")),
        ("speaker similarity", lambda trial: rating_value(trial, "speaker_rating")),
        ("accent clue annotations", annotation_count),
    ]

    with (OUTPUT_DIR / "summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.writer(output)
        writer.writerow(
            ["prolific_pid"]
            + [
                similarity_type
                for similarity_type, _ in summary_groups
                for _ in suffixes
            ]
        )
        writer.writerow([""] + suffixes * len(summary_groups))

        for participant_id, participant in sorted(participants.items()):
            row = [participant_id]
            for _, value_function in summary_groups:
                for suffix in suffixes:
                    values = [
                        value
                        for trial_id, trial in participant["experimental"].items()
                        if trial_suffix(trial_id) == suffix
                        if (value := value_function(trial)) is not None
                    ]
                    row.append(mean_std_text(values))
            writer.writerow(row)


def write_annotations(participants):
    participants = evaluated_participants(participants)
    stimuli = all_stimuli(participants)
    suffixes = sorted({trial_suffix(stimulus) for stimulus in stimuli})
    columns = [
        "prolific_pid",
        "TAR_SPK",
        *ATTENTION_COLUMNS,
        *stimuli,
        *(f"mean_{suffix}" for suffix in suffixes),
        *(f"std_dev_{suffix}" for suffix in suffixes),
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
            counts_by_suffix = {suffix: [] for suffix in suffixes}
            for stimulus in stimuli:
                trial = participant["experimental"].get(stimulus, {})
                annotation = annotation_value(trial)
                row[stimulus] = annotation
                count = annotation_count(trial)
                counts.append(count)
                counts_by_suffix[trial_suffix(stimulus)].append(count)
            for suffix, suffix_counts in counts_by_suffix.items():
                row[f"mean_{suffix}"] = statistics.fmean(suffix_counts)
                row[f"std_dev_{suffix}"] = (
                    statistics.stdev(suffix_counts)
                    if len(suffix_counts) > 1
                    else ""
                )
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
    participants = evaluated_participants(participants)
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
        default=None,
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
    write_summary(participants)
    write_annotations(participants)
    write_demographics(participants)
    write_post_survey_feedback(participants)
    evaluation_count = len(evaluated_participants(participants))
    print(
        f"Wrote demographics for {len(participants)} participants and "
        f"six evaluation outputs for {evaluation_count} participants to {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()
