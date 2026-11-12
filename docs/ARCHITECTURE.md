# Architecture

How the parts fit together, for maintainers. What the user sees and the
settings are in [README.md](../README.md). File references are relative to
`external/midis2jam2/app/src/` (`cm` = commonMain, `dm` = desktopMain) or
`external/delalalalay-lama/`.

| Component | Where | Job |
| --- | --- | --- |
| Launcher | `dm/.../delaylama/`, `dm/.../ui/home/delaylama/` | Card, panel, mixer window; saves the choices |
| Renderer hooks | `dm/.../delaylama/`, `cm/.../delaylama/` | Routes sung channels, stands the monks in the scene, sets levels |
| `DelayLamaVoice.exe` | `Windows/voice_*` | The helper: one process per sung channel |
| `DelayLamaStandalone.exe` | `Windows/` | The unchanged standalone. Add Delay Lama starts it with no arguments |

## The launcher

On Windows the performance runs in the launcher's process; the separate
renderer process (fed a base64 JSON `RendererBundle`) is for macOS and
recordings.

The card (`DelayLamaCard`) opens the panel (`DelayLamaScreen`), which lists the
channels from `ChannelSurvey` (programs named by the file's GM/GS/XG/GM2 mode).
`DelayLamaPanelModel`, a Koin single, holds the state; `select(file)` reads the
channels off the UI thread and restores the file's choices. Every change is
saved at once in `DelayLamaStore`, its own preferences node: the options as
JSON, and each file's `FileChoices` under the SHA-256 of its contents.

Play hands a `DelayLamaConfig` (`cm/.../starter/configuration/`) to the
performance through `ExecutionState.delayLama`, `PerformanceConfigFactory` and
`PerformanceConfig.delayLama`; per-channel settings are in
`DelayLamaConfig.options`. The config comes from:

| Play | Source |
| --- | --- |
| Home tab | The panel; the environment variable is ignored |
| Command line | `MIDIS2JAM2_DELAY_LAMA` if set, else the panel's remembered choices (`DelayLamaStore.rememberedConfig`) |
| Queue, recordings, Gradle tools | `MIDIS2JAM2_DELAY_LAMA` or the `midis2jam2.delayLama` system property |

`StandaloneLauncher` starts each standalone in its own folder, beside its
`Resources/`. It looks at the options' path, then next to the app, next to the
helper, and in a development checkout.

## Routing

`MidiPackage.build` (`dm/.../starter/MidiPackage.kt`) makes one Gervill
`MidiDevice` per port, and the `JwSequencerImpl` pump thread sends every event
through `MidiPorts.dispatch` to `MidiDevice.dispatch` (`cm/.../midi/system/`).
`VoiceHelperManager.route` wraps each device in a `DelayLamaRouterDevice` after
the Gervills are made and before the sequencer opens them, so the sequencer and
the reset logic are unchanged.

The router sends sung channels' events to their helper as protocol lines;
everything else, and every SysEx, reaches the device untouched. It turns the
stop sweep (a note-off for each note 0–127) into one `allnotesoff`, decodes
RPN 0 into `bendrange` (NRPN 99/98 deselects, CC 121 resets the selection, and
a GM, GM2, GS or XG reset puts it back to 2), tracks bank select so `program`
carries `msb × 128 + lsb`, passes every CC on as `cc`, and drops aftertouch.

In profile mode (the default), once the helper is up, the router sends
`set articulator 1`, `exaggerate`, the staged profile for the channel's program
and bank (`ImitationProfiles`, the Kotlin port of `tools/profiles/expand.py`)
and `set range.shift`, the channel's octave fit
([IMITATION.md §7.1](IMITATION.md#71-range)). It sends them again when a
program change or reset maps to another profile. Each `on` carries the note's
length in the file (`ChannelScore`). `profile=plain` sends the plain-mode lines
instead. A channel whose helper can't start plays on the device.

`VoiceHelperManager` finds `DelayLamaVoice.exe` (the config's `exe`, next to
the app, or `delalalalay-lama/Windows/build/Release/` under an `external`
folder above the working directory). When the ports open it starts one helper
per channel with `--monks`, a title, a `--label` naming the channel's
instruments (`ChannelSurvey.instrumentNames`), and a place from
`MonkWindowLayout`: columns on the main screen's work area, leaving the mixer's
width free, all shrinking alike down to 35 % when they don't fit. When the
performance ends the ports close, which sends `quit` and closes stdin; a helper
still running 2 s later is killed, and a shutdown hook closes any left over.

`VoiceHelperProcess` (`VoiceHelper.kt`) talks to one helper. A writer thread
holds each line back by the offset ([Timing and latency](#timing-and-latency)).
Stdout is read without pause, so the helper never blocks on a full pipe, and
both streams go to the log (`frames` lines only the first and every 200th, with
a count at the end).

The monk windows are always on top and open without taking the focus. A real
fullscreen window is topmost too and would cover them, so while a channel is
sung, Fullscreen opens as borderless on Windows (`effectiveWindowMode`,
`cm/.../starter/WindowModes.kt`).

`InstrumentAssignment.assign` skips sung channels unless `keep3d` is set. With
a mixer, or monks in the scene, it builds them anyway, kept off stage by
`Instrument.stageGate` ([Delay Lama switches](#delay-lama-switches)).

## Monks in the scene

With the view `scene` or `both` (`DelayLamaConfig.view`) and the instruments
hidden, a live performance's `VoiceHelperManager` (`hasScene`, set by
`MidiPackage`) stands the monks in the 3D scene if the helper's `--help` lists
`--hidden` (asked once per exe) and `Resources/faces.png` is beside it. Each
helper then gets `set report.frames 1` and `set report.pitches 1` after
`hello`, and in the scene view starts with `--hidden`. Its `frames` and
`pitches` lines go into the channel's `MonkFrames`, read on the render thread.
An older helper's `error` for `report.pitches` only loses the nod.

A channel falls back to its window (the router sends `set window.visible 1`)
when its helper answers `report.frames` with an `error`, reports nothing within
5 s, or `faces.png` can't be read. The windows view, `keep3d`, the tools and
the tests always use windows. Recordings get no monks.

`MonkScene` (dm) is the performance's `MonkStage` (cm): which channels stand in
the scene, and whether one is shown now (its frames come and
`DelayLamaMixer.areMonksShown` is true). `InstrumentAssignment` builds those
channels' instruments gated off stage, gives each a `standIn`, and lists them
as `SungChannel`s with their note starts (`PerformanceManager.sungChannels`).

`MonkBillboards` (dm, an app state) cuts `faces.png` into 30 textures as the
helper's window does (frame = column × 6 + row at (column × 314, row × 311),
311 × 291 px, opaque and unlit) and gives each channel a node of K quads side
by side, turned to the camera about the vertical axis (`BillboardControl`,
AxialY).

**Names.** `MonkScene.nameOf` gives each channel's instrument name
(`ChannelSurvey.instrumentNames`, as the mixer's strips have it) and
`areNamesShown` whether they show now (the mixer's switch,
`DelayLamaMixer.names`, else the config's `names`). `MonkBillboards` draws each
name on the GUI node, not in the scene: a choir on the floor has its feet at y
0, so a name in the world below them would be under the floor. Each frame it
projects the middle of the choir's feet (before the nod) to the screen and puts
a `BitmapText` (Inter, 2.4 % of the screen's height, at least 14 px, whole
pixels) on a 60 % black plate just below it. It is hidden with its choir, while
the point is behind the camera, or when the name would be off the screen. Being
over the scene, a back choir's name can lie over a front choir. The scene
preview grabs its frames after the GUI viewport, so the names show there.

**On the floor.** Each frame the choir stands at the instrument the channel
plays now or played last (`SungChannel.standingAt`), while that instrument
would be on stage ignoring its gate (`Instrument.wouldBeVisible`). `MonkFloor`
puts it below the middle of the instrument at rest (`ownRestingBox`), moves it
towards the middle until its whole footprint is on the floor, and steps it
towards the audience (+Z) when something reaching below its top is in the way:
any instrument that may be on stage, at rest, or a choir placed before it
(`MonkFloorPlan`). The place is kept in the instrument root's own space, so the
choir slides across the floor as the instrument would.

**Vocals.** `ChannelSurvey.vocals` picks the sung channels that carry the
song's vocals, and `MidiPackage` (and the scene preview) passes them to
`MonkStage.vocals`. The bundled songs come from a tab site, name no tracks and
give vocal lines any program, so the test is musical. A channel is a vocal when
the program playing most of its notes is one-based 41–45, 53–55 or 57–88 (solo
strings, voices, brass, reeds, pipes, synth leads), at most 20 % of its notes
start while another sounds (`ChannelSummary.overlapping`), and it stays within
E2–C6. On the twelve bundled songs this finds every lead vocal and five songs'
backing vocals, and nothing else; a two-note "ooh" harmony counts as a choir.
A vocal's monks
are `MonkSize.VOCAL_SCALE` times taller and wider (`MonkStage.scale`, used by
`SungInstrument` and `MonkBillboards`). A vocal channel, sung or not, is named
`ChannelSurvey.VOCALS` ("Vocals") in place of its programs: by
`ChannelSurvey.instrumentNames` for the monk windows, the mixer strips and the
scene's names, and by `DelayLamaText.channelPlays` and `summary` in the panel.

### The performance's spread

The spread (`MonkStage.spread`, read every frame: the mixer's slider, else the
config's) moves each choir from its floor place to its place in the plan
(`MonkSpreadPlan`). `InstrumentAssignment` makes the plan when the first choir
stands, since it measures every sung instrument at rest. A channel's
instruments share one place. Camera 1A, the opening camera, is at x −2, z 134.

- **Travel** (`MonkSpread.travel`): from spread 0 to 0.5 a choir moves in a
  straight line from the floor to its place. From 0.5 to 1 every choir moves
  further out from x −2, up to 1.5 times as far at 1, and the ladder moves up to
  40 further back. A choir never stands lower than the floor.
- **Drums' lane** (`MonkLane`): the directions in which 1A sees the drum set,
  in plan, plus a margin. No grid choir stands in it, so from 1A the drums show
  clear of every choir. It is kept whether the file has drums or not.
- **Ladder** (`MonkLadder`): the vocals, then the ensembles (channels whose
  instrument with the most notes is a `StageChoir`, `StageStrings` or
  `StageHorns`), stand behind everything in steps. The lead vocal (most notes;
  the lowest channel among equals) stands alone on the first step, behind the
  wall, so from 1A its feet show above the drums and its head, nod included,
  below the top of the picture. The rest follow in channel order, side by side
  on each step as far as the step's width allows: the first in the middle, then
  right, then left. 1A shows the first step; the moving cameras the rest.
- **Grid** (`MonkGrid`): every other choir stands near where its channel's main
  instrument (the one with the most notes) rests, clear of the lane, the ladder
  and each other. Places lie on arcs round 1A, since the choirs face it. Two
  choirs close in distance from 1A stand side by side; further apart, one stands
  behind the other. Choirs take places one by one, cheapest first, where cost is
  the squared distance from the instrument with front-back distance weighted
  down, so a choir moves front or back before across. A choir with no clear
  place takes the cheapest place out of the lane. Then choirs of the same width
  swap while that costs less, so the last of a kind isn't stranded (a bass
  behind guitars that filled its side). In practice guitars and bass fill the
  right side, keyboards the left. Most grid choirs stand past the floor's edge,
  so they rise over the wall (`MonkGrid.lift`). A choir whose direction from 1A
  overlaps a nearer one's stands `RISE_BEHIND` of that one's monk height higher
  (`MonkGrid.lifts`), worked out every frame so wider spreads keep the steps.
- **Front of the stage** (`MonkFront`): a channel brought to the front (the
  mixer's F, `DelayLamaMixer.front`, read as `MonkStage.front`) stands there at
  any spread: on the floor, in one row in channel order, centred on 1A's
  middle, at the same z however wide the row is. Only choirs shown now count
  (`MonkScene.front`), so a hidden one leaves no gap. The cameras and camera
  focus take the choir where it stands (`SungInstrument.bounds`). Taken away, it
  is back at its spread place in the next frame.

| Constant | Value |
| --- | --- |
| `MonkSize` | monk 48 high; choir at most 208 wide (four monks ≈ 205; bigger choirs get smaller monks); `VOCAL_SCALE` 1.25 |
| `MonkFloor` | y 0, a disc of radius 140 inside the wall (measured from the stage model); step towards the audience up to 160 |
| `MonkSpread` | in place at 0.5 (the default); `MAX_WIDEN` 0.5; `LADDER_BACK` 40; `RISE_BEHIND` 1.1 monk heights |
| `MonkLane` | drum set at x −34 to 47, z −111 to −46, 52 high (every kit); margin 2°, so the lane runs 12° left to 17° right of straight back |
| `MonkLadder` | first step x −2, z −170, 44 up; each step 40 further back and 1.1 × its tallest monk higher (66 behind a step of vocals); step width 540 (two four-monk vocals), gap 8 |
| `MonkGrid` | 100 to 420 from 1A every 6, every 1° up to 80° each side; z 60 to −230, at most 450 to the side, at least 100 in plan from cameras 1A, 1B, 1C; side by side when under 60 apart in distance from 1A, at least 8 apart across; front-back weight 0.5; wall lift up to 40 over 16 past the floor; one choir behind another rises 53 for full-size monks |
| `MonkFront` | x −2, z 60 (106 in front of the drums, 74 from 1A in plan, which shows the choir down to about its hands), gap 8 |

The scene preview (`:app:delayLamaScenePreview`, see CLAUDE.md) shows the
stage from above (`scene_<s>s_top.png`) and the first choir at the front
(`scene_<s>s_front_wide.png`, `_front_top.png`).

### Nods and cameras

Each monk nods (`MonkNod`): it rises above its place while the note it sings
(`MonkFrames.pitches`) is away from where its pitch has settled (a follower
with a 0.3 s time constant), by up to 12 % of its height (`tanh` of the
distance over 3 semitones, eased over 0.06 s), either way, never below its
place. A note begun from silence starts settled. `MonkBillboards.refresh` moves
the nods by performance time: still while paused, reset after a jump back or
while the choir is hidden.

An instrument whose stand-in is shown holds its place
(`Instrument.holdsPlace`), so instruments of its kind stand beside the choir.
`CinematicCamPlugin` takes it as on stage (`isPresentable`), `restingBox`
frames the choir (`standInBounds`), and a shot of a choir gets the normal lens
where it asks for the long one (`baseFov`). `ClassicAutoCamPlugin` uses an
instrument's angles only while the instrument itself is on stage
(`isAllowedOnStage`), since they are set for where it floats.

## The mixer and levels

A single-file performance with sung channels opens `DelayLamaMixerWindow`
(titled "Delay Lama Everything Controls", `DelayLamaText.CONTROLS_TITLE`;
Compose, always on top, at the right of the main screen;
`MidiPackage.build(showMixer = true)` from `ApplicationService` only). It
closes when the routers close. `DelayLamaMixer` holds a strip per channel and
tells the routers which levels changed. A sung channel's level goes to its
helper as `set gain` (panel gain × level). Any other channel's level scales its
CC 7 by the square root, reapplied after a system reset. The F button and the
instrument names switch (only with `hasScene`) change no level, and Reset and
the Delay Lama switches leave them alone.

A sung channel the mixer doesn't let be heard (`isHeard` false) hides its
monks: they leave the scene, where its place is not held and the cameras skip
it, and the router sends `set window.visible 0` with the gain. Heard again,
they come back where its view shows them. The router sends the window line only
when being heard changes (`SungChannel.wasHeard`), so volume moves and camera
focus don't repeat it.

### Delay Lama switches

`DelayLamaMixer.Strip.isSwitchOn` holds each switch, and switch listeners get
the keys that changed. Nothing starts or stops: with a mixer, the router sends
every event of a sung channel to its helper **and** to the synthesizer, and a
switch only changes levels.

| Switch | Helper | Synthesizer's copy |
| --- | --- | --- |
| On | Plays at its gain | CC 7 = 0; the file's CC 7 values are held back and resent after resets |
| Off | `set gain 0`, `set window.visible 0`; monks in the scene hidden | The file's CC 7, scaled by the mixer |

When every sung channel is off, `VoiceHelperManager.followSwitch` puts
Gervill's line back to 0 dB (and down by the balance when any is on again).
Switched on, a window returns only where its view shows it
(`MonkFrames.isWindowWanted`). Helper lines wait the offset, which matches
Gervill's longer buffer, so both swap at the same moment. While a switch is on,
the channel's 3D instruments are kept off stage
(`PerformanceManager.sungInstrumentsOnStage` by channel key, and
`Instrument.stageGate`) and the cameras skip them; their rhythm notes stay off
stage, because the drum set is shared. Without a mixer (queue, tools,
recordings) sung channels never reach the synthesizer.

### Balance

While any channel is sung, every Gervill plays `balance` dB quieter (default 6)
through the master gain of its Java Sound line (`dm/domain/LineGain.kt`, set
from `VoiceHelperManager.balance` before the ports open). The gain is after
Gervill's limiter and outside MIDI, so resets, seeks and master volume messages
can't undo it. The monks end up 6 dB louder against the band than plain
playback; the whole mix is about 4.4 dB quieter. Other MIDI devices get no
balance.

## Camera focus

`MidiPackage` makes one `ChannelFocus` whenever Delay Lama sings, on or off,
at the configured strength (`focus`, `focusScale`), shared by the routers and
the mixer. `CameraFocusState`, an app state of a live performance (a single
file or each queue song, never recordings), works every frame from the camera
and `FocusSubjects` (a sung channel shown in the scene is its choir, any other
channel its instruments on stage). It measures each channel's presence (how
much closer than camera 1A, squared, times how much of it is in the picture
against 1A's), how unevenly presence is spread (0 from 1A), and how near the
most present one is. `CameraFocus.offsets` turns that into per-channel offsets.

| | Value |
| --- | --- |
| Near channel stands out by | up to 12 dB × strength |
| Its own rise | at most 6 dB, not scaled (the helper has about 9 dB of headroom; a full +12 would clip); the rest comes off the other channels |
| Unseen channels fall by | up to 21 dB at strength 1 (the 15 dB cut scales), 48 at 2 |
| Strength (`scale`) | 0–2, default 1, 5 % steps in the panel and mixer; read every frame |
| Easing | 0.1 s time constant (a 12 dB cut is 90 % there in 0.23 s) |
| Sending | at most every 15 ms, in 0.25 dB steps; first batch after a cut about 1.8 dB of 12 at 60 frames a second, 3.4 at 30 |
| Remeasuring | instruments' boxes at most once a second, three a frame |

Nothing else waits: a send goes straight to the routers on the render thread,
and a helper's `set gain` waits only the usual offset, which lands it with
Gervill's CC 7. The routers multiply the offsets into the mixer's level
(`levelOf`): a sung channel's `set gain` (capped at 4; the helper smooths it
over about 5 ms), any other channel's CC 7 (capped at 127), with or without a
mixer. The mixer's controls are unchanged. Switched off, the offsets glide back
to 0 dB; the app state's end sets them to 0.

## The helper (DelayLamaVoice.exe)

A Win32 console program, a CMake target in `Windows/` (`voice_*`) beside the
standalone, reusing `DSP/`, the WinMM player (`Windows/audio_engine.h`), the
face artwork and the monk frame logic. It runs at above-normal priority with
power throttling off, so its audio keeps up when its window is covered, and
opens no MIDI inputs.

**Choir.** One process hosts up to K monk synths (`--monks` 1–8, default 4;
each simultaneous note goes to another monk), mixes them into one waveOut
stream and shows them side by side in one window.

**Plain mode.** A note goes to the lowest-numbered silent monk; when none is
free, to the monk released longest ago, or else it steals the oldest note
(never the current highest or lowest, pedal-only notes first), and the stolen
monk glides. CC 1, 5, 12 and 13 are not routed to the DSP.

**Levels.** Velocity, CC 7 and CC 11 on the GM curve (squared), times `gain`.
The default volume is 0.09, so four monks at full velocity and CC 7 127 stay
just under full scale. A released monk only gets quieter, since the DSP still
plays its last grains. Profile mode uses the moderate velocity curve
((velocity/127)^1) and 4× headroom: each synth's DSP volume goes up to 4× and
the articulator's levels down by the same factor.

**Profile mode.** The articulator (`Windows/voice_articulator.*`) applies the
channel's profile to each note ([IMITATION.md](IMITATION.md)). The choir
renders 1 ms sub-blocks and the articulator sets every monk's values between
them. It allocates voices itself (connected notes stay on one monk) and sings
the written pitch plus `range.shift`. The DSP envelope and the synths' echo are
off, and one echo runs on the mix. The mouth follows the vowel and shows closed
lips.

**Window.** Frameless or titled, always on top, opened without taking the
focus, at `--x --y --width --height` (client area, physical pixels). Other
options: `--no-topmost`, `--no-title-bar`, `--title`, `--label` (a strip under
the monks naming the instrument) and `--hidden`. Closing it ends the helper.

**Reports** (protocol below). The window's frames come from `ChoirFrames`
(`Windows/voice_frames.*`, in the core library), updated on its 30 ms timer.
The window thread prints the report lines; the command reader posts it a
message so the first line comes at once, and each `set report.frames 1` gets a
full line (a resync). A monk's sung note is `Choir::monk_sung_note`. All stdout
goes through one lock (`reply` in `voice_main.cpp`). `--render` accepts both
keys and prints nothing.

**Offline render.** `--render <in> <out.wav>` renders a command script with no
audio device. Commands take effect at the exact sample the `wait`s reach, so
the output depends only on the script and options. CTest and the listening
renders use it.

## Pipe protocol (version 1)

Text lines over the helper's stdin, UTF-8 and `\n`-terminated (a trailing `\r`
is fine), so you can type it by hand and log it as is. Blank lines and `#`
lines are ignored, and command words are case-insensitive. Any change to the
commands bumps the version, here and in `Windows/voice_protocol.h`
(`kProtocolVersion`). Version 1 only adds to version 0, so the helper accepts
`hello 0` and `hello 1` and answers in the version asked for.

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
wait <ms>                    pause the reader, 0-3600000; for test scripts and --render
quit
```

`set` keys in plain mode:

| Key | Range | Meaning |
| --- | --- | --- |
| `gain` | 0–4 | Channel gain on top of velocity, CC 7 and CC 11 |
| `window.visible` | 0/1 | Hides or shows the monk window; the sound is untouched. Both modes |
| `volume`, `glide`, `voice`, `vowel`, `vibrato`, `vibrato_rate`, `breath`, `echo_amount`, `echo_time`, `sustain`, `unison_spread` | 0–1 | The standalone's sound settings, named after its INI keys |
| `echo_feedback` | 0–0.95 | |
| `attack`, `decay`, `release` | 0–10 s | |
| `unison_voices` | 1–10 | Whole numbers |
| `unison_detune` | 0–100 cents | |

`set articulator 1` switches to profile mode (0 switches back). There the `set`
keys are the profile keys of [IMITATION.md §7](IMITATION.md#7-profile-parameters)
as `section.param`, listed with their ranges in
`Windows/voice_profile_keys.inc`. They are staged with `profile.begin` /
`profile.apply`, reset with `profile.reset`, and joined by the channel keys of
[IMITATION.md §12](IMITATION.md#12-interface). Protocol 0's sound keys are
refused in profile mode; `gain`, `volume` and `window.visible` work in both.
Keys added since the version's first release (`onset.bandwidth`,
`onset.after_rest`, `vibrato.lock`, `voice.formant1`–`3`, `dyn.gain`,
`window.visible`, `report.frames`, `report.pitches`) are additive: an older
helper answers `error` and plays on.

`set report.frames` (0/1, both modes): on, the helper prints one `frames` line
at once, then one whenever any monk's frame changes on the window's animation
tick (30 ms), whether the window is shown or hidden.

`set report.pitches` (0/1, both modes): on, the helper prints one `pitches`
line at once, then one on the animation tick whenever a monk starts or stops
singing or its sung note has moved 0.05 semitone from the last line's.

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

A frame index is the one the window draws: `faces.png` is 5 columns × 6 rows,
column-major (frame = column × 6 + row), each cell 314 × 311 px holding a
311 × 291 px frame at its top left. Lines on stdout are whole: `ready`,
`error`, `frames` and `pitches` never interleave. The option `--hidden` opens
the window hidden, as if `set window.visible 0` had come first.

The helper exits on `quit`, at the end of stdin, or when its window is closed.
Exit codes: 0 normal, 1 startup failure (an `error` line says which), 2 bad
command line or an unsupported `hello` version.

## Timing and latency

- The sequencer pump runs every 1 ms on `System.currentTimeMillis`.
- The helper applies events at the next audio block: 512 frames at 48 kHz
  (about 10.7 ms), with about 43 ms queued (4 buffers).
- On a loopback recording of the system mix, a helper sounds **169 ms before**
  Gervill (Gervill reports 120 ms; its Java Sound line adds the rest). So the
  default offset is **175 ms on Gervill** and 0 on other devices. The router
  delays every helper line by it, stop and seek included.
- To measure again, run `./gradlew :app:delayLamaLatency
  [-PdelayLamaLatency=<offset>]` while recording the output: each woodblock is
  followed 500 ms later by a monk note.
- On a seek, midis2jam2 sends note-offs, then chases CCs, programs and pitch
  bend up to the new position (`JwSequencerImpl.chaseEvents`), and the router
  passes them on. RPNs and NRPNs are rebuilt as number then data
  (`cm/.../midi/system/ParameterChase.kt`), so the bend range survives a seek.
