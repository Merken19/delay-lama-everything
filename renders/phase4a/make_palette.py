"""Phase 4a palette demo: writes DelayLamaVoice scripts and renders them.

Protocol 0 has no articulator yet, so this script draws the curves itself:
every 5 ms it sends `set vowel`, `set breath`, `set gain` (level), `bend`
(pitch offset) and `set vibrato`. The `sing()` function is a rough prototype
of the phase 4b articulator; its parameter names follow docs/IMITATION.md.

Run from anywhere:  python make_palette.py
Output: scripts/*.txt, *.wav and LISTENING.md next to this file.
"""

import math
import pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXE = ROOT / "external/delalalalay-lama/Windows/build/Release/DelayLamaVoice.exe"
TICK = 5.0  # ms between control updates

# Move shapes, x in 0..1 -> 0..1 (docs/IMITATION.md, "Curves").
SHAPES = {
    "step": lambda x: 1.0 if x >= 1 else 0.0,  # hold, then jump at the end
    "linear": lambda x: x,
    "exp": lambda x: (1 - math.exp(-3 * x)) / (1 - math.exp(-3)),
    "ease": lambda x: x * x * (3 - 2 * x),
    "late": lambda x: x * x,
}


def move(a, b, t, duration, shape="linear"):
    if duration <= 0 or t >= duration:
        return b
    if t <= 0:
        return a
    return a + (b - a) * SHAPES[shape](t / duration)


def decay_to(peak, floor, t, duration):
    """Exponential fall from peak toward floor, 95% of the way at `duration`."""
    if duration <= 0:
        return peak
    return floor + (peak - floor) * math.exp(-3 * max(0.0, t) / duration)


def bend_value(semitones):
    st = max(-12.0, min(12.0, semitones))
    return int(round(8192 + st / 12 * (8191 if st >= 0 else 8192)))


class Take:
    """One WAV: timed commands plus labelled sections for the listening guide."""

    def __init__(self, name, title, monks=1):
        self.name, self.title, self.monks = name, title, monks
        self.events = []
        self.sections = []
        self.last = {}
        self.t = 0.0

    def at(self, t, line):
        self.events.append((t, len(self.events), line))

    def value(self, t, key, v):
        """set/bend at time t, skipping repeats so scripts stay readable."""
        if key == "bend":
            v = bend_value(v)
            if self.last.get(key) != v:
                self.at(t, f"bend {v}")
        else:
            v = round(v, 4)
            if self.last.get(key) != v:
                self.at(t, f"set {key} {v:g}")
        self.last[key] = v

    def section(self, label, t=None):
        self.sections.append((self.t if t is None else t, label))

    def curve(self, key, t0, a, b, duration, shape="linear"):
        n = max(1, int(round(duration / TICK)))
        for i in range(n + 1):
            self.value(t0 + i * duration / n, key, move(a, b, i * duration / n, duration, shape))

    def note(self, t, note, length, velocity=100):
        self.at(t, f"on {note} {velocity}")
        self.at(t + length, f"off {note}")

    def script(self):
        lines = [f"# {self.title}", "# Written by renders/phase4a/make_palette.py; do not edit."]
        now = 0.0
        for t, _, line in sorted(self.events):
            if t > now + 1e-9:
                lines.append(f"wait {t - now:.3f}".rstrip("0").rstrip("."))
                now = t
            lines.append(line)
        return "\n".join(lines) + "\n"


def header(take, echo=0.0):
    """Neutral start: no echo, no DSP glide, floor vibrato only, full CC7."""
    for line in ["hello 0", "bendrange 12", "cc 7 127", f"set echo_amount {echo:g}",
                 "set glide 0", "set vibrato 0", "set vibrato_rate 0.5", "set breath 0.5",
                 "set voice 0.5", "set vowel 0.5", "set gain 1"]:
        take.at(-1000.0, line)  # before any note's presets (they start 15 ms early)
    take.last = {"vowel": 0.5, "breath": 0.5, "gain": 1.0, "voice": 0.5,
                 "vibrato": 0.0, "vibrato_rate": 0.5, "bend": 8192}


# --- Prototype articulator ---------------------------------------------------

