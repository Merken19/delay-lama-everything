# CLAUDE.md

Maintenance guidance for Delay Lama Everything.

## What this is

A midis2jam2 fork that plays MIDI files with chosen channels sung by Delay
Lama. Each sung channel runs in a helper process (`DelayLamaVoice.exe`,
built from delalalalay-lama) that sings it with a choir of monks, shown in
the 3D scene in place of the instrument or in the helper's always-on-top
window. A mixer sets every channel's level and switches each sung channel
between the monks and midis2jam2's own sound. A button opens
`DelayLamaStandalone.exe` for free play. There is no recording.
[README.md](README.md) has the overview, user settings and known limits.

Version 1.0 is released. Docs describe the current state, not history, and
must stay true: when code changes behaviour, fix its doc in the same work.

Read first:

- Delay Lama code in midis2jam2, the helper, the pipe protocol, timing or
  levels: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- imitation profiles, the articulator, `profiles/imitation.json`:
  [docs/IMITATION.md](docs/IMITATION.md).
- anything in delalalalay-lama: `external/delalalalay-lama/CLAUDE.md`.

## Layout

- `docs/`: ARCHITECTURE.md, IMITATION.md, BUILDING_LINUX_MACOS.md.
- `external/midis2jam2/`: clone of wyskoj/midis2jam2 (`origin` = upstream).
  Our branch `delay-lama` goes to the user's fork Merken19/midis2jam2
  (remote `fork`). Kotlin, Gradle, GPL-3.0.
- `external/delalalalay-lama/`: clone of Merken19/delalalalay-lama, branch
  `voice-helper` (pushed to `origin`). The helper is the CMake target
  `Windows/voice_*`; it reuses `DSP/`, the bridge and the monk drawing.
- `profiles/imitation.json`: the imitation profiles.
  `tools/profiles/expand.py` turns one into the helper's `set` lines.
- `tools/tuning/`: profile tuning tools (IMITATION.md §15); output in
  `renders/tuning/<family>/`.
- `tools/listening/`: local A/B listening site, never packaged.
  `py tools\listening\serve.py`, then http://127.0.0.1:8740/. It reads
  `listening.json` sets under `renders/` and saves `answers.json`/`answers.md`
  beside them.
- `tools/testmidi/make_test_midis.py`: writes `tests/midi/01`–`07`.
- `tools/drumfix/fix_gp_drums.py <in folder> <out folder>`: fixes MIDI files
  whose drums use Guitar Pro 7 articulation numbers (0 = snare, 8 = kick,
  22 = crash) instead of GM keys, which play silent or as a beep.
- `tools/package/`: Windows package script and check; output in `dist/`.
- `tests/midi/`: test MIDI files, `k525_mvt1.mid` and the A/B clips in
  `ab/`; its README says what each tests.
- `bundle/`: what the package ships beside the app (soundfont, cube map,
  songs, licenses). Only `README.md` and `NOTICE.txt` are tracked; keep the
  NOTICE true to the files. App side: `DelayLamaBundle`
  (`delaylama.package.bundle`).
- `renders/`: ignored output of render scripts and previews; all of it can
  be remade.
- The top folder is a git repo (branch `main`, `origin` =
  Merken19/delay-lama-everything) with the docs and our glue; `external/`
  is ignored, each clone is its own repo. All three repos commit with the
  GitHub no-reply address (repo-local `user.email`); GitHub refuses the
  private one.

## Rules

- **Never push** unless the user asks. Never push to midis2jam2's `origin`
  (the upstream author's repo).
- **Commit** only when the user asks: clones on the branches above, the top
  repo on `main` when the user confirms.
- **DSP**: only add functions to `external/delalalalay-lama/DSP/`; never
  change existing behaviour (the macOS build shares it).
- **No simulated input** on the user's desktop. Test with code or ask.
- **Sound needs ears, levels don't**: offer offline WAV renders and ask for
  an ear check instead of calling a sound good. Set loudness by measurement
  against Gervill (IMITATION.md §15), never by ear.
- **Pipe protocol** (ARCHITECTURE.md) is protocol 1: change the doc and the
  version number together. Additive `set` keys need no new version.
- midis2jam2's behaviour catalogue (`docs/SPEC.md`,
  `app/src/desktopTest/resources/spec/behaviour.yaml`, `SpecCoverageTest`):
  new user-visible behaviour needs an entry and a test.
- The Delay Lama panel and mixer are English only (`DelayLamaText`):
  `LocalizationTest` fails if a `values/strings.xml` string is missing from
  another locale.
- Keep `ImitationProfiles.kt` and `tools/profiles/expand.py` in step (a test
  compares them).
- Keep GPL notices in midis2jam2 files, and the AudioNerdz artwork terms
  with any package that ships `Resources/`.

## Build and run

Delay Lama (PowerShell, from `external/delalalalay-lama`; close a running
exe before rebuilding, it locks itself):

```powershell
cmake -S .\Windows -B .\Windows\build -G "Visual Studio 17 2022" -A x64
cmake --build .\Windows\build --config Release --parallel
ctest --test-dir .\Windows\build -C Release --output-on-failure
.\Windows\build\Release\DelayLamaStandalone.exe
.\Windows\build\Release\DelayLamaVoice.exe            # then type: on 60 100
.\Windows\build\Release\DelayLamaVoice.exe --render .\Tests\voice_scripts\chord.txt chord.wav
```

