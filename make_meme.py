#!/usr/bin/env python3
"""make_meme.py — draws meme.png for the gta6-meme-x-01 entry.

Everything in the picture is drawn by this script (Pillow primitives only),
except make.fun's ghost, which is the official press-kit mark
(assets/mark-1024.png from https://make.fun/press/) with its magenta disc
keyed out by flood fill, so the ghost itself — sparkle eyes, black outline,
magenta star coin in its round hand — sits in the scene.

The joke: two panels, one wait. Top: a gamer who waited for GTA VI since
GTA V (2013) is now a dusty skeleton in his chair. Bottom: the make.fun
ghost, in the mirror-image chair under a Vice City sunset, has spent the
same wait at a laptop stacking USDC bounty coins under a neon make.fun
billboard. Run: python3 make_meme.py  (writes meme.png, 1200x1200)
"""

import math
import random
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
W, PANEL_H, GUTTER = 1200, 596, 8
H = PANEL_H * 2 + GUTTER

FONT_BLACK = "/usr/share/fonts/truetype/noto/NotoSansDisplay-Black.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/noto/NotoSansDisplay-Bold.ttf"
FONT_FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size, black=True):
    path = FONT_BLACK if black else FONT_BOLD
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.truetype(FONT_FALLBACK, size)


def fit_font(draw, text, max_width, start, black=True):
    size = start
    while size > 10:
        f = font(size, black)
        if draw.textlength(text, font=f) <= max_width:
            return f
        size -= 2
    return font(10, black)


def caption(draw, lines, y, start=64, fill=(255, 255, 255), stroke=8):
    for line in lines:
        f = fit_font(draw, line, W - 60, start)
        w = draw.textlength(line, font=f)
        draw.text(((W - w) / 2, y), line, font=f, fill=fill,
                  stroke_width=stroke, stroke_fill=(0, 0, 0))
        y += int(f.size * 1.12)
    return y


