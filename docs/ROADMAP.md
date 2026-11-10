# Roadmap

v1 (D61) is a MIDI file's chosen channels sung by monk choirs in
always-on-top windows, imitating their instruments. It also includes the
launcher's Delay Lama panel, the mixer with its Delay Lama switch, Add Delay
Lama and one Windows zip. Work on one milestone per session. Tick items as
they land, and add a dated line to the log at the bottom.

## Done

- **Setup**: both clones in `external/` and the test MIDIs (`tests/midi/`,
  made by `tools/testmidi/make_test_midis.py`).
- **Helper** `DelayLamaVoice.exe`: protocol 0/1, choir, window, `--render`,
  `--label`, `window.visible` (ARCHITECTURE.md). The user ear-checked it.
- **Routing in midis2jam2**:
  - router and helper processes, with the RPN bend range and the seek chase
    (D31)
  - offset (D30) and balance (D34, D36)
  - hidden 3D instruments, and Fullscreen as borderless (D47)
- **Launcher and playback**:
  - the Delay Lama card and panel, choices remembered per file, Add Delay
    Lama (D44)
  - monk window layout and names (D57), the mixer (D58) and the switch (D60)
- **Imitation, phases 4a and 4b**:
  - the spec ([IMITATION.md](IMITATION.md)), the articulator and profile mode
    (D20, D41)
  - steady onsets (D33) and folding (D37)
  - singing violins and ensembles (D39, D42), the bass "doo" (D40); drums stay
    with Gervill (D23)
- **Imitation, phase 4c so far**: piano, flute, trumpet and tenor sax (D48,
  D56).
- **Packaging**: `tools/package/` makes and checks the zip (D55).

## To do for v1

### Monk windows and the mixer (one session)

- [ ] Closing a monk window hides it while the helper keeps singing; the
      mixer can show it again (D10). Add a catalogue entry and a test
- [ ] An Add Delay Lama button in the mixer (D64)

### The fork (when the user says so)

- [x] Fork wyskoj/midis2jam2 to the user's GitHub and push `delay-lama`
      there (D62): Merken19/midis2jam2, remote `fork` in the clone
- [ ] The package's `NOTICE.txt` points at the fork instead of the patch
      (D55)

### Phase 4c: the remaining families (one family per session)

Method and lessons: IMITATION.md §15–16. Set levels by measurement (D63), and
ask the ear only about the sound itself. The scope follows O19's proposal
until the user says otherwise.

- [ ] Guitars: clean, nylon, jazz, muted, overdrive, distortion, harmonics
      (GM 25–32)
- [ ] Basses other than finger: pick, fretless, slap (GM 35–40)
- [ ] Organs (GM 17–24) and chromatic percussion (GM 9–16)
- [ ] Cello, contrabass, tremolo strings, pizzicato, harp, timpani
      (GM 43–48), and the synth strings on `strings.ensemble` (GM 51–52)
- [ ] Choir, voice and orchestra hit (GM 53–56)
- [ ] Trombone, tuba and horn, which measure much brighter than Gervill and
      need a horn profile; also the muted trumpet and the brass section
      (GM 58–64), and the alto, soprano and baritone saxes (GM 65–68)
- [ ] Reeds (GM 69–72), and the other pipes on `flute` (GM 75–80)
- [ ] Synth lead and pad (GM 81–96)
- [ ] GM 97–128 at first-guess syllables with measured levels (O19)
- [ ] Across families: the glide for fast runs, repeated notes, unison, and
      `nucleus.pitch_track` on low instruments

### User checks (hands and ears)

- [ ] Play the test files (`tests/midi/PLAY_CHECK.md`)
- [ ] In the panel: set channels, play a file, try Add Delay Lama
- [ ] Play a file with many sung channels: are all the windows on screen?
      Try the mixer's M, S and sliders
- [ ] Flip one channel's Delay Lama switch while a file plays, mid-note
      too, then All off and All on: does only that channel's sound swap,
      cleanly and in time, do its monks hide and return, and does its
      instrument come and go (D60)?
- [ ] The unzipped package: play a file with sung channels, try Add Delay
      Lama, make a recording, read `NOTICE.txt`

### Release

- [ ] The final package once 4c and the fork are done, with
      `check_package.ps1` and the user's check above

## Phase 5: monks in the 3D scene (branches `monk-sprites`, D65)

Started before v1 is finished, at the user's request. Two sessions work in
parallel, one per clone; neither touches the other's repository.

- [x] Helper (delalalalay-lama): `set report.frames` and the `frames` line,
      `--hidden`, whole stdout lines, CTest checks (D68)
- [x] midis2jam2: read the frame reports, load `faces.png` beside the
      helper, draw each sung channel's choir as a billboard where its hidden
      instrument stands (D66), the view setting with its fallback, the
      switch and the cameras (D67), catalogue entries and tests
