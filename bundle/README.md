# Package bundle

What `tools/package/make_package.ps1` ships next to `midis2jam2.exe`, so the
package plays well with no setup. Only this README and `NOTICE.txt` are
tracked; the files themselves are git-ignored (large, and third-party).

| Folder | Holds | Now |
| --- | --- | --- |
| `soundfonts/` | `.sf2` / `.dls` soundfonts, with their text files | Timbres of Heaven (XGM) 4.00(G), 420 MB |
| `backgrounds/<name>/` | a cube map: one image per side named `NORTH`, `EAST`, `SOUTH`, `WEST`, `UP`, `DOWN` (any case; png, jpg, jpeg, bmp or gif) | `tibet/` |
| `midi/` | songs | 12 rock songs with fixed drums (`tools/drumfix`) |
| `licenses/` | license texts for the above, copied into the package's `licenses\` | GPL-2.0 for the soundfont |

`NOTICE.txt` here is appended to the package's `NOTICE.txt`: keep it true
to what the folders hold.

What the packaged app does with them (`DelayLamaBundle`, catalogue entry
`delaylama.package.bundle`): at every start it copies each cube map into
`~/.midis2jam2/backgrounds/` unless a folder of that name is there. On its
first start for a user it adds the soundfonts to the settings' soundbank
list and selects the first on the home tab (unless one is selected; a listed
soundfont of the same file name stands in for the bundled copy), and makes
the first complete cube map the background (unless a background other than
the default was chosen). Later starts keep the user's choices but point the
soundfonts a package added at the new copy when the package folder moves.
The home tab's MIDI picker opens in `midi\`.

`make_package.ps1 -NoBundle` leaves the bundle out; `-Bundle <folder>` takes
another folder of the same layout.
