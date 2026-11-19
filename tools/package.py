"""Package the built themes as a zip on the Desktop: vellum/ + vellum_clear/ (the theme folders) + README.txt.
Local only, nothing is uploaded.

    python tools/build.py            (build both first)
    python tools/build.py --clear
    python tools/package.py          (writes Desktop\\<ZIP>)
"""
import os, re, shutil, sys, tempfile, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = '0.2.0'
# (theme name, folder in the zip, build folder)
THEMES = (('Vellum', 'vellum', os.path.join(ROOT, 'build', 'glass')),
          ('Vellum Clear', 'vellum_clear', os.path.join(ROOT, 'build', 'glass_clear')))
ZIP = os.path.join(os.path.expanduser('~'), 'Desktop', 'Vellum_ROSE_UI_theme_v%s.zip' % VERSION)

README = '''VELLUM  -  a frosted glass UI theme for ROSE Online          version %(v)s
==========================================================================

Minimal, iOS-style glass: translucent panels with a thin white rim, soft shadows, rounded
corners and a single monotone palette (white and grey).

  * Health bars are dark glass, mana bars are light glass, everything else is mid grey.
  * Tabs sit in the title row as glass pills (the pill glides between tabs in the inventory,
    game arena, options and a few other windows).
  * Buttons, checkboxes, dropdowns, sliders and scrollbars are all redrawn as glass.
  * The menu on the right is a "control center" card of rounded tiles.
  * The minimap is a clean rounded square: it collapses with a springy morph, and long zone
    names scroll like a song title.
  * New zones show a small glass pill at the top of the screen.
  * Arrow, plus, minus, close and trash buttons, the Zulie / Honor / Valor / Premium icons,
    and the bars above characters are redrawn to match.

TWO THEMES IN THIS ZIP
----------------------
  * Vellum        (folder "vellum")        the frosted glass windows.
  * Vellum Clear  (folder "vellum_clear")  the same theme with near see-through windows: only the
                                           thin rim shows, slots keep a soft dark fill, text has a
                                           slight shadow and the tab pills gently breathe.
Install one or both, they don't clash.

INSTALL
-------
 1. Close the game.
 2. Copy the folder  "vellum"  and/or  "vellum_clear"  from this zip into

        <your ROSE Online folder>\\data\\ui\\themes\\

    so that this file exists:   ...\\data\\ui\\themes\\vellum\\theme.toml
 3. Start the game and choose   Options > Interface > Theme > Vellum  (or Vellum Clear)
 4. Restart the game once after switching. The game caches pictures by file name, so a full
    restart (not just Ctrl+F5) makes sure you see the new art.

UNINSTALL
---------
Pick another theme in the options, then delete the "vellum" / "vellum_clear" folder.

GOOD TO KNOW
------------
 * It uses a few scripts from the game's own default theme ("rose"), which every install has.
 * Text floating in the 3D world (character and monster names, dropped item labels) keeps its
   black outline on purpose, so it stays readable against the scenery.
 * Tab rows whose tabs change at runtime (skills, NPC shop) use a plain glass pill instead of
   a gliding one.
 * If a window ever looks broken, open the game's Event Log. Lines such as "Cant get file from
   vfs" mean the folder was only partly copied: copy it again and restart the game.
 * Made for the game's current Early Access UI. If a game update changes the UI pages, some
   windows may need an update.

CREDITS
-------
Built on the community stock ROSE UI theme by Rednim (its pages, layout and the Nunito font
are used under their own licences). Game artwork belongs to its owners. All glass artwork,
icons and styling in this theme were generated for it.
''' % {'v': VERSION}


def main():
    for _, _, build in THEMES:
        if not os.path.isdir(build):
            sys.exit('build first: python tools/build.py  and  python tools/build.py --clear')
    stage = tempfile.mkdtemp(prefix='vellum_pkg_')
    try:
        if os.path.exists(ZIP):
            os.remove(ZIP)
        with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            z.writestr('README.txt', README.replace('\n', '\r\n'))
            for name, folder, build in THEMES:
                theme_dir = os.path.join(stage, folder)
                shutil.copytree(build, theme_dir)
                toml = os.path.join(theme_dir, 'theme.toml')
                text = open(toml, encoding='utf-8').read()
                text, n = re.subn(r'^name = ".*"', 'name = "%s"' % name, text, flags=re.M)
                assert n == 1, 'theme.toml has no name line'
                open(toml, 'w', encoding='utf-8', newline='').write(text)
                for dirpath, _, files in os.walk(theme_dir):
                    for f in sorted(files):
                        full = os.path.join(dirpath, f)
                        z.write(full, os.path.join(folder, os.path.relpath(full, theme_dir)).replace(os.sep, '/'))
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    print('wrote', ZIP, '(%.1f MB)' % (os.path.getsize(ZIP) / 1048576))


if __name__ == '__main__':
    main()
