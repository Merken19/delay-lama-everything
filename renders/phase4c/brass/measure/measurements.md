# Phase 4c brass and sax: measurements

Written by `measure_4c_brass.py` (DelayLamaVoice in profile mode, 48 kHz, a copy of the helper built with `voice.formant1-3`; Gervill with the JDK's soundbank).

## 1. Profiles and fold

As `expand.resolve` gives them (the router sends these). GM programs 0-based: trumpet and muted trumpet (56, 59) map to `trumpet`, horn, brass section and synth brass (60-63) to `brass.section`, soprano and alto (64-65) to `sax.alto`, tenor and baritone (66-67) to `sax.tenor`.

- `trumpet`: `{"onset":{"vowel":null,"time":15,"curve":0,"attack":6,"lips":0,"burst":0.6,"burst_time":30,"scoop":-0.4,"scoop_time":40,"peak":1.15},"body":{"vowel":null,"decay":150,"sustain":0.8},"ending":{"vowel":null,"vowel_time":null,"release":100,"lips":0},"phrase":{"dip_level":0.05,"mode":2},"nucleus":{"vowel":0.5},"range":{"fit":2,"high":72},"vibrato":{"depth":0.35,"delay":350,"fade":300},"voice":{"size":0.6}}`
- `trombone`: `{"onset":{"vowel":null,"time":40,"curve":3,"attack":25,"lips":1,"burst":null,"burst_time":0,"scoop":-1.5,"scoop_time":120},"body":{"vowel":null,"sustain":1},"ending":{"vowel":0.25,"vowel_time":null,"release":120,"lips":0},"phrase":{"dip_level":0.2,"mode":0,"glide":0.5},"nucleus":{"vowel":0.5},"range":{"fit":2,"high":72},"vibrato":{"depth":0.35,"delay":400,"fade":300},"voice":{"size":0.35}}`
- `tuba`: `{"onset":{"vowel":null,"time":40,"curve":3,"attack":30,"lips":1,"burst":null,"burst_time":0},"body":{"vowel":null,"sustain":0.9},"ending":{"vowel":0.0,"vowel_time":null,"release":100,"lips":1},"phrase":{"dip_level":0.2,"mode":2},"nucleus":{"vowel":0.25},"range":{"fit":2,"high":72},"voice":{"size":0.0}}`
- `brass.section`: `{"onset":{"vowel":null,"time":40,"curve":3,"attack":20,"lips":1,"burst":null,"burst_time":0},"body":{"vowel":null,"sustain":0.85},"ending":{"vowel":null,"vowel_time":null,"release":120,"lips":0},"phrase":{"dip_level":0.2,"mode":2},"nucleus":{"vowel":0.5},"range":{"fit":2,"high":72},"ensemble":{"unison":4,"detune":8}}`
- `sax.alto`: `{"onset":{"vowel":null,"time":50,"curve":3,"attack":20,"lips":0,"burst":null,"burst_time":0,"scoop":-0.8,"scoop_time":100},"body":{"vowel":0.5,"vowel_time":500},"ending":{"vowel":0.25,"vowel_time":null,"release":120,"lips":0},"phrase":{"dip_level":0.2,"mode":1},"nucleus":{"vowel":0.0},"range":{"fit":2,"high":72},"vibrato":{"depth":0.35,"delay":350,"fade":300},"voice":{"size":0.55}}`
- `sax.tenor`: `{"onset":{"vowel":null,"time":50,"curve":3,"attack":3,"lips":0,"burst":null,"burst_time":0,"scoop":-0.8,"scoop_time":100},"body":{"vowel":0.25,"vowel_time":500,"breath":0.6},"ending":{"vowel":null,"vowel_time":null,"release":20,"lips":0},"phrase":{"dip_level":0.2,"mode":1},"nucleus":{"vowel":0.0},"range":{"fit":2,"high":72},"vibrato":{"depth":0.35,"delay":350,"fade":300},"voice":{"size":0.4}}`

Note: `sax.tenor` extends `sax.alto` but its own syllable ("d-u>o") is merged after the parent's entry, so the syllable's defaults replace what the alto set: onset.attack 20 -> 3; ending.vowel 0.25 -> None; ending.release 120 -> 20. IMITATION.md 15 gives every sax attack 20 and an "o" ending over 120 ms, so the tenor sings with a crisper attack and a 20 ms release by accident. Fix (when the profile changes): repeat those keys in `sax.tenor`.

| Line | Profile | Written range (median) | range.shift |
| --- | --- | --- | --- |
| trumpet.mid | trumpet | F4-F5 (C5) | +0 |
| sax.mid | sax.tenor | E3-G4 (C4) | +0 |
| alto.mid | sax.alto | B3-D5 (G4) | +0 |
| trombone.mid | trombone | E2-G3 (C3) | +0 |
| tuba.mid | tuba | E1-G2 (C2) | +0 |
| horn.mid | brass.section | E3-G4 (C4) | +0 |
| trumpet.mid | brass.section | F4-F5 (C5) | +0 |

trumpet.mid sits right at the D37 ceiling (median C5 = `range.high` 72). The same line a tone higher (median D5, a common trumpet lead) would be sung -12 st, an octave below what c03 sang as written and the user kept. A per-profile `range.high` (e.g. 76 for the trumpet) would keep trumpet leads as written; not tested here.

## 2. Held notes against Gervill

Each note held 1.5 s at velocity 96, measured 0.7-1.45 s in (lead vibrato has reached its depth). Per cell: energy above 1.5 kHz in dB of the total / spectral centroid in Hz / loudest harmonic. 'Breath band': the strongest harmonic between 3.5 and 5.5 kHz, its level against the note's loudest harmonic, and its ring (dB above the mean of its two neighbours; a smooth brass spectrum is near 0, a partial that whistles stands out).

### trumpet (GM 56, `trumpet`)

| Note | Gervill | Monk | Gervill breath band (H, vs loudest, ring) | Monk breath band |
| --- | --- | --- | --- | --- |
| G3 | -7 / 1029 / H4 | -6 / 1595 / H6 | H18 -24 dB, ring +2 | H19 -20 dB, ring +5 |
| C4 | -13 / 766 / H3 | -5 / 1791 / H3 | H14 -43 dB, ring +1 | H19 -17 dB, ring +7 |
| E4 | -9 / 960 / H3 | -2 / 2373 / H9 | H11 -32 dB, ring +0 | H15 -15 dB, ring +9 |
| G4 | -9 / 909 / H2 | -9 / 1149 / H2 | H9 -34 dB, ring +0 | H13 -24 dB, ring +10 |
| A4 | -10 / 1016 / H2 | -6 / 1724 / H3 | H8 -31 dB, ring +0 | H11 -17 dB, ring +18 |
| C5 | -6 / 1218 / H2 | -1 / 2572 / H6 | H7 -28 dB, ring -2 | H7 -11 dB, ring +1 |
| D5 | -5 / 1441 / H2 | -1 / 2688 / H5 | H6 -19 dB, ring +2 | H6 -19 dB, ring -6 |
| E5 | -5 / 1651 / H2 | -10 / 1282 / H1 | H6 -20 dB, ring -0 | H6 -16 dB, ring +3 |
| G5 | -0 / 1950 / H2 | -6 / 1186 / H1 | H5 -16 dB, ring -2 | H5 -19 dB, ring -3 |
| A5 | -0 / 2189 / H2 | -5 / 1510 / H1 | H4 -10 dB, ring +3 | H4 -15 dB, ring +4 |
| C6 | -3 / 1957 / H1 | -1 / 2997 / H3 | H4 -15 dB, ring -1 | H5 -12 dB, ring +21 |

### tenor (GM 66, `sax.tenor`)

| Note | Gervill | Monk | Gervill breath band (H, vs loudest, ring) | Monk breath band |
| --- | --- | --- | --- | --- |
| A2 | -13 / 583 / H1 | -7 / 1036 / H4 | H32 -30 dB, ring +10 | H45 -24 dB, ring +4 |
| C3 | -8 / 714 / H1 | -6 / 1193 / H3 | H32 -31 dB, ring +11 | H38 -19 dB, ring +5 |
| E3 | -6 / 913 / H1 | -3 / 1724 / H16 | H22 -20 dB, ring +8 | H30 -15 dB, ring +3 |
| G3 | -7 / 881 / H2 | -7 / 1057 / H2 | H18 -21 dB, ring +6 | H26 -22 dB, ring +5 |
| A3 | -7 / 997 / H2 | -7 / 921 / H2 | H16 -19 dB, ring +3 | H22 -25 dB, ring +7 |
| C4 | -7 / 1192 / H2 | -6 / 1317 / H3 | H14 -18 dB, ring +3 | H19 -25 dB, ring +7 |
| D4 | -5 / 1443 / H3 | -1 / 2259 / H9 | H12 -15 dB, ring +1 | H17 -18 dB, ring +8 |
| E4 | -3 / 1656 / H5 | -2 / 2033 / H8 | H11 -14 dB, ring -2 | H15 -19 dB, ring +11 |
| G4 | -3 / 1510 / H4 | -8 / 924 / H1 | H10 -14 dB, ring +6 | H10 -25 dB, ring +13 |

### alto (GM 65, `sax.alto`)

| Note | Gervill | Monk | Gervill breath band (H, vs loudest, ring) | Monk breath band |
| --- | --- | --- | --- | --- |
| G3 | -8 / 812 / H1 | -7 / 1469 / H4 | H18 -22 dB, ring +2 | H19 -21 dB, ring +5 |
| C4 | -5 / 1155 / H1 | -7 / 1314 / H3 | H15 -22 dB, ring +2 | H19 -22 dB, ring +7 |
| E4 | -6 / 998 / H1 | -1 / 2676 / H9 | H11 -25 dB, ring +2 | H15 -13 dB, ring +9 |
| G4 | -5 / 1187 / H1 | -14 / 1088 / H2 | H10 -23 dB, ring +1 | H13 -24 dB, ring +11 |
| A4 | -5 / 1311 / H1 | -5 / 1723 / H2 | H8 -19 dB, ring +0 | H11 -12 dB, ring +17 |
| C5 | -1 / 2036 / H1 | -4 / 2009 / H2 | H7 -13 dB, ring -1 | H7 -10 dB, ring +3 |
| E5 | -1 / 2536 / H4 | -6 / 1626 / H1 | H6 -9 dB, ring +1 | H6 -12 dB, ring +4 |

### trombone (GM 57, `trombone`)

| Note | Gervill | Monk | Gervill breath band (H, vs loudest, ring) | Monk breath band |
| --- | --- | --- | --- | --- |
| E2 | -12 / 749 / H7 | -6 / 1379 / H8 | H43 -35 dB, ring +0 | H60 -20 dB, ring +3 |
| G2 | -10 / 889 / H6 | -6 / 1358 / H7 | H36 -30 dB, ring +0 | H50 -22 dB, ring +3 |
| C3 | -8 / 963 / H5 | -3 / 1889 / H21 | H27 -31 dB, ring +0 | H38 -11 dB, ring +3 |
| E3 | -10 / 864 / H4 | -5 / 1579 / H6 | H22 -32 dB, ring +1 | H30 -18 dB, ring +5 |
| G3 | -7 / 1031 / H4 | -5 / 1536 / H5 | H18 -26 dB, ring +2 | H26 -19 dB, ring +6 |
| C4 | -8 / 955 / H3 | -7 / 1368 / H4 | H14 -31 dB, ring -1 | H19 -19 dB, ring +7 |
| E4 | -6 / 1187 / H3 | -2 / 2174 / H8 | H11 -23 dB, ring +1 | H15 -17 dB, ring +10 |

### tuba (GM 58, `tuba`)

| Note | Gervill | Monk | Gervill breath band (H, vs loudest, ring) | Monk breath band |
| --- | --- | --- | --- | --- |
| E1 | -32 / 254 / H4 | -6 / 917 / H6 | H89 -58 dB, ring +13 | H120 -22 dB, ring +0 |
| G1 | -28 / 288 / H4 | -6 / 928 / H5 | H72 -50 dB, ring +3 | H101 -22 dB, ring +2 |
| C2 | -19 / 402 / H4 | -6 / 917 / H4 | H55 -42 dB, ring +1 | H75 -25 dB, ring +2 |
| E2 | -22 / 417 / H4 | -5 / 1104 / H3 | H43 -47 dB, ring +1 | H60 -22 dB, ring +2 |
| G2 | -18 / 479 / H4 | -6 / 843 / H3 | H37 -40 dB, ring +2 | H50 -24 dB, ring +4 |
| C3 | -12 / 650 / H4 | -5 / 1092 / H2 | H28 -32 dB, ring +3 | H38 -20 dB, ring +5 |

### horn (GM 60, `brass.section`)

| Note | Gervill | Monk | Gervill breath band (H, vs loudest, ring) | Monk breath band |
| --- | --- | --- | --- | --- |
| C3 | -40 / 191 / H1 | -6 / 1438 / H6 | H31 -78 dB, ring +10 | H37 -21 dB, ring +6 |
| E3 | -33 / 245 / H1 | -6 / 1491 / H5 | H22 -69 dB, ring -1 | H23 -19 dB, ring +6 |
| G3 | -27 / 287 / H1 | -6 / 1448 / H4 | H20 -59 dB, ring +4 | H25 -19 dB, ring +9 |
| C4 | -15 / 404 / H1 | -6 / 1430 / H3 | H14 -48 dB, ring -1 | H19 -22 dB, ring +11 |
| E4 | -14 / 498 / H1 | -2 / 2433 / H9 | H11 -35 dB, ring +5 | H15 -7 dB, ring +15 |
| G4 | -10 / 590 / H1 | -15 / 925 / H2 | H9 -29 dB, ring +3 | H10 -27 dB, ring +14 |
| C5 | -14 / 794 / H1 | -4 / 1761 / H2 | H7 -34 dB, ring -1 | H7 -8 dB, ring +9 |

### section (GM 61, `brass.section`)

| Note | Gervill | Monk | Gervill breath band (H, vs loudest, ring) | Monk breath band |
| --- | --- | --- | --- | --- |
| G3 | -9 / 918 / H5 | -7 / 1249 / H4 | H18 -25 dB, ring +5 | H25 -22 dB, ring +8 |
| C4 | -5 / 1254 / H5 | -8 / 1176 / H3 | H18 -25 dB, ring +4 | H19 -23 dB, ring +11 |
| E4 | -2 / 1548 / H5 | -2 / 2532 / H9 | H11 -12 dB, ring +3 | H15 -7 dB, ring +17 |
| G4 | -2 / 1857 / H5 | -15 / 941 / H2 | H11 -12 dB, ring +3 | H10 -28 dB, ring +15 |
| C5 | -2 / 1545 / H3 | -3 / 1926 / H2 | H8 -17 dB, ring +4 | H7 -7 dB, ring +8 |
| E5 | -2 / 1950 / H3 | -15 / 1231 / H2 | H6 -15 dB, ring +1 | H6 -21 dB, ring +7 |

Means over the notes:

| Instrument | Profile | Above 1.5 kHz, Gervill / monk (dB) | Centroid, Gervill / monk (Hz) |
| --- | --- | --- | --- |
| trumpet | trumpet | -6.2 / -4.7 | 1372 / 1897 |
| tenor | sax.tenor | -6.5 / -5.2 | 1099 / 1385 |
| alto | sax.alto | -4.5 / -6.3 | 1434 / 1701 |
| trombone | trombone | -9.0 / -4.8 | 948 / 1612 |
| tuba | tuba | -21.8 / -5.4 | 415 / 967 |
| horn | brass.section | -21.9 / -6.4 | 430 / 1561 |
| section | brass.section | -3.7 / -8.4 | 1512 / 1509 |

## 3. Trumpet onsets (trumpet.mid, sung as written)

The first 80 ms of each note (10 ms frames) against its body (150-250 ms in). Level: loudest frame, dB. Flare: largest rise of any bin up to 3.5 kHz within 40 dB of the body's loudest. Breath: 3.5-5.5 kHz band energy, onset peak against body. Whistle: the breath band's strongest bin minus the frame's strongest bin (dB; nearer 0 = a high partial as loud as the note), onset peak and body mean. Medians / worst over 37 notes.

| Variant | Level | Flare | Breath rise | Whistle onset | Whistle body |
| --- | --- | --- | --- | --- | --- |
| Gervill | +1.6 / +1.9 | +22.3 / +27.5 | +9.2 / +10.6 | -17.8 / +0.0 | -24.2 / -12.8 |
| now | +2.0 / +5.9 | +15.3 / +31.4 | +2.1 / +4.2 | -9.6 / +0.0 | -11.5 / -2.5 |
| breath 0.45 | +2.0 / +6.0 | +15.3 / +31.4 | +2.3 / +4.6 | -12.3 / -3.7 | -16.0 / -6.8 |
| breath 0.3 | +2.0 / +6.0 | +15.3 / +31.4 | +2.2 / +4.3 | -15.2 / -7.5 | -19.2 / -10.3 |
| breath 0.3, burst 0.6 | +2.0 / +6.0 | +15.3 / +31.4 | +2.5 / +5.4 | -13.4 / -6.4 | -19.2 / -10.3 |
| no breath | +2.0 / +6.0 | +15.3 / +31.4 | +2.0 / +4.9 | -26.4 / -16.9 | -28.9 / -18.8 |
| F3 off | +1.8 / +4.9 | +15.4 / +31.4 | +2.2 / +4.2 | -5.8 / +0.0 | -10.1 / -0.2 |

Per note for A4 and E5 (whistle onset / body, dB):

| Note (time) | Gervill | now | breath 0.45 | breath 0.3 | breath 0.3, burst 0.6 | no breath | F3 off |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E5 (1.1 s) | -13 / -15 | -6 / -11 | -8 / -15 | -13 / -19 | -10 / -19 | -34 / -40 | -6 / -11 |
| E5 (1.7 s) | -13 / -15 | -10 / -12 | -13 / -17 | -18 / -20 | -14 / -20 | -33 / -38 | -10 / -12 |
| A4 (2.9 s) | -20 / -28 | -13 / -20 | -15 / -25 | -20 / -27 | -16 / -27 | -26 / -32 | -13 / -20 |
| A4 (4.1 s) | -20 / -28 | -12 / -16 | -16 / -21 | -20 / -24 | -20 / -24 | -29 / -33 | -12 / -16 |
| A4 (5.6 s) | -20 / -28 | -12 / -15 | -16 / -20 | -20 / -23 | -20 / -23 | -28 / -33 | -12 / -15 |
| A4 (6.5 s) | -20 / -28 | -16 / -17 | -18 / -21 | -23 / -25 | -19 / -25 | -26 / -33 | -16 / -17 |
| E5 (7.7 s) | -12 / -15 | -10 / -11 | -12 / -15 | -17 / -19 | -13 / -19 | -37 / -40 | -10 / -11 |
| E5 (10.1 s) | -13 / -15 | -6 / -12 | -8 / -17 | -13 / -20 | -10 / -20 | -34 / -38 | -6 / -12 |
| E5 (10.4 s) | -13 / -16 | -6 / -12 | -8 / -16 | -13 / -20 | -9 / -20 | -35 / -39 | -6 / -12 |
| E5 (10.7 s) | -13 / -16 | -6 / -10 | -8 / -15 | -13 / -18 | -9 / -18 | -34 / -41 | -6 / -10 |
| A4 (12.5 s) | -20 / -28 | -16 / -15 | -20 / -20 | -23 / -23 | -22 / -23 | -31 / -33 | -16 / -15 |
| E5 (13.4 s) | -13 / -15 | -6 / -10 | -8 / -15 | -13 / -18 | -10 / -18 | -35 / -41 | -6 / -10 |
| A4 (13.7 s) | -16 / -28 | -16 / -17 | -18 / -21 | -22 / -25 | -19 / -25 | -25 / -32 | -16 / -17 |
| A4 (15.2 s) | -20 / -28 | -16 / -17 | -19 / -21 | -23 / -24 | -20 / -24 | -29 / -33 | -16 / -17 |

## 4. Tenor sax brightness (sax.mid)

The whole line's spectrum in octave bands, dB of the total, and its centroid. Gervill's tenor first; 'diff' rows are the monk minus Gervill (positive = more energy there than Gervill).

| Variant | 0-200 | 200-400 | 400-800 | 800-1600 | 1600-3200 | 3200-6400 | 6400- | Centroid (Hz) | Above 1.6 kHz vs Gervill (dB) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gervill | -18 | -9 | -4 | -6 | -7 | -12 | -27 | 1185 | 0 |
| now | -7 | +4 | +0 | -13 | +1 | -4 | -28 | 998 | -0.3 |
| like c04 (4a) | -13 | -5 | +1 | -0 | +1 | -2 | -28 | 1410 | +0.4 |
| steady u | -5 | +6 | -2 | -21 | -1 | -4 | -28 | 725 | -1.5 |
| steady oo | -6 | +5 | -1 | -17 | +0 | -4 | -28 | 952 | -0.3 |
| F3 off | -6 | +5 | +1 | -12 | -41 | -3 | -28 | 608 | -8.4 |
| F3 x0.6 | -7 | +4 | +0 | -1 | -8 | -4 | -28 | 792 | -6.4 |
| breath 0.3 | -7 | +5 | +0 | -13 | +1 | -10 | -28 | 921 | -0.6 |
| size 0.25 | -6 | +6 | -1 | -16 | +0 | -4 | -28 | 882 | -0.7 |
| steady u, F3 off | -4 | +7 | -1 | -20 | -43 | -4 | -28 | 479 | -9.3 |
| u>o, F3 off, breath 0.3 | -6 | +6 | +1 | -12 | -44 | -9 | -28 | 500 | -14.3 |
| steady u, F3 x0.6, breath 0.3 | -5 | +6 | -2 | -1 | -24 | -10 | -28 | 553 | -15.6 |

(Every variant row is the difference from Gervill's row above.)

## 5. Level against Gervill

Each line as the router sings it (one monk, CC7 100, gain 1) against Gervill's instrument on the same notes (BS.1770 integrated loudness).

| Line | Profile | Gervill (LUFS) | Monk (LUFS) | Monk vs Gervill (dB) |
| --- | --- | --- | --- | --- |
| trumpet.mid (GM 56) | trumpet | -21.4 | -22.3 | -0.9 |
| sax.mid (GM 66) | sax.tenor | -19.0 | -23.6 | -4.6 |
| alto.mid (GM 65) | sax.alto | -22.6 | -21.9 | +0.7 |
| trombone.mid (GM 57) | trombone | -26.8 | -26.1 | +0.7 |
| tuba.mid (GM 58) | tuba | -28.3 | -28.5 | -0.1 |
| horn.mid (GM 60) | brass.section | -20.7 | -22.7 | -2.0 |
| trumpet.mid (GM 61) | brass.section | -24.0 | -21.8 | +2.2 |

## 6. Candidates on held notes

As section 2. Per cell: above 1.5 kHz (dB of total) / centroid (Hz) / the breath band's ring (dB over its neighbours). Last row: means.

### trumpet (`trumpet`)

| Note | Gervill | now | breath 0.45 | breath 0.3 | no breath |
| --- | --- | --- | --- | --- | --- |
| E4 | -9 / 960 / +0 | -2 / 2342 / +10 | -3 / 2211 / +10 | -3 / 2166 / +10 | -3 / 2126 / +3 |
| G4 | -9 / 909 / +0 | -9 / 1176 / +12 | -9 / 1111 / +12 | -9 / 1090 / +11 | -10 / 1070 / +2 |
| A4 | -10 / 1016 / +0 | -6 / 1713 / +19 | -6 / 1666 / +19 | -7 / 1650 / +19 | -7 / 1637 / -2 |
| C5 | -6 / 1218 / -1 | -1 / 2571 / +3 | -1 / 2396 / +1 | -1 / 2330 / -0 | -2 / 2265 / -6 |
| E5 | -5 / 1651 / -0 | -10 / 1284 / +1 | -12 / 1176 / -1 | -12 / 1139 / -3 | -13 / 1104 / -11 |
| G5 | -0 / 1950 / -2 | -6 / 1184 / -4 | -6 / 1131 / -6 | -6 / 1113 / -8 | -6 / 1097 / -17 |
| C6 | -3 / 1957 / -1 | -1 / 2998 / +21 | -1 / 2920 / +20 | -1 / 2893 / +19 | -1 / 2867 / -11 |
| mean | -6.0 / 1380 / -1 | -5.0 / 1895 / +9 | -5.4 / 1802 / +8 | -5.6 / 1769 / +7 | -5.8 / 1738 / -6 |

### tenor (`sax.tenor`)

| Note | Gervill | now | F3 x0.6 | F3 x0.6, breath 0.3 | F3 off, breath 0.3 |
| --- | --- | --- | --- | --- | --- |
| A2 | -13 / 583 / +10 | -7 / 1036 / +4 | -8 / 820 / +4 | -8 / 751 / +4 | -21 / 583 / +4 |
| C3 | -8 / 714 / +11 | -6 / 1193 / +5 | -6 / 921 / +5 | -7 / 831 / +5 | -20 / 616 / +5 |
| E3 | -6 / 913 / +8 | -3 / 1724 / +3 | -3 / 1272 / +3 | -4 / 1127 / +3 | -15 / 704 / +3 |
| G3 | -7 / 881 / +6 | -7 / 1057 / +5 | -7 / 872 / +5 | -7 / 801 / +5 | -21 / 609 / +5 |
| A3 | -7 / 997 / +3 | -7 / 921 / +7 | -10 / 653 / +7 | -10 / 589 / +7 | -22 / 485 / +7 |
| C4 | -7 / 1192 / +3 | -6 / 1317 / +7 | -5 / 1107 / +7 | -5 / 1031 / +7 | -20 / 770 / +7 |
| D4 | -5 / 1443 / +1 | -1 / 2259 / +8 | -5 / 1451 / +8 | -7 / 1067 / +8 | -12 / 834 / +8 |
| E4 | -3 / 1656 / -2 | -2 / 2033 / +11 | -2 / 1400 / +11 | -2 / 1280 / +11 | -15 / 652 / +11 |
| G4 | -3 / 1510 / +6 | -8 / 924 / +13 | -7 / 808 / +14 | -7 / 781 / +14 | -25 / 580 / +14 |
| mean | -6.5 / 1099 / +5 | -5.2 / 1385 / +7 | -5.8 / 1034 / +7 | -6.3 / 918 / +7 | -19.0 / 648 / +7 |

### trombone (`trombone`)

| Note | Gervill | now | F3 x0.6 | F3 off | F3 off, breath 0.3 |
| --- | --- | --- | --- | --- | --- |
| E2 | -12 / 749 / +0 | -6 / 1379 / +3 | -6 / 1137 / +3 | -12 / 1001 / +3 | -20 / 803 / +3 |
| G2 | -10 / 889 / +0 | -6 / 1358 / +3 | -6 / 1105 / +3 | -12 / 974 / +3 | -20 / 789 / +3 |
| C3 | -8 / 963 / +0 | -3 / 1889 / +3 | -4 / 1452 / +3 | -8 / 1367 / +3 | -16 / 939 / +3 |
| E3 | -10 / 864 / +1 | -5 / 1579 / +5 | -5 / 1304 / +5 | -11 / 1194 / +5 | -19 / 980 / +5 |
| G3 | -7 / 1031 / +2 | -5 / 1536 / +6 | -5 / 1291 / +6 | -11 / 1166 / +6 | -19 / 931 / +6 |
| C4 | -8 / 955 / -1 | -7 / 1368 / +7 | -6 / 1210 / +7 | -14 / 1095 / +7 | -21 / 975 / +7 |
| E4 | -6 / 1187 / +1 | -2 / 2174 / +10 | -2 / 1546 / +10 | -8 / 1445 / +10 | -15 / 931 / +10 |
| mean | -9.0 / 948 / +1 | -4.8 / 1612 / +5 | -4.9 / 1292 / +5 | -10.9 / 1177 / +5 | -18.4 / 907 / +5 |

### tuba (`tuba`)

| Note | Gervill | now | F3 off | F3 off, breath 0.3 | F3 off, F2 x0.7, breath 0.3 |
| --- | --- | --- | --- | --- | --- |
| E1 | -32 / 254 / +13 | -6 / 917 / +0 | -12 / 632 / +0 | -19 / 400 / +0 | -19 / 348 / +0 |
| G1 | -28 / 288 / +3 | -6 / 928 / +2 | -12 / 638 / +2 | -19 / 407 / +2 | -19 / 353 / +2 |
| C2 | -19 / 402 / +1 | -6 / 917 / +2 | -12 / 627 / +2 | -20 / 410 / +2 | -20 / 355 / +2 |
| E2 | -22 / 417 / +1 | -5 / 1104 / +2 | -11 / 742 / +2 | -18 / 443 / +2 | -18 / 380 / +2 |
| G2 | -18 / 479 / +2 | -6 / 843 / +4 | -12 / 588 / +4 | -20 / 391 / +4 | -21 / 365 / +4 |
| C3 | -12 / 650 / +3 | -5 / 1092 / +5 | -10 / 764 / +5 | -18 / 459 / +5 | -20 / 381 / +5 |
| mean | -21.8 / 415 / +4 | -5.4 / 967 / +2 | -11.4 / 665 / +2 | -19.1 / 418 / +2 | -19.8 / 364 / +2 |

### horn (`brass.section`)

| Note | Gervill | now | F3 off | F3 off, breath 0.3 | o, F3 off, breath 0.3 |
| --- | --- | --- | --- | --- | --- |
| C3 | -40 / 191 / +10 | -6 / 1438 / +6 | -13 / 1058 / +6 | -21 / 908 / +6 | -22 / 481 / +6 |
| E3 | -33 / 245 / -1 | -6 / 1491 / +6 | -11 / 1136 / +6 | -19 / 918 / +6 | -16 / 635 / +6 |
| G3 | -27 / 287 / +4 | -6 / 1448 / +9 | -13 / 1029 / +9 | -20 / 863 / +9 | -21 / 631 / +9 |
| C4 | -15 / 404 / -1 | -6 / 1430 / +11 | -15 / 932 / +11 | -22 / 828 / +11 | -20 / 776 / +11 |
| E4 | -14 / 498 / +5 | -2 / 2433 / +15 | -5 / 2010 / +15 | -12 / 1192 / +15 | -13 / 772 / +15 |
| G4 | -10 / 590 / +3 | -15 / 925 / +14 | -19 / 888 / +14 | -25 / 856 / +14 | -20 / 704 / +14 |
| C5 | -14 / 794 / -1 | -4 / 1761 / +9 | -6 / 1610 / +20 | -9 / 1065 / +20 | -31 / 530 / +20 |
| mean | -21.9 / 430 / +3 | -6.4 / 1561 / +10 | -11.7 / 1238 / +11 | -18.2 / 947 / +11 | -20.4 / 647 / +12 |

