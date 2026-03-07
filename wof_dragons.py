"""
Wings of Fire — All Dragon Tribes (2.5D Smooth Style v3)
Slimmer dragons, better layout, mountains, cave, proper TwinWing colors.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random, math

W, H = 1920, 1080
img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
draw = ImageDraw.Draw(img)

def lerp(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

def shade(c, amt):
    return tuple(max(0, min(255, v + amt)) for v in c[:3])

def grad_rect(x1, y1, x2, y2, tc, bc):
    for yy in range(y1, y2):
        t = (yy - y1) / max(1, y2 - y1)
        draw.line([(x1, yy), (x2, yy)], fill=lerp(tc, bc, t))

def shaded_ellipse(d, cx, cy, rx, ry, col, outline_col=None, ow=2):
    """Ellipse with top-highlight / bottom-shadow for 2.5D depth."""
    hi = shade(col, 55)
    sh = shade(col, -45)
    # draw from outside in so inner (lighter) overwrites
    for ring in range(max(rx, ry), 0, -1):
        frac = ring / max(rx, ry)
        srx, sry = int(rx * frac), int(ry * frac)
        if frac > 0.55:
            c = lerp(col, sh, (frac - 0.55) / 0.45)
        else:
            c = lerp(hi, col, frac / 0.55)
        d.ellipse([cx - srx, cy - sry, cx + srx, cy + sry], fill=c)
    if outline_col:
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=outline_col, width=ow)

# ══════════════════════════════════════════════════════════════
# ENVIRONMENT
# ══════════════════════════════════════════════════════════════
ground_y = int(H * 0.52)

# Sky
grad_rect(0, 0, W, ground_y + 40, (110, 185, 255), (195, 225, 255))

# ── Mountains (big, layered) ──
def draw_mountain(cx, w, h, base_y, col):
    pts = [(cx - w, base_y)]
    steps = 30
    for i in range(steps + 1):
        x = cx - w + 2 * w * i / steps
        peak = h * math.sin(math.pi * i / steps)
        # add some jaggedness
        jag = h * 0.08 * math.sin(i * 1.3) + h * 0.05 * math.sin(i * 3.7)
        pts.append((int(x), int(base_y - peak + jag)))
    pts.append((cx + w, base_y))
    draw.polygon(pts, fill=col)
    # Snow caps
    snow_pts = []
    for i in range(steps // 3, 2 * steps // 3 + 1):
        x = cx - w + 2 * w * i / steps
        peak = h * math.sin(math.pi * i / steps)
        jag = h * 0.08 * math.sin(i * 1.3) + h * 0.05 * math.sin(i * 3.7)
        snow_pts.append((int(x), int(base_y - peak + jag)))
    if len(snow_pts) >= 3:
        # close the snow polygon
        snow_pts.append((snow_pts[-1][0], snow_pts[-1][1] + int(h * 0.15)))
        snow_pts.append((snow_pts[0][0], snow_pts[0][1] + int(h * 0.15)))
        draw.polygon(snow_pts, fill=shade(col, 60))

# Back mountains (lighter, further away)
for cx, w, h, sv in [(150, 220, 180, 30), (450, 280, 220, 20), (750, 250, 200, 25),
                      (1050, 300, 240, 15), (1350, 260, 190, 28), (1650, 240, 170, 22), (1850, 200, 160, 18)]:
    draw_mountain(cx, w, h, ground_y + 10, (130 + sv, 145 + sv, 170 + sv))

# Front mountains (darker, closer)
for cx, w, h, sv in [(300, 200, 130, 0), (900, 250, 160, -10), (1500, 220, 140, 5)]:
    draw_mountain(cx, w, h, ground_y + 10, (100 + sv, 120 + sv, 150 + sv))

# ── Ground zones ──
# Forest (left ~40%)
grad_rect(0, ground_y, int(W * 0.40), H, (55, 135, 45), (35, 95, 30))
# Grassland (middle ~30%)
grad_rect(int(W * 0.40), ground_y, int(W * 0.68), H, (65, 150, 50), (45, 115, 35))
# Desert (right ~32%)
grad_rect(int(W * 0.68), ground_y, W, H, (215, 190, 125), (185, 155, 95))

# Blend zones
for x in range(int(W * 0.36), int(W * 0.44)):
    t = (x - W * 0.36) / (W * 0.08)
    for y in range(ground_y, H):
        yt = (y - ground_y) / max(1, H - ground_y)
        c1 = lerp((55, 135, 45), (35, 95, 30), yt)
        c2 = lerp((65, 150, 50), (45, 115, 35), yt)
        draw.point((x, y), fill=lerp(c1, c2, t))
for x in range(int(W * 0.64), int(W * 0.72)):
    t = (x - W * 0.64) / (W * 0.08)
    for y in range(ground_y, H):
        yt = (y - ground_y) / max(1, H - ground_y)
        c1 = lerp((65, 150, 50), (45, 115, 35), yt)
        c2 = lerp((215, 190, 125), (185, 155, 95), yt)
        draw.point((x, y), fill=lerp(c1, c2, t))

# Sand dunes
for dcx, dcy, dw, dh in [(int(W * 0.78), ground_y + 55, 130, 28),
                           (int(W * 0.90), ground_y + 85, 110, 22),
                           (int(W * 0.74), ground_y + 120, 90, 18),
                           (int(W * 0.85), ground_y + 150, 70, 14)]:
    for dy in range(dh):
        t = dy / dh
        c = lerp((235, 215, 155), (200, 175, 120), t)
        hw = int(dw * math.sqrt(max(0, 1 - t * t)))
        draw.line([(dcx - hw, dcy - dh + dy), (dcx + hw, dcy - dh + dy)], fill=c)

# ── Cave (in the mountains, left-center) ──
cave_cx, cave_cy = int(W * 0.30), ground_y - 10
cave_w, cave_h = 80, 55
# Dark opening
draw.ellipse([cave_cx - cave_w, cave_cy - cave_h, cave_cx + cave_w, cave_cy + cave_h],
             fill=(25, 20, 15))
# Inner shadow gradient
for r in range(min(cave_w, cave_h), 0, -2):
    t = r / min(cave_w, cave_h)
    c = lerp((25, 20, 15), (10, 8, 5), 1 - t)
    rx2 = int(cave_w * t)
    ry2 = int(cave_h * t)
    draw.ellipse([cave_cx - rx2, cave_cy - ry2, cave_cx + rx2, cave_cy + ry2], fill=c)
# Rocky arch around cave
for a in range(180, 360):
    rad = math.radians(a)
    for thick in range(12):
        ax = cave_cx + int((cave_w + thick) * math.cos(rad))
        ay = cave_cy + int((cave_h + thick) * math.sin(rad))
        t = thick / 12
        rc = lerp((90, 80, 70), (60, 55, 45), t)
        draw.point((ax, ay), fill=rc)
# Stalactites
for sx in range(-50, 51, 18):
    sh = random.randint(8, 20)
    draw.polygon([(cave_cx + sx - 3, cave_cy - cave_h + 5),
                   (cave_cx + sx + 3, cave_cy - cave_h + 5),
                   (cave_cx + sx, cave_cy - cave_h + 5 + sh)],
                  fill=(60, 55, 45))

# ── River (smoother, better positioned) ──
rl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
rd = ImageDraw.Draw(rl)
river_pts = []
for rx in range(int(W * 0.35), int(W * 0.72), 2):
    t = (rx - W * 0.35) / (W * 0.37)
    ry = ground_y + 170 + int(50 * math.sin(t * 3.8)) + int(t * 60)
    river_pts.append((rx, ry))
for pt in river_pts:
    rw = 28
    for dy in range(-rw, rw + 1):
        dt = abs(dy) / rw
        deep = lerp((45, 110, 210), (30, 80, 170), dt)
        light = lerp((90, 170, 245), (55, 130, 215), dt)
        c = lerp(light, deep, dt)
        a = int(210 * (1 - dt * 0.3))
        rd.point((pt[0], pt[1] + dy), fill=c + (a,))
# Specular highlights on water
for i in range(0, len(river_pts), 15):
    pt = river_pts[i]
    for sr in range(6, 0, -1):
        a = int(100 * (1 - sr / 6))
        rd.ellipse([pt[0] - sr * 2, pt[1] - sr, pt[0] + sr * 2, pt[1] + sr],
                   fill=(200, 230, 255, a))
img = Image.alpha_composite(img, rl)
draw = ImageDraw.Draw(img)

# ── Trees (varied, better spacing) ──
def draw_tree(cx, cy, sz, var=0):
    tw = max(2, int(sz * 0.2))
    th = int(sz * 1.0)
    # Trunk shading
    for dx in range(-tw, tw + 1):
        t = (dx + tw) / max(1, 2 * tw)
        c = lerp((85 + var, 55 + var, 22), (55 + var, 35 + var, 12), t)
        draw.line([(cx + dx, cy + int(sz * 0.3)), (cx + dx, cy + th)], fill=c)
    # Canopy blobs
    for lx, ly, lr in [(0, -sz * 0.5, sz * 0.7), (-sz * 0.35, -sz * 0.2, sz * 0.55),
                        (sz * 0.3, -sz * 0.25, sz * 0.5), (0, -sz * 0.8, sz * 0.5),
                        (-sz * 0.15, -sz * 0.1, sz * 0.6)]:
        g = (30 + var, 120 + var * 2, 35 + var)
        shaded_ellipse(draw, cx + int(lx), cy + int(ly), int(lr), int(lr * 0.75), g)

random.seed(42)
for _ in range(20):
    tx = random.randint(20, int(W * 0.35))
    ty = random.randint(ground_y + 5, ground_y + 90)
    ts = random.randint(20, 42)
    draw_tree(tx, ty, ts, random.randint(-8, 15))
# A few trees in the middle
for _ in range(5):
    tx = random.randint(int(W * 0.40), int(W * 0.55))
    ty = random.randint(ground_y + 15, ground_y + 60)
    draw_tree(tx, ty, random.randint(15, 28), random.randint(0, 20))

# ── Portal (right side, in desert) ──
pcx, pcy = int(W * 0.82), ground_y - 30
pl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
pd = ImageDraw.Draw(pl)
# Glow
for r in range(95, 55, -1):
    a = int(55 * (95 - r) / 40)
    pd.ellipse([pcx - r, pcy - int(r * 1.5), pcx + r, pcy + int(r * 1.5)], fill=(120, 40, 200, a))
# Body
for r in range(60, 0, -1):
    t = r / 60
    c = lerp((220, 130, 255), (50, 0, 100), t)
    pd.ellipse([pcx - r, pcy - int(r * 1.45), pcx + r, pcy + int(r * 1.45)], fill=c + (235,))
# Swirl
random.seed(77)
for a in range(0, 720, 7):
    rad = math.radians(a)
    sr = 48 * (1 - a / 720)
    sx = pcx + int(sr * math.cos(rad * 2.5 + sr * 0.09))
    sy = pcy + int(sr * 1.4 * math.sin(rad * 2.5 + sr * 0.09))
    ps = max(1, int(3 * (1 - a / 720)))
    pd.ellipse([sx - ps, sy - ps, sx + ps, sy + ps], fill=(240, 190, 255, 140))
# Frame
pd.ellipse([pcx - 63, pcy - 92, pcx + 63, pcy + 92], outline=(190, 110, 240, 220), width=4)
pd.ellipse([pcx - 67, pcy - 97, pcx + 67, pcy + 97], outline=(110, 45, 170, 160), width=3)
img = Image.alpha_composite(img, pl)
draw = ImageDraw.Draw(img)

# ── Sun ──
sl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(sl)
scx, scy = W - 140, 75
for r in range(75, 28, -1):
    a = int(45 * (75 - r) / 47)
    sd.ellipse([scx - r, scy - r, scx + r, scy + r], fill=(255, 240, 100, a))
shaded_ellipse(sd, scx, scy, 30, 30, (255, 245, 140))
img = Image.alpha_composite(img, sl)
draw = ImageDraw.Draw(img)

# Clouds
cl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
cd = ImageDraw.Draw(cl)
for ccx, ccy, cw in [(200, 65, 65), (550, 45, 50), (950, 80, 60), (1400, 50, 48)]:
    for dx, dy, cr in [(-cw // 2, 4, cw // 2), (0, -cw // 5, cw // 2 + 4),
                        (cw // 2, 2, cw // 2 - 6), (cw // 4, cw // 6, cw // 3)]:
        for r in range(cr, 0, -1):
            a = int(170 * (1 - (r / cr) ** 2))
            cd.ellipse([ccx + dx - r, ccy + dy - r, ccx + dx + r, ccy + dy + r],
                       fill=(242, 246, 255, a))
img = Image.alpha_composite(img, cl)
draw = ImageDraw.Draw(img)

# ══════════════════════════════════════════════════════════════
# SLIM 2.5D DRAGON
# ══════════════════════════════════════════════════════════════

def draw_dragon(x, y, body, wing, eye, sz=1.0, left=False, name="",
                belly=None, fx_func=None, split_body=None):
    """Draw a slim, properly proportioned 2.5D dragon."""
    global img, draw
    s = sz
    f = -1 if left else 1
    if belly is None:
        belly = shade(body, 45)

    # Ground shadow
    sl2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sld = ImageDraw.Draw(sl2)
    sld.ellipse([x - int(50 * s), y + int(22 * s), x + int(50 * s), y + int(30 * s)],
                fill=(0, 0, 0, 40))
    img = Image.alpha_composite(img, sl2)
    draw = ImageDraw.Draw(img)

    body_draw = body

    # ── Tail (long, curved, thin) ──
    for i in range(25):
        t = i / 24
        ttx = x - int(f * (40 + 70 * t) * s)
        tty = y + int((5 - 20 * t + 15 * math.sin(t * 4)) * s)
        thick = max(2, int((8 - 6 * t) * s))
        tc = lerp(body, shade(body, -25), t)
        draw.ellipse([ttx - thick, tty - thick // 2, ttx + thick, tty + thick // 2], fill=tc)
    # Tail spade
    tp_x = x - int(f * 110 * s)
    tp_y = y - int(12 * s)
    draw.polygon([(tp_x, tp_y - int(8 * s)), (tp_x - int(f * 12 * s), tp_y),
                   (tp_x, tp_y + int(6 * s))], fill=wing, outline=(30, 30, 30), width=1)

    # ── Wing (behind body) ──
    wl2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wl2)
    wx, wy = x - int(f * 8 * s), y - int(22 * s)
    pts = [
        (wx, wy),
        (wx - int(f * 40 * s), wy - int(55 * s)),
        (wx - int(f * 22 * s), wy - int(30 * s)),
        (wx - int(f * 58 * s), wy - int(42 * s)),
        (wx - int(f * 32 * s), wy - int(18 * s)),
        (wx - int(f * 65 * s), wy - int(22 * s)),
        (wx - int(f * 38 * s), wy + int(10 * s)),
        (wx, wy + int(5 * s)),
    ]
    wd.polygon(pts, fill=wing + (190,), outline=(35, 35, 35, 200), width=2)
    bone = shade(wing, -35) + (190,)
    for bi in [1, 3, 5]:
        wd.line([(wx, wy), pts[bi]], fill=bone, width=max(1, int(2.5 * s)))
    img = Image.alpha_composite(img, wl2)
    draw = ImageDraw.Draw(img)

    # ── Hind legs ──
    for off in [16]:
        lx = x + int(off * s * f * 0.4)
        ly = y + int(12 * s)
        shaded_ellipse(draw, lx, ly, int(7 * s), int(11 * s), shade(body, -15), (35, 35, 35))
        shaded_ellipse(draw, lx - int(f * 2 * s), ly + int(15 * s), int(5 * s), int(6 * s), shade(body, -20))
        for cl in [-3, 0, 3]:
            draw.ellipse([lx + int(cl * s) - 1, ly + int(19 * s),
                          lx + int(cl * s) + 2, ly + int(23 * s)], fill=(50, 50, 50))

    # ── Body (slimmer! wider than tall) ──
    bw, bh = int(42 * s), int(22 * s)

    if split_body:
        # For TwinWing: left half one color, right half another
        c1, c2 = split_body
        # Draw body as two halves blended
        for ring in range(max(bw, bh), 0, -1):
            frac = ring / max(bw, bh)
            srx, sry = int(bw * frac), int(bh * frac)
            # left half color 1, right half color 2, blend in middle
            for dx in range(-srx, srx + 1):
                blend = (dx + srx) / max(1, 2 * srx)  # 0 = left, 1 = right
                base = lerp(c1, c2, blend)
                hi = shade(base, 50)
                sh2 = shade(base, -40)
                if frac > 0.55:
                    c = lerp(base, sh2, (frac - 0.55) / 0.45)
                else:
                    c = lerp(hi, base, frac / 0.55)
                dy_max = int(sry * math.sqrt(max(0, 1 - (dx / max(1, srx)) ** 2)))
                for dy in range(-dy_max, dy_max + 1, max(1, dy_max // 3)):
                    draw.point((x + dx, y + dy), fill=c)
        draw.ellipse([x - bw, y - bh, x + bw, y + bh], outline=(35, 35, 35), width=2)
    else:
        shaded_ellipse(draw, x, y, bw, bh, body, (35, 35, 35))

    # Belly highlight
    shaded_ellipse(draw, x + int(f * 5 * s), y + int(5 * s), int(28 * s), int(12 * s), belly)

    # ── Front legs ──
    flx = x + int(f * 20 * s)
    fly = y + int(12 * s)
    shaded_ellipse(draw, flx, fly, int(6 * s), int(10 * s), body, (35, 35, 35))
    shaded_ellipse(draw, flx + int(f * 2 * s), fly + int(14 * s), int(5 * s), int(5 * s), shade(body, -10))
    for cl in [-3, 0, 3]:
        draw.ellipse([flx + int(f * 2 * s) + int(cl * s) - 1, fly + int(17 * s),
                      flx + int(f * 2 * s) + int(cl * s) + 2, fly + int(21 * s)], fill=(50, 50, 50))

    # ── Neck (curved, slender) ──
    for ni in range(15):
        t = ni / 14
        nx = x + int(f * (18 + 30 * t) * s)
        ny = y - int((12 + 28 * t) * s)
        nr = max(3, int((11 - 4 * t) * s))
        nc = lerp(body, shade(body, -8), t)
        shaded_ellipse(draw, nx, ny, nr, int(nr * 0.7), nc)

    # ── Head (elongated snout) ──
    hx = x + int(f * 52 * s)
    hy = y - int(44 * s)
    hr = int(16 * s)
    shaded_ellipse(draw, hx, hy, hr, int(hr * 0.75), body, (35, 35, 35))
    # Snout - longer, thinner
    snx = hx + int(f * 22 * s)
    shaded_ellipse(draw, snx, hy + int(2 * s), int(14 * s), int(7 * s), shade(body, 8))
    # Nostrils
    for no in [3, 7]:
        draw.ellipse([snx + int(f * no * s) - 1, hy - 1, snx + int(f * no * s) + 2, hy + 2], fill=(25, 25, 25))
    # Jaw line
    jaw_x1 = min(hx - int(8 * s), hx + int(f * 30 * s))
    jaw_x2 = max(hx - int(8 * s), hx + int(f * 30 * s))
    draw.arc([jaw_x1, hy + int(2 * s), jaw_x2, hy + int(12 * s)],
             10 if not left else 150, 170 if not left else 350, fill=(40, 40, 40), width=1)

    # Eye
    ex, ey = hx + int(f * 4 * s), hy - int(4 * s)
    er = int(5.5 * s)
    # White
    shaded_ellipse(draw, ex, ey, er, int(er * 0.9), (250, 250, 255), (30, 30, 30))
    # Iris
    ir = int(3.5 * s)
    for r in range(ir, 0, -1):
        t = r / ir
        draw.ellipse([ex - r, ey - r, ex + r, ey + r], fill=lerp(shade(eye, 35), shade(eye, -25), t))
    # Pupil (slit)
    draw.ellipse([ex - int(1.5 * s), ey - int(2.5 * s), ex + int(1.5 * s), ey + int(2.5 * s)], fill=(8, 8, 8))
    # Highlight
    draw.ellipse([ex - int(2 * s), ey - int(3 * s), ex - int(0.5 * s), ey - int(1 * s)], fill=(255, 255, 255))

    # Horns (two, swept back)
    for ho in [-6, 3]:
        hbx = hx + int(ho * s * f * 0.4)
        hby = hy - int(hr * 0.65)
        tip_x = hbx - int(f * 8 * s)
        tip_y = hby - int(16 * s)
        # Draw horn with gradient
        for hi in range(int(18 * s)):
            t = hi / (18 * s)
            hc = lerp((215, 200, 145), (140, 120, 70), t)
            hw = max(1, int(3.5 * s * (1 - t)))
            hy2 = hby - hi
            hx2 = hbx + int((tip_x - hbx) * t)
            draw.line([(hx2 - hw, hy2), (hx2 + hw, hy2)], fill=hc)

    # Spines along back
    for si in range(7):
        t = si / 6
        sp_x = x + int(f * (-22 + 12 * t) * s)
        sp_y = y - int((20 + 6 * math.sin(t * 3)) * s)
        sp_h = int((7 + 4 * (1 - t)) * s)
        draw.polygon([(sp_x - int(1.5 * s), sp_y), (sp_x + int(1.5 * s), sp_y),
                       (sp_x, sp_y - sp_h)], fill=shade(wing, -15), outline=(45, 45, 45))

    # Label
    if name:
        try:
            font = ImageFont.truetype("arial.ttf", max(12, int(13 * s)))
        except:
            font = ImageFont.load_default()
        tlen = draw.textlength(name, font=font)
        ly = y + int(30 * s)
        draw.rounded_rectangle([x - tlen // 2 - 5, ly - 1, x + tlen // 2 + 5, ly + 16],
                                radius=7, fill=(15, 15, 20, 200), outline=(90, 90, 110))
        draw.text((x - tlen // 2, ly), name, fill=(255, 255, 255), font=font)

    # FX
    if fx_func:
        fx_func(x, y, s, f, hx, hy)


# ══════════════════════════════════════════════════════════════
# FAN-MADE FX
# ══════════════════════════════════════════════════════════════

def errorwing_fx(x, y, s, f, hx, hy):
    global img, draw
    fl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fl)
    random.seed(int(x * 7 + y * 3))
    for _ in range(55):
        gx = x + random.randint(int(-60 * s), int(60 * s))
        gy = y + random.randint(int(-50 * s), int(40 * s))
        gw = random.randint(3, int(12 * s))
        gh = random.randint(1, int(4 * s))
        c = random.choice([(180, 0, 255, 150), (120, 0, 200, 130),
                            (0, 0, 0, 170), (220, 60, 255, 110), (50, 0, 80, 140)])
        fd.rectangle([gx, gy, gx + gw, gy + gh], fill=c)
    for _ in range(7):
        gy = y + random.randint(int(-40 * s), int(30 * s))
        gw = random.randint(15, int(55 * s))
        gx = x + random.randint(int(-35 * s), int(20 * s))
        fd.rectangle([gx, gy, gx + gw, gy + 2],
                     fill=random.choice([(200, 0, 255, 90), (0, 0, 0, 110)]))
    img = Image.alpha_composite(img, fl)
    draw = ImageDraw.Draw(img)

def twinwing_fx(x, y, s, f, hx, hy):
    global img, draw
    ol = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ol)
    orbs = [((255, 30, 30), x - int(38 * s), y - int(48 * s)),
            ((30, 70, 255), x + int(38 * s), y - int(48 * s))]
    for oc, ox, oy in orbs:
        for r in range(int(20 * s), int(10 * s), -1):
            a = int(50 * (int(20 * s) - r) / (10 * s))
            od.ellipse([ox - r, oy - r, ox + r, oy + r], fill=oc + (a,))
        for r in range(int(10 * s), 0, -1):
            t = r / (10 * s)
            c = lerp((255, 255, 255), oc, t)
            od.ellipse([ox - r, oy - r, ox + r, oy + r], fill=c + (220,))
        od.ellipse([ox - int(3 * s), oy - int(4 * s), ox, oy - int(1.5 * s)], fill=(255, 255, 255, 200))
    img = Image.alpha_composite(img, ol)
    draw = ImageDraw.Draw(img)

def cloudwing_fx(x, y, s, f, hx, hy):
    global img, draw
    cl2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cld = ImageDraw.Draw(cl2)
    random.seed(int(x * 5 + y))
    for _ in range(25):
        cx2 = x + random.randint(int(-55 * s), int(55 * s))
        cy2 = y + random.randint(int(-40 * s), int(30 * s))
        cr = random.randint(int(7 * s), int(18 * s))
        for r in range(cr, 0, -1):
            a = int(80 * (1 - (r / cr) ** 2))
            sv = random.randint(235, 248)
            cld.ellipse([cx2 - r, cy2 - r, cx2 + r, cy2 + int(r * 0.7)], fill=(sv, sv, sv + 5, a))
    img = Image.alpha_composite(img, cl2)
    draw = ImageDraw.Draw(img)

def cyberwing_fx(x, y, s, f, hx, hy):
    global img, draw
    cl2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cld = ImageDraw.Draw(cl2)
    random.seed(int(x + y * 7))
    ps = max(3, int(4 * s))
    for px in range(x - int(50 * s), x + int(50 * s), ps):
        for py in range(y - int(40 * s), y + int(35 * s), ps):
            if random.random() < 0.22:
                sc = random.choice([(0, 120, 255, 90), (0, 200, 255, 70),
                                     (0, 80, 220, 110), (0, 255, 255, 50)])
                cld.rectangle([px, py, px + ps - 1, py + ps - 1], fill=sc)
    for _ in range(4):
        ly = y + random.randint(int(-30 * s), int(25 * s))
        cld.line([(x - int(45 * s), ly), (x + int(45 * s), ly)], fill=(0, 220, 255, 70), width=1)
    img = Image.alpha_composite(img, cl2)
    draw = ImageDraw.Draw(img)


# ══════════════════════════════════════════════════════════════
# PLACE ALL DRAGONS — well-spaced layout
# ══════════════════════════════════════════════════════════════

dragons = [
    # ── FOREST (left area, x: 60-400) ──
    {"x": 80, "y": ground_y + 50, "body": (120, 85, 50), "wing": (155, 115, 55),
     "eye": (190, 155, 45), "name": "MudWing", "sz": 0.82, "left": False, "belly": (165, 135, 85)},

    {"x": 220, "y": ground_y + 15, "body": (15, 155, 45), "wing": (55, 195, 65),
     "eye": (0, 115, 0), "name": "LeafWing", "sz": 0.74, "left": True, "belly": (75, 195, 95)},

    {"x": 130, "y": ground_y + 130, "body": (225, 45, 35), "wing": (250, 125, 35),
     "eye": (250, 205, 0), "name": "SkyWing", "sz": 0.76, "left": False, "belly": (250, 125, 95)},

    {"x": 370, "y": ground_y + 100, "body": (35, 185, 55), "wing": (250, 75, 175),
     "eye": (75, 250, 75), "name": "RainWing", "sz": 0.73, "left": True, "belly": (95, 215, 115)},

    # ── CAVE AREA (near cave entrance, x: ~500-600) ──
    # NightWing lurking near cave
    {"x": cave_cx - 90, "y": cave_cy + 45, "body": (30, 18, 65), "wing": (50, 22, 105),
     "eye": (115, 0, 215), "name": "NightWing", "sz": 0.8, "left": False, "belly": (65, 45, 95)},

    # ── MIDDLE / RIVER (x: 650-900) ──
    {"x": 650, "y": ground_y + 25, "body": (25, 95, 165), "wing": (45, 155, 205),
     "eye": (0, 175, 250), "name": "SeaWing", "sz": 0.8, "left": False, "belly": (75, 155, 215)},

    {"x": 800, "y": ground_y - 15, "body": (195, 220, 245), "wing": (165, 205, 240),
     "eye": (75, 125, 250), "name": "IceWing", "sz": 0.74, "left": True, "belly": (225, 235, 250)},

    {"x": 750, "y": ground_y + 100, "body": (195, 165, 220), "wing": (220, 190, 245),
     "eye": (155, 75, 215), "name": "SilkWing", "sz": 0.72, "left": False, "belly": (225, 205, 240)},

    {"x": 940, "y": ground_y + 10, "body": (215, 165, 35), "wing": (205, 140, 10),
     "eye": (45, 45, 45), "name": "HiveWing", "sz": 0.74, "left": True, "belly": (235, 205, 95)},

    # ── DESERT (far right, x: 1500-1700) ──
    {"x": 1680, "y": ground_y + 60, "body": (230, 205, 115), "wing": (240, 220, 135),
     "eye": (35, 35, 35), "name": "SandWing", "sz": 0.84, "left": True, "belly": (245, 230, 165)},

    # ═══ FAN-MADE ═══

    # ErrorWing — forest edge, glitch particles
    {"x": 480, "y": ground_y + 40, "body": (85, 0, 125), "wing": (145, 5, 205),
     "eye": (255, 0, 255), "name": "ErrorWing \u2605", "sz": 0.8, "left": False,
     "belly": (115, 35, 155), "fx": errorwing_fx},

    # TwinWing — split red/blue body, red+blue orbs, in grassland
    {"x": 1080, "y": ground_y + 80, "body": (160, 40, 60), "wing": (120, 60, 180),
     "eye": (250, 195, 0), "name": "TwinWing \u2605", "sz": 0.8, "left": True,
     "belly": (180, 80, 100), "fx": twinwing_fx,
     "split": ((220, 40, 40), (40, 60, 220))},  # RED left, BLUE right

    # CloudWing — floating above, cloud-like
    {"x": 820, "y": ground_y - 120, "body": (232, 235, 245), "wing": (210, 220, 242),
     "eye": (95, 155, 250), "name": "CloudWing \u2605", "sz": 0.84, "left": False,
     "belly": (242, 245, 252), "fx": cloudwing_fx},

    # CyberWing — near portal (NOT near SandWing)
    {"x": pcx - 10, "y": pcy + 80, "body": (5, 65, 165), "wing": (0, 125, 235),
     "eye": (0, 250, 250), "name": "CyberWing \u2605", "sz": 0.8, "left": True,
     "belly": (35, 105, 195), "fx": cyberwing_fx},
]

# Sort by Y for depth ordering
dragons.sort(key=lambda d: d["y"])

for d in dragons:
    draw_dragon(
        d["x"], d["y"], d["body"], d["wing"], d["eye"],
        sz=d.get("sz", 0.75), left=d.get("left", False),
        name=d.get("name", ""), belly=d.get("belly"),
        fx_func=d.get("fx"), split_body=d.get("split"))

# ── Title ──
try:
    tf = ImageFont.truetype("arial.ttf", 34)
    sf = ImageFont.truetype("arial.ttf", 17)
except:
    tf = ImageFont.load_default()
    sf = ImageFont.load_default()

title = "Wings of Fire \u2014 All Tribes"
tl = draw.textlength(title, font=tf)
draw.rounded_rectangle([W // 2 - tl // 2 - 14, 14, W // 2 + tl // 2 + 14, 52],
                        radius=10, fill=(12, 12, 22, 215), outline=(200, 175, 75))
draw.text((W // 2 - tl // 2, 16), title, fill=(255, 220, 55), font=tf)

sub = "\u2605 = Fan-Made Tribes"
sl3 = draw.textlength(sub, font=sf)
draw.rounded_rectangle([W // 2 - sl3 // 2 - 10, 58, W // 2 + sl3 // 2 + 10, 78],
                        radius=7, fill=(12, 12, 22, 200))
draw.text((W // 2 - sl3 // 2, 60), sub, fill=(195, 145, 250), font=sf)

# ── Save ──
final = img.convert("RGB")
final.save("wof_all_tribes.png", "PNG")
print(f"Saved wof_all_tribes.png ({W}x{H})")
