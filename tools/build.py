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
SLOT = dict(margin=0, radius=8, tint=(255, 255, 255, 26), rim_top=150, rim_mid=110, rim_bottom=170, sheen=0,
            shadow=0, shadow_dy=0, shadow_blur=1, inner_top=100)
PIECES += (('gl-gbg-flat', dict(margin=0, radius=2, tint=(255, 255, 255, 45), rim_top=45, rim_mid=45, rim_bottom=45, sheen=0,
                                 shadow=0, shadow_dy=0, shadow_blur=1)), ('gl-slot', SLOT), ('gl-gbg-lg', _groove(6)), ('gl-gbg-md', _groove(4)), ('gl-gbg-sm', _groove(2)), ('gl-gbg-xs', _groove(1)),
           ('gl-slt', dict(SB_TRACK, radius=4)), ('gl-hud', HUDWIN))

# Monotone gauge fills: HP dark, MP light, everything else mid-grey.
DARK = dict(top=(86, 92, 110), bottom=(26, 29, 40), alpha=135, rim=(255, 255, 255), rim_a=55, hl_a=120, rim_top_a=235, sheen=70)
LIGHT = dict(top=(255, 255, 255), bottom=(206, 216, 232), alpha=120, rim=(255, 255, 255), rim_a=70, hl_a=255, rim_top_a=255, sheen=90)
MID = dict(top=(214, 222, 234), bottom=(150, 159, 172), alpha=120, rim=(255, 255, 255), rim_a=60, hl_a=180, rim_top_a=235, sheen=80)
# (name, w, h, radius, colours, inset dp): the large HUD bars sit inside their groove as slim glass pills
DARK_FLAT = dict(DARK, rim_a=0, hl_a=0, rim_top_a=0, sheen=0)
LIGHT_FLAT = dict(LIGHT, rim_a=0, hl_a=0, rim_top_a=0, sheen=0)
FILLS = (('gl-f-dark-xs', 99, 4, 2, DARK_FLAT, 0), ('gl-f-light-xs', 99, 4, 2, LIGHT_FLAT, 0),
         ('gl-f-dark-lg', 185, 18, 5, DARK, 2), ('gl-f-light-lg', 185, 18, 5, LIGHT, 2),
         ('gl-f-mid-exp', 185, 7, 3, MID, 1),
         ('gl-f-dark-md', 99, 11, 4, DARK, 1), ('gl-f-mid-md', 99, 11, 4, MID, 1),
         ('gl-f-dark-sm', 99, 7, 2, DARK, 0.5), ('gl-f-light-sm', 99, 7, 2, LIGHT, 0.5))


# menu strip button id -> glyph (tools/glass_menu: generated css below)
MENU = {'gamearena-scoreboard': 'bars', 'item-mall': 'bag', 'premium-storage': 'star', 'character': 'person',
        'game-arena': 'swords', 'group-manager-menu': 'users', 'inventory': 'box', 'skill-list': 'bolt', 'quest-list': 'list',
        'friend-list': 'heart', 'party-finder': 'search', 'mail': 'envelope', 'clan': 'shield', 'system': 'gear'}
MENU_KINDS = sorted(set(MENU.values()))


BTN_DECO = 'tiled-box(gl-btn-tl, gl-btn-t, gl-btn-tr, gl-btn-l, gl-btn-c, gl-btn-r, gl-btn-bl, gl-btn-b, gl-btn-br)'
BTN_DECO_H = 'tiled-box(gl-btnh-tl, gl-btnh-t, gl-btnh-tr, gl-btnh-l, gl-btnh-c, gl-btnh-r, gl-btnh-bl, gl-btnh-b, gl-btnh-br)'


