# Phase 4c piano round 2: levels

Written by `make_4c_piano_r2.py`. Loudness by ITU-R BS.1770 (gated, LUFS).

## band/

Gervill: the full band -17.9 LUFS, its piano alone -22.1 LUFS, the band without piano -19.8 LUFS. Live mix as in round 1: the band without piano 6 dB down (D36) plus the helper at its own level, then the whole mix at the full band's loudness. 4 monks.

| Clip | Monks alone (LUFS) | Monks vs Gervill's piano (dB) | Live mix peak before matching | Mix gain |
| --- | --- | --- | --- | --- |
| now | -24.6 | -2.6 | -6.3 dBFS | +4.6 dB |
| open | -24.6 | -2.6 | -6.3 dBFS | +4.6 dB |
| open_lock | -24.9 | -2.8 | -6.9 dBFS | +4.7 dB |
| open_long | -21.6 | +0.5 | -5.9 dBFS | +2.5 dB |
| open_lock_long | -21.7 | +0.4 | -6.0 dBFS | +2.5 dB |

## chords/

Gervill: -22.1 LUFS, active RMS -25.0 dB.

| Clip | Natural loudness (LUFS) | Gain to Gervill (LUFS / active RMS, dB) | Peak after |
| --- | --- | --- | --- |
| locked_long | -21.7 | -0.4 / +1.8 | -8.4 dBFS |
| locked_long_open | -21.7 | -0.4 / +1.8 | -8.4 dBFS |

