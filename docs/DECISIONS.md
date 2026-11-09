# Decisions

Each decision is settled. Reopen one only when the user asks. The IDs stay
fixed because code comments cite them; gaps are retired numbers (list at
the bottom). Rows named O… were open items that the user has since
confirmed, and they keep their IDs. An open item carries a proposal that a
session may follow, saying so.

## Scope and repositories

| # | Decision | Date, by |
| --- | --- | --- |
| D6 | **No recording.** midis2jam2's video recording stays as it is, and the sung channels are missing from it. | 2026-11-03, user |
| D7 | **Add Delay Lama opens `DelayLamaStandalone.exe`** for free play by hand. It is not tied to the playing file, and the file's monks are not interactive. | 2026-11-03, user |
| O13 | **The standalone stays unchanged.** Every Add Delay Lama opens one more instance, and the instances share `settings.ini` and its window geometry. | 2026-11-08, user |
| D61 | **v1 scope.** v1 is the chosen channels sung by monk choirs in always-on-top windows, imitating their instruments, plus the launcher's Delay Lama panel, the mixer with its Delay Lama switch, Add Delay Lama and one Windows zip. Monks inside the 3D scene (phase 5) come after v1. Lyrics are out of scope altogether. | 2026-11-08, user |
| D62 | **Forks and remotes** (settles O1). midis2jam2 is forked to the user's GitHub, with our work on its `delay-lama` branch. `DelayLamaVoice` stays on the `voice-helper` branch of Merken19/delalalalay-lama. The top-level repo (branch `main`, `external/` ignored) is committed to `main` when the user confirms, which is the user's call. It gets a remote when the user wants one. Nothing is pushed unless the user asks. The fork itself is not created yet. | 2026-11-08, user |
| D64 | **Add Delay Lama is also in the mixer** (settles O8). The launcher's card and panel keep their button. The Delay Lama mixer, the window that is open while a file plays (D58), gets one too. There is no key in the 3D window. The user called it "the Delay Lama preferences window", which this reads as the mixer. Not built yet. | 2026-11-08, user |

## The helper and its protocol

| # | Decision | Date, by |
| --- | --- | --- |
| D1 | **One helper process per sung channel.** `DelayLamaVoice.exe` is a native Win32 program built from the delalalalay-lama sources (same DSP, monk artwork and WinMM audio). midis2jam2 starts it and streams the channel's events over a pipe. | 2026-11-03, user |
| D2 | **The monks are shown in their own windows**, which are always on top. In-scene monks come after v1 (D61). | 2026-11-03, user |
| D3 | **Chords are sung by a monk choir.** Each simultaneous note on a channel goes to another monk, up to a per-channel limit. A limit of 1 gives a single monk. | 2026-11-03, user |
| O3 | **Choir size and stealing.** The default is 4 monks per channel, settable from 1 to 8. When every monk is busy, the oldest note is stolen, but never the current highest or lowest one. | 2026-11-08, user (confirmed) |
| O4 | **One window per channel**, with its monks side by side. | 2026-11-08, user (confirmed) |
| D5 | **Pitch bend in a file is pitch bend**, not the standalone's vowel wheel. The bend range follows RPN 0 (default ±2 semitones; the DSP allows ±12). | 2026-11-03, Claude |
| D8 | **Helper loudness (plain mode).** Velocity, CC7 and CC11 each scale a monk's level on the GM curve (squared), times a per-channel `gain` (default 1). The default volume is 0.09, about 16 dB below the standalone, so four monks at full velocity and CC7 127 stay just under full scale. | 2026-11-03, Claude; user ear-checked |
| D9 | **Protocol 0 details.** `hello` is optional and `ready` answers it. A bad line gets `error ...` and is skipped. `wait <ms>` is for scripts and `--render`. The helper exits on `quit` or at the end of stdin, with exit codes 0, 1 (startup) and 2 (command line, protocol version). | 2026-11-03, Claude |
| D10 | **Closing a monk window hides it.** The helper keeps running and the window can be shown again from the mixer (D58). Revised by the user on 2026-11-08 and not built yet: today a closed window ends its helper, and the channel goes silent. | 2026-11-08, user |
| D11 | **Choir allocation.** A note goes to the lowest-numbered silent monk, so a melody stays on the first monk, or else to the monk released longest ago. Notes held only by the sustain pedal are stolen first, and a stolen monk glides to its new note. CC 1, 5, 12 and 13 are not routed to the DSP. | 2026-11-03, Claude |
| D17 | **Choir monks vary subtly**: voice size ±0.03, vibrato rate ±8 %, their own vibrato seeds, and a stereo position that matches their place in the window. | 2026-11-03, user |
| D27 | **A released monk's level never rises** (plain mode). After a note-off the DSP still plays its last grains, so a raised gain or CC11 would replay them loud. | 2026-11-04, Claude |
| D28 | **Protocol 1 details.** `hello` accepts 0 and 1, and `ready` answers in the version asked for. `on` takes an optional note length (-1 = unknown). `next` and the profile keys need profile mode, where protocol 0's sound keys are refused; `gain` and `volume` work in both modes. New `set` keys are added within protocol 1, and an older helper answers `error` and plays on. | 2026-11-04, Claude |
| D35 | **Profile-mode level headroom.** The helper raises each synth's DSP volume by up to 4× and lowers the articulator's levels by the same factor, so levels above 1 work and the sound is unchanged. | 2026-11-04, Claude |
| D59 | **The helper runs one priority step up, with power throttling off**, so its audio keeps up when its window is covered or off screen. The user confirmed this fixed the silent monks. | 2026-11-08, Claude; user confirmed |

