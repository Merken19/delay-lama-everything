Delay Lama Everything {{VERSION}} for Windows (64-bit)
=====================================================

midis2jam2 with Delay Lama: it plays MIDI files in 3D and lets Delay Lama
monks sing the channels you choose, imitating each channel's instrument.

Run
---

1. Unzip this folder anywhere you can write to (for example your Documents).
2. Start midis2jam2.exe.
3. Choose a MIDI file on the home tab, open the Delay Lama card, switch on the
   channels the monks should sing, then press Play. Each sung channel gets its
   own always-on-top window of monks.
4. "Add Delay Lama" on that panel opens DelayLamaStandalone.exe, a Delay Lama
   you play by hand with the mouse or a MIDI keyboard.

midis2jam2 finds DelayLamaVoice.exe, DelayLamaStandalone.exe and
profiles\imitation.json next to midis2jam2.exe. The panel's options can point
to other copies instead.

Nothing is installed: delete the folder to remove it. midis2jam2 keeps its
settings in your user profile; the standalone keeps its own in
%APPDATA%\DelayLamaStandalone\settings.ini.

What is in this folder
----------------------

midis2jam2.exe, app\, runtime\   midis2jam2 and the Java runtime it runs on
DelayLamaVoice.exe               the singing helper, one per sung channel
DelayLamaStandalone.exe          Delay Lama to play by hand
Resources\                       AudioNerdz' Delay Lama artwork and manual
profiles\imitation.json          how the monks imitate each instrument
licenses\, NOTICE.txt            licenses and where the source code is
source\                          our changes to midis2jam2, as a patch

Requirements: Windows 10 or 11, 64-bit, OpenGL graphics. The monks are not
in midis2jam2's video recordings.

Built {{BUILT}}.