- [x] End to end: play a file with sung channels in each view, and a
      `delayLamaPanelPreview`-style offscreen render of the scene for review
      (`:app:delayLamaScenePreview`; PNGs in `renders/phase5/scene_preview/`)
- [x] Spread the choirs around the stage and up, with a slider in the
      panel and the mixer (D70)
- [x] The monks nod while their pitch moves (D71): `report.pitches` in the
      helper, `MonkNod` in the scene, catalogue entry and tests
- [ ] User check: do the nods read well (size, speed, rising for a move
      either way), live with a file that has glides, bends and leaps?
- [ ] User check: do the billboards sit well on stage (D69's placement and
      size, D70's spread at its default and on the slider), and do the
      mouths move in time with the singing?

## Camera focus (branches `camera-focus`, D72)

At the user's request, while phase 5 waits for its user checks. midis2jam2
and the top-level docs only; the helper needed no change.

- [x] The focus model (`CameraFocus`, `FocusSmoother`, `FocusSender`,
      `FocusSubjects`), `ChannelFocus` and `CameraFocusState`, applied in
      the routers on top of the mixer, also without a mixer (the queue)
- [x] The switches: panel option, mixer switch kept as the panel's,
      `focus=0|1`; the mixer's strips show the offset
- [x] Catalogue entries `delaylama.focus.*` and `DelayLamaFocusTest`
- [x] A scripted camera move recorded from the scene and replayed into a
      render (`:app:delayLamaScenePreview` `focus:` mode,
      `:app:delayLamaBalance` `timeline=`): `renders/phase5/focus/`, with a
      `listening.json`
- [x] User check (ears), round 1: glides smooth, change too small; the
      user asked for +12 dB when near (now D72's 12 dB)
- [ ] User check (ears), round 2: the listening set in
      `renders/phase5/focus/` (`focus_move_2`). Is 12 dB the right size?
- [ ] User check (live): play a file with focus on, fly the free camera to
      a choir and away, let the cinematic camera cut, and switch focus off
      and on in the mixer. Does it follow the camera without pumping?

## Log

- 2026-11-10: The user answered the camera focus listening set: glides
  smooth, the change too small, "make the change +12db when near an
  element". `CameraFocus` now lets the most present channel's own
  nearness carry the focus (`nearness`), sets its contrast to 12 dB, never
  raises the channels' average, and caps a channel's own rise at 6 dB with
  the rest taken off every channel: at a full +12 the monks clipped (346
  samples at full scale over the hold). Re-rendered: monks +6.0 dB (peak
  -3.4 dBFS), band -9.3 dB, 15.3 dB more contrast; the set is now round 2
  (`focus_move_2`). `DelayLamaFocusTest` (17) and `SpecCoverageTest` pass.
  Committed at the user's request on the `camera-focus` branches
  (midis2jam2 `54d58e31`, with the renders here). Not pushed.

- 2026-11-10: At the user's request, camera focus (D72) on the
  `camera-focus` branches (midis2jam2 from `delay-lama` 92310132, the
  top-level repo from `main`). New `cm/delaylama/CameraFocus.kt` and
  `dm/delaylama/ChannelFocus.kt`; the router, `VoiceHelperManager.route`,
  `MidiPackage`, the mixer and its window, the panel, `DelayLamaConfig`
  (`focus=`), `DelayLamaOptions`, `InstrumentAssignment`
  (`PerformanceManager.channelInstruments`) and both applications changed.
  The first model (distance plus a wide 30° margin) hardly moved anything
  in the scene, so what is in the picture now carries most of it. Four
  catalogue entries, 16 tests in `DelayLamaFocusTest`. Scripted move on
  `03_band.mid` (sax sung, 10-34 s): monks +2.6 dB and band -4.7 dB over
  the hold, identical elsewhere; panel and mixer previews re-rendered.
  Full `desktopTest`: 734 tests, 1 failed, 3 skipped; the failure is
  `BankSelectAssignmentTest`'s catalogue sweep (Jazz, Brush, Orchestra and
  SFX Sets timed out on a terminated headless engine), which stalls on this
  machine without the change too. Not committed; not tried live; not
  heard.

- 2026-11-10: At the user's request ("very stable right now"), committed
  the phase 5 work and merged the `monk-sprites` branches (D65): the
  top-level repo into `main`, midis2jam2 into `delay-lama`,
  delalalalay-lama into `voice-helper`. Nothing pushed. The temporary drum
  probes in midis2jam2 (`TempDrumProbe.kt`, its attach line in
  `Midis2jam2Application.desktop.kt`, `DrumProbeTest.kt`,
  `DrumRenderProbe.kt`) were left out, then deleted at the user's request.

- 2026-11-10: The user heard a beep from the drums of some demo MIDIs. Cause:
  their channel-10 notes are Guitar Pro 7 articulation numbers, not General
  MIDI keys, so most soundfonts leave the drums silent, and Timbres of
  Heaven plays key 22 as "MC-505 Beep2". New
  `tools/drumfix/fix_gp_drums.py` (table checked against alphaTab's
  `PercussionMapper`) wrote fixed copies of the 12 affected files to
  `MusicandSound/demoMidis/drums-fixed/`. A Timbres of Heaven render of the
  fixed Smells Like Teen Spirit drums has sound in 284 of 301 s (180 before).
  No ear check yet.

- 2026-11-10: At the user's request, sped up midis2jam2's `desktopTest`.
  It took about 3.5 min of tests in one JVM, plus up to 3 min more when a
  headless-engine call hung until its 180 s timeout (`TickStabilityTest`
  on an empty file this time; it passes alone). In `app/build.gradle.kts`
  the test classes now run in 4 parallel JVMs (`-PtestForks=n` overrides).
  In `HeadlessPerformance`, an engine call now times out after 60 s and
  fails with the engine thread's stack attached. Full suite: 718 tests
  green, with a 115 s test phase (1 m 44 s end to end once compiled). The
  hang's cause isn't found yet. These midis2jam2 changes sit uncommitted on
  `monk-sprites`, alongside that branch's own uncommitted work.

- 2026-11-10: At the user's request, the monks in the scene nod while their
  pitch moves (D71). delalalalay-lama `monk-sprites`: DSP addition
  `monk_synth_sung_note`, bridge `dl_get_sung_note`,
  `Choir::monk_sung_note`, `set report.pitches` and the `pitches` line
  (`ChoirFrames::take_pitch_report`), new checks in `voice_frames_checks.cpp`
  and the live `_frames_cli`; CTest 11/11, /W4 clean, release build rebuilt.
  midis2jam2 `monk-sprites`: `MonkFrames.pitches`/`parsePitches`, the
  helper manager sends `set report.pitches 1`, `MonkNod` per monk in
  `MonkBillboards`. New catalogue entry `delaylama.scene.nod` with 3 tests;
  `DelayLamaSceneTest` (21), `DelayLamaRoutingTest` and `SpecCoverageTest`
  pass. Full `desktopTest`: 718 tests, 1 failed, 3 skipped; the failure was
  an engine-thread timeout in `TickStabilityTest` (no Delay Lama in it),
  which passes alone. Not committed; not tried live, and no render (a still can't show a
  nod).

- 2026-11-10: At the user's request, the choirs spread around the stage and
  up (D70, `MonkSpread`): a fan towards the back and sides in channel order,
  over the wall, every second choir half a monk higher, never lower than on
  the floor. A 0-100 % spread (50 % by default) in the panel, `spread=` in
  the environment variable, and a live slider in the mixer that is kept as
  the panel's. The wall was measured by raycasting the stage model. Previews
  of `03_band.mid` at 0, 25, 50 and 100 % and K525 at 50 % in
  `renders/phase5/spread_preview/`; panel and mixer previews re-rendered.
  New catalogue entry `delaylama.scene.spread` with 3 tests;
  `DelayLamaSceneTest` (18), `DelayLamaMixerTest`, `DelayLamaPanelTest`,
  `DelayLamaSetupTest`, `SpecCoverageTest`, `CinematicCameraTest` and
  `InstrumentAssignmentTest` pass. Not committed. The first draft of
  `MonkSpread` went into midis2jam2 `c04c2099` (committed by the per-channel
  switch session); the working tree finishes it. Not tried live.

- 2026-11-10: At the user's request, the mixer's Delay Lama switch is now
  one per sung channel (D60 revised): a switch on each sung strip, and a
  card at the top that counts them, with All off / All on. A channel's
  switch moves only its helper gain, window, monks in the scene, synthesizer
  copy and 3D instrument. Gervill's balance comes off only once every sung
  channel is off. Also at the user's request, every channel Delay Lama can
  sing now starts sung (D45 revised). The command line without the variable
  sings the same for a file with nothing remembered, and saved choices are
  kept. Catalogue entries `delaylama.mixer.switch`, `-switch-balance`,
  `delaylama.instruments.switch`, `delaylama.scene.switch`,
  `delaylama.panel.channels` and `.memory` were reworded, and tests were
  added or updated. Mixer previews were re-rendered in
  `renders/phase5/panel_preview/`. `desktopTest`: 712 tests, 1 failed, 3
  skipped. The failure is `BankSelectAssignmentTest`'s catalogue sweep
  (SFX Set timed out), which stalls on this machine at the base commit
  too. Not tried by hand in a live performance. Committed on `monk-sprites`
  in all three repositories at the user's request, with the phase 5 work
  (helper c979238, midis2jam2 c04c2099). Not pushed.
- 2026-11-09: Choirs four times bigger, as the user asked (D69): monks 48
  high, choirs up to 208 wide. The floor rules follow: a choir's footprint,
  facing the audience, must be on the floor (the old rule would have pulled
  every choir of four to within 37 of the middle), the step forward is up to
  160, and choirs of different channels keep clear of each other. The
  cinematic camera films a choir with the normal lens where a shot asks for
  the long one, and the classic camera's instrument angles are for real
  instruments again. Previews re-rendered in `renders/phase5/scene_preview/`.
  The same six test classes pass (63 tests).
- 2026-11-09: The user chose choirs on the stage floor (D69). They now stand
  on the floor below their instrument's place, are brought in front of the
  back wall when that place is behind it (K525's strings), and step towards
  the audience when a floor-standing instrument is in the way (`MonkFloor`).
  Size unchanged. Previews re-rendered in `renders/phase5/scene_preview/`.
  `DelayLamaSceneTest` (13), `DelayLamaSetupTest`, `DelayLamaMixerTest`,
  `SpecCoverageTest`, `CinematicCameraTest` and `InstrumentAssignmentTest`
  pass.
- 2026-11-09: Phase 5 midis2jam2 side on `monk-sprites` (not committed):
  frame reports into `MonkFrames`, `--hidden`, the window fallback, the
  billboards (`MonkBillboards`, `cm/delaylama/MonkStage.kt`), the stand-in
  place and the cameras, `view=` and the panel's "Show the monks", 6
  catalogue entries (`delaylama.scene.*`, `DelayLamaSceneTest`), and the
  `:app:delayLamaScenePreview` tool (PNGs in `renders/phase5/scene_preview/`,
  the panel in `renders/phase5/panel_preview/`). D69 records the placement
  and size for the user's look. `desktopTest`: 706 tests, 705 passed, 3
  skipped; `TickStabilityTest` "stepping a silent file" timed out under load
  and passes alone, and `BankSelectAssignmentTest`'s catalogue sweep was
  left out because it stalls on this machine at the base commit too (its
  headless app stops itself about 5 s after boot). Played `k525_mvt1.mid`
  channel 1 in each view with the new helper: scene and both log frame
  reports throughout and stand the choir in the scene, windows asks for
  none.
- 2026-11-09: Fixed Play pressed twice quickly starting the song twice on
  top of itself (midis2jam2 `ApplicationService`: one performance at a
  time, by compare-and-set; a failed start frees Play). Spec
  `home.play.one-at-a-time`, `ApplicationServiceTest`. Not committed; not
  tried by hand in the launcher.
- 2026-11-09: README gained "Building from source": the three public repos
  and their branches, the prerequisites, cloning into `external/` (with
  upstream midis2jam2 as `origin` for the package's source patch), and the
  build, run and package steps. Not tried on a fresh machine.
- 2026-11-09: Pushed to GitHub at the user's request: top-level `main` to
  Merken19/delay-lama-everything, delalalalay-lama `voice-helper` to its
  `origin`, midis2jam2 `delay-lama` to the new fork Merken19/midis2jam2
  (remote `fork`). Unpushed commits were rewritten to the no-reply email
  (same trees, dates and messages), and each repo now commits with it.
- 2026-11-09: Phase 5 helper side on delalalalay-lama `monk-sprites`
  (not committed): `set report.frames` in both modes, the `frames` line
  from the window's tick (`ChoirFrames`, `Windows/voice_frames.*`), a full
  line at once after each `set report.frames 1`, `--hidden`, and one stdout
  lock. New CTest `delay_lama_voice_frames` and
  `delay_lama_voice_frames_cli` (the live helper, hidden and silent);
  CTest 11/11, /W4 clean. The release build is in `Windows/build/Release/`.
- 2026-11-08: The user answered the completion questions (D61–D64, D10
  revised, O-items confirmed, O19 open). Committed the D57–D60 work:
  delalalalay-lama `48a4c43` on `voice-helper` (CTest 9/9) and midis2jam2
  `ca72ffb9` on `delay-lama` (693 tests, 0 failures, 3 skipped); nothing is
  pushed. Rebuilt the package from those commits
  (`dist/DelayLamaEverything-2026-11-08-windows-x64.zip`, 193 MB), and
  `check_package.ps1` passed. Removed the merged `phase2-check` branch and
  its worktree registration. The docs are trimmed to the current state,
  with the older history dropped. At the user's request, deleted the WAVs
  of every answered listening set in `renders/` (313 files, 1.1 GB). The
  scripts, MIDI, answers and PNGs stay; the 4c tools render their WAVs
  again from MIDI.