BASE = dict(
    vowel=0.5, onset_vowel=None, onset_time=0.0, onset_curve="ease",
    breath=0.4, burst=None, burst_time=0.0,
    scoop=0.0, scoop_time=0.0, scoop_curve="exp",
    attack=0.0, peak=1.0, decay=0.0, sustain=1.0,
    drift_vowel=None, drift_time=0.0, max_len=0.0,
    vib=0.0, vib_rate=0.5, vib_delay=0.0, vib_fade=0.0,
    end_vowel=None, end_time=0.0, release=20.0, fall=0.0, fall_time=0.0,
    voice=0.5, dip_time=0.0, dip_level=0.25, dip_vowel=None,
    glide_time=60.0, glide_curve="ease",
)


def sing(take, notes, profile, level=1.0):
    """Sing a line: notes = [(start_ms, note, length_ms, mode[, overrides])].

    mode: "new" (from silence), "re" (re-articulate: dip, then a new onset),
    "legato" (no new onset; the pitch glides from the previous note).
    note may be a tuple for a block chord (every monk gets the same curves).
    overrides: profile keys for this note only, plus "level" (a gain factor).
    """
    base = dict(BASE, **profile)
    prev = None  # (chord, vowel, level) at the hand-over
    last_stop = -math.inf  # when the previous note's curves end
    for k, entry in enumerate(notes):
        t0, note, length, mode = entry[:4]
        over = dict(entry[4]) if len(entry) > 4 else {}
        lvl = level * over.pop("level", 1.0)
        p = dict(base, **over)
        chord = note if isinstance(note, tuple) else (note,)
        next_t0 = notes[k + 1][0] if k + 1 < len(notes) else math.inf
        end_t = t0 + (min(length, p["max_len"]) if p["max_len"] else length)
        stop_t = min(next_t0, end_t + 1.5 * p["release"])
        legato = (mode == "legato" and prev is not None and len(chord) == 1
                  and prev[0] != chord)
        re = mode in ("re", "legato") and prev is not None and not legato
        onset_v = p["onset_vowel"] if p["onset_vowel"] is not None else p["vowel"]
        if re and p["dip_vowel"] is not None:
            onset_v = p["dip_vowel"]
        dip = p["dip_time"] if re else 0.0
        state = {}

        def at(tau):
            t = t0 + tau
            # vowel
            if legato:
                v = move(prev[1], p["vowel"], tau, p["glide_time"], "ease")
            else:
                v = move(onset_v, p["vowel"], tau - dip, p["onset_time"], p["onset_curve"])
            if p["drift_vowel"] is not None and tau > p["onset_time"] + dip:
                v = move(p["vowel"], p["drift_vowel"], tau - p["onset_time"] - dip,
                         p["drift_time"], "exp")
            # level
            ta = tau - dip
            if legato:
                lev = move(prev[2], p["peak"] * p["sustain"] if p["decay"] else p["peak"], tau, 40)
            elif tau < dip:
                lev = p["dip_level"] * p["peak"]
            else:
                start = p["dip_level"] * p["peak"] if re else 0.0
                lev = move(start, p["peak"], ta, p["attack"]) if p["attack"] else p["peak"]
                if p["decay"] and ta > p["attack"]:
                    lev = decay_to(p["peak"], p["peak"] * p["sustain"], ta - p["attack"], p["decay"])
            # pitch offset
            off = 0.0
            if legato:
                off = move(prev[0][0] - chord[0], 0.0, tau, p["glide_time"], p["glide_curve"])
            elif p["scoop"]:
                off = p["scoop"] * (1 - SHAPES[p["scoop_curve"]](min(1.0, max(0.0, ta) / p["scoop_time"])))
            # ending
            if t >= end_t:
                te = t - end_t
                if "end" not in state:
                    state["end"] = (v, lev)
                v0, l0 = state["end"]
                if p["end_vowel"] is not None:
                    v = move(v0, p["end_vowel"], te, p["end_time"] or p["release"], "ease")
                else:
                    v = v0
                lev = l0 * math.exp(-3 * te / max(p["release"], 1.0))
                if p["fall"]:
                    off += p["fall"] * SHAPES["late"](min(1.0, te / p["fall_time"]))
            # breath and vibrato
            b = p["breath"]
            if p["burst"] is not None and not legato:
                b = move(p["burst"], p["breath"], ta, p["burst_time"], "exp") if ta >= 0 else p["breath"] * 0.5
            vib = 0.0 if tau < p["vib_delay"] else move(0.0, p["vib"], tau - p["vib_delay"], p["vib_fade"])
            return v, lev, off, b, vib

        v, lev, off, b, vib = at(0.0)
        # A silent monk gets its values 15 ms early (the level smoother settles);
        # while the previous note's tail still runs, they go with the note-on,
        # or that tail's last ticks would overwrite them.
        pre = t0 if (legato or re or last_stop > t0 - 15.0) else t0 - 15.0
        for key, val in (("voice", p["voice"]), ("vibrato_rate", p["vib_rate"]),
                         ("vowel", v), ("breath", b), ("vibrato", vib),
                         ("gain", lev * lvl), ("bend", off)):  # bend too: a slur starts from the old pitch
            take.value(pre, key, val)
        if prev is not None and not legato:
            for n in prev[0]:  # before the new on: a repeated pitch must not cancel it
                take.at(t0, f"off {n}")
        for n in chord:
            take.at(t0, f"on {n} 100")
        if legato:
            take.at(t0 + 1.0, f"off {prev[0][0]}")  # overlap: the monk is stolen, no new onset
        tau = TICK
        while t0 + tau < stop_t:
            v, lev, off, b, vib = at(tau)
            for key, val in (("vowel", v), ("breath", b), ("vibrato", vib),
                             ("gain", lev * lvl), ("bend", off)):
                take.value(t0 + tau, key, val)
            tau += TICK
        prev = (chord, v, lev)
        last_stop = stop_t
        if next_t0 == math.inf or notes[k + 1][3] == "new":
            for n in chord:
                take.at(stop_t, f"off {n}")
            prev = None
    # Back to the neutral state, so plain notes after a phrase sound as in header().
    for key, val in (("gain", 1.0), ("bend", 0.0), ("vowel", 0.5), ("breath", 0.5),
                     ("voice", 0.5), ("vibrato", 0.0), ("vibrato_rate", 0.5)):
        take.value(stop_t + 5.0, key, val)
    take.t = max(take.t, stop_t)


