# Codebase notes

Facts about the two upstream codebases that this project builds on. The
bases are midis2jam2 `4f817a08` (master, app version 2.2.0) and
delalalalay-lama `172db87` (main). Our work is on midis2jam2's
`delay-lama` branch and delalalalay-lama's `voice-helper` branch, and their
`git log` lists the commits. `voice-helper` is pushed to Merken19/delalalalay-lama and
`delay-lama` to the fork Merken19/midis2jam2 (remote `fork`; D62).

Line numbers drift; fix them when a session finds one wrong.

## midis2jam2 (`external/midis2jam2`)

Paths below are under `app/src/`. `cm` = `commonMain/kotlin/org/wysko/midis2jam2`,
`dm` = `desktopMain/kotlin/org/wysko/midis2jam2`.

**Stack**: Kotlin 2.3.10 Multiplatform (desktop JVM + Android), Compose
Multiplatform 1.10.2 for the launcher, jMonkeyEngine 3.9.0 (LWJGL3 on
Windows) for the renderer, kmidi 0.2.4 for MIDI files, Koin for dependency
injection. Needs JDK 21 (README). GPL-3.0.

### Processes

- The launcher (`dm/main.kt`, Compose) starts the renderer as a **separate
  JVM process**: `dm/domain/ApplicationService.desktop.kt:374-391`
  (`ProcessBuilder`, main class `org.wysko.midis2jam2.renderer.RendererMainKt`).
- One performance at a time: `ApplicationService.startApplication`,
  `startQueueApplication` and `startRecording` claim `isApplicationRunning`
  with a compare-and-set (`claimPerformance`), so a second Play that lands
  before the button is drawn disabled starts nothing; a start that throws
  releases it. Test: `ApplicationServiceTest` (`home.play.one-at-a-time`).
- `dm/renderer/RendererMain.kt` decodes its first argument, a base64 JSON
  `RendererBundle` (`dm/renderer/RendererBundle.kt`: `midiFiles`, `config`,
  `recordOptions`), and runs a single file, a queue, or a recording.
- `PerformanceConfig` (`cm/starter/configuration/PerformanceConfig.kt:37`):
  `settings`, `midiDevice` (default `"Gervill"`), `soundbank`, `isLooping`.
  It is built by `PerformanceConfigFactory` from the settings and the home
  tab. Phase 2 added `delayLama` (`DelayLamaConfig`, same folder); phase 3
  passes the home tab panel's one to `create(isLooping, delayLama)`, else it
  is read from the environment (`DelayLamaConfig.fromEnvironment`, D44).

### Audio path (where the router hooks in)

1. `MidiPackage.build` (`dm/starter/MidiPackage.kt:53`) reads the file and,
   for Gervill, makes **one Gervill per MIDI port** (`gervillPorts`) in a
   `MidiPorts`. Phase 2 wraps them there with
   `VoiceHelperManager.route` (`dm/delaylama/`), with the `ImitationPlan`
   from `VoiceHelperManager.imitationPlan` (profile mode, built from the
   file's sequence; its clock is the sequencer's `position`, so the sequencer
   is created before routing and opened after); the soundbank is still loaded
   on the unwrapped Gervills, which `filterIsInstance<GervillMidiDevice>`
   needs. On Windows the performance runs in the launcher's own process (the
   separate renderer process is macOS only), so the launcher's environment
   reaches it.
2. `MidiPorts` (`cm/midi/system/MidiPorts.kt`): port `n` plays on device
   `n % size`; `dispatch(PortedEvent)`. Just before routing,
   `VoiceHelperManager.balance` sets each Gervill's `outputGainDb` (D36):
   minus the balance while a channel is sung, else 0 (the app's Gervill,
   `GervillMidiDevice.instance`, plays every performance of the launcher).
3. `JwSequencerImpl` (`cm/midi/system/JwSequencerImpl.kt`): a pump thread at
   max priority, `sleep(1)` loop (line 107), clocked by
   `System.currentTimeMillis`. `stop()` calls `sendAllNotesOff` (line 187):
   a note-off for 16 channels × 128 notes on every device (only if it was
   running: a seek while paused sends none). `setPosition` runs
   `chaseEvents`, which re-sends CCs (0-126, in number order), poly pressure,
   program, pitch bend and channel pressure for every channel. Since phase 2
   RPNs and NRPNs are left out of the CC replay and rebuilt by
   `ParameterChase` (`cm/midi/system/ParameterChase.kt`) as number + data.
   Live events come from the pump thread, chased ones from the sequencer's
   thread pool.
