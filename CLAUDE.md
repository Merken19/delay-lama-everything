# CLAUDE.md

Maintenance guidance for Delay Lama Everything.

## What this is

A midis2jam2 fork that plays MIDI files with selected channels sung by
Delay Lama. Each sung channel runs in a native helper process
(`DelayLamaVoice.exe`) built from the delalalalay-lama sources, which sings
the channel with a choir of monks. By default the monks stand in the 3D
scene where the channel's instrument would be; they can also be shown in
the helpers' always-on-top windows. While a file plays, a mixer window sets
every channel's level and switches each sung channel between the monks and
midis2jam2's own sound. A button opens `DelayLamaStandalone.exe` instances
for free play. There is no recording. The overview, with the user-facing
settings and the known limits, is in [README.md](README.md).

## Working on it

Version 1.0 is released. The docs describe the current state, not its
history, and must stay true: when code changes behaviour, fix the doc that
describes it in the same piece of work.

Before touching:

- midis2jam2's Delay Lama code, the helper, the pipe protocol, timing or
  levels: read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- the imitation profiles, the articulator or `profiles/imitation.json`: read
  [docs/IMITATION.md](docs/IMITATION.md).
- anything in delalalalay-lama: read its own
  `external/delalalalay-lama/CLAUDE.md`, which governs that repo.

Some code comments cite old decision numbers; that list is retired, and
ARCHITECTURE.md and IMITATION.md give the current behaviour and its reasons.

## Layout and where code goes

- `docs/`: the technical reference (ARCHITECTURE.md, IMITATION.md) and
  `BUILDING_LINUX_MACOS.md`.
- `external/midis2jam2/`: clone of wyskoj/midis2jam2 (`origin` = upstream).
  Our work is on its branch `delay-lama`, pushed to the user's fork
  Merken19/midis2jam2 (remote `fork`). Kotlin, Gradle, GPL-3.0.
- `external/delalalalay-lama/`: clone of Merken19/delalalalay-lama (the user's
  repo). The helper is a CMake target there (`Windows/voice_*`), on branch
  `voice-helper` (pushed to `origin`). It reuses `DSP/`, the bridge and the monk
  drawing code.
- `profiles/imitation.json`: the imitation profiles.
  `tools/profiles/expand.py` turns one into the helper's `set` lines.
- `renders/`: WAV renders and listening sets, and the profile tuning tools
  (`renders/phase4c/`, IMITATION.md §15).
- `tests/midi/`: test files (`tools/testmidi/make_test_midis.py`), with
  `PLAY_CHECK.md`, a manual play check.
- `tools/package/`: the Windows package script and its check. Output goes
  to `dist/` (ignored).
- `tools/listening/`: a local A/B listening website (dev tool, never
  packaged). Run `py tools\listening\serve.py` and open
  http://127.0.0.1:8740/. Render scripts write a `listening.json` next to
  their WAVs, and the user's answers land in `answers.json`/`answers.md`
  there. The format is in its README.
- `tools/drumfix/fix_gp_drums.py`: writes fixed copies of MIDI files whose
  drum notes are Guitar Pro 7 articulation numbers (0 = snare, 8 = kick,
  22 = crash, ...) instead of General MIDI keys. Those files play silent
  drums in most soundfonts and a beep (key 22) in Timbres of Heaven. Run
  `py tools\drumfix\fix_gp_drums.py <in folder> <out folder>`.
- The top-level folder is a git repository (branch `main`, `origin` =
  Merken19/delay-lama-everything). It holds the docs and our glue;
  `external/` is ignored, since each clone there is its own repository.
- Commits in all three repos use the GitHub no-reply address (repo-local
  `user.email`); GitHub refuses pushes that carry the private one.

## Rules

- **Never push** to any remote unless the user asks. midis2jam2's `origin` is
  the upstream author's repo: never push there.
- **Commits**: only when the user asks. In the clones they go on the
  branches above. The top-level repo is committed to `main` when the user
  confirms.
- **DSP**: only add functions to `external/delalalalay-lama/DSP/`, and never
  change existing behaviour (that repo's rule; the macOS build shares the
  files).
- **No simulated input**: never inject mouse, touch or keyboard input on the
  user's desktop (delalalalay-lama rule). Test with code or ask the user.
- **Sound needs ears, levels don't**: whether something sounds right is the
  user's call, so prefer offline WAV renders they can compare and ask for an
  ear check instead of claiming a sound is good. Loudness is the exception:
  set levels by measurement against Gervill (IMITATION.md §15) and don't ask
  the ear.
- Keep the pipe protocol (docs/ARCHITECTURE.md) versioned: change the doc and
  the version number together (protocol 1). Additive `set` keys need no new
  version.
- midis2jam2 keeps a behaviour catalogue (`docs/SPEC.md`,
  `app/src/desktopTest/resources/spec/behaviour.yaml`, `SpecCoverageTest`).
  New user-visible behaviour we add needs an entry and a test, or the
  suite fails.
- The Delay Lama panel and mixer are English only (`DelayLamaText`):
  midis2jam2's `LocalizationTest` fails if a string in `values/strings.xml`
  is missing from any of its other locales.
- Licensing: keep GPL notices in midis2jam2 files, and keep the AudioNerdz
  artwork terms with any package that ships `Resources/`.

## Build and run

Delay Lama standalone and `DelayLamaVoice` (PowerShell, from
`external/delalalalay-lama`):