def gap(take, ms=450.0):
    take.t += ms


# --- The takes -----------------------------------------------------------------

def p01_vowels():
    take = Take("p01_vowels", "Vowel axis: nine positions, then u-o-a-e-i at four pitches")
    header(take)
    take.section("Nine positions 0, .125 ... 1 on note 69 (sounds A3, 220 Hz): u, (ʊ), o, (ɔ), a, (æ), e, (ɪ), i")
    for i in range(9):
        take.value(take.t - 15, "vowel", i / 8)
        take.note(take.t, 69, 650)
        take.t += 650 + 250
    for note, label in ((57, "110 Hz"), (69, "220 Hz"), (81, "440 Hz"), (93, "880 Hz")):
        gap(take, 300)
        take.section(f"u-o-a-e-i on note {note} (sounds {label})")
        for v in (0.0, 0.25, 0.5, 0.75, 1.0):
            take.value(take.t - 15, "vowel", v)
            take.note(take.t, note, 450)
            take.t += 450 + 150
    return take


def p02_sweeps():
    take = Take("p02_sweeps", "Vowel moves drawn at 5 ms steps, note 69 (220 Hz)")
    header(take)

    def held(label, a, b, duration, shape, before=250, after=350):
        take.section(label)
        take.value(take.t - 15, "vowel", a)
        take.note(take.t, 69, before + duration + after)
        take.curve("vowel", take.t + before, a, b, duration, shape)
        take.t += before + duration + after + 350

    held("Slow sweep u -> i (1 s, linear): passes o, a, e on the way", 0.0, 1.0, 1000, "linear")
    held("Slow sweep i -> u (1 s, linear): ee-eh-ah-oh-oo", 1.0, 0.0, 1000, "linear")
    for ms in (400, 200, 100, 50):
        held(f"'yeow' i -> u in {ms} ms (ease)", 1.0, 0.0, ms, "ease", 200, 300)
    for ms in (200, 100, 50, 25):
        held(f"'wa' u -> a in {ms} ms (ease)", 0.0, 0.5, ms, "ease", 120, 300)
    held("Jump u -> i (step): what an unsmoothed change sounds like", 0.0, 1.0, 0, "step")
    held("'ai' a -> i in 150 ms (ease)", 0.5, 1.0, 150, "ease")
    held("'ya' i -> a in 80 ms (exp)", 1.0, 0.5, 80, "exp", 60, 400)
    return take


