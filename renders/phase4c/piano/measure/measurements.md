# Phase 4c piano: measurements

Written by `measure_4c_piano.py` (DelayLamaVoice in profile mode, 48 kHz).

## 1. Tuning of single notes

Piano profile with no decay, one monk, 4 s; mean pitch of the strongest of the first four harmonics over 0.6-4.2 s, weighted by its amplitude. Model: the DSP's two quantizations under the 0.2 st vibrato floor (see the script).

| Note | Hz | Period (samples) | Measured (cents) | Model (cents) | Vibrato peak (cents) |
| --- | --- | --- | --- | --- | --- |
| C3 | 130.8 | 366.94 | +3.4 | +1.6 | 22 |
| C#3 | 138.6 | 346.34 | +2.0 | +1.1 | 21 |
| D3 | 146.8 | 326.90 | +1.1 | +1.1 | 22 |
| D#3 | 155.6 | 308.56 | +0.6 | +1.6 | 20 |
| E3 | 164.8 | 291.24 | -0.6 | +1.5 | 21 |
| F3 | 174.6 | 274.89 | +1.8 | +2.6 | 23 |
| F#3 | 185.0 | 259.46 | +2.0 | +2.1 | 20 |
| G3 | 196.0 | 244.90 | +2.2 | +1.3 | 22 |
| G#3 | 207.7 | 231.16 | +2.5 | +2.1 | 21 |
| A3 | 220.0 | 218.18 | +3.4 | +2.9 | 20 |
| A#3 | 233.1 | 205.94 | +5.0 | +2.5 | 24 |
| B3 | 246.9 | 194.38 | +5.2 | +3.0 | 21 |
| C4 | 261.6 | 183.47 | +4.8 | +3.4 | 20 |
| C#4 | 277.2 | 173.17 | +3.8 | +3.1 | 22 |
| D4 | 293.7 | 163.45 | +4.1 | +4.4 | 23 |
| D#4 | 311.1 | 154.28 | +3.5 | +5.0 | 23 |
| E4 | 329.6 | 145.62 | +1.4 | +3.7 | 19 |
| F4 | 349.2 | 137.45 | +5.6 | +5.8 | 24 |
| F#4 | 370.0 | 129.73 | +4.4 | +4.8 | 22 |
| G4 | 392.0 | 122.45 | +2.7 | +4.1 | 21 |
| G#4 | 415.3 | 115.58 | +6.6 | +6.3 | 25 |
| A4 | 440.0 | 109.09 | +5.0 | +6.0 | 26 |
| A#4 | 466.2 | 102.97 | +5.9 | +6.3 | 25 |
| B4 | 493.9 | 97.19 | +5.2 | +5.5 | 21 |
| C5 | 523.3 | 91.73 | +8.9 | +9.6 | 25 |
| C#5 | 554.4 | 86.59 | +2.8 | +9.6 | 19 |
| D5 | 587.3 | 81.73 | -1.8 | +10.6 | 37 |
| D#5 | 622.3 | 77.14 | +10.6 | +10.8 | 23 |
| E5 | 659.3 | 72.81 | +8.4 | +8.7 | 15 |
| F5 | 698.5 | 68.72 | +3.0 | +11.2 | 15 |
| F#5 | 740.0 | 64.87 | +1.6 | +11.2 | 29 |
| G5 | 784.0 | 61.23 | +2.0 | +13.1 | 35 |
| G#5 | 830.6 | 57.79 | -5.0 | +11.9 | 77 |
| A5 | 880.0 | 54.55 | -2.9 | +12.1 | 45 |
| A#5 | 932.3 | 51.48 | +1.1 | +13.1 | 43 |
| B5 | 987.8 | 48.59 | -4.9 | +11.2 | 81 |
| C6 | 1046.5 | 45.87 | -4.7 | +16.0 | 46 |

## 2. Intervals in a held chord

Three monks hold the chord 6 s (no decay). Each note's pitch is followed through its fundamental and smoothed over 5 ms. For each pair: the mean interval error, its standard deviation and the 1-99 % span (cents), i.e. how far the interval wobbles as the monks' vibrato floors (±0.2 st each) run apart.

