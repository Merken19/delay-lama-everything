#!/usr/bin/env python3
"""Writes the Delay Lama Everything test MIDI set into tests/midi/.

Roadmap phase 0, "Gather test MIDI files": a melody, chords, a band, pitch
bends (with RPN 0 bend-range changes), lyrics and a multi-port file. Every
file is composed here, from scratch and deterministically, so the set can be
remade anywhere with the standard library only:

    py tools\\testmidi\\make_test_midis.py            # writes tests/midi/*.mid
    py tools\\testmidi\\make_test_midis.py --list     # and prints what is in them

tests/midi/README.md says what each file tests and how to sing it.
"""

import argparse
import math
import pathlib
import sys

PPQ = 480
Q = PPQ  # quarter note
E = PPQ // 2  # eighth
S = PPQ // 4  # sixteenth
H = 2 * PPQ  # half
DQ = Q + E  # dotted quarter
DH = H + Q  # dotted half
W = 4 * PPQ  # whole note, one 4/4 bar
BAR = W

# Order of events on the same tick: meta first (port, names, lyrics), then
# system exclusive, controllers and programs, bends, note-offs and note-ons,
# so a repeated note ends before it starts again.
META, SYSEX, CONTROL, BEND, NOTE_OFF, NOTE_ON = range(6)

NAMES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

# General MIDI, zero-based (as in the file).
PIANO, CLEAN_GUITAR, OVERDRIVE_GUITAR, FINGER_BASS = 0, 27, 29, 33
VIOLIN, CELLO, STRINGS, VOICE_OOHS = 40, 42, 48, 53
ALTO_SAX, DRAWBAR_ORGAN, WARM_PAD = 65, 16, 89

DRUMS = 9  # channel 10
KICK, SNARE, HAT, CRASH = 36, 38, 42, 49

GM_SYSTEM_ON = bytes([0x7E, 0x7F, 0x09, 0x01, 0xF7])


def n(name):
    """MIDI note number of a name like C4 (60), F#3 or Bb2."""
    key = NAMES[name[0]]
    rest = name[1:]
    while rest and rest[0] in "#b":
        key += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    return 12 * (int(rest) + 1) + key


def vlq(value):
    """A variable-length quantity."""
    out = [value & 0x7F]
    value >>= 7
    while value:
        out.append(0x80 | (value & 0x7F))
        value >>= 7
    return bytes(reversed(out))