def menu_css():
    """Control Center style menu: one glass card, 3 columns of 36dp rounded tiles, expands and collapses as before."""
    hud = 'tiled-box(gl-hud-tl, gl-hud-t, gl-hud-tr, gl-hud-l, gl-hud-c, gl-hud-r, gl-hud-bl, gl-hud-b, gl-hud-br)'
    out = ['/* Glass menu (written by tools/build.py) */',
           '#game-menu-hud { width: 164dp; }',
           '#game-menu-hud #button-container { width: 164dp; margin-left: 0dp; box-sizing: border-box; display: flex; flex-wrap: wrap; '
           'gap: 8dp; padding: 0dp 20dp; text-align: left; justify-content: flex-start; align-content: flex-start; }',
           '#game-menu-hud #button-container.expanded, #game-menu-hud #button-container.expanded-premium, '
           '#game-menu-hud #button-container.expanded-scoreboard, #game-menu-hud #button-container.expanded-premium-scoreboard '
           '{ height: 252dp; padding: 20dp; decorator: %s; }' % hud,
           '#game-menu-hud .tooltip { width: 36dp; height: 36dp; }',
           '#game-menu-hud button { width: 36dp; height: 36dp; opacity: 1; transition: transform 0.14s cubic-out; }',
           '#game-menu-hud button:hover { transform: scale(1.08); }', '#game-menu-hud button:active { transform: scale(0.92); }',
           '#game-menu-hud #menu-toggle { width: 56dp; height: 24dp; margin-left: 54dp; decorator: %s, image(gl-tg-up); }' % BTN_DECO,
           '#game-menu-hud #menu-toggle:hover, #game-menu-hud #menu-toggle:active { decorator: %s, image(gl-tg-up); }' % BTN_DECO_H,
           '#game-menu-hud #menu-toggle.open { decorator: %s, image(gl-tg-down); }' % BTN_DECO,
           '#game-menu-hud #menu-toggle.open:hover, #game-menu-hud #menu-toggle.open:active { decorator: %s, image(gl-tg-down); }' % BTN_DECO_H]
    for bid, kind in MENU.items():
        art_name = 'gl-mt-%s' % kind
        out.append('#game-menu-hud #%s { decorator: image(%s); }' % (bid, art_name))
        out.append('#game-menu-hud #%s:hover, #game-menu-hud #%s:active { decorator: image(%s-h); }' % (bid, bid, art_name))
    return chr(10).join(out) + chr(10)


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
    out += [('inventory-weight', art.round_icon('weight', 'n', radius=11)), ('mall-points', art.round_icon('gem', 'n', radius=11))]
    for kind in ('globe', 'bars', 'gift', 'bag', 'minus', 'plus'):       # minimap buttons, 22dp
        for st in ('n', 'h'):
            out.append(('gl-m-%s%s' % (kind, '' if st == 'n' else '-h'), art.round_icon(kind, st, radius=11)))
    out += [('gl-m-sun', art.plain_glyph('sun')), ('gl-m-moon', art.plain_glyph('moon'))]
    for kind in MENU_KINDS:                                     # the right-hand menu strip, 30dp
        for st in ('n', 'h'):
            out.append(('gl-mb-%s%s' % (kind, '' if st == 'n' else '-h'), art.round_icon(kind, st, radius=15)))
    for kind in MENU_KINDS:                                     # menu tiles, 36dp rounded squares
        for st in ('n', 'h'):
            out.append(('gl-mt-%s%s' % (kind, '' if st == 'n' else '-h'), art.round_icon(kind, st, radius=11, size=36)))
    out += [('gl-tg-up', art.toggle_chevron('up')), ('gl-tg-down', art.toggle_chevron('down'))]   # menu toggle chevrons
    for kind in ('gear', 'move', 'resize'):                     # chat corner buttons, 22dp
        for st in ('n', 'h'):
            out.append(('gl-c-%s%s' % (kind, '' if st == 'n' else '-h'), art.round_icon(kind, st, radius=11)))
    for st in ('n', 'h'):                                       # notification bell, 36dp
        out.append(('gl-bell' + ('' if st == 'n' else '-h'), art.round_icon('bell', st, radius=18)))
    for kind in ('cb', 'rd'):
        for st in ('off', 'off-h', 'on', 'on-h', 'p', 'd', 'd-on'):
            out.append(('gl-%s-%s' % (kind, st), art.toggle(kind, st)))
    for st in ('n', 'h', 'd'):
        out.append(('gl-chev' + ('' if st == 'n' else '-' + st), art.chevron(st)))
    out += [('gl-grip', art.grip(False)), ('gl-grip-h', art.grip(True))]
    return out

