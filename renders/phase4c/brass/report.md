# Phase 4c brass round 1: levels and bands

Written by `make_4c_brass.py`. Loudness by ITU-R BS.1770 (gated, LUFS); bands in dB of each clip's total energy.

## trumpet/

Gervill: -21.4 LUFS; 800-1600 Hz -2.0 dB, above 1.6 kHz -7.7 dB, 3.5-5.5 kHz -20.5 dB of the total.

| Clip | Natural loudness (LUFS) | vs Gervill (dB) | 800-1600 Hz | Above 1.6 kHz | 3.5-5.5 kHz | Peak after matching |
| --- | --- | --- | --- | --- | --- | --- |
| now | -22.3 | -0.9 | -2.6 | -5.8 | -13.8 | -12.1 dBFS |
| breath045 | -22.5 | -1.1 | -2.5 | -6.2 | -17.9 | -11.9 dBFS |
| breath03 | -22.6 | -1.1 | -2.5 | -6.3 | -21.1 | -11.8 dBFS |
| breath03_puff | -22.6 | -1.1 | -2.5 | -6.3 | -21.0 | -11.8 dBFS |
| nobreath | -22.6 | -1.2 | -2.4 | -6.5 | -33.8 | -11.7 dBFS |

## sax/

Gervill: -19.0 LUFS; 800-1600 Hz -6.4 dB, above 1.6 kHz -6.0 dB, 3.5-5.5 kHz -13.2 dB of the total.

| Clip | Natural loudness (LUFS) | vs Gervill (dB) | 800-1600 Hz | Above 1.6 kHz | 3.5-5.5 kHz | Peak after matching |
| --- | --- | --- | --- | --- | --- | --- |
| now | -23.6 | -4.6 | -19.4 | -6.3 | -15.4 | -9.7 dBFS |
| f3low | -24.1 | -5.1 | -7.2 | -12.4 | -15.5 | -9.3 dBFS |
| f3low_b03 | -24.3 | -5.3 | -7.1 | -14.4 | -21.4 | -9.2 dBFS |
| f3off_b03 | -25.7 | -6.7 | -18.3 | -20.3 | -20.4 | -8.6 dBFS |
| f3low_b03_fix | -24.2 | -5.2 | -7.1 | -14.3 | -21.4 | -9.5 dBFS |

## band/

Gervill: the full band -17.3 LUFS, its trumpet alone -21.4, its tenor alone -19.2, the band without them -20.5 LUFS. Live mix: the band without horns 6 dB down (D36) plus each helper at its own level (CC7 100, the file's velocities, gain 1), then the whole mix at the full band's loudness.

| Clip | Trumpet monk (LUFS, vs Gervill's) | Sax monk (LUFS, vs Gervill's) | Mix gain |
| --- | --- | --- | --- |
| now | -21.7 (-0.3) | -23.9 (-4.7) | +3.8 dB |
| darker | -21.9 (-0.5) | -23.9 (-4.7) | +3.9 dB |
| darkest | -21.7 (-0.3) | -23.9 (-4.7) | +3.8 dB |

