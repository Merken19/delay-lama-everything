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
  channel starts off (D45). Below the channels are the options for every
  file: balance, offset, imitation strength, keep the 3D instruments, and the
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
  helper's stdout and stderr go to the log.
- **Monk windows and window modes.** The helpers start before the 3D window
  exists. Their windows are always on top and open without taking the focus.
  They stay above windowed and borderless performances. A real fullscreen
  window is topmost too and covers them, so while a channel is sung,
  Fullscreen opens as borderless on Windows (D47; `effectiveWindowMode`,
  `cm/.../starter/WindowModes.kt`).
- **Hidden instruments**: `InstrumentAssignment.assign` skips sung channels
  unless `keep3d` is set (O7). With a mixer it builds them anyway, gated by
  the switch (below).
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
- **Delay Lama switch** (D60). The card at the top of the mixer chooses who
  plays the sung channels: the monks (on, at start) or the synthesizer
  (off), never both. Nothing starts or stops. With a mixer, a router sends
  every event of a sung channel to its helper **and** to the synthesizer,
  and the switch only changes levels:
  - On: the synthesizer's copy gets CC 7 = 0. The file's CC 7 values are
    held back, and resent after resets.
  - Off: the helper gets `set gain 0` and `set window.visible 0`, the
    synthesizer's copy gets the file's CC 7 scaled by the mixer, and
    `VoiceHelperManager.followSwitch` puts Gervill's line back to 0 dB.

  The helper's lines wait the offset, which matches Gervill's longer buffer,
  so both swap at the same moment. The sung channels' 3D instruments are
  built and kept off stage while the switch is on
  (`PerformanceManager.sungInstrumentsOnStage`, `Instrument.stageGate`; the
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
  D57). `set window.visible` hides and shows it. Today closing the window
  ends the helper; D10 changes that to hiding it, shown again from the mixer
  (not built yet).
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

helper → midis2jam2 (stdout):

```text
ready <version>              answer to hello; window open, audio running
error <message>              a bad line (it is skipped) or a startup failure
```

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
