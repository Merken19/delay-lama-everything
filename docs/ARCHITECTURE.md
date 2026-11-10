# Architecture

How the parts fit, following [DECISIONS.md](DECISIONS.md). File references
are relative to `external/midis2jam2/app/src/` (Kotlin, `cm` = commonMain,
`dm` = desktopMain) or `external/delalalalay-lama/` (C/C++). More detail is
in [CODEBASE_NOTES.md](CODEBASE_NOTES.md).

## Components

### 1. midis2jam2 launcher (Compose desktop UI)

The home tab picks a file, a MIDI device and a soundbank. On Windows the
performance runs in the launcher's process (the separate renderer process,
fed a base64 JSON `RendererBundle`, is for macOS and recordings). Delay Lama
adds the following (`dm/.../delaylama/` and `dm/.../ui/home/delaylama/`):

- A **Delay Lama card** on the home tab (`DelayLamaCard`): what is sung in
  the chosen file, a *Choose channels* button that opens the **panel**
  (`DelayLamaScreen`), and **Add Delay Lama**.
- The panel lists each channel Delay Lama could sing (`ChannelSurvey`: every
  port's channels with melodic notes, never channel 10). For each it shows
  the programs (named by the file's GM/GS/XG/GM2 mode), note range, most
  notes at once and note count. Each channel has a switch, the choir size
  (1–8), the imitation (auto, plain, or any profile) and a level in dB. A new
  channel starts on (D45), so a file sings every channel it can until the
  user switches some off. A file played from the command line without the
  environment variable sings the same: its remembered choices, else these
  starting ones (`DelayLamaStore.rememberedConfig`). Below the channels are the options for every
  file: balance, offset, imitation strength, where the monks are shown (in
  the scene, their windows, or both; D67), keep the 3D instruments, and the
  paths of the helper, the standalone and `imitation.json`, each showing the
  file found.
- `DelayLamaPanelModel` (a Koin single) holds the state. `select(file)`
  reads the channels off the UI thread and restores the file's remembered
  choices. Every change is saved at once in `DelayLamaStore`, a preferences
  node of its own: the options as JSON, and each file's `FileChoices` under
  the SHA-256 of its contents (O12).
- Play hands the panel's `DelayLamaConfig` to the performance
  (`ExecutionState.delayLama`, `PerformanceConfigFactory.create`).
  Per-channel settings are in `DelayLamaConfig.options` (choir, gain,
  profile). D44 says where choices come from in each kind of start.
- **Add Delay Lama** (`StandaloneLauncher`) starts one more
  `DelayLamaStandalone.exe` in its own folder (beside its `Resources/`). It
  looks at the options' path, then next to the app, next to the helper, and
  in a development checkout. The standalone is not tied to the file (D7) and
  outlives the app.
- The panel's words are English only (`DelayLamaText`, D43).

### 2. midis2jam2 renderer (jMonkeyEngine)

`MidiPackage.build` (`dm/.../starter/MidiPackage.kt`) makes one Gervill
`MidiDevice` per MIDI port. The `JwSequencerImpl` pump thread sends every
event through `MidiPorts.dispatch` to `MidiDevice.dispatch` (`cm/.../midi/system/`).
Delay Lama hooks in there:

- **`DelayLamaRouterDevice`** wraps each port's device. Events on sung
  channels go to that channel's helper as protocol lines. Everything else,
  and every SysEx, reaches the device untouched. `VoiceHelperManager.route`
  wraps the ports after the Gervills are made and before the sequencer opens
  them, so the sequencer and the reset logic are unchanged. The router does
  the following:
  - It turns the stop sweep (a note-off for each note 0–127) into one
    `allnotesoff`.
  - It decodes RPN 0 into `bendrange` (NRPN 99/98 deselects, CC 121 resets
    the selection) and puts it back to 2 on a GM, GM2, GS or XG reset.
  - It tracks bank select, so `program` carries `msb × 128 + lsb`.
  - It passes every CC on as `cc` and drops aftertouch.
  - In **profile mode** (the default, D41) it sends, once the helper is up,
    `set articulator 1`, `exaggerate`, the staged profile of the channel's
    program and bank (`ImitationProfiles`, the Kotlin port of
    `tools/profiles/expand.py`) and `set range.shift`, the channel's octave
    fit (D37). It sends them again at a program change or reset that maps to
    another profile. Each `on` carries the note's length in the file
    (`ChannelScore`). `profile=plain` sends phase 2's lines.

  A channel whose helper can't start plays on the device instead.
- **`VoiceHelperManager`** finds `DelayLamaVoice.exe` (the config's `exe`,
  next to the app, or `delalalalay-lama/Windows/build/Release/` under an
  `external` folder above the working directory). It starts one helper per
  channel when the ports open, with `--monks`, a title, a `--label` naming
  the channel's instruments (`ChannelSurvey.instrumentNames`), and a place
  from `MonkWindowLayout` (D57). The ports close when the performance ends,
  which sends `quit` and closes stdin. A helper still running 2 s later is
  killed, and a shutdown hook closes any left over.
- **`VoiceHelperProcess`** (`VoiceHelper.kt`) speaks to one helper. A writer
  thread holds each line back by the offset (D30) and writes it. The
  helper's stdout and stderr go to the log (`frames` lines only the first
  and every 200th, with a count when the helper ends), and stdout is read
  without pause, so the helper never blocks on a full pipe.
- **Monk windows and window modes.** The helpers start before the 3D window
  exists. Their windows are always on top and open without taking the focus.
  They stay above windowed and borderless performances. A real fullscreen
  window is topmost too and covers them, so while a channel is sung,
  Fullscreen opens as borderless on Windows (D47; `effectiveWindowMode`,
  `cm/.../starter/WindowModes.kt`).
- **Monks in the scene** (D66–D68; `monk-sprites` branch). With the view in
  the scene or both (`DelayLamaConfig.view`, default scene) and the
  instruments hidden, a live performance's `VoiceHelperManager`
  (`hasScene`, set by `MidiPackage`) puts the monks in the 3D scene if it
  can: the helper's `--help` lists `--hidden` (asked once per exe) and
  `Resources/faces.png` is beside it. Each helper then gets `set
  report.frames 1` and `set report.pitches 1` (D71) after `hello`, and in
  the scene view starts with `--hidden`. Its `frames` and `pitches` lines
  go into the channel's `MonkFrames` (read on the render thread); an older
  helper's `error` for `report.pitches` changes nothing but the nod. A channel shows its window instead (the router sends
  `set window.visible 1`, at once) when its helper answers that line with an
  `error` naming `report.frames`, reports nothing within 5 s, or
  `faces.png` can't be read; without the helper support or `faces.png`,
  every channel stays in its window, as do the windows view, `keep3d`, the
  tools and the tests. Recordings get no monks (D6).
  - `MonkScene` (dm) is the performance's `MonkStage` (cm): which channels
    stand in the scene, and whether one is shown now (its frames come and
    its switch is on). `InstrumentAssignment` then builds those channels'
    instruments even without a mixer, gated off stage, gives them a
    `standIn`, and lists them per channel as `SungChannel`s with their note
    starts (`PerformanceManager.sungChannels`).
  - `MonkBillboards` (dm, an app state after the performance) cuts
    `faces.png` into 30 textures as the helper's window does (frame =
    column × 6 + row at (column × 314, row × 311), 311 × 291 px, opaque and
    unlit) and gives each channel a node of K quads side by side, turned to
    the camera about the vertical axis (`BillboardControl`, AxialY). Each
    frame it stands the choir at the instrument the channel plays now or
    played last (`SungChannel.standingAt`: the latest note start), while
    that instrument would be on stage ignoring its gate
    (`Instrument.wouldBeVisible`). The choir stands on the stage floor
    (D69; `MonkFloor`: y 0, a disc of radius 140 inside the wall, measured
    from the stage model) below the middle of the instrument at rest
    (`ownRestingBox`), brought towards the middle of the stage until all of
    its footprint, facing the audience, is on the floor, and stepped towards
    the audience (+Z, up to 160) when something reaching below its top is in
    the way: every instrument that may be on stage, at rest, measured once,
    and the choirs of other channels placed before it (`MonkFloorPlan`). The place is
    kept in the instrument root's own space, so the choir slides across the
    floor as the instrument would; a slide up or down leaves it on the
    floor. A monk is 48 units high, a choir at most 208 wide (`MonkSize`;
    the user's size, D69). The performance's spread (D70; `MonkStage.spread`,
    read every frame: the mixer's slider, else the config's) then moves it
    from that floor place towards the back and sides in a fan, in channel
    order, and up in two alternating tiers (`MonkSpread.place`, given to
    each `SungInstrument` by `InstrumentAssignment`); never lower than on
    the floor.
  - Each monk nods (D71, `MonkNod`, one per monk): it rises above its place
    in the choir while the note it sings (`MonkFrames.pitches`) is away from
    where its pitch has settled (a follower with a 0.3 s time constant), by
    up to 12 % of its height (`tanh` of the distance over 3 semitones,
    eased over 0.06 s), either way, and never below its place. A note begun
    from silence starts settled. `MonkBillboards.refresh` moves the nods by
    the performance's time: still while paused, reset after a jump back or
    while the choir is hidden.
  - An instrument whose stand-in is shown holds its place
    (`Instrument.holdsPlace`): instruments of its kind stand beside the
    choir as they would beside it. `CinematicCamPlugin` takes it as on stage
    (`isPresentable`), `restingBox` frames the choir's box (`standInBounds`),
    and a shot of a choir gets the normal lens where it asks for the long
    one (`baseFov`). `ClassicAutoCamPlugin` chooses its angles for an
    instrument only while the instrument itself is on stage
    (`isAllowedOnStage`): they are set for where the instrument floats.
- **Hidden instruments**: `InstrumentAssignment.assign` skips sung channels
  unless `keep3d` is set (O7). With a mixer, or monks in the scene, it builds
  them anyway, kept off stage by `Instrument.stageGate` (the switch, below).
- **Config**: `DelayLamaConfig` (`cm/.../starter/configuration/`) in
  `PerformanceConfig.delayLama`. The panel makes it for home-tab plays. For
  the command line, the queue and the tools, `PerformanceConfigFactory` reads
  the `MIDIS2JAM2_DELAY_LAMA` environment variable or the
  `midis2jam2.delayLama` system property (D44; syntax in CLAUDE.md).
- **Mixer** (D58). A launcher performance with sung channels opens
  `DelayLamaMixerWindow` (Compose, always on top, at the right of the main
  screen; `MidiPackage.build(showMixer = true)` from `ApplicationService`
  only). `DelayLamaMixer` holds a strip per channel the file plays, with
  mute, solo and volume (−30 to +6 dB), and tells the routers which levels
  changed. A sung channel's level goes to its helper as `set gain` (panel
  gain × level). Any other channel's level scales its CC 7 by the square
  root, and is reapplied after a system reset. The window closes when the
  routers close.
