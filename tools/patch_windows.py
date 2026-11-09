"""Generate the src/game pages for glass windows from the stock pages.

PAGES      windows on the shared glass look (tools/glass_window.css): + the open animation script
OVERLAYS   HUD, party and group overlays (tools/glass_hud.css): + that stylesheet; party/group get a glass-blue fill
           colour (the page computes it from the opacity setting) and a firmer default opacity
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ('game_arena.html', 'group_manager.html', 'options_bgfx.html')
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
        # like the inventory: explicit header (title, close, tabs) and a content div, instead of the template's body
        a = s.index('<div class="ui-tab-strip">')
        b = s.index('</div>', a) + len('</div>')
        strip = s[a:b]
        s = s[:a] + s[b:]
        strip = strip.replace('<div class="ui-tab-strip">',
                              '<div class="ui-tab-strip gl-header-tabs"><div class="gl-slider" id="gl-arena-slider"></div>')
        body_open = '<body open-sound="3" close-sound="4" template="window-fixed-size" id="game-arena">'
        s = swap(s, body_open, '<body open-sound="3" close-sound="4" class="window-fixed-size" id="game-arena">' + NL +
                 '<handle class="window-title" move_target="#document" id="window-title-text"></handle>' + NL +
                 '<button class="window-title-close" onclick="close"></button>' + NL + strip + NL +
                 '<div id="window-content">', name)
        s = swap(s, '</body>', '</div>' + NL + '</body>', name)
        extra = '<script>' + NL + arena_tabs + '</script>' + NL
    if name == 'options_bgfx.html':   # tabs become a sliding pill bar in the title row
        opt_tabs = open(os.path.join(ROOT, 'tools', 'glass_tabs_options.lua'), encoding='utf-8').read()
        assert '<' not in opt_tabs and '&' not in opt_tabs
        extra = '<script>' + NL + opt_tabs + '</script>' + NL + '<link type="text/rcss" href="../styles/glass_options.css" />' + NL
        for i, old in enumerate(('<tab class="ui-tab"><str string-id="478">Video</str></tab>',
                                 '<tab class="ui-tab"><str string-id="479">Audio</str></tab>',
                                 '<tab class="ui-tab"><str string-id="480">Interface</str></tab>',
                                 '<tab class="ui-tab"><str string-id="1366">Game</str></tab>',
                                 '<tab class="ui-tab">Key Bindings</tab>',
                                 '<tab class="ui-tab">Gamepad</tab>',
                                 '<tab id="chat-options-tab" class="ui-tab">Chat</tab>')):
            s = swap(s, old, old.replace('<tab ', '<tab gl-tab="%d" ' % i, 1), name)
        s = swap(s, '<tabset id="options-tabs">', '<div class="gl-slider gl-opt-slider" id="gl-opt-slider"></div>' + NL +
                 '<tabset id="options-tabs">', name)
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


# ---- minimap: rounded-square viewport, glass day/night glyphs, simpler gift blink, glass stylesheet
name = 'minimap.html'
s = load(name)
s = swap(s, 'mask-radius="50%"', 'mask-radius="7%"', name)
s = swap(s, '<img data-if="!is_day" sprite="GEN_DECO09" class="day-night-icon"/>', '<span data-if="!is_day" class="gl-dn gl-night"></span>', name)
s = swap(s, '<img data-if="is_day" sprite="GEN_DECO10" class="day-night-icon"/>', '<span data-if="is_day" class="gl-dn gl-day"></span>', name)
s = swap(s, '<span style="color: rgb(131, 147, 202)">', '<span style="color: rgb(255, 255, 255)">', name)
s = swap(s, """                0% { decorator: image(GEN_BTN106); }
                50% { decorator: image(GEN_BTN109); }
                100% { decorator: image(GEN_BTN106); }""", """                0% { opacity: 1; }
                50% { opacity: 0.35; }
                100% { opacity: 1; }""", name)
# item mall button removed (Alt+B still opens it)
i = s.index('<!-- Item Mall button -->')
j = s.index('</button>', i) + len('</button>')
s = s[:i] + s[j:]
# long zone names scroll inside their box (Spotify style); the collapsed pill shows the coordinates too
s = swap(s, '<span id="zone-name">{{zone_name}}</span>', '<masked id="zone-name" mask-radius="5%"><span id="zone-name-text" class="gl-mq">{{zone_name}}</span></masked>', name)
s = swap(s, '<span id="zone-name-min">{{zone_name}}</span>', '<masked id="zone-name-min" mask-radius="5%"><span id="zone-name-min-text" class="gl-mq">{{zone_name}}</span></masked>', name)
s = swap(s, '<span id="time-min">{{server_time}}</span>', '<span id="time-min">{{server_time}}</span>' + NL + '<span id="coords-min">{{player_coordinates}}</span>', name)
s = swap(s, '<div id="minimap-root" data-model="minimap">', '<div id="minimap-root" data-model="minimap">' + NL + '<div id="gl-tick"></div>', name)
mm_lua = open(os.path.join(ROOT, 'tools', 'glass_minimap.lua'), encoding='utf-8').read()
assert '<' not in mm_lua and '&' not in mm_lua
kf = ['@keyframes gl-pill-a { from { opacity: 0; transform: scale(1.1, 1.1); } to { opacity: 1; transform: scale(1, 1); } }',
      '@keyframes gl-pill-b { from { opacity: 0; transform: scale(1.1, 1.1); } to { opacity: 1; transform: scale(1, 1); } }',
      '@keyframes gl-panel-a { from { opacity: 0; transform: scale(0.9, 0.9); } to { opacity: 1; transform: scale(1, 1); } }',
      '@keyframes gl-panel-b { from { opacity: 0; transform: scale(0.9, 0.9); } to { opacity: 1; transform: scale(1, 1); } }',
      '@keyframes gl-tk-a { from { opacity: 0; } to { opacity: 0.02; } }',
      '@keyframes gl-tk-b { from { opacity: 0; } to { opacity: 0.02; } }',
      '#gl-tick { position: absolute; left: 0dp; top: 0dp; width: 1dp; height: 1dp; opacity: 0; pointer-events: none; }',
      '#gl-tick.tk-a { animation: 1.2s linear 1 gl-tk-a; }', '#gl-tick.tk-b { animation: 1.2s linear 1 gl-tk-b; }']
for n in range(4, 164, 4):   # marquee: hold, slide n dp, hold, slide back; about 14 dp per second
    kf.append('@keyframes gl-mq-%d { 0%% { left: 0dp; } 16%% { left: 0dp; } 50%% { left: -%ddp; } 66%% { left: -%ddp; } 100%% { left: 0dp; } }' % (n, n, n))
    kf.append('.mq-%d { animation: %ds linear infinite gl-mq-%d; }' % (n, max(4, int(n * 0.21 + 0.5)), n))
s = swap(s, '    </head>', '        <style>' + NL + NL.join(kf) + NL + '</style>' + NL + '<script>' + NL + mm_lua + '</script>' + NL +
         '        <link type="text/rcss" href="../styles/glass_minimap.css" />' + NL + '    </head>', name)
save(name, s)
