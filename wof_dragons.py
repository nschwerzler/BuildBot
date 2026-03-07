"""
Wings of Fire — All Dragon Tribes (v4 — Slim 3D Dragons)
Properly proportioned slim dragons with strong 3D shading.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random, math

W, H = 1920, 1080
img = Image.new("RGBA", (W, H))
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

def shaded_oval(d, cx, cy, rx, ry, col, light_angle=135, strength=0.7, outline_c=None):
    """Draw an oval with directional 3D lighting. light_angle in degrees."""
    la = math.radians(light_angle)
    lx, ly = math.cos(la), -math.sin(la)  # light direction vector
    hi = shade(col, int(70 * strength))
    sh = shade(col, int(-55 * strength))
    mid = col
    for ring in range(max(rx, ry), 0, -1):
        frac = ring / max(rx, ry)
        srx, sry = int(rx * frac), int(ry * frac)
        # Sample position on the sphere for this ring
        # outer rings = edges = darker, inner = facing light = brighter
        if frac > 0.5:
            # Edge: blend base to shadow
            edge_t = (frac - 0.5) / 0.5
            c = lerp(mid, sh, edge_t * 0.8)
        else:
            # Inner: blend highlight to base
            inner_t = frac / 0.5
            c = lerp(hi, mid, inner_t)
        d.ellipse([cx - srx, cy - sry, cx + srx, cy + sry], fill=c)
    # Add a specular highlight spot offset toward light
    spec_x = cx + int(rx * 0.25 * lx)
    spec_y = cy + int(ry * 0.25 * ly)
    spec_r = max(2, int(min(rx, ry) * 0.22))
    for r in range(spec_r, 0, -1):
        a = int(60 * (1 - r / spec_r))
        spec_col = tuple(min(255, v + a) for v in hi)
        d.ellipse([spec_x - r, spec_y - r, spec_x + r, spec_y + r], fill=spec_col)
    if outline_c:
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=outline_c, width=2)

# ══════════════════════════════════════════════════════════════
# ENVIRONMENT
# ══════════════════════════════════════════════════════════════
ground_y = int(H * 0.50)

# Sky
grad_rect(0, 0, W, ground_y + 30, (105, 180, 255), (190, 220, 255))

# Mountains - back layer (light, distant)
def draw_mountain_range(peaks, base_y, col, snow_col=None):
    for cx, half_w, h in peaks:
        pts = [(cx - half_w, base_y)]
        for i in range(40):
            t = i / 39
            x = cx - half_w + 2 * half_w * t
            peak_h = h * math.sin(math.pi * t)
            jag = h * 0.06 * math.sin(t * 17) + h * 0.04 * math.cos(t * 23)
            pts.append((int(x), int(base_y - peak_h + jag)))
        pts.append((cx + half_w, base_y))
        draw.polygon(pts, fill=col)
        if snow_col:
            # Snow on top third
            sp = []
            for i in range(12, 28):
                t = i / 39
                x = cx - half_w + 2 * half_w * t
                peak_h = h * math.sin(math.pi * t)
                jag = h * 0.06 * math.sin(t * 17) + h * 0.04 * math.cos(t * 23)
                sp.append((int(x), int(base_y - peak_h + jag)))
            if len(sp) >= 3:
                sp.append((sp[-1][0], sp[-1][1] + int(h * 0.12)))
                sp.append((sp[0][0], sp[0][1] + int(h * 0.12)))
                draw.polygon(sp, fill=snow_col)

draw_mountain_range(
    [(120, 200, 190), (380, 240, 230), (650, 220, 210), (900, 270, 250),
     (1150, 230, 200), (1400, 260, 235), (1680, 210, 185), (1880, 180, 170)],
    ground_y + 8, (140, 155, 180), (195, 205, 220))

draw_mountain_range(
    [(250, 180, 140), (550, 200, 160), (850, 190, 150), (1250, 220, 170), (1550, 190, 145)],
    ground_y + 8, (110, 128, 158), (175, 188, 205))

# Ground zones
grad_rect(0, ground_y, int(W * 0.38), H, (52, 130, 42), (32, 88, 28))
grad_rect(int(W * 0.38), ground_y, int(W * 0.66), H, (62, 148, 48), (42, 108, 32))
grad_rect(int(W * 0.66), ground_y, W, H, (212, 188, 122), (182, 152, 92))

# Blends
for x in range(int(W * 0.34), int(W * 0.42)):
    t = (x - W * 0.34) / (W * 0.08)
    for y in range(ground_y, H):
        yt = (y - ground_y) / max(1, H - ground_y)
        c1 = lerp((52, 130, 42), (32, 88, 28), yt)
        c2 = lerp((62, 148, 48), (42, 108, 32), yt)
        draw.point((x, y), fill=lerp(c1, c2, t))
for x in range(int(W * 0.62), int(W * 0.70)):
    t = (x - W * 0.62) / (W * 0.08)
    for y in range(ground_y, H):
        yt = (y - ground_y) / max(1, H - ground_y)
        c1 = lerp((62, 148, 48), (42, 108, 32), yt)
        c2 = lerp((212, 188, 122), (182, 152, 92), yt)
        draw.point((x, y), fill=lerp(c1, c2, t))

# Sand dunes
for dcx, dcy, dw, dh in [(int(W * 0.76), ground_y + 50, 120, 25),
                           (int(W * 0.88), ground_y + 80, 100, 20),
                           (int(W * 0.72), ground_y + 115, 85, 16),
                           (int(W * 0.84), ground_y + 145, 70, 13)]:
    for dy in range(dh):
        t = dy / dh
        c = lerp((232, 212, 152), (198, 172, 118), t)
        hw = int(dw * math.sqrt(max(0, 1 - t * t)))
        draw.line([(dcx - hw, dcy - dh + dy), (dcx + hw, dcy - dh + dy)], fill=c)

# Cave
cave_cx, cave_cy = int(W * 0.22), ground_y + 5
cave_w, cave_h = 65, 45
# Arch
for a in range(0, 181):
    rad = math.radians(a)
    for thick in range(15):
        ax = cave_cx + int((cave_w + thick + 3) * math.cos(rad))
        ay = cave_cy - int((cave_h + thick + 3) * math.sin(rad))
        t = thick / 15
        rc = lerp((95, 85, 72), (55, 48, 38), t)
        draw.point((ax, ay), fill=rc)
# Dark inside
draw.ellipse([cave_cx - cave_w, cave_cy - cave_h, cave_cx + cave_w, cave_cy + cave_h // 2 + 30],
             fill=(18, 15, 10))
for r in range(min(cave_w, cave_h), 0, -3):
    t = r / min(cave_w, cave_h)
    c = lerp((18, 15, 10), (8, 5, 2), 1 - t)
    rx2 = int(cave_w * t)
    ry2 = int((cave_h // 2 + 30) * t)
    draw.ellipse([cave_cx - rx2, cave_cy - ry2, cave_cx + rx2, cave_cy + ry2], fill=c)
# Stalactites
random.seed(88)
for sx in range(-40, 45, 14):
    sh = random.randint(6, 16)
    draw.polygon([(cave_cx + sx - 2, cave_cy - cave_h + 8),
                   (cave_cx + sx + 2, cave_cy - cave_h + 8),
                   (cave_cx + sx, cave_cy - cave_h + 8 + sh)], fill=(55, 48, 38))

# River
rl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
rd = ImageDraw.Draw(rl)
for rx in range(int(W * 0.32), int(W * 0.70), 2):
    t = (rx - W * 0.32) / (W * 0.38)
    ry = ground_y + 180 + int(45 * math.sin(t * 3.5)) + int(t * 55)
    rw = 26
    for dy in range(-rw, rw + 1):
        dt = abs(dy) / rw
        c = lerp((85, 165, 242), (32, 78, 168), dt)
        a = int(215 * (1 - dt * 0.25))
        rd.point((rx, ry + dy), fill=c + (a,))
    # Specular
    if rx % 18 == 0:
        for sr in range(5, 0, -1):
            al = int(90 * (1 - sr / 5))
            rd.ellipse([rx - sr * 2, ry - sr, rx + sr * 2, ry + sr], fill=(200, 228, 255, al))
img = Image.alpha_composite(img, rl)
draw = ImageDraw.Draw(img)

# Trees
def draw_tree(cx, cy, sz, var=0):
    tw = max(2, int(sz * 0.18))
    th = int(sz * 0.9)
    for dx in range(-tw, tw + 1):
        t = (dx + tw) / max(1, 2 * tw)
        c = lerp((80 + var, 52 + var, 20), (52 + var, 32 + var, 10), t)
        draw.line([(cx + dx, cy + int(sz * 0.25)), (cx + dx, cy + th)], fill=c)
    for lx, ly, lr in [(0, -sz * 0.45, sz * 0.6), (-sz * 0.3, -sz * 0.15, sz * 0.48),
                        (sz * 0.28, -sz * 0.2, sz * 0.44), (0, -sz * 0.7, sz * 0.42)]:
        g = (28 + var, 115 + var * 2, 32 + var)
        shaded_oval(draw, cx + int(lx), cy + int(ly), int(lr), int(lr * 0.72), g, strength=0.8)

random.seed(42)
for _ in range(18):
    tx = random.randint(15, int(W * 0.32))
    ty = random.randint(ground_y + 8, ground_y + 85)
    draw_tree(tx, ty, random.randint(18, 38), random.randint(-6, 12))
for _ in range(4):
    tx = random.randint(int(W * 0.38), int(W * 0.50))
    ty = random.randint(ground_y + 20, ground_y + 55)
    draw_tree(tx, ty, random.randint(12, 22), random.randint(0, 15))

# Portal
pcx, pcy = int(W * 0.82), ground_y - 25
pl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
pd = ImageDraw.Draw(pl)
for r in range(88, 52, -1):
    a = int(50 * (88 - r) / 36)
    pd.ellipse([pcx - r, pcy - int(r * 1.45), pcx + r, pcy + int(r * 1.45)], fill=(115, 38, 195, a))
for r in range(55, 0, -1):
    t = r / 55
    c = lerp((215, 125, 250), (45, 0, 95), t)
    pd.ellipse([pcx - r, pcy - int(r * 1.42), pcx + r, pcy + int(r * 1.42)], fill=c + (232,))
random.seed(77)
for a in range(0, 700, 6):
    rad = math.radians(a)
    sr = 45 * (1 - a / 700)
    sx = pcx + int(sr * math.cos(rad * 2.3 + sr * 0.09))
    sy = pcy + int(sr * 1.38 * math.sin(rad * 2.3 + sr * 0.09))
    ps = max(1, int(2.5 * (1 - a / 700)))
    pd.ellipse([sx - ps, sy - ps, sx + ps, sy + ps], fill=(238, 188, 255, 135))
pd.ellipse([pcx - 58, pcy - 84, pcx + 58, pcy + 84], outline=(185, 105, 235, 215), width=4)
pd.ellipse([pcx - 62, pcy - 90, pcx + 62, pcy + 90], outline=(105, 42, 165, 155), width=3)
img = Image.alpha_composite(img, pl)
draw = ImageDraw.Draw(img)

# Sun
sl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(sl)
scx, scy = W - 135, 70
for r in range(70, 25, -1):
    a = int(40 * (70 - r) / 45)
    sd.ellipse([scx - r, scy - r, scx + r, scy + r], fill=(255, 238, 95, a))
shaded_oval(sd, scx, scy, 28, 28, (255, 242, 135), strength=0.4)
img = Image.alpha_composite(img, sl)
draw = ImageDraw.Draw(img)

# Clouds
cl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
cd = ImageDraw.Draw(cl)
for ccx, ccy, cw in [(180, 62, 62), (520, 42, 48), (920, 75, 58), (1360, 48, 45)]:
    for dx, dy, cr in [(-cw // 2, 3, cw // 2), (0, -cw // 5, cw // 2 + 3),
                        (cw // 2, 2, cw // 2 - 5), (cw // 4, cw // 6, cw // 3)]:
        for r in range(cr, 0, -1):
            a = int(165 * (1 - (r / cr) ** 2))
            cd.ellipse([ccx + dx - r, ccy + dy - r, ccx + dx + r, ccy + dy + r],
                       fill=(240, 244, 252, a))
img = Image.alpha_composite(img, cl)
draw = ImageDraw.Draw(img)

# ══════════════════════════════════════════════════════════════
# SLIM 3D DRAGON — proper elongated proportions
# ══════════════════════════════════════════════════════════════

def draw_dragon(x, y, body, wing, eye, sz=1.0, left=False, name="",
                belly=None, fx_func=None, split_body=None):
    """Slim, elongated 3D dragon with strong directional shading."""
    global img, draw
    s = sz
    f = -1 if left else 1
    if belly is None:
        belly = shade(body, 42)
    dark = shade(body, -45)
    light = shade(body, 55)

    # Shadow on ground
    sl2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sld = ImageDraw.Draw(sl2)
    sld.ellipse([x - int(55 * s), y + int(18 * s), x + int(55 * s), y + int(25 * s)],
                fill=(0, 0, 0, 35))
    img = Image.alpha_composite(img, sl2)
    draw = ImageDraw.Draw(img)

    # ── Tail — long sinuous curve ──
    for i in range(30):
        t = i / 29
        ttx = x - int(f * (35 + 85 * t) * s)
        tty = y + int((0 - 12 * t + 18 * math.sin(t * 5.5)) * s)
        thick = max(1, int((6 - 5 * t) * s))
        tc = lerp(body, dark, t * 0.6)
        # 3D: top lighter, bottom darker
        shaded_oval(draw, ttx, tty, thick, max(1, int(thick * 0.6)), tc, strength=0.6)
    # Tail fin
    tp_x = x - int(f * 120 * s)
    tp_y = y + int(5 * s)
    draw.polygon([(tp_x, tp_y - int(7 * s)), (tp_x - int(f * 10 * s), tp_y),
                   (tp_x, tp_y + int(5 * s))], fill=wing, outline=(30, 30, 30), width=1)

    # ── Wing (behind body) ──
    wl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wl)
    wx, wy = x - int(f * 5 * s), y - int(14 * s)
    # Bigger, more dramatic wing shape
    pts = [
        (wx, wy),
        (wx - int(f * 45 * s), wy - int(62 * s)),
        (wx - int(f * 25 * s), wy - int(35 * s)),
        (wx - int(f * 65 * s), wy - int(48 * s)),
        (wx - int(f * 35 * s), wy - int(20 * s)),
        (wx - int(f * 72 * s), wy - int(25 * s)),
        (wx - int(f * 42 * s), wy + int(8 * s)),
        (wx, wy + int(4 * s)),
    ]
    # Wing membrane with gradient fill
    wd.polygon(pts, fill=wing + (180,), outline=(28, 28, 28, 195), width=2)
    # Wing bones
    bone = shade(wing, -30) + (195,)
    for bi in [1, 3, 5]:
        wd.line([(wx, wy), pts[bi]], fill=bone, width=max(1, int(2.5 * s)))
    # Light streaks on membrane
    for i in range(3):
        mx = (wx + pts[1 + i * 2][0]) // 2
        my = (wy + pts[1 + i * 2][1]) // 2
        wd.ellipse([mx - int(6 * s), my - int(4 * s), mx + int(6 * s), my + int(4 * s)],
                   fill=shade(wing, 25) + (50,))
    img = Image.alpha_composite(img, wl)
    draw = ImageDraw.Draw(img)

    # ── Hind legs (slim) ──
    hlx = x + int(f * 5 * s)
    hly = y + int(8 * s)
    # Thigh
    shaded_oval(draw, hlx, hly, int(5 * s), int(9 * s), shade(body, -12), strength=0.7,
                outline_c=(35, 35, 35))
    # Shin
    shaded_oval(draw, hlx - int(f * 1 * s), hly + int(13 * s), int(3.5 * s), int(5 * s),
                shade(body, -18), strength=0.6)
    # Claws
    for cl in [-2, 0, 2]:
        draw.ellipse([hlx + int(cl * s) - 1, hly + int(16 * s),
                      hlx + int(cl * s) + 2, hly + int(19 * s)], fill=(45, 45, 45))

    # ── Body — ELONGATED oval (wide, not tall) ──
    bw = int(40 * s)  # wide
    bh = int(15 * s)  # slim!  ratio ~2.7:1

    if split_body:
        # TwinWing: red/blue split
        c1, c2 = split_body
        bl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bd = ImageDraw.Draw(bl)
        # Left half
        for ring in range(max(bw, bh), 0, -1):
            frac = ring / max(bw, bh)
            srx, sry = int(bw * frac), int(bh * frac)
            # Two halves with gradient between
            for dx in range(-srx, srx + 1):
                blend = (dx + srx) / max(1, 2 * srx)  # 0=left, 1=right
                base = lerp(c1, c2, blend)
                if frac > 0.5:
                    c = lerp(base, shade(base, -40), (frac - 0.5) / 0.5 * 0.7)
                else:
                    c = lerp(shade(base, 50), base, frac / 0.5)
                dy_max = sry * math.sqrt(max(0, 1 - (dx / max(1, srx)) ** 2))
                for dy in [int(-dy_max), int(-dy_max * 0.5), 0, int(dy_max * 0.5), int(dy_max)]:
                    bd.point((x + dx, y + dy), fill=c + (255,))
        bd.ellipse([x - bw, y - bh, x + bw, y + bh], outline=(35, 35, 35, 200), width=2)
        img = Image.alpha_composite(img, bl)
        draw = ImageDraw.Draw(img)
    else:
        shaded_oval(draw, x, y, bw, bh, body, strength=0.75, outline_c=(35, 35, 35))

    # Belly highlight stripe
    shaded_oval(draw, x + int(f * 3 * s), y + int(4 * s), int(25 * s), int(7 * s),
                belly, strength=0.5)

    # ── Front legs ──
    flx = x + int(f * 22 * s)
    fly = y + int(7 * s)
    shaded_oval(draw, flx, fly, int(4.5 * s), int(8.5 * s), body, strength=0.7,
                outline_c=(35, 35, 35))
    shaded_oval(draw, flx + int(f * 1.5 * s), fly + int(12 * s), int(3 * s), int(4 * s),
                shade(body, -8), strength=0.6)
    for cl in [-2, 0, 2]:
        draw.ellipse([flx + int(f * 1.5 * s) + int(cl * s) - 1, fly + int(14 * s),
                      flx + int(f * 1.5 * s) + int(cl * s) + 2, fly + int(17 * s)], fill=(45, 45, 45))

    # ── Neck — long, curved, slender ──
    for ni in range(18):
        t = ni / 17
        # S-curve neck
        nx = x + int(f * (18 + 35 * t) * s)
        ny = y - int((10 + 30 * t + 5 * math.sin(t * 2.5)) * s)
        nr = max(2, int((9 - 4.5 * t) * s))
        nc = lerp(body, shade(body, -5), t * 0.3)
        shaded_oval(draw, nx, ny, nr, int(nr * 0.65), nc, strength=0.7)

    # ── Head — elongated, angular ──
    hx = x + int(f * 58 * s)
    hy = y - int(48 * s)
    # Main head
    shaded_oval(draw, hx, hy, int(14 * s), int(10 * s), body, strength=0.8,
                outline_c=(32, 32, 32))
    # Snout — long, thin, tapered
    snx = hx + int(f * 22 * s)
    sny = hy + int(2 * s)
    shaded_oval(draw, snx, sny, int(14 * s), int(5.5 * s), shade(body, 8), strength=0.7,
                outline_c=(32, 32, 32))
    # Nostrils
    for no in [5, 10]:
        draw.ellipse([snx + int(f * no * s) - 1, sny - 1, snx + int(f * no * s) + 2, sny + 2],
                     fill=(22, 22, 22))
    # Jaw line
    jaw_x1 = min(hx, hx + int(f * 28 * s))
    jaw_x2 = max(hx, hx + int(f * 28 * s))
    if jaw_x2 > jaw_x1 + 2:
        draw.arc([jaw_x1, hy + int(3 * s), jaw_x2, hy + int(11 * s)],
                 10 if not left else 150, 170 if not left else 350, fill=(38, 38, 38), width=1)

    # Eye — slit pupil, 3D iris
    ex, ey = hx + int(f * 5 * s), hy - int(3 * s)
    er = int(4.5 * s)
    # Eyeball
    shaded_oval(draw, ex, ey, er, int(er * 0.85), (248, 248, 252), strength=0.3,
                outline_c=(28, 28, 28))
    # Iris gradient
    ir = int(3 * s)
    for r in range(ir, 0, -1):
        t = r / ir
        draw.ellipse([ex - r, ey - r, ex + r, ey + r],
                     fill=lerp(shade(eye, 35), shade(eye, -28), t))
    # Slit pupil
    draw.line([(ex, ey - int(2.5 * s)), (ex, ey + int(2.5 * s))], fill=(5, 5, 5), width=max(1, int(1.5 * s)))
    # Specular
    draw.ellipse([ex - int(1.5 * s), ey - int(2.5 * s), ex - int(0.3 * s), ey - int(1 * s)],
                 fill=(255, 255, 255))

    # ── Horns — swept back, 3D gradient ──
    for ho in [-5, 4]:
        hbx = hx + int(ho * s * f * 0.35)
        hby = hy - int(8 * s)
        tip_x = hbx - int(f * 10 * s)
        tip_y = hby - int(18 * s)
        for hi in range(int(20 * s)):
            t = hi / (20 * s)
            hc = lerp((218, 202, 148), (135, 118, 65), t)
            hw = max(0, int(3.2 * s * (1 - t)))
            hy2 = hby - hi
            hx2 = int(hbx + (tip_x - hbx) * t)
            if hw > 0:
                draw.line([(hx2 - hw, hy2), (hx2 + hw, hy2)], fill=hc)

    # ── Spines along back ──
    for si in range(8):
        t = si / 7
        sp_x = x + int(f * (-20 + 10 * t) * s)
        sp_y = y - int((13 + 4 * math.sin(t * 3.5)) * s)
        sp_h = int((8 + 5 * (1 - t)) * s)
        spine_col = shade(wing, -12)
        draw.polygon([(sp_x - int(1 * s), sp_y), (sp_x + int(1 * s), sp_y),
                       (sp_x, sp_y - sp_h)], fill=spine_col, outline=(42, 42, 42))

    # ── Label ──
    if name:
        try:
            font = ImageFont.truetype("arial.ttf", max(12, int(13 * s)))
        except:
            font = ImageFont.load_default()
        tl = draw.textlength(name, font=font)
        ly = y + int(24 * s)
        draw.rounded_rectangle([x - tl // 2 - 5, ly - 1, x + tl // 2 + 5, ly + 16],
                                radius=7, fill=(12, 12, 18, 205), outline=(85, 85, 105))
        draw.text((x - tl // 2, ly), name, fill=(255, 255, 255), font=font)

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
        gx = x + random.randint(int(-58 * s), int(58 * s))
        gy = y + random.randint(int(-48 * s), int(38 * s))
        gw = random.randint(3, int(11 * s))
        gh = random.randint(1, int(3 * s))
        c = random.choice([(178, 0, 255, 145), (118, 0, 198, 125),
                            (0, 0, 0, 165), (218, 58, 255, 105), (48, 0, 78, 135)])
        fd.rectangle([gx, gy, gx + gw, gy + gh], fill=c)
    for _ in range(7):
        gy = y + random.randint(int(-38 * s), int(28 * s))
        gw = random.randint(12, int(52 * s))
        gx = x + random.randint(int(-32 * s), int(18 * s))
        fd.rectangle([gx, gy, gx + gw, gy + 2],
                     fill=random.choice([(198, 0, 255, 88), (0, 0, 0, 108)]))
    img = Image.alpha_composite(img, fl)
    draw = ImageDraw.Draw(img)

def twinwing_fx(x, y, s, f, hx, hy):
    global img, draw
    ol = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ol)
    orbs = [((255, 25, 25), x - int(35 * s), y - int(42 * s)),
            ((25, 65, 255), x + int(35 * s), y - int(42 * s))]
    for oc, ox, oy in orbs:
        for r in range(int(18 * s), int(9 * s), -1):
            a = int(48 * (int(18 * s) - r) / (9 * s))
            od.ellipse([ox - r, oy - r, ox + r, oy + r], fill=oc + (a,))
        for r in range(int(9 * s), 0, -1):
            t = r / (9 * s)
            c = lerp((255, 255, 255), oc, t)
            od.ellipse([ox - r, oy - r, ox + r, oy + r], fill=c + (218,))
        od.ellipse([ox - int(2.5 * s), oy - int(3.5 * s), ox - int(0.5 * s), oy - int(1 * s)],
                   fill=(255, 255, 255, 195))
    img = Image.alpha_composite(img, ol)
    draw = ImageDraw.Draw(img)

def cloudwing_fx(x, y, s, f, hx, hy):
    global img, draw
    cl2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cld = ImageDraw.Draw(cl2)
    random.seed(int(x * 5 + y))
    for _ in range(22):
        cx2 = x + random.randint(int(-52 * s), int(52 * s))
        cy2 = y + random.randint(int(-38 * s), int(28 * s))
        cr = random.randint(int(6 * s), int(16 * s))
        for r in range(cr, 0, -1):
            a = int(75 * (1 - (r / cr) ** 2))
            sv = random.randint(232, 248)
            cld.ellipse([cx2 - r, cy2 - r, cx2 + r, cy2 + int(r * 0.7)], fill=(sv, sv, sv + 4, a))
    img = Image.alpha_composite(img, cl2)
    draw = ImageDraw.Draw(img)

def cyberwing_fx(x, y, s, f, hx, hy):
    global img, draw
    cl2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cld = ImageDraw.Draw(cl2)
    random.seed(int(x + y * 7))
    ps = max(3, int(4 * s))
    for px in range(x - int(48 * s), x + int(48 * s), ps):
        for py in range(y - int(38 * s), y + int(32 * s), ps):
            if random.random() < 0.2:
                sc = random.choice([(0, 118, 255, 85), (0, 198, 255, 65),
                                     (0, 78, 218, 105), (0, 255, 255, 48)])
                cld.rectangle([px, py, px + ps - 1, py + ps - 1], fill=sc)
    for _ in range(4):
        ly = y + random.randint(int(-28 * s), int(22 * s))
        cld.line([(x - int(42 * s), ly), (x + int(42 * s), ly)], fill=(0, 218, 255, 65), width=1)
    img = Image.alpha_composite(img, cl2)
    draw = ImageDraw.Draw(img)


# ══════════════════════════════════════════════════════════════
# LAYOUT — Spread evenly, no overlapping
# ══════════════════════════════════════════════════════════════

dragons = [
    # ── FOREST (x 60–350) ──
    {"x": 70, "y": ground_y + 55, "body": (118, 82, 48), "wing": (152, 112, 52),
     "eye": (188, 152, 42), "name": "MudWing", "sz": 0.82, "left": False, "belly": (162, 132, 82)},

    {"x": 240, "y": ground_y + 20, "body": (12, 152, 42), "wing": (52, 192, 62),
     "eye": (0, 112, 0), "name": "LeafWing", "sz": 0.74, "left": True, "belly": (72, 192, 92)},

    # SkyWing — moved to grassland, clearly visible
    {"x": 500, "y": ground_y + 45, "body": (222, 42, 32), "wing": (248, 122, 32),
     "eye": (248, 202, 0), "name": "SkyWing", "sz": 0.78, "left": False, "belly": (248, 122, 92)},

    {"x": 380, "y": ground_y + 95, "body": (32, 182, 52), "wing": (248, 72, 172),
     "eye": (72, 248, 72), "name": "RainWing", "sz": 0.74, "left": True, "belly": (92, 212, 112)},

    # ── CAVE (NightWing clearly visible, just outside) ──
    {"x": cave_cx + 95, "y": cave_cy + 35, "body": (28, 15, 62), "wing": (48, 20, 102),
     "eye": (112, 0, 212), "name": "NightWing", "sz": 0.82, "left": True, "belly": (62, 42, 92)},

    # ErrorWing near cave too
    {"x": cave_cx - 80, "y": cave_cy + 40, "body": (82, 0, 122), "wing": (142, 2, 202),
     "eye": (255, 0, 255), "name": "ErrorWing \u2605", "sz": 0.8, "left": False,
     "belly": (112, 32, 152), "fx": errorwing_fx},

    # ── RIVER / GRASSLAND (x 600–950) ──
    {"x": 650, "y": ground_y + 15, "body": (22, 92, 162), "wing": (42, 152, 202),
     "eye": (0, 172, 248), "name": "SeaWing", "sz": 0.8, "left": True, "belly": (72, 152, 212)},

    {"x": 800, "y": ground_y - 10, "body": (192, 218, 242), "wing": (162, 202, 238),
     "eye": (72, 122, 248), "name": "IceWing", "sz": 0.76, "left": False, "belly": (222, 232, 248)},

    {"x": 760, "y": ground_y + 85, "body": (192, 162, 218), "wing": (218, 188, 242),
     "eye": (152, 72, 212), "name": "SilkWing", "sz": 0.72, "left": True, "belly": (222, 202, 238)},

    {"x": 950, "y": ground_y + 25, "body": (212, 162, 32), "wing": (202, 138, 8),
     "eye": (42, 42, 42), "name": "HiveWing", "sz": 0.76, "left": False, "belly": (232, 202, 92)},

    # ── GRASSLAND/DESERT EDGE (x 1050–1200) ──
    # TwinWing with red/blue split
    {"x": 1100, "y": ground_y + 55, "body": (158, 38, 58), "wing": (118, 58, 178),
     "eye": (248, 192, 0), "name": "TwinWing \u2605", "sz": 0.82, "left": True,
     "belly": (178, 78, 98), "fx": twinwing_fx,
     "split": ((225, 35, 35), (35, 55, 225))},

    # CloudWing floating above
    {"x": 850, "y": ground_y - 115, "body": (230, 232, 242), "wing": (208, 218, 240),
     "eye": (92, 152, 248), "name": "CloudWing \u2605", "sz": 0.85, "left": False,
     "belly": (240, 242, 250), "fx": cloudwing_fx},

    # ── DESERT (x 1400–1700) far apart ──
    {"x": 1700, "y": ground_y + 65, "body": (228, 202, 112), "wing": (238, 218, 132),
     "eye": (32, 32, 32), "name": "SandWing", "sz": 0.85, "left": True, "belly": (242, 228, 162)},

    # CyberWing right at the portal
    {"x": pcx, "y": pcy + 85, "body": (2, 62, 162), "wing": (0, 122, 232),
     "eye": (0, 248, 248), "name": "CyberWing \u2605", "sz": 0.82, "left": False,
     "belly": (32, 102, 192), "fx": cyberwing_fx},
]

# Depth sort
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
tl2 = draw.textlength(title, font=tf)
draw.rounded_rectangle([W // 2 - tl2 // 2 - 14, 14, W // 2 + tl2 // 2 + 14, 52],
                        radius=10, fill=(10, 10, 20, 218), outline=(198, 172, 72))
draw.text((W // 2 - tl2 // 2, 16), title, fill=(255, 218, 52), font=tf)

sub = "\u2605 = Fan-Made Tribes"
sl3 = draw.textlength(sub, font=sf)
draw.rounded_rectangle([W // 2 - sl3 // 2 - 10, 58, W // 2 + sl3 // 2 + 10, 78],
                        radius=7, fill=(10, 10, 20, 198))
draw.text((W // 2 - sl3 // 2, 60), sub, fill=(192, 142, 248), font=sf)

# Save
final = img.convert("RGB")
final.save("wof_all_tribes.png", "PNG")
print(f"Saved wof_all_tribes.png ({W}x{H})")
