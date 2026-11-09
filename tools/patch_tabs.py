"""Tabbed windows (see build.py TABSET_HEADERS / STRIP_HEADERS for the matching generated CSS).

TABSETS   pages with a static tabset of N tabs: tabs move to the title row (CSS) and get a sliding pill
          (div#gl-tab-slider + glass_tabs_header.lua reading gl-tab on each tab)
STRIPS    pages with a tab strip that is moved to the title row; optional data-bound sliding pill
OTHER     pages that only get the open animation (tabs stay where they are, static pill from the shared CSS)
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NL = chr(10)

TABSETS = {   # page -> number of tabs
    'game/clan.html': 2, 'game/friend_list.html': 2, 'game/mail.html': 2, 'game/personal_store.html': 2,
}
STRIPS = {    # page -> (old strip open tag, new strip open tag, slider markup placed first inside the strip)
    'game/storage.html': ('<div class="ui-tab-strip" id="storage-tabs">',
                          '<div class="ui-tab-strip gl-header-bar gl-slide" id="storage-tabs">',
                          '<div class="gl-slider" data-class-at1="tabs[1].active" data-class-at2="tabs[2].active" data-class-at3="tabs[3].active"></div>'),
    'game/avatar_store.html': ('<div class="ui-tab-strip">', '<div class="ui-tab-strip gl-slide">',
                               '<div class="gl-slider" data-class-at1="buy"></div>'),
    'game/npc_shop.html': ('<div class="ui-tab-strip" id="shop-tabs"', '<div class="ui-tab-strip gl-header-bar" id="shop-tabs"', ''),
    'game/skills.html': ('<div id="skills-tabs" class="skills-tab-row ui-tab-strip"',
                         '<div id="skills-tabs" class="skills-tab-row ui-tab-strip gl-header-bar"', ''),
}
OTHER = {     # nested tabset (Sell / Buy): only needs the ui-tab class so the shared glass tab rules apply
    'game/personal_store_management.html': [('<tab class="default">Sell</tab>', '<tab class="ui-tab default">Sell</tab>'),
                                            ('<tab class="default">Buy</tab>', '<tab class="ui-tab default">Buy</tab>')],
}

lua = open(os.path.join(ROOT, 'tools', 'glass_open.lua'), encoding='utf-8').read()
tabs_lua = open(os.path.join(ROOT, 'tools', 'glass_tabs_header.lua'), encoding='utf-8').read()
for text in (lua, tabs_lua):
    assert '<' not in text and '&' not in text   # the page is XML
KEYFRAMES = (NL + '@keyframes gl-open-a { 0% { opacity: 0; transform: translateY(5dp) scale(0.985); } 100% { opacity: 1; transform: translateY(0dp) scale(1); } }' +
             NL + '@keyframes gl-open-b { 0% { opacity: 0; transform: translateY(5dp) scale(0.985); } 100% { opacity: 1; transform: translateY(0dp) scale(1); } }' + NL)


def swap(s, old, new, name):
    assert s.count(old) == 1, (name, old)
    return s.replace(old, new)


def load(name):
    return open(os.path.join(ROOT, 'upstream', name), encoding='utf-8').read()


def save(name, s):
    out = os.path.join(ROOT, 'src', name)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8', newline='').write(s)


def finish(name, s, with_tabs_lua):
    extra = ('<script>' + NL + tabs_lua + '</script>' + NL) if with_tabs_lua else ''
    s = swap(s, '</head>', '<style>' + KEYFRAMES + '</style>' + NL + '<script>' + NL + lua + '</script>' + NL + extra + '</head>', name)
    save(name, s)


for name, n in TABSETS.items():
    s = load(name)
    assert len(re.findall(r'<tab[ >]', s)) == n, (name, len(re.findall(r'<tab[ >]', s)))
    i = [0]

    def number(m):
        k = i[0]
        i[0] += 1
        tag = m.group(0).replace('<tab ', '<tab gl-tab="%d" ' % k, 1)
        return tag.replace('class="default"', 'class="ui-tab default"')
    s = re.sub(r'<tab [^>]*>', number, s)
    first = s.index('<tabset')
    s = s[:first] + '<div class="gl-slider" id="gl-tab-slider"></div>' + NL + s[first:]
    finish(name, s, True)

for name, (old, new, slider) in STRIPS.items():
    s = load(name)
    s = swap(s, old, new, name)
    if slider:   # slider goes first inside the strip: find the end of that opening tag
        a = s.index(new) + len(new)
        a = s.index('>', a) + 1 if not new.endswith('>') else a
        s = s[:a] + slider + s[a:]
    finish(name, s, False)

for name, pairs in OTHER.items():
    s = load(name)
    for old, new in pairs:
        s = swap(s, old, new, name)
    finish(name, s, False)
print('patch_tabs: %d pages' % (len(TABSETS) + len(STRIPS) + len(OTHER)))
