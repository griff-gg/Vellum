"""Turn the stock inventory page (upstream) into src/game/inventory.html with the glass styles and the effect test."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = open(os.path.join(ROOT, 'upstream', 'game', 'inventory.html'), encoding='utf-8').read()
css = open(os.path.join(ROOT, 'tools', 'glass_inventory.css'), encoding='utf-8').read()
lua = open(os.path.join(ROOT, 'tools', 'glass_probe.lua'), encoding='utf-8').read()
assert '<' not in lua and '&' not in lua   # the page is XML


def swap(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


s = swap(s, '        </style>', css + '        </style>')
s = swap(s, '    </head>', '        <script>\n' + lua + '        </script>\n    </head>')
s = swap(s, '<button class="window-title-close" onclick="close"></button>',
         '<button class="window-title-close" onclick="close"><span>&#215;</span></button>')
chips = ''.join('<div id="gp-%s">%s</div>' % (t, t.upper()) for t in ('grad', 'glow', 'hard', 'inset', 'drop', 'blur'))
s = swap(s, '        </div>\n    </body>',
         '            <div id="glass-probe">' + chips + '</div>\n'
         '            <div id="gp-demo">click a test above</div>\n'
         '        </div>\n    </body>')
out = os.path.join(ROOT, 'src', 'game', 'inventory.html')
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, 'w', encoding='utf-8', newline='').write(s)
print('wrote', out)
