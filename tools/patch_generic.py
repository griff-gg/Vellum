"""Glass windows that only need the shared look (tools/glass_window.css) plus the open animation:
the stock page + inline keyframes + the open script. PAGES maps a page path (relative to upstream/) to a list of
extra (old, new) text swaps. The window ids that match these pages live in build.py GLASS_WINDOWS."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NL = chr(10)

PAGES = {
    'game/char_actions.html': [],
    'game/character_preview.html': [],
    'game/character_stats.html': [],
    'game/choice_box.html': [],
    'game/clan_create.html': [],
    'game/disassembly.html': [],
    'game/duel.html': [],
    'game/empowerment.html': [],
    'game/mall_cart.html': [],
    'game/mall_storage.html': [],
    'game/monster_inspector.html': [],
    'game/npc_dialog.html': [],
    'game/npc_transaction.html': [],
    'game/number_input.html': [],
    'game/party_finder.html': [],
    'game/party_options.html': [],
    'game/personal_store_price.html': [],
    'game/player_trade.html': [],
    'game/private_chat.html': [],
    'game/quest_list.html': [],
    'game/refine.html': [],
    'game/reinforcement.html': [],
    'game/respawn.html': [],
    'game/style_change.html': [],
    'game/tutorial.html': [],
    'game/world_map.html': [],
    'game/gamearena_scoreboard.html': [],
    'game/personal_vending.html': [],
    'game/item_mall.html': [],
    'common/message_box.html': [],
    'external/character_create.html': [],
    'external/tos.html': [],
    'external/avatar_selection.html': [],
    'game/crafting.html': [],
    # the system menu has no body id; the shared rules need one
    'game/system_menu.html': [('<body open-sound="3" close-sound="4" template="window-fixed-size">',
                               '<body id="game-system-menu" open-sound="3" close-sound="4" template="window-fixed-size">')],
}

lua = open(os.path.join(ROOT, 'tools', 'glass_open.lua'), encoding='utf-8').read()
assert '<' not in lua and '&' not in lua   # the page is XML
KEYFRAMES = (NL + '@keyframes gl-open-a { 0% { opacity: 0; transform: translateY(5dp) scale(0.985); } 100% { opacity: 1; transform: translateY(0dp) scale(1); } }' +
             NL + '@keyframes gl-open-b { 0% { opacity: 0; transform: translateY(5dp) scale(0.985); } 100% { opacity: 1; transform: translateY(0dp) scale(1); } }' + NL)


def swap(s, old, new, name):
    assert s.count(old) == 1, (name, old)
    return s.replace(old, new)


for name, extra in PAGES.items():
    s = open(os.path.join(ROOT, 'upstream', name), encoding='utf-8').read()
    for old, new in extra:
        s = swap(s, old, new, name)
    s = swap(s, '</head>', '<style>' + KEYFRAMES + '</style>' + NL + '<script>' + NL + lua + '</script>' + NL + '</head>', name)
    out = os.path.join(ROOT, 'src', name)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8', newline='').write(s)
print('patch_generic: %d pages' % len(PAGES))
