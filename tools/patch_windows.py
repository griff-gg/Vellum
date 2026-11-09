"""Generate src/game pages for the windows that use the shared glass look (tools/glass_window.css):
the stock page plus the open animation script, and a x on the close button."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ('game_arena.html', 'group_manager.html')
NL = chr(10)
lua = open(os.path.join(ROOT, 'tools', 'glass_open.lua'), encoding='utf-8').read()
assert '<' not in lua and '&' not in lua   # the page is XML

for name in PAGES:
    s = open(os.path.join(ROOT, 'upstream', 'game', name), encoding='utf-8').read()
    assert s.count('</head>') == 1, name
    s = s.replace('</head>', '<script>' + NL + lua + '</script>' + NL + '</head>')
    out = os.path.join(ROOT, 'src', 'game', name)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8', newline='').write(s)
    print('wrote', out)
