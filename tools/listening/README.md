# Listening tests (dev tool)

A local website for A/B listening tests on the WAV renders in `renders/`.
It is a **development tool only**: not part of Delay Lama Everything and
never packaged. Python 3.11 standard library plus plain HTML/CSS/JS, no
installs or CDNs, so it works offline.

```powershell
py tools\listening\serve.py          # then open http://127.0.0.1:8740/
```

Options: `--port N`, `--renders <folder>` (default: the repo's `renders/`),
`--open` (open the default browser). The server binds to `127.0.0.1` only,
serves only `.wav` files from the renders folder, and accepts saves only
from its own pages. Ctrl+C stops it. Manifest problems are printed at start
and shown on the index page.

## Using it

- **Index** (`/`): by default, only the tests that still need an answer
  (no answer saved yet; a skip counts as answered) in folders that have a
  `listening.json`, grouped by their top folder under `renders/`. Sets with a manifest problem are shown
  too. **Show all** (remembered per browser) lists every set, including
  answered tests and folders without a manifest, with the latest answers.
- **Comparison page**: the question, every clip with its description, and a
  player. All clips of a test are decoded with Web Audio and play in sync;
  switching changes only which one you hear, so it keeps the position.
  - `1`–`9`, `0` (10th) or `↑`/`↓` switch clip; `Space` play/pause;
    `←`/`→` seek 2 s (`Shift`: 0.5 s); `Home` back to the start (or loop
    start); `L` loop on/off; `[` / `]` loop start/end at the playhead.
  - Click the waveform to seek, drag on it to set a loop region.
- **Blind mode** (checkbox, remembered per browser): candidates are shuffled
  and shown as letters A, B, C…; references keep their names. Choices tied to
  a clip show the same letters. Names are revealed when you save or skip;
  "New blind round" reshuffles. A save after the reveal counts as sighted.
- **Answers**: the test's multiple-choice questions, confidence
  (low/medium/high), a note, **Save** or **Skip**. Every save is appended;
  previous answers are shown on the page (folded away during a blind round).

## Where answers go

Next to the manifest (or the WAVs, for folders without one):

- `answers.json`: the data. `tests.<test id>` is a list of entries, oldest
  first, the last one current.
- `answers.md`: a readable summary, regenerated on every save (don't edit
  it).

An entry:

```json
{
  "saved": "2026-11-03T23:37:42+01:00",
  "status": "answered",
  "blind": true,
  "letters": { "A": "as_written", "B": "up2", "C": "up1" },
  "answers": [
    { "question": "octave", "text": "Which octave should the monk sing?",
      "choice": "up1", "label": "+1 octave", "letter": "C" }
  ],
  "confidence": "medium",
  "note": "free text"
}
```

`status` is `answered` or `skipped`. `choice` is a choice id (a list for
multi-select questions, `null` when left blank); `label` copies the choice
text so the entry still reads right if the manifest changes. `letters` and
`letter` appear only for blind answers.

## Manifest format (`listening.json`)

Put a `listening.json` in a folder under `renders/`. File paths are relative
to that folder (they may point into subfolders, never outside `renders/`).
Render scripts should write it next to their output.

```json
{
  "format": 1,
  "title": "A/B: Delay Lama vs. Gervill",
  "intro": "Shown on the index and under 'About this set'.",
  "tests": [
    {
      "id": "c01_bass",
      "title": "Bass",
      "question": "Bass line (finger bass, A1-A2): which octave should the monk sing?",
      "notes": "Optional extra line under the question.",
      "blind": true,
      "clips": [
        { "file": "c01_bass/01_gervill_solo.wav", "label": "Gervill",
          "desc": "What midis2jam2 plays, alone", "group": "Alone",
          "condition": "gervill", "reference": true },
        { "file": "c01_bass/02_monk_as_written_solo.wav", "label": "As written",
          "desc": "Delay Lama, as written, alone", "group": "Alone",
          "condition": "as_written" },
        { "file": "p05_range.wav", "start": 10.4, "end": 13.0,
          "label": "A segment of a longer file" }
      ],
      "questions": [
        { "id": "octave", "text": "Which octave should the monk sing?",
          "multi": false,
          "choices": [
            { "id": "as_written", "label": "As written", "condition": "as_written" },
            { "id": "none", "label": "None fit" }
          ] }
      ]
    }
  ]
}
```

| Field | Meaning |
| --- | --- |
| `format` | Always `1` for now. |
| `tests[].id` | Unique in the file; answers are stored under it. |
| `tests[].blind` | `false` turns blind mode off for a test whose question needs the names. Default `true`. |
| `clips[].file` | WAV path. Required. |
| `clips[].start`, `end` | Optional seconds: the clip is that segment of the file. Lets one long render become several switchable clips. |
| `clips[].id` | Optional; default the file stem. |
| `clips[].label`, `desc` | Name and one-line description (hidden in blind mode). |
| `clips[].group` | Optional heading; clips are shown grouped, in order of first appearance (for example "Alone", "In the band"). |
| `clips[].condition` | What the clip is a version of. Clips sharing a condition (the same candidate alone and in the band) get the same blind letter. Default: the clip id. |
| `clips[].reference` | `true` for the reference (Gervill): never shuffled or hidden. |
| `questions` | Optional. Default: one "which is best?" question over the non-reference conditions plus "None of them / can't tell". |
| `questions[].multi` | `true` for tick-all-that-apply. |
| `choices[].condition` | Ties a choice to a condition, so in blind mode it shows that clip's letter instead of the label. |

Clips of different lengths are padded with silence to the longest, so keep
the clips of one test the same length when switching between them matters.
`all.wav` files (concatenations) are best left out.

**Folders without a manifest**: any folder with WAVs that no manifest uses
becomes one test listing its WAVs (except `all.wav`) with a generic "Which
is best?" question.
