"""Generated glass art. The game can't draw CSS shadows, blur or gradients, so depth is baked into 9-slice images."""
import struct

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SS = 4          # supersampling while drawing
RES = 2         # sprite pixels per dp (sheet uses resolution: 2x)


def write_dds(path, img):
    """Uncompressed 32-bit RGBA DDS (same header layout as the stock glassui_0.dds)."""
    img = img.convert('RGBA')
    w, h = img.size
    hdr = bytearray(128)
    hdr[0:4] = b'DDS '
    struct.pack_into('<IIIIIII', hdr, 4, 124, 0x2100F, h, w, w * 4, 0, 1)
    struct.pack_into('<II', hdr, 76, 32, 0x41)
    struct.pack_into('<IIIII', hdr, 88, 32, 0xFF, 0xFF00, 0xFF0000, 0xFF000000)
    struct.pack_into('<I', hdr, 108, 0x1000)
    with open(path, 'wb') as f:
        f.write(hdr)
        f.write(img.tobytes())


def _mask(size, box, radius):
    m = Image.new('L', size, 0)
    ImageDraw.Draw(m).rounded_rectangle(box, radius=radius, fill=255)
    return np.asarray(m, dtype=np.float32) / 255.0


def glass_panel(margin, radius, tint, rim_top, rim_mid, rim_bottom, sheen, shadow, shadow_dy, shadow_blur, edge=4):
    """One 9-slice glass panel.

    margin  dp of shadow room around the glass (the element's padding must cover it)
    radius  corner radius of the glass in dp
    Returns (image at RES, corner size in sprite px, edge size in sprite px).
    """
    k = RES * SS
    corner = (margin + radius) * k
    n = 2 * corner + edge * k
    size = (n, n)
    m = margin * k
    glass = _mask(size, (m, m, n - 1 - m, n - 1 - m), radius * k)
    inner = _mask(size, (m + k, m + k, n - 1 - m - k, n - 1 - m - k), max(radius - 1, 1) * k)
    rim = np.clip(glass - inner, 0, 1)

    # soft shadow below the glass, only outside it so the glass tint stays clean
    sh = Image.new('L', size, 0)
    dy = shadow_dy * k
    ImageDraw.Draw(sh).rounded_rectangle((m, m + dy, n - 1 - m, n - 1 - m + dy), radius=radius * k, fill=255)
    sh = np.asarray(sh.filter(ImageFilter.GaussianBlur(shadow_blur * k)), dtype=np.float32) / 255.0
    sh_a = sh * (1 - glass) * shadow / 255.0

    # rim brightness by height: bright top corners, even sides, dim bottom (light from above)
    y = np.arange(n, dtype=np.float32)[:, None] * np.ones((1, n), np.float32)
    top = np.clip((y - m) / (corner - m), 0, 1)
    bot = np.clip((y - (n - corner)) / (corner - m), 0, 1)
    rim_a = np.where(y < corner, rim_top + (rim_mid - rim_top) * top,
                     np.where(y >= n - corner, rim_mid + (rim_bottom - rim_mid) * bot, rim_mid)) / 255.0

    # faint white sheen at the top of the glass, gone by the end of the corner band
    sheen_a = glass * np.clip(1 - (y - m) / (corner - m), 0, 1) ** 2 * sheen / 255.0

    out = np.zeros((n, n, 4), np.float32)
    # shadow (black) under everything
    out[..., 3] = sh_a
    # glass tint over it
    ta = glass * tint[3] / 255.0
    for i in range(3):
        out[..., i] = tint[i] / 255.0 * ta
    out[..., 3] = ta + out[..., 3] * (1 - ta)
    # white layers: sheen, then rim (premultiplied "over")
    for a in (sheen_a, rim * rim_a):
        for i in range(3):
            out[..., i] = a + out[..., i] * (1 - a)
        out[..., 3] = a + out[..., 3] * (1 - a)
    rgb = np.where(out[..., 3:4] > 0, out[..., :3] / np.maximum(out[..., 3:4], 1e-6), 0)
    img = np.dstack([rgb, out[..., 3:4]])
    img = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA')
    img = img.resize((n // SS, n // SS), Image.LANCZOS)
    return img, corner // SS, edge * RES


def slices(prefix, x0, y0, corner, edge):
    """Sprite rects (name -> x y w h in sprite px) for a 9-slice laid out at x0,y0."""
    c, e = corner, edge
    cols = ((x0, c), (x0 + c, e), (x0 + c + e, c))
    rows = ((y0, c), (y0 + c, e), (y0 + c + e, c))
    names = (('tl', 't', 'tr'), ('l', 'c', 'r'), ('bl', 'b', 'br'))
    out = {}
    for r, (yy, hh) in enumerate(rows):
        for q, (xx, ww) in enumerate(cols):
            out['%s-%s' % (prefix, names[r][q])] = (xx, yy, ww, hh)
    return out


def sweep(w=160, h=480, angle=10, core=(3.0, 95), soft=(14.0, 55)):
    """A soft diagonal streak of light (1 px per dp), brighter towards the top; moved across a window on open."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    t = np.radians(angle)
    d = (x - w / 2) * np.cos(t) + (y - h / 2) * np.sin(t)      # distance from the streak's centre line
    a = soft[1] * np.exp(-(d / soft[0]) ** 2) + core[1] * np.exp(-(d / core[0]) ** 2)
    a *= 1.0 - 0.65 * (y / h)                                   # light from above
    img = np.zeros((h, w, 4), np.uint8)
    img[..., :3] = 255
    img[..., 3] = np.clip(a, 0, 255).astype(np.uint8)
    return Image.fromarray(img, 'RGBA')


def close_icon(hover, radius=13):
    """Round glass close button with a thin x (one sprite, 2 px per dp)."""
    img, _, _ = glass_panel(margin=0, radius=radius, tint=(255, 255, 255, 72 if hover else 42),
                            rim_top=245 if hover else 225, rim_mid=150 if hover else 110, rim_bottom=95 if hover else 70,
                            sheen=70 if hover else 50, shadow=0, shadow_dy=0, shadow_blur=1, edge=0)
    k = 8
    n = img.width * k // 1
    glyph = Image.new('L', (n, n), 0)
    d = ImageDraw.Draw(glyph)
    c, r, wd = n / 2, n * 0.19, int(n * 0.07)
    d.line((c - r, c - r, c + r, c + r), fill=255, width=wd)
    d.line((c - r, c + r, c + r, c - r), fill=255, width=wd)
    glyph = glyph.resize(img.size, Image.LANCZOS)
    white = Image.new('RGBA', img.size, (255, 255, 255, 255))
    white.putalpha(glyph.point(lambda v: int(v * (1.0 if hover else 0.92))))
    out = img.copy()
    out.alpha_composite(white)
    return out


def gauge_fill(w, h, radius, top, bottom, alpha, rim, rim_a, hl_a, inset=0.5, res=RES, ss=SS):
    """A gauge fill: rounded bar (w x h dp) with a vertical colour gradient, thin rim and a bright top line."""
    k = res * ss
    W, H = w * k, h * k
    ins = int(inset * res * ss)                # breathing room (dp) between the groove and the bar
    rw = ss                                    # rim width, 1 final px
    mask = _mask((W, H), (ins, ins, W - 1 - ins, H - 1 - ins), max(radius * k - ins, 1))
    inner = _mask((W, H), (ins + rw, ins + rw, W - 1 - ins - rw, H - 1 - ins - rw), max(radius * k - ins - rw, 1))
    rim_m = np.clip(mask - inner, 0, 1)
    t = (np.arange(H, dtype=np.float32) / max(H - 1, 1))[:, None] * np.ones((1, W), np.float32)
    col = np.zeros((H, W, 3), np.float32)
    for i in range(3):
        col[..., i] = (top[i] + (bottom[i] - top[i]) * t) / 255.0
    y = np.arange(H, dtype=np.float32)[:, None] * np.ones((1, W), np.float32)
    hl = ((y >= ins + rw) & (y < ins + rw + rw * 2)).astype(np.float32) * inner * hl_a / 255.0
    out = np.zeros((H, W, 4), np.float32)
    a = inner * alpha / 255.0
    out[..., :3] = col * a[..., None]
    out[..., 3] = a
    for layer, c in ((rim_m * rim_a / 255.0, rim), (hl, (255, 255, 255))):
        for i in range(3):
            out[..., i] = (c[i] / 255.0) * layer + out[..., i] * (1 - layer)
        out[..., 3] = layer + out[..., 3] * (1 - layer)
    rgb = np.where(out[..., 3:4] > 0, out[..., :3] / np.maximum(out[..., 3:4], 1e-6), 0)
    img = Image.fromarray((np.clip(np.dstack([rgb, out[..., 3:4]]), 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA')
    return img.resize((W // ss, H // ss), Image.LANCZOS)


def _glyph(kind, n):
    """Mask (L, n x n) of a monochrome icon glyph, drawn white."""
    g = Image.new('L', (n, n), 0)
    d = ImageDraw.Draw(g)
    c, wd = n / 2, max(int(n * 0.075), 2)
    if kind == 'options':
        r = n * 0.06
        for dx in (-0.22, 0, 0.22):
            d.ellipse((c + dx * n - r, c - r, c + dx * n + r, c + r), fill=255)
    elif kind == 'leave':
        d.line([(c - 0.02 * n, c - 0.22 * n), (c - 0.22 * n, c - 0.22 * n), (c - 0.22 * n, c + 0.22 * n),
                (c - 0.02 * n, c + 0.22 * n)], fill=255, width=wd, joint='curve')
        d.line((c - 0.1 * n, c, c + 0.24 * n, c), fill=255, width=wd)
        d.line([(c + 0.11 * n, c - 0.12 * n), (c + 0.24 * n, c), (c + 0.11 * n, c + 0.12 * n)], fill=255, width=wd, joint='curve')
    elif kind == 'kick':
        r = n * 0.085
        d.ellipse((c - 0.07 * n - r, c - 0.14 * n - r, c - 0.07 * n + r, c - 0.14 * n + r), outline=255, width=wd)
        d.arc((c - 0.25 * n, c - 0.01 * n, c + 0.11 * n, c + 0.35 * n), 180, 360, fill=255, width=wd)
        d.line((c + 0.12 * n, c + 0.02 * n, c + 0.28 * n, c + 0.02 * n), fill=255, width=wd)
    elif kind == 'entrust':
        pts = []
        for i in range(10):
            ang = -np.pi / 2 + i * np.pi / 5
            rr = n * (0.25 if i % 2 == 0 else 0.105)
            pts.append((c + rr * np.cos(ang), c + 0.02 * n + rr * np.sin(ang)))
        d.polygon(pts, fill=255)
    return g


def round_icon(kind, state, radius=10):
    """Round glass toolbar button with a white glyph. state: 'n' normal, 'h' hover, 'd' disabled (2 px per dp)."""
    tint, rt, rm, rb, sh, ga = {'n': (42, 225, 110, 70, 50, 0.92), 'h': (78, 245, 150, 95, 80, 1.0),
                                'd': (16, 90, 50, 30, 14, 0.38)}[state]
    img, _, _ = glass_panel(margin=0, radius=radius, tint=(255, 255, 255, tint), rim_top=rt, rim_mid=rm,
                            rim_bottom=rb, sheen=sh, shadow=0, shadow_dy=0, shadow_blur=1, edge=0)
    k = 8
    g = _glyph(kind, img.width * k).resize(img.size, Image.LANCZOS)
    white = Image.new('RGBA', img.size, (255, 255, 255, 255))
    white.putalpha(g.point(lambda v: int(v * ga)))
    out = img.copy()
    out.alpha_composite(white)
    return out


def knob(hover, radius=9):
    """Round glass knob for range sliders."""
    img, _, _ = glass_panel(margin=0, radius=radius, tint=(255, 255, 255, 215 if hover else 185),
                            rim_top=255, rim_mid=200 if hover else 170, rim_bottom=150 if hover else 120,
                            sheen=90, shadow=0, shadow_dy=0, shadow_blur=1, edge=0)
    return img
