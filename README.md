# Vellum

A frosted glass UI theme for ROSE Online: translucent panels with a thin white rim, rounded corners and a white/grey palette.
Tabs are glass pills that glide between tabs, the menu is a "control center" card, and the minimap is a clean rounded square.

**Vellum Clear** is the same theme with near see-through windows: only the thin rim shows, slots keep a soft
dark fill, text has a slight shadow and the tab pills gently breathe.

## Install

Download the zip from Releases, copy the `vellum` and/or `vellum_clear` folder into `<ROSE Online>\data\ui\themes\`,
then pick Options > Interface > Theme > Vellum (or Vellum Clear) and restart the game once.

## Build from source

    python tools/build.py             # build into build/glass
    python tools/build.py --clear     # build Vellum Clear into build/glass_clear
    python tools/build.py --install   # also copy into the game's data/ui/themes (works with --clear too)
    python tools/package.py           # release zip on the Desktop

Needs Python 3 with Pillow and NumPy.

## Credits

Built on the community stock ROSE UI theme by Rednim (`upstream/`, used under its own licence).
Fonts: Nunito and Noto, under the SIL Open Font License. Game artwork belongs to its owners.
