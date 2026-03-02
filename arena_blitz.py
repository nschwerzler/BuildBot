"""
Arena Blitz — A top-down arena survival shooter.
Move with WASD, aim with mouse. Weapons auto-fire!
Survive waves of enemies, collect XP, level up, pick upgrades.
Boss every 5 waves. How long can you last?
"""

import pygame, math, random, sys, json, os, time, array, struct

# ── Mixer pre-init (mono) ──────────────────────────────────────────────
pygame.mixer.pre_init(frequency=44100, size=-16, channels=1, buffer=512)
pygame.init()
pygame.mixer.quit()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

# ── Window ──────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 900, 700
ARENA_W, ARENA_H = 2400, 2400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("⚔️ Arena Blitz ⚔️")
clock = pygame.time.Clock()
FPS = 60

# ── Save ────────────────────────────────────────────────────────────────
SAVE_FILE = "arena_blitz_save.json"

# ── Colours ─────────────────────────────────────────────────────────────
BG_DARK      = (18, 18, 28)
BG_TILE_A    = (25, 25, 38)
BG_TILE_B    = (30, 30, 44)
WHITE        = (255, 255, 255)
BLACK        = (0, 0, 0)
RED          = (220, 50, 50)
GREEN        = (50, 200, 80)
BLUE         = (60, 120, 220)
YELLOW       = (255, 220, 50)
ORANGE       = (240, 160, 40)
PURPLE       = (160, 80, 220)
CYAN         = (80, 220, 220)
PINK         = (240, 100, 180)
GOLD         = (255, 215, 0)
GRAY         = (120, 120, 120)
DARK_GRAY    = (60, 60, 60)
LIGHT_GRAY   = (180, 180, 180)
HP_RED       = (200, 40, 40)
HP_GREEN     = (60, 200, 60)
XP_BLUE      = (80, 140, 255)
PANEL_BG     = (20, 20, 35, 200)
SHADOW       = (0, 0, 0, 100)

# ── Fonts ───────────────────────────────────────────────────────────────
font_xl   = pygame.font.SysFont("Segoe UI", 52, bold=True)
font_lg   = pygame.font.SysFont("Segoe UI", 36, bold=True)
font_md   = pygame.font.SysFont("Segoe UI", 24, bold=True)
font_sm   = pygame.font.SysFont("Segoe UI", 18)
font_xs   = pygame.font.SysFont("Segoe UI", 14)
font_dmg  = pygame.font.SysFont("Segoe UI", 20, bold=True)

# ── Programmatic SFX ───────────────────────────────────────────────────
def _clamp(v):
    return max(-32767, min(32767, int(v)))

def _make_sound(samples_list):
    raw = array.array("h", [_clamp(s) for s in samples_list])
    snd = pygame.mixer.Sound(buffer=raw)
    return snd

def _sfx_shoot():
    sr = 44100
    dur = 0.08
    samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        freq = 800 - t * 6000
        v = math.sin(2 * math.pi * freq * t) * (1 - t / dur) * 8000
        v += random.uniform(-1500, 1500) * (1 - t / dur)
        samples.append(v)
    snd = _make_sound(samples)
    snd.set_volume(0.3)
    return snd

def _sfx_shoot_shotgun():
    sr = 44100
    dur = 0.12
    samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        freq = 200 - t * 800
        v = math.sin(2 * math.pi * freq * t) * (1 - t / dur) * 10000
        v += random.uniform(-4000, 4000) * (1 - t / dur)
        samples.append(v)
    snd = _make_sound(samples)
    snd.set_volume(0.35)
    return snd

def _sfx_hit():
    sr = 44100
    dur = 0.06
    samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        v = math.sin(2 * math.pi * 300 * t) * (1 - t / dur) * 6000
        v += random.uniform(-3000, 3000) * max(0, 1 - t / dur * 2)
        samples.append(v)
    snd = _make_sound(samples)
    snd.set_volume(0.25)
    return snd

def _sfx_enemy_die():
    sr = 44100
    dur = 0.18
    samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        freq = 400 - t * 1500
        v = math.sin(2 * math.pi * freq * t) * (1 - t / dur) * 9000
        v += random.uniform(-2000, 2000) * (1 - t / dur)
        samples.append(v)
    snd = _make_sound(samples)
    snd.set_volume(0.35)
    return snd

def _sfx_xp_pickup():
    sr = 44100
    dur = 0.07
    samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        freq = 600 + t * 3000
        v = math.sin(2 * math.pi * freq * t) * (1 - t / dur) * 5000
        samples.append(v)
    snd = _make_sound(samples)
    snd.set_volume(0.2)
    return snd

def _sfx_level_up():
    sr = 44100
    dur = 0.4
    samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        freq = 400 + t * 800
        v = math.sin(2 * math.pi * freq * t) * 8000
        v *= max(0, 1 - t / dur)
        v += math.sin(2 * math.pi * freq * 1.5 * t) * 3000 * max(0, 1 - t / dur)
        samples.append(v)
    snd = _make_sound(samples)
    snd.set_volume(0.4)
    return snd

def _sfx_player_hit():
    sr = 44100
    dur = 0.15
    samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        v = random.uniform(-8000, 8000) * max(0, 1 - t / dur)
        v += math.sin(2 * math.pi * 120 * t) * 6000 * max(0, 1 - t / dur)
        samples.append(v)
    snd = _make_sound(samples)
    snd.set_volume(0.4)
    return snd

def _sfx_boss_spawn():
    sr = 44100
    dur = 0.6
    samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        freq = 80 + math.sin(t * 10) * 30
        v = math.sin(2 * math.pi * freq * t) * 10000 * min(1, t * 5) * max(0, 1 - t / dur * 0.5)
        v += random.uniform(-3000, 3000) * max(0, 1 - t / dur)
        samples.append(v)
    snd = _make_sound(samples)
    snd.set_volume(0.5)
    return snd

def _sfx_wave_clear():
    sr = 44100
    dur = 0.5
    samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        note = [523, 659, 784][min(2, int(t / dur * 3))]
        v = math.sin(2 * math.pi * note * t) * 7000 * max(0, 1 - t / dur * 0.6)
        samples.append(v)
    snd = _make_sound(samples)
    snd.set_volume(0.4)
    return snd

def _sfx_heal():
    sr = 44100
    dur = 0.2
    samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        freq = 500 + t * 1500
        v = math.sin(2 * math.pi * freq * t) * 6000 * max(0, 1 - t / dur)
        samples.append(v)
    snd = _make_sound(samples)
    snd.set_volume(0.3)
    return snd

def _sfx_game_over():
    sr = 44100
    dur = 1.0
    samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        freq = 300 - t * 200
        v = math.sin(2 * math.pi * freq * t) * 8000 * max(0, 1 - t / dur)
        v += math.sin(2 * math.pi * freq * 0.5 * t) * 4000 * max(0, 1 - t / dur)
        samples.append(v)
    snd = _make_sound(samples)
    snd.set_volume(0.5)
    return snd