## Imitation

| # | Decision | Date, by |
| --- | --- | --- |
| D4 | **Vowel and articulation imitate the instrument**, the way a person imitates one with their mouth. Per-instrument profiles use all of Delay Lama's parameters ([IMITATION.md](IMITATION.md)). | 2026-11-03, user |
| D12 | **Profiles are numbers plus a syllable shorthand** ("d-a-ng"), which expands to numbers. Explicit numbers override the syllable. | 2026-11-03, user |
| D13 | **Musical character with an exaggeration amount** (0–2, default 1) that scales scoops, vowel swings, vibrato, falls and dips. It is one value for every channel. | 2026-11-03, user; one value 2026-11-08 |
| D14 | **Sing the written pitch.** The helper adds back the octave that the DSP drops. High parts fold down (D37). | 2026-11-04, user |
| D16 | **The mouth shows the sung vowel**, plus closed lips during closures (b, m and w onsets, dips, "m" endings, very low levels). | 2026-11-03, user |
| D18 | **DSP additions must be add-only**, and their defaults must keep today's sound (the macOS build shares `DSP/`). | 2026-11-03, user |
| D19 | **The profile data is `profiles/imitation.json`**: syllable table, profiles (with `extends`) and the program/bank map. midis2jam2 expands it and sends numeric `set` keys, staged with `profile.begin` and `profile.apply`. | 2026-11-03, Claude |
| D20 | **The articulator owns the sound in profile mode.** It runs 1 ms ticks. Legato uses the DSP's own glide, which is set to 0 for new and re-articulated notes. The DSP envelope is unused and the helper runs one echo on the choir mix. Plain mode keeps phase 1's sound. | 2026-11-04, Claude; glide by the user |
| D21 | **Moderate velocity curve.** In profile mode the level follows (velocity/127)^1, while CC7 and CC11 keep the GM curve. | 2026-11-04, user |
| D22 | **No noise layer.** Consonants stay pure Delay Lama. | 2026-11-04, user |
| D23 | **Drums stay with Gervill.** Rhythm channels are not offered and there is no beatbox monk. | 2026-11-04, user |
| D24 | **Most profiles have no echo** (`space.echo` 0), and the vibrato floor stays as it is. Sung leads use depth 0.15 (DSP units). | 2026-11-04, user |
| D25 | **Palette defaults.** Breath is 0.75. Vowel moves take about 100 ms for "wa" and 400 ms for "yeow" (25 ms sounds unnatural), and hard consonants may step. Breath bursts are colour only, and voice size is a subtle control. DSP glides of 0.5 and 0.15 both sound natural. | 2026-11-04, user |
| D26 | **`onset.mask` is an experiment key, default 0.** It fixed no glitch by ear. | 2026-11-04, user |
| D29 | **A syllable sets every key that syllables control.** The keys its tokens don't name are reset to defaults, so a parent profile's syllable never leaks into a child's. | 2026-11-04, Claude |
| D33 | **Onsets are steady.** Any vowel move at a note's start is heard as a glitch, whether brighter or darker. Onset tokens keep their vowel only as `colour`, and a profile opts in with an explicit `onset.vowel`. Consonants come from attack, dip, lips and scoop. | 2026-11-04, user |
| D37 | **High parts fold down by octaves.** With `range.fit` 2 and `range.high` 72, the router shifts a channel down by whole octaves, per channel and profile, while the median of its notes is above C5. It never shifts up, so a line keeps its shape. | 2026-11-05, user (fold); Claude (per channel) |
| D38 | **`onset.bandwidth` and `onset.after_rest` are experiment keys, default off.** They saved no consonant by ear. | 2026-11-05, user |
| D39 | **Violins sing.** GM 41–42 map to `lead.singer` ("ah", folded), which beat the violin imitation in K525. `strings.violin` stays for picking per channel, without glides. | 2026-11-05, user |
| D40 | **The bass sings "doo" on a held "oo".** `bass.finger` is "d-oo-m" with `nucleus.pitch_track` 0. Pitch tracking had darkened it to "u". | 2026-11-05, user |
| D41 | **Profile mode is the default.** A channel takes the profile that its program and bank map to (`profile=auto`). `profile=plain` gives phase 2's sound and `profile=<name>` gives one profile for all channels. The router says `hello 1` and sends each note's length. The map's `bank` is MSB × 128 + LSB. Without a profile file the helpers sing plain. | 2026-11-05, Claude |
| D42 | **String ensembles 1–2 (GM 49–50) sing as `lead.singer` too**, so a chordal part becomes a small choir of singers. `strings.ensemble` keeps GM 45–46 and 51–52. | 2026-11-05, user |
| D46 | **`vibrato.lock`** (default 0) lets a chord's monks share one vibrato LFO so its intervals hold. It needs a DSP addition. No profile uses it (D56). | 2026-11-05, Claude |
| D48 | **The piano ends on its vowel, with no "ng"** ("d-i>e"). The "ng" sweep was heard as a high pitch at note ends. | 2026-11-06, user |
| D49 | **Timbre and level keys**: `voice.formant1`–`3` (0–2; each formant's frequencies times the factor, 0 silences it) and `dyn.gain` (0–4, the profile's level factor). They need a DSP addition. | 2026-11-07, Claude |
| D56 | **4c picks so far.** `piano` as D48 left it (no lock, 900 ms decay). `flute`: `voice.formant3` 0, breath 0.3, `phrase.mode` 0 with glide 0.1, `dyn.gain` 1.8. `trumpet` and `sax.tenor` unchanged; the user accepts the glitch heard in their band clip. Slow flute slurs stay legato, with no new key. | 2026-11-08, user |
| D63 | **Levels by measurement.** In 4c Claude sets each profile's level (`dyn.gain` and the like) by rendering it against Gervill and matching loudness (ITU-R BS.1770, gated) at the live balance. The user's ear is not asked about loudness. Ear checks stay for how a sound sounds (timbre, glitches). | 2026-11-08, user |

