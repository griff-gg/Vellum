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


def glass_panel(margin, radius, tint, rim_top, rim_mid, rim_bottom, sheen, shadow, shadow_dy, shadow_blur, edge=4,
                inner_top=0):
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
    # fade the shadow to nothing before the image edge, so a wide blur is never cut off in a straight line
    if margin > 0:
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
        to_edge = np.minimum(np.minimum(xx, n - 1 - xx), np.minimum(yy, n - 1 - yy))
        t = np.clip(to_edge / (m * 0.8), 0, 1)
        sh = sh * (t * t * (3 - 2 * t))
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
    # recessed look: a dark inner edge along the top that fades out over 3dp (inner_top = its strength)
    if inner_top:
        a = glass * np.clip(1 - (y - m) / (3 * k), 0, 1) ** 2 * inner_top / 255.0
        for i in range(3):
            out[..., i] = out[..., i] * (1 - a)
        out[..., 3] = a + out[..., 3] * (1 - a)
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


def gauge_fill(w, h, radius, top, bottom, alpha, rim, rim_a, hl_a, inset=0.5, rim_top_a=None, sheen=0,
               res=RES, ss=SS):
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
    ty = (y - ins) / max(H - 2 * ins, 1)                       # 0 at the top of the bar, 1 at the bottom
    rim_alpha = rim_a if rim_top_a is None else rim_top_a + (rim_a - rim_top_a) * np.clip(ty, 0, 1) ** 0.6
    sheen_l = inner * np.clip(1 - ty / 0.55, 0, 1) ** 1.5 * sheen / 255.0   # soft white over the upper half
    for layer, c in ((sheen_l, (255, 255, 255)), (rim_m * rim_alpha / 255.0, rim), (hl, (255, 255, 255))):
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
    elif kind == 'minus':
        d.line((c - 0.22 * n, c, c + 0.22 * n, c), fill=255, width=wd)
    elif kind == 'plus':
        d.line((c - 0.22 * n, c, c + 0.22 * n, c), fill=255, width=wd)
        d.line((c, c - 0.22 * n, c, c + 0.22 * n), fill=255, width=wd)
    elif kind == 'globe':
        r = 0.27 * n
        d.ellipse((c - r, c - r, c + r, c + r), outline=255, width=wd)
        d.ellipse((c - 0.11 * n, c - r, c + 0.11 * n, c + r), outline=255, width=max(wd - 1, 2))
        d.line((c - r, c, c + r, c), fill=255, width=max(wd - 1, 2))
    elif kind == 'bars':
        for i, hgt in enumerate((0.20, 0.34, 0.26)):
            x0 = c + (i - 1) * 0.2 * n
            d.rounded_rectangle((x0 - 0.06 * n, c + 0.22 * n - hgt * n, x0 + 0.06 * n, c + 0.22 * n), radius=int(n * 0.03), fill=255)
    elif kind == 'gift':
        t = max(int(n * 0.055), 2)
        d.rounded_rectangle((c - 0.22 * n, c - 0.02 * n, c + 0.22 * n, c + 0.27 * n), radius=int(n * 0.03), outline=255, width=t)
        d.rounded_rectangle((c - 0.27 * n, c - 0.14 * n, c + 0.27 * n, c - 0.02 * n), radius=int(n * 0.03), outline=255, width=t)
        d.line((c, c - 0.14 * n, c, c + 0.27 * n), fill=255, width=t)
        d.arc((c - 0.20 * n, c - 0.30 * n, c, c - 0.12 * n), 90, 360, fill=255, width=t)
        d.arc((c, c - 0.30 * n, c + 0.20 * n, c - 0.12 * n), 180, 450, fill=255, width=t)
    elif kind == 'bag':
        t = max(int(n * 0.055), 2)
        d.polygon([(c - 0.20 * n, c - 0.10 * n), (c + 0.20 * n, c - 0.10 * n), (c + 0.27 * n, c + 0.27 * n), (c - 0.27 * n, c + 0.27 * n)],
                  outline=255, width=t)
        d.arc((c - 0.13 * n, c - 0.27 * n, c + 0.13 * n, c + 0.05 * n), 180, 360, fill=255, width=t)
    elif kind == 'sun':
        r = 0.11 * n
        d.ellipse((c - r, c - r, c + r, c + r), fill=255)
        for i in range(8):
            ang = i * np.pi / 4
            d.line((c + 0.19 * n * np.cos(ang), c + 0.19 * n * np.sin(ang),
                    c + 0.29 * n * np.cos(ang), c + 0.29 * n * np.sin(ang)), fill=255, width=max(wd - 1, 2))
    elif kind == 'moon':
        r = 0.26 * n
        d.ellipse((c - r, c - r, c + r, c + r), fill=255)
        d.ellipse((c - r * 0.1, c - r * 1.35, c + r * 1.55, c + r * 0.3), fill=0)
    elif kind == 'person':
        r = n * 0.1
        d.ellipse((c - r, c - 0.16 * n - r, c + r, c - 0.16 * n + r), outline=255, width=wd)
        d.arc((c - 0.22 * n, c - 0.02 * n, c + 0.22 * n, c + 0.46 * n), 180, 360, fill=255, width=wd)
    elif kind == 'users':
        t = max(wd - 1, 2)
        for dx in (-0.13, 0.13):
            r = n * 0.075
            d.ellipse((c + dx * n - r, c - 0.16 * n - r, c + dx * n + r, c - 0.16 * n + r), outline=255, width=t)
            d.arc((c + dx * n - 0.14 * n, c - 0.04 * n, c + dx * n + 0.14 * n, c + 0.30 * n), 180, 360, fill=255, width=t)
    elif kind == 'swords':
        for sg in (1, -1):
            d.line((c - 0.24 * n * sg, c - 0.24 * n, c + 0.24 * n * sg, c + 0.24 * n), fill=255, width=wd)
            px, py = c + 0.12 * n * sg, c + 0.12 * n
            wx, wy = -0.7071 * 0.09 * n, sg * 0.7071 * 0.09 * n
            d.line((px - wx, py - wy, px + wx, py + wy), fill=255, width=wd)
    elif kind == 'box':
        d.rounded_rectangle((c - 0.22 * n, c - 0.2 * n, c + 0.22 * n, c + 0.24 * n), radius=int(n * 0.05), outline=255, width=wd)
        d.line((c - 0.22 * n, c - 0.05 * n, c + 0.22 * n, c - 0.05 * n), fill=255, width=wd)
        d.line((c - 0.07 * n, c + 0.06 * n, c + 0.07 * n, c + 0.06 * n), fill=255, width=wd)
    elif kind == 'bolt':
        pts = [(0.05, -0.28), (-0.15, 0.04), (-0.02, 0.04), (-0.07, 0.28), (0.15, -0.06), (0.02, -0.06)]
        d.polygon([(c + x * n, c + y * n) for x, y in pts], fill=255)
    elif kind == 'list':
        for dy in (-0.15, 0, 0.15):
            d.line((c - 0.08 * n, c + dy * n, c + 0.24 * n, c + dy * n), fill=255, width=wd)
            r = n * 0.035
            d.ellipse((c - 0.24 * n - r, c + dy * n - r, c - 0.24 * n + r, c + dy * n + r), fill=255)
    elif kind == 'heart':
        pts = []
        for i in range(60):
            t = i / 60 * 2 * np.pi
            x = 16 * np.sin(t) ** 3
            y = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
            pts.append((c + x * n * 0.0155, c + 0.02 * n + y * n * 0.0155))
        d.polygon(pts, fill=255)
    elif kind == 'search':
        r = 0.15 * n
        d.ellipse((c - 0.05 * n - r, c - 0.05 * n - r, c - 0.05 * n + r, c - 0.05 * n + r), outline=255, width=wd)
        d.line((c + 0.07 * n, c + 0.07 * n, c + 0.25 * n, c + 0.25 * n), fill=255, width=wd)
    elif kind == 'envelope':
        d.rounded_rectangle((c - 0.26 * n, c - 0.18 * n, c + 0.26 * n, c + 0.18 * n), radius=int(n * 0.04), outline=255, width=wd)
        d.line([(c - 0.26 * n, c - 0.16 * n), (c, c + 0.04 * n), (c + 0.26 * n, c - 0.16 * n)], fill=255, width=max(wd - 1, 2), joint='curve')
    elif kind == 'shield':
        d.polygon([(c - 0.21 * n, c - 0.24 * n), (c + 0.21 * n, c - 0.24 * n), (c + 0.21 * n, c + 0.04 * n),
                   (c, c + 0.28 * n), (c - 0.21 * n, c + 0.04 * n)], outline=255, width=wd)
    elif kind == 'gear':
        r = 0.12 * n
        d.ellipse((c - r, c - r, c + r, c + r), outline=255, width=wd)
        for i in range(8):
            ang = i * np.pi / 4
            d.line((c + 0.17 * n * np.cos(ang), c + 0.17 * n * np.sin(ang), c + 0.27 * n * np.cos(ang), c + 0.27 * n * np.sin(ang)),
                   fill=255, width=wd + 2)
    elif kind == 'move':
        a = 0.25 * n
        h = 0.07 * n
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            tx, ty = c + dx * a, c + dy * a
            d.line((c, c, tx, ty), fill=255, width=wd)
            d.line((tx, ty, tx - dx * 0.08 * n - dy * h, ty - dy * 0.08 * n + dx * h), fill=255, width=wd)
            d.line((tx, ty, tx - dx * 0.08 * n + dy * h, ty - dy * 0.08 * n - dx * h), fill=255, width=wd)
    elif kind == 'resize':
        d.line((c - 0.2 * n, c + 0.2 * n, c + 0.2 * n, c - 0.2 * n), fill=255, width=wd)
        tx, ty = c + 0.22 * n, c - 0.22 * n
        d.line((tx, ty, tx - 0.15 * n, ty), fill=255, width=wd)
        d.line((tx, ty, tx, ty + 0.15 * n), fill=255, width=wd)
        bx, by = c - 0.22 * n, c + 0.22 * n
        d.line((bx, by, bx + 0.15 * n, by), fill=255, width=wd)
        d.line((bx, by, bx, by - 0.15 * n), fill=255, width=wd)
    elif kind == 'tri-right':
        d.polygon([(c - 0.13 * n, c - 0.21 * n), (c - 0.13 * n, c + 0.21 * n), (c + 0.21 * n, c)], fill=255)
    elif kind == 'tri-left':
        d.polygon([(c + 0.13 * n, c - 0.21 * n), (c + 0.13 * n, c + 0.21 * n), (c - 0.21 * n, c)], fill=255)
    elif kind == 'tri-up':
        d.polygon([(c - 0.21 * n, c + 0.13 * n), (c + 0.21 * n, c + 0.13 * n), (c, c - 0.21 * n)], fill=255)
    elif kind == 'tri-down':
        d.polygon([(c - 0.21 * n, c - 0.13 * n), (c + 0.21 * n, c - 0.13 * n), (c, c + 0.21 * n)], fill=255)
    elif kind == 'x':
        d.line((c - 0.2 * n, c - 0.2 * n, c + 0.2 * n, c + 0.2 * n), fill=255, width=wd)
        d.line((c - 0.2 * n, c + 0.2 * n, c + 0.2 * n, c - 0.2 * n), fill=255, width=wd)
    elif kind == 'trash':
        t = max(wd - 1, 2)
        d.line((c - 0.23 * n, c - 0.13 * n, c + 0.23 * n, c - 0.13 * n), fill=255, width=t)
        d.line([(c - 0.07 * n, c - 0.13 * n), (c - 0.07 * n, c - 0.22 * n), (c + 0.07 * n, c - 0.22 * n), (c + 0.07 * n, c - 0.13 * n)], fill=255, width=t, joint='curve')
        d.polygon([(c - 0.17 * n, c - 0.07 * n), (c + 0.17 * n, c - 0.07 * n), (c + 0.14 * n, c + 0.26 * n), (c - 0.14 * n, c + 0.26 * n)], outline=255, width=t)
        d.line((c - 0.05 * n, c, c - 0.045 * n, c + 0.18 * n), fill=255, width=t)
        d.line((c + 0.05 * n, c, c + 0.045 * n, c + 0.18 * n), fill=255, width=t)
    elif kind == 'coin':
        d.ellipse((c - 0.23 * n, c - 0.23 * n, c + 0.23 * n, c + 0.23 * n), outline=255, width=wd)
        r = 0.07 * n
        d.ellipse((c - r, c - r, c + r, c + r), fill=255)
    elif kind == 'weight':
        d.polygon([(c - 0.2 * n, c + 0.26 * n), (c + 0.2 * n, c + 0.26 * n), (c + 0.15 * n, c - 0.02 * n), (c - 0.15 * n, c - 0.02 * n)], fill=255)
        d.arc((c - 0.1 * n, c - 0.27 * n, c + 0.1 * n, c + 0.05 * n), 180, 360, fill=255, width=wd)
    elif kind == 'gem':
        t = max(wd - 1, 2)
        d.polygon([(c, c - 0.25 * n), (c + 0.22 * n, c - 0.05 * n), (c, c + 0.25 * n), (c - 0.22 * n, c - 0.05 * n)], outline=255, width=t)
        d.line((c - 0.22 * n, c - 0.05 * n, c + 0.22 * n, c - 0.05 * n), fill=255, width=t)
    elif kind == 'zulie':
        d.line([(c - 0.17 * n, c - 0.2 * n), (c + 0.17 * n, c - 0.2 * n), (c - 0.17 * n, c + 0.2 * n), (c + 0.17 * n, c + 0.2 * n)],
               fill=255, width=wd, joint='curve')
        d.line((c, c - 0.29 * n, c, c + 0.29 * n), fill=255, width=max(wd - 1, 2))
    elif kind == 'letter-h':
        d.line((c - 0.16 * n, c - 0.23 * n, c - 0.16 * n, c + 0.23 * n), fill=255, width=wd)
        d.line((c + 0.16 * n, c - 0.23 * n, c + 0.16 * n, c + 0.23 * n), fill=255, width=wd)
        d.line((c - 0.16 * n, c, c + 0.16 * n, c), fill=255, width=wd)
    elif kind == 'letter-v':
        d.line([(c - 0.2 * n, c - 0.22 * n), (c, c + 0.23 * n), (c + 0.2 * n, c - 0.22 * n)], fill=255, width=wd, joint='curve')
    elif kind == 'letter-p':
        d.line((c - 0.14 * n, c - 0.24 * n, c - 0.14 * n, c + 0.26 * n), fill=255, width=wd)
        d.rounded_rectangle((c - 0.14 * n, c - 0.24 * n, c + 0.16 * n, c + 0.06 * n), radius=int(n * 0.12), outline=255, width=wd)
    elif kind == 'menu':
        for dy in (-0.14, 0, 0.14):
            d.line((c - 0.2 * n, c + dy * n, c + 0.2 * n, c + dy * n), fill=255, width=wd)
    elif kind == 'bell':
        d.arc((c - 0.17 * n, c - 0.24 * n, c + 0.17 * n, c + 0.1 * n), 180, 360, fill=255, width=wd)
        d.line((c - 0.17 * n, c - 0.07 * n, c - 0.22 * n, c + 0.15 * n), fill=255, width=wd)
        d.line((c + 0.17 * n, c - 0.07 * n, c + 0.22 * n, c + 0.15 * n), fill=255, width=wd)
        d.line((c - 0.25 * n, c + 0.15 * n, c + 0.25 * n, c + 0.15 * n), fill=255, width=wd)
        r = n * 0.045
        d.ellipse((c - r, c + 0.22 * n - r, c + r, c + 0.22 * n + r), fill=255)
    elif kind in ('entrust', 'star'):
        pts = []
        for i in range(10):
            ang = -np.pi / 2 + i * np.pi / 5
            rr = n * (0.25 if i % 2 == 0 else 0.105)
            pts.append((c + rr * np.cos(ang), c + 0.02 * n + rr * np.sin(ang)))
        d.polygon(pts, fill=255)
    return g