4. `MidiDevice.dispatch` (`cm/midi/system/MidiEventDispatch.kt`) turns kmidi
   events into `MidiDevice` calls (`cm/midi/system/MidiDevice.kt`: note
   on/off, CC, program, pitch bend, channel and poly pressure, SysEx).
5. `GervillMidiDevice` (`dm/domain/GervillMidiDevice.kt`) sends
   `ShortMessage`s to `javax.sound.midi` Gervill. It is opened with the
   default latency (not set anywhere in the app): it reports 120 ms, and
   sounds 169 ms after a helper (measured 2026-11-04; ARCHITECTURE "Timing").
   Since D36 its `open` goes through `LineGain` (`dm/domain/LineGain.kt`),
   which notes the source lines open on every mixer before and after
   `Synthesizer.open()` and puts `outputGainDb` on the new one's
   `MASTER_GAIN`; `appliedOutputGainDb` reads it back.

Gervill internals (JDK 21 `com.sun.media.sound`, checked 2026-11-04):

- `SoftSynthesizer.open()` gets its own line,
  `AudioSystem.getSourceDataLine(getFormat())` (44.1 kHz, 16-bit stereo),
  opens it with a buffer of its latency, and closes it on `close()`.
  `open(SourceDataLine, Map)` takes a line, but `AudioSynthesizer` is not
  exported from `java.desktop`; only the renderer process (macOS and
  recordings) and the Gradle tool and test tasks have `--add-exports`.
- `SoftMainMixer`: the Universal Real Time master volume (`F0 7F 7F 04 01 ll
  mm F7`) sets `v = value / 16384` and the mix is multiplied by **v²**,
  before the AGC limiter (`SoftLimiter`: gain 0.99 / peak above 0.99, so a
  dense band sits at -0.1 dBFS). `reset()` (GM System On / Off, GM2 On) puts
  the master volume back to full. (A volume change also scales the right
  channel by v, not v², for one buffer: a Gervill slip, harmless.)
- `DirectAudioDevice` lines (every `SourceDataLine` on Windows, Linux and
  macOS) have `MASTER_GAIN` (-80 to +6 dB) after `open` for 8/16-bit PCM of
  up to 2 channels; the native `nWrite` applies it to the samples. Mixers
  are cached by their providers and list their open lines in
  `getSourceLines()`.

- `MidiDeviceManager` (`cm/manager/MidiDeviceManager.kt`) sends the GM/GS/XG
  reset SysEx at start and zeroes CC91/CC93 if reverb or chorus is off.
- Channel key = `port × 16 + channel` (`cm/midi/MidiPort.kt:47`).
- External MIDI devices (`dm/domain/MidiService.desktop.kt`) get every port
  on one device.

### Visual path

- `InstrumentAssignment.assign` (`cm/instrument/algorithmic/InstrumentAssignment.kt:53`)
  groups each channel's events by **Look** (instrument identity from bank,
  program and rhythm state via `assignment/ChannelSetupTimeline.kt` and
  `assignment/VoiceResolver.kt`) and builds one `Instrument` per look. Rhythm
  notes from every channel are pooled into the drum set (channel 10 =
  `PRIMARY_RHYTHM_CHANNEL`). Phase 2 skips Delay Lama channel keys here
  (`config.delayLama.hiddenChannels`) to hide their 3D instruments.
- `Instrument` (`cm/instrument/Instrument.kt`): `isVisible`,
  `calculateVisibility(time)`, `tick(time, delta)`.
- Program names for the UI: `assignment/VoiceCatalogue.kt`.

### Other

- Recording (`dm/record/`) renders audio offline with its own Gervill ports;
  Delay Lama won't be in recordings (D6).
- Settings are stored with Java preferences (`dm/domain/PlatformSettings.desktop.kt`,
  node `org/wysko/midis2jam2`; on Windows the registry key
  `HKCU\Software\JavaSoft\Prefs\org\wysko\midis2jam2`, with Java's
  `/`-escaping of capitals): `app_settings` (the `AppSettings` JSON,
  decoded with unknown keys ignored, `SettingsRepository.kt`),
  `home_tab_state` and `playback_history` (each played file is added).
