# Package bundle

The extras `tools/package/make_package.ps1` ships next to `midis2jam2.exe`,
so the package plays well with no setup. Only this README and `NOTICE.txt`
are tracked; the files themselves are large and third-party, so git ignores
them.

| Folder | Holds | Now |
| --- | --- | --- |
| `soundfonts/` | `.sf2` or `.dls` soundfonts, with their text files | Timbres of Heaven (XGM) 4.00(G), 420 MB |
| `backgrounds/<name>/` | a cube map: one image per side, named `NORTH`, `EAST`, `SOUTH`, `WEST`, `UP`, `DOWN` (any case; png, jpg, jpeg, bmp or gif) | `tibet/` |
| `midi/` | songs | 12 rock songs with fixed drums (`tools/drumfix`) |
| `licenses/` | license texts for the above, copied into the package's `licenses\` | GPL-2.0 for the soundfont |

`NOTICE.txt` is added to the package's `NOTICE.txt`. Keep it true to what
the folders hold.

## What the packaged app does with it

`DelayLamaBundle` (catalogue entry `delaylama.package.bundle`) runs at every
start:

- It copies each cube map into `~/.midis2jam2/backgrounds/`, unless a folder
  of that name is already there.
- On a user's first start, it adds the soundfonts to the soundbank list and
  selects the first one on the home tab, unless one is already selected. A
  listed soundfont with the same file name stands in for the bundled copy.
  It also makes the first complete cube map the background, unless the user
  chose a background other than the default.
- On later starts it keeps the user's choices. If the package folder has
  moved, it points the soundfonts the package added at the new copy.

The home tab's MIDI picker opens in `midi\`.

To ship without the bundle, pass `-NoBundle` to `make_package.ps1`. To ship
another folder with the same layout, pass `-Bundle <folder>`.
