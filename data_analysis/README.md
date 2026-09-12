# Data Analysis

## Source Data

- `./jsons/participant_data_evaluation/` contains ratings \& annotations from both voice donors and stranger-listeners, and the demographics of stranger-listeners.
- `./jsons/participant_data_recording/` contains the demographics of voice donors.
- `../stage_2_accent_evaluation/data/wav/` contains all the processed recordings and generations.

## Processed survey responses

### Ratings, annoations, demographics and post-survey feedbacks

```bash
python3 01_generate_csvs.py
```

- `./results/accent_similarity_ratings.csv`
- `./results/speaker_similarity_ratings.csv`
- `./results/accent_clues_annotations.csv`
- `./results/demographics.csv`
- `./results/post_survey_feedback.csv`

### Interactive annotation demo

```bash
python3 02_generate_annotation_viewer.py
python3 -m http.server 1234
```

View the annotations for one target speaker (e.g. 63d0260e307282309d31e2d1) with:
- [Local]
http://localhost:1234/results/annotation_viewer.html?TAR_SPK=63d0260e307282309d31e2d1
- [Deployed](https://sweb.inf.ed.ac.uk/~s2526235/listening_tests/202607_accent_evaluation/data_analysis/results/annotation_viewer.html?TAR_SPK=63d0260e307282309d31e2d1)

To bold selected listeners and place them in the bottom rows, add their comma-separated Prolific IDs with `LISTENERS`:

```text
http://localhost:1234/results/annotation_viewer.html?TAR_SPK=63d0260e307282309d31e2d1&LISTENERS=listener_id_1,listener_id_2
```

### Agreement scores

# Data analysis scripts

```bash
python3 03_calculate_interannotator_agreement.py
```

- `./results/interannotator_agreement_<TAR_SPK>.json`

Agreement JSONs separately report agreement among listeners and agreement between the voice donor and listeners.

Target speakers/voice donors without listener data yet are marked `insufficient_listeners`.
