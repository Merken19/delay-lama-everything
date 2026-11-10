# Test MIDI files

Test files for playing Delay Lama by hand. Every file is composed by
[`tools/testmidi/make_test_midis.py`](../../tools/testmidi/make_test_midis.py)
(standard library only; nothing here was downloaded), so the set can be
remade, or changed, with:

```powershell
py tools\testmidi\make_test_midis.py          # writes tests\midi\*.mid
py tools\testmidi\make_test_midis.py --list   # and prints each file's channels, programs, bends and RPN 0s
```

Each file is format 1 at 480 ticks per beat, 30-45 s long, with markers for
its sections. Channels are numbered from 1 here, as in the app and in
`MIDIS2JAM2_DELAY_LAMA` (README.md, "Command-line settings"). Every
program maps to a profile in `profiles/imitation.json` (profile mode is the
default; add `;profile=plain` for plain Delay Lama). A manual play check
with these files is in [PLAY_CHECK.md](PLAY_CHECK.md).

| File | Tests | Sing it with |
| --- | --- | --- |
| `01_melody.mid` | One line on one channel (violin, `lead.singer`): slurs, a repeated note, a fast slurred run, staccato with rests, long notes, and a CC 11 swell on bar 4's held A4. 92 bpm, 31 s. | `channels=1` |
| `02_chords.mid` | Chords on channel 1 (piano, `piano`): triads, four-note chords (a full choir of 4), a five-note chord in bar 9 (one more than the choir: voice stealing, which keeps the top and bottom notes), arpeggios held only by the sustain pedal (bars 10-11) and a top voice moving over a held chord (bar 12). Channel 2 doubles the harmony as a slurred string pad (`lead.singer`). 84 bpm, 38 s. | `channels=1` (piano choir); `channels=2` (string pad); `channels=1;monks=8` (no stealing) |
| `03_band.mid` | A band on 5 channels: alto sax lead on 1 (`sax.alto`; it enters at bar 5, so its monk waits 4 bars), finger bass on 2 (`bass.finger`), clean guitar off-beats on 3 (`guitar.clean`), a warm pad on 4 from bar 9 (`pad`), drums on 10. 110 bpm, 38 s. | `channels=1` (lead); `channels=1,2` (lead and bass: two choirs) |
| `04_bends.mid` | Pitch bends on channel 1 (overdrive guitar, `guitar.overdrive`). Bars 1-4 at the default range of 2 (no RPN): a whole-step bend, two dips, a dense vibrato of bends. Bars 5-8 after RPN 0 = 12: an octave slide and a +6 bend. Bars 9-10 after an NRPN with data entry (99/98 = 32/32, CC 6 = 64), which must not change the range: the slide is an octave again. Bars 11-12 after RPN 0 = 7: a fifth. Bars 13-14 after a GM System On SysEx: the range is 2 again. Channel 2 (organ) plays each held bend's target note softly, so you can hear whether the monk lands on it. 90 bpm, 38 s. | `channels=1` |
| `05_lyrics.mid` | A sung melody on channel 1 (Voice Oohs, `choir.oohs`) with a Lyric meta event on every note, two verses, over a soft piano on channel 2. Verse 1 ends each line with a `\r` lyric event, verse 2 starts each line with `/` (both karaoke conventions midis2jam2 reads). The helper doesn't sing words; the lyrics should show in the 3D window and change nothing in the singing. 96 bpm, 43 s. | `channels=1` |
| `06_multiport.mid` | Two MIDI ports with the same channel numbers. MIDI Port meta events (FF 21) put tracks 1-2 on the file's port 0 and tracks 3-4 on port 1; midis2jam2 numbers the ports a file uses in order, so they are its ports 1 and 2 (`MidiPort.kt`, `portedEventsInPlayOrder`). Port 1: violin on channel 1 (default bend range; a whole-step bend in bar 8), drums on 10. Port 2: cello on channel 1 (RPN 0 = 12; an octave slide in bar 6), piano on 2. Each port plays on its own Gervill, so the two channel 1s keep their own program and bend range. 100 bpm, 29 s. | `channels=1` (violin, port 1); `channels=2.1` (cello, port 2); `channels=1,2.1` (both) |

Things to watch in any of them: the monk sings in time with the band (the
offset), the band is 6 dB down while a channel is sung (the balance), the
sung channel's 3D instrument is replaced by its choir (`keep3d` keeps it),
and seeking or pausing stops the monks at once. In `04_bends.mid`, seeking
into bars 5-12 should keep that section's range (the seek chase rebuilds
RPNs).

Notes on the file format: the conductor track (tempo, time signature,
markers) has no channel events, so it uses no port. midis2jam2 reads only
the MIDI Port meta event (FF 21) for ports; the MIDI Channel Prefix (FF 20)
is a different thing and is not used here.

## Other MIDI files in the repo

- `renders/phase2/k525_mvt1.mid`: Mozart's K525, first movement, a real
  file (violin 1 is channel 1, program 48). `channels=1`.
- `renders/phase4a/ab/midi/`: short A/B clips (c01 bass to c09 drums), each
  a solo, rest or band version of one instrument.