- **Delay Lama switches** (D60). Each sung channel's strip in the mixer has
  a switch that chooses who plays that channel: its monks (on, at start) or
  the synthesizer (off), never both. The card at the top counts how many are
  on, with a button that switches them all off (when all are on) or all on.
  `DelayLamaMixer.Strip.isSwitchOn` holds each, and switch listeners get the
  keys that changed. Nothing starts or stops. With a mixer, a router sends
  every event of a sung channel to its helper **and** to the synthesizer,
  and a switch only changes that channel's levels:
  - On: the synthesizer's copy gets CC 7 = 0. The file's CC 7 values are
    held back, and resent after resets.
  - Off: the helper gets `set gain 0` and `set window.visible 0`, the
    synthesizer's copy gets the file's CC 7 scaled by the mixer. Once every
    sung channel is off, `VoiceHelperManager.followSwitch` puts Gervill's
    line back to 0 dB (and down by the balance when any is on again). The
    channel's monks in the scene are hidden too. Switched on, a window comes back only
    where its channel's view shows it (`MonkFrames.isWindowWanted`).

  The helper's lines wait the offset, which matches Gervill's longer buffer,
  so both swap at the same moment. The sung channels' 3D instruments are
  built and kept off stage while their channel's switch is on
  (`PerformanceManager.sungInstrumentsOnStage`, by channel key, and
  `Instrument.stageGate`; the
  cameras skip them). Their rhythm notes stay off stage, because the drum set
  is shared. Without a mixer (queue, tools, recordings) sung channels never
  reach the synthesizer.