def round_icon(kind, state, radius=10, size=None):
    """Round glass toolbar button with a white glyph. state: 'n' normal, 'h' hover, 'd' disabled (2 px per dp)."""
    tint, rt, rm, rb, sh, ga = {'n': (42, 225, 110, 70, 50, 0.92), 'h': (78, 245, 150, 95, 80, 1.0),
                                'd': (16, 90, 50, 30, 14, 0.38), 'p': (14, 120, 95, 150, 0, 0.8)}[state]
    img, _, _ = glass_panel(margin=0, radius=radius, tint=(255, 255, 255, tint), rim_top=rt, rim_mid=rm,
                            rim_bottom=rb, sheen=sh, shadow=0, shadow_dy=0, shadow_blur=1,
                            edge=0 if size is None else size - 2 * radius)
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


def _overlay(img, draw_fn, rgb, alpha, k=8):
    """Draw a white-mask glyph with draw_fn(ImageDraw, n) on a supersampled mask and composite it in `rgb` onto img."""
    n = img.width * k
    g = Image.new('L', (n, n), 0)
    draw_fn(ImageDraw.Draw(g), n)
    g = g.resize(img.size, Image.LANCZOS)
    col = Image.new('RGBA', img.size, tuple(rgb) + (255,))
    col.putalpha(g.point(lambda v: int(v * alpha)))
    out = img.copy()
    out.alpha_composite(col)
    return out


