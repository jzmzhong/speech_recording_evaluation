# Stage 1 Voice Recording

## Run locally

From the parent directory:

```bash
python3 -m http.server 1234 --directory stage_1_prolific_recording
```

Use `localhost` or HTTPS so the browser can request microphone access.

### Local links

- [Full mode](http://localhost:1234/)
- [Debug mode](http://localhost:1234/?debug=1)
- [Full mode with Prolific metadata](http://localhost:1234/?PROLIFIC_PID=testparticipant&STUDY_ID=teststudy&SESSION_ID=testsession)
- [Debug mode with Prolific metadata](http://localhost:1234/?PROLIFIC_PID=testparticipant&STUDY_ID=teststudy&SESSION_ID=testsession&debug=1)

## Online links

The deployed study is hosted on [Edinburgh sweb](https://computing.help.inf.ed.ac.uk/sweb).

- [Full mode](https://sweb.inf.ed.ac.uk/~s2526235/listening_tests/202607_accent_evaluation/stage_1_prolific_recording/)
- [Debug mode](https://sweb.inf.ed.ac.uk/~s2526235/listening_tests/202607_accent_evaluation/stage_1_prolific_recording/?debug=1)
- [Full mode with Prolific metadata](https://sweb.inf.ed.ac.uk/~s2526235/listening_tests/202607_accent_evaluation/stage_1_prolific_recording/?PROLIFIC_PID=testparticipant&STUDY_ID=teststudy&SESSION_ID=testsession)
- [Debug mode with Prolific metadata](https://sweb.inf.ed.ac.uk/~s2526235/listening_tests/202607_accent_evaluation/stage_1_prolific_recording/?PROLIFIC_PID=testparticipant&STUDY_ID=teststudy&SESSION_ID=testsession&debug=1)

## Data files

- Full-study utterances (34): [`data/utterances.json`](data/utterances.json)
- Debug utterances (2): [`data/utterances_debug.json`](data/utterances_debug.json)
- Recording and survey responses upload handler: [`save-recording.cgi`](save-recording.cgi)

Participant recordings and metadata are stored together in a private participant directory:

```text
participant_data/<PARTICIPANT_ID>/
├── recording_<PARTICIPANT_ID>_<TIMESTAMP>.json
├── <PARTICIPANT_ID>_<UTTERANCE_ID>.webm
└── ...
```