- Window modes (`AppSettings.GraphicsSettings.WindowMode`, settings tab):
  `Windowed` (default), `BorderlessFullscreen` (Windows only: an undecorated
  window resized to the primary monitor through GLFW,
  `applyBorderlessWindow` in `dm/starter/ApplicationHelpers.desktop.kt`; elsewhere it falls back to
  `Fullscreen`) and `Fullscreen` (jME `isFullscreen`: a GLFW fullscreen
  window at the screen's resolution, which GLFW makes `WS_EX_TOPMOST`).
  The window is created after `MidiPackage.build`, so after the Delay Lama
  helpers' windows. The mode a performance really opens in is
  `effectiveWindowMode` (`cm/starter/WindowModes.kt`): the fallbacks above, plus Fullscreen as
  borderless while Delay Lama sings (D47). It lives in its own file because
  `cm/starter/ApplicationHelpers.kt` reads the screen when its class loads,
  which throws in headless tests.
- Behaviour catalogue: `docs/SPEC.md`,
  `app/src/desktopTest/resources/spec/behaviour.yaml`, and
  `SpecCoverageTest`, which fails on uncited behaviour.
- Gradle: `./gradlew run` (launcher; `--args="<file.mid>"` plays a file at
  once, via `CmdStart`), `:app:compileKotlinDesktop`, `:app:desktopTest`.
  Run tasks add `--add-exports=java.desktop/com.sun.media.sound=ALL-UNNAMED`.
  Configuring the project needs an Android SDK even for desktop tasks:
  `ANDROID_HOME` (here `%LOCALAPPDATA%\Android\Sdk`) or `local.properties`.
- Logging: `logger()` (`cm/util/Logging.kt`) has only `debug`, `warn` and
  `error`.
- Tests: `NoOpMidiDevice` and `NoOpSequencer` (`desktopTest/.../testing/
  NoOpSequencer.kt`) record what they are sent; `HeadlessPerformance.start`
  takes a `delayLama` config (phase 2) for assignment tests. The suite runs
  headless and must pass without an audio device: `DelayLamaBalanceTest`
  opens a real Gervill line and skips (JUnit assumption) when none opens.
- Delay Lama tools (`desktopTest/.../tools/delaylama/`, Gradle tasks in
  `app/build.gradle.kts`): `LatencyProbe` (`:app:delayLamaLatency`) and
  `BalanceRender` (`:app:delayLamaBalance`: `band.wav`, `full.wav`, each
  monk, and `live.wav`, the band at the config's balance plus the monks; in
  profile mode by default, like live playback; its argument is
  `<file>;<out dir>;<config, any number of ;-settings>;<seconds>`), and
  `ScenePreview` (`:app:delayLamaScenePreview`, phase 5: the 3D scene with
  the monks standing in it, rendered on jME's `OffscreenSurface`, a hidden
  GLFW window with dummy input, from a fake frame source; the stage,
  lights and instruments but no background or camera manager; argument
  `<file>;<out dir>;<config>;<seconds,...>`; writes `scene_<s>s_wide.png`
  from camera 1A, `_choir.png` close to the first sung choir, and `_off.png`
  with the switch off).
- Profile mode (`dm/delaylama/`, 2026-11-05): `ImitationProfiles.kt` loads
  `profiles/imitation.json` and is a port of `tools/profiles/expand.py`
  (resolve, program map, `setLines`, `fitShift`); `ChannelScore.kt` reads the
  sung channels' notes ahead (lengths, bank and program at each note);
  `ImitationPlan.kt` picks each channel's profile and octave shift and looks
  up note lengths. `DelayLamaProfilesTest` runs `expand.py --dump` (skipped
  without Python or outside this checkout) and compares every profile's lines
  and the map for programs 0-127. The JSON is outside Gradle's inputs, so
  after changing only `imitation.json` run it with `--rerun`.

- Launcher panel (phase 3, 2026-11-05): `dm/ui/home/delaylama/DelayLamaPanel.kt`
  (`DelayLamaCard` on the home screen's `LazyColumn`, `DelayLamaScreen`,
  `DelayLamaText`), and in `dm/delaylama/`: `ChannelSurvey.kt` (a file's
  channels via `ChannelSetupTimeline` and `VoiceCatalogues`),
  `DelayLamaChoices.kt` (`ChannelChoice`, `FileChoices`, `DelayLamaOptions`,
  `DelayLamaStore`), `DelayLamaPanelModel.kt` and `StandaloneLauncher.kt`.
  `ChannelChoice.initial` is a channel's starting choice (sung, D45);
  choices are saved only when the user changes one, so an untouched file
  keeps following it, and `DelayLamaStore.rememberedConfig(file, survey)`
  falls back to it for a file with nothing saved. Koin singles in `dm/di/UiModule.desktop.kt`; `DesktopHomeScreenModel`
  takes the panel and calls `select` from `setMidiFile` (the file picker
  goes through it too). Desktop stores every `StoreName` in one preferences
  node; the panel keeps its own node, so no `StoreName` (and no Android
  mapping) was added. Tests: `DelayLamaPanelTest`.
- Packaging (phase 6, 2026-11-07): the Windows package is Compose
  Desktop's jpackage app image (`:app:createDistributable`, block
  `compose.desktop.application.nativeDistributions` in `app/build.gradle.kts`,
  now with `includeAllModules = true`; output
  `app/build/compose/binaries/main/app/midis2jam2/`: `midis2jam2.exe`,
  `app/`, `runtime/`). Upstream releases use install4j (`install4j/`), not
  available here. The jpackage launcher sets the system property
  `jpackage.app-path`; `dm/delaylama/DelayLamaInstall.kt` turns it into the
  app folder, and `VoiceHelperManager.locateHelper`,
  `StandaloneLauncher.locate` and `ImitationProfiles.locate` take an
  `appDirectory` (default from it) that they search right after an explicit
  path. `DelayLamaPanelModel` passes it through and logs the three resolved
  paths at start (`Delay Lama: app folder ...`, debug, read by
  `tools/package/check_package.ps1`). Recording's renderer JVM
  (`ApplicationService.detectRendererClasspath`) now takes the launcher's
  class path in a jpackage image too (it knew only Gradle and install4j);
  jlink leaves out `runtime/bin/java.exe`, so the package script copies it
  from the same JDK. Test: `DelayLamaPanelTest`
  (`delaylama.package.locate`).
