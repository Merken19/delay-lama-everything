"""Fix MIDI files whose drum notes are Guitar Pro 7 articulation numbers.

Some exported MIDI files (seen in tab-site downloads) write each drum hit's
Guitar Pro 7 articulation index (0 = snare hit, 3 = closed hi-hat,
8 = kick, 22 = crash high, ...) on channel 10 instead of its General MIDI
key. Most soundfonts leave those low keys empty, so the kick, snare and
hi-hat go silent; XG-style soundfonts such as Timbres of Heaven put sound
effects there instead (key 22 is a metronome beep).

This script finds such files in a folder and writes fixed copies to another
folder. It only changes the key byte of channel-10 note-on, note-off and
key-pressure events, so timing, lengths and every other event stay as they
were. Files whose drums already use General MIDI keys are skipped.

The index -> key table follows the Guitar Pro 7 drum kit order, as listed
in alphaTab's PercussionMapper.instrumentArticulations (outputMidiNumber).

Usage:
    py tools\\drumfix\\fix_gp_drums.py <input folder> <output folder> [--force]

--force fixes every file with drum notes, not only the ones detected.
"""

import os
import struct
import sys

# Guitar Pro 7 articulation index -> General MIDI drum key.
GP7_TO_GM = [
    38, 37, 38, 42, 46, 46, 44, 35, 36, 50,   # 0-9: snare hit/side stick/rim shot, hi-hat closed/half/open, pedal hi-hat, kicks, tom very high
    48, 47, 45, 43, 51, 51, 53, 51, 55, 55,   # 10-19: toms, ride edge/middle/bell/choke, splash hit/choke
    52, 52, 49, 49, 57, 57, 56, 56, 56, 56,   # 20-29: china, crash high, crash medium, cowbells
    56, 56, 77, 76, 60, 60, 60, 61, 61, 61,   # 30-39: cowbell high, woodblocks, bongos
    66, 65, 68, 67, 64, 64, 64, 63, 63, 62,   # 40-49: timbales, agogos, congas
    72, 71, 73, 74, 86, 87, 54, 54, 54, 54,   # 50-59: whistles, guiro, surdo, tambourine
    79, 78, 58, 81, 80, 43, 49, 49, 69, 69,   # 60-69: cuica, vibraslap, triangle, grancassa, piatti, cabasa
    85, 75, 70, 70, 70, 70, 82, 82, 53, 53,   # 70-79: castanets, claves, maracas, shaker, bell tree
    53, 53, 62, 62, 39, 40, 40, 41, 59, 59,   # 80-89: jingle/tinkle bell, golpe, hand clap, electric snare, sticks, floor tom, ride 2
    59, 59, 49, 37, 38,                       # 90-94: ride 2, reverse cymbal, metronome
]

# General MIDI drum keys start at 35 (27 with the GS extras). A file whose
# drums put this share of hits below 27 is taken to use articulation numbers.
LOW_KEY_SHARE = 0.10


def vlq(data, i):
    value = 0
    while True:
        b = data[i]
        i += 1
        value = (value << 7) | (b & 0x7F)
        if b < 0x80:
            return value, i


def drum_key_offsets(data):
    """Byte offsets of the key byte of every channel-10 note event."""
    if data[:4] != b"MThd":
        raise ValueError("not a standard MIDI file")
    i = 8 + struct.unpack(">I", data[4:8])[0]
    offsets = []
    while i + 8 <= len(data):
        kind = data[i:i + 4]
        length = struct.unpack(">I", data[i + 4:i + 8])[0]
        j, end = i + 8, i + 8 + length
        i = end
        if kind != b"MTrk":
            continue
        status = None
        while j < end:
            _, j = vlq(data, j)
            b = data[j]
            if b == 0xFF:
                length, j = vlq(data, j + 2)
                j += length
                status = None
                continue
            if b in (0xF0, 0xF7):
                length, j = vlq(data, j + 1)
                j += length
                status = None
                continue
            if b & 0x80:
                status = b
                j += 1
            if status is None:
                raise ValueError("running status with no status byte")
            kind_nibble = status & 0xF0
            size = 1 if kind_nibble in (0xC0, 0xD0) else 2
            if status & 0x0F == 9 and kind_nibble in (0x80, 0x90, 0xA0):
                offsets.append(j)
            j += size
    return offsets


def fix(data, force=False):
    """Return (fixed bytes or None, number of hits, number remapped)."""
    offsets = drum_key_offsets(data)
    if not offsets:
        return None, 0, 0
    low = sum(1 for o in offsets if data[o] < 27)
    if not force and low / len(offsets) < LOW_KEY_SHARE:
        return None, len(offsets), 0
    out = bytearray(data)
    changed = 0
    for o in offsets:
        key = data[o]
        if key < len(GP7_TO_GM):
            out[o] = GP7_TO_GM[key]
            changed += 1
    return bytes(out), len(offsets), changed


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    force = "--force" in argv
    if len(args) != 2:
        print(__doc__)
        return 2
    src, dst = args
    os.makedirs(dst, exist_ok=True)
    for name in sorted(os.listdir(src)):
        if not name.lower().endswith((".mid", ".midi")):
            continue
        path = os.path.join(src, name)
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as f:
            data = f.read()
        try:
            fixed, events, changed = fix(data, force)
        except (ValueError, IndexError, struct.error) as e:
            print(f"skip  {name}: unreadable ({e})")
            continue
        if fixed is None:
            print(f"ok    {name}: drums already use General MIDI keys" if events else f"ok    {name}: no drums")
            continue
        with open(os.path.join(dst, name), "wb") as f:
            f.write(fixed)
        print(f"fixed {name}: {changed} of {events} drum note events remapped")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