def p03_breath():
    take = Take("p03_breath", "Breath (aspiration) levels and bursts")
    header(take)
    take.section("Breath 0, .25, .5 (default), .75, 1 on vowel a, note 69 (220 Hz)")
    for b in (0.0, 0.25, 0.5, 0.75, 1.0):
        take.value(take.t - 15, "breath", b)
        take.note(take.t, 69, 700)
        take.t += 700 + 250
    gap(take, 200)
    take.section("Breath 1 on notes 45, 69, 93 (55, 220, 880 Hz): the pings follow the pitch")
    for note in (45, 69, 93):
        take.note(take.t, note, 800)
        take.t += 800 + 250
    gap(take, 200)
    take.section("Onset bursts on 'a': none, then breath 1 -> 0.3 over 15, 40, 100 ms")
    for ms in (0, 15, 40, 100):
        take.value(take.t - 15, "breath", 1.0 if ms else 0.3)
        take.note(take.t, 69, 500)
        if ms:
            take.curve("breath", take.t, 1.0, 0.3, ms, "exp")
        take.t += 500 + 300
    return take


def p04_voice():
    take = Take("p04_voice", "Voice size (formant scale 0.75-1.25)")
    header(take)
    take.section("Voice 0, .25, .5 (default), .75, 1 on vowel a, note 69 (220 Hz)")
    for v in (0.0, 0.25, 0.5, 0.75, 1.0):
        take.value(take.t - 15, "voice", v)
        take.note(take.t, 69, 700)
        take.t += 700 + 250
    gap(take, 200)
    take.section("'Tuba': voice 0, vowel 0.1, note 50 (73 Hz)")
    take.value(take.t - 15, "voice", 0.0)
    take.value(take.t - 15, "vowel", 0.1)
    take.note(take.t, 50, 1000)
    take.t += 1300
    take.section("'Piccolo': voice 1, vowel 1, note 93 (880 Hz)")
    take.value(take.t - 15, "voice", 1.0)
    take.value(take.t - 15, "vowel", 1.0)
    take.note(take.t, 93, 1000)
    take.t += 1300
    return take


def p05_range():
    take = Take("p05_range", "Range: arpeggios per octave, then one bass riff at four octaves")
    header(take)
    take.value(-1, "vowel", 0.4)
    for c in (24, 36, 48, 60, 72, 84, 96):
        hz = 440 * 2 ** ((c - 12 - 69) / 12)
        take.section(f"C-E-G-C from note {c} (sounds from {hz:.0f} Hz)")
        for n in (c, c + 4, c + 7, c + 12):
            take.note(take.t, n, 230)
            take.t += 250
        take.t += 350
    take.section("Note 108 (sounds C7, 2093 Hz)")
    take.note(take.t, 108, 600)
    take.t += 1000
    riff = [(0, 0), (1, 0), (2, 3), (3, 5), (4, 7), (5, 5), (6, 3), (7, 0)]
    dum = dict(vowel=0.12, onset_vowel=0.55, onset_time=25, attack=0, decay=260, sustain=0.35,
               end_vowel=0.0, release=50, breath=0.25, voice=0.35)
    for shift, label in ((0, "as written (E1 = note 28): the DSP sounds it at E0, 21 Hz"),
                         (12, "+1 octave (note 40): sounds E1, 41 Hz"),
                         (24, "+2 octaves (note 52): sounds E2, 82 Hz"),
                         (36, "+3 octaves (note 64): sounds E3, 165 Hz")):
        take.section(f"Bass riff 'dum' {label}")
        notes = [(take.t + i * 260, 28 + shift + st, 200, "new") for i, st in riff]
        sing(take, notes, dum)
        take.t += 500
    return take