## midis2jam2

| # | Decision | Date, by |
| --- | --- | --- |
| O2 | **Delay Lama is chosen per channel** (port + channel), with every program the channel uses shown. The profile follows program changes. | 2026-11-08, user (confirmed) |
| O7 | **A sung channel's 3D instrument is hidden**, and `keep3d` keeps it. The switch brings it back while it is off (D60). | 2026-11-08, user (confirmed) |
| O12 | **Choices are remembered per file**, keyed by the SHA-256 of its contents, in the preferences node `org/wysko/midis2jam2/delaylama`. | 2026-11-08, user (confirmed) |
| D30 | **Delay Lama offset**: 175 ms on Gervill by default and 0 on other devices, settable with `offset=<ms>`. A helper sounds 169 ms before Gervill (loopback measurement). | 2026-11-04, Claude; user OK 2026-11-08 |
| D31 | **The seek chase rebuilds RPNs and NRPNs** as parameter number then data (`ParameterChase`), so the bend range survives a seek. Catalogued as `playback.seek.parameters`. | 2026-11-04, Claude |
| D34 | **Balance: the monks sit 6 dB louder against the band** than plain playback had them, at the same overall loudness. | 2026-11-04, user |
| D36 | **The balance is a gain on Gervill's audio line.** While any channel is sung, every Gervill plays `balance` dB quieter (0–30, default 6), set through the master gain of the Java Sound line it opened (`LineGain`). The gain sits after Gervill's limiter, so resets, seeks and master volume messages can't undo it. Other MIDI devices get no balance. The whole mix is about 4.4 dB quieter, which the user accepts. | 2026-11-04, Claude; user confirmed |
| D43 | **The Delay Lama panel is English only** (`DelayLamaText`). | 2026-11-05, Claude; user OK 2026-11-08 |
| D44 | **Where the choices come from.** From the home tab: the panel (the environment variable is ignored). From the command line: `MIDIS2JAM2_DELAY_LAMA` if set, else the panel's remembered choices. Queue, recordings and Gradle tools: the variable. Choir, level and imitation are per channel; balance, offset, exaggeration, `keep3d` and the three paths apply to every file. | 2026-11-05, Claude |
| D45 | **A new channel starts off (not sung)**, with one monk per note it plays at once (up to 4) and imitation set to auto. | 2026-11-05, Claude |
| D47 | **On Windows, Fullscreen opens as borderless while Delay Lama sings**, because a real fullscreen window covers the topmost monk windows. Catalogued as `delaylama.windows.fullscreen-as-borderless`. | 2026-11-05, user |
| D57 | **Monk windows are laid out on the main screen.** They fill the work area in columns from the left, and all of them shrink alike (down to 35 %) when the columns don't fit across. The mixer's width stays free. Each window is named after its channel's instruments, in its title and in a label strip. | 2026-11-08, user asked; Claude |
| D58 | **The Delay Lama mixer.** A launcher performance with sung channels opens an always-on-top mixer with a strip per channel: mute, solo, volume from -30 to +6 dB, and Reset. A sung channel's level goes to its helper as `set gain`, and any other channel's scales its CC 7. The mix is not remembered. | 2026-11-08, user asked; Claude |
| D60 | **The Delay Lama switch** in the mixer: monks or midis2jam2's own sound for the sung channels, never both, switched by levels alone (helper `set gain`, the synthesizer's CC 7, Gervill's line gain) at the same moment, mid-note too. Off also hides the monk windows (`set window.visible`) and puts the sung channels' 3D instruments on stage. It is on at start and not remembered. Without a mixer nothing changes. | 2026-11-08, user asked; Claude |