def toggle(kind, state):
    """20dp checkbox ('cb') or radio ('rd'). state: off, off-h, on, on-h, p (pressed), d (disabled), d-on."""
    radius = 6 if kind == 'cb' else 10
    on = state in ('on', 'on-h', 'd-on')
    base = dict(margin=0, radius=radius, shadow=0, shadow_dy=0, shadow_blur=1, edge=8 if kind == 'cb' else 0,
                sheen=0, inner_top=0)
    if on:
        hov = state == 'on-h'
        spec = dict(base, tint=(255, 255, 255, 215 if hov else 190), rim_top=255, rim_mid=210 if hov else 180,
                    rim_bottom=160 if hov else 130, sheen=90)
        if state == 'd-on':
            spec.update(tint=(255, 255, 255, 40), rim_top=110, rim_mid=70, rim_bottom=50, sheen=20)
    elif state == 'p':
        spec = dict(base, tint=(0, 0, 0, 80), rim_top=110, rim_mid=95, rim_bottom=150)
    elif state == 'd':
        spec = dict(base, tint=(255, 255, 255, 12), rim_top=80, rim_mid=55, rim_bottom=45)
    else:
        hov = state == 'off-h'
        spec = dict(base, tint=(255, 255, 255, 58 if hov else 26), rim_top=210 if hov else 150,
                    rim_mid=160 if hov else 110, rim_bottom=200 if hov else 170, inner_top=100)
    img, _, _ = glass_panel(**spec)
    if kind == 'rd' and img.size != (40, 40):
        img = img.resize((40, 40), Image.LANCZOS)
    if on:
        ink = (34, 38, 50)
        a = 0.35 if state == 'd-on' else 0.95
        if kind == 'cb':
            def mark(d, n):
                d.line([(n * 0.27, n * 0.52), (n * 0.43, n * 0.68), (n * 0.74, n * 0.33)], fill=255,
                       width=int(n * 0.1), joint='curve')
        else:
            def mark(d, n):
                r = n * 0.17
                d.ellipse((n / 2 - r, n / 2 - r, n / 2 + r, n / 2 + r), fill=255)
        img = _overlay(img, mark, ink, a)
    return img


