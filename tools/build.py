"""Build the Glass theme: upstream/ (stock theme) + src/ overrides -> build/glass.

    python tools/build.py            build
    python tools/build.py --install  build and copy to the game's data/ui/themes/glass
"""
import os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UP, SRC, OUT = (os.path.join(ROOT, p) for p in ('upstream', 'src', os.path.join('build', 'glass')))
GAME = r'C:\Program Files\ROSE Online\data\ui\themes\glass'
NAME = 'Glass (test)'


def build():
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(UP, OUT)
    for dirpath, _, files in os.walk(SRC):
        for f in files:
            src = os.path.join(dirpath, f)
            dst = os.path.join(OUT, os.path.relpath(src, SRC))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    toml = os.path.join(OUT, 'theme.toml')
    text = re.sub(r'^name = ".*"', 'name = "%s"' % NAME, open(toml, encoding='utf-8').read(), flags=re.M)
    open(toml, 'w', encoding='utf-8', newline='').write(text)
    print('built', OUT)


if __name__ == '__main__':
    build()
    if '--install' in sys.argv:
        shutil.rmtree(GAME, ignore_errors=True)
        shutil.copytree(OUT, GAME)
        print('installed', GAME)