midis2jam2 (PowerShell, from `external/midis2jam2`) needs JDK 21 (`PATH`
has 17) and the Android SDK even for desktop tasks. It finds the helper in
`external/delalalalay-lama/Windows/build/Release/`.

```powershell
$env:JAVA_HOME = 'C:\Program Files\Java\jdk-21'
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
.\gradlew.bat run                                   # the launcher
$env:MIDIS2JAM2_DELAY_LAMA = 'channels=1'           # Delay Lama sings channel 1
.\gradlew.bat run --args="..\..\tests\midi\k525_mvt1.mid"   # plays the file at once
```

The launcher's Delay Lama card opens the channel panel and ignores the
variable. `MIDIS2JAM2_DELAY_LAMA` is for `--args=<file>` (without it, a file
sings the panel's remembered choices), the queue and the tools; settings
are separated by `;`:

- `channels=1,2.4`: one-based, `port.channel`; channel 10 is refused
- `monks=2`, `gain=0.8`, `offset=175`, `keep3d`, `exe=<path>`,
  `profiles=<path>`, `exaggerate=<0-2>`
- `balance=6`: dB Gervill comes down while a channel is sung
- `profile=auto|plain|<name>`: `auto` (default) imitates each channel's
  program
- `view=scene|windows|both`: where the monks show. `scene` (default) starts
  the helper windows hidden; `keep3d` keeps the monks in their windows
- `spread=<0-1>`: how far the scene's choirs spread around the stage and up
  (default 0.5; 0 = on the floor)
- `focus=0|1`: camera focus, default off; channels the camera is close to
  and looks at get louder, the rest quieter
- `focusstrength=<0-2>`: scales focus (default 1 = 100 %, 0 = no change); a
  channel's own rise stays at most 6 dB
- `names=0|1`: instrument names below the choirs in the scene, default on

`spread`, `names`, `focus` and `focusstrength` also have controls in the
panel and the mixer (the window titled "Delay Lama Everything Controls").

### Checks and tools (`.\gradlew.bat`, from `external/midis2jam2`)

- `:app:compileKotlinDesktop`: compile only.
- `:app:desktopTest`: 4 parallel JVMs, under 2 min. `--rerun` forces it,
  `-PtestForks=1` uses one JVM (about 3.5 min). A headless-engine call over
  60 s fails with the engine thread's stack; such hangs are intermittent.
- `:app:delayLamaLatency`: latency probe; record the system output while it
  plays (ARCHITECTURE.md "Timing and latency").
- `:app:delayLamaBalance -PdelayLamaBalance="<file.mid>;<out dir>;channels=1;profile=plain;30"`:
  offline render of the Gervill band, each sung channel's monk apart, and
  `live.wav` at the config's balance. Profile mode unless `profile=plain`.
- `:app:delayLamaPanelPreview -PdelayLamaPanelPreview="<file.mid>;<out dir>"`:
  the Delay Lama card and panel as PNGs, plus the mixer with one and with
  all sung channels off (`mixer_*.png`). No window.
- `:app:delayLamaScenePreview -PdelayLamaScenePreview="<file.mid>;<out dir>;channels=1;8,40"`:
  the 3D scene with the monks as PNGs at those seconds (wide, high above
  the audience, far behind camera 1A, close to the choir, switched off, and
  the first choir at the front of the stage, the mixer's F). Fake frame source, hidden
  window, no helper, no input.
  - `focus:<start>-<end>` in place of the seconds plays with focus on and a
    scripted move in to the first choir and out, writing
    `focus_timeline.csv` and `focus_<s>s.png`; `:app:delayLamaBalance`
    replays it with `timeline=<csv>`.
  - `smoothing=<time constant s>,<send interval s>` overrides the focus
    easing (v1.0 is `0.3,0.05`) for before/after renders.

A stuck test JVM can lock `app\build\test-results`: look for an old
`Gradle Test Executor` java process, or use an init script that moves the
`Test` tasks' `binaryResultsDirectory` and reports.

### Windows package (PowerShell, from the top folder)

```powershell
.\tools\package\make_package.ps1             # -SkipBuild reuses the app image
.\tools\package\check_package.ps1
```

It builds midis2jam2's app image (JDK 21 and Android SDK as above), copies
in the Delay Lama exes from `external/delalalalay-lama/Windows/build/Release/`
(build them first, or pass `-BuildDelayLama`) and writes
`dist/DelayLamaEverything/` and its zip. The check unzips the newest zip,
starts its launcher, reads the Delay Lama paths from its log and renders a
voice script with the packaged helper, sending no input. Details and
options: `tools/package/README.md`.

Linux and macOS builds are not supported in v1.0; see
`docs/BUILDING_LINUX_MACOS.md`.

## Environment

Windows 11 Pro, PowerShell (Git Bash available). VS 2022 Community, CMake
3.29.6, JDK 17 (Temurin, on `PATH`) and JDK 21
(`C:\Program Files\Java\jdk-21`).
