# Phase 4c piano set: levels

Written by `make_4c_piano.py`. Loudness by ITU-R BS.1770 (gated, LUFS).

## chords/

Gervill: -22.1 LUFS, active RMS -25.0 dB.

| Clip | Natural loudness (LUFS) | Gain to Gervill (LUFS / active RMS, dB) | Peak after |
| --- | --- | --- | --- |
| now | -24.6 | +2.6 / +4.9 | -7.1 dBFS |
| locked | -24.9 | +2.8 / +5.1 | -6.9 dBFS |
| locked_long | -21.7 | -0.4 / +1.8 | -8.4 dBFS |

## lines/

Gervill: -24.7 LUFS, active RMS -28.1 dB.

| Clip | Natural loudness (LUFS) | Gain to Gervill (LUFS / active RMS, dB) | Peak after |
| --- | --- | --- | --- |
| now | -27.3 | +2.6 / +4.6 | -11.1 dBFS |
| long | -25.2 | +0.5 / +2.3 | -12.9 dBFS |
| long_open | -25.2 | +0.5 / +2.3 | -12.9 dBFS |
| long_e | -24.4 | -0.3 / +1.3 | -12.3 dBFS |
| long_big | -25.0 | +0.3 / +2.4 | -14.2 dBFS |

## band/

Gervill: the full band -17.9 LUFS, its piano alone -22.1 LUFS, the band without piano -19.8 LUFS. Live mix: the band without piano 6 dB down (D36) plus the helper at its own level (CC7 100, velocities from the file, gain 1), then the whole mix at the full band's loudness.

| Clip | Monks alone (LUFS) | Monks vs Gervill's piano (dB) | Live mix peak before matching | Mix gain |
| --- | --- | --- | --- | --- |
| now_4 | -24.6 | -2.6 | -6.3 dBFS | +4.6 dB |
| cand_4 | -21.7 | +0.4 | -6.0 dBFS | +2.5 dB |
| cand_6 | -21.3 | +0.7 | -5.3 dBFS | +2.2 dB |

