import pathlib, sys
import numpy as np
H = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(H), str(H.parent), str(H.parents[1] / "phase4a" / "ab"), str(H.parents[2] / "tools" / "profiles")]
sys.dont_write_bytecode = True
sys.argv = [sys.argv[0]]
import dl, make_ab, make_4b
from check_4b import flare
def run(name, profile, notes, extra):
    x = dl.render(make_4b.script(notes, profile, extra), tail=800); m = dl.mono(x)
    fl = [flare(m, t / 1000, 440 * 2 ** ((n - 69) / 12)) for t, n, d in notes]
    t, f, ap = dl.yin(m, 0.5, 9.0, fmin=150, fmax=2000, win=0.012, hop=0.005)
    # pitch above the current note (target = latest note started)
    tgt = np.array([max([n for s, n, d in notes if s / 1000 <= a] or [0]) for a in t])
    dev = dl.hz_to_note(f) - tgt
    ok = (ap < 0.2) & (abs(dev) < 5)
    print(f"{name:34s} worst flare {max(fl):+5.1f} dB ({sum(x > 8 for x in fl)} >8), pitch frames >+0.5 st: {int(np.sum(ok & (dev > 0.5)))}")
V = make_ab.melody(12); G = make_ab.melody(-12)
run("violin", "strings.violin", V, [])
run("violin steady onset", "strings.violin", V, [("onset.vowel", -1)])
run("violin glide 0.15", "strings.violin", V, [("phrase.glide", 0.15)])
run("violin no pitch_track", "strings.violin", V, [("nucleus.pitch_track", 0)])
run("violin vowel 0.8 steady", "strings.violin", V, [("onset.vowel", -1), ("nucleus.vowel", 0.8), ("nucleus.pitch_track", 0)])
run("clean guitar", "guitar.clean", G, [])
run("clean guitar steady onset", "guitar.clean", G, [("onset.vowel", -1)])
run("clean guitar steady all", "guitar.clean", G, [("onset.vowel", -1), ("body.vowel", -1), ("ending.vowel", -1), ("phrase.dip_vowel", -1)])