# Windows (body ids) that get the shared glass look from tools/glass_window.css. The inventory has its own page styles.
GLASS_WINDOWS = ('game-arena', 'group-manager', '#group-settings-panel', 'game-options',
                 'game-character-actions', 'game-character-preview', 'character-stats', 'game-choice-box', 'clan-create',
                 'disassembly', 'game-duel', 'empowerment', 'mall-cart', 'mall-storage', 'game-monster-inspector',
                 'npc-dialog', 'npc-transaction', 'game-number-input', 'game-party-finder', 'party-options',
                 'game-personal-store-price', 'player-trade', 'game-private-chat', 'game-quest-list', 'refine',
                 'game-reinforcement', 'respawn', 'game-style-change', 'tutorial', 'game-world-map',
                 'ui_gamearena_scoreboard', 'personal-vending', 'item-mall', 'common-message-box', 'game-system-menu',
                 'game-clan', 'game-friend-list', 'game-mail', 'game-personal-store', 'game-personal-store-management',
                 'storage', 'game-avatar-store', 'npc-shop', 'skills',
                 'external-character-create', 'external-tos', '#avatar-selection-window', '#login-container .window-box',
                 '#external-login-queue .window-box', 'game-crafting')
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


# Tabs moved into the title row. TABSET_HEADERS: body id -> number of tabs (each tab TAB_W dp wide, sliding pill).
# STRIP_HEADERS: body id -> (strip selector, bar width dp, tab count for the sliding pill or 0 for a static pill).
TAB_W = 76
TABSET_HEADERS = {'game-clan': 2, 'game-friend-list': 2, 'game-mail': 2, 'game-personal-store': 2}
STRIP_HEADERS = {'storage': ('#storage-tabs', 230, 4), 'npc-shop': ('#shop-tabs', 240, -1), 'skills': ('#skills-tabs', 340, -1)}   # count -1: tabs change at runtime, glass_strips.lua slides the pill
IN_CONTENT_SLIDERS = {'game-avatar-store': 2}
# Data-bound pills for tab rows whose tabs change at runtime: (body id, strip selector) -> most tabs.
# The strip gets class nN (tab count), the selected tab leaves a hidden span.gl-ix[gl-i=K] before the pill.
DB_STRIPS = {}   # 2026-11-10: data-bound pills for skills / shop broke in game; those rows use the static pill for now   # sliding pill in a strip that stays below the title


def pill_decorator():
    return 'tiled-box(gl-pill-tl, gl-pill-t, gl-pill-tr, gl-pill-l, gl-pill-c, gl-pill-r, gl-pill-bl, gl-pill-b, gl-pill-br)'


