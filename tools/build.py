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
WINDOW = dict(margin=MARGIN, radius=18, tint=(24, 28, 38, 175),
              rim_top=190, rim_mid=80, rim_bottom=45, sheen=34,
              shadow=120, shadow_dy=4, shadow_blur=5)
# Segmented bar: darker recessed glass with the same light-from-above rim.
TRACK = dict(margin=0, radius=11, tint=(0, 0, 0, 60), rim_top=170, rim_mid=75, rim_bottom=40, sheen=22,
             shadow=0, shadow_dy=0, shadow_blur=1)
# Selected pill: brighter glass that catches the light.
PILL = dict(margin=0, radius=8, tint=(255, 255, 255, 62), rim_top=240, rim_mid=140, rim_bottom=85, sheen=70,
            shadow=0, shadow_dy=0, shadow_blur=1)
# Buttons in four states: resting glass, brighter on hover, dimmer and flipped light when pressed, faint when disabled.
BTN = dict(margin=0, radius=12, tint=(255, 255, 255, 40), rim_top=215, rim_mid=120, rim_bottom=70, sheen=55,
           shadow=0, shadow_dy=0, shadow_blur=1)
BTN_H = dict(BTN, tint=(255, 255, 255, 72), rim_top=245, rim_mid=165, rim_bottom=100, sheen=85)
BTN_P = dict(BTN, tint=(0, 0, 0, 70), rim_top=110, rim_mid=95, rim_bottom=150, sheen=0)
BTN_D = dict(BTN, tint=(255, 255, 255, 14), rim_top=90, rim_mid=50, rim_bottom=30, sheen=14)
# Scrollbars: thin recessed groove, glass thumb (hover brighter, pressed dimmer).
SB_TRACK = dict(margin=0, radius=5, tint=(0, 0, 0, 70), rim_top=80, rim_mid=50, rim_bottom=35, sheen=0,
                shadow=0, shadow_dy=0, shadow_blur=1)
SB_THUMB = dict(margin=0, radius=3, tint=(255, 255, 255, 80), rim_top=215, rim_mid=140, rim_bottom=95, sheen=60,
                shadow=0, shadow_dy=0, shadow_blur=1)
SB_THUMB_H = dict(SB_THUMB, tint=(255, 255, 255, 120), rim_top=245, rim_mid=175, rim_bottom=120, sheen=90)
SB_THUMB_P = dict(SB_THUMB, tint=(255, 255, 255, 45), rim_top=170, rim_mid=120, rim_bottom=90, sheen=30)
PIECES = (('gl-win', WINDOW), ('gl-track', TRACK), ('gl-pill', PILL),
          ('gl-sbt', SB_TRACK), ('gl-sbb', SB_THUMB), ('gl-sbbh', SB_THUMB_H), ('gl-sbbp', SB_THUMB_P),
          ('gl-btn', BTN), ('gl-btnh', BTN_H), ('gl-btnp', BTN_P), ('gl-btnd', BTN_D))

# Gauges: light frosted groove (by bar height), range-slider groove, and a compact panel for the HUD overlay.
def _groove(radius):   # recessed frosted groove: dark inner edge on top, bright lower lip
    return dict(margin=0, radius=radius, tint=(255, 255, 255, 30), rim_top=120, rim_mid=110, rim_bottom=190, sheen=0,
                shadow=0, shadow_dy=0, shadow_blur=1, inner_top=110)
HUDWIN = dict(WINDOW, margin=6, shadow_dy=2, shadow_blur=2.5)   # the window glass with a tighter shadow that fits 6dp
PIECES += (('gl-gbg-lg', _groove(6)), ('gl-gbg-md', _groove(4)), ('gl-gbg-sm', _groove(2)), ('gl-gbg-xs', _groove(1)),
           ('gl-slt', dict(SB_TRACK, radius=4)), ('gl-hud', HUDWIN))