| Setting | Mean error per note (cents) | Interval error: mean ± sd (span) | Worst span |
| --- | --- | --- | --- |
| 60-64-67: now (own seeds, vibrato_var 0.08) | +3.3, +3.7, +4.0 | +0.4 ±22.5 (span 75); +0.7 ±21.0 (span 78); +0.3 ±20.6 (span 76) | 78 |
| 60-64-67: own seeds, vibrato_var 0 | +3.3, +3.7, +4.0 | +0.5 ±19.9 (span 74); +0.7 ±23.1 (span 78); +0.3 ±16.0 (span 72) | 78 |
| 60-64-67: own seeds, vibrato_var 0.2 | +3.4, +3.7, +4.0 | +0.3 ±19.9 (span 75); +0.6 ±20.0 (span 77); +0.3 ±19.9 (span 76) | 77 |
| 60-64-67: one seed, vibrato_var 0 (lockstep) | +3.3, +3.6, +4.1 | +0.3 ±2.6 (span 10); +0.8 ±3.7 (span 13); +0.5 ±2.0 (span 8) | 13 |
| 60-64-67: vibrato.lock 1 (new in phase 4c) | +3.3, +3.5, +3.9 | +0.2 ±2.5 (span 10); +0.7 ±3.8 (span 13); +0.5 ±2.1 (span 8) | 13 |
| 57-60-64: now (own seeds, vibrato_var 0.08) | +2.8, +3.5, +3.6 | +0.7 ±23.3 (span 77); +0.8 ±20.8 (span 75); +0.1 ±20.7 (span 76) | 77 |
| 57-60-64: own seeds, vibrato_var 0 | +2.6, +3.5, +3.6 | +0.8 ±22.0 (span 77); +0.9 ±24.3 (span 76); +0.1 ±16.0 (span 72) | 77 |
| 57-60-64: own seeds, vibrato_var 0.2 | +2.9, +3.5, +3.6 | +0.6 ±20.7 (span 77); +0.7 ±19.8 (span 76); +0.1 ±20.1 (span 76) | 77 |
| 57-60-64: one seed, vibrato_var 0 (lockstep) | +2.9, +3.3, +3.6 | +0.4 ±4.1 (span 15); +0.8 ±2.7 (span 11); +0.3 ±3.4 (span 12) | 15 |
| 57-60-64: vibrato.lock 1 (new in phase 4c) | +2.6, +3.3, +3.5 | +0.6 ±4.2 (span 15); +0.8 ±2.8 (span 11); +0.2 ±3.3 (span 12) | 15 |

In music the monks' histories differ. The same chord (C4-E4-G4) after five melody notes on the first monk, and as a pedalled arpeggio (300 ms apart, held together):

| Setting | Mean error per note (cents) | Interval error: mean ± sd (span) | Worst span |
| --- | --- | --- | --- |
| after a melody: now (own seeds, vibrato_var 0.08) | +3.2, +3.7, +4.0 | +0.5 ±21.3 (span 76); +0.8 ±19.9 (span 77); +0.3 ±20.6 (span 76) | 77 |
| arpeggio: now (own seeds, vibrato_var 0.08) | +3.1, +3.8, +4.0 | +0.7 ±17.5 (span 74); +0.8 ±20.0 (span 77); +0.2 ±20.5 (span 76) | 77 |
| after a melody: one seed, vibrato_var 0 (lockstep) | +3.2, +3.6, +4.1 | +0.4 ±16.2 (span 71); +0.9 ±16.8 (span 74); +0.5 ±2.0 (span 8) | 74 |
| arpeggio: one seed, vibrato_var 0 (lockstep) | +3.4, +3.7, +3.9 | +0.4 ±17.1 (span 65); +0.5 ±25.3 (span 79); +0.2 ±17.1 (span 67) | 79 |
| after a melody: vibrato.lock 1 (new in phase 4c) | +3.3, +3.6, +4.0 | +0.3 ±2.6 (span 10); +0.7 ±3.8 (span 13); +0.4 ±2.0 (span 8) | 13 |
| arpeggio: vibrato.lock 1 (new in phase 4c) | +3.3, +3.5, +4.0 | +0.2 ±2.5 (span 10); +0.7 ±3.7 (span 13); +0.4 ±2.0 (span 8) | 13 |

## 3. Decay

