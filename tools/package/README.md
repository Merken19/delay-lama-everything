# Windows package

`make_package.ps1` builds Delay Lama Everything's Windows package: one folder,
zipped, that runs without this source tree.

```powershell
.\tools\package\make_package.ps1                    # builds midis2jam2, collects, zips
.\tools\package\check_package.ps1                   # unzips the newest zip and checks it headlessly
```

Output: `dist\DelayLamaEverything\` and
`dist\DelayLamaEverything-<date>-windows-x64.zip` (about 190 MB without the
bundle; with the current one, a 420 MB soundfont, about 530 MB; `dist/` is
git-ignored).

## What it does

1. Builds midis2jam2's jpackage app image with Compose Desktop's
   `:app:createDistributable` (from `external\midis2jam2` as checked out, with
   `JAVA_HOME` = JDK 21 and `ANDROID_HOME`). The image is `midis2jam2.exe`,
   `app\` (the jars) and `runtime\` (a JDK 21 runtime with every module,
   `includeAllModules` in `app/build.gradle.kts`). Upstream releases use
   install4j instead, which isn't available here.
2. Adds `runtime\bin\java.exe` and `javaw.exe` from the same JDK (jlink leaves
   them out; recording starts its renderer with them). It refuses if the
   runtime wasn't made from that JDK.
3. Copies `DelayLamaVoice.exe`, `DelayLamaStandalone.exe` and all of
   `Resources\` from `external\delalalalay-lama\Windows\build\Release\`. It
   doesn't build them unless you pass `-BuildDelayLama`; a locked exe is
   retried for a minute.
4. Copies `profiles\imitation.json`, the licenses (`licenses\`: midis2jam2
   GPL-3.0 and its third-party notices, delalalalay-lama MIT, MonkSynth MIT)
   and writes `NOTICE.txt` and `README.txt` from `package-NOTICE.txt` and
   `package-README.txt` here, filling in the commits.
5. Writes `source\midis2jam2-delay-lama.patch`: every change on midis2jam2's
   checkout against upstream (`git merge-base HEAD origin/master`), committed
   or not, new files included. `NOTICE.txt` names the upstream commit, so the
   two make the GPL source.
6. Copies the bundle (`bundle\` at the top, or `-Bundle <folder>`):
   `soundfonts\`, `backgrounds\` and `midi\` next to `midis2jam2.exe`, its
   `licenses\` into the package's, and appends its `NOTICE.txt` to the
   package's and `package-README-bundle.txt` to the README. It refuses a
   bundle without a `NOTICE.txt`. `-NoBundle` leaves it all out. What the
   app does with it is in [bundle/README.md](../../bundle/README.md).
7. Zips the folder (`DelayLamaEverything\` at the zip's top).

midis2jam2 finds the three Delay Lama files next to `midis2jam2.exe`: the
jpackage launcher sets `jpackage.app-path`, and `DelayLamaInstall` turns it into
the app folder the locators look in first, after the panel's own paths
(catalogue entry `delaylama.package.locate`).

## Options

| Option | Default | |
| --- | --- | --- |
| `-Version` | today's date | the zip's name part |
| `-OutDir` | `dist` | where the folder and zip go |
| `-Jdk` | `C:\Program Files\Java\jdk-21` | builds midis2jam2; source of `java.exe` |
| `-AndroidSdk` | `%LOCALAPPDATA%\Android\Sdk` | Gradle needs it |
| `-SkipBuild` | off | reuse the app image already built |
| `-BuildDelayLama` | off | build delalalalay-lama with CMake first |
| `-NoZip` | off | stop after the folder |
| `-Bundle` | `bundle` | the soundfonts, cube maps and songs to ship |
| `-NoBundle` | off | ship without them |

## The check

`check_package.ps1 [-Zip <zip>] [-Script <voice script>] [-Keep]` unzips to a
temp folder, then from a folder outside the package:

- starts `midis2jam2.exe` with its stderr redirected, waits for the
  `Delay Lama: app folder ...; helper ..., standalone ..., profiles ...` log
  line (`DelayLamaPanelModel`), checks the three paths are the package's own,
  and stops it. The launcher opens its window for a few seconds; nothing is
  clicked or typed. Paths set in the panel's options would override the
  package's and fail this check;
- when the package ships a bundle, checks `NOTICE.txt` covers it and the
  launcher's `Delay Lama: package bundle in ...` log line names the
  package's folder, each soundfont and each complete cube map. Starting the
  launcher applies the bundle to this Windows user's settings like any first
  start would (`DelayLamaBundle`), so on a machine whose settings already
  have a soundfont and background it changes nothing visible;
- runs the packaged `DelayLamaVoice.exe --render` on
  `external\delalalalay-lama\Tests\voice_scripts\chord.txt` and checks the WAV.

Not checked headlessly: playing a file with the monks, Add Delay Lama, and
recording. Check those by hand in the unzipped package before handing a zip
out.