def tabs_css():
    out = ['/* Tabs in the title row (written by tools/build.py) */']
    track = 'tiled-box(gl-track-tl, gl-track-t, gl-track-tr, gl-track-l, gl-track-c, gl-track-r, gl-track-bl, gl-track-b, gl-track-br)'
    tab = ('flex: none; height: 16dp; line-height: 16dp; margin: 0dp; padding: 0dp 2dp; box-sizing: border-box; text-align: center; '
           'font-size: 11dp; font-weight: 700; font-effect: none; decorator: none; background-color: transparent; border-width: 0dp; '
           'white-space: nowrap; border-radius: 8dp; color: rgba(255, 255, 255, 170); position: relative; '
           'transition: background-color 0.16s cubic-out, color 0.16s cubic-out;')
    for i, n in TABSET_HEADERS.items():
        w = n * TAB_W
        out.append('body#%s #window-content { position: static; overflow: visible; max-height: none; }' % i)
        out.append('body#%s tabset > tabs { position: absolute; top: 22dp; right: 54dp; width: %ddp; height: 22dp; box-sizing: border-box; '
                   'padding: 3dp 0dp; gap: 0dp; margin: 0dp; flex-direction: row; border-width: 0dp; decorator: %s; }' % (i, w, track))
        out.append('body#%s tabset > tabs > .ui-tab, body#%s tabset > tabs > .ui-tab:hover { %s width: %ddp; }' % (i, i, tab, TAB_W))
        out.append('body#%s tabset > tabs > .ui-tab:hover { color: rgb(255, 255, 255); }' % i)
        out.append('body#%s tabset > tabs > .ui-tab:selected, body#%s tabset > tabs > .ui-tab.selected { decorator: none; '
                   'background-color: transparent; border-width: 0dp; color: rgb(255, 255, 255); }' % (i, i))
        out.append('body#%s .gl-slider { position: absolute; top: 25dp; width: %ddp; height: 16dp; right: %ddp; pointer-events: none; '
                   'decorator: %s; transition: right 0.28s cubic-out; }' % (i, TAB_W - 4, 54 + (n - 1) * TAB_W + 2, pill_decorator()))
        for k in range(1, n):
            out.append('body#%s .gl-slider.at%d { right: %ddp; }' % (i, k, 54 + (n - 1 - k) * TAB_W + 2))
    for i, (sel, w, n) in STRIP_HEADERS.items():
        out.append('body#%s #window-content { position: static; overflow: visible; max-height: none; }' % i)
        out.append('body#%s %s { position: absolute; top: 22dp; right: 54dp; width: %ddp; height: 22dp; margin: 0dp; }' % (i, sel, w))
        out.append('body#%s %s > .ui-tab, body#%s %s > .ui-tab:hover { height: 16dp; line-height: 16dp; font-size: 11dp; min-height: 16dp; padding: 0dp 2dp; '
                   'white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }' % (i, sel, i, sel))
        if n == -1:
            out.append('body#%s %s > .gl-slider { height: 16dp; }' % (i, sel))
        if n > 0:
            out.append('body#%s %s > .gl-slider { height: 16dp; width: %.1f%%; left: 0.5%%; }' % (i, sel, 100.0 / n - 1))
            for k in range(1, n):
                out.append('body#%s %s > .gl-slider.at%d { left: %.1f%%; }' % (i, sel, k, k * 100.0 / n + 0.5))
    for i, n in IN_CONTENT_SLIDERS.items():
        out.append('body#%s .ui-tab-strip.gl-slide > .gl-slider { width: %.1f%%; left: 0.5%%; }' % (i, 100.0 / n - 1))
        for k in range(1, n):
            out.append('body#%s .ui-tab-strip.gl-slide > .gl-slider.at%d { left: %.1f%%; }' % (i, k, k * 100.0 / n + 0.5))
    for (i, sel), top in DB_STRIPS.items():
        out.append('body#%s %s > .gl-slider { width: 0dp; left: 0.5%%; }' % (i, sel))
        for n in range(2, top + 1):
            out.append('body#%s %s.n%d > .gl-slider { width: %.2f%%; }' % (i, sel, n, 100.0 / n - 1))
            for k in range(1, n):
                out.append('body#%s %s.n%d > .gl-ix[gl-i="%d"] ~ .gl-slider { left: %.2f%%; }' % (i, sel, n, k, k * 100.0 / n + 0.5))
    return chr(10).join(out) + chr(10)


def window_css():
    css = open(os.path.join(ROOT, 'tools', 'glass_window.css'), encoding='utf-8').read()
    text = '/* Shared glass window look (written by tools/build.py) */\n' + scoped(css, GLASS_WINDOWS) + '\n' + OPEN_KEYFRAMES
    # crafting keeps its title and close button one level down (inside a data-model div), so those rules use descendant selectors
    text = text.replace('body#game-crafting > ', 'body#game-crafting ')
    open(os.path.join(OUT, 'styles', 'glass_window.css'), 'w', encoding='utf-8', newline='').write(text)
    open(os.path.join(OUT, 'styles', 'glass_tabs.css'), 'w', encoding='utf-8', newline='').write(tabs_css())
    open(os.path.join(OUT, 'styles', 'glass_menu.css'), 'w', encoding='utf-8', newline='').write(menu_css())
    comp = os.path.join(OUT, 'styles', 'components.css')
    shared = open(os.path.join(ROOT, 'tools', 'glass_shared.css'), encoding='utf-8').read()
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', re.sub(r'/\*.*?\*/', '', css, flags=re.S)):   # glass scrollbars for EVERY page
        keep = ['body ' + x.strip()[2:] for x in m.group(1).split(',') if x.strip().startswith('W scrollbar')]
        if keep:
            shared += ',\n'.join(keep) + ' {' + m.group(2) + '}\n'
    sb_only = shared[shared.index('body scrollbar'):] if 'body scrollbar' in shared else ''
    sbp = os.path.join(OUT, 'styles', 'scrollbar.css')
    sb_stock = open(sbp, encoding='utf-8').read()
    assert len(sb_stock) > 500, 'scrollbar.css is empty'
    open(sbp, 'w', encoding='utf-8', newline='').write(sb_stock + chr(10) + sb_only)
    stock = open(comp, encoding='utf-8').read()   # read BEFORE opening for write (open(..., 'w') truncates the file)
    assert len(stock) > 1000, 'components.css is empty'
    open(comp, 'w', encoding='utf-8', newline='').write(stock + shared)
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
                      '        <link type="text/rcss" href="../styles/glass_window.css" />' + chr(10) +
                      '        <link type="text/rcss" href="../styles/glass_tabs.css" />')
        open(tpl, 'w', encoding='utf-8', newline='').write(t)
    for name in ('glass_gauge.css', 'glass_hud.css', 'glass_options.css', 'glass_minimap.css', 'glass_overlays.css'):
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


