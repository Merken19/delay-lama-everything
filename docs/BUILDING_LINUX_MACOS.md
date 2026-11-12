# Building on Linux or macOS

Delay Lama Everything v1.0 is built and tested on Windows x64 only. Nothing
here has been compiled or run on Linux or macOS: these are notes from reading
the code, for anyone who wants to try a port. The Windows build is in
[README.md](../README.md#building-from-source-windows), and the components and
the pipe protocol are in [ARCHITECTURE.md](ARCHITECTURE.md). Paths are relative
to `external/midis2jam2/` or `external/delalalalay-lama/`.

## What is already portable

- **midis2jam2** (`app/src/`). Upstream is cross-platform and our code is plain
  JVM, so it should build. `app/build.gradle.kts` already picks per-OS
  dependencies (LWJGL 2 on macOS, LWJGL 3 elsewhere, Compose and FFmpeg natives
  for the host), and `createDistributable` makes an app image for the host OS.
- **The vocal engine** (`DSP/`, C11), shared with the macOS standalone.
- **The helper's core** (`Windows/voice_protocol.*`, `voice_allocator.*`,
  `voice_choir.*`, `voice_articulator.*`, `voice_frames.*`, `monk_animation.h`):
  portable C++17, but it links the Win32 bridge.
- **The Python tools** in `tools/` use only the standard library and likely run
  as they are with `python3`.

You need JDK 21 (`JAVA_HOME`) and the Android SDK with Platform 36, its
licences accepted (`ANDROID_HOME`), since Gradle configures the Android target
even for desktop tasks. The helper needs CMake 3.20 or newer and a C11 and
C++17 compiler: the Xcode Command Line Tools on macOS (the standalone asks for
Xcode 15 or newer), or GCC or Clang on Linux with your audio backend's and, for
the monk window, a windowing toolkit's development files.

## What is Win32-only

`Windows/CMakeLists.txt` stops on any other host (`message(FATAL_ERROR ...)`
when `NOT WIN32`), so a port needs its own CMake project or a reworked one.

| File | Tied to | A port needs |
| --- | --- | --- |
| `standalone_bridge_win32.c` | `CRITICAL_SECTION`, WinMM MIDI input | A bridge implementing `voice_bridge.h` (`dl_create_without_midi` and the other additions, which the macOS `Sources/standalone_bridge.c` lacks) with `pthread` or `std::mutex`; no MIDI input |
| `voice_render.cpp` | `kAudioFrames` from `audio_engine.h`; `write_wav` takes a `std::wstring` and uses `_wfopen_s` | A shared constant and a narrow-path `fopen` |
| `audio_engine.h` | WinMM `waveOut`, `CreateThread`: four 512-frame 48 kHz stereo buffers | Output on the platform's API (or PortAudio, miniaudio) calling `Choir::render_callback` |
| `voice_main.cpp` | `wmain`, `ReadFile`/`WriteFile` on std handles, threads, `Sleep`, console control handler, priority and power throttling, GDI+ startup, the message loop | `main`, POSIX or C++ streams, `std::thread`, signal handling; raised priority is optional |
| `voice_window.*` | Win32 window, 30 ms `WM_TIMER` tick, topmost | A toolkit window. The `frames` and `pitches` reports print from this tick, so a port needs the tick even with no window |
| `monk_art.*`, `ui_common.cpp`, `app.h` | GDI+ bitmaps, DPI calls, `module_directory()` | Image loading, scaled drawing, the binary's own folder |

The package scripts (`tools/package/*.ps1`) are Windows-only too.
`MonkWindowLayout.kt` places the helper windows with Windows' frame sizes in
physical pixels, so placement elsewhere will likely be off, but harmless. The
standalone has a macOS build (`build.sh`, the Swift app in `Sources/`, and
`Tests/run_macos_tests.sh` for the shared C tests), which its maintainers have
not built or tested; it does not build the helper. There is no Linux
standalone.