## Packaging

| # | Decision | Date, by |
| --- | --- | --- |
| D55 | **The Windows package is a zip** of midis2jam2's jpackage app image (`createDistributable`, every JDK module). The Delay Lama exes, `Resources/` (all AudioNerdz files) and `profiles/imitation.json` sit beside `midis2jam2.exe`. The runtime is the local Oracle JDK 21.0.1. Until the fork is public (D62), the GPL source is the upstream commit named in `NOTICE.txt` plus `source/midis2jam2-delay-lama.patch`. | 2026-11-07, Claude; zip and runtime confirmed by the user 2026-11-08 |

## Open, with proposals

| # | Question | Proposal |
| --- | --- | --- |
| O19 | Which 4c families need an ear check? | Every remaining family gets a measured pass against Gervill: levels by D63, plus fixes for what measurement shows (buzz, whistles, decay). An ear check is asked only where a choice of sound is left. Synth FX, ethnic, percussive and sound effects (GM 97–128) keep their first-guess syllables, with measured levels. |

## Retired numbers

D15 (lyrics later) and D2's in-scene half became D61, D32 (environment-only config) became D44, and the second D8 (top-level repo) became D62. D50–D54 were never used. Former open items: O1 → D62, O5 → D23, O6 → D14, O8 → D64, O9 → D47, O10 → D34/D36, O11 → D30, O14 → D21, O15 → D22, O16 → D24, O17 → D40, O18 → D42.