- Window layout and mixer (2026-11-08, D57-D58): `dm/delaylama/MonkWindowLayout.kt`
  (columns on the primary screen's work area, physical pixels from Java's
  scaled bounds and insets; frame allowances for a titled window at 96 DPI:
  31 top, 8 sides and bottom), `DelayLamaMixer.kt` (strips as a `StateFlow`,
  listeners get the keys whose level changed),
  `dm/ui/home/delaylama/DelayLamaMixerWindow.kt` (a `ComposeWindow` opened on
  the EDT outside the launcher's composition, so it reads the theme from
  Koin's `SettingsModel` directly; `DelayLamaMixerContent` is the
  composable), and in `ChannelSurvey`: `playingChannels`, `instrumentNames`.
  `MidiPackage.build(showMixer)` wires them (`delayLamaPorts`); only
  `ApplicationService`'s single-file play passes `true`. Tests:
  `DelayLamaMixerTest`; the panel preview also renders `mixer_*.png`.
- Delay Lama switches (2026-11-08, D60; per channel since 2026-11-09):
  `DelayLamaMixer.Strip.isSwitchOn` / `isDelayLamaOn`, and on the mixer
  `isDelayLamaOn(key)`, `isAnyDelayLamaOn`, `setDelayLamaOn(key, on)`,
  `setAllDelayLamaOn` and `addSwitchListener` (gets the keys that changed);
  the window's `DelayLamaSwitches` card and a `Switch` on each sung strip. In
  `DelayLamaRouterDevice` `isSwitchable` (a mixer is present) sends every
  sung-channel event to `device` too, `shadowVolume` (CC 7 0 while on),
  `helperGain` (0 while off) and `applySwitch(keys)`, all by channel;
  `VoiceHelperManager.followSwitch` sets Gervill's `outputGainDb` from
  `isAnyDelayLamaOn`. `MidiPackage.delayLamaMixer` and
  `sungInstrumentsOnStage` (a function of the channel key) reach
  `Midis2jam2Application` (desktop) and from there
  `PerformanceManager.sungInstrumentsOnStage`; `InstrumentAssignment` builds
  hidden channels when it is set and gives their instruments
  `Instrument.stageGate` (bound to their channel), which `isVisible`
  (getter and setter) checks every
  frame; `CinematicCamPlugin` tests `isPresentable` (since phase 5; it was
  `isAllowedOnStage`, which `ClassicAutoCamPlugin` still tests). Tests:
  `DelayLamaMixerTest`, `DelayLamaSetupTest`
  (`HeadlessPerformance.start(sungInstrumentsOnStage = ...)`).
