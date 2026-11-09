"""Build the Glass theme: upstream/ (stock theme) + src/ overrides + generated art -> build/glass.

    python tools/build.py            build
    python tools/build.py --install  build and copy to the game's data/ui/themes/glass
"""
import hashlib, os, re, shutil, sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import art

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UP, SRC, OUT = (os.path.join(ROOT, p) for p in ('upstream', 'src', os.path.join('build', 'glass')))
GAME = r'C:\Program Files\ROSE Online\data\ui\themes\glass'
NAME = 'Glass (test)'

# Window glass. MARGIN (dp) is the shadow room around the glass: windows add it to their padding.
MARGIN = 12
WINDOW = dict(margin=MARGIN, radius=20, tint=(150, 160, 175, 120),
              rim_top=230, rim_mid=150, rim_bottom=110, sheen=40,
              shadow=110, shadow_dy=4, shadow_blur=7)
# Item slots: light glass, bright top rim, no shadow.
SLOT = dict(margin=0, radius=8, tint=(255, 255, 255, 38),
            rim_top=210, rim_mid=120, rim_bottom=90, sheen=46,
            shadow=0, shadow_dy=0, shadow_blur=1)


def sheet(name, im):
    """Write imgs/<name>_<hash>.dds. New art gets a new name: the game caches textures by path."""
    fn = '%s_%s.dds' % (name, hashlib.sha1(im.tobytes()).hexdigest()[:8])
    art.write_dds(os.path.join(OUT, 'imgs', fn), im)
    return fn


def glass_css():
    win, corner, edge = art.glass_panel(**WINDOW)
    slot, s_corner, s_edge = art.glass_panel(**SLOT)
    rects = art.slices('gl-win', 0, 0, corner, edge)
    rects.update(art.slices('gl-slot', win.width + 2, 0, s_corner, s_edge))
    im = Image.new('RGBA', (win.width + 2 + slot.width, max(win.height, slot.height)), (0, 0, 0, 0))
    im.paste(win, (0, 0))
    im.paste(slot, (win.width + 2, 0))
    fn = sheet('glass_frame', im)
    lines = ['/* Glass art (written by tools/build.py). Sprites at 2x. */',
             '@spritesheet glass-frame {', '    src: ../imgs/%s;' % fn, '    resolution: 2x;']
    lines += ['    %s: %dpx %dpx %dpx %dpx;' % ((k,) + v) for k, v in rects.items()]
    lines += ['}', '']
    open(os.path.join(OUT, 'styles', 'glass_frame.css'), 'w', encoding='utf-8', newline='').write('\n'.join(lines))
    print('art', fn, 'corner %dpx edge %dpx' % (corner, edge))


def build():
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(UP, OUT)
    for dirpath, _, files in os.walk(SRC):
        for f in files:
            src = os.path.join(dirpath, f)
            dst = os.path.join(OUT, os.path.relpath(src, SRC))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    glass_css()
    toml = os.path.join(OUT, 'theme.toml')
    text = re.sub(r'^name = ".*"', 'name = "%s"' % NAME, open(toml, encoding='utf-8').read(), flags=re.M)
    open(toml, 'w', encoding='utf-8', newline='').write(text)
    print('built', OUT)


if __name__ == '__main__':
    build()
    if '--install' in sys.argv:
        shutil.rmtree(GAME, ignore_errors=True)
        shutil.copytree(OUT, GAME)
        print('installed', GAME)