def p06_vibrato():
    take = Take("p06_vibrato", "Vibrato: the floor that never stops, depth, rate, delayed vibrato")
    header(take)
    for depth, rate, label in ((0.0, 0.5, "depth 0, rate 0.5: the floor (about ±0.2 st, 5-7 Hz)"),
                               (0.0, 0.0, "depth 0, rate 0: floor slowed to about 1.5 Hz"),
                               (0.0, 1.0, "depth 0, rate 1: floor at about 24 Hz, a growl"),
                               (0.15, 0.5, "depth 0.15 (helper default)"),
                               (0.4, 0.5, "depth 0.4"),
                               (1.0, 0.5, "depth 1 (±1.2 st)"),
                               (0.3, 0.3, "depth 0.3, rate 0.3 (slow, about 3 Hz)"),
                               (0.3, 0.7, "depth 0.3, rate 0.7 (fast, about 11 Hz)")):
        take.section(label)
        take.value(take.t - 15, "vibrato", depth)
        take.value(take.t - 15, "vibrato_rate", rate)
        take.note(take.t, 69, 1500)
        take.t += 1500 + 350
    take.section("Delayed vibrato: straight for 400 ms, then fades in to 0.4 over 500 ms")
    take.value(take.t - 15, "vibrato", 0.0)
    take.value(take.t - 15, "vibrato_rate", 0.5)
    take.note(take.t, 69, 1800)
    take.curve("vibrato", take.t + 400, 0.0, 0.4, 500)
    take.t += 2200
    return take


def p07_glide():
    take = Take("p07_glide", "Legato: the DSP's constant-rate glide vs. glides drawn in a fixed time")
    header(take)
    line = [69, 76, 74, 72, 69]

    def dsp_glide(glide, label):
        take.section(label)
        take.at(take.t - 15, f"set glide {glide}")
        t = take.t
        for i, n in enumerate(line):
            take.at(t + i * 400, f"on {n} 100")
            if i:
                take.at(t + i * 400 + 1, f"off {line[i - 1]}")
        take.at(t + len(line) * 400, f"off {line[-1]}")
        take.at(t + len(line) * 400 + 5, "set glide 0")
        take.t = t + len(line) * 400 + 500

    dsp_glide(0.5, "DSP glide 0.5 (helper default): 23.5 st/s, a fifth takes 0.3 s")
    dsp_glide(0.15, "DSP glide 0.15: 75 st/s")
    for ms, shape in ((40, "ease"), (90, "ease"), (200, "ease"), (90, "exp")):
        take.section(f"Drawn glide, {ms} ms ({shape}), any interval")
        notes = [(take.t + i * 400, n, 400, "new" if i == 0 else "legato") for i, n in enumerate(line)]
        sing(take, notes, dict(glide_time=ms, glide_curve=shape, release=30))
        take.t += 500
    run = [69, 71, 73, 74, 76, 78, 80, 81, 80, 78, 76, 74, 73, 71, 69]
    take.section("Fast run (110 ms notes) with DSP glide 0.5: the notes smear")
    take.at(take.t - 15, "set glide 0.5")
    for i, n in enumerate(run):
        take.at(take.t + i * 110, f"on {n} 100")
        if i:
            take.at(take.t + i * 110 + 1, f"off {run[i - 1]}")
    take.at(take.t + len(run) * 110, f"off {run[-1]}")
    take.at(take.t + len(run) * 110 + 5, "set glide 0")
    take.t += len(run) * 110 + 500
    take.section("Same run, drawn 30 ms glides")
    notes = [(take.t + i * 110, n, 110, "new" if i == 0 else "legato") for i, n in enumerate(run)]
    sing(take, notes, dict(glide_time=30, release=30))
    take.t += 500
    take.section("Same run re-articulated ('da-da-da': 20 ms dip to i-ish)")
    notes = [(take.t + i * 110, n, 110, "new" if i == 0 else "re") for i, n in enumerate(run)]
    sing(take, notes, dict(dip_time=20, dip_level=0.2, dip_vowel=0.8, onset_time=25, release=30))
    take.t += 500
    return take