- Monks in the scene (phase 5, 2026-11-09, D66-D68; branch `monk-sprites`):
  `MonkView` and `isMonksInScene` in `DelayLamaConfig.kt`;
  `cm/delaylama/MonkStage.kt` (`MonkStage`, `SungInstrument.spot`/`bounds`
  (by choir size; the obstacles come from a lazy list in
  `InstrumentAssignment` through a `MonkFloorPlan`, which also keeps choirs
  of different channels apart), `MonkFloor` (the stage floor: y 0, radius 140,
  found by raycasting `Models.Stage.Stage`, whose wall stands at about
  145-150 and is 40 high), `MonkSpread` (D70: the fan and the tiers, applied
  in `SungInstrument.spot` through its `spread` function; the slot is the
  channel's place in `MonkStage.channels` sorted), `SungChannel.playing`/`standingAt`, `MonkSize`;
  a package of the same name as the desktop one); `dm/delaylama/MonkFrames.kt` (per-channel frame state,
  `parseFrames`, `parsePitches` (D71), the fallback listeners), `MonkNod.kt` (D71: how far one
  monk rises while its pitch moves) and `MonkBillboards.kt` (`MonkScene`,
  the app state with a `MonkNod` per monk, `liftsOf`, `cutFaces`). `VoiceHelperManager` got `hasScene`, `canHide`
  (`knowsHidden`: runs `--help` once per exe and time stamp), `facesBeside`,
  `monksInScene`, `framesOf`; its `startProcess` is now nullable (`null`
  starts the real helper with its stdout fed to `MonkFrames.accept`).
  `DelayLamaRouterDevice` got `monkFrames` (`windowVisible`, `applyWindow`).
  `MidiPackage.monkScene` reaches `Midis2jam2Application` and
  `Midis2jam2QueueApplication`, which set `PerformanceManager.monkStage` and
  attach `MonkBillboards` (not for recordings). In `Instrument`: `standIn`,
  `standInBounds`, `wouldBeVisible` (the visibility ignoring the gate; the
  old `isVisible` backing field is now `isWanted`), `isStandInShown`,
  `isPresentable`, `holdsPlace` (used by `updateInstrumentIndex`,
  `findSimilarAndVisible` and `atRest`). `SubjectExtraction.kt`:
  `restingBox` returns the stand-in's box, `ownRestingBox` the instrument's.
  Panel: `DelayLamaOptions.view`, `ViewRow`, `DelayLamaText.view`. Tests:
  `DelayLamaSceneTest` (`HeadlessPerformance.start(monkStage = ...)`).
  `faces.png` frames are 311 × 291 px on a 314 × 311 grid (the helper's
  `kFaceWidth`/`kFaceHeight`, `kFaceCellWidth`/`kFaceCellHeight` in
  `Windows/app.h`).
- The app has no Compose UI tests; `ImageComposeScene` (Compose desktop,
  already on the test classpath) renders a composable offscreen, which the
  `delayLamaPanelPreview` tool uses. `AppTheme` needs Koin; the tool uses
  `MaterialTheme(lightScheme/darkScheme, appTypography())` instead.
- `LocalizationTest` fails if a string in `values/strings.xml` is missing
  from any of the 17 other locales; hence D43.

## delalalalay-lama (`external/delalalalay-lama`)

Its own `CLAUDE.md` is authoritative for that repo (rules, build, tests,
history). The facts this project depends on:

### DSP (`DSP/`, shared with the macOS build: add only, never change)

- API: `DSP/synth.h`. A monophonic last-note stack of 16 notes; unison up to
  10 voices.
- **Every note sounds an octave below its MIDI pitch**: `grain_period`
  (`DSP/voice.c:191`) uses `note - 12`, as MonkSynth does. MIDI note 57 (A3)
  sings at 110 Hz. The helper adds the octave back to sing the written pitch (D14). Measured on renders
  (phase 4a): right from 16 Hz to 1 kHz, within +3 to +14 cents. Grains are
  20 ms, so below a sounding ~50 Hz (notes under ~43) the voice becomes a
  pulse train; at a sounding 2 kHz it is ~15 dB quieter; above ~400 Hz the
  loudness jumps 5–8 dB from note to note (harmonics vs. formants).
- **Velocity is ignored**: `monk_voice_note_on` (`DSP/voice.c:402`) does
  `(void)velocity`. The helper turns velocity into level instead.
- Pitch bend ±12 st: `monk_synth_set_pitch_bend` (`DSP/synth.c:248`), applied
  at once (no smoothing); the helper reaches it through `dl_set_pitch_bend`.
- Level: `monk_synth_set_level` (`DSP/synth.c:359`), smoothed about 5 ms;
  the helper reaches it through `dl_set_level`. It is applied **after the
  echo** (`process_chunk`, `DSP/synth.c:445`), so changing it per note also
  changes the echo tail; the target is updated once per process call.
- **A note-off leaves a tail**: with no envelope the voice stops making grains
  at once, but the grains already in the overlap buffer play out (up to one
  20 ms grain; `monk_voice_process`, `DSP/voice.c`). The output level applies
  to that tail, so the helper never raises a released monk's level
  (phase 1 fix, 2026-11-04).
- **The three formants are equally strong** (`compute_grain`), and F3 has a
  narrow 62.5 Hz bandwidth. On high notes, where harmonics are far apart, a
  harmonic that lands on F3 (about 3 kHz at voice 0.6) rings as a whistle
  about as loud as the low partials, on some notes only (phase 4a trumpet:
  A4, B4, D5).
- **Loudness**: at the standalone's defaults (volume 0.28, level 0.75) one
  monk on middle C already peaks near 0 dBFS (RMS about -13 dBFS); lower
  notes are louder (pitch compensation). Hence the helper's lower default
  volume (DECISIONS D8).
- The output is deterministic: every voice's RNG and vibrato phase are seeded
  the same way, so a script renders the same samples every time. It also
  means every monk of a choir has the same vibrato jitter pattern.
- CC routing `monk_synth_midi_cc` (`DSP/synth.c:368`): 1 vibrato, 5 glide,
  7 volume (`value × 127 × 0.001`, so at most 0.127; default 0.1), 12 echo
  mix, 13 voice.
- **Vowel axis**: `FORMANT_FREQS` (`DSP/voice.c:29`). By the formant values,
  0 → 1 runs u, o, a, e, i (the comment says a, e, i, o, u). Three formants,
  equally loud; F2 rises steadily, F1 (openness) peaks at a (0.5). The vowel
  is read once per grain (once per pitch period).
- **The vowel snaps during MIDI playback**: in the MIDI branch of the ramp
  code (`DSP/voice.c:233` onwards) `current_vowel = target_vowel` every
  sample. Only the XY flag path ramps the vowel (`monk_voice_set_vowel`,
  line 471).
- Glide during MIDI playback: constant slew of 12 / (glide + 0.01)
  semitones/s, snapping within 0.2 st (a fifth took 288 ms at 0.5).
- Voice: formant scale `0.75 + 0.5 × voice`.
- Vibrato (`compute_vibrato`, `DSP/voice.c:254`): peak deviation is
  depth + 0.2 st, so it never stops (measured ±0.21 st at depth 0); rate
  ≈ 6 × 4^(2r−1) Hz × (1 + 0.2 depth), jittered (1.4 Hz at r 0, 5.9 at 0.5,
  24 at 1).
- Breath (aspiration): default 0.5; two inharmonic partials (about 3.8 and
  4.95 kHz, decaying in about 2 ms) in each grain, so a ping per pitch
  period rather than noise. Where a harmonic of the note lands near those
  partials (A4 and E5 in phase 4a's trumpet render), they ring as a faint
  whistle, strongest during a full breath burst.

### Windows app (`Windows/`)

- Bridge: `Sources/standalone_bridge.h` (shared API) and
  `Windows/standalone_bridge_win32.c`. One critical section per handle.
  `dl_create` opens **every WinMM MIDI input** (via `create_handle`, line 156).
  In `handle_midi_message` (line 78): note 127 is reserved as the flag's
  placeholder (so the helper cannot sing note 127 either), **the pitch wheel
  sets the vowel**, CC 120/123 mean all notes off, and other CCs go to
  `monk_synth_midi_cc`.
- Windows-only bridge additions for the helper: `Windows/voice_bridge.h`
  (`dl_create_without_midi`; `dl_set_pitch_bend`, `dl_set_level`,
  `dl_set_vowel`; phase 4b: `dl_set_vibrato_seed`, `dl_set_formant_bandwidth`
  (round 3); phase 4c: `dl_copy_vibrato`, which locks one handle at a time,
  and `dl_set_formant_scale` (pipes); phase 5: `dl_get_sung_note` (D71);
  and `dl_voice_note_on` /
  `dl_voice_note_off`, one note per handle with no note-stack fallback). The
  macOS bridge has no counterpart.
- DSP additions (phase 4b, D18): `monk_synth_set_vibrato_seed` in
  `DSP/synth.c` restarts the vibrato jitter from a seed (unison voice i gets
  seed + 7919 i, as at creation); `monk_synth_set_formant_bandwidth`
  (round 3) rebuilds every voice's `exp_decay` table with the bandwidths
  scaled (scale 1 is the exact default table; `build_aspiration` used the
  table once at init, so the breath partials stay as they are). Phase 4c
  (D46): `monk_synth_get_vibrato_state` / `monk_synth_set_vibrato_state`
  read and write each voice's vibrato phase, jitter, jitter counter and RNG
  (`MonkVibratoState` in `synth.h`), so `vibrato.lock` can put synths in
  step. Phase 4c pipes (D49): `monk_voice_set_formant_scale` (`DSP/voice.c`,
  appended) rebuilds one formant's spline table as `build_formant_tables`
  does, with its five vowel points times a factor (1 = the exact default
  table, 0 = silent, since a 0 Hz damped sine is zero), and
  `monk_synth_set_formant_scale` applies it to every unison voice; the voice
  size still scales the result. Phase 5 (D71): `monk_synth_sung_note`
  reads the main voice's `current_pitch + pitch_bend_offset` (glided, bent,
  no vibrato) for the pitch reports. None of them is called by the
  standalone.
- Pitch quantization (measured in phase 4c): `grain_period` floors the pitch
  to 1/32 semitone (flat by up to 3 cents), then `monk_voice_process`
  truncates the period to whole samples (sharp). The vibrato floor dithers
  both, so a note's mean pitch is +2 to +5 cents from C3 to A4 and +9 to +11
  at C5-D#5. High notes therefore move in steps (30-50 cents at F5-E6, ~17 at
  A4), and vibrato and glides become staircases up there (IMITATION.md §16).
  The vibrato LFO (`compute_vibrato`) only advances while the voice is
  active.