- **Balance** (D34, D36). While any channel is sung, every Gervill plays
  `balance` dB quieter (default 6), through the master gain of its Java Sound
  line (`dm/domain/LineGain.kt`, set from `VoiceHelperManager.balance` before
  the ports open). The gain comes after Gervill's limiter and outside MIDI.
  Other MIDI devices get no balance.

### 3. DelayLamaVoice.exe (the helper)

A Win32 console program, a CMake target beside the standalone in
`external/delalalalay-lama/Windows/` (`voice_*`). It reuses `DSP/`, the WinMM
player (`Windows/audio_engine.h`), the face artwork and the monk frame logic.

- **One process per sung channel** (D1). It hosts up to *K* monk synths (the
  choir, D3), mixes them into **one** waveOut stream, and shows them side by
  side in one window (O4).
- **Voice allocator** (plain mode): a note goes to the lowest-numbered
  silent monk. When none is free it steals per O3 and D11, taking
  pedal-held notes first, and the stolen monk glides. Choir size is
  `--monks` 1–8 (default 4).
- **Levels**: velocity, CC7 and CC11 on the GM curve times `gain` (D8). A
  released monk only gets quieter (D27). Profile mode uses the moderate
  velocity curve (D21) and 4× headroom (D35).
- **Articulator** (`Windows/voice_articulator.*`, profile mode): applies the
  channel's profile to each note ([IMITATION.md](IMITATION.md)). The choir
  renders 1 ms sub-blocks and the articulator sets every monk's values
  between them (D20). It allocates voices itself (connected notes stay on
  one monk) and sings the written pitch plus the router's `range.shift`. The
  DSP envelope and the synths' echo are off, and one echo runs on the mix.
  In profile mode the mouth follows the vowel and shows closed lips (D16).