def p08_level():
    take = Take("p08_level", "Level shapes: decays, attacks, and repeated notes")
    header(take)
    for decay, label in ((120, "Pluck: exponential decay, 95% gone in 120 ms"),
                         (400, "Pluck: exponential decay, 400 ms"),
                         (1200, "Pluck: exponential decay, 1.2 s")):
        take.section(label)
        sing(take, [(take.t, 69, decay * 1.4, "new")], dict(decay=decay, sustain=0.0, release=40))
        take.t += 400
    take.section("Same 1.2 s fall, but linear (the DSP's own ADSR decay)")
    take.at(take.t - 15, "set decay 1.2")
    take.at(take.t - 15, "set sustain 0")
    take.note(take.t, 69, 1500)
    take.at(take.t + 1505, "set decay 0")
    take.at(take.t + 1505, "set sustain 1")
    take.t += 1900
    for attack in (0, 30, 120, 400):
        take.section(f"Attack {attack} ms")
        sing(take, [(take.t, 69, attack + 500, "new")], dict(attack=attack, release=60))
        take.t += 350
    rep = lambda: [(take.t + i * 180, 69, 180, "new" if i == 0 else "re") for i in range(6)]
    take.section("Six repeated notes, plain (what the helper does today)")
    t = take.t
    for i in range(6):
        take.note(t + i * 180, 69, 179.5)
    take.t = t + 6 * 180 + 450
    for label, prof in (("dip only (30 ms to 20%)", dict(dip_time=30, dip_level=0.2)),
                        ("dip + dark vowel: 'ba-ba'", dict(dip_time=30, dip_level=0.2, dip_vowel=0.0, onset_time=40)),
                        ("dip + bright vowel: 'da-da'", dict(dip_time=25, dip_level=0.15, dip_vowel=0.8, onset_time=30)),
                        ("dip + breath burst: 'ta-ta'", dict(dip_time=25, dip_level=0.1, dip_vowel=0.75, onset_time=25,
                                                             burst=1.0, burst_time=30))):
        take.section(f"Six repeated notes, {label}")
        sing(take, rep(), prof)
        take.t += 450
    return take


def p09_space():
    take = Take("p09_space", "Echo amount and unison on a short phrase")
    header(take)
    phrase = [(0, 62, 300), (300, 64, 300), (600, 67, 450), (1200, 69, 300), (1500, 67, 300), (1800, 64, 700)]

    def play(label, setup, teardown):
        take.section(label)
        for line in setup:
            take.at(take.t - 15, line)
        for start, n, length in phrase:
            take.note(take.t + start, n, length)
        take.t += 2500
        for line in teardown:
            take.at(take.t - 20, line)
        take.t += 1200

    for echo in (0.0, 0.2, 0.42, 0.8):
        label = {0.42: " (helper default)", 0.8: " (Delay Lama's Rabten preset)"}.get(echo, "")
        play(f"Echo amount {echo}{label}", [f"set echo_amount {echo}"], ["set echo_amount 0"])
    play("Unison 3 voices, detune 12 cents, spread 0.15, no echo",
         ["set unison_voices 3", "set unison_detune 12", "set unison_spread 0.15"],
         ["set unison_voices 1", "set unison_detune 0", "set unison_spread 0"])
    return take