# Monotone gauge fills: HP dark, MP light, everything else mid-grey.
DARK = dict(top=(86, 92, 110), bottom=(26, 29, 40), alpha=135, rim=(255, 255, 255), rim_a=55, hl_a=120, rim_top_a=235, sheen=70)
LIGHT = dict(top=(255, 255, 255), bottom=(206, 216, 232), alpha=120, rim=(255, 255, 255), rim_a=70, hl_a=255, rim_top_a=255, sheen=90)
MID = dict(top=(214, 222, 234), bottom=(150, 159, 172), alpha=120, rim=(255, 255, 255), rim_a=60, hl_a=180, rim_top_a=235, sheen=80)
# (name, w, h, radius, colours, inset dp): the large HUD bars sit inside their groove as slim glass pills
FILLS = (('gl-f-dark-lg', 185, 18, 5, DARK, 2), ('gl-f-light-lg', 185, 18, 5, LIGHT, 2),
         ('gl-f-mid-exp', 185, 7, 3, MID, 1),
         ('gl-f-dark-md', 99, 11, 4, DARK, 1), ('gl-f-mid-md', 99, 11, 4, MID, 1),
         ('gl-f-dark-sm', 99, 7, 2, DARK, 0.5), ('gl-f-light-sm', 99, 7, 2, LIGHT, 0.5))


def sprites():
    """Single (non-sliced) sprites: name -> image."""
    out = [('gl-close', art.close_icon(False)), ('gl-close-h', art.close_icon(True)),
           ('gl-knob', art.knob(False)), ('gl-knob-h', art.knob(True))]
    for name, w, h, r, c, ins in FILLS:
        out.append((name, art.gauge_fill(w, h, r, c['top'], c['bottom'], c['alpha'], c['rim'], c['rim_a'], c['hl_a'], ins,
                                                  c.get('rim_top_a'), c.get('sheen', 0))))
    for kind in ('options', 'leave', 'kick', 'entrust'):
        for st in ('n', 'h', 'd'):
            out.append(('gl-i-%s%s' % (kind, '' if st == 'n' else '-' + st), art.round_icon(kind, st)))
    for kind in ('globe', 'bars', 'gift', 'bag', 'minus', 'plus'):       # minimap buttons, 22dp
        for st in ('n', 'h'):
            out.append(('gl-m-%s%s' % (kind, '' if st == 'n' else '-h'), art.round_icon(kind, st, radius=11)))
    out += [('gl-m-sun', art.plain_glyph('sun')), ('gl-m-moon', art.plain_glyph('moon'))]
    for kind in ('cb', 'rd'):
        for st in ('off', 'off-h', 'on', 'on-h', 'p', 'd', 'd-on'):
            out.append(('gl-%s-%s' % (kind, st), art.toggle(kind, st)))
    for st in ('n', 'h', 'd'):
        out.append(('gl-chev' + ('' if st == 'n' else '-' + st), art.chevron(st)))
    out += [('gl-grip', art.grip(False)), ('gl-grip-h', art.grip(True))]
    return out

# Windows (body ids) that get the shared glass look from tools/glass_window.css. The inventory has its own page styles.
GLASS_WINDOWS = ('game-arena', 'group-manager', '#group-settings-panel', 'game-options')
# Scripts the glass windows run on open: fade/settle in (tools/glass_open.lua).
OPEN_KEYFRAMES = '''@keyframes gl-open-a { 0% { opacity: 0; transform: translateY(5dp) scale(0.985); } 100% { opacity: 1; transform: translateY(0dp) scale(1); } }
@keyframes gl-open-b { 0% { opacity: 0; transform: translateY(5dp) scale(0.985); } 100% { opacity: 1; transform: translateY(0dp) scale(1); } }
'''


def scoped(css, ids):
    """Expand a leading W in every selector to body#<id>, once per id."""
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    out = []
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        sels = []
        for sel in m.group(1).split(','):
            sel = sel.strip()
            sels += [sel.replace('W', i if i.startswith('#') else 'body#' + i, 1) for i in ids] if sel.startswith('W') else [sel]
        out.append(',\n'.join(sels) + ' {' + m.group(2) + '}\n')
    return '\n'.join(out)