SFX = {
    "shoot": _sfx_shoot(),
    "shoot_sg": _sfx_shoot_shotgun(),
    "hit": _sfx_hit(),
    "die": _sfx_enemy_die(),
    "xp": _sfx_xp_pickup(),
    "level": _sfx_level_up(),
    "player_hit": _sfx_player_hit(),
    "boss": _sfx_boss_spawn(),
    "wave": _sfx_wave_clear(),
    "heal": _sfx_heal(),
    "game_over": _sfx_game_over(),
}

# ── Helpers ─────────────────────────────────────────────────────────────
def vec_len(x, y):
    return math.sqrt(x * x + y * y)

def vec_norm(x, y):
    d = vec_len(x, y)
    if d < 0.0001:
        return 0, 0
    return x / d, y / d

def angle_to(ax, ay, bx, by):
    return math.atan2(by - ay, bx - ax)

def dist(ax, ay, bx, by):
    return math.sqrt((bx - ax) ** 2 + (by - ay) ** 2)

def lerp(a, b, t):
    return a + (b - a) * t

def draw_text_shadow(surf, text, font, color, x, y, anchor="topleft"):
    ts = font.render(text, True, (0, 0, 0))
    tr = font.render(text, True, color)
    rect = tr.get_rect(**{anchor: (x, y)})
    surf.blit(ts, (rect.x + 2, rect.y + 2))
    surf.blit(tr, rect)
    return rect

# ── Particles ───────────────────────────────────────────────────────────
class Particle:
    __slots__ = ["x", "y", "vx", "vy", "life", "max_life", "color", "size"]
    def __init__(self, x, y, vx, vy, life, color, size=3):
        self.x = x; self.y = y; self.vx = vx; self.vy = vy
        self.life = life; self.max_life = life
        self.color = color; self.size = size

particles: list[Particle] = []

def spawn_particles(x, y, color, count=6, speed=120, life=0.4, size=3):
    for _ in range(count):
        a = random.uniform(0, math.pi * 2)
        s = random.uniform(speed * 0.3, speed)
        particles.append(Particle(x, y, math.cos(a) * s, math.sin(a) * s,
                                  life + random.uniform(-0.1, 0.1), color, size))

def update_particles(dt):
    for p in particles:
        p.x += p.vx * dt
        p.y += p.vy * dt
        p.life -= dt
    particles[:] = [p for p in particles if p.life > 0]

def draw_particles(surf, cam_x, cam_y):
    for p in particles:
        alpha = max(0, p.life / p.max_life)
        sz = max(1, int(p.size * alpha))
        sx = int(p.x - cam_x)
        sy = int(p.y - cam_y)
        if -10 < sx < WIDTH + 10 and -10 < sy < HEIGHT + 10:
            pygame.draw.circle(surf, p.color, (sx, sy), sz)

# ── Damage Numbers ─────────────────────────────────────────────────────
class DmgNumber:
    __slots__ = ["x", "y", "text", "color", "life", "vy"]
    def __init__(self, x, y, text, color=WHITE):
        self.x = x; self.y = y; self.text = text; self.color = color
        self.life = 0.7; self.vy = -80

dmg_numbers: list[DmgNumber] = []

def update_dmg_numbers(dt):
    for d in dmg_numbers:
        d.y += d.vy * dt
        d.life -= dt
    dmg_numbers[:] = [d for d in dmg_numbers if d.life > 0]

