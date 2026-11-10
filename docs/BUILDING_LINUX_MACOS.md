# Building on Linux or macOS

> **Status.** Delay Lama Everything v1.0 is built and tested on Windows x64
> only. Nothing in this document has been compiled or run on Linux or macOS.
> It is guidance for someone who wants to try a port: what already runs
> elsewhere, what is tied to Windows, and where to start. Statements marked
> *likely* or *untested* come from reading the code, not from a build.

The Windows build steps are in [../README.md](../README.md#building-from-source-windows),
and the components and the pipe protocol in [ARCHITECTURE.md](ARCHITECTURE.md).
Code paths below are relative to each repository: `external/midis2jam2/`
(branch `delay-lama`) or `external/delalalalay-lama/` (branch `voice-helper`).

## What runs where

| Component | Where it lives | State on Linux and macOS |
| --- | --- | --- |
| midis2jam2 fork (launcher, 3D scene, mixer, routing) | `app/src/` (Kotlin, Gradle) | Upstream midis2jam2 is cross-platform; our Kotlin code is plain JVM. Should build; untested. |
| Vocal engine | `DSP/` (C11) | Portable C, shared with the macOS standalone. |
| Helper logic: protocol, choir, articulator, frame reports | `Windows/voice_protocol.*`, `voice_allocator.*`, `voice_choir.*`, `voice_articulator.*`, `voice_frames.*`, `monk_animation.h` | Portable C++17 in itself, but it links the Win32 bridge (see below). |
| Offline render and WAV writer | `Windows/voice_render.*` | Nearly portable: small Win32 leftovers. |
| Bridge (synth handles, locking, MIDI input) | `Windows/standalone_bridge_win32.c`, `voice_bridge.h` | Win32: `CRITICAL_SECTION` and WinMM MIDI input. |
| Helper audio output | `Windows/audio_engine.h` | Win32: WinMM `waveOut`. |
| Helper window and monk drawing | `Windows/voice_window.*`, `monk_art.*`, `ui_common.cpp`, `app.h` | Win32 and GDI+. |
| Helper entry point | `Windows/voice_main.cpp` | Win32: `wmain`, stdin/stdout handles, threads, process priority. |
| Delay Lama standalone | `Windows/` (Win32) and `Sources/` + `build.sh` (macOS) | Windows only; the macOS version exists but is untested. |
| Package scripts | `tools/package/*.ps1` | Windows only (PowerShell, `.exe` names, zip layout). |
| Python tools | `tools/profiles/`, `tools/listening/`, `tools/testmidi/`, `tools/drumfix/` | Standard-library Python 3; likely run as they are with `python3`. |

The CMake project in `Windows/CMakeLists.txt` stops on any other host
(`message(FATAL_ERROR ...)` when `NOT WIN32`), so a port needs its own CMake
project or a reworked one.

## Prerequisites

Both systems:

- Git, and Python 3 for the tools.
- **JDK 21**, with `JAVA_HOME` pointing at it.
- The **Android SDK** with Android SDK Platform 36 and its licences
  accepted (`sdkmanager --licenses`), with `ANDROID_HOME` set. midis2jam2 is
  a Kotlin Multiplatform project and Gradle configures its Android target
  even for desktop tasks.
- For the helper: **CMake 3.20 or newer** and a C11/C++17 compiler (the
  CMake file asks for C11 and C++17).

macOS: the Xcode Command Line Tools (the standalone's README asks for
Xcode 15 or newer). Linux: GCC or Clang, the development files of whichever
audio backend you choose (for example ALSA, PipeWire or JACK) and of a
windowing toolkit if you port the monk window.

## Building midis2jam2

Clone the three repositories as in the README (same folder names), then
from `external/midis2jam2`:

```sh
export JAVA_HOME=/path/to/jdk-21
export ANDROID_HOME=/path/to/Android/Sdk
./gradlew run                       # the launcher
MIDIS2JAM2_DELAY_LAMA='channels=1' ./gradlew run --args="$PWD/../../tests/midi/01_melody.mid"
./gradlew :app:desktopTest          # the test suite
```

`app/build.gradle.kts` already picks per-OS dependencies: LWJGL 2 on macOS
and LWJGL 3 elsewhere, Compose for the current OS, and the host's FFmpeg
natives (both architectures on macOS). `createDistributable` makes an app
image for the host OS; no native package formats are set.

**Without a helper.** The helper is looked up by name (`DelayLamaVoice.exe`).
When none is found, each channel picked for Delay Lama logs
`DelayLamaVoice.exe not found` and plays on the synthesizer instead, so
playback behaves like upstream midis2jam2 with the Delay Lama layer present
but silent. The **Add Delay Lama** button reports that it can't find
`DelayLamaStandalone.exe`. One test runs `tools/profiles/expand.py` through
`py` or `python` and is skipped when neither is on `PATH` (often the case on
Linux, where it is `python3`).

**macOS runs the performance in another process.** On macOS
`ApplicationService.desktop.kt` hands the performance to midis2jam2's
separate renderer process (`renderer/RendererMain.kt`). That path builds the
Delay Lama routing, but it opens no mixer and does not pass the monks to the
3D scene. With a working helper the monks would likely be started hidden
for the scene and then not shown; `view=windows` or `keep3d` should avoid
that. Untested; a macOS port should wire the mixer and the scene through
this path, or run the performance in-process as Windows and Linux do.

## Porting the helper

The helper is one process per sung channel. midis2jam2 writes protocol
lines to its stdin and reads its stdout. The replacement must keep:

- the pipe protocol, version 1, exactly as in
  [ARCHITECTURE.md](ARCHITECTURE.md#pipe-protocol-version-1), including the
  `frames` and `pitches` report lines the scene depends on;
- the command line midis2jam2 passes (`--monks`, `--title`, `--label`,
  `--hidden`, `--x`/`--y`/`--width`/`--height`) and `--render`;
- a `--help` text that contains `--hidden`: midis2jam2 runs `--help` and
  only stands the monks in the scene when it finds that word;
- `Resources/faces.png` beside the binary. midis2jam2 reads it itself to
  draw the monks in the scene, and starts the helper in its own folder.

Win32-bound pieces, and what each would need:

| File | Tied to | Would need |
| --- | --- | --- |
| `standalone_bridge_win32.c` | `CRITICAL_SECTION`, WinMM MIDI input | A bridge with `pthread`/`std::mutex` locking that implements `voice_bridge.h` (`dl_create_without_midi` and the other additions). The macOS bridge `Sources/standalone_bridge.c` has no counterpart for those. The helper needs no MIDI input. |
| `voice_render.cpp` | includes `audio_engine.h` (for `kAudioFrames`); `write_wav` takes a `std::wstring` and uses `_wfopen_s` | A shared constant and a narrow-path `fopen`. |
| `audio_engine.h` | WinMM `waveOut`, `CreateThread` (four 512-frame 48 kHz stereo buffers fed by a render callback) | An output on the platform's API (Core Audio, ALSA, PipeWire, JACK, or a library such as PortAudio or miniaudio) that calls the same `Choir::render_callback`. |
| `voice_main.cpp` | `wmain` and wide arguments, `ReadFile`/`WriteFile` on std handles, `CreateThread`, `Sleep`, console control handler, `SetPriorityClass` and power throttling, GDI+ startup, the message loop | `main`, POSIX `read`/`write` or C++ streams, `std::thread`, signal handling; a raised priority is optional. |
| `voice_window.*` | Win32 window, `WM_TIMER` 30 ms tick, `SetWindowPos`, topmost | A window from the platform's toolkit. Note that the `frames`/`pitches` reports are printed from this window's tick, hidden or shown, so a port needs that tick even with no window. |
| `monk_art.*`, `ui_common.cpp`, `app.h` | GDI+ bitmaps, DPI calls, `module_directory()` | Image loading and scaled drawing on the platform, and the binary's own folder. |

`MonkWindowLayout.kt` places the helper windows with Windows' frame sizes
and in physical pixels, so window placement on other systems will likely be
off, though harmless.

A suggested order:

1. **Offline render.** Build `DSP/`, a portable bridge, the six core files
   and `voice_render.*` into a command-line tool that runs
   `--render <script> <out.wav>`. The core tests in `Tests/voice_*_checks.cpp`
   link the same library and use no Windows API, so they can come along.
   Compare its WAVs with the Windows helper's on `Tests/voice_scripts/`.
2. **Audio output.** Add the live mode: stdin reader, protocol replies on
   stdout, and the audio callback. With `view=windows`, midis2jam2 then
   needs nothing else.
3. **Window and frame reports.** Add the 30 ms tick that prints `frames` and
   `pitches`, `--hidden`, and the `--help` text; then the monk window.

**Telling midis2jam2 about the binary.** Without changes it looks only for
`DelayLamaVoice.exe`: beside the packaged app, in the working directory,
then at `delalalalay-lama/Windows/build/Release/DelayLamaVoice.exe` under an
`external` folder found upwards. Any path works if given explicitly: the
`exe=<path>` setting of `MIDIS2JAM2_DELAY_LAMA`, or the helper path field
in the launcher's Delay Lama panel. To find a port's binary by default,
change `locateHelper` and `EXE_NAME` in
`app/src/desktopMain/kotlin/org/wysko/midis2jam2/delaylama/VoiceHelperManager.kt`,
and `locate` in `StandaloneLauncher.kt` beside it for the standalone. The
packaged lookup uses the jpackage launcher's folder (`DelayLamaInstall.kt`);
inside a macOS `.app` that is likely `Contents/MacOS`.

## The macOS standalone

`build.sh` (zsh) compiles `DSP/*.c` and `Sources/standalone_bridge.c` with
clang, then the Swift app in `Sources/` (AppKit, AVFoundation, CoreMIDI), for
arm64 and x86_64, joins them with `lipo` into
`build/Delay Lama Standalone.app`, copies `Resources/` and the licence, and
signs it ad hoc. Its own header says it has not been built or tested by the
maintainers; the repository's README says the same. `Tests/run_macos_tests.sh`
runs the shared C tests on a Mac. It builds the standalone only, not the
helper. There is no Linux standalone.

## Rules for a port

- `DSP/` is shared with the macOS build: only add functions there, and never
  change existing behaviour.
- Keep the pipe protocol versioned. Change [ARCHITECTURE.md](ARCHITECTURE.md)
  and the version number together; additive `set` keys need no new version.
- Licences: midis2jam2 and our changes to it are GPL-3.0, and must ship
  with their source when distributed. The Delay Lama code is MIT. The
  AudioNerdz artwork (`Resources/`) and manual are freeware, not relicensed:
  they may be distributed freely with all original files, but not sold or
  used in commercial promotion.

Ports are welcome. If you get the helper or the whole project running on
Linux or macOS, please open a pull request against the repository the change
belongs to, with what you tested and on which system.
