"""Phase 4c brass and sax: measurements before the ear check (IMITATION.md 16:
trumpet c03 "very good; an occasional very high pitch", sax c04 "too bright
for a tenor sax"). Writes measure/measurements.md.

1. Profiles as resolved, and the fold (D37) of each line.
2. Held notes: each profile's sounding notes held 1.5 s against Gervill's
   instrument at the same pitch (0.7-1.45 s after the onset): energy above
   1.5 kHz (dB of the total), spectral centroid, the loudest harmonic, and the
   strongest harmonic in the breath band (3.5-5.5 kHz, where the DSP's two
   aspiration partials sit, 3.80 and 4.95 kHz): its level against the loudest
   harmonic and how far it stands above its two neighbours ("ring").
3. Trumpet onsets in trumpet.mid: the first 80 ms of each note against its
   body (level, harmonic flare up to 3.5 kHz, breath-band energy, and the
   breath band's strongest bin against the strongest bin), for the profile and
   for less breath, no burst and F3 off; then each A4 and E5 note.
4. Sax brightness: sax.mid's spectrum in octave bands against Gervill's tenor,
   for the profile now, phase 4a's c04 settings and darker candidates
   (steady "u"/"oo", F3 off or lowered, less breath, a bigger voice).
5. Level: each line's monk against Gervill's instrument (BS.1770).

Run: py renders/phase4c/brass/measure_4c_brass.py
"""

import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import brass_phrases as bp  # noqa: E402
from brass_phrases import dl, pp, expand  # noqa: E402

sys.path.insert(0, str(HERE.parent / "piano"))
from make_4c_piano import lufs  # noqa: E402

SR = dl.SR
OUT = HERE / "measure"
TMP = bp.TMP
NAMES = "C C# D D# E F F# G G# A A# B".split()
HOLD, GAP = 1500.0, 700.0
BREATH_LO, BREATH_HI = 3500.0, 5500.0


def name(n):
    return f"{NAMES[n % 12]}{n // 12 - 1}"


def hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def spectrum(x, t0, t1):
    seg = dl.mono(x)[int(t0 * SR):int(t1 * SR)]
    p = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2
    return p, np.fft.rfftfreq(len(seg), 1 / SR)


def harmonics(p, f, f0):
    """Power (dB) of each harmonic below 12 kHz: the peak within +-3% (and
    under half the spacing), so lead vibrato's +-2% stays inside."""
    out = []
    k = 1
    while k * f0 < 12000:
        half = min(0.03 * k * f0, 0.45 * f0)
        band = np.abs(f - k * f0) < half
        out.append(10 * np.log10(p[band].max() + 1e-20))
        k += 1
    return np.array(out)


def note_stats(x, t0, t1, f0):
    p, f = spectrum(x, t0, t1)
    h = harmonics(p, f, f0)
    bright = 10 * np.log10(p[f > 1500].sum() / p.sum())
    centroid = (p * f).sum() / p.sum()
    ks = [k for k in range(len(h)) if BREATH_LO <= (k + 1) * f0 <= BREATH_HI]
    if ks:
        kb = max(ks, key=lambda k: h[k])
        neighbours = [h[j] for j in (kb - 1, kb + 1) if 0 <= j < len(h)]
        ring = h[kb] - np.mean(neighbours)
        breath = (kb + 1, h[kb] - h.max(), ring)
    else:
        breath = (0, -99.0, 0.0)
    return {"bright": bright, "centroid": centroid, "loudest": 1 + int(np.argmax(h)), "breath": breath}


def held_phrase(notes):
    return pp.Phrase("held", [(bp.START + k * (HOLD + GAP), n, HOLD, 96) for k, n in enumerate(notes)])


def gervill_held(program, notes, tag):
    phrase = held_phrase(notes)
    mid = TMP / f"held_{tag}.mid"
    pp.write_mid(mid, {0: (program, phrase.notes, [])})
    return pp.gervill(mid, TMP / f"held_{tag}.wav")


