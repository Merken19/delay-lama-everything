"""Phase 4a A/B renders: the instrument as midis2jam2 plays it (Gervill, default
soundbank) against Delay Lama candidates (octave choices, velocity response),
alone and inside a small band.

Needs Java 17+ (GervillRender.java) and the phase 1 DelayLamaVoice.exe.
Run: python make_ab.py   Output: c*/ folders of WAVs, midi/, scripts/, AB_LISTENING.md
"""

import math
import pathlib
import shutil
import struct
import subprocess
import sys
import wave

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import make_palette as mp  # noqa: E402  (prototype articulator)

SR = 48000
BEAT = 600.0  # 100 bpm
START = 500.0
GAP_S = 1.2  # silence between sections in all.wav
JAVA = ["java", "--add-exports", "java.desktop/com.sun.media.sound=ALL-UNNAMED",
        str(HERE / "GervillRender.java")]

# --- The band piece (5 bars, A minor: Am F C G Am) ------------------------------

Q, E, H, DQ, W = BEAT, BEAT / 2, BEAT * 2, BEAT * 1.5, BEAT * 4
MELODY = [(69, E), (72, E), (76, Q), (76, E), (74, E), (72, Q),
          (69, DQ), (67, E), (65, Q), (69, Q),
          (67, E), (69, E), (72, E), (74, E), (76, H),
          (74, Q), (71, Q), (67, H),
          (69, W)]
CHORDS = [(57, 60, 64), (57, 60, 65), (55, 60, 64), (55, 59, 62), (57, 60, 64)]
ROOTS = [33, 29, 36, 31]
LEAD, BASS, PIANO, DRUMS = 0, 1, 2, 9


def timeline(durations, start=START):
    t, out = start, []
    for note, d in durations:
        out.append((t, note, d))
        t += d
    return out


def melody(transpose=0, legato_fill=False):
    """(start, note, length): 90% lengths, as a sequenced lead would be."""
    return [(t, n + transpose, d * 0.9) for t, n, d in timeline(MELODY)]


def bass_line():
    notes = []
    for bar, r in enumerate(ROOTS):
        t = START + bar * W
        for off, n, d in ((0, r, Q), (Q, r, E), (Q + E, r + 12, E), (H, r, Q), (H + Q, r + 7, Q)):
            notes.append((t + off, n, d * 0.85))
    notes.append((START + 4 * W, 33, W))
    return notes


def piano_chords():
    out = []
    for bar, chord in enumerate(CHORDS[:4]):
        for beat in range(4):
            out.append((START + bar * W + beat * Q, chord, Q * 0.75))
    out.append((START + 4 * W, CHORDS[4], W))
    return out


def drum_hits():
    hits = []
    for bar in range(4):
        t = START + bar * W
        for k in range(8):
            hits.append((t + k * E, 42, 70))
        for beat in (0, 2):
            hits.append((t + beat * Q, 36, 105))
        hits.append((t + 2.5 * Q, 36, 85))
        for beat in (1, 3):
            hits.append((t + beat * Q, 38, 95))
    hits += [(START + 4 * W, 36, 110), (START + 4 * W, 49, 100)]
    return hits


# --- MIDI files -------------------------------------------------------------------

def vlq(n):
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.insert(0, (n & 0x7F) | 0x80)
        n >>= 7
    return bytes(out)


def write_mid(path, parts):
    """parts: {channel: (program, [(start_ms, note_or_chord, length_ms, velocity)])}."""
    ticks = lambda ms: int(round(ms / BEAT * 480))
    tracks = [b"\x00\xff\x51\x03" + int(BEAT * 1000).to_bytes(3, "big") + b"\x00\xff\x2f\x00"]
    for channel, (program, notes) in sorted(parts.items()):
        events = [(0, 0, bytes([0xC0 | channel, program]))]
        for start, note, length, velocity in notes:
            for n in (note if isinstance(note, tuple) else (note,)):
                events.append((ticks(start), 1, bytes([0x90 | channel, n, velocity])))
                events.append((ticks(start + length), 0, bytes([0x80 | channel, n, 0])))
        events.sort(key=lambda ev: (ev[0], ev[1]))
        data, now = b"", 0
        for tick, _, msg in events:
            data += vlq(tick - now) + msg
            now = tick
        tracks.append(data + b"\x00\xff\x2f\x00")
    body = b"".join(b"MTrk" + struct.pack(">I", len(t)) + t for t in tracks)
    path.write_bytes(b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks), 480) + body)