def chevron(state):
    """Dropdown arrow (24 x 22 dp, transparent): a thin white chevron."""
    img = Image.new('RGBA', (48, 44), (0, 0, 0, 0))
    a = {'n': 0.85, 'h': 1.0, 'd': 0.3}[state]

    def mark(d, n):
        d.line([(n * 0.34, n * 0.42), (n * 0.5, n * 0.58), (n * 0.66, n * 0.42)], fill=255, width=int(n * 0.07), joint='curve')
    return _overlay(img, mark, (255, 255, 255), a)


def grip(hover):
    """Resize handle (14 x 14 dp): three short diagonal lines in the corner."""
    img = Image.new('RGBA', (28, 28), (0, 0, 0, 0))

    def mark(d, n):
        w = max(int(n * 0.07), 2)
        for i in range(3):
            o = n * (0.30 + 0.2 * i)
            d.line([(n * 0.92, o), (o, n * 0.92)], fill=255, width=w)
    return _overlay(img, mark, (255, 255, 255), 1.0 if hover else 0.55)


def plain_glyph(kind, alpha=0.9, size=20):
    """A bare white glyph (no button), size x size dp at 2 px per dp."""
    img = Image.new('RGBA', (size * 2, size * 2), (0, 0, 0, 0))
    return _overlay(img, lambda d, n: d.bitmap((0, 0), _glyph(kind, n), fill=255), (255, 255, 255), alpha)


