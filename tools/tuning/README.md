# Tuning tools

Scripts for tuning an imitation profile the way `docs/IMITATION.md` §15
describes: write test phrases, measure the monks against Gervill, then build
a listening set for the choices that are left. They are development tools and
are never packaged.

## What you need

- `DelayLamaVoice.exe` built in `external\delalalalay-lama\Windows\build\Release\`
- `java` on `PATH` (the JDK 17 there works) for the Gervill renders
- Python with `numpy` and `scipy`; `matplotlib` only if you draw
  spectrograms with `dl.spectrogram_png`

## The tools

| File | What it does |
| --- | --- |
| `dl.py` | Shared helpers: renders a helper script with `DelayLamaVoice.exe --render`, reads and writes WAVs, tracks pitch, measures band levels, draws spectrograms. |
| `GervillRender.java` | Renders a MIDI file to a 48 kHz WAV with Gervill, the synth midis2jam2 plays through. Run by the phrase modules; an optional third argument is a soundbank. |
| `piano/piano_phrases.py` | The piano family's test phrases, plus the parts every family reuses: the MIDI writer, the Gervill render, and the script builder that turns a phrase and a profile into the lines the router would send. |
| `piano/measure_4c_piano.py` | Measures the piano profile against Gervill (tuning, chords, decay, endings, vowel drift) and writes `measure/measurements.md`. `--quick` measures the tuning on every third note only. |
| `piano/make_4c_piano.py` | Renders the piano listening set: clips matched to Gervill's integrated loudness, a `listening.json` and a `report.md` with the levels. |
| `pipe/pipe_phrases.py`, `measure_4c_pipe.py`, `make_4c_pipe.py` | The same for the flute: shows how a family reuses the piano code and adds the router's `range.shift`. |
| `brass/brass_phrases.py`, `measure_4c_brass.py`, `make_4c_brass.py` | The same for trumpet and sax. Renders with a fresh copy of the helper, so a rebuild can run at the same time. |

To tune a new family, copy a family folder and change its phrases, its
measurements and its candidates.

## Running them

From the top folder:

```powershell
py tools\tuning\piano\measure_4c_piano.py
py tools\tuning\piano\make_4c_piano.py
py tools\listening\serve.py          # then listen at http://127.0.0.1:8740/
```

Everything a script writes goes to `renders\tuning\<family>\`: the MIDI
files in `midi\`, the helper scripts in `scripts\`, the measurements in
`measure\measurements.md`, and the listening set with its `listening.json`
and `report.md`. `renders\` is git-ignored, so you can delete it at any time
and run the scripts again.

Once you have picked a sound, put it in `profiles\imitation.json` and run
midis2jam2's `DelayLamaProfilesTest` (with `--rerun` after a change to the
JSON only).
