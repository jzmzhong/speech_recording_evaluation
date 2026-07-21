# Stage 2 Accent Evaluation

## Run locally

From the parent directory:

```bash
python3 -m http.server 1234 --directory stage_2_accent_evaluation
```

### Local links

Own-voice evaluation (`testparticipant` evaluates their own voice):

- [Full mode](http://localhost:1234/?PROLIFIC_PID=testparticipant)
- [Debug mode](http://localhost:1234/?PROLIFIC_PID=testparticipant&debug=1)

Target-speaker evaluation (`testevaluator` evaluates `testparticipant`):

- [Full mode](http://localhost:1234/?PROLIFIC_PID=testevaluator&TAR_SPK=testparticipant)
- [Debug mode](http://localhost:1234/?PROLIFIC_PID=testevaluator&TAR_SPK=testparticipant&debug=1)

Preview:

- [Random one-question preview](http://localhost:1234/?preview=question)

## Online links

The deployed study is hosted on [sweb](https://computing.help.inf.ed.ac.uk/sweb), provided by School of Informatics, University of Edinburgh.

Own-voice evaluation:

- [Full mode](https://sweb.inf.ed.ac.uk/~s2526235/listening_tests/202607_accent_evaluation/stage_2_accent_evaluation/?PROLIFIC_PID=testparticipant)
- [Debug mode](https://sweb.inf.ed.ac.uk/~s2526235/listening_tests/202607_accent_evaluation/stage_2_accent_evaluation/?PROLIFIC_PID=testparticipant&debug=1)

Target-speaker evaluation:

- [Full mode](https://sweb.inf.ed.ac.uk/~s2526235/listening_tests/202607_accent_evaluation/stage_2_accent_evaluation/?PROLIFIC_PID=testevaluator&TAR_SPK=testparticipant)
- [Debug mode](https://sweb.inf.ed.ac.uk/~s2526235/listening_tests/202607_accent_evaluation/stage_2_accent_evaluation/?PROLIFIC_PID=testevaluator&TAR_SPK=testparticipant&debug=1)

Preview:

- [Random one-question preview](https://sweb.inf.ed.ac.uk/~s2526235/listening_tests/202607_accent_evaluation/stage_2_accent_evaluation/?preview=question)

## Data files

- Segmented utterances: [`data/utterances_segmented.json`](data/utterances_segmented.json)
- Survey configuration and instructions: [`data/content.json`](data/content.json)
- Audio directory: [`data/wav/`](data/wav/)
- Survey responses upload handler: [`save-responses.cgi`](save-responses.cgi)

Audio paths use the resolved speaker ID, which comes from an approved `PROLIFIC_PID` or from `TAR_SPK`:

```text
# recording as reference speech
data/wav/<SPEAKER_ID>/<SPEAKER_ID>_<UTTERANCE_ID>.wav
# TTS generation as candidate speech
data/wav/<SPEAKER_ID>/cloned_<SPEAKER_ID>_<UTTERANCE_ID>_ref_<REFERENCE_UTTERANCE_ID>_<TTS_SYSTEM>.wav
```