- Formants (`DSP/voice.c`, `FORMANT_BW` and `compute_grain`): bandwidths
  32.5 / 47.5 / 62.5 Hz, and the three formants are equally strong. That is
  why a moving vowel can be heard as a moving pitch (IMITATION.md §16).
- Audio: `Windows/audio_engine.h`. WinMM waveOut, 48 kHz stereo 16-bit,
  `kAudioBuffers = 4` × `kAudioFrames = 512` (≈10.7 ms per block, ≈43 ms
  queued). Events land between blocks. `AudioEngine` plays one bridge handle
  or a render callback (the helper's choir mix).
- Monk animation: `MonkAnimator` (`Windows/monk_animation.h`). Singing
  frame = `6 + round(vowel × 23)`, clamped to 6–29. The sheet is
  column-major (`Windows/monk_art.cpp:15`, 6 rows per column): column 0 is
  closed lips (idle only), 1 pout (u), 2 round (o), 3 wide (a), 4 smile
  (e, i); the row is the head pose. Idle: hold frame 5 with
  blinks on frame 2, then a 24-step shuffle after 4.8 s. One animator (idle
  clock) per monk, with an optional idle offset; the choir uses
  `kChoirIdleOffsetsMs`. The standalone's `App::active_frame`
  (`Windows/delay_lama_win32.cpp:288`) delegates to its one animator.
- Monk artwork: `FaceFrames` (loads the 30 frames) and `FaceCache` (draws a
  frame pre-scaled) in `Windows/monk_art.h`. `MonkWindow`
  (`Windows/monk_window.cpp`) and the helper's `ChoirWindow` use them;
  `ClassicWindow` still has its own face cache.
- Artwork: `Resources/faces.png` (30 frames, 5 columns × 6 rows; each
  314 × 311-px cell holds a 311 × 291-px frame at its top left: a 3-px
  border on the right and 20 unused rows below, `kFaceHeight` in
  `Windows/app.h`), `background.png`,
  `about.png`. `Resources/` must sit next to the exe.
- No command-line arguments and no single-instance guard. Settings are in
  `%APPDATA%\DelayLamaStandalone\settings.ini` (or a portable `settings.ini`
  next to the exe), shared by every instance.
- Licensing: code MIT; DSP derived from MonkSynth (MIT,
  `MONKSYNTH-LICENSE.txt`); artwork is AudioNerdz freeware, not relicensed.

### DelayLamaVoice (`Windows/voice_*`, phases 1, 4b and 5)

- Console exe built next to the standalone (`Windows/build/Release/`), with
  `Resources/faces.png` copied beside it. Usage and commands:
  `DelayLamaVoice --help` and `Windows/README.md` in that repo.
- `voice_protocol.*`: the parser for protocol 1 (ARCHITECTURE.md;
  `kProtocolVersion` 1, `kOldestProtocolVersion` 0).
  `voice_allocator.*`: which monk sings which note (O3). `voice_choir.*`: one
  bridge handle per monk, channel state (bend, CC7/11/64, gain), the `set`
  keys, and the mix; plain or profile mode, with one recursive mutex shared
  by apply, render and the window's queries. `voice_articulator.*` (phase
  4b): profile mode, the per-note curves, its own allocation, pan and the
  choir echo; its keys are listed once in `voice_profile_keys.inc`.
  `voice_render.*`: `--render` and the WAV writer. `voice_frames.*`
  (phase 5, D68): `ChoirFrames`, the frame each monk shows (singing frame,
  closed lips, idle clock) and when a `frames` line is due; also when a
  `pitches` line is due and what it says (D71, `take_pitch_report`, from
  `Choir::monk_sung_note`). These six are
  the `delay_lama_voice_core` library that CTest links.