def toggle_chevron(direction):
    """Chevron for the menu toggle pill: transparent 56 x 24 dp canvas (2 px per dp), chevron pointing 'up' or 'down'."""
    img = Image.new('RGBA', (112, 48), (0, 0, 0, 0))

    def mark(d, n):
        # drawn on a square mask of side n; the canvas is 112 x 48 so place the chevron in the middle of a square crop
        s_ = n * 0.14 if direction == 'up' else -n * 0.14
        cy = n / 2
        d.line([(n * 0.40, cy + s_ * 0.5), (n * 0.5, cy - s_ * 0.5), (n * 0.60, cy + s_ * 0.5)], fill=255, width=int(n * 0.045), joint='curve')
    k = 8
    w, h = img.size
    g = Image.new('L', (w * k, w * k), 0)        # square mask so the chevron math (centred at n / 2) lands in the middle band
    mark(ImageDraw.Draw(g), w * k)            # square mask side = width, then crop the middle band
    g = g.crop((0, (w * k - h * k) // 2, w * k, (w * k - h * k) // 2 + h * k)).resize(img.size, Image.LANCZOS)
    white = Image.new('RGBA', img.size, (255, 255, 255, 255))
    white.putalpha(g.point(lambda v: int(v * 0.95)))
    out = img.copy()
    out.alpha_composite(white)
    return out


def write_tga(path, img):
    """32-bit TGA, top-left origin, like Rednim's controls.tga."""
    img = img.convert('RGBA')
    w, h = img.size
    hdr = struct.pack('<BBBHHBHHHHBB', 0, 0, 2, 0, 0, 0, 0, 0, w, h, 32, 0x28)
    r, g, b, a = img.split()
    with open(path, 'wb') as f:
        f.write(hdr)
        f.write(Image.merge('RGBA', (b, g, r, a)).tobytes())


def nine_slice(img, corner, edge, W, H):
    """Stretch a 9-slice panel (as returned by glass_panel) to W x H pixels."""
    n = img.width
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))

    def cr(x, y, w, h):
        return img.crop((x, y, x + w, y + h))
    c = corner
    out.paste(cr(0, 0, c, c), (0, 0)); out.paste(cr(n - c, 0, c, c), (W - c, 0))
    out.paste(cr(0, n - c, c, c), (0, H - c)); out.paste(cr(n - c, n - c, c, c), (W - c, H - c))
    out.paste(cr(c, 0, edge, c).resize((W - 2 * c, c)), (c, 0)); out.paste(cr(c, n - c, edge, c).resize((W - 2 * c, c)), (c, H - c))
    if H > 2 * c:
        out.paste(cr(0, c, c, edge).resize((c, H - 2 * c)), (0, c)); out.paste(cr(n - c, c, c, edge).resize((c, H - 2 * c)), (W - c, c))
        out.paste(cr(c, c, edge, edge).resize((W - 2 * c, H - 2 * c)), (c, c))
    return out