def monk_held(profile_name, notes, extra=()):
    phrase = held_phrase(notes)
    return dl.render(bp.script(phrase, bp.profile(profile_name), extra, shift=0), monks=1, tail=300)


def per_note(x, notes):
    out = []
    for k, n in enumerate(notes):
        t0 = (bp.START + k * (HOLD + GAP)) / 1000
        out.append(note_stats(x, t0 + 0.7, t0 + 1.45, hz(n)))
    return out


# --- 1. Profiles and fold -----------------------------------------------------------

def profiles_section(report):
    data = expand.load()
    report += ["## 1. Profiles and fold", "",
               "As `expand.resolve` gives them (the router sends these). GM programs 0-based: "
               "trumpet and muted trumpet (56, 59) map to `trumpet`, horn, brass section and synth "
               "brass (60-63) to `brass.section`, soprano and alto (64-65) to `sax.alto`, tenor and "
               "baritone (66-67) to `sax.tenor`.", ""]
    for prof in ("trumpet", "trombone", "tuba", "brass.section", "sax.alto", "sax.tenor"):
        report.append(f"- `{prof}`: `{json.dumps(expand.resolve(data, prof), separators=(',', ':'))}`")
    alto, tenor = expand.resolve(data, "sax.alto"), expand.resolve(data, "sax.tenor")
    diffs = []
    for section in ("onset", "ending"):
        for key, value in alto[section].items():
            if tenor[section].get(key) != value:
                diffs.append(f"{section}.{key} {value} -> {tenor[section].get(key)}")
    report += ["", "Note: `sax.tenor` extends `sax.alto` but its own syllable (\"d-u>o\") is merged "
               "after the parent's entry, so the syllable's defaults replace what the alto set: "
               + "; ".join(diffs) + ". IMITATION.md 15 gives every sax attack 20 and an \"o\" ending "
               "over 120 ms, so the tenor sings with a crisper attack and a 20 ms release by "
               "accident. Fix (when the profile changes): repeat those keys in `sax.tenor`.", "",
               "| Line | Profile | Written range (median) | range.shift |", "| --- | --- | --- | --- |"]
    for phrase, _, prof in bp.lines():
        ns = sorted(n for _, n, _, _ in phrase.notes)
        report.append(f"| {phrase.name}.mid | {prof} | {name(ns[0])}-{name(ns[-1])} ({name(ns[len(ns) // 2])}) "
                      f"| {bp.shift_of(phrase, bp.profile(prof)):+d} |")
    up = pp.Phrase("up", [(t, n + 2, d, v) for t, n, d, v in bp.trumpet().notes])
    report += ["", f"trumpet.mid sits right at the D37 ceiling (median C5 = `range.high` 72). The same "
               f"line a tone higher (median D5, a common trumpet lead) would be sung "
               f"{bp.shift_of(up, bp.profile('trumpet')):+d} st, an octave below what c03 sang as "
               "written and the user kept. A per-profile `range.high` (e.g. 76 for the trumpet) "
               "would keep trumpet leads as written; not tested here.", ""]


# --- 2. Held notes ------------------------------------------------------------------

HELD = [
    ("trumpet", "trumpet", [55, 60, 64, 67, 69, 72, 74, 76, 79, 81, 84]),
    ("tenor", "sax.tenor", [45, 48, 52, 55, 57, 60, 62, 64, 67]),
    ("alto", "sax.alto", [55, 60, 64, 67, 69, 72, 76]),
    ("trombone", "trombone", [40, 43, 48, 52, 55, 60, 64]),
    ("tuba", "tuba", [28, 31, 36, 40, 43, 48]),
    ("horn", "brass.section", [48, 52, 55, 60, 64, 67, 72]),
    ("section", "brass.section", [55, 60, 64, 67, 72, 76]),
]


