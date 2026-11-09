"""Phase 4c piano test phrases (IMITATION.md section 17), the MIDI writer, the
Gervill renderer and the DelayLamaVoice script builder. Dev tool, never
packaged; make_4c_piano.py and measure_4c_piano.py use it.

Every phrase is a list of notes (start ms, written MIDI note, length ms,
velocity) plus sustain-pedal events (ms, 0 or 127), at 100 bpm with a 500 ms
lead-in. The MIDI files land in midi/ and are meant to be reused as test files:

  scale.mid          C major scale C4-C5-C4 in eighths, non-legato
  repeated.mid       repeated G4: eighths, then sixteenths, then E4 eighths
  legato.mid         a cantabile line, each note overlapping the next by 40 ms
  run.mid            a fast run C4-G5-C4, 100 ms per note
  long.mid           one long C4 and one long C major chord (3 s each)
  block_chords.mid   four-note chords on every beat (C Am | F G)
  broken_chords.mid  pedalled arpeggios (C | G), then a long pedalled C chord
  lines.mid          scale, repeated, legato, run and long C4 in one file
  piano_part.mid     block chords, broken chords and the long chord (5 bars)
  band.mid           piano_part with drums and a finger bass (channel 1 piano,
                     channel 2 bass, channel 10 drums)
"""

import pathlib
import struct
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.dont_write_bytecode = True  # nothing written into the shared tool folders
sys.path[:0] = [str(ROOT / "renders" / "phase4b" / "diag"), str(ROOT / "tools" / "profiles")]
import dl  # noqa: E402
import expand  # noqa: E402

GERVILL = ROOT / "renders" / "phase4a" / "ab" / "GervillRender.java"
JAVA = ["java", "--add-exports", "java.desktop/com.sun.media.sound=ALL-UNNAMED", str(GERVILL)]

BEAT = 600.0  # 100 bpm
Q, E, S, H, W = BEAT, BEAT / 2, BEAT / 4, 2 * BEAT, 4 * BEAT
START = 500.0
PIANO, BASS, DRUMS = 0, 1, 9


class Phrase:
    def __init__(self, name, notes, pedal=(), length=None):
        self.name = name
        self.notes = sorted(notes)
        self.pedal = sorted(pedal)
        end = max(t + d for t, _, d, _ in self.notes)
        self.length = length or end

    def shifted(self, ms):
        return Phrase(self.name, [(t + ms, n, d, v) for t, n, d, v in self.notes],
                      [(t + ms, v) for t, v in self.pedal])


def line(pitches, step, fraction, velocity=80, start=START, overlap=0.0):
    """Equal steps; each note `fraction` of a step long, plus `overlap` ms."""
    return [(start + i * step, n, step * fraction + overlap, velocity) for i, n in enumerate(pitches)]


def scale():
    up = [60, 62, 64, 65, 67, 69, 71, 72]
    notes = line(up + up[-2::-1], E, 0.85)
    notes[-1] = (notes[-1][0], 60, Q * 0.9, 80)
    return Phrase("scale", notes)


def repeated():
    notes = line([67] * 4, E, 0.8, 84)
    notes += line([67] * 8, S, 0.75, 78, START + 4 * E)
    notes += line([64] * 4, E, 0.8, 80, START + 4 * E + 8 * S)
    notes.append((START + 8 * E + 8 * S, 64, Q * 0.9, 76))
    return Phrase("repeated", notes)


def legato():
    """An original cantabile line in quarters (halves at phrase ends), each
    note held 40 ms into the next, as a pianist's legato."""
    tune = [(67, Q), (69, Q), (67, Q), (64, Q), (65, Q), (67, Q), (72, H)]
    notes, t = [], START
    for k, (n, d) in enumerate(tune):
        last = k == len(tune) - 1
        notes.append((t, n, d * 0.95 if last else d + 40, 78))
        t += d
    return Phrase("legato", notes)


def run():
    up = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79]
    notes = line(up + up[-2::-1], 100.0, 0.95, 80)
    notes[-1] = (notes[-1][0], 60, Q * 0.9, 80)
    return Phrase("run", notes)


def long_notes():
    notes = [(START, 60, 3000.0, 90)]
    notes += [(START + 3600, n, 3000.0, 82) for n in (60, 64, 67, 72)]
    return Phrase("long", notes)


CHORDS = {"C": (60, 64, 67, 72), "Am": (60, 64, 69, 72), "F": (60, 65, 69, 72), "G": (59, 62, 67, 71)}


def block_chords(start=START):
    notes = []
    for beat, name in enumerate(["C", "C", "Am", "Am", "F", "F", "G", "G"]):
        velocity = 84 if beat % 2 == 0 else 72
        notes += [(start + beat * Q, n, Q * 0.8, velocity) for n in CHORDS[name]]
    return Phrase("block_chords", notes)


ARPEGGIOS = [(48, 55, 60, 64, 67, 72, 67, 64), (43, 50, 55, 59, 62, 67, 62, 59)]
FINAL = (48, 55, 60, 64, 67)


def broken_chords(start=START):
    """Two bars of pedalled arpeggios in eighths (C, G), then a long C chord.
    The pedal is changed at each bar line (up with the new bass note, down 60 ms
    later), so up to six notes ring at once."""
    notes, pedal = [], []
    for bar, arpeggio in enumerate(ARPEGGIOS):
        t0 = start + bar * W
        notes += [(t0 + k * E, n, E * 0.9, 80 if k == 0 else 70) for k, n in enumerate(arpeggio)]
        pedal += [(t0, 0), (t0 + 60, 127)]
    t0 = start + 2 * W
    notes += [(t0, n, W * 0.95, 76) for n in FINAL]
    pedal += [(t0, 0), (t0 + 60, 127), (t0 + W, 0)]
    return Phrase("broken_chords", notes, pedal)