# First-guess family gestures (hypotheses for the tuning sessions).
GESTURES = [
    ("Bass 'dum' (note 52, sounds E2)", 52, 500,
     dict(vowel=0.12, onset_vowel=0.55, onset_time=25, decay=300, sustain=0.3, end_vowel=0.0,
          release=60, breath=0.25, voice=0.35)),
    ("Piano 'ding' (note 72, sounds C4)", 72, 1100,
     dict(vowel=0.95, onset_vowel=0.6, onset_time=20, decay=900, sustain=0.0, drift_vowel=0.8,
          drift_time=800, end_vowel=0.1, release=120, breath=0.3, burst=0.8, burst_time=15,
          vib_rate=0.0, voice=0.6)),
    ("Clean guitar 'dang' (note 67, sounds G3)", 67, 1100,
     dict(vowel=0.58, onset_vowel=0.7, onset_time=30, decay=1300, sustain=0.1, drift_vowel=0.4,
          drift_time=1000, end_vowel=0.15, release=140, breath=0.3, burst=0.9, burst_time=25,
          vib_rate=0.0)),
    ("Overdrive guitar 'nyeow' (note 64, sounds E3)", 64, 1300,
     dict(vowel=0.5, onset_vowel=1.0, onset_time=140, scoop=-1.0, scoop_time=90, attack=15,
          decay=1500, sustain=0.75, vib=0.4, vib_rate=0.55, vib_delay=450, vib_fade=300,
          end_vowel=0.05, end_time=250, release=280, fall=-0.7, fall_time=300, breath=0.6,
          voice=0.45)),
    ("Same 'nyeow' with the vibrato floor at 24 Hz as a growl", 64, 1300,
     dict(vowel=0.5, onset_vowel=1.0, onset_time=140, scoop=-1.0, scoop_time=90, attack=15,
          decay=1500, sustain=0.75, vib=0.0, vib_rate=1.0, end_vowel=0.05, end_time=250,
          release=280, fall=-0.7, fall_time=300, breath=0.7, voice=0.45)),
    ("Trombone 'bwaa' (note 58, sounds Bb2)", 58, 1000,
     dict(vowel=0.55, onset_vowel=0.0, onset_time=70, burst=0.9, burst_time=40, breath=0.4,
          scoop=-1.5, scoop_time=120, attack=25, vib=0.25, vib_delay=400, vib_fade=300,
          end_vowel=0.3, release=120, voice=0.35)),
    ("Trumpet 'taa' with a fall-off (note 70, sounds Bb3)", 70, 800,
     dict(vowel=0.6, onset_vowel=0.75, onset_time=30, burst=1.0, burst_time=30, breath=0.45,
          scoop=-0.5, scoop_time=50, attack=8, peak=1.25, decay=200, sustain=0.75, vib=0.2,
          vib_delay=500, end_vowel=0.4, release=200, fall=-2.5, fall_time=300, voice=0.6)),
    ("Muted trumpet 'wah' (note 70)", 70, 700,
     dict(vowel=0.55, onset_vowel=0.0, onset_time=180, breath=0.6, attack=20, vib=0.15,
          vib_delay=300, end_vowel=0.0, end_time=200, release=200, voice=0.6)),
    ("Sax 'doo-ah' (note 67, sounds G3)", 67, 1300,
     dict(vowel=0.12, onset_vowel=0.6, onset_time=40, drift_vowel=0.5, drift_time=500, breath=0.7,
          scoop=-0.8, scoop_time=100, attack=20, vib=0.35, vib_rate=0.55, vib_delay=350,
          vib_fade=250, end_vowel=0.2, release=120)),
    ("Flute 'hoo' (note 79, sounds G4)", 79, 1200,
     dict(vowel=0.2, onset_vowel=0.12, onset_time=60, breath=0.9, burst=1.0, burst_time=60,
          attack=40, vib=0.15, vib_delay=250, vib_fade=300, release=100, voice=0.75)),
    ("Violin 'neee' (note 76, sounds E4)", 76, 1400,
     dict(vowel=0.92, onset_vowel=0.85, onset_time=80, breath=0.35, attack=120, vib=0.3,
          vib_rate=0.6, vib_delay=300, vib_fade=400, release=200, voice=0.7)),
    ("Cello 'mmmooo' (note 60, sounds C3)", 60, 1500,
     dict(vowel=0.25, onset_vowel=0.0, onset_time=250, breath=0.35, attack=150, vib=0.3,
          vib_rate=0.45, vib_delay=350, vib_fade=400, end_vowel=0.05, release=250, voice=0.3)),
    ("Organ 'ooo' (note 69): straight on and off, slow floor", 69, 1000,
     dict(vowel=0.3, vib_rate=0.0, attack=5, release=15, breath=0.2)),
    ("Glockenspiel 'ting' (note 84, sounds C5)", 84, 700,
     dict(vowel=1.0, onset_vowel=0.85, onset_time=10, decay=450, sustain=0.0, drift_vowel=0.9,
          drift_time=400, burst=1.0, burst_time=10, breath=0.4, vib_rate=0.0, voice=1.0)),
    ("Marimba 'bonk' (note 72, sounds C4)", 72, 400,
     dict(vowel=0.25, onset_vowel=0.45, onset_time=20, decay=200, sustain=0.0, end_vowel=0.0,
          release=40, breath=0.3, vib_rate=0.0, voice=0.45)),
]


def g01_gestures():
    take = Take("g01_gestures", "First-guess syllables per family, one note each")
    header(take)
    for label, note, length, prof in GESTURES:
        take.section(label)
        sing(take, [(take.t, note, length, "new")], prof)
        take.t += 500
    take.section("Muted guitar 'chugga': 8 notes, 60 ms each, 125 ms apart (note 52)")
    notes = [(take.t + i * 125, 52, 125, "new" if i == 0 else "re") for i in range(8)]
    sing(take, notes, dict(vowel=0.3, onset_vowel=0.7, onset_time=15, burst=1.0, burst_time=20,
                           breath=0.5, max_len=60, decay=50, sustain=0.3, end_vowel=0.1,
                           release=20, dip_time=0, voice=0.4))
    take.t += 500
    return take