# Monotone theme: every yellow / gold highlight in the stock sheets and pages becomes white (selection tints become white tints).
# Only colour VALUES are touched; class names such as ".yellow" and tags such as fc_gold keep their names.
MONO_LITERALS = (('rgb(255, 112, 102)', 'rgb(255, 255, 255)'), ('#ffe178', '#ffffff'), ('#ffd66b', '#ffffff'), ('#f39c12', '#ffffff'),
                 ('rgb(255, 247, 191)', 'rgb(255, 255, 255)'), ('rgb(255, 215, 57)', 'rgb(255, 255, 255)'),
                 ('rgb(255, 217, 0)', 'rgb(255, 255, 255)'), ('rgb(255,217,0)', 'rgb(255, 255, 255)'),
                 ('rgb(255, 255, 0)', 'rgb(255, 255, 255)'), ('rgb(246, 200, 118)', 'rgb(255, 255, 255)'),
                 ('rgba(255, 225, 120, 35)', 'rgba(255, 255, 255, 55)'), ('rgba(220, 180, 20, 80)', 'rgba(255, 255, 255, 55)'),
                 ('rgba(255, 255, 0, 120)', 'rgba(255, 255, 255, 70)'))
YELLOW_VALUE = re.compile(r'((?:color|border(?:-[a-z]+)*|background(?:-color)?|outline(?:-color)?)\s*:[^;{}"\'<>]*?)(?<![\w.-])yellow(?![\w-])')


def monotone_pass():
    changed = 0
    for dirpath, _, files in os.walk(OUT):
        for f in files:
            if not f.endswith(('.css', '.html')):
                continue
            path = os.path.join(dirpath, f)
            text = open(path, encoding='utf-8').read()
            new = text
            for old, rep in MONO_LITERALS:
                new = new.replace(old, rep)
            prev = None
            while prev != new:                      # several yellows can share one declaration
                prev = new
                new = YELLOW_VALUE.sub(lambda m: m.group(1) + 'rgb(255, 255, 255)', new)
            if new != text:
                open(path, 'w', encoding='utf-8', newline='').write(new)
                changed += 1
    print('monotone pass: %d files changed' % changed)


# Stock icon sprites that live in LOOSE picture files (imgs/controls.tga, imgs/glassui_0.dds) are repainted in place as minimal
# glass. The repainted sheets get a content-hash file name: the game caches textures by path, so a reload would keep the old art.
ICON_KIND = {'plus-button': 'plus', 'minus-button': 'minus', 'close-button': 'x', 'button-trash': 'trash', 'button-zulie': 'zulie',
             'rw-close': 'x', 'rw-trash': 'trash', 'rw-window-title-close': 'x',
             'sq-up': 'tri-up', 'sq-down': 'tri-down', 'sq-left': 'tri-left', 'sq-right': 'tri-right', 'sq-plus': 'plus', 'sq-minus': 'minus'}