def vgradient(size, stops):
    """Vertical gradient image from [(pos0..1, (r,g,b)), ...]."""
    w, h = size
    img = Image.new("RGB", (1, h))
    px = []
    for yy in range(h):
        t = yy / max(1, h - 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                k = 0 if p1 == p0 else (t - p0) / (p1 - p0)
                px.append(tuple(int(c0[j] + (c1[j] - c0[j]) * k) for j in range(3)))
                break
        else:
            px.append(stops[-1][1])
    img.putdata(px)
    return img.resize((w, h))


# ---------------------------------------------------------------- the ghost
def extract_ghost():
    """Key the magenta disc out of the official mark, keep the ghost."""
    mark = Image.open(HERE / "assets" / "mark-1024.png").convert("RGBA")
    px = mark.load()
    w, h = mark.size
    # the disc is the most magenta pixel among points known to sit on it
    # (sampling blindly once landed on the black ring instead)
    candidates = [(512, 150), (300, 160), (724, 160), (160, 512), (864, 512),
                  (512, 940), (200, 850), (824, 850), (250, 300), (774, 300)]
    disc = max((px[x, y][:3] for x, y in candidates),
               key=lambda c: c[0] - c[1])

    def is_disc(x, y):
        r, g, b, a = px[x, y]
        if a < 10:
            return False
        return (abs(r - disc[0]) + abs(g - disc[1]) + abs(b - disc[2])) < 130

    seen = bytearray(w * h)
    queue = deque()
    for seed in candidates:
        if is_disc(*seed):
            queue.append(seed)
            seen[seed[1] * w + seed[0]] = 1
    while queue:
        x, y = queue.popleft()
        px[x, y] = (0, 0, 0, 0)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and is_disc(nx, ny):
                seen[ny * w + nx] = 1
                queue.append((nx, ny))
    # the disc's black outer ring is a separate dark component, not touching
    # the ghost's own outline: flood it away from its topmost pixel
    def is_dark(x, y):
        r, g, b, a = px[x, y]
        return a >= 10 and r + g + b < 200

    seed = None
    for y in range(h):
        if is_dark(w // 2, y):
            seed = (w // 2, y)
            break
    if seed:
        seen2 = bytearray(w * h)
        queue = deque([seed])
        seen2[seed[1] * w + seed[0]] = 1
        while queue:
            x, y = queue.popleft()
            px[x, y] = (0, 0, 0, 0)
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h and not seen2[ny * w + nx] and is_dark(nx, ny):
                    seen2[ny * w + nx] = 1
                    queue.append((nx, ny))
    # shave the anti-aliased fringe off the alpha edge
    alpha = mark.split()[3].filter(ImageFilter.MinFilter(3))
    mark.putalpha(alpha)
    bbox = mark.getbbox()
    ghost = mark.crop(bbox)
    ghost.save(HERE / "assets" / "ghost.png")
    return ghost


# ------------------------------------------------------------------- scenes
def bone_line(d, pts, bone=(228, 221, 199), edge=(110, 104, 88), w_out=13, w_in=8):
    d.line(pts, fill=edge, width=w_out, joint="curve")
    d.line(pts, fill=bone, width=w_in, joint="curve")


def cobweb(d, cx, cy, r, sx=1, sy=1, color=(205, 205, 205)):
    for k in range(5):
        a = math.radians(k * 22.5)
        d.line([cx, cy, cx + sx * r * math.cos(a), cy + sy * r * math.sin(a)],
               fill=color, width=2)
    if sx > 0 and sy > 0:
        start, end = 0, 90
    elif sx < 0 and sy > 0:
        start, end = 90, 180
    elif sx < 0 and sy < 0:
        start, end = 180, 270
    else:
        start, end = 270, 360
    for k in (0.35, 0.6, 0.85):
        rr = r * k
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], start=start, end=end,
              fill=color, width=2)


def top_panel():
    img = vgradient((W, PANEL_H), [(0.0, (52, 57, 72)), (0.78, (74, 79, 92)), (1.0, (60, 63, 74))])
    d = ImageDraw.Draw(img, "RGBA")
    # floor
    d.rectangle([0, 486, W, PANEL_H], fill=(38, 40, 48))
    d.line([0, 486, W, 486], fill=(24, 25, 31), width=4)

    # wall calendar, forever 2013
    cal = [58, 188, 218, 384]
    d.rectangle(cal, fill=(214, 205, 182), outline=(90, 84, 70), width=3)
    d.rectangle([cal[0], cal[1], cal[2], cal[1] + 62], fill=(168, 52, 44))
    f = fit_font(d, "2013", 140, 52)
    d.text(((cal[0] + cal[2]) / 2, cal[1] + 4), "2013", font=f, fill=(245, 240, 228), anchor="ma")
    for r in range(4):
        for c in range(5):
            x = cal[0] + 22 + c * 28
            y = cal[1] + 88 + r * 26
            d.ellipse([x, y, x + 9, y + 9], fill=(120, 114, 96))
    d.ellipse([cal[0] + 100, cal[1] + 132, cal[0] + 132, cal[1] + 164], outline=(190, 40, 34), width=4)

    # faded Vice City poster
    pos = [946, 188, 1150, 452]
    d.rectangle(pos, fill=(30, 62, 70), outline=(16, 34, 40), width=3)
    d.line([1010, 420, 1022, 330, 1040, 268], fill=(196, 116, 146), width=7)
    for ang in (-70, -40, -12, 18, 48):
        a = math.radians(ang)
        d.line([1040, 268, 1040 + 62 * math.cos(a), 268 + 44 * math.sin(a)],
               fill=(196, 116, 146), width=6)
    f = fit_font(d, "VICE CITY", 180, 34)
    d.text(((pos[0] + pos[2]) / 2, 396), "VICE CITY", font=f, fill=(214, 150, 168), anchor="ma")

    # gaming chair
    d.rounded_rectangle([452, 232, 748, 566], 36, fill=(34, 36, 44))
    d.rounded_rectangle([524, 200, 676, 268], 24, fill=(34, 36, 44))
    d.rounded_rectangle([478, 258, 722, 540], 28, fill=(44, 47, 57))

    # the skeleton, slumped, still holding the controller
    bone = (228, 221, 199)
    # legs: femurs + shins + faded sneakers
    bone_line(d, [(566, 452), (516, 528), (510, 584)])
    bone_line(d, [(622, 452), (672, 528), (680, 584)])
    d.rounded_rectangle([478, 574, 540, 596], 8, fill=(150, 60, 52))
    d.rounded_rectangle([648, 574, 712, 596], 8, fill=(150, 60, 52))
    # pelvis + spine
    d.ellipse([548, 424, 640, 470], outline=bone, width=7)
    bone_line(d, [(592, 428), (590, 396), (592, 360)], w_out=12, w_in=7)
    # ribs
    for i, y in enumerate((368, 392, 416)):
        d.arc([524, y - 22, 664, y + 26], start=15, end=165, fill=bone, width=6)
    # arms to the controller
    bone_line(d, [(534, 372), (506, 430), (550, 490)])
    bone_line(d, [(652, 372), (678, 428), (642, 490)])
    # skull, tilted, resting low
    d.ellipse([522, 238, 656, 366], fill=bone, outline=(110, 104, 88), width=3)
    d.rounded_rectangle([534, 330, 644, 386], 14, fill=bone, outline=(110, 104, 88), width=3)
    d.ellipse([548, 282, 580, 320], fill=(18, 18, 22))
    d.ellipse([600, 282, 632, 320], fill=(18, 18, 22))
    d.polygon([(589, 318), (578, 340), (600, 340)], fill=(18, 18, 22))
    for x in (556, 578, 600, 622):
        d.line([x, 348, x, 380], fill=(110, 104, 88), width=3)
    d.line([540, 252, 574, 276], fill=(110, 104, 88), width=3)
    # controller in its hands
    d.rounded_rectangle([528, 474, 664, 534], 20, fill=(24, 24, 30), outline=(70, 72, 82), width=3)
    d.ellipse([556, 494, 574, 512], fill=(90, 92, 102))
    d.ellipse([616, 494, 634, 512], fill=(90, 92, 102))
    for (x, y, c) in [(644, 486, (150, 60, 52)), (630, 499, (70, 110, 160)), (644, 512, (90, 150, 90))]:
        d.ellipse([x, y, x + 9, y + 9], fill=c)

    # cobwebs + a unifying layer of dust over the art (caption stays crisp)
    cobweb(d, 6, 158, 120, 1, 1)
    cobweb(d, W - 6, 158, 120, -1, 1)
    rng = random.Random(2013)
    for _ in range(500):
        x, y = rng.uniform(0, W), rng.uniform(0, PANEL_H)
        d.point((x, y), fill=(200, 200, 205))
    d.rectangle([0, 0, W, PANEL_H], fill=(148, 148, 150, 22))
    caption(d, ["WAITING FOR GTA VI", "SINCE GTA V (2013):"], 12)
    return img


def palm(d, base_x, base_y, height, lean, color=(22, 9, 38), scale=1.0):
    top_x = base_x + lean
    top_y = base_y - height
    pts = []
    for i in range(21):
        t = i / 20
        x = base_x + (top_x - base_x) * t + 14 * math.sin(t * math.pi) * (1 if lean >= 0 else -1)
        pts.append((x, base_y + (top_y - base_y) * t))
    d.line(pts, fill=color, width=int(13 * scale), joint="curve")
    for ang in (-165, -125, -85, -45, -8, 25):
        a = math.radians(ang)
        ex = top_x + 118 * scale * math.cos(a)
        ey = top_y - 46 * scale * math.sin(a) + 26 * scale
        mid = (top_x + 62 * scale * math.cos(a), top_y - 40 * scale * math.sin(a) - 12 * scale)
        d.line([(top_x, top_y), mid, (ex, ey)], fill=color, width=int(9 * scale), joint="curve")


def coin_stack(d, cx, base_y, n, w=92):
    gold, edge = (246, 192, 66), (176, 128, 34)
    for i in range(n):
        y = base_y - i * 17
        d.ellipse([cx - w / 2, y - 20, cx + w / 2, y + 4], fill=gold, outline=edge, width=3)
    f = fit_font(d, "$", 30, 26)
    d.text((cx, base_y - n * 17 - 14), "$", font=f, fill=(120, 84, 16), anchor="mm")


def bottom_panel(ghost):
    img = vgradient((W, PANEL_H), [(0.0, (26, 10, 56)), (0.42, (110, 26, 96)),
                                   (0.68, (214, 74, 88)), (0.86, (248, 148, 66)), (1.0, (252, 178, 84))])
    d = ImageDraw.Draw(img, "RGBA")
    caption(d, ["MY AI AGENT ON make.fun:", "STACKING USDC BOUNTIES THE WHOLE TIME:"], 12, start=58)

    # retro sun on the horizon
    sun = Image.new("RGBA", (W, PANEL_H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sun)
    sd.ellipse([470, 268, 730, 528], fill=(255, 196, 84, 255))
    for i, y in enumerate((430, 452, 472, 490)):
        sd.rectangle([470, y, 730, y + 5 + i * 2], fill=(0, 0, 0, 0))
    img.paste(Image.alpha_composite(img.convert("RGBA"), sun).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(img, "RGBA")

    # skyline silhouette
    rng = random.Random(6)
    x = 0
    while x < W:
        bw = rng.randint(46, 96)
        bh = rng.randint(60, 150)
        d.rectangle([x, 452 - bh, x + bw, 452], fill=(30, 13, 48))
        for _ in range(bw // 14):
            wx = x + rng.randint(6, max(7, bw - 12))
            wy = 452 - bh + rng.randint(8, max(9, bh - 16))
            d.rectangle([wx, wy, wx + 4, wy + 6], fill=(255, 214, 110))
        x += bw + rng.randint(2, 10)

    # palms first, so the billboard stands in front of their fronds
    palm(d, 66, 500, 300, 46, scale=1.0)
    palm(d, 1150, 505, 260, -40, scale=0.85)

    # neon billboard: make.fun, worked into the skyline
    board = [776, 180, 1136, 276]
    glow = Image.new("RGBA", (W, PANEL_H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    f = fit_font(gd, "make.fun", 300, 74)
    gd.rounded_rectangle(board, 14, outline=(255, 64, 170), width=5)
    gd.text(((board[0] + board[2]) / 2, (board[1] + board[3]) / 2), "make.fun",
            font=f, fill=(255, 92, 190), anchor="mm")
    img.paste(Image.alpha_composite(img.convert("RGBA"),
                                    glow.filter(ImageFilter.GaussianBlur(9))).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle(board, 14, fill=(24, 6, 34, 235), outline=(255, 64, 170), width=4)
    d.text(((board[0] + board[2]) / 2, (board[1] + board[3]) / 2), "make.fun",
           font=f, fill=(255, 150, 215), anchor="mm")
    d.line([836, 276, 836, 380], fill=(30, 13, 48), width=8)
    d.line([1076, 276, 1076, 380], fill=(30, 13, 48), width=8)

    # mirror-image gaming chair, then the ghost at its laptop
    d.rounded_rectangle([372, 250, 716, 540], 36, fill=(40, 22, 62))
    d.rounded_rectangle([454, 220, 634, 290], 24, fill=(40, 22, 62))
    g = ghost.resize((440, int(440 * ghost.height / ghost.width)), Image.LANCZOS)
    img.paste(g, (324, 146), g)
    d = ImageDraw.Draw(img, "RGBA")

    # desk across the bottom (occludes the ghost's base: it sits at the desk)
    d.rectangle([0, 470, W, PANEL_H], fill=(26, 13, 36))
    d.rectangle([0, 470, W, 484], fill=(52, 28, 66))
    d.line([0, 484, W, 484], fill=(255, 120, 190), width=2)

    # laptop, screen lit with the game he waited for
    d.polygon([(428, 512), (652, 512), (684, 556), (396, 556)], fill=(22, 22, 28))
    d.rounded_rectangle([440, 386, 640, 516], 10, fill=(18, 18, 24), outline=(90, 90, 104), width=3)
    scr = vgradient((176, 106), [(0.0, (110, 26, 96)), (0.7, (232, 94, 60)), (1.0, (250, 170, 80))])
    img.paste(scr, (452, 398))
    d = ImageDraw.Draw(img, "RGBA")
    f = fit_font(d, "GTA VI", 150, 44)
    d.text((540, 420), "GTA VI", font=f, fill=(255, 255, 255), anchor="ma",
           stroke_width=3, stroke_fill=(60, 10, 50))
    f = fit_font(d, "OUT NOW", 90, 20, black=False)
    d.text((540, 472), "OUT NOW", font=f, fill=(140, 255, 220), anchor="ma")

    # the stack: gold coins, USDC coins, a money bag
    coin_stack(d, 792, 540, 5)
    coin_stack(d, 902, 540, 8)
    coin_stack(d, 1006, 540, 6)
    for cx, cy in [(1092, 512), (1128, 540), (1064, 544)]:
        d.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=(39, 117, 202), outline=(220, 238, 255), width=4)
        f = fit_font(d, "$", 34, 32)
        d.text((cx, cy - 1), "$", font=f, fill=(255, 255, 255), anchor="mm")
    d.ellipse([742, 470, 838, 556], fill=(74, 128, 74), outline=(40, 74, 40), width=3)
    d.polygon([(772, 478), (808, 478), (796, 452), (784, 452)], fill=(74, 128, 74), outline=(40, 74, 40))
    f = fit_font(d, "$", 44, 44)
    d.text((790, 516), "$", font=f, fill=(230, 244, 220), anchor="mm")
    return img


def main():
    ghost = extract_ghost()
    canvas = Image.new("RGB", (W, H), (0, 0, 0))
    canvas.paste(top_panel(), (0, 0))
    canvas.paste(bottom_panel(ghost), (0, PANEL_H + GUTTER))
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, PANEL_H, W, PANEL_H + GUTTER], fill=(0, 0, 0))
    canvas.save(HERE / "meme.png")
    print("wrote", HERE / "meme.png", canvas.size)


if __name__ == "__main__":
    main()