def g02_phrases():
    take = Take("g02_phrases", "One melody, four ways; one bass line, two ways")
    header(take)
    mel = [(0, 62, 300), (300, 64, 300), (600, 67, 450), (1200, 69, 300), (1500, 67, 300),
           (1800, 64, 600), (2600, 62, 300), (2900, 64, 300), (3200, 62, 1200)]

    def phrase(modes):
        out = []
        for i, (s, n, l) in enumerate(mel):
            prev_end = mel[i - 1][0] + mel[i - 1][2] if i else None
            mode = "new" if i == 0 or s > prev_end else modes
            out.append((take.t + s, n, l, mode))
        return out

    take.section("Plain: one vowel, no articulation (today's helper)")
    for s, n, l in mel:
        take.note(take.t + s, n, l - 0.5)
    take.t += 4400 + 500
    take.section("'doo-doo' (soft, re-articulated, dark)")
    sing(take, phrase("re"), dict(vowel=0.15, onset_vowel=0.6, onset_time=35, dip_time=25,
                                  dip_level=0.25, attack=10, release=80, vib=0.15, vib_delay=300,
                                  vib_fade=200, end_vowel=0.05))
    take.t += 500
    take.section("Legato 'aah' with 80 ms drawn glides (synth lead / violin slur)")
    sing(take, phrase("legato"), dict(vowel=0.6, glide_time=80, attack=40, release=150, vib=0.25,
                                      vib_delay=250, vib_fade=200, voice=0.6))
    take.t += 500
    take.section("Trumpet-like 'taa-daa' (tongued: dip, breath burst, small scoop)")
    sing(take, phrase("re"), dict(vowel=0.6, onset_vowel=0.75, onset_time=25, dip_time=20,
                                  dip_level=0.1, burst=1.0, burst_time=30, breath=0.45, scoop=-0.4,
                                  scoop_time=40, attack=6, peak=1.15, decay=150, sustain=0.8,
                                  vib=0.2, vib_delay=350, release=100, voice=0.6))
    take.t += 700
    bass = [(i * 250, n, 230) for i, n in enumerate([52, 52, 55, 57, 52, 52, 50, 47])]
    take.section("Bass line, plain (note 52 = sounds E2)")
    for s, n, l in bass:
        take.note(take.t + s, n, l)
    take.t += 2000 + 500
    take.section("Bass line 'dum dum doon'")
    notes = [(take.t + s, n, l, "new") for s, n, l in bass]
    sing(take, notes, dict(vowel=0.12, onset_vowel=0.55, onset_time=25, decay=300, sustain=0.3,
                           end_vowel=0.0, release=50, breath=0.25, voice=0.35))
    take.t += 500
    return take


def mmss(ms):
    return f"{int(ms // 60000)}:{(ms % 60000) / 1000:04.1f}"


def main():
    takes = [p01_vowels(), p02_sweeps(), p03_breath(), p04_voice(), p05_range(), p06_vibrato(),
             p07_glide(), p08_level(), p09_space(), g01_gestures(), g02_phrases()]
    (HERE / "scripts").mkdir(exist_ok=True)
    guide = ["# Phase 4a palette demo: listening guide", "",
             "Rendered by `make_palette.py` with `DelayLamaVoice.exe --render` (protocol 0,",
             "one monk, 48 kHz). The curves are drawn by the script at 5 ms steps, since the",
             "helper has no articulator yet. Notes sound an octave below their MIDI number.",
             "Echo is off except in p09.", ""]
    for take in takes:
        script = HERE / "scripts" / f"{take.name}.txt"
        wav = HERE / f"{take.name}.wav"
        script.write_text(take.script(), encoding="utf-8")
        subprocess.run([str(EXE), "--render", str(script), str(wav), "--monks", str(take.monks),
                        "--tail", "800"], check=True)
        guide += [f"## {take.name}.wav", "", take.title, ""]
        guide += [f"- {mmss(t)}  {label}" for t, label in take.sections]
        guide.append("")
    (HERE / "LISTENING.md").write_text("\n".join(guide), encoding="utf-8")


if __name__ == "__main__":
    main()