## Where a port would start

Build midis2jam2 first, from `external/midis2jam2`:

```sh
export JAVA_HOME=/path/to/jdk-21
export ANDROID_HOME=/path/to/Android/Sdk
./gradlew run
MIDIS2JAM2_DELAY_LAMA='channels=1' ./gradlew run --args="$PWD/../../tests/midi/01_melody.mid"
./gradlew :app:desktopTest
```

Without a helper, each Delay Lama channel logs `DelayLamaVoice.exe not found`
and plays on the synthesizer, so playback works like upstream midis2jam2, and
**Add Delay Lama** reports that it can't find `DelayLamaStandalone.exe`. One
test runs `tools/profiles/expand.py` through `py` or `python` and is skipped
when neither is on `PATH` (as on many Linux systems, which have `python3`).

Then port the helper in this order:

1. **Offline render**: `DSP/`, a portable bridge, the core files and
   `voice_render.*` as a tool that runs `--render <script> <out.wav>`. The core
   tests (`Tests/voice_*_checks.cpp`) use no Windows API. Compare its WAVs with
   the Windows helper's on `Tests/voice_scripts/`.
2. **Audio output**: the stdin reader, replies on stdout and the audio
   callback. With `view=windows` midis2jam2 then needs nothing else.
3. **Window and reports**: the 30 ms tick printing `frames` and `pitches`,
   `--hidden`, the `--help` text, then the monk window.

**Finding the binary.** midis2jam2 looks only for `DelayLamaVoice.exe`: beside
the packaged app, in the working directory, then at
`delalalalay-lama/Windows/build/Release/DelayLamaVoice.exe` under an
`external` folder found upwards. Any path works through the `exe=<path>`
setting or the panel's helper path. To find a port's binary by default, change
`locateHelper` and `EXE_NAME` in
`app/src/desktopMain/kotlin/org/wysko/midis2jam2/delaylama/VoiceHelperManager.kt`,
and `locate` in `StandaloneLauncher.kt` beside it. The packaged lookup and the
bundle (`DelayLamaBundle.kt`) use the jpackage launcher's folder
(`DelayLamaInstall.kt`), likely `Contents/MacOS` inside a macOS `.app`.

**macOS runs the performance in another process**
(`ApplicationService.desktop.kt` hands it to `renderer/RendererMain.kt`). That
path builds the Delay Lama routing but opens no mixer and doesn't pass the
monks to the 3D scene, so monks started hidden for the scene would likely never
show; `view=windows` or `keep3d` should avoid that. A macOS port should wire
the mixer and the scene through that path, or run the performance in-process
as Windows and Linux do.

## Rules a port must follow

- **Keep the helper's interface**: the pipe protocol, version 1, exactly as in
  [ARCHITECTURE.md](ARCHITECTURE.md#pipe-protocol-version-1), with the
  `frames` and `pitches` lines; the command line midis2jam2 passes (`--monks`,
  `--title`, `--label`, `--hidden`, `--x`/`--y`/`--width`/`--height`) and
  `--render`; a `--help` text containing `--hidden`, without which midis2jam2
  keeps the monks out of the scene; and `Resources/faces.png` beside the
  binary, which midis2jam2 reads to draw the monks (it starts the helper in its
  own folder).
- **`DSP/` is shared** with the macOS build: only add functions there, and
  never change existing behaviour.
- **Keep the protocol versioned**: change ARCHITECTURE.md and the version
  number together; additive `set` keys need no new version.
- **Licences**: midis2jam2 and our changes to it are GPL-3.0 and must ship with
  their source when distributed. The Delay Lama code is MIT. The AudioNerdz
  artwork (`Resources/`) and manual are freeware, not relicensed: they may be
  distributed freely with all original files, but not sold or used in
  commercial promotion.

Ports are welcome. If you get the helper or the whole project running on Linux
or macOS, please open a pull request against the repository the change belongs
to, saying what you tested and on which system.
