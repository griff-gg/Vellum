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
s = swap(s, '<button class="window-title-close" onclick="close"></button>',
         '<button class="window-title-close" onclick="close"><span>&#215;</span></button>')
out = os.path.join(ROOT, 'src', 'game', 'inventory.html')
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, 'w', encoding='utf-8', newline='').write(s)
print('wrote', out)