```powershell
cmake -S .\Windows -B .\Windows\build -G "Visual Studio 17 2022" -A x64
cmake --build .\Windows\build --config Release --parallel
ctest --test-dir .\Windows\build -C Release --output-on-failure
.\Windows\build\Release\DelayLamaStandalone.exe
.\Windows\build\Release\DelayLamaVoice.exe            # then type: on 60 100
.\Windows\build\Release\DelayLamaVoice.exe --render .\Tests\voice_scripts\chord.txt chord.wav
```

A running `DelayLamaVoice.exe` or standalone locks its exe, so close it
before rebuilding.

midis2jam2 (PowerShell, from `external/midis2jam2`). It needs JDK 21 (the
JDK on `PATH` is 17) and, even for desktop tasks, the Android SDK:

```powershell
$env:JAVA_HOME = 'C:\Program Files\Java\jdk-21'
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
.\gradlew.bat run                                  # the launcher
$env:MIDIS2JAM2_DELAY_LAMA = 'channels=1'           # Delay Lama sings channel 1
.\gradlew.bat run --args="..\..\renders\phase2\k525_mvt1.mid"   # plays the file at once
```

In the launcher, the home tab's Delay Lama card opens the panel that picks
the channels, and it ignores the environment variable.
`MIDIS2JAM2_DELAY_LAMA` is for the command line (`--args=<file>`; without
the variable, a file sings the panel's remembered choices), the queue and
the tools. Its settings are separated by `;`:

- `channels=1,2.4`: one-based channels, `port.channel`; channel 10 is refused
- `monks=2`, `gain=0.8`
- `balance=6`: how many dB Gervill comes down while a channel is sung
- `offset=175`
- `keep3d`
- `exe=<path>`
- `profile=auto|plain|<name>`: the default `auto` makes each channel imitate
  its program
- `exaggerate=<0-2>`
- `profiles=<path>`
- `view=scene|windows|both`: where the monks are shown. The default `scene`
  stands them in the 3D scene and starts the helper windows hidden; `keep3d`
  keeps them in their windows
- `spread=<0-1>`: how far the choirs in the scene spread around the stage
  and up (default 0.5, 0 leaves them on the floor). The panel and the
  mixer have a slider for it
- `focus=0|1`: camera focus, off by default. The channels the camera is
  close to and looks at get louder, the rest quieter. The panel and the
  mixer have a switch for it

Keep `ImitationProfiles.kt` and `tools/profiles/expand.py` in step (a test
compares them). The helper is found in
`external/delalalalay-lama/Windows/build/Release/`.

Checks and tools (all `.\gradlew.bat`):

- `:app:compileKotlinDesktop` compiles only.
- `:app:desktopTest` runs the tests in 4 parallel JVMs, under 2 min;
  `--rerun` forces a run, `-PtestForks=1` runs them in one JVM (about
  3.5 min). A headless-engine call that takes over 60 s fails with the
  engine thread's stack attached; such hangs are intermittent (they pass
  alone).
- `:app:delayLamaLatency` is the latency probe. Record the system output
  while it plays (ARCHITECTURE.md "Timing and latency").
- `:app:delayLamaBalance -PdelayLamaBalance="<file.mid>;<out dir>;channels=1;profile=plain;30"`
  renders a file offline: the Gervill band, each sung channel's monk apart,
  and `live.wav`, the mix that live playback makes at the config's balance.
  It uses profile mode unless the config says `profile=plain`.
- `:app:delayLamaPanelPreview -PdelayLamaPanelPreview="<file.mid>;<out dir>"`
  renders the launcher's Delay Lama card and panel to PNGs with no window,
  plus the mixer with one sung channel switched off, and with all of them
  off (`mixer_*.png`).
- `:app:delayLamaScenePreview -PdelayLamaScenePreview="<file.mid>;<out dir>;channels=1;8,40"`
  renders the 3D scene with the monks standing in it to PNGs at those
  seconds (wide, close to the choir, and switched off), from a fake frame
  source and a hidden window; no helper runs and no input is sent. With
  `focus:<start>-<end>` in place of the seconds it plays the file with
  camera focus on and a scripted move in to the first choir and out,
  writing `focus_timeline.csv` and `focus_<s>s.png`;
  `:app:delayLamaBalance` replays that file with a `timeline=<csv>`
  setting.

If a stuck test JVM locks `app\build\test-results`, look for an old
`Gradle Test Executor` java process, or use a Gradle init script that moves
the `Test` tasks' `binaryResultsDirectory` and reports elsewhere.

The Windows package (PowerShell, from the top folder):

```powershell
.\tools\package\make_package.ps1             # -SkipBuild reuses the app image
.\tools\package\check_package.ps1
```

The package script builds midis2jam2's app image with Gradle (JDK 21 and
the Android SDK as above) and copies in the Delay Lama exes from
`external/delalalalay-lama/Windows/build/Release/`. Build those first; the
script doesn't, unless given `-BuildDelayLama`. It writes
`dist/DelayLamaEverything/` and
`dist/DelayLamaEverything-<date>-windows-x64.zip`. The check unzips the
newest zip to a temp folder, starts its launcher and reads the Delay Lama
paths from its log, then renders a voice script with the packaged helper
(no input is sent). Options are in `tools/package/README.md`.

Building on Linux or macOS is not supported in v1.0; porting notes are in
`docs/BUILDING_LINUX_MACOS.md`.

## Environment

- Windows 11 Pro, PowerShell primary (Git Bash available).
- VS 2022 Community, CMake 3.29.6, JDK 17 (Temurin, on PATH) and JDK 21
  (`C:\Program Files\Java\jdk-21`).
