# Delay Lama Everything

Play any MIDI file through Delay Lama.

[midis2jam2](https://github.com/wyskoj/midis2jam2) plays the file and animates
its 3D band as usual. Any instrument you pick becomes a Delay Lama instead:
its notes are sung by the Delay Lama vocal synth from
[delalalalay-lama](https://github.com/Merken19/delalalalay-lama), shaped to
imitate that instrument, and a monk window named after the instrument sings
along. A choir of monks sings the chords. While the file plays, a mixer
window mutes, solos or turns up or down any channel, sung or not. Its
**Delay Lama** switch flips at any moment between the monks and midis2jam2's
own sound for the sung channels (never both at once). An **Add Delay Lama**
button opens extra Delay Lama standalone instances so you can jam along by
hand. There is no recording.

> **Status (2026-11-08)**: everything above works on Windows and ships as
> one zip (`tools/package/`). What is left for v1 is in
> [docs/ROADMAP.md](docs/ROADMAP.md): tuning the remaining instrument
> families, two monk-window changes, the fork, and the user's checks.

## How it fits together

```text
 midis2jam2 launcher (Compose UI)            pick file and Delay Lama channels:
        │                                     choir size, imitation, level
        ▼
 midis2jam2 performance (jMonkeyEngine) ──3D band (sung channels hidden)──▶ screen
        │  sequencer events
        ▼
   Delay Lama router (MidiDevice wrapper)       ◀── mixer window: levels, Delay Lama switch
        ├── other channels ──────────▶ Gervill (Java synth) ───────────────▶ speakers
        └── sung channels ──pipe─────▶ DelayLamaVoice.exe  (one per channel)
                                         choir of monk synths ─────────────▶ speakers
                                         monk window, always on top ───────▶ screen

 "Add Delay Lama" button ─────────────▶ DelayLamaStandalone.exe (free play, not tied to the file)
```

- **midis2jam2 fork**: reads and plays the file, draws the band, and sends
  the chosen channels to Delay Lama instead of Gervill.
- **DelayLamaVoice.exe** (built from the delalalalay-lama sources): one
  process per sung channel. It sings the channel through a choir of monk
  synths, shapes each note with an *instrument imitation profile*
  ([docs/IMITATION.md](docs/IMITATION.md)), and shows the monks.
- **DelayLamaStandalone.exe** (existing): opened by **Add Delay Lama** for
  playing by hand.

Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Repository layout

| Path | Contents |
| --- | --- |
| `README.md` | This overview |
| `CLAUDE.md` | Working guidance for coding sessions, with the build commands |
| `docs/ROADMAP.md` | What is done, what is left for v1, and a log |
| `docs/DECISIONS.md` | Decisions, and open questions with proposals |
| `docs/ARCHITECTURE.md` | Components, pipe protocol, timing |
| `docs/IMITATION.md` | How Delay Lama imitates each instrument, and how to tune it |
| `docs/CODEBASE_NOTES.md` | Facts about both upstream codebases, with file references |
| `profiles/imitation.json` | The imitation profiles and the program map |
| `tests/midi/` | Test MIDI files and the play-check list |
| `renders/` | WAV renders for ear checks, and the tuning tools |
| `tools/` | Package script, profile expander, test-file generator, listening website |
| `external/midis2jam2/` | Clone of wyskoj/midis2jam2 (GPL-3.0), branch `delay-lama`; to be the fork |
| `external/delalalalay-lama/` | Clone of Merken19/delalalalay-lama (MIT code, freeware artwork), branch `voice-helper` |

## Requirements (Windows)

- Windows 10 or 11, x64.
- To run: the zip from `tools/package/` brings its own Java runtime.
- To build: **JDK 21** and the Android SDK for midis2jam2 (the JDK on
  `PATH` here is 17, so set `JAVA_HOME`), and Visual Studio 2022 (Desktop
  C++) with CMake 3.29 for the native parts. The commands are in
  [CLAUDE.md](CLAUDE.md#build-and-run).

## Licensing

- midis2jam2 is **GPL-3.0**, so our modified midis2jam2 must stay GPL-3.0 if
  it is distributed, with its source.
- The Delay Lama standalone code is MIT, and its vocal engine is derived from
  MIT-licensed [MonkSynth](https://github.com/JonET/monksynth). MIT code can
  be combined with GPL code.
- The Delay Lama artwork (`Resources/*.png`) and manual are AudioNerdz'
  2002–2004 freeware. They are **not relicensed**: they may be distributed
  freely with all original files, but not sold or used in commercial
  promotion.
- This project is not affiliated with AudioNerdz or the midis2jam2 authors.
