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
- [ ] User check: do the billboards sit well on stage (D69's placement and
      size), and do the mouths move in time with the singing?

## Log

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