def draw_dmg_numbers(surf, cam_x, cam_y):
    for d in dmg_numbers:
        alpha = max(0, min(1, d.life / 0.4))
        sx = int(d.x - cam_x)
        sy = int(d.y - cam_y)
        if -50 < sx < WIDTH + 50 and -50 < sy < HEIGHT + 50:
            ts = font_dmg.render(d.text, True, d.color)
            ts.set_alpha(int(alpha * 255))
            surf.blit(ts, (sx - ts.get_width() // 2, sy))

# ── Screen Shake ────────────────────────────────────────────────────────
shake_amount = 0.0
shake_timer = 0.0

def add_shake(amount=4, dur=0.12):
    global shake_amount, shake_timer
    shake_amount = max(shake_amount, amount)
    shake_timer = max(shake_timer, dur)

def update_shake(dt):
    global shake_amount, shake_timer
    if shake_timer > 0:
        shake_timer -= dt
        if shake_timer <= 0:
            shake_amount = 0
            shake_timer = 0

def get_shake_offset():
    if shake_timer > 0:
        return random.uniform(-shake_amount, shake_amount), random.uniform(-shake_amount, shake_amount)
    return 0, 0

# ── Bullet ──────────────────────────────────────────────────────────────
class Bullet:
    __slots__ = ["x", "y", "vx", "vy", "damage", "life", "radius", "pierce",
                 "color", "hit_enemies"]
    def __init__(self, x, y, vx, vy, damage, color=YELLOW, radius=4, pierce=0):
        self.x = x; self.y = y; self.vx = vx; self.vy = vy
        self.damage = damage; self.life = 2.0; self.radius = radius
        self.pierce = pierce; self.color = color
        self.hit_enemies = set()

bullets: list[Bullet] = []

def update_bullets(dt, enemies):
    global bullets
    to_remove = []
    for b in bullets:
        b.x += b.vx * dt
        b.y += b.vy * dt
        b.life -= dt
        if b.life <= 0 or b.x < -50 or b.x > ARENA_W + 50 or b.y < -50 or b.y > ARENA_H + 50:
            to_remove.append(b)
            continue
        for e in enemies:
            if id(e) in b.hit_enemies:
                continue
            if dist(b.x, b.y, e.x, e.y) < b.radius + e.radius:
                e.hp -= b.damage
                b.hit_enemies.add(id(e))
                spawn_particles(e.x, e.y, e.color, count=4, speed=80)
                dmg_numbers.append(DmgNumber(e.x, e.y - e.radius, str(int(b.damage)), YELLOW))
                SFX["hit"].play()
                add_shake(2, 0.05)
                if b.pierce <= 0:
                    to_remove.append(b)
                    break
                else:
                    b.pierce -= 1
    bullets[:] = [b for b in bullets if b not in to_remove]

def draw_bullets(surf, cam_x, cam_y):
    for b in bullets:
        sx = int(b.x - cam_x)
        sy = int(b.y - cam_y)
        if -10 < sx < WIDTH + 10 and -10 < sy < HEIGHT + 10:
            pygame.draw.circle(surf, b.color, (sx, sy), b.radius)
            # small trail
            pygame.draw.circle(surf, WHITE, (sx, sy), max(1, b.radius - 2))

# ── XP Orb ──────────────────────────────────────────────────────────────
class XPOrb:
    __slots__ = ["x", "y", "value", "life", "radius"]
    def __init__(self, x, y, value=1):
        self.x = x; self.y = y; self.value = value; self.life = 12.0
        self.radius = 5 + min(3, value // 5)

xp_orbs: list[XPOrb] = []

def update_xp_orbs(dt, player):
    for orb in xp_orbs:
        orb.life -= dt
        # Magnetism: pull toward player when close
        d = dist(orb.x, orb.y, player.x, player.y)
        attract_range = player.magnet_range
        if d < attract_range:
            pull = 1.0 - d / attract_range
            nx, ny = vec_norm(player.x - orb.x, player.y - orb.y)
            speed = 300 + pull * 400
            orb.x += nx * speed * dt
            orb.y += ny * speed * dt
    xp_orbs[:] = [o for o in xp_orbs if o.life > 0]

def draw_xp_orbs(surf, cam_x, cam_y):
    for orb in xp_orbs:
        sx = int(orb.x - cam_x)
        sy = int(orb.y - cam_y)
        if -10 < sx < WIDTH + 10 and -10 < sy < HEIGHT + 10:
            # Pulsing glow
            t = time.time() * 5
            glow_r = orb.radius + int(math.sin(t + orb.x) * 2)
            pygame.draw.circle(surf, (40, 80, 200), (sx, sy), glow_r + 3)
            pygame.draw.circle(surf, XP_BLUE, (sx, sy), glow_r)
            pygame.draw.circle(surf, WHITE, (sx, sy), max(1, glow_r - 3))

# ── Health Pickup ───────────────────────────────────────────────────────
class HealthPickup:
    __slots__ = ["x", "y", "heal", "life", "radius"]
    def __init__(self, x, y, heal=20):
        self.x = x; self.y = y; self.heal = heal
        self.life = 15.0; self.radius = 10

health_pickups: list[HealthPickup] = []

def draw_health_pickups(surf, cam_x, cam_y):
    for hp in health_pickups:
        sx = int(hp.x - cam_x)
        sy = int(hp.y - cam_y)
        if -10 < sx < WIDTH + 10 and -10 < sy < HEIGHT + 10:
            pygame.draw.circle(surf, RED, (sx, sy), hp.radius)
            pygame.draw.rect(surf, WHITE, (sx - 5, sy - 2, 10, 4))
            pygame.draw.rect(surf, WHITE, (sx - 2, sy - 5, 4, 10))

# ── Enemy Types ─────────────────────────────────────────────────────────
ENEMY_TYPES = {
    "grunt": {"hp": 20, "speed": 80, "radius": 12, "color": (200, 60, 60),
              "damage": 8, "xp": 1, "attack_cd": 1.0},
    "fast": {"hp": 12, "speed": 160, "radius": 9, "color": (220, 180, 40),
             "damage": 5, "xp": 1, "attack_cd": 0.6},
    "tank": {"hp": 80, "speed": 45, "radius": 18, "color": (100, 80, 160),
             "damage": 15, "xp": 3, "attack_cd": 1.5},
    "shooter": {"hp": 25, "speed": 55, "radius": 11, "color": (60, 180, 60),
                "damage": 10, "xp": 2, "attack_cd": 2.0},
    "swarm": {"hp": 8, "speed": 120, "radius": 7, "color": (180, 100, 50),
              "damage": 4, "xp": 1, "attack_cd": 0.5},
    "ghost": {"hp": 30, "speed": 70, "radius": 13, "color": (150, 150, 220),
              "damage": 12, "xp": 2, "attack_cd": 1.2},
}

class Enemy:
    __slots__ = ["x", "y", "hp", "max_hp", "speed", "radius", "color",
                 "damage", "xp", "attack_cd", "attack_timer", "etype",
                 "is_boss", "flash_timer", "alive"]
    def __init__(self, x, y, etype="grunt", wave=1, is_boss=False):
        info = ENEMY_TYPES.get(etype, ENEMY_TYPES["grunt"])
        scale = 1 + (wave - 1) * 0.15
        self.x = x; self.y = y
        self.etype = etype
        self.is_boss = is_boss
        boss_mult = 10 if is_boss else 1
        self.hp = info["hp"] * scale * boss_mult
        self.max_hp = self.hp
        self.speed = info["speed"] * (0.8 if is_boss else 1)
        self.radius = info["radius"] * (2.5 if is_boss else 1)
        c = info["color"]
        self.color = (min(255, c[0] + 40), min(255, c[1] + 20), min(255, c[2] + 20)) if is_boss else c
        self.damage = info["damage"] * scale * (2 if is_boss else 1)
        self.xp = int(info["xp"] * scale * (15 if is_boss else 1))
        self.attack_cd = info["attack_cd"]
        self.attack_timer = 0
        self.flash_timer = 0
        self.alive = True

enemies: list[Enemy] = []
enemy_bullets: list[Bullet] = []

def spawn_enemy_at_edge(player_x, player_y, etype="grunt", wave=1, is_boss=False):
    # Spawn at a random edge, at least 400px from player
    for _ in range(20):
        side = random.randint(0, 3)
        if side == 0:
            x, y = random.uniform(50, ARENA_W - 50), 50
        elif side == 1:
            x, y = random.uniform(50, ARENA_W - 50), ARENA_H - 50
        elif side == 2:
            x, y = 50, random.uniform(50, ARENA_H - 50)
        else:
            x, y = ARENA_W - 50, random.uniform(50, ARENA_H - 50)
        if dist(x, y, player_x, player_y) > 350:
            enemies.append(Enemy(x, y, etype, wave, is_boss))
            if is_boss:
                SFX["boss"].play()
                add_shake(8, 0.3)
            return
    # fallback
    enemies.append(Enemy(ARENA_W // 2, 50, etype, wave, is_boss))

def update_enemies(dt, player):
    for e in enemies:
        if not e.alive:
            continue
        # Move toward player
        dx = player.x - e.x
        dy = player.y - e.y
        d = vec_len(dx, dy)
        if d > 0:
            nx, ny = dx / d, dy / d
        else:
            nx, ny = 0, 0

        # Shooter type: stop and shoot from distance
        if e.etype == "shooter" and d < 300 and d > 120:
            # Stand still and shoot
            pass
        else:
            e.x += nx * e.speed * dt
            e.y += ny * e.speed * dt

        # Keep in arena
        e.x = max(e.radius, min(ARENA_W - e.radius, e.x))
        e.y = max(e.radius, min(ARENA_H - e.radius, e.y))

        # Attack timer
        e.attack_timer -= dt
        e.flash_timer -= dt

        # Melee damage
        if d < e.radius + player.radius and e.attack_timer <= 0:
            player.take_damage(e.damage)
            e.attack_timer = e.attack_cd
            add_shake(4, 0.1)

        # Shooter fires bullets
        if e.etype == "shooter" and d < 350 and e.attack_timer <= 0:
            bspeed = 250
            bx, by = nx * bspeed, ny * bspeed
            enemy_bullets.append(Bullet(e.x, e.y, bx, by, e.damage, color=GREEN, radius=5))
            e.attack_timer = e.attack_cd

        # Check death
        if e.hp <= 0:
            e.alive = False
            SFX["die"].play()
            spawn_particles(e.x, e.y, e.color, count=12, speed=150, life=0.5, size=4)
            # Drop XP
            xp_val = e.xp
            for _ in range(max(1, xp_val)):
                ox = e.x + random.uniform(-15, 15)
                oy = e.y + random.uniform(-15, 15)
                xp_orbs.append(XPOrb(ox, oy, 1))
            # Chance to drop health
            if random.random() < (0.15 if not e.is_boss else 1.0):
                health_pickups.append(HealthPickup(e.x, e.y, 15 + (10 if e.is_boss else 0)))

    enemies[:] = [e for e in enemies if e.alive]

def update_enemy_bullets(dt, player):
    to_remove = []
    for b in enemy_bullets:
        b.x += b.vx * dt
        b.y += b.vy * dt
        b.life -= dt
        if b.life <= 0 or b.x < -50 or b.x > ARENA_W + 50 or b.y < -50 or b.y > ARENA_H + 50:
            to_remove.append(b)
            continue
        if dist(b.x, b.y, player.x, player.y) < b.radius + player.radius:
            player.take_damage(b.damage)
            spawn_particles(player.x, player.y, RED, count=5, speed=100)
            to_remove.append(b)
            add_shake(3, 0.08)
    enemy_bullets[:] = [b for b in enemy_bullets if b not in to_remove]

def draw_enemies(surf, cam_x, cam_y):
    for e in enemies:
        sx = int(e.x - cam_x)
        sy = int(e.y - cam_y)
        if -50 < sx < WIDTH + 50 and -50 < sy < HEIGHT + 50:
            r = int(e.radius)
            # Shadow
            pygame.draw.ellipse(surf, (0, 0, 0), (sx - r, sy + r // 2, r * 2, r))
            # Body
            col = e.color if e.flash_timer <= 0 else WHITE
            pygame.draw.circle(surf, col, (sx, sy), r)
            # Eyes
            ex1 = sx - r // 3
            ex2 = sx + r // 3
            ey = sy - r // 4
            eye_r = max(2, r // 5)
            pygame.draw.circle(surf, WHITE, (ex1, ey), eye_r + 1)
            pygame.draw.circle(surf, WHITE, (ex2, ey), eye_r + 1)
            pygame.draw.circle(surf, BLACK, (ex1, ey), eye_r)
            pygame.draw.circle(surf, BLACK, (ex2, ey), eye_r)
            # Boss crown
            if e.is_boss:
                pts = [(sx - r, sy - r - 5), (sx - r // 2, sy - r - 15),
                       (sx, sy - r - 5), (sx + r // 2, sy - r - 15),
                       (sx + r, sy - r - 5)]
                pygame.draw.polygon(surf, GOLD, pts)
            # HP bar
            if e.hp < e.max_hp:
                bar_w = r * 2
                bar_h = 4
                bx = sx - r
                by = sy - r - 10 - (15 if e.is_boss else 0)
                pygame.draw.rect(surf, DARK_GRAY, (bx, by, bar_w, bar_h))
                fill = max(0, e.hp / e.max_hp)
                pygame.draw.rect(surf, HP_GREEN if fill > 0.5 else ORANGE if fill > 0.25 else HP_RED,
                                 (bx, by, int(bar_w * fill), bar_h))

    # Enemy bullets
    for b in enemy_bullets:
        sx = int(b.x - cam_x)
        sy = int(b.y - cam_y)
        if -10 < sx < WIDTH + 10 and -10 < sy < HEIGHT + 10:
            pygame.draw.circle(surf, b.color, (sx, sy), b.radius)

# ── Weapon System ───────────────────────────────────────────────────────
class Weapon:
    def __init__(self, name, cooldown, damage, speed, spread=0, count=1,
                 pierce=0, color=YELLOW, burst=1):
        self.name = name
        self.base_cooldown = cooldown
        self.cooldown = cooldown
        self.damage = damage
        self.speed = speed
        self.spread = spread  # radians
        self.count = count  # projectiles per shot
        self.pierce = pierce
        self.color = color
        self.burst = burst
        self.timer = 0

    def fire(self, x, y, angle):
        self.timer = self.cooldown
        new_bullets = []
        for b in range(self.burst):
            for i in range(self.count):
                if self.count > 1:
                    a = angle - self.spread / 2 + self.spread * i / (self.count - 1)
                else:
                    a = angle + random.uniform(-self.spread / 2, self.spread / 2)
                a += random.uniform(-0.03, 0.03)  # tiny inaccuracy
                vx = math.cos(a) * self.speed
                vy = math.sin(a) * self.speed
                bx = x + math.cos(a) * 15
                by = y + math.sin(a) * 15
                new_bullets.append(Bullet(bx, by, vx, vy, self.damage,
                                          self.color, radius=4 + self.damage // 15,
                                          pierce=self.pierce))
        if self.count >= 3:
            SFX["shoot_sg"].play()
        else:
            SFX["shoot"].play()
        return new_bullets

# ── Player ──────────────────────────────────────────────────────────────
class Player:
    def __init__(self):
        self.x = ARENA_W / 2
        self.y = ARENA_H / 2
        self.radius = 14
        self.speed = 200
        self.hp = 100
        self.max_hp = 100
        self.xp = 0
        self.level = 1
        self.xp_to_next = 10
        self.kills = 0
        self.i_frames = 0  # invincibility frames
        self.magnet_range = 80
        # Weapons
        self.weapons = [Weapon("Pistol", 0.35, 10, 500, spread=0.05)]
        # Passive stats
        self.damage_mult = 1.0
        self.speed_mult = 1.0
        self.cooldown_mult = 1.0
        self.armor = 0
        # Aura
        self.aura_damage = 0
        self.aura_range = 0
        self.aura_timer = 0

    def take_damage(self, amount):
        if self.i_frames > 0:
            return
        actual = max(1, amount - self.armor)
        self.hp -= actual
        self.i_frames = 0.5
        SFX["player_hit"].play()
        dmg_numbers.append(DmgNumber(self.x, self.y - self.radius - 10,
                                     f"-{int(actual)}", RED))
        add_shake(5, 0.1)

    def heal(self, amount):
        old = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        healed = self.hp - old
        if healed > 0:
            SFX["heal"].play()
            dmg_numbers.append(DmgNumber(self.x, self.y - self.radius - 10,
                                         f"+{int(healed)}", GREEN))

    def add_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * 1.35) + 5
            SFX["level"].play()
            add_shake(6, 0.15)
            spawn_particles(self.x, self.y, XP_BLUE, count=20, speed=200, life=0.6, size=4)
            return True  # signal level up
        return False

    def update(self, dt, keys):
        self.i_frames -= dt
        # Movement
        mx, my = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]: my -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: my += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: mx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: mx += 1
        if mx != 0 or my != 0:
            nx, ny = vec_norm(mx, my)
            spd = self.speed * self.speed_mult
            self.x += nx * spd * dt
            self.y += ny * spd * dt
        # Clamp in arena
        self.x = max(self.radius, min(ARENA_W - self.radius, self.x))
        self.y = max(self.radius, min(ARENA_H - self.radius, self.y))
        # Update weapon timers
        for w in self.weapons:
            w.timer -= dt
        # Aura damage
        if self.aura_damage > 0:
            self.aura_timer -= dt
            if self.aura_timer <= 0:
                self.aura_timer = 0.5
                for e in enemies:
                    if dist(self.x, self.y, e.x, e.y) < self.aura_range:
                        e.hp -= self.aura_damage * self.damage_mult
                        dmg_numbers.append(DmgNumber(e.x, e.y - e.radius,
                                                     str(int(self.aura_damage * self.damage_mult)), CYAN))

    def auto_fire(self, mouse_x, mouse_y, cam_x, cam_y):
        # Aim toward mouse (world coords)
        world_mx = mouse_x + cam_x
        world_my = mouse_y + cam_y
        angle = angle_to(self.x, self.y, world_mx, world_my)
        new_bullets = []
        for w in self.weapons:
            if w.timer <= 0:
                w.cooldown = w.base_cooldown * self.cooldown_mult
                blist = w.fire(self.x, self.y, angle)
                for b in blist:
                    b.damage *= self.damage_mult
                new_bullets.extend(blist)
        return new_bullets

    def draw(self, surf, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        r = self.radius
        # Aura ring
        if self.aura_damage > 0:
            aura_r = int(self.aura_range)
            aura_surf = pygame.Surface((aura_r * 2, aura_r * 2), pygame.SRCALPHA)
            pulse = int(20 + math.sin(time.time() * 4) * 10)
            pygame.draw.circle(aura_surf, (80, 220, 220, pulse),
                               (aura_r, aura_r), aura_r)
            surf.blit(aura_surf, (sx - aura_r, sy - aura_r))
        # Shadow
        pygame.draw.ellipse(surf, (0, 0, 0), (sx - r, sy + r // 2, r * 2, r))
        # Body
        body_col = CYAN if self.i_frames > 0 and int(self.i_frames * 20) % 2 == 0 else BLUE
        pygame.draw.circle(surf, body_col, (sx, sy), r)
        pygame.draw.circle(surf, (100, 160, 255), (sx, sy), r, 2)
        # Eyes
        pygame.draw.circle(surf, WHITE, (sx - 4, sy - 3), 5)
        pygame.draw.circle(surf, WHITE, (sx + 4, sy - 3), 5)
        pygame.draw.circle(surf, BLACK, (sx - 4, sy - 3), 3)
        pygame.draw.circle(surf, BLACK, (sx + 4, sy - 3), 3)

# ── Upgrade Choices ─────────────────────────────────────────────────────
UPGRADES = [
    {"name": "🔫 +Damage",       "desc": "+20% bullet damage",
     "apply": lambda p: setattr(p, 'damage_mult', p.damage_mult * 1.2)},
    {"name": "💨 +Speed",        "desc": "+15% move speed",
     "apply": lambda p: setattr(p, 'speed_mult', p.speed_mult * 1.15)},
    {"name": "🔥 +Fire Rate",    "desc": "+15% fire rate",
     "apply": lambda p: setattr(p, 'cooldown_mult', p.cooldown_mult * 0.85)},
    {"name": "❤️ +Max HP",        "desc": "+25 max HP",
     "apply": lambda p: (setattr(p, 'max_hp', p.max_hp + 25), p.heal(25))},
    {"name": "🧲 +Magnet",       "desc": "+40 XP magnet range",
     "apply": lambda p: setattr(p, 'magnet_range', p.magnet_range + 40)},
    {"name": "🛡️ +Armor",         "desc": "+3 armor (reduces dmg taken)",
     "apply": lambda p: setattr(p, 'armor', p.armor + 3)},
    {"name": "💥 Pierce Shot",   "desc": "Bullets pierce +1 enemy",
     "apply": lambda p: [setattr(w, 'pierce', w.pierce + 1) for w in p.weapons]},
    {"name": "🌀 Aura",          "desc": "Damage nearby enemies passively",
     "apply": lambda p: (setattr(p, 'aura_damage', p.aura_damage + 8),
                          setattr(p, 'aura_range', max(p.aura_range, 100) + 30))},
    {"name": "🎯 Multi-Shot",    "desc": "+1 projectile per weapon",
     "apply": lambda p: [setattr(w, 'count', w.count + 1) or
                          setattr(w, 'spread', max(w.spread, 0.15) + 0.1) for w in p.weapons]},
    {"name": "⚡ Burst Fire",    "desc": "+1 burst round per weapon",
     "apply": lambda p: [setattr(w, 'burst', w.burst + 1) for w in p.weapons]},
    {"name": "🔄 Heal",          "desc": "Heal 30 HP now",
     "apply": lambda p: p.heal(30)},
    {"name": "🎆 Shotgun",       "desc": "Add a shotgun weapon!",
     "apply": lambda p: p.weapons.append(
         Weapon("Shotgun", 0.8, 8, 400, spread=0.6, count=5, color=ORANGE))},
    {"name": "⚙️ Minigun",       "desc": "Add a rapid-fire minigun!",
     "apply": lambda p: p.weapons.append(
         Weapon("Minigun", 0.08, 4, 550, spread=0.15, color=PINK))},
    {"name": "💎 Railgun",       "desc": "Add a piercing railgun!",
     "apply": lambda p: p.weapons.append(
         Weapon("Railgun", 1.2, 50, 800, pierce=5, color=CYAN, count=1))},
]

def get_upgrade_choices(count=3):
    return random.sample(UPGRADES, min(count, len(UPGRADES)))

# ── Wave System ─────────────────────────────────────────────────────────
class WaveManager:
    def __init__(self):
        self.wave = 0
        self.enemies_left = 0
        self.spawn_timer = 0
        self.spawn_delay = 1.0
        self.spawned = 0
        self.total_to_spawn = 0
        self.wave_active = False
        self.intermission = 3.0
        self.inter_timer = 2.0

    def start_wave(self):
        self.wave += 1
        self.spawned = 0
        base = 5 + self.wave * 3
        self.total_to_spawn = min(base, 60)
        self.enemies_left = self.total_to_spawn
        self.spawn_timer = 0
        self.spawn_delay = max(0.2, 1.0 - self.wave * 0.03)
        self.wave_active = True

    def update(self, dt, player):
        if not self.wave_active:
            self.inter_timer -= dt
            if self.inter_timer <= 0:
                self.start_wave()
            return

        # Spawn enemies
        if self.spawned < self.total_to_spawn:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self.spawn_timer = self.spawn_delay
                # Pick enemy type based on wave
                types = ["grunt"]
                if self.wave >= 2: types.append("fast")
                if self.wave >= 3: types.append("swarm"); types.append("swarm")
                if self.wave >= 4: types.append("shooter")
                if self.wave >= 5: types.append("tank")
                if self.wave >= 7: types.append("ghost")

                etype = random.choice(types)
                spawn_enemy_at_edge(player.x, player.y, etype, self.wave)
                self.spawned += 1

                # Boss every 5 waves (spawns with last batch)
                if self.wave % 5 == 0 and self.spawned == self.total_to_spawn:
                    boss_types = ["tank", "grunt", "ghost"]
                    spawn_enemy_at_edge(player.x, player.y,
                                        random.choice(boss_types),
                                        self.wave, is_boss=True)

        # Check wave clear
        if self.spawned >= self.total_to_spawn and len(enemies) == 0:
            self.wave_active = False
            self.inter_timer = self.intermission
            SFX["wave"].play()

# ── HUD ─────────────────────────────────────────────────────────────────
def draw_hud(surf, player, wave_mgr, game_time):
    # HP bar
    bar_x, bar_y, bar_w, bar_h = 20, 20, 200, 20
    pygame.draw.rect(surf, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h), border_radius=4)
    fill = max(0, player.hp / player.max_hp)
    fill_col = HP_GREEN if fill > 0.5 else ORANGE if fill > 0.25 else HP_RED
    pygame.draw.rect(surf, fill_col, (bar_x, bar_y, int(bar_w * fill), bar_h), border_radius=4)
    pygame.draw.rect(surf, WHITE, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=4)
    hp_text = font_sm.render(f"HP: {int(player.hp)}/{int(player.max_hp)}", True, WHITE)
    surf.blit(hp_text, (bar_x + bar_w // 2 - hp_text.get_width() // 2, bar_y + 1))

    # XP bar
    xp_y = bar_y + bar_h + 6
    pygame.draw.rect(surf, DARK_GRAY, (bar_x, xp_y, bar_w, 14), border_radius=3)
    xp_fill = min(1, player.xp / max(1, player.xp_to_next))
    pygame.draw.rect(surf, XP_BLUE, (bar_x, xp_y, int(bar_w * xp_fill), 14), border_radius=3)
    pygame.draw.rect(surf, WHITE, (bar_x, xp_y, bar_w, 14), 1, border_radius=3)
    xp_text = font_xs.render(f"Lv {player.level}  XP: {player.xp}/{player.xp_to_next}", True, WHITE)
    surf.blit(xp_text, (bar_x + 4, xp_y))

    # Wave / Kills / Time
    info_y = xp_y + 22
    draw_text_shadow(surf, f"Wave {wave_mgr.wave}", font_md, GOLD, bar_x, info_y)
    draw_text_shadow(surf, f"Kills: {player.kills}", font_sm, WHITE, bar_x, info_y + 28)
    mins = int(game_time) // 60
    secs = int(game_time) % 60
    draw_text_shadow(surf, f"Time: {mins}:{secs:02d}", font_sm, LIGHT_GRAY, bar_x, info_y + 48)

    # Weapons list
    wy = HEIGHT - 30
    wx = 20
    for w in player.weapons:
        cd_pct = max(0, w.timer / w.cooldown) if w.cooldown > 0 else 0
        col = GRAY if cd_pct > 0 else WHITE
        txt = font_xs.render(f"{w.name}", True, col)
        surf.blit(txt, (wx, wy))
        wx += txt.get_width() + 15

    # Enemy count
    ec = len(enemies)
    if ec > 0:
        draw_text_shadow(surf, f"Enemies: {ec}", font_sm, RED, WIDTH - 140, 20)

    # Minimap
    mm_size = 120
    mm_x = WIDTH - mm_size - 10
    mm_y = HEIGHT - mm_size - 10
    mm_surf = pygame.Surface((mm_size, mm_size), pygame.SRCALPHA)
    mm_surf.fill((0, 0, 0, 120))
    # Player dot
    px = int(player.x / ARENA_W * mm_size)
    py = int(player.y / ARENA_H * mm_size)
    pygame.draw.circle(mm_surf, BLUE, (px, py), 3)
    # Enemy dots
    for e in enemies:
        ex = int(e.x / ARENA_W * mm_size)
        ey = int(e.y / ARENA_H * mm_size)
        col = GOLD if e.is_boss else RED
        pygame.draw.circle(mm_surf, col, (ex, ey), 2 if not e.is_boss else 3)
    # XP dots
    for o in xp_orbs:
        ox = int(o.x / ARENA_W * mm_size)
        oy = int(o.y / ARENA_H * mm_size)
        pygame.draw.rect(mm_surf, XP_BLUE, (ox, oy, 1, 1))
    pygame.draw.rect(mm_surf, WHITE, (0, 0, mm_size, mm_size), 1)
    surf.blit(mm_surf, (mm_x, mm_y))

# ── Draw arena background ──────────────────────────────────────────────
TILE_SIZE = 64

def draw_arena_bg(surf, cam_x, cam_y):
    # Fill with dark
    surf.fill(BG_DARK)
    # Draw tiles
    start_x = int(cam_x // TILE_SIZE)
    start_y = int(cam_y // TILE_SIZE)
    end_x = start_x + WIDTH // TILE_SIZE + 2
    end_y = start_y + HEIGHT // TILE_SIZE + 2
    for tx in range(start_x, end_x):
        for ty in range(start_y, end_y):
            if 0 <= tx * TILE_SIZE < ARENA_W and 0 <= ty * TILE_SIZE < ARENA_H:
                color = BG_TILE_A if (tx + ty) % 2 == 0 else BG_TILE_B
                sx = tx * TILE_SIZE - int(cam_x)
                sy = ty * TILE_SIZE - int(cam_y)
                pygame.draw.rect(surf, color, (sx, sy, TILE_SIZE, TILE_SIZE))
    # Arena border
    bx = -int(cam_x)
    by = -int(cam_y)
    pygame.draw.rect(surf, (80, 80, 120), (bx, by, ARENA_W, ARENA_H), 3)

# ── Level Up Screen ────────────────────────────────────────────────────
def draw_level_up(surf, choices, hover_idx):
    # Dim overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surf.blit(overlay, (0, 0))

    draw_text_shadow(surf, "LEVEL UP!", font_xl, GOLD, WIDTH // 2, 100, anchor="midtop")
    draw_text_shadow(surf, "Choose an upgrade:", font_md, WHITE, WIDTH // 2, 160, anchor="midtop")

    card_w, card_h = 220, 160
    total_w = len(choices) * card_w + (len(choices) - 1) * 20
    start_x = WIDTH // 2 - total_w // 2
    rects = []

    for i, choice in enumerate(choices):
        cx = start_x + i * (card_w + 20)
        cy = 220
        hovered = (i == hover_idx)
        bg_col = (60, 60, 100) if not hovered else (80, 80, 140)
        border_col = GOLD if hovered else GRAY
        rect = pygame.Rect(cx, cy, card_w, card_h)
        pygame.draw.rect(surf, bg_col, rect, border_radius=10)
        pygame.draw.rect(surf, border_col, rect, 3, border_radius=10)
        # Name
        name_surf = font_md.render(choice["name"], True, WHITE)
        surf.blit(name_surf, (cx + card_w // 2 - name_surf.get_width() // 2, cy + 20))
        # Desc (word wrap simple)
        desc = choice["desc"]
        words = desc.split()
        lines = []
        line = ""
        for w in words:
            test = line + " " + w if line else w
            if font_sm.size(test)[0] < card_w - 20:
                line = test
            else:
                lines.append(line)
                line = w
        if line:
            lines.append(line)
        for li, l in enumerate(lines):
            ds = font_sm.render(l, True, LIGHT_GRAY)
            surf.blit(ds, (cx + card_w // 2 - ds.get_width() // 2, cy + 60 + li * 20))
        rects.append(rect)
    return rects

# ── Save / Load High Score ─────────────────────────────────────────────
def load_save():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {"high_score": 0, "best_wave": 0, "best_kills": 0, "games_played": 0}

def save_game(data):
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ── Main Menu ───────────────────────────────────────────────────────────
def draw_main_menu(surf, save_data, hover):
    surf.fill(BG_DARK)
    # Title
    draw_text_shadow(surf, "ARENA BLITZ", font_xl, CYAN, WIDTH // 2, 120, anchor="midtop")
    draw_text_shadow(surf, "⚔️ Survive the Waves ⚔️", font_md, GOLD, WIDTH // 2, 185, anchor="midtop")

    # Stats
    sy = 250
    draw_text_shadow(surf, f"Games Played: {save_data['games_played']}", font_sm, LIGHT_GRAY,
                     WIDTH // 2, sy, anchor="midtop")
    draw_text_shadow(surf, f"Best Wave: {save_data['best_wave']}", font_sm, LIGHT_GRAY,
                     WIDTH // 2, sy + 25, anchor="midtop")
    draw_text_shadow(surf, f"Best Kills: {save_data['best_kills']}", font_sm, LIGHT_GRAY,
                     WIDTH // 2, sy + 50, anchor="midtop")

    # Play button
    btn_w, btn_h = 250, 60
    bx = WIDTH // 2 - btn_w // 2
    by = 400
    btn_rect = pygame.Rect(bx, by, btn_w, btn_h)
    col = (80, 200, 120) if hover == "play" else (60, 160, 90)
    pygame.draw.rect(surf, col, btn_rect, border_radius=12)
    pygame.draw.rect(surf, WHITE, btn_rect, 2, border_radius=12)
    draw_text_shadow(surf, "PLAY", font_lg, WHITE, WIDTH // 2, by + 12, anchor="midtop")

    # Quit button
    qy = 490
    quit_rect = pygame.Rect(bx, qy, btn_w, btn_h)
    qcol = (200, 80, 80) if hover == "quit" else (160, 60, 60)
    pygame.draw.rect(surf, qcol, quit_rect, border_radius=12)
    pygame.draw.rect(surf, WHITE, quit_rect, 2, border_radius=12)
    draw_text_shadow(surf, "QUIT", font_lg, WHITE, WIDTH // 2, qy + 12, anchor="midtop")

    # Controls
    cy = 580
    draw_text_shadow(surf, "WASD / Arrows = Move   |   Mouse = Aim   |   Auto-fire!", font_xs, GRAY,
                     WIDTH // 2, cy, anchor="midtop")
    draw_text_shadow(surf, "Survive waves, collect XP, pick upgrades!", font_xs, GRAY,
                     WIDTH // 2, cy + 20, anchor="midtop")

    return btn_rect, quit_rect

# ── Game Over Screen ────────────────────────────────────────────────────
def draw_game_over(surf, player, wave_mgr, game_time, save_data, hover):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surf.blit(overlay, (0, 0))

    draw_text_shadow(surf, "GAME OVER", font_xl, RED, WIDTH // 2, 80, anchor="midtop")

    mins = int(game_time) // 60
    secs = int(game_time) % 60
    stats = [
        f"Wave Reached: {wave_mgr.wave}",
        f"Kills: {player.kills}",
        f"Level: {player.level}",
        f"Time: {mins}:{secs:02d}",
    ]
    new_best = wave_mgr.wave > save_data.get("best_wave", 0)
    if new_best:
        stats.append("🏆 NEW BEST WAVE! 🏆")

    for i, s in enumerate(stats):
        col = GOLD if "NEW BEST" in s else WHITE
        draw_text_shadow(surf, s, font_md, col, WIDTH // 2, 170 + i * 40, anchor="midtop")

    # Retry
    btn_w, btn_h = 200, 50
    bx = WIDTH // 2 - btn_w // 2
    ry = 420
    retry_rect = pygame.Rect(bx, ry, btn_w, btn_h)
    col = (80, 200, 120) if hover == "retry" else (60, 160, 90)
    pygame.draw.rect(surf, col, retry_rect, border_radius=10)
    pygame.draw.rect(surf, WHITE, retry_rect, 2, border_radius=10)
    draw_text_shadow(surf, "RETRY", font_md, WHITE, WIDTH // 2, ry + 12, anchor="midtop")

    # Menu
    my = 490
    menu_rect = pygame.Rect(bx, my, btn_w, btn_h)
    mcol = (180, 140, 40) if hover == "menu" else (140, 110, 30)
    pygame.draw.rect(surf, mcol, menu_rect, border_radius=10)
    pygame.draw.rect(surf, WHITE, menu_rect, 2, border_radius=10)
    draw_text_shadow(surf, "MENU", font_md, WHITE, WIDTH // 2, my + 12, anchor="midtop")

    return retry_rect, menu_rect

# ── Main Game Loop ──────────────────────────────────────────────────────
def main():
    save_data = load_save()
    state = "menu"  # menu, playing, level_up, game_over
    player = Player()
    wave_mgr = WaveManager()
    game_time = 0.0
    level_choices = []
    level_rects = []
    level_hover = -1

    # Camera
    cam_x, cam_y = 0, 0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)  # cap delta
        mx, my = pygame.mouse.get_pos()

        # ── Events ──────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state == "menu":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    play_rect, quit_rect = draw_main_menu(screen, save_data, "")
                    if play_rect.collidepoint(mx, my):
                        state = "playing"
                        player = Player()
                        wave_mgr = WaveManager()
                        game_time = 0.0
                        enemies.clear(); bullets.clear(); enemy_bullets.clear()
                        xp_orbs.clear(); health_pickups.clear()
                        particles.clear(); dmg_numbers.clear()
                    elif quit_rect.collidepoint(mx, my):
                        running = False

            elif state == "level_up":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i, rect in enumerate(level_rects):
                        if rect.collidepoint(mx, my):
                            level_choices[i]["apply"](player)
                            state = "playing"
                            break

            elif state == "game_over":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    retry_rect, menu_rect = draw_game_over(screen, player, wave_mgr,
                                                           game_time, save_data, "")
                    if retry_rect.collidepoint(mx, my):
                        state = "playing"
                        player = Player()
                        wave_mgr = WaveManager()
                        game_time = 0.0
                        enemies.clear(); bullets.clear(); enemy_bullets.clear()
                        xp_orbs.clear(); health_pickups.clear()
                        particles.clear(); dmg_numbers.clear()
                    elif menu_rect.collidepoint(mx, my):
                        state = "menu"

            elif state == "playing":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = "menu"

        # ── Update ──────────────────────────────────────────────────
        if state == "playing":
            game_time += dt
            keys = pygame.key.get_pressed()
            player.update(dt, keys)

            # Auto fire
            new_b = player.auto_fire(mx, my, cam_x, cam_y)
            bullets.extend(new_b)

            # Wave
            wave_mgr.update(dt, player)

            # Bullets vs enemies
            update_bullets(dt, enemies)
            update_enemies(dt, player)
            update_enemy_bullets(dt, player)

            # XP orbs
            update_xp_orbs(dt, player)
            for orb in xp_orbs[:]:
                if dist(orb.x, orb.y, player.x, player.y) < player.radius + orb.radius:
                    leveled = player.add_xp(orb.value)
                    player.kills += 0  # xp doesn't count kills
                    SFX["xp"].play()
                    xp_orbs.remove(orb)
                    if leveled:
                        state = "level_up"
                        level_choices = get_upgrade_choices(3)
                        break

            # Health pickups
            for hp_pu in health_pickups[:]:
                hp_pu.life -= dt
                if dist(hp_pu.x, hp_pu.y, player.x, player.y) < player.radius + hp_pu.radius:
                    player.heal(hp_pu.heal)
                    health_pickups.remove(hp_pu)
            health_pickups[:] = [h for h in health_pickups if h.life > 0]

            # Track kills (from enemies killed this frame)
            # We track via xp gained = proxy... let's just count directly
            # (already done in enemy death via alive flag - count here)

            # Count kills properly
            # We set e.alive = False on death, killed count via particles
            # Let's add a simpler approach: count killed enemies
            # Actually let's track in the enemy death handler above
            # For now do it via a frame counter
            # ... let's just increment kills in enemy death
            # We'll add it in update_enemies indirectly by checking before/after

            # Player death
            if player.hp <= 0:
                SFX["game_over"].play()
                state = "game_over"
                save_data["games_played"] = save_data.get("games_played", 0) + 1
                if wave_mgr.wave > save_data.get("best_wave", 0):
                    save_data["best_wave"] = wave_mgr.wave
                if player.kills > save_data.get("best_kills", 0):
                    save_data["best_kills"] = player.kills
                save_game(save_data)

            # Particles
            update_particles(dt)
            update_dmg_numbers(dt)
            update_shake(dt)

            # Camera
            target_cx = player.x - WIDTH / 2
            target_cy = player.y - HEIGHT / 2
            cam_x = lerp(cam_x, target_cx, min(1, 8 * dt))
            cam_y = lerp(cam_y, target_cy, min(1, 8 * dt))
            cam_x = max(0, min(ARENA_W - WIDTH, cam_x))
            cam_y = max(0, min(ARENA_H - HEIGHT, cam_y))

        # ── Draw ────────────────────────────────────────────────────
        if state == "menu":
            hover = ""
            play_rect, quit_rect = draw_main_menu(screen, save_data, "")
            if play_rect.collidepoint(mx, my): hover = "play"
            elif quit_rect.collidepoint(mx, my): hover = "quit"
            draw_main_menu(screen, save_data, hover)

        elif state in ("playing", "level_up"):
            sx, sy = get_shake_offset()
            draw_arena_bg(screen, cam_x + sx, cam_y + sy)
            draw_xp_orbs(screen, cam_x + sx, cam_y + sy)
            draw_health_pickups(screen, cam_x + sx, cam_y + sy)
            draw_bullets(screen, cam_x + sx, cam_y + sy)
            draw_enemies(screen, cam_x + sx, cam_y + sy)
            draw_particles(screen, cam_x + sx, cam_y + sy)
            player.draw(screen, cam_x + sx, cam_y + sy)
            draw_dmg_numbers(screen, cam_x + sx, cam_y + sy)
            draw_hud(screen, player, wave_mgr, game_time)

            # Wave announcement
            if not wave_mgr.wave_active and wave_mgr.inter_timer > 0 and wave_mgr.wave > 0:
                t = wave_mgr.inter_timer
                alpha = min(1, t / 1.5) * 255
                txt = font_lg.render(f"Wave {wave_mgr.wave} Clear!", True, GOLD)
                txt.set_alpha(int(alpha))
                screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 60))
                next_txt = font_sm.render(f"Next wave in {t:.0f}s", True, WHITE)
                next_txt.set_alpha(int(alpha))
                screen.blit(next_txt, (WIDTH // 2 - next_txt.get_width() // 2, HEIGHT // 2 - 20))

            if wave_mgr.wave_active and wave_mgr.spawned <= 3:
                txt = font_lg.render(f"Wave {wave_mgr.wave}", True, GOLD)
                txt.set_alpha(180)
                screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 80))

            if state == "level_up":
                # Check hover
                level_hover = -1
                for i, rect in enumerate(level_rects):
                    if rect.collidepoint(mx, my):
                        level_hover = i
                        break
                level_rects = draw_level_up(screen, level_choices, level_hover)

        elif state == "game_over":
            # Draw the game state behind the overlay
            draw_arena_bg(screen, cam_x, cam_y)
            draw_enemies(screen, cam_x, cam_y)
            player.draw(screen, cam_x, cam_y)

            hover = ""
            retry_rect, menu_rect = draw_game_over(screen, player, wave_mgr,
                                                    game_time, save_data, "")
            if retry_rect.collidepoint(mx, my): hover = "retry"
            elif menu_rect.collidepoint(mx, my): hover = "menu"
            draw_game_over(screen, player, wave_mgr, game_time, save_data, hover)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

# ── Kills tracking (patch into enemy death) ─────────────────────────────
# We need to track kills — let's patch update_enemies to count them
_original_update_enemies = update_enemies

def update_enemies_with_kills(dt, player):
    before = len(enemies)
    _original_update_enemies(dt, player)
    after = len(enemies)
    killed = before - after
    player.kills += killed

update_enemies = update_enemies_with_kills

if __name__ == "__main__":
    main()
