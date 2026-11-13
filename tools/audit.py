"""Coverage and sanity audit of the built Glass theme: python tools/audit.py"""
import glob, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def pages(base):
    return sorted(p.replace(os.sep, '/')[len(base) + 1:] for d in ('game', 'common', 'external')
                  for p in glob.glob(os.path.join(base, d, '*.html')))


up, done = pages('upstream'), set(pages('src'))
print('pages in upstream: %d, glass-patched: %d' % (len(up), len(done)))
print('UNTOUCHED (stock):', [p for p in up if p not in done])

src = open('tools/build.py', encoding='utf-8').read()
block = src[src.index('GLASS_WINDOWS = ('):]
block = block[:block.index(')\n') + 1]
ids = re.findall(r"'([^']+)'", block)
pid = set()
for p in pages('build/glass'):
    pid |= set(re.findall(r'\bid="([^"]+)"', open(os.path.join('build/glass', p), encoding='utf-8').read()))
print('%d window ids; unmatched: %s' % (len(ids), [i for i in ids if i.lstrip('#').split(' ')[0] not in pid]))

defined = set(re.findall(r'^\s+(gl-[\w-]+):', open('build/glass/styles/glass_frame.css').read(), flags=re.M))
used = set()
files = glob.glob('build/glass/styles/glass_*.css') + [os.path.join('build/glass', p) for p in pages('build/glass')]
for f in files:
    if f.endswith('glass_frame.css'):
        continue
    used |= set(re.findall(r'(?<![\w-])(gl-(?:[a-z0-9]+-)*[a-z0-9]+)(?=[,)\s;])', open(f, encoding='utf-8').read()))
skip = ('gl-open', 'gl-shown', 'gl-slider', 'gl-rail', 'gl-label', 'gl-opt-', 'gl-arena', 'gl-header', 'gl-tab', 'gl-dn', 'gl-day', 'gl-night',
        'gl-mq', 'gl-pill-a', 'gl-pill-b', 'gl-panel', 'gl-tk', 'gl-tick', 'gl-slide', 'gl-island', 'gl-zn', 'gl-drop', 'gl-zt', 'gl-dyn', 'gl-st-', 'gl-strips', 'gl-ix')
print('MISSING sprites:', sorted(n for n in used if n not in defined and not n.startswith(skip)))
print('sprites defined:', len(defined))
