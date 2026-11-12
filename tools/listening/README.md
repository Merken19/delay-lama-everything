# Listening tests

A small local website for A/B listening tests on the WAVs in `renders/`.
It is a development tool and is never packaged. It needs only Python 3.11
and works offline.

```powershell
py tools\listening\serve.py          # then open http://127.0.0.1:8740/
```

Options: `--port N`, `--renders <folder>` (default: the repo's `renders/`)
and `--open` to open your browser. The server listens on `127.0.0.1` only,
serves only `.wav` files from the renders folder and accepts saves only
from its own pages. Ctrl+C stops it. If the renders folder doesn't exist,
it tells you and exits; run a render script first.

## Using it

- **Index** (`/`) lists the tests that still need an answer, in folders that
  have a `listening.json`, grouped by their top folder. A skip counts as an
  answer. Sets with a manifest problem show here too, and the problem is
  printed at start. **Show all** lists every set, answered tests and
  folders without a manifest included.
- **Comparison page**: the question, each clip with its description, and a
  player. All clips of a test play in sync, so switching keeps your place.
  - `1`–`9`, `0` (10th) or `↑`/`↓` switch clip; `Space` plays or pauses.
  - `←`/`→` seek 2 s (`Shift`: 0.5 s); `Home` goes back to the start or
    the loop start.
  - `L` turns the loop on or off; `[` and `]` set its start and end at the
    playhead. You can also drag on the waveform to set a loop, or click to
    seek.
- **Blind mode** (a checkbox): candidates are shuffled and shown as A, B,
  C; references keep their names. Names are revealed when you save or skip,
  and "New blind round" shuffles again. A save after the reveal counts as
  sighted.
- **Answers**: pick from the test's questions, set a confidence (low,
  medium, high), add a note, then **Save** or **Skip**. Every save is kept,
  and earlier answers show on the page.

Show all and blind mode are remembered per browser.

## Where answers go

Next to the manifest (or the WAVs, for a folder without one):

- `answers.json`: the data. `tests.<test id>` is a list of entries, oldest
  first; the last one is current.
- `answers.md`: a readable summary, rewritten on every save. Don't edit it.

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

`status` is `answered` or `skipped`. `choice` is a choice id: a list for a
multi-select question, `null` when left blank. `label` copies the choice
text, so the entry still reads right if the manifest changes. `letters` and
`letter` appear only in blind answers.

## Writing a manifest (`listening.json`)

Have your render script write a `listening.json` next to its WAVs, in a
folder under `renders/`. File paths are relative to that folder and may
point into subfolders, never outside `renders/`.

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
| `format` | Always `1`. |
| `tests[].id` | Unique in the file; answers are stored under it. |
| `tests[].blind` | `false` turns blind mode off for a test whose question needs the names. Default `true`. |
| `clips[].file` | The WAV. Required. |
| `clips[].start`, `end` | Optional seconds: the clip is that part of the file, so one long render can give several clips. |
| `clips[].id` | Optional; defaults to the file name without extension. |
| `clips[].label`, `desc` | Name and one-line description, hidden in blind mode. |
| `clips[].group` | Optional heading. Clips show grouped, in order of first appearance ("Alone", "In the band"). |
| `clips[].condition` | What the clip is a version of. Clips that share a condition (one candidate alone and in the band) get the same blind letter. Defaults to the clip id. |
| `clips[].reference` | `true` for the reference (Gervill): never shuffled or hidden. |
| `questions` | Optional. Without it you get one "Which is best?" question over the non-reference conditions, plus "None of them / can't tell". |
| `questions[].multi` | `true` for tick-all-that-apply. |
| `choices[].condition` | Ties a choice to a condition, so blind mode shows that clip's letter instead of the label. |

Shorter clips are padded with silence to the longest, so keep the clips of
one test the same length when switching matters. Leave out `all.wav` files
(concatenations of the other clips).

A folder with WAVs that no manifest uses becomes one test that lists its
WAVs (except `all.wav`) with a generic "Which is best?" question.
