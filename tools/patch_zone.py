"""Zone notice (game/zone_notice.html): a compact glass pill at the top centre that drops in like the Dynamic Island."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NL = chr(10)
name = 'zone_notice.html'
s = open(os.path.join(ROOT, 'upstream', 'game', name), encoding='utf-8').read()


def swap(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


lua = open(os.path.join(ROOT, 'tools', 'glass_zone.lua'), encoding='utf-8').read()
assert '<' not in lua and '&' not in lua   # the page is XML

css = '''
            /* glass pill, centred at the top: the body keeps the game's 90% wide, centred text box */
            body#game-zone-notice { top: 8dp; font-effect: none; }
            #gl-island {
                display: inline-block; max-width: 420dp; padding: 12dp 28dp 12dp 28dp; transform-origin: 50% 0% 0;
                decorator: tiled-box(gl-hud-tl, gl-hud-t, gl-hud-tr, gl-hud-l, gl-hud-c, gl-hud-r, gl-hud-bl, gl-hud-b, gl-hud-br);
            }
            #game-zone-notice #zone-name {
                font-size: 13dp; line-height: 18dp; margin-bottom: 0dp; font-weight: 800; color: rgb(255, 255, 255);
                text-transform: uppercase; letter-spacing: 1.8dp; font-effect: shadow(0dp 1dp rgba(0, 0, 0, 130));
            }
            #game-zone-notice #zone-description {
                font-size: 11dp; line-height: 15dp; margin-top: 2dp; color: rgba(255, 255, 255, 190);
                font-effect: shadow(0dp 1dp rgba(0, 0, 0, 120));
            }
            #gl-zn-tick { position: absolute; left: 0dp; top: 0dp; width: 1dp; height: 1dp; opacity: 0; pointer-events: none; }
            #gl-zn-tick.tk-a { animation: 0.3s linear 1 gl-zt-a; }
            #gl-zn-tick.tk-b { animation: 0.3s linear 1 gl-zt-b; }
            @keyframes gl-zt-a { from { opacity: 0; } to { opacity: 0.02; } }
            @keyframes gl-zt-b { from { opacity: 0; } to { opacity: 0.02; } }
            @keyframes gl-drop-a { from { transform: translateY(-80dp) scale(0.55, 0.55); } to { transform: translateY(0dp) scale(1, 1); } }
            @keyframes gl-drop-b { from { transform: translateY(-80dp) scale(0.55, 0.55); } to { transform: translateY(0dp) scale(1, 1); } }
'''
s = swap(s, '        </style>', css + '        </style>' + NL + '        <link type="text/rcss" href="../styles/glass_frame.css" />' + NL +
         '        <script>' + NL + lua + '        </script>')
old = '''        <div data-model="zone-notice">
            <div id="zone-name" class="ui-section-title">{{ name }}</div>
            <div id="zone-description" class="ui-banner-text">{{ description }}</div>
        </div>'''
new = '''        <div data-model="zone-notice">
            <div id="gl-island">
                <div id="gl-zn-tick"></div>
                <div id="zone-name" class="ui-section-title">{{ name }}</div>
                <div id="zone-description" class="ui-banner-text" data-if="description != ''">{{ description }}</div>
            </div>
        </div>'''
s = swap(s, old, new)
out = os.path.join(ROOT, 'src', 'game', name)
open(out, 'w', encoding='utf-8', newline='').write(s)
print('wrote', out)
