import pathlib, sys
import numpy as np
H = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(H), str(H.parent), str(H.parents[1] / "phase4a" / "ab"), str(H.parents[2] / "tools" / "profiles")]
sys.dont_write_bytecode = True; sys.argv = [sys.argv[0]]
import dl, make_ab, make_4b
def run(name, profile, notes, extra):
    m = dl.mono(dl.render(make_4b.script(notes, profile, extra), tail=800))
    t, f, ap = dl.yin(m, 0.5, 9.0, fmin=150, fmax=2000, win=0.012, hop=0.005)
    bad = []
    for a, hz, q in zip(t, f, ap):
        started = [n for s, n, d in notes if s / 1000 <= a]
        if not started or q > 0.2: continue
        hi = max(started[-2:])
        d = dl.hz_to_note(hz) - hi
        if 0.5 < d < 5: bad.append((round(a, 2), round(d, 2)))
    print(f"{name:28s} frames above both notes by >0.5 st: {len(bad)} {bad[:8]}")
V = make_ab.melody(12)
run("violin", "strings.violin", V, [])
run("violin vibrato straight", "strings.violin", V, [("vibrato.depth", 0.2)])
run("violin pitch_track 0", "strings.violin", V, [("nucleus.pitch_track", 0)])
run("violin mode 3", "strings.violin", V, [("phrase.mode", 3)])
