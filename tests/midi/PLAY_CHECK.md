# Play check

The roadmap's user check "Play the test files". Play each file below live
with the channels given, and answer the questions (in chat, or under
"Answers" at the end of this file). How it sounds is your call; Claude
checked offline that every file loads and that the router sends the
chosen channel's notes, bends and bend ranges to its helper
(2026-11-05).

## Setup (once per PowerShell window)

From the top-level folder:

```powershell
cd external\midis2jam2
$env:JAVA_HOME = 'C:\Program Files\Java\jdk-21'
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
```

Then, for each row, set the channels and play the file (it starts at
once; close the 3D window, or let the file end, then close the launcher
before the next one). Leave other Delay Lama windows closed.

## Files

| # | Commands | Look and listen for |
| --- | --- | --- |
| 1 | `$env:MIDIS2JAM2_DELAY_LAMA = 'channels=1'`<br>`.\gradlew.bat run --args="..\..\tests\midi\01_melody.mid"` | One monk window, top left. The violin melody is the only part, so you hear only the monk. Slurs connect, the repeated B4s (bar 5) restart, the staccato bars (9-10) are short, the long A4 (bar 4) swells and fades. |
| 2a | `$env:MIDIS2JAM2_DELAY_LAMA = 'channels=1'`<br>`.\gradlew.bat run --args="..\..\tests\midi\02_chords.mid"` | A choir of 4 monks for the piano, over the band's string pad. Bar 9's five-note chord: four monks sing, and the top and bottom notes are kept. Bars 10-11: the arpeggio notes keep sounding while the pedal is down, and stop when it lifts. |
| 2b | `$env:MIDIS2JAM2_DELAY_LAMA = 'channels=2'`<br>`.\gradlew.bat run --args="..\..\tests\midi\02_chords.mid"` | The string pad sung by a choir of singers (D42), slurred from chord to chord, under the piano. |
| 3 | `$env:MIDIS2JAM2_DELAY_LAMA = 'channels=1,2'`<br>`.\gradlew.bat run --args="..\..\tests\midi\03_band.mid"` | Two monk windows (channel 1 above channel 2). The bass monk sings from the start; the sax monk waits 4 bars, then sings the lead. Both in time with the drums; the monks easy to hear over the band. |
| 4 | `$env:MIDIS2JAM2_DELAY_LAMA = 'channels=1'`<br>`.\gradlew.bat run --args="..\..\tests\midi\04_bends.mid"` | The organ plays each held bend's target note: the monk should land on it every time. Bars 1-4 a whole step and small dips, bars 5-8 an octave slide, bars 9-10 an octave again (an NRPN must not change the range), bars 11-12 a fifth, bars 13-14 a whole step (after a GM reset). Then once more, seeking into bars 5-12 with the playback bar: the bends there keep their section's size. |
| 5 | `$env:MIDIS2JAM2_DELAY_LAMA = 'channels=1'`<br>`.\gradlew.bat run --args="..\..\tests\midi\05_lyrics.mid"` | The lyrics show in the 3D window, line by line, in both verses; the monk sings the melody as usual (Delay Lama never sings words, D61). |
| 6a | `$env:MIDIS2JAM2_DELAY_LAMA = 'channels=1,2.1'`<br>`.\gradlew.bat run --args="..\..\tests\midi\06_multiport.mid"` | Two monk windows, "channel 1" and "port 2, channel 1". The first sings the high violin line (a small bend in bar 8), the second the low cello line (an octave slide up in bar 6). Neither takes the other's bends. |
| 6b | `$env:MIDIS2JAM2_DELAY_LAMA = 'channels=2.1'`<br>`.\gradlew.bat run --args="..\..\tests\midi\06_multiport.mid"` | Only the cello is sung; the violin plays on Gervill. |

When you are done: `Remove-Item Env:MIDIS2JAM2_DELAY_LAMA`.

## Questions

For each row: did the monk sing the right part, in time, with nothing
missing or stuck? Anything that glitched or sounded wrong (which file,
which bar)?

Any window mode works (Settings, Graphics): Fullscreen opens as borderless
while Delay Lama sings, so the monk windows stay on top (D47).

## Answers

(empty)