def band(lead_program, lead_notes, without=None):
    parts = {
        BASS: (33, [(t, n, l, 100) for t, n, l in bass_line()]),
        PIANO: (0, [(t, c, l, 78) for t, c, l in piano_chords()]),
        DRUMS: (0, [(t, n, 120, v) for t, n, v in drum_hits()]),
    }
    if lead_notes is not None:
        parts[LEAD] = (lead_program, lead_notes)
    if without is not None:
        parts.pop(without, None)
    return parts


# --- Rendering and mixing ---------------------------------------------------------

def read_wav(path):
    with wave.open(str(path)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64)
    return x.reshape(-1, 2) / 32768


def write_wav(path, x):
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def gervill(name, parts):
    mid = HERE / "midi" / f"{name}.mid"
    wav = HERE / "tmp" / f"{name}.wav"
    write_mid(mid, parts)
    subprocess.run(JAVA + [str(mid), str(wav)], check=True)
    return read_wav(wav)


def monk(name, notes, profile, monks=1):
    """notes: [(start, note_or_chord, length, mode[, overrides])], helper note numbers."""
    take = mp.Take(name, name, monks)
    mp.header(take)
    mp.sing(take, notes, profile)
    script = HERE / "scripts" / f"{name}.txt"
    script.write_text(take.script(), encoding="utf-8")
    wav = HERE / "tmp" / f"{name}.wav"
    subprocess.run([str(mp.EXE), "--render", str(script), str(wav), "--monks", str(monks),
                    "--tail", "1500"], check=True, capture_output=True)
    return read_wav(wav)


def rms(x):
    a = x[int(START * SR / 1000):int((START + 5 * W) * SR / 1000)]
    return math.sqrt(np.mean(a ** 2))


def pad(x, n):
    return np.vstack([x, np.zeros((n - len(x), 2))]) if len(x) < n else x[:n]


def phrase(notes, mode, shift):
    """Melody/bass notes -> helper notes: written pitch +12 (the DSP sings an
    octave low) + 12 * shift; mode for connected notes, legato fills gaps."""
    out = []
    for i, entry in enumerate(notes):
        t, n, length = entry[:3]
        extra = entry[3] if len(entry) > 3 else None
        connected = i > 0 and t - (notes[i - 1][0] + notes[i - 1][2]) <= 120
        m = mode if connected else "new"
        if mode == "legato" and i + 1 < len(notes):
            nxt = notes[i + 1][0]
            if nxt - (t + length) <= 120:
                length = nxt - t
        up = 12 + 12 * shift
        n2 = tuple(x + up for x in n) if isinstance(n, tuple) else n + up
        out.append((t, n2, length, m) + ((extra,) if extra else ()))
    return out


class Comparison:
    def __init__(self, name, title):
        self.name, self.title = name, title
        self.sections = []  # (file name, label, signal)

    def add(self, file, label, x):
        self.sections.append((file, label, x))

    def write(self, guide):
        folder = HERE / self.name
        folder.mkdir(exist_ok=True)
        n = max(len(x) for _, _, x in self.sections)
        peak = max(np.abs(x).max() for _, _, x in self.sections)
        scale = 0.89 / peak  # one gain for every section, so loudness stays comparable
        gap = np.zeros((int(GAP_S * SR), 2))
        chunks, t = [], 0.0
        guide += [f"## {self.name}/", "", self.title, ""]
        for i, (file, label, x) in enumerate(self.sections, 1):
            y = pad(x, n) * scale
            write_wav(folder / f"{i:02d}_{file}.wav", y)
            guide.append(f"- `{i:02d}_{file}.wav` (all.wav {mp.mmss(t * 1000)}): {label}")
            chunks += [y, gap]
            t += (len(y) + len(gap)) / SR
        write_wav(folder / "all.wav", np.vstack(chunks))
        guide.append("")