def held_section(report):
    report += ["## 2. Held notes against Gervill", "",
               "Each note held 1.5 s at velocity 96, measured 0.7-1.45 s in (lead vibrato has "
               "reached its depth). Per cell: energy above 1.5 kHz in dB of the total / spectral "
               "centroid in Hz / loudest harmonic. 'Breath band': the strongest harmonic between "
               "3.5 and 5.5 kHz, its level against the note's loudest harmonic, and its ring "
               "(dB above the mean of its two neighbours; a smooth brass spectrum is near 0, a "
               "partial that whistles stands out).", ""]
    summary = []
    for tag, prof, notes in HELD:
        g = per_note(gervill_held(bp.PROGRAM[tag], notes, tag), notes)
        m = per_note(monk_held(prof, notes), notes)
        report += [f"### {tag} (GM {bp.PROGRAM[tag]}, `{prof}`)", "",
                   "| Note | Gervill | Monk | Gervill breath band (H, vs loudest, ring) | Monk breath band |",
                   "| --- | --- | --- | --- | --- |"]
        fmt = lambda s: f"{s['bright']:+.0f} / {s['centroid']:.0f} / H{s['loudest']}"
        fb = lambda s: "-" if not s["breath"][0] else \
            f"H{s['breath'][0]} {s['breath'][1]:+.0f} dB, ring {s['breath'][2]:+.0f}"
        for n, gs, ms in zip(notes, g, m):
            report.append(f"| {name(n)} | {fmt(gs)} | {fmt(ms)} | {fb(gs)} | {fb(ms)} |")
        report.append("")
        summary.append((tag, prof, np.mean([s["bright"] for s in g]), np.mean([s["bright"] for s in m]),
                        np.mean([s["centroid"] for s in g]), np.mean([s["centroid"] for s in m])))
    report += ["Means over the notes:", "",
               "| Instrument | Profile | Above 1.5 kHz, Gervill / monk (dB) | Centroid, Gervill / monk (Hz) |",
               "| --- | --- | --- | --- |"]
    for tag, prof, gb, mb, gc, mc in summary:
        report.append(f"| {tag} | {prof} | {gb:+.1f} / {mb:+.1f} | {gc:.0f} / {mc:.0f} |")
    report.append("")


# --- 3. Trumpet onsets --------------------------------------------------------------

def stft(x, t0, t1, win=0.010, hop=0.002):
    mono = dl.mono(x)
    n = int(win * SR)
    frames = [np.abs(np.fft.rfft(mono[a:a + n] * np.hanning(n), 4096)) ** 2
              for a in range(max(0, int(t0 * SR)), int(t1 * SR) - n, int(hop * SR))]
    return 10 * np.log10(np.array(frames) + 1e-20), np.fft.rfftfreq(4096, 1 / SR)


def onset_stats(x, phrase, shift=0):
    """Per note: level, flare, breath, whistle (onset max) and body whistle."""
    out = []
    for t, n, d, _ in phrase.notes:
        t0 = t / 1000
        dur = min(d, 600) / 1000
        if dur < 0.12:
            continue
        on, f = stft(x, t0, t0 + 0.08)
        ref = stft(x, t0 + min(0.15, dur - 0.1), t0 + min(0.25, dur))[0]
        low = f <= 3500
        hi = (f >= BREATH_LO) & (f <= BREATH_HI)
        tot = lambda s, m: 10 * np.log10((10 ** (s[:, m] / 10)).sum(axis=1))
        body = ref[:, low].max(axis=0)
        live = body > body.max() - 40
        whistle = lambda s: s[:, hi].max(axis=1) - s.max(axis=1)
        out.append({"note": n + shift, "t": t0,
                    "level": tot(on, low).max() - tot(ref, low).mean(),
                    "flare": (on[:, low].max(axis=0) - body)[live].max(),
                    "breath": tot(on, hi).max() - tot(ref, hi).mean(),
                    "whistle_on": whistle(on).max(), "whistle_body": whistle(ref).mean()})
    return out