def window_css():
    css = open(os.path.join(ROOT, 'tools', 'glass_window.css'), encoding='utf-8').read()
    text = '/* Shared glass window look (written by tools/build.py) */\n' + scoped(css, GLASS_WINDOWS) + '\n' + OPEN_KEYFRAMES
    open(os.path.join(OUT, 'styles', 'glass_window.css'), 'w', encoding='utf-8', newline='').write(text)
    # the art + rules load with the window templates; they only match the ids above (and the gauges/HUD pages)
    for tname in sorted(os.listdir(os.path.join(OUT, 'templates'))):
        if not tname.endswith('.html'):
            continue
        tpl = os.path.join(OUT, 'templates', tname)
        t = open(tpl, encoding='utf-8').read()
        old = '        <link type="text/rcss" href="../styles/window.css" />'
        if t.count(old) != 1:
            continue
        t = t.replace(old, old + chr(10) + '        <link type="text/rcss" href="../styles/glass_frame.css" />' + chr(10) +
                      '        <link type="text/rcss" href="../styles/glass_gauge.css" />' + chr(10) +
                      '        <link type="text/rcss" href="../styles/glass_window.css" />')
        open(tpl, 'w', encoding='utf-8', newline='').write(t)
    for name in ('glass_gauge.css', 'glass_hud.css', 'glass_options.css', 'glass_minimap.css'):
        shutil.copy2(os.path.join(ROOT, 'tools', name), os.path.join(OUT, 'styles', name))


def sheet(name, im):
    """Write imgs/<name>_<hash>.dds. New art gets a new name: the game caches textures by path."""
    fn = '%s_%s.dds' % (name, hashlib.sha1(im.tobytes()).hexdigest()[:8])
    art.write_dds(os.path.join(OUT, 'imgs', fn), im)
    return fn


def glass_css():
    """Bake every glass piece into one sheet: 9-slice pieces as <name>-tl ... <name>-br, single sprites by name."""
    items = [(name,) + art.glass_panel(**spec) for name, spec in PIECES]        # (name, img, corner, edge)
    items += [(name, img, None, None) for name, img in sprites()]
    maxw, x, y, rowh, placed = 2048, 0, 0, 0, []
    for name, img, corner, edge in items:
        if x + img.width > maxw:
            x, y, rowh = 0, y + rowh + 2, 0
        placed.append((name, img, corner, edge, x, y))
        x += img.width + 2
        rowh = max(rowh, img.height)
    im = Image.new('RGBA', (maxw, y + rowh), (0, 0, 0, 0))
    rects = {}
    for name, img, corner, edge, px, py in placed:
        im.paste(img, (px, py))
        if corner is None:
            rects[name] = (px, py, img.width, img.height)
        else:
            rects.update(art.slices(name, px, py, corner, edge))
    fn = sheet('glass_frame', im)
    lines = ['/* Glass art (written by tools/build.py). Sprites at 2x. */',
             '@spritesheet glass-frame {', '    src: ../imgs/%s;' % fn, '    resolution: 2x;']
    lines += ['    %s: %dpx %dpx %dpx %dpx;' % ((k,) + v) for k, v in rects.items()]
    lines += ['}', '']
    open(os.path.join(OUT, 'styles', 'glass_frame.css'), 'w', encoding='utf-8', newline='').write(chr(10).join(lines))
    print('art', fn, im.size)


def build():
    import runpy
    for script in ('patch_inventory.py', 'patch_windows.py', 'patch_zone.py'):   # regenerate src/game pages from upstream
        runpy.run_path(os.path.join(ROOT, 'tools', script))
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(UP, OUT)
    for dirpath, _, files in os.walk(SRC):
        for f in files:
            src = os.path.join(dirpath, f)
            dst = os.path.join(OUT, os.path.relpath(src, SRC))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    glass_css()
    window_css()
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
