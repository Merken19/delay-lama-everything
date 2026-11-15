# Delay Lama Everything

Play any MIDI file through Delay Lama. Version 1.0, for Windows x64.

[midis2jam2](https://github.com/wyskoj/midis2jam2) plays the file and animates
its 3D band as usual, but any instrument you pick becomes a Delay Lama: the
vocal synth from [delalalalay-lama](https://github.com/Merken19/delalalalay-lama)
sings its notes in place of the instrument's own sound, shaped to imitate it,
and a choir of monks sings the chords. The monks stand on the stage where the
instrument was, spread out so the choirs don't hide each other or the drums,
and nod as their pitch moves, each with its instrument's name below it. The
song's vocals stand a little bigger behind the drums. They are named Vocals
everywhere (the panel, the mixer, the windows and the scene), not after the sax
or other instrument the file gives them. You can show the monks in their own
always-on-top windows instead, or both. [How Delay Lama sings a
channel](#how-delay-lama-sings-a-channel) says what you hear.

While the file plays, the **Delay Lama Everything Controls** window (the
mixer) sets every channel's level and flips each sung channel between the
monks and midis2jam2's own sound. With camera focus on,
the channels the camera is close to get louder. **Add Delay Lama** opens extra
Delay Lama standalones so you can jam along by hand. There is no recording.

## How Delay Lama sings a channel

You choose which channels Delay Lama sings; the rest of the file plays as
usual.

- **One Delay Lama per sung channel.** Play starts a `DelayLamaVoice.exe`
  helper for each sung channel. It holds a choir of 1 to 8 monks, each a whole
  Delay Lama voice singing one note at a time, so a chord is shared out among
  the monks (with more notes at once than monks, a monk takes over a held
  note). The choir stands on stage in the instrument's place, or in the
  helper's window.
- **Melodic channels only.** Any channel with melodic notes, on any port, can
  be sung. Drums (channel 10) always stay with midis2jam2.
- **The other channels** play on midis2jam2's own synthesizer (Gervill), 6 dB
  quieter by default so the monks are heard.
- **Add Delay Lama** is separate: a standalone you play by hand, not tied to
  the file.

### A sung channel is pure Delay Lama

Everything you hear from a sung channel comes from the Delay Lama vocal
engine. No samples, soundfont or other synthesizer are mixed in, and
midis2jam2's synthesizer doesn't play the channel: without the mixer the
channel's notes never reach it, and with the mixer it gets them at volume 0, so
the mixer's switch can hand the channel over without a gap.

The engine is the one in `DelayLamaStandalone.exe` (delalalalay-lama's
`DSP/`), a clean-room recreation of AudioNerdz' 2002 Delay Lama derived from
[MonkSynth](https://github.com/JonET/monksynth). Instruments differ only in how
its parameters are set:

- **auto** (the default) uses the imitation profile for the channel's program.
  The profile works the engine's own controls: vowel, level, breath, pitch
  bend, glide, vibrato depth and rate, voice size and formants, unison voices
  and detune, and the echo on the whole choir. Vowel, level and pitch move
  within each note, updated every millisecond, so a trumpet sings "ta", a
  finger bass "doom" and a flute "hoo". A profile may also move a channel by
  whole octaves to suit the voice; one whose notes sit mostly above C5 comes
  down.
- **One profile** picked in the panel applies to every note of that channel.
- **plain** sings with the standalone's own sound.

The helper adds a few controls to the engine (each formant's scale and width,
each monk's own vibrato); at their neutral values the sound is exactly the
standalone's. How the profiles work, and which instrument gets which, is in
[docs/IMITATION.md](docs/IMITATION.md).

You hear the instrument's own sound instead only when you switch the channel's
**Delay Lama** switch off in the mixer, or when its helper can't start (the
channel then plays on midis2jam2's synthesizer so it is still heard).

## Using it

### The Delay Lama card and panel

Pick a MIDI file on the launcher's home tab. The **Delay Lama** card shows what
will be sung, and **Choose channels** opens the panel. It lists every channel
Delay Lama can sing (every port's channels with melodic notes; drums on channel
10 stay with midis2jam2), with its programs, note range, most notes at once and
note count. Each channel has:

- a switch for sung or not (every channel starts sung);
- the choir size, 1 to 8 monks (a new channel gets one monk per note it plays
  at once, up to 4);
- the imitation: *auto* (follow the channel's program), *plain* (Delay Lama's
  own sound) or any one profile;
- a level in dB.

Below are the options for every file: balance, offset, imitation strength,
where the monks are shown, the choirs' spread, instrument names, camera focus,
keeping the 3D
instruments, and the paths of the helper, the standalone and
`imitation.json`, each showing the file it found. Changes are saved at once:
channel choices per file (by its contents), options for all files.

### Playing a file

Press Play. Each sung channel gets its own `DelayLamaVoice.exe` helper, and its
choir takes its 3D instrument's place on stage (unless *keep the 3D
instruments* is on). The band plays 6 dB quieter by default so you hear the
monks. On Windows, Fullscreen opens as borderless while Delay Lama sings,
because a real fullscreen window would cover the monk windows.

### Delay Lama Everything Controls (the mixer)

Playing a single file with sung channels, from the launcher or the command
line, opens the mixer, an always-on-top window titled **Delay Lama Everything
Controls**, with a strip per channel for mute, solo, volume (−30 to +6 dB) and
Reset.

- A sung channel's **Delay Lama** switch hands the channel to midis2jam2's own
  sound when off: its monks hide and its 3D instrument returns, at once, even
  mid-note. A card at the top counts the channels switched on and switches
  them all off or all on.
- A sung channel you can't hear (muted, or left out of a solo) hides its monks
  without bringing its instrument back, until you can hear it again.
- **F** (with the monks in the scene) brings that channel's choir to the front
  of the stage, on the floor in the middle of the opening camera's picture,
  whatever the spread; press it again to send it back. Several choirs at the
  front stand side by side in channel order.
- **Instrument names** (with the monks in the scene, on by default) shows the
  name of what each channel plays below its choir, as the mixer's strip names
  it: white on a dark band just under the monks' feet, the same size however
  far the choir is. It is drawn over the scene, so a choir further back can
  have its name over the monks in front; a name whose spot is off the screen
  isn't shown.
- The **spread**, **instrument names**, **camera focus** and **focus
  strength** controls act at once and are saved as the panel's.

Levels, switches and F buttons are not remembered: each play starts with every
sung channel on and none at the front.

### Camera focus

Off by default; switch it on in the panel or the mixer. The channel the camera
is nearest to and sees best then stands out by up to 12 dB: it rises by up to 6
dB, the other channels come down, and channels with nothing in the picture fall
further. From the wide camera 1A, or with the camera near several things alike,
nothing changes. The changes glide in about a quarter of a second, on top of
the mixer's levels.

**Focus strength** scales this from 0 to 200 % (default 100 %): at 200 % the
near channel stands out by up to 24 dB, at 50 % by 6, at 0 % not at all. A
channel's own level still rises by at most 6 dB. You can set it while focus is
off.

### Add Delay Lama

**Add Delay Lama** on the card or the panel opens one more
`DelayLamaStandalone.exe` to play by hand with the mouse or a MIDI keyboard. It
is not tied to the file and stays open after midis2jam2 closes. All instances
share the standalone's settings (`%APPDATA%\DelayLamaStandalone\settings.ini`)
and open every MIDI input.

### Command-line settings

The home tab always uses the panel. A file played from the command line
(`midis2jam2.exe <file.mid>`, or `gradlew run --args=<file>` in a source
checkout) uses the `MIDIS2JAM2_DELAY_LAMA` environment variable if it is set,
and otherwise the panel's remembered choices for that file (for a new file,
every channel it can sing). The queue reads the variable too. Separate the
settings with `;`:

| Setting | Meaning |
| --- | --- |
| `channels=1,2.4` | The sung channels, one-based, `port.channel`; channel 10 is refused |
| `monks=2` | Choir size, 1 to 8 (default 4) |
| `gain=0.8` | Level of the sung channels, 0 to 4 (default 1) |
| `balance=6` | How many dB the band (Gervill) comes down while a channel is sung, 0 to 30 (default 6) |
| `offset=175` | Milliseconds the monks' notes are held back to stay in time with the band, 0 to 2000 (default 175 on Gervill, 0 on other MIDI devices) |
| `keep3d` | Keep the sung channels' 3D instruments; the monks then stay in their windows |
| `exe=<path>` | The `DelayLamaVoice.exe` to use |
| `profile=auto\|plain\|<name>` | Imitation: `auto` (default) imitates each channel's program, `plain` is Delay Lama's own sound, a name picks one profile for every channel |
| `exaggerate=<0-2>` | Imitation strength (default 1) |
| `profiles=<path>` | The `imitation.json` to use |
| `view=scene\|windows\|both` | Where the monks are shown (default `scene`: on stage, with the helper windows hidden) |
| `spread=<0-1>` | How far the choirs spread around the stage and up (default 0.5; 0 leaves them on the floor) |
| `names=0\|1` | Instrument names below the choirs in the scene (default on) |
| `focus=0\|1` | Camera focus (default off) |
| `focusstrength=<0-2>` | Camera focus strength (default 1, that is 100 %) |

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
        │                                    │       and its strength
        ├── other channels ──────────▶ Gervill (Java synth) ───────────────▶ speakers
        └── sung channels ──pipe─────▶ DelayLamaVoice.exe  (one per channel)
                                         choir of monk synths ─────────────▶ speakers
                                         monk window, always on top ───────▶ screen
                                         (hidden in the scene view)

 "Add Delay Lama" button ─────────────▶ DelayLamaStandalone.exe (free play, not tied to the file)
```

Each helper shapes its notes with an imitation profile
([docs/IMITATION.md](docs/IMITATION.md)) and reports which face each monk
shows, so the choir on stage matches the singing. The details are in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Repository layout

| Path | Contents |
| --- | --- |
| `CLAUDE.md` | Maintenance guidance, with the build commands and tools |
| `docs/` | [ARCHITECTURE.md](docs/ARCHITECTURE.md), [IMITATION.md](docs/IMITATION.md), [BUILDING_LINUX_MACOS.md](docs/BUILDING_LINUX_MACOS.md) |
| `profiles/imitation.json` | The imitation profiles and the program map |
| `tests/midi/` | Test MIDI files |
| `bundle/` | The soundfont, cube map and songs the package ships (git-ignored but for its README and NOTICE) |
| `renders/` | Output of the render and tuning scripts (git-ignored) |
| `tools/` | Package script, profile expander, tuning tools, test-file generator, GP7 drum fixer, listening website |
| `external/midis2jam2/` | Clone of the midis2jam2 fork (GPL-3.0) |
| `external/delalalalay-lama/` | Clone of delalalalay-lama (MIT code, freeware artwork) |

## Building from source (Windows)

The project is three public repositories: this one holds the docs, profiles
and tools, and the code is in the other two, cloned into `external/`
(git-ignored here; each is its own repository).

| Folder | Repository | Branch |
| --- | --- | --- |
| *(top)* | [Merken19/delay-lama-everything](https://github.com/Merken19/delay-lama-everything) | `main` |
| `external/midis2jam2/` | [Merken19/midis2jam2](https://github.com/Merken19/midis2jam2), a fork of [wyskoj/midis2jam2](https://github.com/wyskoj/midis2jam2) | `delay-lama` |
| `external/delalalalay-lama/` | [Merken19/delalalalay-lama](https://github.com/Merken19/delalalalay-lama) | `voice-helper` |

Keep these folder names: midis2jam2 looks for the helper at
`external/delalalalay-lama/Windows/build/Release/` and for
`profiles/imitation.json` above its own folder, and the package script expects
both clones under `external/`.

### Prerequisites

- Windows 10 or 11, x64, and [Git](https://git-scm.com/). You don't need Git
  LFS: its only files are midis2jam2's Blender sources, which the build doesn't
  read.
- **Visual Studio 2022** with the *Desktop development with C++* workload, and
  **CMake 3.20 or newer** (tested with 3.29; Visual Studio's own works).
- **JDK 21**, for example [Azul Zulu 21](https://www.azul.com/downloads/#zulu)
  or Oracle JDK 21, with `JAVA_HOME` pointing at it (another JDK on `PATH` is
  fine).
- The **Android SDK**, even for the desktop build, because Gradle configures
  midis2jam2's Android target. Install it with
  [Android Studio](https://developer.android.com/studio) or the command-line
  tools, add *Android SDK Platform 36*, accept the licences
  (`sdkmanager --licenses`) and point `ANDROID_HOME` at it (by default
  `%LOCALAPPDATA%\Android\Sdk`).
- Optional: **Python 3** (`py` or `python`) for `tools/`, which use only the
  standard library. One midis2jam2 test runs `tools/profiles/expand.py` and is
  skipped without Python.
- An internet connection for Gradle's first run (several hundred MB).

### 1. Get the sources

```powershell
git clone https://github.com/Merken19/delay-lama-everything.git
cd delay-lama-everything
git clone -b voice-helper https://github.com/Merken19/delalalalay-lama.git external\delalalalay-lama
git clone -b delay-lama -o fork https://github.com/Merken19/midis2jam2.git external\midis2jam2
git -C external\midis2jam2 remote add origin https://github.com/wyskoj/midis2jam2.git
git -C external\midis2jam2 fetch origin
```

The last two lines add upstream midis2jam2 as `origin`. Only the package
script needs it: it writes the GPL source patch against `origin/master`.

### 2. Build the Delay Lama exes

From `external\delalalalay-lama`:

```powershell
cmake -S .\Windows -B .\Windows\build -G "Visual Studio 17 2022" -A x64
cmake --build .\Windows\build --config Release --parallel
ctest --test-dir .\Windows\build -C Release --output-on-failure
```

This puts `DelayLamaVoice.exe` and `DelayLamaStandalone.exe`, with the artwork
in `Resources\`, in `Windows\build\Release\`. To try the helper on its own:

```powershell
.\Windows\build\Release\DelayLamaVoice.exe --render .\Tests\voice_scripts\chord.txt chord.wav
```

A running helper or standalone locks its exe, so close it before rebuilding.

### 3. Build and run midis2jam2

From `external\midis2jam2` (adjust the two paths to your installs):

```powershell
$env:JAVA_HOME = 'C:\Program Files\Java\jdk-21'
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
.\gradlew.bat run
```

This opens the launcher. To play a file straight from the command line
instead, with the [settings above](#command-line-settings):

```powershell
$env:MIDIS2JAM2_DELAY_LAMA = 'channels=1'
.\gradlew.bat run --args="$PWD\..\..\tests\midi\01_melody.mid"
```

Run the tests with `.\gradlew.bat :app:desktopTest` (under 2 minutes).

### 4. Optional: the Windows package

From the top folder, with the same `JAVA_HOME` and `ANDROID_HOME`:

```powershell
.\tools\package\make_package.ps1      # add -BuildDelayLama to run step 2 too
.\tools\package\check_package.ps1
```

This writes `dist\DelayLamaEverything\` and
`dist\DelayLamaEverything-<date>-windows-x64.zip`, which runs without the
source tree and brings its own Java runtime. It also ships `bundle/`: a
soundfont, a cube map background and songs to try, which the packaged app
selects on a user's first start (unless they chose others), with its MIDI
picker opening in the songs. The bundle's files are git-ignored, so in a fresh
clone fill `bundle/` yourself ([bundle/README.md](bundle/README.md)) or package
with `-NoBundle`. The options are in
[tools/package/README.md](tools/package/README.md).

### Linux and macOS

Version 1.0 is built and tested on Windows only: the helper uses Win32 and
WinMM, and the monk windows, their layout and the package are Windows-specific.
See [docs/BUILDING_LINUX_MACOS.md](docs/BUILDING_LINUX_MACOS.md).

## Known limits

- **Imitation is tuned for some instruments only**: piano (GM 1–8), pipes and
  flutes (73–80), trumpet (57), tenor sax (67), violin, viola and string
  ensembles 1–2 (41–42, 49–50, sung as a singer on "ah"), and finger bass (34).
  The other instruments with a profile play a first guess whose level is not
  matched to the band; trombone, tuba and horn sound much brighter than
  midis2jam2's own sound. Harp, timpani, orchestra hit and GM 97–128 have no
  profile and play `default`. Which profile plays what is in
  [docs/IMITATION.md §13](docs/IMITATION.md#13-profile-data).
- **Closing a monk window ends that channel's helper**, so the channel goes
  silent, and the mixer can't bring it back. In the default scene view the
  windows are hidden.
- **Add Delay Lama is only on the card and panel**, not in the mixer.
- **The queue has no mixer**: its songs take their Delay Lama settings, camera
  focus included, from `MIDIS2JAM2_DELAY_LAMA`.
- **Drums are never sung**: rhythm channels (channel 10) stay with midis2jam2.
- **No words**: the monks never sing lyrics.
- **No recording**: midis2jam2's video recording works as before but leaves
  out the sung channels and the monks.
- **Windows x64 only** (see [Linux and macOS](#linux-and-macos)).

## Licensing

- midis2jam2 is **GPL-3.0**, so our modified midis2jam2 must stay GPL-3.0 if
  it is distributed, with its source.
- The Delay Lama standalone code is MIT, and its vocal engine is derived from
  MIT-licensed [MonkSynth](https://github.com/JonET/monksynth). MIT code can be
  combined with GPL code.
- The Delay Lama artwork (`Resources/*.png`) and manual are AudioNerdz'
  2002–2004 freeware. They are **not relicensed**: they may be distributed
  freely with all original files, but not sold or used in commercial
  promotion.
- This project is not affiliated with AudioNerdz or the midis2jam2 authors.
