# Two-Stage Accent Evaluation Study

This repository contains a two-stage jsPsych study for collecting speech recordings, evaluating and annotating percieved speaker and accent similarity between natural and cloned speech.

## Study workflow

1. **Stage 1 — Voice recording:** participants record 34 prompted utterances and provide demographic information.
2. **Audio preparation:** recordings are converted, processed, and used to generate cloned candidate speech.
3. **Stage 2 — Accent evaluation:** listeners compare reference and candidate recordings, rate speaker/accent similarity, and annotate perceived accent clues.
4. **Analysis:** response JSON files are collected for downstream analysis.

## Project structure

| Directory | Purpose |
|---|---|
| [`stage_1_prolific_recording/`](stage_1_prolific_recording/) | Stage 1 recording website and upload backend |
| [`stage_2_accent_evaluation/`](stage_2_accent_evaluation/) | Stage 2 listening, rating, and annotation website |
<!-- | [`data_processing/`](data_processing/) | Raw recordings, converted audio, segmentation files, and processing scripts |
| [`data_analysis/`](data_analysis/) | Collected evaluation responses and analysis inputs | -->

See the stage-specific instructions:

- [Stage 1 README](stage_1_prolific_recording/README.md)
- [Stage 2 README](stage_2_accent_evaluation/README.md)

## Run locally

Run either website from this repository’s root directory.

Stage 1:

```bash
python3 -m http.server 1234 --directory stage_1_prolific_recording
```

- [Stage 1 full mode](http://localhost:1234/)
- [Stage 1 debug mode](http://localhost:1234/?debug=1)

Stage 2:

```bash
python3 -m http.server 1234 --directory stage_2_accent_evaluation
```

- [Stage 2 own-voice mode](http://localhost:1234/?PROLIFIC_PID=testparticipant)
- [Stage 2 target-speaker mode](http://localhost:1234/?PROLIFIC_PID=testevaluator&TAR_SPK=testparticipant)
- [Stage 2 debug mode](http://localhost:1234/?PROLIFIC_PID=testparticipant&debug=1)
- [Stage 2 question preview](http://localhost:1234/?preview=question)

## Prolific parameters

Both stages accept standard Prolific URL parameters:

```text
PROLIFIC_PID=<participant ID>
STUDY_ID=<study ID>
SESSION_ID=<session ID>
```

Stage 2 also accepts `TAR_SPK=<speaker ID>`. An approved `PROLIFIC_PID` loads that participant’s own speech; otherwise, `TAR_SPK` selects the speech being evaluated.

## Online studies

- [Stage 1 recording study](https://sweb.inf.ed.ac.uk/~s2526235/listening_tests/202607_accent_evaluation/stage_1_prolific_recording/)
- [Stage 2 accent evaluation](https://sweb.inf.ed.ac.uk/~s2526235/listening_tests/202607_accent_evaluation/stage_2_accent_evaluation/)