def range_comparison(name, title, program, gervill_notes, monk_notes, mode, profile, shifts,
                     part=LEAD, monks=1):
    c = Comparison(name, title)
    solo = gervill(f"{name}_solo", {part: (program, gervill_notes)})
    full = gervill(f"{name}_band", band(program, gervill_notes) if part == LEAD else band(None, None))
    rest = gervill(f"{name}_rest", band(program, gervill_notes, without=part))
    target = rms(solo)
    c.add("gervill_solo", "Gervill (what midis2jam2 plays), alone", solo)
    voiced = []
    for shift, label in shifts:
        x = monk(f"{name}_{shift:+d}", phrase(monk_notes, mode, shift), profile, monks)
        x = x * (target / rms(x))  # same loudness as the instrument it replaces
        voiced.append((shift, label, x))
        c.add(f"monk_{label.split(' (')[0].replace(' ', '_').replace('+', 'up').replace('-', 'down')}_solo",
              f"Delay Lama, {label}, alone", x)
    c.add("gervill_band", "Band, Gervill", full)
    for shift, label, x in voiced:
        n = max(len(rest), len(x))
        c.add(f"monk_{label.split(' (')[0].replace(' ', '_').replace('+', 'up').replace('-', 'down')}_band",
              f"Band with Delay Lama, {label}", pad(rest, n) + pad(x, n))
    return c


# Profiles for phrases (first guesses, as in g01/g02).
DUM = dict(vowel=0.12, onset_vowel=0.55, onset_time=25, decay=300, sustain=0.3, end_vowel=0.0,
           release=50, breath=0.25, voice=0.35)
DING = dict(vowel=0.95, onset_vowel=0.6, onset_time=20, decay=500, sustain=0.0, drift_vowel=0.8,
            drift_time=500, end_vowel=0.1, release=100, breath=0.3, burst=0.8, burst_time=15,
            vib_rate=0.0, voice=0.6)
TAA = dict(vowel=0.6, onset_vowel=0.75, onset_time=25, dip_time=20, dip_level=0.1, burst=1.0,
           burst_time=30, breath=0.45, scoop=-0.4, scoop_time=40, attack=6, peak=1.15, decay=150,
           sustain=0.8, vib=0.2, vib_delay=350, release=100, voice=0.6)
SAX = dict(vowel=0.12, onset_vowel=0.6, onset_time=40, drift_vowel=0.5, drift_time=500, breath=0.7,
           scoop=-0.8, scoop_time=100, attack=20, vib=0.35, vib_rate=0.55, vib_delay=350,
           vib_fade=250, end_vowel=0.2, release=120, glide_time=60)
FLUTE = dict(vowel=0.2, onset_vowel=0.12, onset_time=60, breath=0.9, burst=1.0, burst_time=60,
             attack=40, vib=0.15, vib_delay=250, vib_fade=300, release=100, voice=0.75,
             dip_time=20, dip_level=0.2, dip_vowel=0.55)
VIOLIN = dict(vowel=0.92, onset_vowel=0.85, onset_time=80, breath=0.35, attack=120, vib=0.3,
              vib_rate=0.6, vib_delay=300, vib_fade=400, release=200, voice=0.7, glide_time=60)
NYEOW = dict(vowel=0.5, onset_vowel=1.0, onset_time=140, scoop=-1.0, scoop_time=90, attack=15,
             decay=1500, sustain=0.75, vib=0.4, vib_rate=0.55, vib_delay=450, vib_fade=300,
             end_vowel=0.05, end_time=250, release=280, fall=-0.7, fall_time=300, breath=0.6,
             voice=0.45, glide_time=50)

WRITTEN = (0, "as written")
NATIVE = (-1, "-1 octave (Delay Lama native)")


def velocity_comparison():
    vel = [50, 58, 66, 74, 82, 90,  # bar 1: crescendo
           112, 60, 60, 112,         # bar 2: accents on 1 and 4
           60, 72, 84, 96, 120,      # bar 3: crescendo to ff
           110, 90, 70,              # bar 4: diminuendo
           40]                       # bar 5: soft ending
    notes = [(t, n, l, v) for (t, n, l), v in zip(melody(), vel)]
    c = Comparison("c08_velocity", "Velocity: a trumpet line from soft (40) to loud (120), "
                   "with accents in bar 2 (Delay Lama as written)")
    solo = gervill("c08_velocity_solo", {LEAD: (56, notes)})
    target = rms(solo)
    c.add("gervill_solo", "Gervill trumpet with these velocities", solo)
    for key, label, power, bright in (("none", "no velocity response (classic Delay Lama)", 0, 0),
                                      ("moderate", "moderate: about 12 dB from 127 to 32", 1, 0),
                                      ("gm", "GM curve, as the phase 1 helper does: about 24 dB", 2, 0),
                                      ("gm_bright", "GM curve, plus brighter vowel and more breath "
                                                    "when hard", 2, 1)):
        line = []
        for t, n, l, v in notes:
            over = {"level": (v / 127) ** power / (100 / 127) ** power}
            if bright:
                d = (v - 80) / 47
                over.update(vowel=min(1.0, TAA["vowel"] + 0.15 * d),
                            onset_vowel=min(1.0, TAA["onset_vowel"] + 0.1 * d),
                            burst=min(1.0, max(0.3, 0.75 + 0.25 * d)))
            line.append((t, n, l, over))
        x = monk(f"c08_velocity_{key}", phrase(line, "re", 0), TAA)
        c.add(f"monk_{key}", f"Delay Lama, {label}", x * (target / rms(x)))
    return c


