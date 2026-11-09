"""Note-to-note transition in the DSP with everything else steady: does the new
note sound at its pitch from the first grain?"""
import pathlib, sys
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dl
OUT = pathlib.Path(__file__).parent / "transition"
OUT.mkdir(exist_ok=True)
HEAD = "bendrange 12\ncc 7 127\nset echo_amount 0\nset glide 0\nset vibrato 0\nset breath 0.5\nset voice 0.75\nset vowel 0.2\nset gain 1\n"
def case(a, b, gap_ms, gain_dip=None):
    s = HEAD + f"wait 100\non {a} 100\nwait 300\n"
    if gain_dip is not None:
        s += f"set gain {gain_dip}\n"
    if gap_ms >= 0:
        s += f"off {a}\n" + (f"wait {gap_ms}\n" if gap_ms else "") + f"on {b} 100\n"
    else:
        s += f"on {b} 100\nwait {-gap_ms}\noff {a}\n"
    s += "wait 400\noff %d\nwait 100\n" % b
    return s
for name, args in [("flute_cut", (93, 96, 0)), ("flute_gap30", (93, 96, 30)), ("flute_legato", (93, 96, -5)),
                   ("flute_cut_dip", (93, 96, 0, 0.2)), ("bass_cut", (45, 48, 0)), ("mid_cut", (69, 72, 0))]:
    x = dl.render(case(*args))
    dl.write_wav(OUT / f"{name}.wav", x)
    t1 = 0.4 + max(0, args[2]) / 1000 if args[2] >= 0 else 0.4
    m = dl.mono(x)
    hi = args[1] - 12
    fmin = 0.8 * 440 * 2 ** ((min(args[0], args[1]) - 12 - 69) / 12) / 2
    tt, f0, ap = dl.yin(m, t1 - 0.03, t1 + 0.1, fmin=max(30, fmin), fmax=2500, win=0.02 if hi < 50 else 0.008, hop=0.002)
    print(name, np.round(dl.hz_to_note(f0) - hi, 1)[::2].tolist())
    dl.spectrogram_png(x, OUT / f"{name}.png", t1 - 0.04, t1 + 0.12, fmax=5000, win=0.008, title=name, marks=[t1])