SQ_STATE = {'n': 'n', 'h': 'h', 'p': 'p', 'a': 'p', 'd': 'd'}
SPRITE_LINE = re.compile(r'^\s+([\w-]+)-([nhpad]):\s*(\d+)px\s+(\d+)px\s+(\d+)px\s+(\d+)px;')


def restyle_glassui():
    """Repaint each listed sprite inside the picture file its own spritesheet block points to; verify nothing else changed."""
    from PIL import ImageChops
    css_path = os.path.join(OUT, 'styles', 'spritesheet_glassui.css')
    css = open(os.path.join(UP, 'styles', 'spritesheet_glassui.css'), encoding='utf-8').read()
    cur, jobs = None, {}
    for line in css.splitlines():
        m = re.match(r'\s*src:\s*([^;]+);', line)
        if m:
            cur = m.group(1).strip()
            continue
        m = SPRITE_LINE.match(line)
        if m and cur and cur.startswith('../imgs/') and m.group(1) in ICON_KIND:
            jobs.setdefault(cur, []).append(m)
    total, new_css = 0, open(css_path, encoding='utf-8').read()
    for src, matches in jobs.items():
        path = os.path.normpath(os.path.join(OUT, 'styles', src))
        original = Image.open(path).convert('RGBA')
        sheet = original.copy()
        mask = Image.new('L', sheet.size, 0)
        for m in matches:
            kind = ICON_KIND[m.group(1)]
            x, y, w, h = (int(m.group(i)) for i in (3, 4, 5, 6))
            radius = w // 2 if kind in ('coin', 'zulie') else (6 if w <= 20 else 7)
            icon = art.round_icon(kind, SQ_STATE[m.group(2)], radius=radius, size=min(w, h) if kind in ('coin', 'zulie') else w).resize((w, h), Image.LANCZOS)
            sheet.paste(icon, (x, y))
            mask.paste(255, (x, y, x + w, y + h))
            total += 1
        outside = ImageChops.subtract(ImageChops.difference(original, sheet).convert('L').point(lambda v: 255 if v else 0), mask)
        assert outside.getbbox() is None, 'repaint touched pixels outside its sprites in ' + src
        base, ext = os.path.splitext(os.path.basename(path))
        h8 = hashlib.sha1(sheet.tobytes()).hexdigest()[:8]
        new_name = '%s_%s%s' % (base, h8, ext)
        (art.write_tga if ext == '.tga' else art.write_dds)(os.path.join(OUT, 'imgs', new_name), sheet)
        os.remove(path)
        assert new_css.count(src) == 1, src
        new_css = new_css.replace(src, '../imgs/' + new_name)
        print('  repainted %d sprites -> %s' % (len(matches), new_name))
    open(css_path, 'w', encoding='utf-8', newline='').write(new_css)
    print('glass icon sprites repainted:', total)


# Stock gauge sprites (imgs/gauge.dds, loose) repainted as glass: the bars above characters (yours and your group's), monster and
# NPC plates all draw from these. Red = dark, blue = light, everything else mid grey; they stay translucent (about 50 percent).
GAUGE_BG = ('gauge-bg-sm-md', 'gauge-bg-sm-sm', 'gauge-bg-sm-lg-yellow', 'gauge-bg-lg-lg-red', 'gauge-bg-lg-lg-blue')
GAUGE_FILL = {'gauge-red-sm-md': DARK, 'gauge-red-sm-sm': DARK, 'gauge-lg-lg-red': DARK,
              'gauge-blue-sm-sm': LIGHT, 'gauge-lg-lg-blue': LIGHT,
              'gauge-pink-sm-md': MID, 'gauge-green-sm-md': MID, 'gauge-purple-sm-sm': MID, 'gauge-sm-lg-yellow': MID}


