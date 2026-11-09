"""Turn the stock inventory page (upstream) into src/game/inventory.html with the glass styles."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = open(os.path.join(ROOT, 'upstream', 'game', 'inventory.html'), encoding='utf-8').read()
css = open(os.path.join(ROOT, 'tools', 'glass_inventory.css'), encoding='utf-8').read()


def swap(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


s = swap(s, '        <style>', '        <link type="text/rcss" href="../styles/glass_frame.css" />\n        <style>')
s = swap(s, '        </style>', css + '        </style>')
lua = open(os.path.join(ROOT, 'tools', 'glass_open.lua'), encoding='utf-8').read()
assert '<' not in lua and '&' not in lua   # the page is XML
NL = chr(10)
s = swap(s, '    </head>', '        <script>' + NL + lua + '        </script>' + NL + '    </head>')
s = swap(s, '<button class="window-title-close" onclick="close"></button>',
         '<button class="window-title-close" onclick="close"><span>&#215;</span></button>')
# sliding glass pills (tab order: Avatar = mode 1, Costume = mode 0, PAT = mode 2; bags 0, 1, 2)
s = swap(s, '<div class="inventory-mode-tabs">',
         '<div class="inventory-mode-tabs"><div class="gl-slider" data-class-at1="mode == 0" data-class-at2="mode == 2"></div>')
s = swap(s, '<div class="ui-tab-strip" id="inventory-bag-tabs">',
         '<div class="ui-tab-strip" id="inventory-bag-tabs"><div class="gl-slider" data-if="mode != 2"'
         ' data-class-at1="bag == 1" data-class-at2="bag == 2"></div>')
out = os.path.join(ROOT, 'src', 'game', 'inventory.html')
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, 'w', encoding='utf-8', newline='').write(s)
print('wrote', out)
