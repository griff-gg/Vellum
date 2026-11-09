"""Generate the src/game pages for glass windows from the stock pages.

PAGES      windows on the shared glass look (tools/glass_window.css): + the open animation script
OVERLAYS   HUD, party and group overlays (tools/glass_hud.css): + that stylesheet; party/group get a glass-blue fill
           colour (the page computes it from the opacity setting) and a firmer default opacity
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ('game_arena.html', 'group_manager.html')
OVERLAYS = ('hud.html', 'party.html', 'arena_group.html')
NL = chr(10)
lua = open(os.path.join(ROOT, 'tools', 'glass_open.lua'), encoding='utf-8').read()
assert '<' not in lua and '&' not in lua   # the page is XML


def load(name):
    return open(os.path.join(ROOT, 'upstream', 'game', name), encoding='utf-8').read()


def save(name, s):
    out = os.path.join(ROOT, 'src', 'game', name)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8', newline='').write(s)
    print('wrote', out)


def swap(s, old, new, name):
    assert s.count(old) == 1, (name, old)
    return s.replace(old, new)


# The inventory (which animates fine) carries its keyframes inside the page, so these pages do too.
KEYFRAMES = (NL + '@keyframes gl-open-a { 0% { opacity: 0; transform: translateY(5dp) scale(0.985); } 100% { opacity: 1; transform: translateY(0dp) scale(1); } }' +
             NL + '@keyframes gl-open-b { 0% { opacity: 0; transform: translateY(5dp) scale(0.985); } 100% { opacity: 1; transform: translateY(0dp) scale(1); } }' + NL)

arena_tabs = open(os.path.join(ROOT, 'tools', 'glass_tabs_arena.lua'), encoding='utf-8').read()
assert '<' not in arena_tabs and '&' not in arena_tabs

for name in PAGES:
    s = load(name)
    extra = ''
    if name == 'game_arena.html':   # sliding pill under the All / Dungeons / PvP tabs
        s = swap(s, '<div class="ui-tab-strip">', '<div class="ui-tab-strip"><div class="gl-slider" id="gl-arena-slider"></div>', name)
        extra = '<script>' + NL + arena_tabs + '</script>' + NL
    s = swap(s, '</head>', '<style>' + KEYFRAMES + '</style>' + NL + '<script>' + NL + lua + '</script>' + NL + extra + '</head>', name)
    save(name, s)

for name in OVERLAYS:
    s = load(name)
    s = swap(s, '    </head>' if '    </head>' in s else '</head>',
             '        <link type="text/rcss" href="../styles/glass_hud.css" />' + NL + '    </head>', name)
    if name != 'hud.html':
        s = swap(s, "'rgba(0, 0, 0, '", "'rgba(26, 30, 40, '", name)
        s = swap(s, 'default-background-opacity="25"', 'default-background-opacity="55"', name)
    save(name, s)