class Track:
    """One track's events; ticks are absolute until the track is written."""

    def __init__(self, name=None, port=None):
        self.events = []
        if port is not None:
            self.meta(0, 0x21, bytes([port]))  # MIDI Port: this track's port, as the file numbers it
        if name:
            self.meta(0, 0x03, name.encode("latin-1"))

    def _add(self, tick, rank, data):
        self.events.append((tick, rank, len(self.events), data))

    def meta(self, tick, kind, data):
        self._add(tick, META, bytes([0xFF, kind]) + vlq(len(data)) + data)

    def text(self, tick, kind, text):
        self.meta(tick, kind, text.encode("latin-1"))

    def tempo(self, tick, bpm):
        self.meta(tick, 0x51, round(60_000_000 / bpm).to_bytes(3, "big"))

    def time_signature(self, tick, numerator, denominator):
        self.meta(tick, 0x58, bytes([numerator, denominator.bit_length() - 1, 24, 8]))

    def lyric(self, tick, text):
        self.text(tick, 0x05, text)

    def sysex(self, tick, body):
        """A system exclusive message; [body] follows the F0 and ends with F7."""
        self._add(tick, SYSEX, b"\xF0" + vlq(len(body)) + body)

    def cc(self, tick, channel, number, value):
        self._add(tick, CONTROL, bytes([0xB0 | channel, number, value]))

    def program(self, tick, channel, program):
        self._add(tick, CONTROL, bytes([0xC0 | channel, program]))

    def setup(self, tick, channel, program, volume=100, pan=64):
        self.program(tick, channel, program)
        self.cc(tick, channel, 7, volume)
        self.cc(tick, channel, 10, pan)
        self.cc(tick, channel, 11, 127)

    def bend_range(self, tick, channel, semitones, cents=0):
        """RPN 0 (pitch bend sensitivity), then the null RPN, as most sequencers write it."""
        for number, value in ((101, 0), (100, 0), (6, semitones), (38, cents), (101, 127), (100, 127)):
            self.cc(tick, channel, number, value)

    def bend(self, tick, channel, value):
        value = max(0, min(16383, round(value)))
        self._add(tick, BEND, bytes([0xE0 | channel, value & 0x7F, value >> 7]))

    def bend_ramp(self, start, length, channel, begin, end, step=10):
        """A smooth bend from [begin] to [end] (14-bit values) over [length] ticks, one event every [step] ticks."""
        count = max(1, length // step)
        for i in range(1, count + 1):
            # A raised cosine, as a player's hand moves.
            shape = 0.5 - 0.5 * math.cos(math.pi * i / count)
            self.bend(start + i * length // count, channel, begin + (end - begin) * shape)

    def note(self, tick, channel, key, velocity, length):
        self._add(tick, NOTE_ON, bytes([0x90 | channel, key, velocity]))
        self._add(tick + length, NOTE_OFF, bytes([0x80 | channel, key, 64]))

    def phrase(self, tick, channel, notes, velocity=90, legato=False):
        """Plays [notes], a list of (name or None for a rest, ticks[, style]) from [tick]; returns the end tick.

        Styles: "s" staccato (half length), "l" slurred into the next note (overlapping it by 30 ticks), "t" held
        to the full length; otherwise a note sounds for 90% of its length. [legato] slurs every note.
        """
        for item in notes:
            name, length = item[0], item[1]
            style = item[2] if len(item) > 2 else ("l" if legato else "")
            if name is not None:
                sounding = {"s": length // 2, "l": length + 30, "t": length}.get(style, length * 9 // 10)
                for key in name.split("+"):
                    self.note(tick, channel, n(key), velocity, sounding)
            tick += length
        return tick

    def end(self):
        return max((tick for tick, *_ in self.events), default=0)

    def to_bytes(self, end_tick):
        body = bytearray()
        last = 0
        for tick, _, _, data in sorted(self.events):
            body += vlq(tick - last) + data
            last = tick
        body += vlq(max(0, end_tick - last)) + b"\xFF\x2F\x00"
        return b"MTrk" + len(body).to_bytes(4, "big") + bytes(body)


def write_smf(path, tracks):
    """A format 1 file of [tracks]; every track ends one beat after the last event of any track."""
    end_tick = max(track.end() for track in tracks) + Q
    data = b"MThd" + (6).to_bytes(4, "big") + (1).to_bytes(2, "big")
    data += len(tracks).to_bytes(2, "big") + PPQ.to_bytes(2, "big")
    data += b"".join(track.to_bytes(end_tick) for track in tracks)
    path.write_bytes(data)


def conductor(title, bpm, markers=()):
    track = Track(title)
    track.text(0, 0x01, "Delay Lama Everything test file: " + title)
    track.time_signature(0, 4, 4)
    track.tempo(0, bpm)
    for tick, text in markers:
        track.text(tick, 0x06, text)
    return track


def chord_hits(track, channel, start, chords, beats, velocity, length):
    """Each chord (a "C4+E4+G4" name) for a bar, struck on each beat in [beats] (0-3)."""
    for bar, chord in enumerate(chords):
        for beat in beats:
            for key in chord.split("+"):
                track.note(start + bar * BAR + beat * Q, channel, n(key), velocity, length)


def held_chords(track, channel, start, chords, velocity, overlap=30):
    """Each chord held for a bar and slurred into the next: a key the next chord doesn't repeat sounds [overlap]
    ticks longer (a repeated key ends on the bar line, or its note-off would cut the new note)."""
    for bar, chord in enumerate(chords):
        following = set(chords[bar + 1].split("+")) if bar + 1 < len(chords) else set()
        for key in chord.split("+"):
            extra = overlap if following and key not in following else 0
            track.note(start + bar * BAR, channel, n(key), velocity, W + extra)


def drum_bars(track, start, bars, crash_bars=(), hats=8):
    for bar in range(bars):
        tick = start + bar * BAR
        if bar in crash_bars:
            track.note(tick, DRUMS, CRASH, 100, Q)
        for beat in (0, 2):
            track.note(tick + beat * Q, DRUMS, KICK, 100, E)
        for beat in (1, 3):
            track.note(tick + beat * Q, DRUMS, SNARE, 95, E)
        for i in range(hats):
            track.note(tick + i * (W // hats), DRUMS, HAT, 70 if i % 2 else 85, S)


# --- The files -------------------------------------------------------------------------------------------------


def melody():
    """One line on one channel: slurs, repeated notes, a run, staccato, long notes and an expression swell."""
    song = conductor("01 Melody", 92)
    lead = Track("Violin melody")
    lead.setup(0, 0, VIOLIN, volume=100)
    notes = [
        # bars 1-4: slurred, then a long note with a CC 11 swell
        ("G4", Q, "l"), ("A4", Q, "l"), ("B4", H),
        ("A4", Q), ("G4", E, "l"), ("A4", E, "l"), ("B4", Q), ("D5", Q),
        ("C5", DH, "l"), ("B4", Q),
        ("A4", W, "t"),
        # bars 5-8: a repeated note, a leap down, a fast slurred run
        ("B4", Q), ("B4", Q), ("A4", Q), ("G4", Q),
        ("E4", H), ("F#4", Q), ("G4", Q),
        ("A4", E, "l"), ("B4", E, "l"), ("A4", E, "l"), ("G4", E, "l"), ("F#4", Q), ("D4", Q),
        ("G4", W, "t"),
        # bars 9-12: staccato arpeggios with rests, then the close
        ("D5", E, "s"), ("B4", E, "s"), ("G4", E, "s"), ("B4", E, "s"), ("D5", Q, "s"), (None, Q),
        ("C5", E, "s"), ("A4", E, "s"), ("F#4", E, "s"), ("A4", E, "s"), ("C5", Q, "s"), (None, Q),
        ("B4", DQ), ("A4", E), ("G4", Q), ("F#4", Q),
        ("G4", DH, "t"), (None, Q),
    ]
    lead.phrase(0, 0, notes, velocity=88)
    swell = 3 * BAR
    for i in range(0, W, 30):  # bar 4: CC 11 80 -> 127 -> 90
        x = i / W
        value = 80 + 47 * math.sin(math.pi * min(x / 0.6, 1) / 2) if x < 0.6 else 127 - 37 * (x - 0.6) / 0.4
        lead.cc(swell + i, 0, 11, round(value))
    lead.cc(4 * BAR, 0, 11, 127)
    return [song, lead]


def chords():
    """Chords on one channel: triads, four-note chords, a five-note chord, sustain-pedal arpeggios, a moving top
    voice. Channel 2 doubles the harmony as a string pad."""
    song = conductor("02 Chords", 84, [(0, "Triads"), (4 * BAR, "Sevenths"), (8 * BAR, "Five notes"),
                                       (9 * BAR, "Pedal arpeggios"), (11 * BAR, "Moving top voice")])
    piano = Track("Piano chords")
    piano.setup(0, 0, PIANO, volume=100)
    # bars 1-4: triads on beats 1 and 3
    chord_hits(piano, 0, 0, ["C4+E4+G4", "A3+C4+E4", "A3+C4+F4", "B3+D4+G4"], (0, 2), 85, H - E)
    # bars 5-8: four-note chords, held (a full choir of 4)
    chord_hits(piano, 0, 4 * BAR, ["C4+E4+G4+B4", "A3+C4+E4+G4", "D4+F4+A4+C5", "G3+B3+D4+F4"], (0,), 85, W - E)
    # bar 9: five notes, one more than the default choir
    chord_hits(piano, 0, 8 * BAR, ["C3+G3+E4+Bb4+D5"], (0,), 90, W - E)
    # bars 10-11: arpeggios held only by the sustain pedal (each key is let go at once)
    for bar, keys in ((9, "C3 G3 C4 E4 G4 C5 G4 E4"), (10, "F2 C3 F3 A3 C4 F4 C4 A3")):
        start = bar * BAR
        piano.cc(start, 0, 64, 127)
        for i, key in enumerate(keys.split()):
            piano.note(start + i * E, 0, n(key), 80, E // 2)
        piano.cc(start + W - 20, 0, 64, 0)
    # bar 12: a chord held while the top voice moves; bar 13: the last chord
    for key in ("C4", "E4", "G4"):
        piano.note(11 * BAR, 0, n(key), 75, W)
    piano.phrase(11 * BAR, 0, [("C5", Q), ("D5", Q), ("E5", Q), ("D5", Q)], velocity=90)
    chord_hits(piano, 0, 12 * BAR, ["C3+G3+C4+E4"], (0,), 85, W)

    pad = Track("String pad")
    pad.setup(0, 1, STRINGS, volume=70)
    progression = ["C3+G3+E4", "A2+E3+C4", "F2+C3+A3", "G2+D3+B3"] * 2 + ["C3+Bb3+E4", "C3+G3+E4", "F2+C3+A3",
                                                                          "C3+G3+E4", "C3+G3+E4"]
    held_chords(pad, 1, 0, progression, 55)
    return [song, piano, pad]


def band():
    """A band: drums, bass, guitar, a pad from bar 9 and an alto sax lead that enters at bar 5."""
    song = conductor("03 Band", 110, [(0, "Intro"), (4 * BAR, "Verse"), (8 * BAR, "Chorus")])
    roots = ["C2", "A1", "F2", "G2"] * 4 + ["C2"]
    triads = ["C4+E4+G4", "A3+C4+E4", "A3+C4+F4", "B3+D4+G4"] * 4

    drums = Track("Drums")
    drums.setup(0, DRUMS, 0, volume=100)
    drum_bars(drums, 0, 16, crash_bars=(0, 8))
    drums.note(16 * BAR, DRUMS, CRASH, 110, W)
    drums.note(16 * BAR, DRUMS, KICK, 110, Q)

    bass = Track("Bass")
    bass.setup(0, 1, FINGER_BASS, volume=110)
    for bar, root in enumerate(roots[:16]):
        r = n(root)
        for at, length, key in ((0, Q, r), (Q, E, r), (Q + E, E, r), (2 * Q, Q, r + 7), (3 * Q, E, r + 12),
                                (3 * Q + E, E, r + 7)):
            bass.note(bar * BAR + at, 1, key, 95, length * 9 // 10)
    bass.note(16 * BAR, 1, n(roots[16]), 100, W)

    guitar = Track("Guitar")
    guitar.setup(0, 2, CLEAN_GUITAR, volume=85, pan=90)
    chord_hits(guitar, 2, 0, triads, (1, 3), 80, E)
    for key in ("C4", "E4", "G4"):
        guitar.note(16 * BAR, 2, n(key), 85, W)

    pad = Track("Pad")
    pad.setup(0, 3, WARM_PAD, volume=60, pan=40)
    held_chords(pad, 3, 8 * BAR, ["C3+G3+E4", "A2+E3+C4", "F2+C3+A3", "G2+D3+B3"] * 2, 60)

    lead = Track("Alto sax lead")
    lead.setup(0, 0, ALTO_SAX, volume=105, pan=64)
    lead.phrase(4 * BAR, 0, [
        ("G4", DQ), ("E4", E), ("G4", Q), ("A4", Q),
        ("C5", H), ("A4", Q), (None, Q),
        ("A4", E, "l"), ("C5", E, "l"), ("A4", E, "l"), ("F4", E), ("G4", Q), ("A4", Q),
        ("G4", DH), (None, Q),
        ("E5", Q), ("D5", Q), ("C5", Q), ("G4", Q),
        ("A4", DQ, "l"), ("B4", E, "l"), ("C5", H),
        ("F4", Q), ("A4", Q), ("C5", Q), ("D5", E, "l"), ("C5", E),
        ("B4", H, "l"), ("D5", H),
        ("C5", E, "s"), ("C5", E, "s"), ("B4", E), ("A4", E), ("G4", Q), ("E4", Q),
        ("A4", DH), ("C5", Q),
        ("D5", DQ), ("C5", E), ("A4", Q), ("F4", Q),
        ("G4", Q), ("A4", Q), ("B4", Q), ("D5", Q),
        ("C5", W, "t"),
    ], velocity=92)
    return [song, drums, bass, guitar, pad, lead]


def bends():
    """Pitch bends on channel 1 at the default range, after RPN 0 changes, after an NRPN (which must not change
    the range) and after a GM reset. Channel 2 plays each held bend's target note softly, for reference."""
    song = conductor("04 Bends", 90, [(0, "Range 2 (default)"), (4 * BAR, "RPN 0: range 12"),
                                      (8 * BAR, "NRPN: range stays 12"), (10 * BAR, "RPN 0: range 7"),
                                      (12 * BAR, "GM reset: range 2")])
    lead = Track("Overdrive guitar bends")
    lead.setup(0, 0, OVERDRIVE_GUITAR, volume=100)
    ref = Track("Organ reference")
    ref.setup(0, 1, DRAWBAR_ORGAN, volume=60)
    up, centre, down = 16383, 8192, 0

    def target(bar, beat, beats, key):
        ref.note(bar * BAR + beat * Q, 1, n(key), 50, beats * Q)

    # Bars 1-4, the default range of 2 semitones (no RPN yet).
    lead.note(0, 0, n("A4"), 95, W)  # A4 bent up a whole step to B4 and back
    lead.bend_ramp(Q, Q, 0, centre, up)
    target(0, 2, 1, "B4")
    lead.bend_ramp(3 * Q, Q - 20, 0, up, centre)
    lead.note(BAR, 0, n("E4"), 95, W)  # E4 dipped down to D4, twice
    for at in (E, 2 * Q + E):
        lead.bend_ramp(BAR + at, E, 0, centre, down)
        lead.bend_ramp(BAR + at + E, E, 0, down, centre)
    lead.note(2 * BAR, 0, n("D4"), 95, W)  # D4 with a vibrato of about a quarter tone, as dense bends
    for i in range(0, W - 40, 10):
        lead.bend(2 * BAR + i, 0, centre + 2048 * math.sin(2 * math.pi * 5 * i / (2 * Q)) * min(1, i / Q))
    lead.bend(3 * BAR - 30, 0, centre)
    lead.phrase(3 * BAR, 0, [("G4", Q), ("A4", Q), ("B4", H, "t")], velocity=90)  # straight notes, centred

    # Bars 5-8: RPN 0 sets the range to 12; A3 slides up an octave to A4, and E4 bends half way (+6, to Bb4).
    lead.bend_range(4 * BAR, 0, 12)
    lead.note(4 * BAR, 0, n("A3"), 95, 2 * W)
    lead.bend_ramp(4 * BAR + 2 * Q, 2 * Q, 0, centre, up)
    target(5, 0, 2, "A4")
    lead.bend_ramp(5 * BAR + 2 * Q, 2 * Q - 20, 0, up, centre)
    lead.note(6 * BAR, 0, n("E4"), 95, W)
    lead.bend_ramp(6 * BAR + Q, Q, 0, centre, centre + 4096)
    target(6, 2, 1, "Bb4")
    lead.bend_ramp(6 * BAR + 3 * Q, Q - 20, 0, centre + 4096, centre)
    lead.phrase(7 * BAR, 0, [("A4", Q), ("G4", Q), ("A4", H, "t")], velocity=90)

    # Bars 9-10: an NRPN with data entry; the range must stay 12, so A3 still slides to A4.
    for number, value in ((99, 32), (98, 32), (6, 64), (38, 0), (99, 127), (98, 127)):
        lead.cc(8 * BAR, 0, number, value)
    lead.note(8 * BAR, 0, n("A3"), 95, 2 * W)
    lead.bend_ramp(8 * BAR + Q, Q, 0, centre, up)
    target(8, 2, 4, "A4")
    lead.bend_ramp(9 * BAR + 2 * Q, Q, 0, up, centre)

    # Bars 11-12: RPN 0 sets the range to 7; D4 bends up a fifth to A4.
    lead.bend_range(10 * BAR, 0, 7)
    lead.note(10 * BAR, 0, n("D4"), 95, 2 * W)
    lead.bend_ramp(10 * BAR + Q, Q, 0, centre, up)
    target(10, 2, 4, "A4")
    lead.bend_ramp(11 * BAR + 2 * Q, Q, 0, up, centre)

    # Bars 13-14: a GM System On resets every channel (the range is 2 again; the programs are set again).
    lead.sysex(12 * BAR, GM_SYSTEM_ON)
    lead.setup(12 * BAR, 0, OVERDRIVE_GUITAR, volume=100)
    ref.setup(12 * BAR, 1, DRAWBAR_ORGAN, volume=60)
    lead.note(12 * BAR + E, 0, n("A4"), 95, 2 * W - E)
    lead.bend_ramp(12 * BAR + Q, Q, 0, centre, up)
    target(12, 2, 4, "B4")
    lead.bend_ramp(13 * BAR + 2 * Q, Q, 0, up, centre)
    return [song, lead, ref]


VERSES = [
    # (syllable, note, ticks); a syllable that ends a word ends with a space
    [("Up ", "G4", E), ("on ", "A4", E), ("the ", "C5", Q), ("moun", "B4", Q), ("tain ", "A4", Q),
     ("an ", "G4", E), ("old ", "E4", E), ("monk ", "G4", Q), ("sings,", "A4", H)],
    [("la ", "C5", Q), ("la ", "B4", Q), ("la ", "A4", E), ("lay, ", "G4", DQ),
     ("and ", "E4", E), ("the ", "F4", E), ("val", "G4", Q), ("ley ", "A4", Q), ("rings.", "G4", Q)],
    [("Ooh ", "E4", H), ("and ", "F4", Q), ("ah, ", "A4", Q),
     ("the ", "G4", E), ("vow", "F4", E), ("els ", "E4", Q), ("turn,", "D4", H)],
    [("round ", "E4", Q), ("and ", "G4", Q), ("round, ", "C5", Q), ("as ", "B4", E), ("the ", "A4", E),
     ("can", "G4", Q), ("dles ", "D4", Q), ("burn.", "C4", H)],
]
VERSE_2_WORDS = [
    ["Down ", "in ", "the ", "vil", "lage ", "the ", "chil", "dren ", "play,"],
    ["la ", "la ", "la ", "lay, ", "at ", "the ", "end ", "of ", "day."],
    ["Ooh ", "and ", "ah, ", "the ", "monk's ", "re", "frain,"],
    ["round ", "and ", "round, ", "then ", "a", "gain, ", "a", "gain."],
]


def lyrics():
    """A sung melody with a Lyric meta event on every note (two verses), over a soft piano."""
    song = conductor("05 Lyrics", 96, [(0, "Verse 1"), (8 * BAR, "Verse 2")])
    voice = Track("Voice")
    voice.setup(0, 0, VOICE_OOHS, volume=100)
    tick = 0
    for verse in (1, 2):
        for line, notes in enumerate(VERSES):
            words = [syllable for syllable, _, _ in notes] if verse == 1 else VERSE_2_WORDS[line]
            for i, (_, key, length) in enumerate(notes):
                if i >= len(words):  # verse 2's line 3 has one syllable fewer: the last note is held over
                    break
                text = words[i]
                if verse == 2 and i == 0:
                    text = "/" + text  # verse 2 starts its lines with "/", the other karaoke convention
                held = sum(length for _, _, length in notes[i:]) if i == len(words) - 1 else length
                voice.lyric(tick, text)
                voice.note(tick, 0, n(key), 90, held * 9 // 10)
                tick += held
            if verse == 1:
                voice.lyric(tick - 1, "\r")  # verse 1 ends its lines with a carriage-return event
    piano = Track("Piano")
    piano.setup(0, 1, PIANO, volume=70)
    bars = ["C3+G3+E4", "A2+E3+C4", "F2+C3+A3", "G2+D3+B3", "C3+G3+E4", "G2+D3+B3", "C3+G3+E4", "G2+D3+B3"]
    chord_hits(piano, 1, 0, bars * 2, (0, 2), 50, H - E)
    for key in ("C3", "G3", "C4", "E4"):
        piano.note(16 * BAR, 1, n(key), 55, W)
    return [song, voice, piano]


def multiport():
    """Two MIDI ports with the same channel numbers: a violin on port 1 channel 1 and a cello on port 2 channel 1,
    each with its own program and bend range, plus drums on port 1 and a piano on port 2."""
    song = conductor("06 Multi-port", 100)
    violin = Track("Port 1 ch 1: violin", port=0)
    violin.setup(0, 0, VIOLIN, volume=100, pan=40)
    violin.phrase(0, 0, [
        ("B4", Q), ("A4", Q), ("G4", H),
        ("G4", Q, "l"), ("A4", Q, "l"), ("B4", H),
        ("C5", Q), ("B4", Q), ("A4", Q), ("G4", Q),
        ("F#4", H), ("A4", H),
        ("B4", DQ), ("C5", E), ("B4", Q), ("A4", Q),
        ("G4", H), ("E4", H),
        ("E4", Q), ("G4", Q), ("C5", Q), ("A4", Q),
        ("A4", W, "t"),
        ("D5", Q), ("B4", Q), ("G4", Q), ("B4", Q),
        ("C5", Q), ("B4", Q), ("A4", Q), ("G4", Q),
        ("A4", Q), ("C5", Q), ("B4", Q), ("A4", Q),
        ("G4", W, "t"),
    ], velocity=88)
    # Bar 8: the violin keeps the default range, so this bend is a whole step (A4 to B4).
    violin.bend_ramp(7 * BAR + Q, Q, 0, 8192, 16383)
    violin.bend_ramp(7 * BAR + 3 * Q, Q - 20, 0, 16383, 8192)

    drums = Track("Port 1 ch 10: drums", port=0)
    drums.setup(0, DRUMS, 0, volume=90)
    drum_bars(drums, 0, 12, crash_bars=(0,), hats=4)

    cello = Track("Port 2 ch 1: cello", port=1)
    cello.setup(0, 0, CELLO, volume=105, pan=90)
    cello.bend_range(0, 0, 12)  # only port 2's channel 1 bends by up to an octave
    cello.phrase(0, 0, [
        ("G3", H), ("D3", H),
        ("E3", H), ("B2", H),
        ("C3", H), ("E3", H),
        ("D3", H), ("F#3", H),
        ("G3", W),
        ("E3", W, "t"),
        ("C3", H), ("G3", H),
        ("D3", W),
        ("G3", H), ("B3", H),
        ("E3", H), ("G3", H),
        ("C3", H), ("D3", H),
        ("G2", W, "t"),
    ], velocity=85)
    # Bar 6: E3 slides up an octave to E4 and back, with port 2's range of 12.
    cello.bend_ramp(5 * BAR + Q, Q, 0, 8192, 16383)
    cello.bend_ramp(5 * BAR + 3 * Q, Q - 20, 0, 16383, 8192)

    piano = Track("Port 2 ch 2: piano", port=1)
    piano.setup(0, 1, PIANO, volume=65)
    chord_hits(piano, 1, 0, ["G3+B3+D4", "E3+G3+B3", "C3+E3+G3", "D3+F#3+A3"] * 3, (0, 2), 50, H - E)
    return [song, violin, drums, cello, piano]


FILES = {
    "01_melody.mid": melody,
    "02_chords.mid": chords,
    "03_band.mid": band,
    "04_bends.mid": bends,
    "05_lyrics.mid": lyrics,
    "06_multiport.mid": multiport,
}


# --- A small reader, for --list ----------------------------------------------------------------------------------


def read_smf(path):
    """(ppq, tracks), each track a list of (tick, status, data) with running status expanded."""
    data = path.read_bytes()
    assert data[:4] == b"MThd"
    ppq = int.from_bytes(data[12:14], "big")
    at = 8 + int.from_bytes(data[4:8], "big")
    tracks = []

    def read_vlq(pos):
        value = 0
        while True:
            byte = data[pos]
            pos += 1
            value = (value << 7) | (byte & 0x7F)
            if not byte & 0x80:
                return value, pos

    while at < len(data):
        size = int.from_bytes(data[at + 4:at + 8], "big")
        pos, stop, tick, status, events = at + 8, at + 8 + size, 0, 0, []
        while pos < stop:
            delta, pos = read_vlq(pos)
            tick += delta
            if data[pos] & 0x80:
                status = data[pos]
                pos += 1
            if status == 0xFF:
                kind = data[pos]
                length, pos = read_vlq(pos + 1)
                events.append((tick, 0xFF, bytes([kind]) + data[pos:pos + length]))
                pos += length
            elif status in (0xF0, 0xF7):
                length, pos = read_vlq(pos)
                events.append((tick, status, data[pos:pos + length]))
                pos += length
            else:
                count = 1 if status & 0xF0 in (0xC0, 0xD0) else 2
                events.append((tick, status, data[pos:pos + count]))
                pos += count
        tracks.append(events)
        at = stop
    return ppq, tracks


def describe(path):
    """A summary of a file: its ports, and each port's channels with their notes, programs, bends and RPN 0s."""
    ppq, tracks = read_smf(path)
    tempo = 500_000
    lines, channels, lyrics, sysexes, end = [], {}, 0, 0, 0
    for events in tracks:
        port = 0
        rpn = {}
        for tick, status, data in events:
            end = max(end, tick)
            if status == 0xFF:
                if data[0] == 0x21:
                    port = data[1]
                elif data[0] == 0x05:
                    lyrics += 1
                elif data[0] == 0x51:
                    tempo = int.from_bytes(data[1:4], "big")
                continue
            if status == 0xF0:
                sysexes += 1
                continue
            info = channels.setdefault((port, status & 0x0F), {"notes": 0, "programs": [], "bends": 0, "rpn0": []})
            kind = status & 0xF0
            if kind == 0x90 and data[1] > 0:
                info["notes"] += 1
            elif kind == 0xC0:
                info["programs"].append(data[0])
            elif kind == 0xE0:
                info["bends"] += 1
            elif kind == 0xB0:
                number, value = data
                key = (port, status & 0x0F)
                if number in (101, 100):
                    rpn.setdefault(key, {})[number] = value
                    rpn[key].pop("nrpn", None)
                elif number in (99, 98):
                    rpn.setdefault(key, {})["nrpn"] = True
                elif number == 6 and rpn.get(key, {}).get(101) == 0 and rpn[key].get(100) == 0 \
                        and not rpn[key].get("nrpn"):
                    info["rpn0"].append(value)
    seconds = end / ppq * tempo / 1_000_000
    ports = sorted({port for port, _ in channels})
    lines.append(f"{path.name}: {len(tracks)} tracks, about {seconds:.0f} s, file ports {ports}, "
                 f"{lyrics} lyric events, {sysexes} SysEx")
    for (port, channel), info in sorted(channels.items()):
        name = f"{ports.index(port) + 1}.{channel + 1}" if len(ports) > 1 else f"{channel + 1}"
        lines.append(f"  channel {name:>4}: {info['notes']:3} notes, programs {info['programs']}, "
                     f"{info['bends']} bends, RPN 0 ranges {info['rpn0']}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=pathlib.Path,
                        default=pathlib.Path(__file__).resolve().parents[2] / "tests" / "midi",
                        help="the folder to write into (default: tests/midi at the top level)")
    parser.add_argument("--list", action="store_true", help="print a summary of each file written")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for name, make in FILES.items():
        path = args.out / name
        write_smf(path, make())
        print(f"wrote {path}")
        if args.list:
            print(describe(path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
