# Phase 4c pipe: measurements

Written by `measure_4c_pipe.py` (DelayLamaVoice in profile mode, 48 kHz; Gervill with the JDK's soundbank).

## 1. Fold (D37)

| Phrase | Written median | range.shift |
| --- | --- | --- |
| tongued | E6 | -24 |
| slurred | B5 | -12 |
| run | G5 | -12 |
| long | E6 | -24 |
| low | B4 | +0 |
| melody | B5 | -12 |

## 2. Harmonics of a held note

Each sounding note held 1.5 s (no burst, vibrato floor), 0.5-1.4 s after the onset: harmonics 2-6 in dB against the fundamental (H1), and which harmonic is the loudest. Gervill's flute (GM 74) at the same note for comparison. '-' is above 24 kHz.

| Note | Monk H2..H6 vs H1 (dB) | Monk loudest | Gervill H2..H6 vs H1 (dB) | Gervill loudest |
| --- | --- | --- | --- | --- |
| C4 | -7 -10 -24 -39 -54 | H1 | +4 -4 -5 -9 -29 | H2 |
| D#4 | -13 -28 -44 -65 -53 | H1 | +2 -6 -5 -11 -32 | H2 |
| F#4 | -7 -30 -65 -49 -28 | H1 | +3 -5 -8 -11 -31 | H2 |
| A4 | -9 -33 -51 -22 -2 | H1 | +3 -5 -6 -13 -33 | H2 |
| C5 | -15 -51 -26 +4 -30 | H5 | +0 -2 -23 -35 -34 | H2 |
| D#5 | -26 -49 -10 -30 -13 | H1 | +1 -4 -23 -35 -32 | H2 |
| F#5 | -55 -31 -25 -18 -38 | H1 | -9 -29 -31 -49 -49 | H1 |
| A5 | -42 +7 -12 -27 -19 | H3 | -8 -31 -30 -49 -48 | H1 |
| C6 | -16 -6 -11 -6 -49 | H1 | -9 -30 -29 -49 -48 | H1 |
| D#6 | +13 +18 +17 -37 -37 | H3 | -12 -23 -48 -52 -63 | H1 |
| F#6 | +32 +12 -9 -32 -28 | H2 | -10 -22 -45 -50 -60 | H1 |
| A6 | +28 +23 -19 -20 -22 | H2 | -22 -45 -55 -93 -90 | H1 |
| C7 | +32 +1 -11 -13 -17 | H2 | -22 -45 -56 -85 -90 | H1 |

## 3. Onsets in melody.mid (sung -12 st)

For each note: the first 80 ms against the same note 150-250 ms in (or its last 100 ms if shorter). Level: loudest 10 ms frame, dB. Flare: the largest rise of any bin up to 3.5 kHz within 40 dB of the note's loudest. Breath: 3.5-6 kHz band energy. Medians and worst cases over the notes; 'onset' notes start from silence or a tongued break, 'slur' notes are legato.

| Variant | Level med / max | Flare med / max (worst note) | Breath med / max |
| --- | --- | --- | --- |
| now | +0.4 / +7.7 | +11.9 / +38.8 (A4) | +0.9 / +6.7 |
| no burst | +0.4 / +7.7 | +11.9 / +38.8 (A4) | +0.9 / +6.7 |
| F3 off | +0.4 / +11.1 | +9.8 / +38.8 (A4) | +0.9 / +6.8 |

## 4. Pitch at the onsets of melody.mid

YIN over each note's first 120 ms after it is 15 ms old: the largest distance from the sounding pitch (cents), and the median.

Worst 3567 cents (G5); medians -12..+30 cents over 46 notes.

## 5. Level

melody.mid: Gervill's flute -17.2 LUFS, the profile's monk -23.2 LUFS (-5.9 dB).

## 6. Taming the buzz: formants and breath

Held notes as in section 2: energy above 1.5 kHz in dB of the total (a flute is mostly below), and the loudest of H2-H4 against H1. F2 off leaves the breath partials (3.8, 4.95 kHz) on their own, so the share goes up again.

| Sounding | Gervill | now | F3 off | F3 off, breath 0.3 | F3 off, size 0.5 | F3 and F2 off |
| --- | --- | --- | --- | --- | --- | --- |
| E4 | -15 / +4 | -13 / -6 | -17 / -6 | -25 / -6 | -11 / -6 | -16 / -30 |
| A4 | -9 / +3 | -2 / -9 | -6 / -9 | -14 / -9 | -5 / -11 | -5 / -25 |
| C5 | -6 / +0 | -0 / -15 | -6 / -15 | -13 / -15 | -8 / -20 | -3 / -30 |
| E5 | -6 / +0 | -2 / +1 | -15 / -35 | -23 / -35 | -19 / -44 | -2 / -34 |
| A5 | -8 / -8 | -1 / +7 | -10 / -12 | -17 / -20 | -6 / -8 | -2 / +6 |
| C6 | -8 / -9 | -4 / -6 | -6 / -11 | -13 / -19 | -4 / -7 | -3 / +8 |
| D#6 | -9 / -12 | -0 / +18 | -0 / +18 | -1 / +10 | -0 / +22 | -0 / +44 |
| F#6 | -8 / -10 | -0 / +32 | -9 / +12 | -16 / +4 | -8 / +20 | -9 / +21 |
| A6 | -0 / -22 | -2 / +28 | -2 / +25 | -7 / +16 | -2 / +29 | -2 / +40 |
| C7 | -0 / -22 | -10 / +32 | -10 / +31 | -17 / +21 | -9 / +34 | -9 / +36 |