Level (dB below each note's peak, 50 ms RMS) at times after the onset, single notes held 6 s. Gervill: its default soundbank, as midis2jam2 plays. Monk: the piano profile as it is (decay 900 ms at C4, sustain 0, track 0.7; a note ends 40 dB down). Monk longer: decay 2500 ms at C4, track 0.85 (the candidate).

| Note | Source | 0.1 s | 0.3 s | 0.5 s | 1 s | 1.5 s | 2 s | 3 s | 4 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C3 | Gervill | -0 | -5 | -8 | -11 | -14 | -17 | -23 | -28 |
| C3 | Monk now | -1 | -8 | -12 | -20 | -30 | -44 | -152 | -152 |
| C3 | Monk longer | -0 | -5 | -7 | -9 | -13 | -18 | -27 | -36 |
| C4 | Gervill | -2 | -7 | -10 | -15 | -18 | -22 | -29 | -36 |
| C4 | Monk now | -2 | -13 | -19 | -29 | -68 | -154 | -154 | -154 |
| C4 | Monk longer | -1 | -9 | -10 | -11 | -16 | -21 | -32 | -155 |
| C5 | Gervill | -2 | -11 | -15 | -19 | -23 | -28 | -36 | -45 |
| C5 | Monk now | -4 | -13 | -16 | -37 | -149 | -149 | -149 | -149 |
| C5 | Monk longer | -2 | -5 | -2 | -4 | -11 | -17 | -29 | -149 |

## 4. Note endings: does the 'ng' sweep flare?

Each note held 600 ms with the longer decay (2.5 s at C4), then released (release 120 ms). 'Rise' is the loudest 10 ms frame of the release against the note's level just before the key lifts (the level itself falls 26 dB over the release, so anything above about -2 dB is the sweep). 'Worst bin': the largest rise of any bin up to 3.5 kHz (below the breath partials) within 40 dB of the note's loudest, against that bin's own highest level in the 60 ms before.

| Note | 'ng' (now): rise | 'ng': worst bin | No 'ng': rise | No 'ng': worst bin |
| --- | --- | --- | --- | --- |
| C3 | +0.8 dB | +25.7 dB | +0.8 dB | +1.1 dB |
| E3 | +0.5 dB | +25.0 dB | +0.4 dB | +2.7 dB |
| G#3 | -2.0 dB | +25.3 dB | -1.9 dB | +0.7 dB |
| C4 | -1.3 dB | +23.9 dB | -1.3 dB | +2.2 dB |
| E4 | -0.7 dB | +23.7 dB | -0.7 dB | +12.2 dB |
| G#4 | -1.4 dB | +24.0 dB | -1.3 dB | +10.6 dB |
| C5 | -0.3 dB | +24.8 dB | -0.3 dB | +6.0 dB |
| E5 | +2.4 dB | +37.8 dB | -0.4 dB | +16.3 dB |
| G#5 | +8.8 dB | +43.3 dB | -0.6 dB | +23.9 dB |
| C6 | -0.6 dB | +23.6 dB | -0.7 dB | +14.5 dB |

## 5. Vowel drift and the decay

One note held 1.8 s with the longer decay (2.5 s at C4, track 0.85). Level (30 ms RMS) minus the exponential decay it should follow, 0.05-1.5 s after the onset, lined up on the first 0.1 s: lowest..highest in dB (+ = the note swells).

| Note | drift i>e (now) | steady i | steady ih (0.88) | steady e (0.75) |
| --- | --- | --- | --- | --- |
| C3 | -4.7..+0.1 | -1.8..+0.2 | -0.4..+2.1 | -0.2..+0.4 |
| G3 | -0.4..+6.3 | -0.2..+2.2 | -2.6..+0.9 | -0.6..+0.2 |
| C4 | -6.3..+0.6 | -0.2..+0.5 | -1.0..+0.2 | -1.6..+0.1 |
| E4 | -1.0..+6.2 | -0.1..+2.4 | -0.4..+0.3 | -0.0..+0.3 |
| G4 | -0.4..+8.5 | -0.5..+5.3 | -0.2..+3.0 | -0.2..+1.8 |
| C5 | -1.3..+9.1 | -0.6..+3.7 | -0.5..+0.8 | -2.4..+1.7 |
| E5 | -0.1..+4.9 | -0.1..+0.8 | -0.0..+0.6 | -0.3..+0.0 |
| G5 | -5.7..+2.2 | -0.9..+6.9 | -0.7..+6.9 | -0.4..+3.2 |
| C6 | -1.5..+9.8 | -0.0..+5.3 | -0.0..+4.3 | -2.4..+0.0 |

