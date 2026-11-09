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
