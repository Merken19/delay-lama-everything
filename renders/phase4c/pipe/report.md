# Phase 4c pipe round 1: levels

Written by `make_4c_pipe.py`. Loudness by ITU-R BS.1770 (gated, LUFS).

## melody/

Gervill: -17.2 LUFS; energy above 1.5 kHz -6.2 dB of the total. The monk sings -12 st (D37).

| Clip | Natural loudness (LUFS) | vs Gervill (dB) | Above 1.5 kHz (dB of total) | Peak after matching |
| --- | --- | --- | --- | --- |
| now | -23.2 | -5.9 | -2.7 | -8.8 dBFS |
| nof3 | -27.7 | -10.5 | -9.9 | -4.9 dBFS |
| nof3_dark | -28.6 | -11.3 | -17.2 | -4.5 dBFS |
| nof3_legato | -27.4 | -10.2 | -9.9 | -4.9 dBFS |
| nof3_dark_legato | -28.3 | -11.1 | -17.4 | -4.6 dBFS |

## band/

Gervill: the full band -15.2 LUFS, its flute alone -17.2 LUFS, the band without flute -19.2 LUFS. Live mix: the band without flute 6 dB down (D36) plus the helper at its own level (CC7 100, the file's velocities, gain 1), then the whole mix at the full band's loudness.

| Clip | Monk alone (LUFS) | Monk vs Gervill's flute (dB) | Mix gain |
| --- | --- | --- | --- |
| now | -23.2 | -5.9 | +5.9 dB |
| nof3_legato | -23.1 | -5.9 | +5.9 dB |
| nof3_dark_legato | -23.2 | -6.0 | +6.0 dB |