def restyle_gauge():
    from PIL import ImageChops
    css_path = os.path.join(OUT, 'styles', 'spritesheet_gauge.css')
    css = open(css_path, encoding='utf-8').read()
    path = os.path.join(OUT, 'imgs', 'gauge.dds')
    original = Image.open(path).convert('RGBA')
    sheet, mask, n = original.copy(), Image.new('L', original.size, 0), 0
    for m in re.finditer(r'^\s+([\w-]+):\s*(\d+)px\s+(\d+)px\s+(\d+)px\s+(\d+)px;', css, re.M):
        name, x, y, w, h = m.group(1), *(int(m.group(i)) for i in (2, 3, 4, 5))
        small = h <= 6
        if name in GAUGE_BG:
            spec = dict(margin=0, radius=1 if small else (4 if h <= 12 else 6), tint=(255, 255, 255, 45 if small else 34),
                        rim_top=45 if small else 120, rim_mid=45 if small else 110, rim_bottom=45 if small else 190, sheen=0,
                        shadow=0, shadow_dy=0, shadow_blur=1, inner_top=0 if small else 110)
            panel, corner, edge = art.glass_panel(**spec)
            icon = art.nine_slice(panel, corner, edge, w * 2, h * 2).resize((w, h), Image.LANCZOS)
        elif name in GAUGE_FILL:
            c = GAUGE_FILL[name]
            flat = dict(c, rim_a=0, hl_a=0, rim_top_a=0, sheen=0) if small else c
            icon = art.gauge_fill(w, h, 1 if small else (3 if h <= 12 else 5), flat['top'], flat['bottom'], flat['alpha'], flat['rim'],
                                  flat['rim_a'], flat['hl_a'], 0 if small else (1 if h <= 12 else 2), flat.get('rim_top_a'), flat.get('sheen', 0)
                                  ).resize((w, h), Image.LANCZOS)
        else:
            continue
        sheet.paste(icon, (x, y))
        mask.paste(255, (x, y, x + w, y + h))
        n += 1
    outside = ImageChops.subtract(ImageChops.difference(original, sheet).convert('L').point(lambda v: 255 if v else 0), mask)
    assert outside.getbbox() is None, 'gauge repaint touched pixels outside its sprites'
    new_name = 'gauge_%s.dds' % hashlib.sha1(sheet.tobytes()).hexdigest()[:8]
    art.write_dds(os.path.join(OUT, 'imgs', new_name), sheet)
    os.remove(path)
    assert css.count('../imgs/gauge.dds') == 1
    open(css_path, 'w', encoding='utf-8', newline='').write(css.replace('../imgs/gauge.dds', '../imgs/' + new_name))
    print('gauge sprites repainted:', n, '->', new_name)


# Currency icons (currencyicon-0..15) come from the game archive; the stock sheet is replaced by a loose glass sheet.
# CURRENCY_GLYPH maps a currency index to a glyph once known; until then each icon shows its index number (diagnostic build).
CURRENCY_GLYPH = {0: 'zulie', 1: 'letter-h', 2: 'letter-v', 5: 'letter-p'}   # confirmed from the user's screenshot of the numbered build
DEFAULT_CURRENCY_GLYPH = 'coin'