- `voice_window.*`: the choir window (monks side by side, equal cells, one
  shared `FaceCache`; with `--label`, a 20 dip strip under them with the
  text, D57). It draws `ChoirFrames`' frames, updates them on its 30 ms
  timer also while hidden, and prints the `frames` and `pitches` lines
  (D68, D71).
  `voice_main.cpp`: options (`--hidden`), the stdin reader thread
  (`ReadFile`, never joined), the stdout lock (`reply`), audio, exit codes,
  and the process priority and power throttling opt-out (D59).
- Tests: `Tests/voice_*_checks.cpp`, CTest `delay_lama_voice_protocol`,
  `_allocator`, `_render`, `_frames`, `_render_cli`, and `_frames_cli`
  (`Tests/voice_frames_cli.cmake` runs the live helper `--hidden` and
  silent on `voice_scripts/frames.txt` and checks its stdout; skipped
  without an audio device). Command scripts for renders and
  ear checks: `Tests/voice_scripts/`. The articulator checks are in
  `voice_render_checks.cpp` (`articulator_*`: determinism, written pitch,
  first-tick values, the onset flare with and without `onset.mask`,
  `onset.bandwidth` returning to the DSP's own sound, `onset.after_rest`,
  glide overshoot, blips between notes, `vibrato.lock` holding a fifth
  steady, and `voice.formant3` 0 and `dyn.gain`); `Tests/dsp_hardening.c`
  checks the vibrato state copy and the formant scale (1 restores the
  default samples exactly).
- Profile data and tools in the top-level repo: `profiles/imitation.json`
  (D19) and `tools/profiles/expand.py` (JSON to `set` lines; midis2jam2's
  `ImitationProfiles` must stay in step with it, see above). The tuning
  tools for 4c families are in `renders/phase4c/` (IMITATION.md §15).
