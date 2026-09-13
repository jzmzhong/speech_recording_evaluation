#!/usr/bin/env python3
"""Create the interactive Stage 2 annotation viewer and package its WAVs."""

import argparse
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent

# The shared generator's filename starts with a number, so it cannot be imported
# with a regular Python import statement.
CSV_GENERATOR_PATH = HERE / "01_generate_csvs.py"
CSV_GENERATOR_SPEC = importlib.util.spec_from_file_location(
    "generate_csvs", CSV_GENERATOR_PATH
)
if CSV_GENERATOR_SPEC is None or CSV_GENERATOR_SPEC.loader is None:
    raise ImportError(f"Could not load {CSV_GENERATOR_PATH}")
CSV_GENERATOR = importlib.util.module_from_spec(CSV_GENERATOR_SPEC)
CSV_GENERATOR_SPEC.loader.exec_module(CSV_GENERATOR)

OUTPUT_DIR = CSV_GENERATOR.OUTPUT_DIR
ATTENTION_COLUMNS = CSV_GENERATOR.ATTENTION_COLUMNS
read_participants = CSV_GENERATOR.read_participants
evaluated_participants = CSV_GENERATOR.evaluated_participants
annotation_value = CSV_GENERATOR.annotation_value
all_stimuli = CSV_GENERATOR.all_stimuli

WAV_SOURCE_DIR = HERE.parent / "stage_2_accent_evaluation" / "data" / "wav"
DEFAULT_TARGET_SPEAKER = "642b3aab1e4144843eb82d33"


def write_annotation_viewer(participants, target_speaker):
    """Create one interactive page comparing all participants by utterance."""
    questions = []
    question_columns = [*ATTENTION_COLUMNS, *all_stimuli(participants)]

    for column in question_columns:
        trial_group = (
            "attention" if column in ATTENTION_COLUMNS else "experimental"
        )
        trials = {
            participant_id: participant[trial_group].get(column, {})
            for participant_id, participant in sorted(participants.items())
        }
        example = next((trial for trial in trials.values() if trial), {})
        audio = {}
        for participant_id, participant in sorted(participants.items()):
            if participant_id != participant["target_speaker"]:
                continue
            donor_trial = participant[trial_group].get(column, {})
            donor_audio = {}
            for field, label in (
                ("reference_speech", "reference"),
                ("candidate_speech", "candidate"),
            ):
                filename = donor_trial.get(field, "")
                source = (
                    WAV_SOURCE_DIR
                    / participant["target_speaker"]
                    / filename
                )
                if filename and not source.is_file():
                    matches = list(WAV_SOURCE_DIR.glob(f"*/{filename}"))
                    if len(matches) == 1:
                        source = matches[0]
                if not filename or not source.is_file():
                    donor_audio[label] = ""
                    continue
                donor_audio[label] = {
                    "directory": source.parent.name,
                    "filename": filename,
                }
            audio[participant["target_speaker"]] = donor_audio

        questions.append(
            {
                "id": column,
                "label": (
                    f"{example.get('question_id', column)} "
                    f"{example.get('attention_check_type', 'attention_check')}"
                    if trial_group == "attention"
                    else example.get("trial_id", column)
                ),
                "segments": example.get("segmented_text", "").split("|"),
                "audio": audio,
                "annotations": {
                    participant_id: annotation_value(trial)
                    for participant_id, trial in trials.items()
                },
            }
        )

    embedded = json.dumps(
        {
            "participants": sorted(participants),
            "participantTargets": {
                participant_id: participant["target_speaker"]
                for participant_id, participant in participants.items()
            },
            "defaultTargetSpeaker": target_speaker,
            "questions": questions,
        },
        ensure_ascii=False,
    ).replace("</", "<\\/")

    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Accent-clue annotations by participant</title>
