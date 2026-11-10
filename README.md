# Delay Lama Everything

Play any MIDI file through Delay Lama.

[midis2jam2](https://github.com/wyskoj/midis2jam2) plays the file and animates
its 3D band as usual. Any instrument you pick becomes a Delay Lama instead:
its notes are sung by the Delay Lama vocal synth from
[delalalalay-lama](https://github.com/Merken19/delalalalay-lama), shaped to
imitate that instrument, and a monk window named after the instrument sings
along. A choir of monks sings the chords. While the file plays, a mixer
window mutes, solos or turns up or down any channel, sung or not. Each sung
channel has its own **Delay Lama** switch there, which flips that channel at
any moment between the monks and midis2jam2's own sound (never both at
once). Every channel Delay Lama can sing is sung until you switch it off in
the panel. An **Add Delay Lama**
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
   Delay Lama router (MidiDevice wrapper)       ◀── mixer window: levels, Delay Lama switches
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
| `external/midis2jam2/` | Clone of wyskoj/midis2jam2 (GPL-3.0), branch `delay-lama`, pushed to the fork Merken19/midis2jam2 |
| `external/delalalalay-lama/` | Clone of Merken19/delalalalay-lama (MIT code, freeware artwork), branch `voice-helper` |

## Building from source (Windows)

The project is three public repositories. This one holds the docs, the
imitation profiles and the tools; the code lives in the other two, which
are cloned into `external/` (git-ignored here, each its own repository):

| Folder | Repository | Branch |
| --- | --- | --- |
| *(top)* | [Merken19/delay-lama-everything](https://github.com/Merken19/delay-lama-everything) | `main` |
| `external/midis2jam2/` | [Merken19/midis2jam2](https://github.com/Merken19/midis2jam2), a fork of [wyskoj/midis2jam2](https://github.com/wyskoj/midis2jam2) | `delay-lama` |
| `external/delalalalay-lama/` | [Merken19/delalalalay-lama](https://github.com/Merken19/delalalalay-lama) | `voice-helper` |

The folder names matter: midis2jam2 looks for the helper at
`external/delalalalay-lama/Windows/build/Release/` and for
`profiles/imitation.json` above its own folder, and the package script
expects both clones under `external/`.

### Prerequisites

- Windows 10 or 11, x64.
- [Git](https://git-scm.com/). Git LFS isn't needed: the only LFS files are
  midis2jam2's Blender sources, which the build doesn't read.
- **Visual Studio 2022** with the *Desktop development with C++* workload
  (it brings the MSVC compiler and the Windows SDK), and **CMake 3.20 or
  newer** (tested with 3.29; the CMake that ships with Visual Studio works).
- **JDK 21**, for example [Azul Zulu 21](https://www.azul.com/downloads/#zulu)
  or Oracle JDK 21. Point `JAVA_HOME` at it; a different JDK on `PATH` is
  fine as long as `JAVA_HOME` is set.
- The **Android SDK**, even for the desktop build (midis2jam2 is a Kotlin
  Multiplatform project and Gradle configures its Android target). Install
  it with [Android Studio](https://developer.android.com/studio) or the
  command-line tools, add *Android SDK Platform 36*, accept the licences
  (`sdkmanager --licenses`) and point `ANDROID_HOME` at it (by default
  `%LOCALAPPDATA%\Android\Sdk`).
- Optional: **Python 3** (the `py` launcher or `python`) for the tools in
  `tools/`. They use only the standard library. One midis2jam2 test runs
  `tools/profiles/expand.py` and is skipped without Python.
- An internet connection for Gradle's first run, which downloads the
  dependencies (several hundred MB).

### 1. Get the sources

```powershell
git clone https://github.com/Merken19/delay-lama-everything.git
cd delay-lama-everything
git clone -b voice-helper https://github.com/Merken19/delalalalay-lama.git external\delalalalay-lama
git clone -b delay-lama -o fork https://github.com/Merken19/midis2jam2.git external\midis2jam2
git -C external\midis2jam2 remote add origin https://github.com/wyskoj/midis2jam2.git
git -C external\midis2jam2 fetch origin
```

The last two lines add upstream midis2jam2 as `origin`. Building and running
don't need it, but the package script does: it writes the GPL source patch
against `origin/master`.

### 2. Build the Delay Lama exes

From `external\delalalalay-lama`, in PowerShell:

```powershell
cmake -S .\Windows -B .\Windows\build -G "Visual Studio 17 2022" -A x64
cmake --build .\Windows\build --config Release --parallel
ctest --test-dir .\Windows\build -C Release --output-on-failure
```

This makes `DelayLamaVoice.exe` (the helper midis2jam2 starts for each sung
channel) and `DelayLamaStandalone.exe`, with the artwork copied to
`Resources\`, in `Windows\build\Release\`. To try the helper on its own:

```powershell
.\Windows\build\Release\DelayLamaVoice.exe --render .\Tests\voice_scripts\chord.txt chord.wav
```

A running helper or standalone locks its exe, so close it before rebuilding.

### 3. Build and run midis2jam2

From `external\midis2jam2`, in PowerShell (adjust the two paths to your
installs):

```powershell
$env:JAVA_HOME = 'C:\Program Files\Java\jdk-21'
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
.\gradlew.bat run
```

This opens the launcher. Its home tab's **Delay Lama** card picks the
channels to sing; then pick a MIDI file and play it. To play a file straight
from the command line instead:

```powershell
$env:MIDIS2JAM2_DELAY_LAMA = 'channels=1'
.\gradlew.bat run --args="$PWD\..\..\tests\midi\01_melody.mid"
```

`MIDIS2JAM2_DELAY_LAMA` picks the sung channels (one-based, `channels=1,3`)
for the command line; its other settings are listed in
[CLAUDE.md](CLAUDE.md#build-and-run). The test suite is
`.\gradlew.bat :app:desktopTest` (under 2 minutes).

### 4. Optional: the Windows package

From the top folder, with the same `JAVA_HOME` and `ANDROID_HOME`:

```powershell
.\tools\package\make_package.ps1      # add -BuildDelayLama to run step 2 too
.\tools\package\check_package.ps1
```

It writes `dist\DelayLamaEverything\` and
`dist\DelayLamaEverything-<date>-windows-x64.zip`, which runs without the
source tree and brings its own Java runtime. Options are in
[tools/package/README.md](tools/package/README.md).

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
