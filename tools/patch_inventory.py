"""Turn the stock inventory page (upstream) into src/game/inventory.html with the glass styles."""
import os, re

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
# what each equipment slot holds (the stock GEN_INVSLOTnn pictures carry these words)
SLOT_LABELS = {1: 'Ring', 2: 'Necklace', 3: 'Earring', 4: 'Arrow', 5: 'Bullet', 6: 'Cannon', 7: 'Shield', 8: 'Weapon',
               17: 'Face', 18: 'Head', 19: 'Back', 20: 'Body', 21: 'Arms', 22: 'Foot',
               23: 'Body', 24: 'Engine', 25: 'Move', 26: 'Ability', 27: 'Weapon'}


def label(m):
    word = SLOT_LABELS[int(m.group(1))]
    return '%s<span class="gl-label%s">%s</span>' % (m.group(0), ' long' if len(word) > 6 else '', word)


s, n = re.subn(r'<img sprite="GEN_INVSLOT(\d\d)" /><item-slot id="[\w-]+" />', label, s)
assert n == 27, n
out = os.path.join(ROOT, 'src', 'game', 'inventory.html')
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, 'w', encoding='utf-8', newline='').write(s)
print('wrote', out)
