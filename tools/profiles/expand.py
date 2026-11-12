"""Expand Delay Lama Everything imitation profiles into DelayLamaVoice `set` lines.

profiles/imitation.json holds the syllable table, the profiles (with
`extends`) and the program map; docs/IMITATION.md sections 7 and 13 are the
spec. midis2jam2's router does the same expansion (`ImitationProfiles.kt`,
whose test compares it with `--dump`; change both together); this tool serves
render scripts and tuning, and fixes the expansion order:
the `extends` chain, then the syllable, then the profile's own numbers.

  py tools/profiles/expand.py guitar.overdrive     # set lines for a profile
  py tools/profiles/expand.py --program 29         # by GM program (0-based)
  py tools/profiles/expand.py --list
  py tools/profiles/expand.py --dump [file.json]   # every profile's lines and the program
                                                   # map as JSON (midis2jam2's
                                                   # DelayLamaProfilesTest compares them)
"""

import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_PATH = ROOT / "profiles" / "imitation.json"
# 'colour' holds an onset token's vowel for reference only: onsets are steady
# unless a profile gives onset.vowel itself.
META = ("extends", "syllable", "comment", "colour")
# The keys syllable tokens set, at their built-in defaults (None = null).
SYLLABLE_DEFAULTS = {
    "onset": {"vowel": None, "time": 0, "curve": 3, "attack": 0, "lips": 0, "burst": None,
              "burst_time": 0},
    "body": {"vowel": None},
    "ending": {"vowel": None, "vowel_time": None, "release": 20, "lips": 0},
    "phrase": {"dip_level": 0.2},
}


def load(path=DEFAULT_PATH):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def merge(base, extra):
    """Section-wise merge: extra's numbers override base's."""
    out = copy.deepcopy(base)
    for section, values in extra.items():
        if section in META:
            continue
        if isinstance(values, dict):
            out.setdefault(section, {}).update(values)
        else:
            out[section] = values
    return out


def onset_token(data, token, seen=()):
    table = data["syllables"]["onsets"]
    if token not in table:
        raise KeyError(f"unknown onset '{token}'")
    if token in seen:
        raise ValueError(f"onset '{token}' extends itself")
    entry = table[token]
    base = onset_token(data, entry["extends"], seen + (token,)) if "extends" in entry else {}
    return merge(base, entry)


def syllable(data, text):
    """'onset-nucleus[-ending]' -> sections. The nucleus may be 'a>b' (b is the
    body drift target); '-u' or 'u' is a soft start with no onset."""
    vowels = data["syllables"]["vowels"]
    endings = data["syllables"]["endings"]
    parts = text.split("-")
    onset = nucleus = ending = None
    if len(parts) == 1:
        nucleus = parts[0]
    elif len(parts) == 2:
        if parts[0] == "" or parts[0].split(">")[0] in vowels and parts[1] in endings:
            nucleus, ending = (parts[1], None) if parts[0] == "" else (parts[0], parts[1])
        else:
            onset, nucleus = parts
    elif len(parts) == 3:
        onset, nucleus, ending = parts
    else:
        raise ValueError(f"bad syllable '{text}'")
    # A syllable sets every key a syllable controls, so nothing of a parent's
    # syllable leaks through (an "h-u" flute extending a "d-a" default must
    # not keep the d's onset vowel).
    out = copy.deepcopy(SYLLABLE_DEFAULTS)
    if onset:
        out = merge(out, onset_token(data, onset))
    first, _, drift = nucleus.partition(">")
    if first not in vowels or (drift and drift not in vowels):
        raise KeyError(f"unknown vowel in '{text}'")
    out = merge(out, {"nucleus": {"vowel": vowels[first]}})
    if drift:
        out = merge(out, {"body": {"vowel": vowels[drift]}})
    if ending:
        if ending not in endings:
            raise KeyError(f"unknown ending '{ending}'")
        out = merge(out, endings[ending])
    return out


def resolve(data, name, seen=()):
    """A profile's sections with every value resolved."""
    profiles = data["profiles"]
    if name not in profiles:
        raise KeyError(f"unknown profile '{name}'")
    if name in seen:
        raise ValueError(f"profile '{name}' extends itself")
    entry = profiles[name]
    out = resolve(data, entry["extends"], seen + (name,)) if "extends" in entry else {}
    if "syllable" in entry:
        out = merge(out, syllable(data, entry["syllable"]))
    return merge(out, entry)


def profile_for_program(data, program, bank=0):
    """Map entries with a bank match first, then plain program entries, then
    'default' (IMITATION.md 14)."""
    for entry in data["map"]:
        if "bank" in entry and entry["bank"] == bank and program in entry["programs"]:
            return entry["profile"]
    for entry in data["map"]:
        if "bank" not in entry and program in entry["programs"]:
            return entry["profile"]
    return "default"


def fit_shift(sections, notes):
    """range.shift (semitones) for a channel from its written note numbers
    (one per note-on), as the router computes it (IMITATION.md 7.1).
    fit 2 (default): down by whole octaves while the median is above
    range.high, never up, so parts already in range sing as written.
    fit 1: whole octaves putting the median nearest range.target. 0: none."""
    rng = sections.get("range", {})
    fit = rng.get("fit", 0)
    if not fit or not notes:
        return 0
    ordered = sorted(n + 12 * rng.get("octave", 0) for n in notes)
    median = ordered[len(ordered) // 2]
    if fit >= 2:
        shift = 0
        while median + shift > rng.get("high", 72):
            shift -= 12
        return shift
    return 12 * round((rng.get("target", 57) - median) / 12)


def set_lines(sections, staged=True):
    """`set` lines for DelayLamaVoice; null values go as -1. Staged lines
    reset to the built-in defaults first and switch atomically."""
    lines = ["set profile.begin 1", "set profile.reset 1"] if staged else []
    for section, values in sections.items():
        for key, value in values.items():
            lines.append(f"set {section}.{key} {-1 if value is None else value:g}")
    if staged:
        lines.append("set profile.apply 1")
    return lines


def main(argv):
    data = load()
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--list":
        print("\n".join(data["profiles"]))
        return 0
    if argv[0] == "--dump":
        if len(argv) > 1:
            data = load(argv[1])
        dump = {
            "profiles": {name: set_lines(resolve(data, name)) for name in data["profiles"]},
            "map": {str(program): profile_for_program(data, program) for program in range(128)},
        }
        print(json.dumps(dump, indent=1))
        return 0
    name = profile_for_program(data, int(argv[1])) if argv[0] == "--program" else argv[0]
    print(f"# profile {name}")
    print("\n".join(set_lines(resolve(data, name))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