TRUMPET_VARIANTS = [
    ("now", "the profile (breath 0.75, burst 0.6)", []),
    ("breath 0.45", "c03's breath (4a's 'taa': 0.45, burst 1.0 there)", [("body.breath", 0.45)]),
    ("breath 0.3", "", [("body.breath", 0.3), ("onset.burst", 0.3)]),
    ("breath 0.3, burst 0.6", "", [("body.breath", 0.3)]),
    ("no breath", "", [("body.breath", 0), ("onset.burst", 0)]),
    ("F3 off", "", [("voice.formant3", 0)]),
]


def trumpet_section(report):
    phrase = bp.trumpet()
    g = pp.gervill(HERE / "midi" / "trumpet.mid", TMP / "trumpet.wav")
    report += ["## 3. Trumpet onsets (trumpet.mid, sung as written)", "",
               "The first 80 ms of each note (10 ms frames) against its body (150-250 ms in). "
               "Level: loudest frame, dB. Flare: largest rise of any bin up to 3.5 kHz within "
               "40 dB of the body's loudest. Breath: 3.5-5.5 kHz band energy, onset peak against "
               "body. Whistle: the breath band's strongest bin minus the frame's strongest bin "
               "(dB; nearer 0 = a high partial as loud as the note), onset peak and body mean. "
               "Medians / worst over 37 notes.", "",
               "| Variant | Level | Flare | Breath rise | Whistle onset | Whistle body |",
               "| --- | --- | --- | --- | --- | --- |"]
    rows = {"Gervill": onset_stats(g, phrase)}
    for label, _, extra in TRUMPET_VARIANTS:
        x = dl.render(bp.script(phrase, bp.profile("trumpet"), extra), monks=1, tail=300)
        rows[label] = onset_stats(x, phrase)
    for label, st in rows.items():
        col = lambda k: np.array([s[k] for s in st])
        report.append(f"| {label} | {np.median(col('level')):+.1f} / {col('level').max():+.1f} | "
                      f"{np.median(col('flare')):+.1f} / {col('flare').max():+.1f} | "
                      f"{np.median(col('breath')):+.1f} / {col('breath').max():+.1f} | "
                      f"{np.median(col('whistle_on')):+.1f} / {col('whistle_on').max():+.1f} | "
                      f"{np.median(col('whistle_body')):+.1f} / {col('whistle_body').max():+.1f} |")
    report += ["", "Per note for A4 and E5 (whistle onset / body, dB):", "",
               "| Note (time) | Gervill | " + " | ".join(list(rows)[1:]) + " |",
               "| --- | --- |" + " --- |" * (len(rows) - 1)]
    for k, s in enumerate(rows["Gervill"]):
        if s["note"] not in (69, 76):
            continue
        cells = [f"{rows[lab][k]['whistle_on']:+.0f} / {rows[lab][k]['whistle_body']:+.0f}" for lab in rows]
        report.append(f"| {name(s['note'])} ({s['t']:.1f} s) | " + " | ".join(cells) + " |")
    report.append("")
    return rows


# --- 4. Sax brightness ------------------------------------------------------------------

OCTAVES = [(0, 200), (200, 400), (400, 800), (800, 1600), (1600, 3200), (3200, 6400), (6400, 24000)]

SAX_VARIANTS = [
    ("now", []),
    ("like c04 (4a)", [("nucleus.vowel", 0.12), ("body.vowel", 0.5), ("body.breath", 0.7),
                       ("voice.size", 0.5)]),
    ("steady u", [("body.vowel", -1)]),
    ("steady oo", [("nucleus.vowel", 0.12), ("body.vowel", -1)]),
    ("F3 off", [("voice.formant3", 0)]),
    ("F3 x0.6", [("voice.formant3", 0.6)]),
    ("breath 0.3", [("body.breath", 0.3)]),
    ("size 0.25", [("voice.size", 0.25)]),
    ("steady u, F3 off", [("body.vowel", -1), ("voice.formant3", 0)]),
    ("u>o, F3 off, breath 0.3", [("voice.formant3", 0), ("body.breath", 0.3)]),
    ("steady u, F3 x0.6, breath 0.3", [("body.vowel", -1), ("voice.formant3", 0.6),
                                        ("body.breath", 0.3)]),
]