- **Window**: frameless or titled, always on top, opened without taking the
  focus. The geometry comes from `--x --y --width --height` (client area,
  physical pixels). Other options: `--no-topmost`, `--no-title-bar`,
  `--title` and `--label` (a strip under the monks naming the instrument,
  D57). `set window.visible` hides and shows it, and `--hidden` opens it
  hidden. Today closing the window ends the helper; D10 changes that to
  hiding it, shown again from the mixer (not built yet).
- **Frame reports** (D68, branch `monk-sprites`): the frames the window
  draws come from `ChoirFrames` (`Windows/voice_frames.*`, in the core
  library), updated on the window's 30 ms timer whether it is shown or
  hidden. With `set report.frames 1` the window thread prints a `frames`
  line when a frame changes; the command reader posts it a message so the
  first line comes at once, and every `set report.frames 1` gets a full
  line (a resync). Pitch reports (D71) go the same way: with `set
  report.pitches 1` the same tick prints a `pitches` line when a monk starts
  or stops singing or its sung note (`Choir::monk_sung_note`: the DSP's
  glided pitch plus bend, without vibrato) moves 0.05 semitone from the last
  line's. All stdout goes through one lock (`reply` in
  `voice_main.cpp`), so lines are whole. `--render` accepts the key and
  prints nothing.
- It runs at above-normal priority with power throttling off (D59), and
  opens no MIDI inputs: it only listens to its pipe.
- `--render <in> <out.wav>` renders a command script offline with no audio
  device. Commands take effect at the exact sample the `wait`s reach, so the
  output depends only on the script and options. CTest and the ear-check
  renders use it.

### 4. DelayLamaStandalone.exe (existing, unchanged)

Add Delay Lama starts it with no arguments. Instances share
`%APPDATA%\DelayLamaStandalone\settings.ini`, and each opens every MIDI input
(O13: left as is).

## Pipe protocol (version 1)

The protocol is text lines over the helper's stdin, UTF-8 and
`\n`-terminated (a trailing `\r` is fine), so it can be typed by hand and
logged as is. Blank lines and `#` lines are ignored, and command words are
case-insensitive. Any change to the commands bumps the version, here and in
`Windows/voice_protocol.h` (`kProtocolVersion`). Version 1 only adds to
version 0, so the helper accepts `hello 0` and `hello 1` and answers in the
version asked for.

midis2jam2 → helper:

```text
hello 1                      protocol version 0 or 1; answered with ready (optional)
on <note> <velocity> [<ms>]  note-on, 0-127; velocity 0 is a note-off. Protocol 1: the
                             note's length in the file (-1 or none = unknown)
off <note>                   note-off
bend <value>                 14-bit pitch bend, 0-16383, centre 8192
bendrange <semitones>        from RPN 0 (default 2); 0-127, decimals allowed
cc <number> <value>          raw CC; 7 volume, 11 expression, 64 sustain, 120/123 all notes
                             off and 121 reset act; every value is kept for the profiles
program <bank> <program>     bank 0-16383, program 0-127
allnotesoff                  stop/seek: release every monk now, pedal or not
set <key> <value>            helper parameter (below)
next <key> <value>           protocol 1: a profile key for the next note only; repeatable,
                             cleared by the next on; profile mode only
wait <ms>                    pause the reader; for test scripts and --render
quit
```