def chain(name, phrases, gap=BEAT):
    notes, pedal, t = [], [], 0.0
    for p in phrases:
        moved = p.shifted(t)
        notes += moved.notes
        pedal += moved.pedal
        t = moved.length - START + gap
    return Phrase(name, notes, pedal)


def lines():
    long_c4 = Phrase("long_c4", [(START, 60, 2500.0, 90)])
    return chain("lines", [scale(), repeated(), legato(), run(), long_c4])


def piano_part():
    """Bars 1-2 block chords, bars 3-4 pedalled arpeggios, bar 5 the long chord."""
    block, broken = block_chords(), broken_chords(START + 2 * W)
    return Phrase("piano_part", block.notes + broken.notes, broken.pedal)


def bass_line():
    """Finger bass (Gervill) under piano_part: roots in quarters, then halves."""
    notes = []
    for beat, root in enumerate([36, 36, 33, 33, 29, 29, 31, 31]):
        notes.append((START + beat * Q, root, Q * 0.85, 96))
    for bar, root in enumerate([36, 31]):
        t0 = START + (2 + bar) * W
        notes += [(t0, root, H * 0.9, 96), (t0 + H, root + 7, H * 0.9, 90)]
    notes.append((START + 4 * W, 36, W * 0.95, 96))
    return notes


def drum_hits():
    hits = []
    for bar in range(4):
        t = START + bar * W
        hits += [(t + k * E, 42, 70) for k in range(8)]
        hits += [(t, 36, 105), (t + 2 * Q, 36, 100), (t + 2.5 * Q, 36, 85)]
        hits += [(t + Q, 38, 95), (t + 3 * Q, 38, 95)]
    hits += [(START + 4 * W, 36, 110), (START + 4 * W, 49, 100)]
    return [(t, n, 120.0, v) for t, n, v in hits]


# --- MIDI --------------------------------------------------------------------------

def vlq(n):
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.insert(0, (n & 0x7F) | 0x80)
        n >>= 7
    return bytes(out)


def ticks(ms):
    return int(round(ms / BEAT * 480))


def write_mid(path, parts):
    """parts: {channel: (program, notes, pedal)}; format 1, 480 ticks per beat."""
    tracks = [b"\x00\xff\x51\x03" + int(BEAT * 1000).to_bytes(3, "big") + b"\x00\xff\x2f\x00"]
    for channel, (program, notes, pedal) in sorted(parts.items()):
        events = [(0, 0, bytes([0xC0 | channel, program]))]
        for t, n, d, v in notes:
            events.append((ticks(t), 2, bytes([0x90 | channel, n, v])))
            events.append((ticks(t + d), 0, bytes([0x80 | channel, n, 0])))
        for t, v in pedal:
            events.append((ticks(t), 1 if v == 0 else 3, bytes([0xB0 | channel, 64, v])))
        events.sort(key=lambda e: (e[0], e[1]))
        data, now = b"", 0
        for tick, _, msg in events:
            data += vlq(tick - now) + msg
            now = tick
        tracks.append(data + b"\x00\xff\x2f\x00")
    body = b"".join(b"MTrk" + struct.pack(">I", len(t)) + t for t in tracks)
    pathlib.Path(path).write_bytes(b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks), 480) + body)


def band_parts(piano=True):
    parts = {BASS: (33, bass_line(), []), DRUMS: (0, drum_hits(), [])}
    if piano:
        p = piano_part()
        parts[PIANO] = (0, p.notes, p.pedal)
    return parts


def write_all_midi(folder=HERE / "midi"):
    folder.mkdir(exist_ok=True)
    for phrase in (scale(), repeated(), legato(), run(), long_notes(), block_chords(), broken_chords(),
                   lines(), piano_part()):
        write_mid(folder / f"{phrase.name}.mid", {PIANO: (0, phrase.notes, phrase.pedal)})
    write_mid(folder / "band.mid", band_parts())
    write_mid(folder / "band_no_piano.mid", band_parts(piano=False))


def gervill(mid, wav):
    subprocess.run(JAVA + [str(mid), str(wav)], check=True, capture_output=True)
    return dl.read_wav(wav)


# --- DelayLamaVoice scripts ----------------------------------------------------------

def script(phrase, sections, extra=(), cc7=100):
    """Protocol 1 script as the router would send it: hello 1, profile mode,
    the profile's set lines, then `on <note> <velocity> <length>`, `off`, and
    the pedal as cc 64, offs before pedal-ups before ons at the same time."""
    events = []
    for t, n, d, v in phrase.notes:
        events.append((t + d, 0, f"off {n}"))
        events.append((t, 2, f"on {n} {v} {d:g}"))
    for t, v in phrase.pedal:
        events.append((t, 1 if v == 0 else 3, f"cc 64 {v}"))
    events.sort(key=lambda e: (e[0], e[1]))
    lines_ = ["hello 1", "set articulator 1", f"cc 7 {cc7}"]
    lines_ += expand.set_lines(sections)
    lines_ += [f"set {k} {v:g}" for k, v in extra]
    t = 0.0
    for when, _, text in events:
        if when > t:
            lines_.append(f"wait {when - t:g}")
            t = when
        lines_.append(text)
    return "\n".join(lines_) + "\n"


def profile(name="piano", data=None, **override):
    """A profile's resolved sections, with section overrides merged in."""
    data = data or expand.load()
    return expand.merge(expand.resolve(data, name), override)