def octave_db(x):
    p = np.abs(np.fft.rfft(dl.mono(x))) ** 2
    f = np.fft.rfftfreq(len(dl.mono(x)), 1 / SR)
    total = p.sum()
    return [10 * np.log10(p[(f >= lo) & (f < hi)].sum() / total + 1e-20) for lo, hi in OCTAVES], \
        (p * f).sum() / total


def sax_section(report):
    phrase = bp.sax()
    g = pp.gervill(HERE / "midi" / "sax.mid", TMP / "sax.wav")
    gb, gc = octave_db(g)
    report += ["## 4. Tenor sax brightness (sax.mid)", "",
               "The whole line's spectrum in octave bands, dB of the total, and its centroid. "
               "Gervill's tenor first; 'diff' rows are the monk minus Gervill (positive = more "
               "energy there than Gervill).", "",
               "| Variant | " + " | ".join(f"{lo}-{hi if hi < 24000 else ''}" for lo, hi in OCTAVES)
               + " | Centroid (Hz) | Above 1.6 kHz vs Gervill (dB) |",
               "| --- |" + " --- |" * (len(OCTAVES) + 2),
               "| Gervill | " + " | ".join(f"{v:+.0f}" for v in gb) + f" | {gc:.0f} | 0 |"]
    out = {}
    for label, extra in SAX_VARIANTS:
        x = dl.render(bp.script(phrase, bp.profile("sax.tenor"), extra), monks=1, tail=300)
        b, c = octave_db(x)
        hi_m = 10 * np.log10(sum(10 ** (v / 10) for v in b[4:]))
        hi_g = 10 * np.log10(sum(10 ** (v / 10) for v in gb[4:]))
        out[label] = (b, c, hi_m - hi_g)
        report.append(f"| {label} | " + " | ".join(f"{v - w:+.0f}" for v, w in zip(b, gb))
                      + f" | {c:.0f} | {hi_m - hi_g:+.1f} |")
    report += ["", "(Every variant row is the difference from Gervill's row above.)", ""]
    return out


# --- 5. Level -----------------------------------------------------------------------

def level_section(report):
    report += ["## 5. Level against Gervill", "",
               "Each line as the router sings it (one monk, CC7 100, gain 1) against Gervill's "
               "instrument on the same notes (BS.1770 integrated loudness).", "",
               "| Line | Profile | Gervill (LUFS) | Monk (LUFS) | Monk vs Gervill (dB) |",
               "| --- | --- | --- | --- | --- |"]
    for phrase, program, prof in bp.lines():
        mid = TMP / f"lvl_{phrase.name}_{program}.mid"
        pp.write_mid(mid, {0: (program, phrase.notes, [])})
        g = pp.gervill(mid, TMP / f"lvl_{phrase.name}_{program}.wav")
        sections = bp.profile(prof)
        m = dl.render(bp.script(phrase, sections), monks=1 if prof != "brass.section" else 1, tail=300)
        report.append(f"| {phrase.name}.mid (GM {program}) | {prof} | {lufs(g):.1f} | {lufs(m):.1f} | "
                      f"{lufs(m) - lufs(g):+.1f} |")
    report.append("")


# --- 6. Candidates on held notes ----------------------------------------------------