def currency_sheet():
    from PIL import ImageDraw, ImageFont
    cell, cols = 64, 8
    sheet = Image.new('RGBA', (cell * cols, cell * 2), (0, 0, 0, 0))
    try:
        font = ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf', 26)
    except Exception:
        font = ImageFont.load_default()
    lines = ['/* Glass currency icons (written by tools/build.py). */', '@spritesheet theme {', '    src: %s;', '    resolution: 2x;']
    for i in range(16):
        x, y = (i % cols) * cell, (i // cols) * cell
        if True:
            icon = art.round_icon(CURRENCY_GLYPH.get(i, DEFAULT_CURRENCY_GLYPH), 'n', radius=16)
        else:
            icon, _, _ = art.glass_panel(margin=0, radius=16, tint=(255, 255, 255, 42), rim_top=225, rim_mid=110, rim_bottom=70, sheen=50,
                                         shadow=0, shadow_dy=0, shadow_blur=1, edge=0)
            d = ImageDraw.Draw(icon)
            label = str(i)
            box = d.textbbox((0, 0), label, font=font)
            d.text(((cell - (box[2] - box[0])) / 2 - box[0], (cell - (box[3] - box[1])) / 2 - box[1]), label, font=font, fill=(255, 255, 255, 240))
        sheet.paste(icon, (x, y))
        lines.append('    currencyicon-%d: %dpx %dpx %dpx %dpx;' % (i, x, y, cell, cell))
    lines.append('}')
    name = 'glass_currency_%s.dds' % hashlib.sha1(sheet.tobytes()).hexdigest()[:8]
    art.write_dds(os.path.join(OUT, 'imgs', name), sheet)
    text = chr(10).join(lines) % ('../imgs/' + name) + chr(10)
    open(os.path.join(OUT, 'styles', 'spritesheet_currencyicon.css'), 'w', encoding='utf-8', newline='').write(text)
    print('currency sheet:', name)


def check_no_empty_sprite_blocks():
    bad = []
    for dirpath, _, files in os.walk(os.path.join(OUT, 'styles')):
        for f in files:
            if not f.endswith('.css'):
                continue
            text = open(os.path.join(dirpath, f), encoding='utf-8').read()
            for m in re.finditer(r'@spritesheet\s+([\w-]+)\s*\{([^}]*)\}', text):
                if not re.search(r'^\s*[\w-]+\s*:\s*-?\d+(?:px)?\s', m.group(2) + ' ', re.M) and 'px' not in re.sub(r'src:[^;]*;|resolution:[^;]*;', '', m.group(2)):
                    bad.append('%s: %s' % (f, m.group(1)))
    assert not bad, 'empty @spritesheet blocks (the game logs an error for each): ' + ', '.join(bad)


def retarget_sprites():
    """inventory-weight and mall-points are defined inside the game's own archive sheets; drop those two definitions so the
    glass versions (defined in glass_frame.css under the same names) are the only ones."""
    for fname, line in (('spritesheet_inventory.css', '    inventory-weight: 133px 257px 21px 21px;\n'),
                        ('spritesheet_icons.css', '    mall-points: 89px 433px 21px 21px;\n')):
        path = os.path.join(OUT, 'styles', fname)
        text = open(path, encoding='utf-8').read().replace('\r\n', '\n')
        assert text.count(line) == 1, (fname, line)
        text = text.replace(line, '')
        text = re.sub(r'@spritesheet (?:mall_currency|inventory-resources)\s*\{\s*src:[^;]*;\s*\}\s*', '', text)
        open(path, 'w', encoding='utf-8', newline='').write(text)


def build():
    import runpy
    for script in ('patch_inventory.py', 'patch_windows.py', 'patch_zone.py', 'patch_generic.py', 'patch_tabs.py', 'patch_overlays.py'):   # regenerate src/game pages from upstream
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
    restyle_glassui()
    restyle_gauge()
    currency_sheet()
    retarget_sprites()
    check_no_empty_sprite_blocks()
    window_css()
    monotone_pass()
    toml = os.path.join(OUT, 'theme.toml')
    text = re.sub(r'^name = ".*"', 'name = "%s"' % NAME, open(toml, encoding='utf-8').read(), flags=re.M)
    open(toml, 'w', encoding='utf-8', newline='').write(text)
    print('built', OUT)


def install():
    """Copy the build over the installed theme IN PLACE: files are overwritten one by one and stale ones removed afterwards,
    so the theme folder is never empty (a running game that reloads mid-install used to log 'Cant get file from vfs')."""
    import time
    os.makedirs(GAME, exist_ok=True)
    wanted = set()
    for dirpath, _, files in os.walk(OUT):
        rel_dir = os.path.relpath(dirpath, OUT)
        dst_dir = os.path.normpath(os.path.join(GAME, rel_dir))
        os.makedirs(dst_dir, exist_ok=True)
        for f in files:
            src, dst = os.path.join(dirpath, f), os.path.join(dst_dir, f)
            wanted.add(os.path.normcase(dst))
            for attempt in range(5):   # the game may hold a file open for a moment
                try:
                    shutil.copy2(src, dst)
                    break
                except PermissionError:
                    time.sleep(0.4)
            else:
                raise SystemExit('could not overwrite (in use?): ' + dst)
    for dirpath, _, files in os.walk(GAME, topdown=False):
        for f in files:
            full = os.path.join(dirpath, f)
            if os.path.normcase(full) not in wanted:
                os.remove(full)
        if dirpath != GAME and not os.listdir(dirpath):
            os.rmdir(dirpath)
    print('installed', GAME)


if __name__ == '__main__':
    build()
    if '--install' in sys.argv:
        install()
