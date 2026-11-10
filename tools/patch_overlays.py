"""Overlay and HUD-style pages: add the glass stylesheets (and the sprite sheet when the page has no window template that
already links it). The rules themselves live in tools/glass_overlays.css and the generated glass_menu.css."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NL = chr(10)

PAGES = [   # (page, extra stylesheet or None)
    ('game/menu.html', 'glass_menu.css'),
    ('game/quickbar.html', None),
    ('game/chat_box.html', None),
    ('game/quest_tracker.html', None),
    ('game/summon_gauge.html', None),
    ('game/duel_scoreboard.html', None),
    ('game/announce.html', None),
    ('game/system_message.html', None),
    ('game/store_signs.html', None),
    ('game/speech_bubbles.html', None),
    ('game/focused_target.html', 'glass_gauge.css'),
    ('game/monster_nameplates.html', 'glass_gauge.css'),
    ('game/npc_nameplates.html', 'glass_gauge.css'),
    ('game/skill_hud.html', None),
    ('game/notification_buttons.html', None),
    ('common/modal_overlay.html', None),
    ('external/login.html', None),
    ('external/login_queue.html', None),
]

for name, extra in PAGES:
    s = open(os.path.join(ROOT, 'upstream', name), encoding='utf-8').read()
    links = []
    if 'type="text/template"' not in s:   # no window template: the sprite sheet is not loaded yet
        links.append('<link type="text/rcss" href="../styles/glass_frame.css" />')
    if extra:
        links.append('<link type="text/rcss" href="../styles/%s" />' % extra)
    links.append('<link type="text/rcss" href="../styles/glass_overlays.css" />')
    assert s.count('</head>') == 1, name
    if name == 'game/menu.html':   # the toggle flips its chevron with the open state
        old = '<button id="menu-toggle" data-event-click="expanded = !expanded" />'
        assert s.count(old) == 1, old
        s = s.replace(old, '<button id="menu-toggle" data-event-click="expanded = !expanded" data-class-open="expanded" />')
    s = s.replace('</head>', NL.join(links) + NL + '</head>')
    out = os.path.join(ROOT, 'src', name)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8', newline='').write(s)
print('patch_overlays: %d pages' % len(PAGES))