def noise_burst(band_hz, tau_ms, length_ms, seed):
    """Band-passed white noise with a 1 ms attack and an exponential decay."""
    n = int(SR * length_ms / 1000)
    rng = np.random.default_rng(seed)
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    spec[(f < band_hz[0]) | (f > band_hz[1])] = 0
    x = np.fft.irfft(spec, n)
    x /= np.abs(x).max()
    t = np.arange(n) / SR * 1000
    return x * np.minimum(1, t / 1.0) * np.exp(-t / tau_ms)


def add_noise(x, hits, ref):
    """Mock-up of a helper-side consonant layer: hits = [(ms, burst, level)]."""
    y = x.copy()
    for k, (ms, burst, level) in enumerate(hits):
        i = int(ms * SR / 1000)
        b = burst * level * ref
        j = min(len(y), i + len(b))
        y[i:j] += b[:j - i, None]
    return y


KICK = dict(vowel=0.0, onset_vowel=0.2, onset_time=20, voice=0.0, scoop=5.0, scoop_time=35,
            decay=90, sustain=0.0, max_len=120, release=20, breath=0.1)
SNARE = dict(vowel=0.55, onset_vowel=0.3, onset_time=15, voice=0.7, breath=1.0, burst=1.0,
             burst_time=20, decay=70, sustain=0.0, max_len=90, release=15)
HAT = dict(vowel=1.0, voice=1.0, breath=1.0, decay=25, sustain=0.0, max_len=30, release=8)


def consonant_comparison():
    c = Comparison("c09_consonants", "Pure Delay Lama vs. a mock-up of a small noise layer "
                   "for consonants and drums (offline mix, not the helper)")
    # Trumpet 'taa' as written, then with a 't' burst at each note.
    trumpet = monk("c09_trumpet", phrase(melody(), "re", 0), TAA)
    ref = math.sqrt(np.mean(trumpet ** 2))
    t_hits = [(t, noise_burst((3000, 9000), 5, 40, k), 2.5) for k, (t, n, l) in enumerate(melody())]
    c.add("trumpet_pure", "Trumpet 'taa', pure Delay Lama (as in c03)", trumpet)
    c.add("trumpet_noise", "Same, plus a 't' noise burst on every note", add_noise(trumpet, t_hits, ref))
    # Muted guitar chug on E2, two bars of eighths.
    chug_notes = [(START + i * E, 52, 70, "new") for i in range(16)]
    chug = monk("c09_chug", chug_notes, dict(vowel=0.3, onset_vowel=0.7, onset_time=15, burst=1.0,
                                             burst_time=20, breath=0.5, max_len=60, decay=50,
                                             sustain=0.3, end_vowel=0.1, release=20, voice=0.4))
    chug = chug * (np.abs(trumpet).max() / np.abs(chug).max())  # as loud as the trumpet
    ref = math.sqrt(np.mean(chug ** 2))
    ch_hits = [(t, noise_burst((2000, 7000), 18, 120, 100 + k), 3.0) for k, (t, n, l, m) in enumerate(chug_notes)]
    c.add("chug_pure", "Muted guitar 'dg-dg', pure Delay Lama", chug)
    c.add("chug_noise", "Same, plus a 'ch' noise burst on every note ('chugga')", add_noise(chug, ch_hits, ref))
    # Beatbox: one monk, kick/snare win over the hi-hat on the same eighth.
    by_time = {}
    for t, n, v in drum_hits():
        by_time.setdefault(t, set()).add(n)
    line, noise = [], []
    for k, t in enumerate(sorted(by_time)):
        hit = by_time[t]
        if 36 in hit:
            line.append((t, 45, 120, "new", KICK))
        elif 38 in hit:
            line.append((t, 64, 90, "new", SNARE))
            noise.append((t, noise_burst((1500, 9000), 45, 250, 200 + k), 2.5))
        else:
            line.append((t, 100, 30, "new", HAT))
            noise.append((t, noise_burst((6000, 15000), 12, 80, 300 + k), 1.2))
        if 49 in hit:
            noise.append((t, noise_burst((4000, 15000), 300, 1500, 400), 1.5))
    box = monk("c09_beatbox", line, {})
    ref = math.sqrt(np.mean(box ** 2))
    boxed = add_noise(box, noise, ref)
    drums = gervill("c09_drums", {DRUMS: band(None, None)[DRUMS]})
    rest = gervill("c09_rest", band(56, [(t, nn, l, 96) for t, nn, l in melody()], without=DRUMS))
    target = rms(drums)
    box, boxed = box * (target / rms(box)), boxed * (target / rms(boxed))
    c.add("drums_gervill", "Gervill drums (kick, snare, hi-hat)", drums)
    c.add("beatbox_pure", "Beatbox monk, pure Delay Lama: kick 'bm', snare 'ka', hat 'ti'", box)
    c.add("beatbox_noise", "Beatbox monk plus noise on snare and hat ('pf', 'ts')", boxed)
    n = max(len(rest), len(box))
    c.add("band_beatbox_pure", "Band (trumpet lead) with the pure beatbox monk instead of drums",
          pad(rest, n) + pad(box, n))
    c.add("band_beatbox_noise", "Band with the beatbox monk plus noise", pad(rest, n) + pad(boxed, n))
    return c


