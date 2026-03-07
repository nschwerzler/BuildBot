"""
Wings of Fire — All Dragon Tribes (2.5D Smooth Style)
Generates a polished 2.5D scene with shaded dragons, environment depth,
and all canon + fan-made tribes.
"""
from PIL import Image, ImageDraw, ImageFont
import random, math

W, H = 1920, 1080
img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
draw = ImageDraw.Draw(img)

def lerp_color(c1, c2, t):
    t = max(0, min(1, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

def draw_smooth_ellipse(cx, cy, rx, ry, base_color, highlight_color, shadow_color):
    """Draw an ellipse with 2.5D shading."""
    for ring in range(max(rx, ry), 0, -1):
        t = ring / max(rx, ry)
        srx = int(rx * t)
        sry = int(ry * t)
        if t > 0.6:
            c = lerp_color(base_color, shadow_color, (t - 0.6) / 0.4)
        else:
            c = lerp_color(highlight_color, base_color, t / 0.6)
        draw.ellipse([cx - srx, cy - sry, cx + srx, cy + sry], fill=c)

def draw_shaded_ellipse(cx, cy, rx, ry, color, outline=True):
    hi = tuple(min(255, c + 60) for c in color[:3])
    sh = tuple(max(0, c - 50) for c in color[:3])
    draw_smooth_ellipse(cx, cy, rx, ry, color, hi, sh)
    if outline:
        draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=(30, 30, 30), width=2)

def draw_gradient_rect(x1, y1, x2, y2, top_color, bot_color):
    for y in range(y1, y2):
        t = (y - y1) / max(1, y2 - y1)
        c = lerp_color(top_color, bot_color, t)
        draw.line([(x1, y), (x2, y)], fill=c)

def shade(color, amount):
    return tuple(max(0, min(255, c + amount)) for c in color[:3])

# ══════════════════════════════════════════════════════════════
# ENVIRONMENT
# ══════════════════════════════════════════════════════════════

# Sky gradient
draw_gradient_rect(0, 0, W, H * 55 // 100, (135, 200, 255), (200, 230, 255))

# Distant mountains
ground_y = H * 50 // 100
for mx, mw, mh, sv in [(200, 300, 120, 0), (500, 250, 100, 10), (800, 350, 140, -5),
                         (1100, 280, 110, 5), (1400, 320, 130, -3), (1700, 260, 95, 8)]:
    mc = (120 + sv, 150 + sv, 180 + sv)
    pts = [(mx - mw // 2, ground_y)]
    for i in range(0, mw + 1, 20):
        peak = mh * math.sin(math.pi * i / mw) * (0.7 + 0.3 * math.sin(i * 0.1))
        pts.append((mx - mw // 2 + i, ground_y - int(peak)))
    pts.append((mx + mw // 2, ground_y))
    draw.polygon(pts, fill=mc)

# Ground zones
draw_gradient_rect(0, ground_y, int(W * 0.42), H, (60, 140, 50), (40, 100, 35))
draw_gradient_rect(int(W * 0.42), ground_y, int(W * 0.7), H, (70, 155, 55), (50, 120, 40))
draw_gradient_rect(int(W * 0.7), ground_y, W, H, (220, 195, 130), (190, 160, 100))

# Desert-grass blend
for x in range(int(W * 0.65), int(W * 0.75)):
    t = (x - W * 0.65) / (W * 0.1)
    for y in range(ground_y, H):
        yt = (y - ground_y) / max(1, H - ground_y)
        grass = lerp_color((70, 155, 55), (50, 120, 40), yt)
        sand = lerp_color((220, 195, 130), (190, 160, 100), yt)
        c = lerp_color(grass, sand, t)
        draw.point((x, y), fill=c)

# Sand dunes
for dcx, dcy, dw, dh in [(W * 78 // 100, ground_y + 60, 120, 25),
                           (W * 88 // 100, ground_y + 90, 100, 20),
                           (W * 72 // 100, ground_y + 130, 80, 15)]:
    for dy in range(dh):
        t = dy / dh
        c = lerp_color((235, 215, 155), (200, 175, 120), t)
        hw = int(dw * math.sqrt(max(0, 1 - (dy / dh) ** 2)))
        draw.line([(dcx - hw, dcy - dh + dy), (dcx + hw, dcy - dh + dy)], fill=c)

# River
river_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
rd = ImageDraw.Draw(river_layer)
river_pts = []
for rx in range(int(W * 0.3), int(W * 0.75), 3):
    t = (rx - W * 0.3) / (W * 0.45)
    ry_base = ground_y + 140 + int(60 * math.sin(t * 4.5)) + int(t * 80)
    river_pts.append((rx, ry_base))
for i, pt in enumerate(river_pts):
    rw = 30 + int(8 * math.sin(i * 0.05))
    t = i / len(river_pts)
    deep = lerp_color((40, 100, 200), (30, 80, 170), t)
    light = lerp_color((80, 160, 240), (60, 140, 220), t)
    for dy in range(-rw, rw + 1):
        dt = abs(dy) / rw
        c = lerp_color(light, deep, dt)
        rd.point((pt[0], pt[1] + dy), fill=c + (200,))
for i in range(0, len(river_pts), 12):
    pt = river_pts[i]
    for sr in range(8, 0, -1):
        a = int(80 * (1 - sr / 8))
        rd.ellipse([pt[0] - sr, pt[1] - sr // 2, pt[0] + sr, pt[1] + sr // 2],
                   fill=(180, 220, 255, a))
img = Image.alpha_composite(img, river_layer)
draw = ImageDraw.Draw(img)

# Trees
def draw_tree_25d(cx, cy, size, shade_var=0):
    s = size
    tw2 = int(s * 0.25)
    th = int(s * 1.2)
    for dx in range(-tw2, tw2 + 1):
        t = (dx + tw2) / max(1, 2 * tw2)
        c = lerp_color((90 + shade_var, 60 + shade_var, 25), (60 + shade_var, 40 + shade_var, 15), t)
        draw.line([(cx + dx, cy), (cx + dx, cy + th)], fill=c)
    for layer in [(0, -s * 0.8, s * 0.9), (-s * 0.4, -s * 0.4, s * 0.7),
                   (s * 0.35, -s * 0.45, s * 0.65), (0, -s * 0.3, s * 0.75), (0, -s * 1.1, s * 0.6)]:
        fx2, fy, fr = int(layer[0]), int(layer[1]), int(layer[2])
        base_g = (35 + shade_var, 130 + shade_var * 2, 40 + shade_var)
        draw_shaded_ellipse(cx + fx2, cy + fy, fr, int(fr * 0.8), base_g, outline=False)

random.seed(42)
for _ in range(22):
    tx = random.randint(30, int(W * 0.38))
    ty = random.randint(ground_y - 10, ground_y + 80)
    ts = random.randint(18, 40)
    draw_tree_25d(tx, ty, ts, random.randint(-10, 20))

# Portal
pcx, pcy = int(W * 0.73), ground_y - 20
portal_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
pd = ImageDraw.Draw(portal_layer)
for r in range(90, 60, -1):
    a = int(60 * (90 - r) / 30)
    pd.ellipse([pcx - r, pcy - int(r * 1.5), pcx + r, pcy + int(r * 1.5)], fill=(120, 40, 200, a))
for r in range(65, 0, -1):
    t = r / 65
    c = lerp_color((220, 120, 255), (60, 0, 120), t)
    pd.ellipse([pcx - r, pcy - int(r * 1.45), pcx + r, pcy + int(r * 1.45)], fill=c + (230,))
random.seed(99)
for a in range(0, 720, 8):
    rad = math.radians(a)
    sr = 55 * (1 - a / 720)
    sx2 = pcx + int(sr * math.cos(rad * 2 + sr * 0.08))
    sy2 = pcy + int(sr * 1.4 * math.sin(rad * 2 + sr * 0.08))
    ps = max(1, int(3 * (1 - a / 720)))
    pd.ellipse([sx2 - ps, sy2 - ps, sx2 + ps, sy2 + ps], fill=(230, 180, 255, 150))
pd.ellipse([pcx - 68, pcy - 98, pcx + 68, pcy + 98], outline=(180, 100, 230, 200), width=4)
pd.ellipse([pcx - 72, pcy - 104, pcx + 72, pcy + 104], outline=(100, 40, 160, 150), width=3)
img = Image.alpha_composite(img, portal_layer)
draw = ImageDraw.Draw(img)

# Sun
sun_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(sun_layer)
scx, scy = W - 150, 80
for r in range(80, 30, -1):
    a = int(40 * (80 - r) / 50)
    sd.ellipse([scx - r, scy - r, scx + r, scy + r], fill=(255, 240, 100, a))
draw_tmp = draw
draw = sd
draw_smooth_ellipse(scx, scy, 35, 35, (255, 245, 140), (255, 255, 200), (255, 220, 60))
draw = draw_tmp
img = Image.alpha_composite(img, sun_layer)
draw = ImageDraw.Draw(img)

# Clouds
cloud_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
cd = ImageDraw.Draw(cloud_layer)
for ccx, ccy, cw in [(250, 70, 70), (600, 50, 55), (1000, 85, 65), (1500, 45, 50)]:
    for dx, dy, cr in [(-cw // 2, 5, cw // 2), (0, -cw // 5, cw // 2 + 5),
                        (cw // 2, 3, cw // 2 - 5), (cw // 4, cw // 6, cw // 3),
                        (-cw // 4, cw // 7, cw // 3)]:
        for r in range(cr, 0, -1):
            a = int(180 * (1 - (r / cr) ** 2))
            cd.ellipse([ccx + dx - r, ccy + dy - r, ccx + dx + r, ccy + dy + r],
                       fill=(245, 248, 255, a))
img = Image.alpha_composite(img, cloud_layer)
draw = ImageDraw.Draw(img)

# ══════════════════════════════════════════════════════════════
# 2.5D DRAGON
# ══════════════════════════════════════════════════════════════

def draw_dragon_25d(x, y, body_col, wing_col, eye_col, size=1.0,
                     facing_left=False, name="", extras=None, belly_col=None):
    global img, draw
    s = size
    fx = -1 if facing_left else 1
    if belly_col is None:
        belly_col = shade(body_col, 50)

    # Shadow
    sl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sld = ImageDraw.Draw(sl)
    sld.ellipse([x - int(55 * s), y + int(30 * s), x + int(55 * s), y + int(42 * s)],
                fill=(0, 0, 0, 50))
    img = Image.alpha_composite(img, sl)
    draw = ImageDraw.Draw(img)

    # Tail
    for i in range(20):
        t = i / 19
        ttx = x - int(fx * (50 + 50 * t) * s)
        tty = y + int((10 - 30 * t) * s) + int(8 * math.sin(t * 5) * s)
        thickness = int((10 - 6 * t) * s)
        tc = lerp_color(body_col, shade(body_col, -30), t)
        draw.ellipse([ttx - thickness // 2, tty - thickness // 3,
                      ttx + thickness // 2, tty + thickness // 3], fill=tc)
    tp_x = x - int(fx * 100 * s)
    tp_y = y - int(20 * s)
    draw.polygon([(tp_x, tp_y - int(10 * s)), (tp_x - int(fx * 14 * s), tp_y),
                   (tp_x, tp_y + int(8 * s))], fill=wing_col, outline=(30, 30, 30), width=1)

    # Wings behind body
    wl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wl)
    wx = x - int(fx * 5 * s)
    wy = y - int(28 * s)
    wing_span = [
        (wx, wy), (wx - int(fx * 35 * s), wy - int(50 * s)),
        (wx - int(fx * 20 * s), wy - int(28 * s)), (wx - int(fx * 55 * s), wy - int(38 * s)),
        (wx - int(fx * 30 * s), wy - int(15 * s)), (wx - int(fx * 60 * s), wy - int(18 * s)),
        (wx - int(fx * 35 * s), wy + int(12 * s)), (wx, wy + int(8 * s)),
    ]
    wd.polygon(wing_span, fill=wing_col + (200,), outline=(30, 30, 30, 200), width=2)
    bone_col = shade(wing_col, -40) + (180,)
    wd.line([(wx, wy), wing_span[1]], fill=bone_col, width=int(3 * s))
    wd.line([(wx, wy), wing_span[3]], fill=bone_col, width=int(2 * s))
    wd.line([(wx, wy), wing_span[5]], fill=bone_col, width=int(2 * s))
    for i in range(3):
        midx = (wx + wing_span[1 + i * 2][0]) // 2
        midy = (wy + wing_span[1 + i * 2][1]) // 2
        wd.ellipse([midx - int(8 * s), midy - int(5 * s),
                    midx + int(8 * s), midy + int(5 * s)], fill=shade(wing_col, 30) + (60,))
    img = Image.alpha_composite(img, wl)
    draw = ImageDraw.Draw(img)

    # Back legs
    for lx_off in [20]:
        lx = x + int(lx_off * s * fx * 0.5)
        ly = y + int(18 * s)
        draw_shaded_ellipse(lx, ly, int(10 * s), int(14 * s), shade(body_col, -20))
        draw_shaded_ellipse(lx, ly + int(18 * s), int(7 * s), int(8 * s), shade(body_col, -25))
        for c_off in [-4, 0, 4]:
            draw.ellipse([lx + int(c_off * s) - 2, ly + int(24 * s),
                          lx + int(c_off * s) + 3, ly + int(28 * s)], fill=(60, 60, 60))

    # Body
    bw, bh = int(52 * s), int(32 * s)
    draw_shaded_ellipse(x, y, bw, bh, body_col)
    draw_shaded_ellipse(x, y + int(8 * s), int(35 * s), int(18 * s), belly_col, outline=False)

    # Front legs
    for lx_off in [-15]:
        lx = x + int(lx_off * s * fx) + int(fx * 15 * s)
        ly = y + int(18 * s)
        draw_shaded_ellipse(lx, ly, int(9 * s), int(13 * s), body_col)
        draw_shaded_ellipse(lx + int(fx * 3 * s), ly + int(16 * s), int(7 * s), int(7 * s), shade(body_col, -15))
        for c_off in [-4, 0, 4]:
            draw.ellipse([lx + int(fx * 3 * s) + int(c_off * s) - 2, ly + int(21 * s),
                          lx + int(fx * 3 * s) + int(c_off * s) + 3, ly + int(25 * s)], fill=(55, 55, 55))

    # Neck
    for ni in range(12):
        t = ni / 11
        nx = x + int(fx * (20 + 25 * t) * s)
        ny = y - int((15 + 22 * t) * s)
        nr = int((14 - 3 * t) * s)
        nc = lerp_color(body_col, shade(body_col, -10), t)
        draw_shaded_ellipse(nx, ny, nr, int(nr * 0.85), nc, outline=False)

    # Head
    hx = x + int(fx * 50 * s)
    hy = y - int(42 * s)
    hr = int(20 * s)
    draw_shaded_ellipse(hx, hy, hr, int(hr * 0.85), body_col)
    snx = hx + int(fx * 20 * s)
    draw_shaded_ellipse(snx, hy + int(3 * s), int(14 * s), int(9 * s), shade(body_col, 10))
    draw.ellipse([snx + int(fx * 6 * s) - 2, hy + int(1 * s) - 2,
                  snx + int(fx * 6 * s) + 2, hy + int(1 * s) + 2], fill=(30, 30, 30))

    # Eye
    ex = hx + int(fx * 6 * s)
    ey = hy - int(5 * s)
    er = int(7 * s)
    for r in range(er, 0, -1):
        t = r / er
        ec = lerp_color((255, 255, 255), (220, 220, 230), t)
        draw.ellipse([ex - r, ey - r, ex + r, ey + r], fill=ec)
    draw.ellipse([ex - er, ey - er, ex + er, ey + er], outline=(30, 30, 30), width=2)
    ir = int(4.5 * s)
    for r in range(ir, 0, -1):
        t = r / ir
        ic = lerp_color(shade(eye_col, 30), shade(eye_col, -30), t)
        draw.ellipse([ex - r, ey - r, ex + r, ey + r], fill=ic)
    pr2 = int(2 * s)
    draw.ellipse([ex - pr2, ey - pr2, ex + pr2, ey + pr2], fill=(10, 10, 10))
    draw.ellipse([ex - int(2 * s), ey - int(3 * s), ex, ey - int(1 * s)], fill=(255, 255, 255))

    # Horns
    for h_off in [-8, 2]:
        horn_bx = hx + int(h_off * s * fx * 0.5)
        horn_by = hy - int(hr * 0.75)
        for hi in range(int(16 * s)):
            t = hi / (16 * s)
            hc = lerp_color((210, 195, 140), (150, 130, 80), t)
            hw = int(4 * s * (1 - t))
            draw.line([(horn_bx - hw // 2, horn_by - hi), (horn_bx + hw // 2, horn_by - hi)], fill=hc)

    # Spines
    for si in range(6):
        t = si / 5
        spine_x = x + int(fx * (-25 + 15 * t) * s)
        spine_y = y - int((28 + 5 * math.sin(t * 3)) * s)
        spine_h = int((8 + 4 * (1 - t)) * s)
        draw.polygon([(spine_x - int(2 * s), spine_y), (spine_x + int(2 * s), spine_y),
                       (spine_x, spine_y - spine_h)], fill=shade(wing_col, -20), outline=(40, 40, 40))

    # Name label
    if name:
        try:
            font = ImageFont.truetype("arial.ttf", max(13, int(14 * s)))
        except:
            font = ImageFont.load_default()
        tw2 = draw.textlength(name, font=font)
        label_y = y + int(38 * s)
        pad = 6
        draw.rounded_rectangle([x - tw2 // 2 - pad, label_y - 2,
                                 x + tw2 // 2 + pad, label_y + 18],
                                radius=8, fill=(20, 20, 30, 200), outline=(100, 100, 120))
        draw.text((x - tw2 // 2, label_y), name, fill=(255, 255, 255), font=font)

    # Extras
    if extras:
        extras(draw, img, x, y, s, fx, hx, hy)

# ══════════════════════════════════════════════════════════════
# FAN-MADE FX
# ══════════════════════════════════════════════════════════════

def errorwing_fx(dr, im, x, y, s, fx, hx, hy):
    global img, draw
    fl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fl)
    random.seed(int(x * 7 + y * 3))
    for _ in range(50):
        gx = x + random.randint(int(-65 * s), int(65 * s))
        gy = y + random.randint(int(-55 * s), int(45 * s))
        gw = random.randint(3, int(10 * s))
        gh = random.randint(1, int(4 * s))
        color = random.choice([(180, 0, 255, 160), (120, 0, 200, 140),
                                (0, 0, 0, 180), (220, 60, 255, 120), (50, 0, 80, 150)])
        fd.rectangle([gx, gy, gx + gw, gy + gh], fill=color)
    for _ in range(6):
        gy = y + random.randint(int(-45 * s), int(35 * s))
        gw2 = random.randint(20, int(60 * s))
        gx = x + random.randint(int(-40 * s), int(20 * s))
        fd.rectangle([gx, gy, gx + gw2, gy + 2],
                     fill=random.choice([(200, 0, 255, 100), (0, 0, 0, 120)]))
    for _ in range(8):
        cx = x + random.randint(int(-30 * s), int(30 * s))
        cy = y + random.randint(int(-30 * s), int(20 * s))
        cs = random.randint(4, 12)
        fd.rectangle([cx, cy, cx + cs, cy + cs],
                     fill=random.choice([(160, 0, 220, 130), (0, 0, 0, 100), (255, 100, 255, 80)]))
    img = Image.alpha_composite(img, fl)
    draw = ImageDraw.Draw(img)

def twinwing_fx(dr, im, x, y, s, fx_dir, hx, hy):
    global img, draw
    ol = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ol)
    orbs = [((255, 40, 40), x - int(40 * s), y - int(52 * s)),
            ((40, 80, 255), x + int(40 * s), y - int(52 * s))]
    for orb_col, ox, oy in orbs:
        for r in range(int(22 * s), int(12 * s), -1):
            a = int(50 * (int(22 * s) - r) / (10 * s))
            od.ellipse([ox - r, oy - r, ox + r, oy + r], fill=orb_col + (a,))
        for r in range(int(12 * s), 0, -1):
            t = r / (12 * s)
            c = lerp_color((255, 255, 255), orb_col, t)
            od.ellipse([ox - r, oy - r, ox + r, oy + r], fill=c + (220,))
        od.ellipse([ox - int(4 * s), oy - int(5 * s), ox, oy - int(2 * s)], fill=(255, 255, 255, 200))
    img = Image.alpha_composite(img, ol)
    draw = ImageDraw.Draw(img)

def cloudwing_fx(dr, im, x, y, s, fx_dir, hx, hy):
    global img, draw
    cl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cld = ImageDraw.Draw(cl)
    random.seed(int(x * 5 + y))
    for _ in range(30):
        cx = x + random.randint(int(-60 * s), int(60 * s))
        cy = y + random.randint(int(-45 * s), int(35 * s))
        cr = random.randint(int(8 * s), int(20 * s))
        for r in range(cr, 0, -1):
            a = int(90 * (1 - (r / cr) ** 2))
            sv = random.randint(235, 250)
            cld.ellipse([cx - r, cy - r, cx + r, cy + int(r * 0.7)], fill=(sv, sv, sv + 5, a))
    img = Image.alpha_composite(img, cl)
    draw = ImageDraw.Draw(img)

def cyberwing_fx(dr, im, x, y, s, fx_dir, hx, hy):
    global img, draw
    cl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cld = ImageDraw.Draw(cl)
    random.seed(int(x + y * 7))
    psize = max(3, int(5 * s))
    for px in range(x - int(55 * s), x + int(55 * s), psize):
        for py in range(y - int(45 * s), y + int(45 * s), psize):
            if random.random() < 0.25:
                shade_c = random.choice([
                    (0, 120, 255, 100), (0, 200, 255, 80),
                    (0, 80, 220, 120), (0, 255, 255, 60), (50, 150, 255, 90)])
                cld.rectangle([px, py, px + psize - 1, py + psize - 1], fill=shade_c)
    for _ in range(4):
        ly = y + random.randint(int(-35 * s), int(30 * s))
        cld.line([(x - int(50 * s), ly), (x + int(50 * s), ly)], fill=(0, 220, 255, 80), width=1)
    for _ in range(15):
        sx3 = x + random.randint(int(-50 * s), int(50 * s))
        sy3 = y + random.randint(int(-40 * s), int(35 * s))
        cld.rectangle([sx3, sy3, sx3 + 2, sy3 + 2], fill=(0, 255, 255, 200))
    img = Image.alpha_composite(img, cl)
    draw = ImageDraw.Draw(img)

# ══════════════════════════════════════════════════════════════
# PLACE ALL DRAGONS
# ══════════════════════════════════════════════════════════════

dragons = [
    # Forest
    {"x": 100, "y": ground_y + 40, "body": (120, 85, 50), "wing": (160, 120, 60),
     "eye": (200, 160, 50), "name": "MudWing", "size": 0.8, "left": False, "belly": (170, 140, 90)},
    {"x": 260, "y": ground_y - 10, "body": (20, 160, 50), "wing": (60, 200, 70),
     "eye": (0, 120, 0), "name": "LeafWing", "size": 0.72, "left": True, "belly": (80, 200, 100)},
    {"x": 140, "y": ground_y + 120, "body": (230, 50, 40), "wing": (255, 130, 40),
     "eye": (255, 210, 0), "name": "SkyWing", "size": 0.75, "left": False, "belly": (255, 130, 100)},
    {"x": 350, "y": ground_y + 90, "body": (40, 190, 60), "wing": (255, 80, 180),
     "eye": (80, 255, 80), "name": "RainWing", "size": 0.72, "left": True, "belly": (100, 220, 120)},
    # River / Middle
    {"x": 550, "y": ground_y + 20, "body": (30, 100, 170), "wing": (50, 160, 210),
     "eye": (0, 180, 255), "name": "SeaWing", "size": 0.78, "left": False, "belly": (80, 160, 220)},
    {"x": 700, "y": ground_y - 20, "body": (200, 225, 250), "wing": (170, 210, 245),
     "eye": (80, 130, 255), "name": "IceWing", "size": 0.72, "left": True, "belly": (230, 240, 255)},
    {"x": 600, "y": ground_y + 110, "body": (35, 20, 70), "wing": (55, 25, 110),
     "eye": (120, 0, 220), "name": "NightWing", "size": 0.78, "left": False, "belly": (70, 50, 100)},
    {"x": 820, "y": ground_y + 60, "body": (200, 170, 225), "wing": (225, 195, 250),
     "eye": (160, 80, 220), "name": "SilkWing", "size": 0.7, "left": True, "belly": (230, 210, 245)},
    {"x": 890, "y": ground_y - 15, "body": (220, 170, 40), "wing": (210, 145, 15),
     "eye": (50, 50, 50), "name": "HiveWing", "size": 0.72, "left": False, "belly": (240, 210, 100)},
    # Desert
    {"x": 1550, "y": ground_y + 50, "body": (235, 210, 120), "wing": (245, 225, 140),
     "eye": (40, 40, 40), "name": "SandWing", "size": 0.82, "left": True, "belly": (250, 235, 170)},
    # Fan-made
    {"x": 440, "y": ground_y - 5, "body": (90, 0, 130), "wing": (150, 10, 210),
     "eye": (255, 0, 255), "name": "ErrorWing \u2605", "size": 0.8, "left": False,
     "belly": (120, 40, 160), "extras": errorwing_fx},
    # TwinWing: red+blue body mix
    {"x": 1000, "y": ground_y + 95, "body": (180, 50, 80), "wing": (80, 60, 200),
     "eye": (255, 200, 0), "name": "TwinWing \u2605", "size": 0.78, "left": True,
     "belly": (200, 100, 120), "extras": twinwing_fx},
    {"x": 750, "y": ground_y - 130, "body": (235, 238, 248), "wing": (215, 225, 245),
     "eye": (100, 160, 255), "name": "CloudWing \u2605", "size": 0.82, "left": False,
     "belly": (245, 248, 255), "extras": cloudwing_fx},
    {"x": pcx + 100, "y": pcy + 60, "body": (10, 70, 170), "wing": (0, 130, 240),
     "eye": (0, 255, 255), "name": "CyberWing \u2605", "size": 0.82, "left": True,
     "belly": (40, 110, 200), "extras": cyberwing_fx},
]

dragons.sort(key=lambda d: d["y"])
for d in dragons:
    draw_dragon_25d(
        d["x"], d["y"], body_col=d["body"], wing_col=d["wing"], eye_col=d["eye"],
        size=d.get("size", 0.75), facing_left=d.get("left", False),
        name=d.get("name", ""), extras=d.get("extras", None), belly_col=d.get("belly", None))

# Title
try:
    title_font = ImageFont.truetype("arial.ttf", 36)
    sub_font = ImageFont.truetype("arial.ttf", 18)
except:
    title_font = ImageFont.load_default()
    sub_font = ImageFont.load_default()

title = "Wings of Fire \u2014 All Tribes"
tw3 = draw.textlength(title, font=title_font)
draw.rounded_rectangle([W // 2 - tw3 // 2 - 16, 12, W // 2 + tw3 // 2 + 16, 54],
                        radius=12, fill=(15, 15, 25, 210), outline=(200, 180, 80))
draw.text((W // 2 - tw3 // 2, 14), title, fill=(255, 225, 60), font=title_font)

subtitle = "\u2605 = Fan-Made Tribes"
sw = draw.textlength(subtitle, font=sub_font)
draw.rounded_rectangle([W // 2 - sw // 2 - 12, 60, W // 2 + sw // 2 + 12, 82],
                        radius=8, fill=(15, 15, 25, 200))
draw.text((W // 2 - sw // 2, 62), subtitle, fill=(200, 150, 255), font=sub_font)

# Save
final = img.convert("RGB")
out_path = "wof_all_tribes.png"
final.save(out_path, "PNG")
print(f"Saved to {out_path} ({W}x{H})")
