"""
Wings of Fire - All Dragon Tribes Art Generator
Draws a cartoony scene with forest, river, desert, portal,
and all canon + fan-made dragon tribes.
"""
from PIL import Image, ImageDraw, ImageFont
import random, math

W, H = 1600, 900
img = Image.new("RGB", (W, H))
draw = ImageDraw.Draw(img)

# ── BACKGROUND ──────────────────────────────────────────────
# Sky gradient
for y in range(H // 2):
    r = int(100 + 80 * y / (H // 2))
    g = int(180 + 60 * y / (H // 2))
    b = int(255 - 30 * y / (H // 2))
    draw.line([(0, y), (W, y)], fill=(r, g, b))

# Ground base
draw.rectangle([0, H // 2, W, H], fill=(80, 160, 60))

# ── DESERT (right side) ────────────────────────────────────
for y in range(H // 2, H):
    t = (y - H // 2) / (H // 2)
    sand_r = int(220 - 30 * t)
    sand_g = int(190 - 40 * t)
    sand_b = int(120 - 30 * t)
    draw.line([(W * 3 // 4, y), (W, y)], fill=(sand_r, sand_g, sand_b))
# Sand dunes
for dx in range(0, W // 4, 60):
    cx = W * 3 // 4 + dx + 30
    cy = H // 2 + 80
    for a in range(180):
        rad = math.radians(a)
        x1 = cx + int(40 * math.cos(rad))
        y1 = cy - int(15 * math.sin(rad))
        draw.point((x1, y1), fill=(210, 185, 110))
    draw.arc([cx - 40, cy - 15, cx + 40, cy + 15], 180, 360, fill=(200, 175, 100), width=2)

# ── FOREST (left side) ─────────────────────────────────────
def draw_tree(cx, cy, size, shade=0):
    trunk_w = size // 4
    trunk_h = size
    draw.rectangle([cx - trunk_w, cy, cx + trunk_w, cy + trunk_h], fill=(100 + shade, 70 + shade, 30))
    for i in range(3):
        r = size - i * (size // 4)
        ty = cy - i * (size // 3)
        draw.polygon([(cx - r, ty + size // 3), (cx + r, ty + size // 3), (cx, ty - size // 2)],
                      fill=(30 + shade, 120 + shade * 2, 40 + shade))

random.seed(42)
for _ in range(18):
    tx = random.randint(20, W // 3)
    ty = random.randint(H // 2 - 30, H // 2 + 60)
    ts = random.randint(25, 55)
    draw_tree(tx, ty, ts, random.randint(0, 30))

# ── RIVER (middle) ─────────────────────────────────────────
river_pts = []
for x in range(W // 3, W * 3 // 4 + 1, 5):
    y_off = int(30 * math.sin((x - W // 3) * 0.012))
    river_pts.append((x, H // 2 + 100 + y_off))
# Draw thick river
for pt in river_pts:
    draw.ellipse([pt[0] - 25, pt[1] - 8, pt[0] + 25, pt[1] + 8], fill=(60, 140, 220))
# River highlights
for i, pt in enumerate(river_pts):
    if i % 8 == 0:
        draw.ellipse([pt[0] - 6, pt[1] - 2, pt[0] + 6, pt[1] + 2], fill=(120, 200, 255))

# ── PORTAL (right-center) ──────────────────────────────────
portal_cx, portal_cy = W * 3 // 4 - 60, H // 2 - 30
for r in range(60, 0, -2):
    intensity = (60 - r) / 60
    pr = int(80 + 175 * intensity)
    pg = int(0 + 50 * intensity)
    pb = int(180 + 75 * intensity)
    draw.ellipse([portal_cx - r, portal_cy - int(r * 1.4),
                  portal_cx + r, portal_cy + int(r * 1.4)], fill=(pr, pg, pb))
# Portal swirl
for a in range(0, 360, 15):
    rad = math.radians(a)
    for sr in range(10, 50, 4):
        sx = portal_cx + int(sr * math.cos(rad + sr * 0.05))
        sy = portal_cy + int(sr * 1.3 * math.sin(rad + sr * 0.05))
        draw.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(200, 100, 255, 180))
# Portal frame
draw.ellipse([portal_cx - 62, portal_cy - 87, portal_cx + 62, portal_cy + 87], outline=(160, 80, 200), width=4)
draw.ellipse([portal_cx - 65, portal_cy - 91, portal_cx + 65, portal_cy + 91], outline=(100, 30, 160), width=2)

# ── SUN ────────────────────────────────────────────────────
draw.ellipse([W - 140, 20, W - 60, 100], fill=(255, 240, 80))
for a in range(0, 360, 30):
    rad = math.radians(a)
    sx = W - 100 + int(55 * math.cos(rad))
    sy = 60 + int(55 * math.sin(rad))
    draw.line([(W - 100 + int(42 * math.cos(rad)), 60 + int(42 * math.sin(rad))),
               (sx, sy)], fill=(255, 230, 50), width=2)

# ── CLOUDS ─────────────────────────────────────────────────
def draw_cloud(cx, cy, w):
    for dx, dy, r in [(-w//3, 0, w//3), (0, -w//6, w//3), (w//3, 0, w//3), (0, w//8, w//4)]:
        draw.ellipse([cx + dx - r, cy + dy - r, cx + dx + r, cy + dy + r], fill=(240, 245, 255))

draw_cloud(200, 60, 60)
draw_cloud(500, 40, 50)
draw_cloud(900, 70, 55)

# ══════════════════════════════════════════════════════════════
# DRAGON DRAWING FUNCTIONS
# ══════════════════════════════════════════════════════════════

def draw_cartoon_dragon(x, y, body_color, wing_color, eye_color, size=1.0, 
                         facing_left=False, name="", extras=None):
    """Draw a cute cartoony dragon at (x,y) with given colors."""
    s = size
    fx = -1 if facing_left else 1

    # Body
    bw, bh = int(50 * s), int(30 * s)
    draw.ellipse([x - bw, y - bh, x + bw, y + bh], fill=body_color, outline=(0, 0, 0), width=2)

    # Neck + Head
    hx = x + int(fx * 45 * s)
    hy = y - int(30 * s)
    # neck
    draw.line([(x + int(fx * 20 * s), y - int(15 * s)), (hx, hy + int(10 * s))],
              fill=body_color, width=int(14 * s))
    draw.line([(x + int(fx * 20 * s), y - int(15 * s)), (hx, hy + int(10 * s))],
              fill=(0, 0, 0), width=int(16 * s))
    draw.line([(x + int(fx * 20 * s), y - int(15 * s)), (hx, hy + int(10 * s))],
              fill=body_color, width=int(12 * s))
    # head
    hr = int(18 * s)
    draw.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=body_color, outline=(0, 0, 0), width=2)
    # snout
    sx = hx + int(fx * 16 * s)
    draw.ellipse([sx - int(10 * s), hy - int(6 * s), sx + int(10 * s), hy + int(8 * s)],
                 fill=body_color, outline=(0, 0, 0), width=2)
    # nostril
    draw.ellipse([sx + int(fx * 4 * s) - 2, hy - 2, sx + int(fx * 4 * s) + 2, hy + 2], fill=(0, 0, 0))
    # eye
    ex = hx + int(fx * 5 * s)
    ey = hy - int(5 * s)
    draw.ellipse([ex - int(5 * s), ey - int(5 * s), ex + int(5 * s), ey + int(5 * s)],
                 fill=(255, 255, 255), outline=(0, 0, 0), width=1)
    draw.ellipse([ex - int(3 * s), ey - int(3 * s), ex + int(3 * s), ey + int(3 * s)], fill=eye_color)
    draw.ellipse([ex - int(1 * s), ey - int(3 * s), ex + int(1 * s), ey - int(1 * s)], fill=(255, 255, 255))

    # Horns
    for hoff in [-6, 0]:
        horn_x = hx + int(fx * hoff * s)
        horn_y = hy - hr
        draw.polygon([(horn_x - int(3 * s), horn_y),
                       (horn_x + int(3 * s), horn_y),
                       (horn_x, horn_y - int(14 * s))],
                      fill=(200, 180, 120), outline=(0, 0, 0), width=1)

    # Wings
    wx = x - int(fx * 5 * s)
    wy = y - int(25 * s)
    wing_pts = [
        (wx, wy),
        (wx - int(fx * 30 * s), wy - int(40 * s)),
        (wx - int(fx * 15 * s), wy - int(20 * s)),
        (wx - int(fx * 45 * s), wy - int(30 * s)),
        (wx - int(fx * 25 * s), wy - int(10 * s)),
        (wx - int(fx * 50 * s), wy - int(15 * s)),
        (wx - int(fx * 30 * s), wy + int(10 * s)),
        (wx, wy + int(5 * s)),
    ]
    draw.polygon(wing_pts, fill=wing_color, outline=(0, 0, 0), width=2)
    # wing membrane lines
    draw.line([(wx, wy), (wx - int(fx * 30 * s), wy - int(40 * s))], fill=(0, 0, 0), width=1)
    draw.line([(wx, wy), (wx - int(fx * 45 * s), wy - int(30 * s))], fill=(0, 0, 0), width=1)

    # Legs
    for lx_off in [-18, 18]:
        lx = x + int(lx_off * s)
        ly = y + int(bh * 0.7)
        draw.rectangle([lx - int(6 * s), ly, lx + int(6 * s), ly + int(20 * s)],
                       fill=body_color, outline=(0, 0, 0), width=2)
        # claws
        for c in [-4, 0, 4]:
            draw.ellipse([lx + int(c * s) - 2, ly + int(20 * s) - 1,
                          lx + int(c * s) + 2, ly + int(20 * s) + 3], fill=(60, 60, 60))

    # Tail
    tx1 = x - int(fx * bw)
    ty1 = y + int(5 * s)
    tx2 = x - int(fx * (bw + 35) * s)
    ty2 = y - int(5 * s)
    tx3 = x - int(fx * (bw + 45) * s)
    ty3 = y - int(15 * s)
    draw.line([(tx1, ty1), (tx2, ty2), (tx3, ty3)], fill=body_color, width=int(8 * s))
    draw.line([(tx1, ty1), (tx2, ty2), (tx3, ty3)], fill=(0, 0, 0), width=int(10 * s))
    draw.line([(tx1, ty1), (tx2, ty2), (tx3, ty3)], fill=body_color, width=int(6 * s))
    # tail tip
    draw.polygon([(tx3 - int(fx * 5 * s), ty3 - int(8 * s)),
                   (tx3 + int(fx * 3 * s), ty3),
                   (tx3 - int(fx * 5 * s), ty3 + int(5 * s))],
                  fill=wing_color, outline=(0, 0, 0), width=1)

    # Belly stripe
    draw.ellipse([x - int(30 * s), y - int(15 * s), x + int(30 * s), y + int(20 * s)],
                 fill=tuple(min(c + 40, 255) for c in body_color[:3]))

    # Name label
    if name:
        try:
            font = ImageFont.truetype("arial.ttf", max(12, int(13 * s)))
        except:
            font = ImageFont.load_default()
        tw = draw.textlength(name, font=font)
        draw.rectangle([x - tw // 2 - 4, y + int(bh + 22 * s),
                        x + tw // 2 + 4, y + int(bh + 38 * s)], fill=(0, 0, 0, 180))
        draw.text((x - tw // 2, y + int(bh + 22 * s)), name, fill=(255, 255, 255), font=font)

    # Extras
    if extras:
        extras(draw, x, y, s, fx, hx, hy)


# ══════════════════════════════════════════════════════════════
# SPECIAL EFFECT FUNCTIONS FOR FAN-MADE DRAGONS
# ══════════════════════════════════════════════════════════════

def errorwing_fx(draw, x, y, s, fx, hx, hy):
    """Glitch particles - purple and black static"""
    random.seed(x + y)
    for _ in range(60):
        gx = x + random.randint(int(-60 * s), int(60 * s))
        gy = y + random.randint(int(-50 * s), int(40 * s))
        gs = random.randint(2, int(6 * s))
        color = random.choice([(180, 0, 255), (100, 0, 180), (0, 0, 0), (200, 50, 255), (60, 0, 100)])
        draw.rectangle([gx, gy, gx + gs, gy + gs // 2], fill=color)
    # Glitch lines
    for _ in range(8):
        gy = y + random.randint(int(-40 * s), int(30 * s))
        gw = random.randint(10, int(40 * s))
        gx = x + random.randint(int(-30 * s), int(30 * s))
        draw.rectangle([gx, gy, gx + gw, gy + 2], fill=random.choice([(180, 0, 255), (0, 0, 0)]))

def twinwing_fx(draw, x, y, s, fx, hx, hy):
    """Two floating orbs - red and blue"""
    for orb_color, ox, oy in [((255, 50, 50), x - int(35 * s), y - int(45 * s)),
                                ((50, 100, 255), x + int(35 * s), y - int(45 * s))]:
        for r in range(int(14 * s), 0, -1):
            alpha_factor = r / (14 * s)
            c = tuple(int(oc * (1 - alpha_factor) + 255 * alpha_factor) for oc in orb_color)
            draw.ellipse([ox - r, oy - r, ox + r, oy + r], fill=c)
        # Glow
        for r in range(int(18 * s), int(14 * s), -1):
            gc = tuple(min(255, oc + 100) for oc in orb_color)
            draw.ellipse([ox - r, oy - r, ox + r, oy + r], outline=gc)

def cloudwing_fx(draw, x, y, s, fx, hx, hy):
    """Cloud puffs around the dragon"""
    random.seed(x * 3 + y)
    for _ in range(20):
        cx = x + random.randint(int(-55 * s), int(55 * s))
        cy = y + random.randint(int(-40 * s), int(35 * s))
        cr = random.randint(int(6 * s), int(16 * s))
        shade = random.randint(220, 250)
        draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(shade, shade, shade + 5))

def cyberwing_fx(draw, x, y, s, fx, hx, hy):
    """Pixelated effect - draw pixel grid over the dragon"""
    random.seed(x + y * 2)
    psize = int(5 * s)
    for px in range(x - int(50 * s), x + int(50 * s), psize):
        for py in range(y - int(40 * s), y + int(40 * s), psize):
            if random.random() < 0.3:
                shade = random.choice([(0, 100, 255), (0, 180, 255), (0, 60, 200), (0, 220, 255)])
                draw.rectangle([px, py, px + psize - 1, py + psize - 1], fill=shade)
    # Digital lines
    for _ in range(5):
        ly = y + random.randint(int(-30 * s), int(25 * s))
        draw.line([(x - int(45 * s), ly), (x + int(45 * s), ly)], fill=(0, 200, 255), width=1)


# ══════════════════════════════════════════════════════════════
# PLACE ALL DRAGONS
# ══════════════════════════════════════════════════════════════

dragons = [
    # FOREST DRAGONS (left area)
    {"x": 80, "y": 380, "body": (100, 70, 40), "wing": (140, 100, 50), "eye": (180, 140, 40),
     "name": "MudWing", "size": 0.75, "left": False},
    {"x": 200, "y": 340, "body": (0, 180, 50), "wing": (50, 220, 80), "eye": (0, 100, 0),
     "name": "LeafWing", "size": 0.72, "left": True},
    {"x": 120, "y": 500, "body": (255, 50, 50), "wing": (255, 120, 30), "eye": (255, 200, 0),
     "name": "SkyWing", "size": 0.7, "left": False},
    {"x": 280, "y": 470, "body": (50, 200, 50), "wing": (255, 100, 200), "eye": (100, 255, 100),
     "name": "RainWing", "size": 0.72, "left": True},

    # RIVER DRAGONS (middle area near water)
    {"x": 480, "y": 400, "body": (30, 120, 180), "wing": (60, 180, 220), "eye": (0, 200, 255),
     "name": "SeaWing", "size": 0.75, "left": False},
    {"x": 600, "y": 360, "body": (200, 230, 255), "wing": (160, 210, 255), "eye": (100, 150, 255),
     "name": "IceWing", "size": 0.7, "left": True},
    {"x": 520, "y": 510, "body": (40, 20, 80), "wing": (60, 30, 120), "eye": (100, 0, 200),
     "name": "NightWing", "size": 0.75, "left": False},
    {"x": 700, "y": 440, "body": (200, 170, 230), "wing": (230, 200, 255), "eye": (140, 80, 200),
     "name": "SilkWing", "size": 0.68, "left": True},
    {"x": 750, "y": 350, "body": (220, 160, 30), "wing": (200, 130, 0), "eye": (50, 50, 50),
     "name": "HiveWing", "size": 0.7, "left": False},

    # DESERT DRAGONS (right area)
    {"x": 1300, "y": 420, "body": (230, 200, 100), "wing": (240, 220, 130), "eye": (0, 0, 0),
     "name": "SandWing", "size": 0.78, "left": True},

    # FAN-MADE: ErrorWing (forest edge - glitchy)
    {"x": 350, "y": 350, "body": (80, 0, 120), "wing": (140, 0, 200), "eye": (255, 0, 255),
     "name": "ErrorWing ★", "size": 0.78, "left": False, "extras": errorwing_fx},

    # FAN-MADE: TwinWing (near river)
    {"x": 850, "y": 480, "body": (150, 80, 180), "wing": (180, 100, 200), "eye": (255, 200, 0),
     "name": "TwinWing ★", "size": 0.75, "left": True, "extras": twinwing_fx},

    # FAN-MADE: CloudWing (in the sky area)
    {"x": 650, "y": 250, "body": (230, 235, 245), "wing": (210, 220, 240), "eye": (100, 160, 255),
     "name": "CloudWing ★", "size": 0.8, "left": False, "extras": cloudwing_fx},

    # FAN-MADE: CyberWing (near portal!)
    {"x": portal_cx + 80, "y": portal_cy + 40, "body": (0, 80, 180), "wing": (0, 140, 255), "eye": (0, 255, 255),
     "name": "CyberWing ★", "size": 0.8, "left": True, "extras": cyberwing_fx},
]

for d in dragons:
    draw_cartoon_dragon(
        d["x"], d["y"],
        body_color=d["body"],
        wing_color=d["wing"],
        eye_color=d["eye"],
        size=d.get("size", 0.75),
        facing_left=d.get("left", False),
        name=d.get("name", ""),
        extras=d.get("extras", None),
    )

# ── TITLE ──────────────────────────────────────────────────
try:
    title_font = ImageFont.truetype("arial.ttf", 32)
    sub_font = ImageFont.truetype("arial.ttf", 16)
except:
    title_font = ImageFont.load_default()
    sub_font = ImageFont.load_default()

title = "Wings of Fire — All Tribes"
tw = draw.textlength(title, font=title_font)
draw.rectangle([W // 2 - tw // 2 - 12, 8, W // 2 + tw // 2 + 12, 48], fill=(0, 0, 0))
draw.text((W // 2 - tw // 2, 10), title, fill=(255, 220, 50), font=title_font)

subtitle = "★ = Fan-Made Tribes"
sw = draw.textlength(subtitle, font=sub_font)
draw.rectangle([W // 2 - sw // 2 - 8, 52, W // 2 + sw // 2 + 8, 72], fill=(0, 0, 0))
draw.text((W // 2 - sw // 2, 54), subtitle, fill=(200, 150, 255), font=sub_font)

# ── SAVE ───────────────────────────────────────────────────
out_path = "wof_all_tribes.png"
img.save(out_path, "PNG")
print(f"Saved to {out_path} ({W}x{H})")