def main():
    for d in ("midi", "scripts", "tmp"):
        (HERE / d).mkdir(exist_ok=True)
    comparisons = [
        range_comparison("c01_bass", "Bass line (finger bass, A1-A2): which octave should the monk sing?",
                         33, [(t, n, l, 100) for t, n, l in bass_line()], bass_line(), "new", DUM,
                         [WRITTEN, (1, "+1 octave"), (2, "+2 octaves")], part=BASS),
        range_comparison("c02_piano", "Piano chords on every beat, sung by a choir of 4 monks",
                         0, [(t, c, l, 78) for t, c, l in piano_chords()], piano_chords(), "new", DING,
                         [WRITTEN, NATIVE], part=PIANO, monks=4),
        range_comparison("c03_trumpet", "Trumpet lead (A4-E5), tongued 'taa-daa'",
                         56, [(t, n, l, 96) for t, n, l in melody()], melody(), "re", TAA,
                         [WRITTEN, NATIVE]),
        range_comparison("c04_sax", "Tenor sax lead (A3-E4), slurred 'doo-ah'",
                         66, [(t, n, l, 96) for t, n, l in melody(-12)], melody(-12), "legato", SAX,
                         [WRITTEN, NATIVE]),
        range_comparison("c05_flute", "Flute lead (A5-E6), tongued 'hoo-too'",
                         73, [(t, n, l, 96) for t, n, l in melody(12)], melody(12), "re", FLUTE,
                         [WRITTEN, NATIVE, (-2, "-2 octaves")]),
        range_comparison("c06_violin", "Violin lead (A5-E6), slurred 'neee'",
                         40, [(t, n, l, 96) for t, n, l in melody(12)], melody(12), "legato", VIOLIN,
                         [WRITTEN, NATIVE, (-2, "-2 octaves")]),
        range_comparison("c07_guitar", "Overdrive guitar lead (A3-E4), 'nyeow' with slides",
                         29, [(t, n, l, 100) for t, n, l in melody(-12)], melody(-12), "legato", NYEOW,
                         [WRITTEN, NATIVE]),
        velocity_comparison(),
        consonant_comparison(),
    ]
    guide = ["# Phase 4a A/B listening guide", "",
             "Each folder compares the instrument as midis2jam2 plays it (Gervill, its default",
             "soundbank) with Delay Lama candidates: first alone, then inside a small band",
             "(drums, bass, piano, lead) where the monk replaces that instrument. Every",
             "candidate is matched to the loudness of the instrument it replaces; one gain per",
             "folder keeps sections comparable. `all.wav` plays the sections in order with",
             f"{GAP_S:g} s gaps. The monk is dry (no echo); Gervill has its default reverb.",
             "The syllables are first guesses (phase 4c tunes them); judge the octave, and",
             "in c08 the dynamics.", "",
             "\"As written\" means the monk sings the file's pitch (the helper adds the",
             "octave that the DSP drops); \"-1 octave\" is Delay Lama's native register.", ""]
    for c in comparisons:
        c.write(guide)
    (HERE / "AB_LISTENING.md").write_text("\n".join(guide), encoding="utf-8")
    shutil.rmtree(HERE / "tmp")  # intermediate renders; the c*/ folders hold the results


if __name__ == "__main__":
    main()
