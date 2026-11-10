# Delay Lama Everything

Play any MIDI file through Delay Lama. Version 1.0, for Windows x64.

[midis2jam2](https://github.com/wyskoj/midis2jam2) plays the file and animates
its 3D band as usual. Any instrument you pick becomes a Delay Lama instead:
its notes are sung by the Delay Lama vocal synth from
[delalalalay-lama](https://github.com/Merken19/delalalalay-lama), shaped to
imitate that instrument, and a choir of monks sings the chords. The monks
stand on the stage in the 3D scene, where the instrument would have been,
spread around the stage and up so the choirs don't hide each other, and nod
while their pitch moves. They can be shown in their own always-on-top
windows instead, or both.

While the file plays, a mixer window mutes, solos or turns up or down any
channel, sung or not. Each sung channel has its own **Delay Lama** switch
there, which flips that channel at any moment between the monks and
midis2jam2's own sound (never both at once). Every channel Delay Lama can
sing is sung until you switch it off in the panel. With **camera focus** on,
the channels the camera is close to and looks at get louder and the rest
quieter. An **Add Delay Lama** button opens extra Delay Lama standalone
instances so you can jam along by hand. There is no recording.

## Using it

### The Delay Lama card and panel

Pick a MIDI file on the launcher's home tab. The **Delay Lama** card shows
what will be sung in it; **Choose channels** opens the panel, which lists
every channel Delay Lama can sing (every port's channels with melodic notes;
drums on channel 10 always stay with midis2jam2). For each channel it shows
the programs, the note range, the most notes played at once and the note
count, and it has:

- a switch: sung or not (every channel starts sung)
- the choir size, 1 to 8 monks (a new channel gets one monk per note it
  plays at once, up to 4)
- the imitation: *auto* (follow the channel's program), *plain* (Delay Lama's
  own sound, no imitation) or any one profile
- a level in dB

Below the channels are the options for every file: balance (how many dB the
band comes down while a channel is sung), offset, imitation strength, where
the monks are shown (in the scene, their windows, or both), the spread of the
choirs, camera focus, keeping the 3D instruments, and the paths of the
helper, the standalone and `imitation.json`, each showing the file found.
Every change is saved at once; the channel choices are remembered per file
(by its contents), the options for every file.

### Playing a file

Press Play. Each sung channel gets its own `DelayLamaVoice.exe` helper, its
3D instrument leaves the stage (unless *keep the 3D instruments* is on) and
its choir stands there instead. The band plays 6 dB quieter by default, so
the monks are heard over it. On Windows, Fullscreen opens as borderless while
Delay Lama sings, because a real fullscreen window would cover the monk
windows.

### The mixer

A single file played with sung channels, from the launcher or the command
line, opens the mixer, an always-on-top window with a strip per channel the
file plays: mute, solo, volume from −30 to +6 dB, and Reset. A sung channel's
strip also has its **Delay Lama** switch: off hands the channel to
midis2jam2's own sound, hides its monks and puts its 3D instrument back on
stage, all at once and mid-note too. A card at the top counts the channels
switched on, with one button for all off or all on. The mixer also has the
spread slider and the camera focus switch, which work at once and are kept
as the panel's. The levels and switches are not remembered: each play starts
with every sung channel on.

### Camera focus

Off by default; switch it on in the panel or the mixer. The channel the
camera is nearest to and sees best stands out by up to 12 dB: it rises by up
to 6 dB and the rest comes off the other channels, while channels with
nothing in the picture fall further. From the wide camera 1A, or with the
camera near several things alike, nothing changes. The changes glide over
about a third of a second and come on top of the mixer's levels without
moving its sliders.

### Add Delay Lama

**Add Delay Lama** on the card or the panel opens one more
`DelayLamaStandalone.exe` to play by hand with the mouse or a MIDI keyboard.
It is not tied to the file and stays open after midis2jam2 closes. Every
instance shares the standalone's settings
(`%APPDATA%\DelayLamaStandalone\settings.ini`) and opens every MIDI input.

### Command-line settings

The home tab always uses the panel. A file played from the command line
(`midis2jam2.exe <file.mid>`, or `gradlew run --args=<file>` in a source
checkout) uses the `MIDIS2JAM2_DELAY_LAMA` environment variable if it is
set, else the panel's remembered choices for that file (for a new file,
every channel it can sing). The queue reads the variable too. Its settings
are separated by `;`:

| Setting | Meaning |
| --- | --- |
| `channels=1,2.4` | The sung channels, one-based, `port.channel`; channel 10 is refused |
| `monks=2` | Choir size, 1 to 8 (default 4) |
| `gain=0.8` | Level of the sung channels (default 1) |
| `balance=6` | How many dB the band (Gervill) comes down while a channel is sung, 0 to 30 (default 6) |
| `offset=175` | Milliseconds the monks' notes are held back to stay in time with the band (default 175 on Gervill, 0 on other MIDI devices) |
| `keep3d` | Keep the sung channels' 3D instruments; the monks then stay in their windows |
| `exe=<path>` | The `DelayLamaVoice.exe` to use |
| `profile=auto\|plain\|<name>` | Imitation: `auto` (default) makes each channel imitate its program, `plain` is Delay Lama's own sound, a name picks one profile for every channel |
| `exaggerate=<0-2>` | Imitation strength (default 1) |
| `profiles=<path>` | The `imitation.json` to use |
| `view=scene\|windows\|both` | Where the monks are shown (default `scene`: on stage, with the helper windows hidden) |
| `spread=<0-1>` | How far the choirs spread around the stage and up (default 0.5; 0 leaves them on the floor) |
| `focus=0\|1` | Camera focus (default off) |

For example, in PowerShell:

```powershell
$env:MIDIS2JAM2_DELAY_LAMA = 'channels=1,2;monks=2;view=both'
```

## How it fits together

```text
 midis2jam2 launcher (Compose UI)            pick file and Delay Lama channels:
        │                                     choir size, imitation, level
        ▼
 midis2jam2 performance (jMonkeyEngine) ──3D band, choirs on stage──────────▶ screen
        │  sequencer events                  ▲ frame and pitch reports
        ▼                                    │
   Delay Lama router (MidiDevice wrapper)    │  ◀── mixer window: levels, Delay Lama
        │                                    │       switches, spread, camera focus
        ├── other channels ──────────▶ Gervill (Java synth) ───────────────▶ speakers
        └── sung channels ──pipe─────▶ DelayLamaVoice.exe  (one per channel)
                                         choir of monk synths ─────────────▶ speakers
                                         monk window, always on top ───────▶ screen
                                         (hidden in the scene view)

 "Add Delay Lama" button ─────────────▶ DelayLamaStandalone.exe (free play, not tied to the file)
```

- **midis2jam2 fork**: reads and plays the file, draws the band and the
  choirs, and sends the chosen channels to Delay Lama instead of Gervill.
- **DelayLamaVoice.exe** (built from the delalalalay-lama sources): one
  process per sung channel. It sings the channel through a choir of monk
  synths, shapes each note with an *instrument imitation profile*
  ([docs/IMITATION.md](docs/IMITATION.md)), shows the monks in its window and
  reports which face each monk shows, so the choir on stage matches the
  singing.
- **DelayLamaStandalone.exe** (unchanged): opened by **Add Delay Lama** for
  playing by hand.

Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Repository layout

| Path | Contents |
| --- | --- |
| `README.md` | This overview |
| `CLAUDE.md` | Maintenance guidance for coding sessions, with the build commands and tools |
| `docs/ARCHITECTURE.md` | Components, pipe protocol, timing |
| `docs/IMITATION.md` | How Delay Lama imitates each instrument, and how a profile is tuned |
| `docs/BUILDING_LINUX_MACOS.md` | Notes on building on Linux and macOS |
| `profiles/imitation.json` | The imitation profiles and the program map |
| `tests/midi/` | Test MIDI files and a manual play check |
| `bundle/` | The soundfont, cube map and songs the package ships (git-ignored but for its README and NOTICE) |
| `renders/` | WAV renders, listening sets and the profile tuning tools |
| `tools/` | Package script, profile expander, test-file generator, GP7 drum fixer, listening website |
| `external/midis2jam2/` | Clone of the midis2jam2 fork (GPL-3.0), branch `delay-lama` |
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

`MIDIS2JAM2_DELAY_LAMA` takes the settings listed under
[Command-line settings](#command-line-settings). The test suite is
`.\gradlew.bat :app:desktopTest` (under 2 minutes).

### 4. Optional: the Windows package

From the top folder, with the same `JAVA_HOME` and `ANDROID_HOME`:

```powershell
.\tools\package\make_package.ps1      # add -BuildDelayLama to run step 2 too
.\tools\package\check_package.ps1
```

It writes `dist\DelayLamaEverything\` and
`dist\DelayLamaEverything-<date>-windows-x64.zip`, which runs without the
source tree and brings its own Java runtime. It also ships what is in
`bundle/`: a soundfont, a cube map background and songs to try. On its first
start for a user, the packaged app selects that soundfont and cube map
(unless the user already chose others) and its MIDI picker opens in the
songs; [bundle/README.md](bundle/README.md) has the layout and the rules.
The bundle's files are git-ignored, so a fresh clone fills `bundle/` itself
or packages with `-NoBundle`. Options are in
[tools/package/README.md](tools/package/README.md).

### Linux and macOS

Version 1.0 is built and tested on Windows only: the helper uses Win32 and
WinMM, and the monk windows, the window layout and the package are
Windows-specific. Guidance for porting and building on other systems is in
[docs/BUILDING_LINUX_MACOS.md](docs/BUILDING_LINUX_MACOS.md).

## Known limits

- **Imitation is tuned for some instruments only.** Piano (GM 1–8), the
  pipes and flutes (73–80), trumpet (57), tenor sax (67), violin and viola
  (41–42) and string ensembles 1–2 (49–50, both sung as a singer on "ah"),
  and finger bass (34) have tuned profiles. Every other instrument plays a
  first-guess profile for its family, with levels not matched to the band:
  guitars, the other basses, organs, chromatic percussion, cello and
  contrabass, harp, timpani, choirs, trombone, tuba, the other saxes, reeds,
  synth leads and pads, and GM 97–128. Trombone, tuba and horn sound much
  brighter than midis2jam2's own sound, and the French horn has no profile
  of its own (it plays the brass section's).
- **Closing a monk window ends that channel's helper**, so the channel goes
  silent; the window can't be brought back from the mixer. In the default
  scene view the windows are hidden, so this concerns the windows and both
  views.
- **Add Delay Lama is only on the launcher's card and panel**, not in the
  mixer.
- **The queue has no mixer**: its songs take their Delay Lama settings,
  camera focus included, from `MIDIS2JAM2_DELAY_LAMA`.
- **Drums are never sung**: rhythm channels (channel 10) stay with
  midis2jam2.
- **No words**: the monks never sing lyrics.
- **No recording**: midis2jam2's video recording works as before but leaves
  the sung channels and the monks out.
- **Windows x64 only** (see [Linux and macOS](#linux-and-macos)).

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