<style>
:root{{--bg:#f7f8fb;--panel:#fff;--text:#20242c;--muted:#5e6675;--line:#d9dee8;--accent:#136f63;--selected:#ffd43b;--word-space:.55em}}
*{{box-sizing:border-box}}html,body{{min-height:100%;background:var(--bg);color:var(--text)}}body{{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}main{{max-width:960px;margin:auto;padding:32px 24px 48px}}.page-header{{display:flex;align-items:end;justify-content:space-between;gap:24px;margin-bottom:24px}}h1{{margin:0;font-size:1.8rem}}.control{{display:flex;align-items:center;gap:10px;color:var(--muted);font-weight:600}}select{{min-width:230px;font:inherit;padding:9px 34px 9px 12px;border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--text)}}.participant{{margin-top:16px;padding:20px;background:var(--panel);border:1px solid var(--line);border-radius:12px;box-shadow:0 1px 2px rgba(32,36,44,.04)}}.participant-header{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px}}.participant h2{{margin:0;font-size:1rem;font-weight:700;overflow-wrap:anywhere}}.annotation-count{{flex:0 0 auto;padding:4px 9px;border-radius:999px;background:#eef7f4;color:var(--accent);font-size:.82rem;font-weight:600}}.annotation-sentence{{display:flex;flex-wrap:wrap;align-items:center;gap:1px;padding:20px;border:1px solid var(--line);border-radius:8px;background:#fbfcfe}}.annotation-token{{display:inline-block;padding:6px 0;border-radius:5px;color:var(--text);font-size:1.3rem;user-select:none}}.annotation-token.selected{{background:var(--selected);color:#000}}.annotation-space{{display:inline-block;flex:0 0 auto;width:var(--word-space);overflow:hidden;font-size:1.3rem;user-select:none}}.annotation-unselectable{{display:inline-block;padding:6px 0;color:var(--text);font-size:1.3rem;user-select:none}}.annotation-boundary{{align-self:center;color:#a4a9b2;font-size:2rem;line-height:1;pointer-events:none;user-select:none}}.empty{{color:var(--muted)}}@media(max-width:680px){{main{{padding:20px 12px 36px}}.page-header{{align-items:stretch;flex-direction:column;gap:14px}}.control{{align-items:stretch;flex-direction:column;gap:6px}}select{{width:100%}}.participant{{padding:14px}}.annotation-sentence{{padding:14px}}}}
.target-field{{display:flex;align-items:center;gap:8px;margin:0 0 22px;color:var(--muted)}}.target-field code{{padding:5px 9px;border:1px solid var(--line);border-radius:6px;background:var(--panel);color:var(--text)}}.role-label{{display:inline-block;margin-left:8px;padding:3px 8px;border-radius:999px;background:#eef7f4;color:var(--accent);font-size:.78rem;font-weight:600}}.participant.voice-donor{{border-color:var(--accent);box-shadow:0 0 0 2px rgba(19,111,99,.10)}}.participant.selected-listener{{border-color:#8b5cf6;background:#fdfbff;box-shadow:0 0 0 2px rgba(139,92,246,.12)}}.participant.selected-listener h2{{font-weight:900}}.participant.selected-listener .role-label{{background:#f0eaff;color:#6842c2}}.listeners-heading{{margin:26px 0 4px;color:var(--muted);font-size:1rem}}.selected-listeners-heading{{margin-top:32px;color:#6842c2}}
.audio-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-bottom:22px}}.audio-card{{padding:16px;background:var(--panel);border:1px solid var(--line);border-radius:10px}}.audio-card h2{{margin:0 0 10px;font-size:1rem}}.audio-card audio{{display:block;width:100%}}.audio-missing{{margin:8px 0 0;color:var(--muted);font-size:.85rem}}@media(max-width:680px){{.audio-grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body><main>
<header class="page-header">
  <h1>Accent-clue annotations</h1>
  <label class="control" for="question"><span>Utterance</span><select id="question"></select></label>
</header>
<p class="target-field"><strong>TAR_SPK</strong><code id="targetSpeaker"></code></p>
<section class="audio-grid" aria-label="Speech recordings">
  <div class="audio-card">
    <h2>Reference speech recording</h2>
    <audio id="referenceAudio" controls preload="metadata"></audio>
    <p class="audio-missing" id="referenceMissing" hidden>Reference audio is unavailable.</p>
  </div>
  <div class="audio-card">
    <h2>Candidate speech recording</h2>
    <audio id="candidateAudio" controls preload="metadata"></audio>
    <p class="audio-missing" id="candidateMissing" hidden>Candidate audio is unavailable.</p>
  </div>
</section>
<div id="participants"></div>
<script>
const data={embedded};
const params=new URLSearchParams(window.location.search);
const targetSpeaker=params.get('TAR_SPK')||data.defaultTargetSpeaker;
const selectedListenerIds=(params.get('LISTENERS')||params.get('listeners')||'').split(/[|,]/).map(value=>value.trim()).filter(Boolean);
const selectedListenerSet=new Set(selectedListenerIds);
const relevantParticipants=data.participants.filter(participant=>data.participantTargets[participant]===targetSpeaker);
const selectedListeners=selectedListenerIds.filter((participant,index)=>participant!==targetSpeaker&&relevantParticipants.includes(participant)&&selectedListenerIds.indexOf(participant)===index);
const otherParticipants=relevantParticipants.filter(participant=>!selectedListenerSet.has(participant)).sort((first,second)=>Number(second===targetSpeaker)-Number(first===targetSpeaker)||first.localeCompare(second));
const orderedParticipants=[...otherParticipants,...selectedListeners];
const selector=document.getElementById('question');
const container=document.getElementById('participants');
const referenceAudio=document.getElementById('referenceAudio');
const candidateAudio=document.getElementById('candidateAudio');
const stageTwoWavBase='../../../../stage_2_accent_evaluation/data/wav';
document.getElementById('targetSpeaker').textContent=targetSpeaker;
const escapeHtml=value=>value.replace(/[&<>"']/g,character=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[character]));
selector.innerHTML=data.questions.map(question=>`<option value="${{question.id}}">${{question.label}}</option>`).join('');
function renderSegment(segment,index,segments,selected){{
  const content=segment.split(/(\\s+)/).map(part=>{{
    if(!part)return '';
    if(/^\\s+$/.test(part))return `<span class="annotation-space" aria-hidden="true">${{'&nbsp;'.repeat(part.length)}}</span>`;
    if(/^[,.!?;:'"“”‘’\\-–—]+$/.test(part))return `<span class="annotation-unselectable">${{escapeHtml(part)}}</span>`;
    return `<span class="annotation-token ${{selected.has(index)?'selected':''}}">${{escapeHtml(part)}}</span>`;
  }}).join('');
  const next=segments[index+1]||'';
  const showBoundary=index<segments.length-1&&segment.length>0&&next.length>0&&!/\\s$/.test(segment)&&!/^\\s/.test(next)&&/^[A-Za-z0-9]/.test(next);
  return content+(showBoundary?'<span class="annotation-boundary" aria-hidden="true">·</span>':'');
}}
function isSelectable(segment){{
  return segment.split(/(\\s+)/).some(part=>part&&!/^\\s+$/.test(part)&&!(/^[,.!?;:'"“”‘’\\-–—]+$/.test(part)));
}}
function render(){{
  const question=data.questions.find(item=>item.id===selector.value);
  const audio=question.audio[targetSpeaker]||{{}};
  for(const [player,missing,file] of [
    [referenceAudio,document.getElementById('referenceMissing'),audio.reference],
    [candidateAudio,document.getElementById('candidateMissing'),audio.candidate]
  ]){{
    const path=file?`${{stageTwoWavBase}}/${{encodeURIComponent(file.directory)}}/${{encodeURIComponent(file.filename)}}`:'';
    player.hidden=!path;
    missing.hidden=Boolean(path);
    if(path&&player.getAttribute('src')!==path){{
      player.src=path;
      player.load();
    }}
    if(!path)player.removeAttribute('src');
  }}
  const selectableCount=question.segments.filter(isSelectable).length;
  const rendered=orderedParticipants.map((participant,position)=>{{
    const selected=new Set((question.annotations[participant]||'').split('|').filter(Boolean).map(Number));
    const sentence=question.segments.map((segment,index)=>renderSegment(segment,index,question.segments,selected)).join('');
    const count=selected.size;
    const isDonor=participant===targetSpeaker;
    const isSelectedListener=selectedListenerSet.has(participant)&&!isDonor;
    const firstListener=participant!==targetSpeaker&&orderedParticipants.slice(0,position).every(item=>item===targetSpeaker);
    const firstSelected=isSelectedListener&&orderedParticipants.slice(0,position).every(item=>!selectedListenerSet.has(item));
    const divider=firstSelected
      ? '<h2 class="listeners-heading selected-listeners-heading">Selected listeners</h2>'
      : (firstListener?'<h2 class="listeners-heading">Other listener annotations</h2>':'');
    const role=isDonor?'Voice donor':(isSelectedListener?'Selected listener':'Listener');
    const classes=['participant',isDonor?'voice-donor':'',isSelectedListener?'selected-listener':''].filter(Boolean).join(' ');
    return `${{divider}}<section class="${{classes}}"><div class="participant-header"><h2>${{participant}}<span class="role-label">${{role}}</span></h2><span class="annotation-count">${{count}}/${{selectableCount}} segments annotated</span></div><div class="annotation-sentence">${{sentence||'<span class="empty">No segmented text available</span>'}}</div></section>`;
  }}).join('');
  const listenerCount=orderedParticipants.filter(participant=>participant!==targetSpeaker).length;
  const emptyListener=listenerCount===0
    ? `<h2 class="listeners-heading">Listener annotations</h2><section class="participant"><div class="participant-header"><h2>Listener<span class="role-label">No responses yet</span></h2><span class="annotation-count">0/${{selectableCount}} segments annotated</span></div><div class="annotation-sentence">${{question.segments.map((segment,index)=>renderSegment(segment,index,question.segments,new Set())).join('')}}</div></section>`
    : '';
  container.innerHTML=rendered+emptyListener;
}}
selector.addEventListener('change',render);render();
</script>
</main></body></html>"""
    (OUTPUT_DIR / "annotation_viewer.html").write_text(document, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target-speaker",
        default=None,
        help="Optionally restrict generated CSVs and HTML data to one audio speaker",
    )
    parser.add_argument(
        "--all-participants",
        action="store_true",
        help="Include every response, ignoring --target-speaker",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    participants = evaluated_participants(
        read_participants(None if args.all_participants else args.target_speaker)
    )

    write_annotation_viewer(
        participants,
        args.target_speaker or DEFAULT_TARGET_SPEAKER,
    )

    print(
        f"Wrote annotation viewer for "
        f"{len(participants)} participants evaluating "
        f"{args.target_speaker or 'all speakers'} "
        f"to {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()