TENOR_FIX = [("onset.attack", 20), ("ending.release", 120), ("ending.vowel", 0.25)]
CANDIDATES = [
    ("trumpet", "trumpet", [64, 67, 69, 72, 76, 79, 84],
     [("now", []), ("breath 0.45", [("body.breath", 0.45), ("onset.burst", 0.45)]),
      ("breath 0.3", [("body.breath", 0.3), ("onset.burst", 0.3)]),
      ("no breath", [("body.breath", 0), ("onset.burst", 0)])]),
    ("tenor", "sax.tenor", [45, 48, 52, 55, 57, 60, 62, 64, 67],
     [("now", []), ("F3 x0.6", [("voice.formant3", 0.6)]),
      ("F3 x0.6, breath 0.3", [("voice.formant3", 0.6), ("body.breath", 0.3)]),
      ("F3 off, breath 0.3", [("voice.formant3", 0), ("body.breath", 0.3)])]),
    ("trombone", "trombone", [40, 43, 48, 52, 55, 60, 64],
     [("now", []), ("F3 x0.6", [("voice.formant3", 0.6)]), ("F3 off", [("voice.formant3", 0)]),
      ("F3 off, breath 0.3", [("voice.formant3", 0), ("body.breath", 0.3)])]),
    ("tuba", "tuba", [28, 31, 36, 40, 43, 48],
     [("now", []), ("F3 off", [("voice.formant3", 0)]),
      ("F3 off, breath 0.3", [("voice.formant3", 0), ("body.breath", 0.3)]),
      ("F3 off, F2 x0.7, breath 0.3", [("voice.formant3", 0), ("voice.formant2", 0.7),
                                       ("body.breath", 0.3)])]),
    ("horn", "brass.section", [48, 52, 55, 60, 64, 67, 72],
     [("now", []), ("F3 off", [("voice.formant3", 0)]),
      ("F3 off, breath 0.3", [("voice.formant3", 0), ("body.breath", 0.3)]),
      ("o, F3 off, breath 0.3", [("nucleus.vowel", 0.25), ("voice.formant3", 0), ("body.breath", 0.3)])]),
]


def candidates_section(report):
    report += ["## 6. Candidates on held notes", "",
               "As section 2. Per cell: above 1.5 kHz (dB of total) / centroid (Hz) / the breath "
               "band's ring (dB over its neighbours). Last row: means.", ""]
    for tag, prof, notes, variants in CANDIDATES:
        g = per_note(gervill_held(bp.PROGRAM[tag], notes, tag), notes)
        cols = [("Gervill", g)] + [(label, per_note(monk_held(prof, notes, extra), notes))
                                   for label, extra in variants]
        report += [f"### {tag} (`{prof}`)", "",
                   "| Note | " + " | ".join(c for c, _ in cols) + " |", "| --- |" + " --- |" * len(cols)]
        cell = lambda s: f"{s['bright']:+.0f} / {s['centroid']:.0f} / {s['breath'][2]:+.0f}"
        for k, n in enumerate(notes):
            report.append(f"| {name(n)} | " + " | ".join(cell(st[k]) for _, st in cols) + " |")
        mean = lambda st, key: np.mean([s[key] for s in st])
        report.append("| mean | " + " | ".join(
            f"{mean(st, 'bright'):+.1f} / {mean(st, 'centroid'):.0f} / "
            f"{np.mean([s['breath'][2] for s in st]):+.0f}" for _, st in cols) + " |")
        report.append("")


def main():
    OUT.mkdir(exist_ok=True)
    bp.use_exe_copy()
    bp.write_all_midi()
    report = ["# Phase 4c brass and sax: measurements", "",
              "Written by `measure_4c_brass.py` (DelayLamaVoice in profile mode, 48 kHz, a copy of "
              "the helper built with `voice.formant1-3`; Gervill with the JDK's soundbank).", ""]
    profiles_section(report)
    held_section(report)
    trumpet_section(report)
    sax_section(report)
    level_section(report)
    candidates_section(report)
    (OUT / "measurements.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
