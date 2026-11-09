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

- [ ] Fork wyskoj/midis2jam2 to the user's GitHub and push `delay-lama`
      there (D62). Then the package's `NOTICE.txt` can point at the fork
      instead of the patch (D55)

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
- [ ] Flip the Delay Lama switch while a file plays, mid-note too: does the
      sound swap cleanly in time, do the windows hide and return, and do the
      instruments come and go (D60)?
- [ ] The unzipped package: play a file with sung channels, try Add Delay
      Lama, make a recording, read `NOTICE.txt`

### Release

- [ ] The final package once 4c and the fork are done, with
      `check_package.ps1` and the user's check above

## After v1

- Monks in the 3D scene (phase 5): helper `state` reports, textured monk
  quads where the hidden instrument stood, and a setting for windows,
  in-scene or both (D2, D61).

## Log

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
