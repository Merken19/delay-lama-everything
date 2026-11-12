# Test MIDI files

Files for trying Delay Lama by ear. Play one with the channels in the
"Sing with" column, from `external\midis2jam2` (JDK 21 and the Android SDK
set as in `CLAUDE.md`):

```powershell
$env:MIDIS2JAM2_DELAY_LAMA = 'channels=1'
.\gradlew.bat run --args="..\..\tests\midi\01_melody.mid"
```

Channels count from 1; `2.1` means port 2, channel 1. Each program maps to
an imitation profile (shown in brackets); add `;profile=plain` for plain
Delay Lama, or `;view=windows` to see the monks in their own windows.

## The generated set

`01`–`07` are written by `tools/testmidi/make_test_midis.py` from scratch,
with the standard library only. Each is format 1, 480 ticks per beat,
29–43 s long, with markers for its sections.

```powershell
py tools\testmidi\make_test_midis.py          # rewrites tests\midi\0*.mid
py tools\testmidi\make_test_midis.py --list   # also prints each file's channels, programs, bends and RPN 0s
```

| File | What's in it | Sing with | Listen for |
| --- | --- | --- | --- |
| `01_melody.mid` | Violin on 1 (`lead.singer`): slurs, repeated B4s (bar 5), a fast run, staccato (bars 9–10), long notes, a CC 11 swell on bar 4's A4. 31 s. | `channels=1` | Slurs connect, repeats restart, staccato is short, the long A4 swells and fades. |
| `02_chords.mid` | Piano on 1 (`piano`): triads, four-note chords, a five-note chord (bar 9), pedal-held arpeggios (bars 10–11), a moving top voice (bar 12). String pad on 2 (`lead.singer`). 38 s. | `channels=1`; `channels=2`; `channels=1;monks=8` | Bar 9: four monks sing, keeping the top and bottom notes (eight monks sing all five). Arpeggio notes ring while the pedal is down. The pad slurs from chord to chord. |
| `03_band.mid` | Alto sax lead on 1 (`sax.alto`, from bar 5), finger bass on 2 (`bass.finger`), clean guitar on 3 (`guitar.clean`), pad on 4 from bar 9 (`pad`), drums on 10. 38 s. | `channels=1`; `channels=1,2` | The sax monk waits 4 bars. Both choirs keep time with the drums and are easy to hear over the band. |
| `04_bends.mid` | Overdrive guitar on 1 (`guitar.overdrive`) with bends: range 2 (bars 1–4), RPN 0 = 12 (bars 5–8), an NRPN that must not change the range (bars 9–10), RPN 0 = 7 (bars 11–12), a GM System On SysEx back to 2 (bars 13–14). Organ on 2 plays each held bend's target. 38 s. | `channels=1` | The monk lands on the organ's note every time. Seeking into bars 5–12 keeps that section's range. |
| `05_lyrics.mid` | Voice Oohs on 1 (`choir.oohs`) with a lyric on every note, two verses (one ending lines with `\r`, one starting them with `/`), soft piano on 2. 43 s. | `channels=1` | The lyrics show in the 3D window line by line; the singing is unchanged (the monks never sing words). |
| `06_multiport.mid` | Two ports with the same channels. Port 1: violin on 1 (a whole-step bend in bar 8), drums on 10. Port 2: cello on 1 (RPN 0 = 12, an octave slide in bar 6), piano on 2. 29 s. | `channels=1,2.1`; `channels=2.1` | Each choir keeps its own program and bends. With `2.1` alone, only the cello is sung. |
| `07_guitars.mid` | Piano on 1 (`piano`), clean guitar on 2, overdrive guitar on 3, banjo on 4 (no profile of its own, so `default`), finger bass on 5, drums on 10, all from bar 1. 31 s. | `channels=1,2,3,4,5`; `channels=2,5` | Guitars, banjo and bass stand in the right wing's rows with the bass in front; the piano's choir fans out on its own. |

In every file, check that the monks sing the right part in time, that the
band comes down 6 dB while a channel is sung, that each sung instrument is
replaced by its choir (`keep3d` keeps it), and that seeking or pausing stops
the monks at once.

## Other MIDI files

- `k525_mvt1.mid`: Mozart's K525, first movement, a real file of about
  6 minutes. Five string channels, all program 48; violin 1 is channel 1.
  Sing it with `channels=1`.
- `ab/`: short clips, about 12 s each, one per instrument. `_solo` is the
  instrument alone, `_band` is it in a band of finger bass, piano and
  drums, and `_rest` is that band without it.

  | Clips | Instrument | Sing with |
  | --- | --- | --- |
  | `c01_bass_*` | finger bass | `channels=2` |
  | `c02_piano_*` | piano | `channels=3` |
  | `c03_trumpet_*` | trumpet | `channels=1` |
  | `c04_sax_*` | tenor sax | `channels=1` |
  | `c05_flute_*` | flute | `channels=1` |
  | `c06_violin_*` | violin | `channels=1` |
  | `c07_guitar_*` | overdrive guitar | `channels=1` |
  | `c08_velocity_solo` | the trumpet line at velocities 40–120 | `channels=1` |
  | `c09_drums`, `c09_rest` | drums alone, and the band without them (trumpet, bass, piano) | `channels=1` on `c09_rest` |