`set` keys in plain mode:

- `gain` (0–4): the channel gain on top of velocity, CC7 and CC11.
- `window.visible` (0/1; both modes): hides or shows the monk window. The
  sound is untouched.
- The standalone's sound settings, named after its INI keys: `volume`,
  `glide`, `voice`, `vowel`, `vibrato`, `vibrato_rate`, `breath`,
  `echo_amount`, `echo_time`, `echo_feedback` (0–0.95), `attack`, `decay`,
  `release` (seconds, 0–10), `sustain`, `unison_voices` (1–10),
  `unison_detune` (cents, 0–100), `unison_spread`. The rest take 0–1.

`set articulator 1` switches to profile mode (0 switches back). There the
`set` keys are the profile keys of IMITATION.md §7 as `section.param`,
listed with their ranges in `Windows/voice_profile_keys.inc`. They are
staged with `profile.begin` / `profile.apply`, reset with `profile.reset`,
and joined by the channel keys of IMITATION.md §12. Protocol 0's sound keys
are refused in profile mode, while `gain`, `volume` and `window.visible`
work in both. Keys added since the version's first release (`onset.bandwidth`,
`onset.after_rest`, `vibrato.lock`, `voice.formant1`–`3`, `dyn.gain`,
`window.visible`) are additive: an older helper answers `error` and plays
on.

`set report.frames` (0/1; both modes; D68, on the `monk-sprites`
branches) turns the frame reports on or off. On, the helper
prints one `frames` line at once and then one whenever any monk's frame
changes on the window's animation tick (30 ms), whether the window is shown
or hidden. Like the other later keys it is additive.

`set report.pitches` (0/1; both modes; D71, on the `monk-sprites`
branches) turns the pitch reports on or off. On, the helper prints one
`pitches` line at once and then one on the animation tick whenever a monk
starts or stops singing or its sung note has moved 0.05 semitone from the
last line's. Additive too: an older helper answers `error`.

helper → midis2jam2 (stdout):

```text
ready <version>              answer to hello; window open, audio running
error <message>              a bad line (it is skipped) or a startup failure
frames <f0> ... <fK-1>       with report.frames on: the faces.png frame (0-29) each of
                             the K monks shows, in window order, closed lips included
pitches <p0> ... <pK-1>      with report.pitches on: the note each monk's synth sings,
                             two decimals, glide and bend included, no vibrato; - while
                             it is silent. Profile mode's notes sit an octave or more
                             above plain mode's, so only the changes mean anything
```

A frame index is the one the window draws: `faces.png` is 5 columns × 6
rows, column-major (frame = column × 6 + row), each cell 314 × 311 px
holding a 311 × 291-px frame at its top left (CODEBASE_NOTES.md "Monk artwork").
Lines on stdout are whole: `ready`, `error`, `frames` and `pitches` never
interleave.
The helper option `--hidden` opens the window hidden, as if `set
window.visible 0` had come first.

The helper exits on `quit` or at the end of stdin (today also when its
window is closed, D10). Exit codes: 0 normal, 1 startup failure (an `error`
line says which), 2 bad command line or an unsupported `hello` version.

## Timing and latency

- The sequencer pump runs every 1 ms on `System.currentTimeMillis`.
- In the helper, events take effect at the next audio block. Blocks are 512
  frames at 48 kHz (≈10.7 ms), with about 43 ms queued (4 buffers).
- **Measured** on a loopback recording of the system mix: a helper sounds
  **169 ms before** Gervill (Gervill reports 120 ms; its Java sound line adds
  the rest). The default offset is therefore **175 ms on Gervill** and 0 on
  other devices (D30). The router delays every helper line by it, stop and
  seek included. To measure again, run `./gradlew :app:delayLamaLatency
  [-PdelayLamaLatency=<offset>]` while recording the output: each woodblock is
  followed 500 ms later by a monk note.
- Seek: midis2jam2 sends note-offs, then *chases* CCs, programs and pitch
  bend up to the new position (`JwSequencerImpl.chaseEvents`), and the router
  passes the chased values on. RPNs and NRPNs are rebuilt as number then data
  (`cm/.../midi/system/ParameterChase.kt`, D31).
