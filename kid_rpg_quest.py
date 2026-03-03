"""
STARLIGHT QUEST — A Kid-Friendly RPG with Undertale-Style Battles!
Ages 4+ and 7+ | No scary content, just silly fun!

You are a brave little Star Kid on a quest to bring back
the stolen Rainbow Crystal from the silly Grumble King!
Travel through cute biomes, meet wacky monsters,
and choose to FIGHT or make FRIENDS!

Controls:
  Arrow Keys / WASD — Move (overworld & dodge attacks)
  Z / SPACE — Confirm / Select
  X / ESC — Cancel / Back
  ENTER — Skip dialogue

Every monster can be befriended with ACT + MERCY!
"""

import pygame
import math
import random
import sys
import json
import os
import array
import time

# ── Mixer & Init ───────────────────────────────────────────────────────
pygame.mixer.pre_init(frequency=44100, size=-16, channels=1, buffer=512)
pygame.init()
pygame.mixer.quit()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

# ── Window ─────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 900, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("⭐ Starlight Quest ⭐")
clock = pygame.time.Clock()
FPS = 60

SAVE_FILE = "kid_rpg_save.json"

# ── Colours ────────────────────────────────────────────────────────────
BLACK       = (0, 0, 0)
WHITE       = (255, 255, 255)
RED         = (220, 60, 60)
GREEN       = (60, 200, 80)
BLUE        = (60, 130, 230)
YELLOW      = (255, 220, 60)
ORANGE      = (245, 165, 50)
PURPLE      = (160, 80, 220)
PINK        = (255, 130, 180)
CYAN        = (80, 220, 230)
BROWN       = (140, 95, 55)
GRAY        = (130, 130, 130)
DARK_GRAY   = (50, 50, 55)
LIGHT_GRAY  = (200, 200, 200)
GOLD        = (255, 215, 0)
SKY_BLUE    = (135, 200, 255)
GRASS_GREEN = (80, 180, 80)
DARK_GREEN  = (40, 120, 50)
SAND        = (230, 210, 160)
SNOW_WHITE  = (240, 245, 255)
ICE_BLUE    = (180, 220, 255)
LAVA_RED    = (200, 50, 30)
HEART_RED   = (255, 30, 30)
MAGIC_PURPLE= (200, 100, 255)
STAR_YELLOW = (255, 255, 100)

# Panel / UI
PANEL_BG    = (20, 20, 30)
MENU_BG     = (30, 20, 50)
BATTLE_BG   = (0, 0, 0)
HP_RED_BAR  = (200, 40, 40)
HP_GREEN_BAR= (60, 200, 60)
HP_YELLOW_BAR=(240, 200, 40)

# ── Fonts ──────────────────────────────────────────────────────────────
font_title  = pygame.font.SysFont("Segoe UI", 56, bold=True)
font_xl     = pygame.font.SysFont("Segoe UI", 40, bold=True)
font_lg     = pygame.font.SysFont("Segoe UI", 30, bold=True)
font_md     = pygame.font.SysFont("Segoe UI", 22, bold=True)
font_sm     = pygame.font.SysFont("Segoe UI", 18)
font_xs     = pygame.font.SysFont("Segoe UI", 14)
font_battle = pygame.font.SysFont("Segoe UI", 20, bold=True)
font_dmg    = pygame.font.SysFont("Segoe UI", 28, bold=True)

# ── SFX generation ─────────────────────────────────────────────────────
def _clamp(v):
    return max(-32767, min(32767, int(v)))

def _make_sound(samples_list):
    raw = array.array("h", [_clamp(s) for s in samples_list])
    return pygame.mixer.Sound(buffer=raw)

def sfx_confirm():
    sr = 44100; dur = 0.12; samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        v = math.sin(2 * math.pi * 800 * t) * 6000 * (1 - t / dur)
        v += math.sin(2 * math.pi * 1200 * t) * 3000 * (1 - t / dur)
        samples.append(v)
    snd = _make_sound(samples); snd.set_volume(0.35); return snd

def sfx_cancel():
    sr = 44100; dur = 0.1; samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        v = math.sin(2 * math.pi * 400 * t) * 5000 * (1 - t / dur)
        samples.append(v)
    snd = _make_sound(samples); snd.set_volume(0.3); return snd

def sfx_hit():
    sr = 44100; dur = 0.15; samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        v = math.sin(2 * math.pi * (300 - t * 1500) * t) * 8000 * (1 - t / dur)
        v += random.uniform(-2000, 2000) * (1 - t / dur)
        samples.append(v)
    snd = _make_sound(samples); snd.set_volume(0.35); return snd

def sfx_heal():
    sr = 44100; dur = 0.3; samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        v = math.sin(2 * math.pi * (500 + t * 800) * t) * 5000 * (1 - t / dur)
        v += math.sin(2 * math.pi * (700 + t * 600) * t) * 3000 * (1 - t / dur)
        samples.append(v)
    snd = _make_sound(samples); snd.set_volume(0.3); return snd

def sfx_dodge():
    sr = 44100; dur = 0.08; samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        v = math.sin(2 * math.pi * 1200 * t) * 4000 * (1 - t / dur)
        samples.append(v)
    snd = _make_sound(samples); snd.set_volume(0.25); return snd

def sfx_level_up():
    sr = 44100; dur = 0.5; samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        freq = 400 + t * 1200
        v = math.sin(2 * math.pi * freq * t) * 6000 * max(0, 1 - t / dur)
        v += math.sin(2 * math.pi * freq * 1.5 * t) * 3000 * max(0, 1 - t / dur)
        samples.append(v)
    snd = _make_sound(samples); snd.set_volume(0.35); return snd

def sfx_mercy():
    sr = 44100; dur = 0.4; samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        v = math.sin(2 * math.pi * 600 * t) * 4000 * max(0, 1 - t / dur)
        v += math.sin(2 * math.pi * 900 * t) * 3000 * max(0, 1 - t / dur)
        v += math.sin(2 * math.pi * 1200 * t) * 2000 * max(0, 1 - t / dur)
        samples.append(v)
    snd = _make_sound(samples); snd.set_volume(0.3); return snd

def sfx_encounter():
    sr = 44100; dur = 0.3; samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        v = math.sin(2 * math.pi * 200 * t) * 7000 * (1 - t / dur)
        v += random.uniform(-3000, 3000) * max(0, 0.5 - t / dur)
        samples.append(v)
    snd = _make_sound(samples); snd.set_volume(0.35); return snd

def sfx_step():
    sr = 44100; dur = 0.05; samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        v = random.uniform(-2000, 2000) * (1 - t / dur)
        samples.append(v)
    snd = _make_sound(samples); snd.set_volume(0.15); return snd

def sfx_sparkle():
    sr = 44100; dur = 0.25; samples = []
    for i in range(int(sr * dur)):
        t = i / sr
        v = math.sin(2 * math.pi * (1000 + t * 2000) * t) * 3000 * (1 - t / dur)
        v += math.sin(2 * math.pi * (1500 + t * 1000) * t) * 2000 * (1 - t / dur)
        samples.append(v)
    snd = _make_sound(samples); snd.set_volume(0.25); return snd

# Pre-generate SFX
SFX_CONFIRM   = sfx_confirm()
SFX_CANCEL    = sfx_cancel()
SFX_HIT       = sfx_hit()
SFX_HEAL      = sfx_heal()
SFX_DODGE     = sfx_dodge()
SFX_LEVEL_UP  = sfx_level_up()
SFX_MERCY     = sfx_mercy()
SFX_ENCOUNTER = sfx_encounter()
SFX_STEP      = sfx_step()
SFX_SPARKLE   = sfx_sparkle()

# ═══════════════════════════════════════════════════════════════════════
#  GAME DATA
# ═══════════════════════════════════════════════════════════════════════

# ── Items ──────────────────────────────────────────────────────────────
ITEMS = {
    "Star Cookie":    {"type": "heal", "value": 15, "desc": "A cookie shaped like a star! Heals 15 HP.", "color": STAR_YELLOW},
    "Rainbow Juice":  {"type": "heal", "value": 30, "desc": "Sparkly juice! Heals 30 HP.", "color": MAGIC_PURPLE},
    "Moon Candy":     {"type": "heal", "value": 50, "desc": "Glowing candy from the moon! Heals 50 HP.", "color": ICE_BLUE},
    "Hug Bandage":    {"type": "heal", "value": 20, "desc": "A warm hug in bandage form! Heals 20 HP.", "color": PINK},
    "Golden Apple":   {"type": "heal", "value": 80, "desc": "A legendary golden apple! Heals 80 HP.", "color": GOLD},
    "Silly Hat":      {"type": "act_boost", "value": 1, "desc": "Monsters find it hilarious!", "color": ORANGE},
    "Friendship Bracelet": {"type": "act_boost", "value": 2, "desc": "Shows you want to be friends!", "color": CYAN},
    "Power Star":     {"type": "atk_boost", "value": 5, "desc": "Boosts ATK by 5 for this fight!", "color": YELLOW},
}

# ── Monster definitions ────────────────────────────────────────────────
class MonsterDef:
    def __init__(self, name, hp, atk, defense, xp, gold, color, flavor,
                 act_options, spare_threshold, attacks, sprite_fn, boss=False):
        self.name = name
        self.hp = hp
        self.atk = atk
        self.defense = defense
        self.xp = xp
        self.gold = gold
        self.color = color
        self.flavor = flavor          # opening text
        self.act_options = act_options  # list of (name, text, mercy_gain)
        self.spare_threshold = spare_threshold  # mercy needed to spare
        self.attacks = attacks         # list of attack pattern names
        self.sprite_fn = sprite_fn     # function to draw the sprite
        self.boss = boss

# ── Sprite drawing helpers ─────────────────────────────────────────────
def draw_slime(surf, x, y, color, t):
    """Cute bouncing slime"""
    bounce = math.sin(t * 3) * 5
    # Body
    pygame.draw.ellipse(surf, color, (x - 30, y - 25 + bounce, 60, 50))
    # Shine
    pygame.draw.ellipse(surf, WHITE, (x - 12, y - 18 + bounce, 12, 10))
    # Eyes
    ey = y - 8 + bounce
    pygame.draw.circle(surf, WHITE, (x - 10, int(ey)), 7)
    pygame.draw.circle(surf, WHITE, (x + 10, int(ey)), 7)
    pygame.draw.circle(surf, BLACK, (x - 8, int(ey + 1)), 4)
    pygame.draw.circle(surf, BLACK, (x + 12, int(ey + 1)), 4)
    # Mouth
    pygame.draw.arc(surf, BLACK, (x - 8, int(ey + 5), 16, 10), 3.14, 6.28, 2)

def draw_mushroom(surf, x, y, color, t):
    """Cute mushroom creature"""
    sway = math.sin(t * 2) * 3
    # Stem
    pygame.draw.rect(surf, (220, 200, 170), (x - 12 + sway, y - 5, 24, 30))
    # Cap
    pygame.draw.ellipse(surf, color, (x - 28 + sway, y - 35, 56, 35))
    # Spots
    for sx, sy in [(-12, -22), (8, -25), (0, -15)]:
        pygame.draw.circle(surf, WHITE, (x + sx + sway, y + sy), 5)
    # Eyes
    ey = y + 5
    pygame.draw.circle(surf, BLACK, (x - 6 + sway, ey), 3)
    pygame.draw.circle(surf, BLACK, (x + 6 + sway, ey), 3)
    # Smile
    pygame.draw.arc(surf, BLACK, (x - 6 + sway, ey + 2, 12, 8), 3.14, 6.28, 2)

def draw_cloud(surf, x, y, color, t):
    """Fluffy cloud monster"""
    bob = math.sin(t * 1.5) * 8
    cy = y + bob
    for ox, oy, r in [(-18, 0, 20), (0, -8, 25), (18, 0, 20), (0, 8, 18)]:
        pygame.draw.circle(surf, color, (x + ox, int(cy + oy)), r)
    # Face
    pygame.draw.circle(surf, BLACK, (x - 8, int(cy - 2)), 3)
    pygame.draw.circle(surf, BLACK, (x + 8, int(cy - 2)), 3)
    pygame.draw.ellipse(surf, BLACK, (x - 5, int(cy + 5), 10, 6))

def draw_flower(surf, x, y, color, t):
    """Happy flower"""
    sway = math.sin(t * 2.5) * 4
    # Stem
    pygame.draw.line(surf, DARK_GREEN, (x + sway, y + 25), (x, y + 55), 4)
    # Leaves
    pygame.draw.ellipse(surf, GREEN, (x - 15, y + 35, 18, 8))
    pygame.draw.ellipse(surf, GREEN, (x + 5, y + 40, 18, 8))
    # Petals
    for angle in range(0, 360, 60):
        px = x + sway + math.cos(math.radians(angle)) * 20
        py = y - 5 + math.sin(math.radians(angle)) * 20
        pygame.draw.circle(surf, color, (int(px), int(py)), 10)
    # Center
    pygame.draw.circle(surf, YELLOW, (x + sway, y - 5), 12)
    # Face
    pygame.draw.circle(surf, BLACK, (x - 4 + sway, y - 8), 2)
    pygame.draw.circle(surf, BLACK, (x + 4 + sway, y - 8), 2)
    pygame.draw.arc(surf, BLACK, (x - 5 + sway, y - 4, 10, 8), 3.14, 6.28, 2)

def draw_snowman(surf, x, y, color, t):
    """Cute snowman"""
    wobble = math.sin(t * 2) * 2
    # Body
    pygame.draw.circle(surf, color, (x + wobble, y + 15), 22)
    pygame.draw.circle(surf, color, (x + wobble, y - 10), 17)
    pygame.draw.circle(surf, color, (x + wobble, y - 30), 13)
    # Hat
    pygame.draw.rect(surf, PURPLE, (x - 12 + wobble, y - 48, 24, 18))
    pygame.draw.rect(surf, PURPLE, (x - 16 + wobble, y - 33, 32, 5))
    # Eyes
    pygame.draw.circle(surf, BLACK, (x - 5 + wobble, y - 32), 2)
    pygame.draw.circle(surf, BLACK, (x + 5 + wobble, y - 32), 2)
    # Carrot nose
    pygame.draw.polygon(surf, ORANGE, [(x + wobble, y - 28), (x + 12 + wobble, y - 26), (x + wobble, y - 24)])
    # Buttons
    for by in [y - 5, y + 5, y + 15]:
        pygame.draw.circle(surf, BLACK, (x + wobble, by), 3)

def draw_ghost(surf, x, y, color, t):
    """Friendly ghost"""
    bob = math.sin(t * 2) * 6
    cy = y + bob
    # Body
    pygame.draw.ellipse(surf, color, (x - 22, int(cy - 30), 44, 45))
    # Wavy bottom
    for i in range(5):
        wave = math.sin(t * 3 + i) * 3
        bx = x - 20 + i * 10
        pygame.draw.circle(surf, color, (bx, int(cy + 12 + wave)), 7)
    # Eyes (cute)
    pygame.draw.circle(surf, BLACK, (x - 8, int(cy - 12)), 5)
    pygame.draw.circle(surf, BLACK, (x + 8, int(cy - 12)), 5)
    pygame.draw.circle(surf, WHITE, (x - 6, int(cy - 14)), 2)
    pygame.draw.circle(surf, WHITE, (x + 10, int(cy - 14)), 2)
    # Mouth
    pygame.draw.ellipse(surf, BLACK, (x - 4, int(cy), 8, 6))

def draw_dragon(surf, x, y, color, t):
    """Cute baby dragon"""
    bob = math.sin(t * 1.8) * 4
    cy = y + bob
    # Body
    pygame.draw.ellipse(surf, color, (x - 25, int(cy - 15), 50, 40))
    # Head
    pygame.draw.circle(surf, color, (x, int(cy - 28)), 18)
    # Horns
    pygame.draw.polygon(surf, GOLD, [(x - 10, int(cy - 42)), (x - 8, int(cy - 55)), (x - 4, int(cy - 42))])
    pygame.draw.polygon(surf, GOLD, [(x + 4, int(cy - 42)), (x + 8, int(cy - 55)), (x + 10, int(cy - 42))])
    # Wings
    wing_flap = math.sin(t * 4) * 10
    pygame.draw.polygon(surf, (*[max(0, c - 40) for c in color],),
                        [(x - 25, int(cy - 10)), (x - 50, int(cy - 30 + wing_flap)), (x - 20, int(cy + 5))])
    pygame.draw.polygon(surf, (*[max(0, c - 40) for c in color],),
                        [(x + 25, int(cy - 10)), (x + 50, int(cy - 30 + wing_flap)), (x + 20, int(cy + 5))])
    # Eyes
    pygame.draw.circle(surf, WHITE, (x - 7, int(cy - 30)), 5)
    pygame.draw.circle(surf, WHITE, (x + 7, int(cy - 30)), 5)
    pygame.draw.circle(surf, BLACK, (x - 6, int(cy - 29)), 3)
    pygame.draw.circle(surf, BLACK, (x + 8, int(cy - 29)), 3)
    # Smile
    pygame.draw.arc(surf, BLACK, (x - 6, int(cy - 23), 12, 8), 3.14, 6.28, 2)
    # Tail
    tail_wag = math.sin(t * 3) * 8
    pygame.draw.line(surf, color, (x + 22, int(cy + 10)), (x + 40, int(cy + 5 + tail_wag)), 4)

def draw_grumble_king(surf, x, y, color, t):
    """The final boss — Grumble King (a big grumpy but cute creature)"""
    bob = math.sin(t * 1.2) * 3
    cy = y + bob
    # Big body
    pygame.draw.ellipse(surf, color, (x - 45, int(cy - 25), 90, 65))
    # Head
    pygame.draw.circle(surf, color, (x, int(cy - 40)), 30)
    # Crown
    crown_pts = [(x - 22, int(cy - 65)), (x - 15, int(cy - 80)), (x - 8, int(cy - 65)),
                 (x, int(cy - 82)), (x + 8, int(cy - 65)),
                 (x + 15, int(cy - 80)), (x + 22, int(cy - 65))]
    pygame.draw.polygon(surf, GOLD, crown_pts)
    pygame.draw.polygon(surf, YELLOW, crown_pts, 2)
    # Crown jewel
    pygame.draw.circle(surf, RED, (x, int(cy - 73)), 4)
    # Grumpy eyebrows
    pygame.draw.line(surf, BLACK, (x - 18, int(cy - 52)), (x - 8, int(cy - 48)), 3)
    pygame.draw.line(surf, BLACK, (x + 8, int(cy - 48)), (x + 18, int(cy - 52)), 3)
    # Eyes
    pygame.draw.circle(surf, WHITE, (x - 12, int(cy - 42)), 7)
    pygame.draw.circle(surf, WHITE, (x + 12, int(cy - 42)), 7)
    pygame.draw.circle(surf, BLACK, (x - 10, int(cy - 41)), 4)
    pygame.draw.circle(surf, BLACK, (x + 14, int(cy - 41)), 4)
    # Pouty mouth
    pygame.draw.arc(surf, BLACK, (x - 10, int(cy - 32), 20, 10), 0, 3.14, 3)
    # Arms
    arm_swing = math.sin(t * 2) * 8
    pygame.draw.line(surf, color, (x - 42, int(cy)), (x - 55, int(cy - 15 + arm_swing)), 8)
    pygame.draw.line(surf, color, (x + 42, int(cy)), (x + 55, int(cy - 15 - arm_swing)), 8)
    # Feet
    pygame.draw.ellipse(surf, (*[max(0, c - 30) for c in color],), (x - 30, int(cy + 30), 25, 12))
    pygame.draw.ellipse(surf, (*[max(0, c - 30) for c in color],), (x + 5, int(cy + 30), 25, 12))

def draw_bunny(surf, x, y, color, t):
    """Cute bunny"""
    hop = abs(math.sin(t * 3)) * 8
    cy = y - hop
    # Body
    pygame.draw.ellipse(surf, color, (x - 18, int(cy - 5), 36, 30))
    # Head
    pygame.draw.circle(surf, color, (x, int(cy - 18)), 15)
    # Ears
    ear_twitch = math.sin(t * 4) * 3
    pygame.draw.ellipse(surf, color, (x - 12, int(cy - 50 + ear_twitch), 10, 28))
    pygame.draw.ellipse(surf, PINK, (x - 10, int(cy - 46 + ear_twitch), 6, 20))
    pygame.draw.ellipse(surf, color, (x + 2, int(cy - 52), 10, 28))
    pygame.draw.ellipse(surf, PINK, (x + 4, int(cy - 48), 6, 20))
    # Eyes
    pygame.draw.circle(surf, BLACK, (x - 6, int(cy - 20)), 3)
    pygame.draw.circle(surf, BLACK, (x + 6, int(cy - 20)), 3)
    # Nose
    pygame.draw.circle(surf, PINK, (x, int(cy - 15)), 2)
    # Tail
    pygame.draw.circle(surf, WHITE, (x + 16, int(cy + 10)), 6)

def draw_robot(surf, x, y, color, t):
    """Cute robot"""
    jitter = math.sin(t * 8) * 1
    # Body
    pygame.draw.rect(surf, color, (x - 20, int(y - 10 + jitter), 40, 35))
    # Head
    pygame.draw.rect(surf, color, (x - 15, int(y - 35 + jitter), 30, 25))
    # Antenna
    pygame.draw.line(surf, GRAY, (x, int(y - 35 + jitter)), (x, int(y - 48 + jitter)), 2)
    blink = (math.sin(t * 5) > 0)
    pygame.draw.circle(surf, RED if blink else YELLOW, (x, int(y - 48 + jitter)), 4)
    # Eyes (LED)
    pygame.draw.rect(surf, GREEN if blink else CYAN, (x - 10, int(y - 30 + jitter), 7, 5))
    pygame.draw.rect(surf, GREEN if blink else CYAN, (x + 3, int(y - 30 + jitter), 7, 5))
    # Mouth
    pygame.draw.rect(surf, DARK_GRAY, (x - 8, int(y - 20 + jitter), 16, 4))
    for mx in range(-6, 8, 4):
        pygame.draw.rect(surf, GREEN, (x + mx, int(y - 20 + jitter), 2, 4))
    # Arms
    pygame.draw.rect(surf, GRAY, (x - 28, int(y - 5 + jitter), 8, 20))
    pygame.draw.rect(surf, GRAY, (x + 20, int(y - 5 + jitter), 8, 20))
    # Legs
    pygame.draw.rect(surf, GRAY, (x - 15, int(y + 25 + jitter), 10, 12))
    pygame.draw.rect(surf, GRAY, (x + 5, int(y + 25 + jitter), 10, 12))

# ── Monster definitions for each biome ─────────────────────────────────
MONSTERS_BY_ZONE = {
    "Sunny Meadow": [
        MonsterDef("Wobble Slime", 28, 4, 1, 8, 5, GREEN,
                   "* A cute green slime wobbles toward you!",
                   [("Poke", "You poke the slime. It giggles!", 35),
                    ("Dance", "You do a silly dance. The slime bounces along!", 50),
                    ("Compliment", "\"You're the wobbliest!\" The slime blushes.", 40)],
                   80, ["slow_bounce", "zigzag"], draw_slime),
        MonsterDef("Giggly Flower", 22, 3, 0, 6, 4, PINK,
                   "* A flower pops up and waves its petals!",
                   [("Smell", "You sniff the flower. Ahh, nice!", 35),
                    ("Water", "You give it water. It grows happy!", 50),
                    ("Sing", "You sing a song. Its petals sway!", 40)],
                   80, ["petal_toss", "spiral"], draw_flower),
        MonsterDef("Fluff Bunny", 25, 5, 1, 10, 6, (240, 200, 220),
                   "* A fluffy bunny hops into your path!",
                   [("Pet", "You pet the bunny. So soft!", 40),
                    ("Carrot", "You offer a carrot. It's delighted!", 50),
                    ("Hop", "You hop together! How fun!", 35)],
                   80, ["hop_attack", "carrot_rain"], draw_bunny),
    ],
    "Mushroom Forest": [
        MonsterDef("Sporeling", 35, 6, 2, 14, 8, (180, 120, 70),
                   "* A little mushroom waddles up to you!",
                   [("Hat", "You admire its cap. It blushes!", 30),
                    ("Share", "You share a snack. It's grateful!", 45),
                    ("Umbrella", "You use it as an umbrella. It giggles!", 50)],
                   85, ["spore_cloud", "bouncing_caps"], draw_mushroom),
        MonsterDef("Mist Ghost", 30, 7, 1, 16, 10, (200, 200, 240),
                   "* A friendly ghost says \"Boo!\" then giggles!",
                   [("Wave", "You wave. The ghost waves back!", 35),
                    ("Peek-a-boo", "You play peek-a-boo! It loves it!", 50),
                    ("Story", "You tell a story. It listens intently!", 40)],
                   85, ["ghost_spiral", "fade_chase"], draw_ghost),
    ],
    "Snowy Peaks": [
        MonsterDef("Snowpal", 40, 7, 3, 18, 12, SNOW_WHITE,
                   "* A little snowman slides up to you!",
                   [("Scarf", "You offer a scarf. It's warm now!", 35),
                    ("Snowball", "You have a snowball fight! Fun!", 45),
                    ("Hug", "You give a warm hug. It doesn't melt!", 50)],
                   85, ["snowball_barrage", "icicle_drop"], draw_snowman),
        MonsterDef("Frost Cloud", 35, 8, 2, 20, 14, ICE_BLUE,
                   "* A chilly cloud drifts by and notices you!",
                   [("Blow", "You blow warm air. It likes the warmth!", 40),
                    ("Catch", "You catch snowflakes it makes! Pretty!", 45),
                    ("Draw", "You draw a picture of it. Adorable!", 40)],
                   85, ["snow_spiral", "freeze_wave"], draw_cloud),
    ],
    "Robot Factory": [
        MonsterDef("Beep Bot", 45, 9, 4, 24, 16, CYAN,
                   "* A little robot rolls up! Beep boop!",
                   [("Fix", "You tighten a loose screw. Thanks!", 35),
                    ("Dance", "You do the robot dance! It copies you!", 50),
                    ("Charge", "You share your battery pack. Bzzz!", 40)],
                   90, ["laser_grid", "gear_spin"], draw_robot),
    ],
    "Dragon's Roost": [
        MonsterDef("Baby Dragon", 55, 10, 3, 30, 20, (240, 120, 60),
                   "* A baby dragon flaps its tiny wings at you!",
                   [("Tickle", "You tickle its belly! It purrs!", 30),
                    ("Toy", "You share a toy. It plays happily!", 40),
                    ("Fly", "You pretend to fly together! Wheee!", 55)],
                   90, ["fire_breath", "wing_gust"], draw_dragon),
    ],
    "Grumble Castle": [
        MonsterDef("Grumble King", 120, 12, 5, 100, 50, PURPLE,
                   "* The Grumble King blocks your path!\n* \"Nobody takes MY Rainbow Crystal!\"",
                   [("Joke", "You tell a joke. He almost smiles!", 15),
                    ("Compliment", "\"Nice crown!\" He looks proud!", 20),
                    ("Gift", "You offer a friendship bracelet!", 25),
                    ("Hug", "You try to hug him. He's confused!", 30)],
                   100, ["crown_toss", "grumble_slam", "rainbow_chaos"], draw_grumble_king, boss=True),
    ],
}

# ── Zone / Map definitions ─────────────────────────────────────────────
ZONES = [
    {"name": "Sunny Meadow", "bg": GRASS_GREEN, "tile": (100, 200, 100), "tile2": (90, 180, 90),
     "desc": "A bright, happy meadow full of flowers!", "encounters": 3,
     "items": ["Star Cookie", "Star Cookie", "Hug Bandage"]},
    {"name": "Mushroom Forest", "bg": (60, 80, 50), "tile": (80, 100, 60), "tile2": (70, 90, 55),
     "desc": "A misty forest with giant mushrooms!", "encounters": 3,
     "items": ["Star Cookie", "Rainbow Juice", "Silly Hat"]},
    {"name": "Snowy Peaks", "bg": (180, 210, 240), "tile": (210, 225, 240), "tile2": (195, 215, 235),
     "desc": "Frosty mountains sparkling with snow!", "encounters": 3,
     "items": ["Rainbow Juice", "Hug Bandage", "Friendship Bracelet"]},
    {"name": "Robot Factory", "bg": (50, 55, 65), "tile": (70, 75, 85), "tile2": (60, 65, 75),
     "desc": "A friendly robot factory! Beep boop!", "encounters": 3,
     "items": ["Moon Candy", "Power Star", "Rainbow Juice"]},
    {"name": "Dragon's Roost", "bg": (100, 60, 40), "tile": (120, 80, 55), "tile2": (110, 70, 50),
     "desc": "A warm cave with a sleepy baby dragon!", "encounters": 2,
     "items": ["Moon Candy", "Golden Apple"]},
    {"name": "Grumble Castle", "bg": (40, 30, 55), "tile": (60, 50, 75), "tile2": (55, 45, 70),
     "desc": "The Grumble King's castle! The final challenge!", "encounters": 1,
     "items": ["Golden Apple"]},
]

# ── Overworld map tile size ────────────────────────────────────────────
OW_TILE = 48
OW_MAP_W, OW_MAP_H = 18, 14

# ═══════════════════════════════════════════════════════════════════════
#  ATTACK PATTERNS (Undertale-style bullet dodging)
# ═══════════════════════════════════════════════════════════════════════
class Bullet:
    def __init__(self, x, y, vx, vy, radius=5, color=WHITE, shape="circle", lifetime=300):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.color = color
        self.shape = shape
        self.lifetime = lifetime
        self.age = 0

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.age += 1
        return self.age < self.lifetime

    def draw(self, surf, box_rect):
        ix, iy = int(self.x), int(self.y)
        if self.shape == "circle":
            pygame.draw.circle(surf, self.color, (ix, iy), self.radius)
        elif self.shape == "star":
            pts = []
            for i in range(5):
                a = math.radians(i * 72 - 90)
                pts.append((ix + math.cos(a) * self.radius, iy + math.sin(a) * self.radius))
                a2 = math.radians(i * 72 + 36 - 90)
                pts.append((ix + math.cos(a2) * self.radius * 0.4, iy + math.sin(a2) * self.radius * 0.4))
            pygame.draw.polygon(surf, self.color, pts)
        elif self.shape == "diamond":
            pts = [(ix, iy - self.radius), (ix + self.radius, iy),
                   (ix, iy + self.radius), (ix - self.radius, iy)]
            pygame.draw.polygon(surf, self.color, pts)
        elif self.shape == "rect":
            pygame.draw.rect(surf, self.color, (ix - self.radius, iy - self.radius,
                                                 self.radius * 2, self.radius * 2))

    def collides_heart(self, hx, hy, hr=8):
        dx = self.x - hx
        dy = self.y - hy
        return (dx * dx + dy * dy) < (self.radius + hr) ** 2


def generate_attack(pattern_name, box_rect, difficulty=1.0, t=0):
    """Generate bullets for a given attack pattern inside the battle box."""
    bullets = []
    bx, by, bw, bh = box_rect
    cx = bx + bw // 2
    cy = by + bh // 2

    speed_mult = 0.6 + difficulty * 0.3  # scales with monster strength

    if pattern_name == "slow_bounce":
        for i in range(4 + int(difficulty * 2)):
            angle = random.uniform(0, math.pi * 2)
            spd = random.uniform(1, 2) * speed_mult
            bullets.append(Bullet(
                bx + random.randint(10, bw - 10),
                by + 5,
                math.cos(angle) * spd,
                math.sin(angle) * spd + 0.5,
                radius=6, color=GREEN, shape="circle"))

    elif pattern_name == "zigzag":
        for i in range(3 + int(difficulty * 2)):
            side = random.choice([bx + 5, bx + bw - 5])
            bullets.append(Bullet(
                side, by + random.randint(20, bh - 20),
                (2 if side == bx + 5 else -2) * speed_mult,
                math.sin(i) * 1.5 * speed_mult,
                radius=5, color=YELLOW, shape="diamond"))

    elif pattern_name == "petal_toss":
        for i in range(5 + int(difficulty * 2)):
            angle = (i / (5 + int(difficulty * 2))) * math.pi * 2
            bullets.append(Bullet(
                cx, cy - 30,
                math.cos(angle + t) * 1.5 * speed_mult,
                math.sin(angle + t) * 1.5 * speed_mult + 0.3,
                radius=6, color=PINK, shape="circle"))

    elif pattern_name == "spiral":
        for i in range(6 + int(difficulty * 2)):
            angle = t + (i / 8) * math.pi * 2
            bullets.append(Bullet(
                cx, cy,
                math.cos(angle) * 2 * speed_mult,
                math.sin(angle) * 2 * speed_mult,
                radius=5, color=MAGIC_PURPLE, shape="star"))

    elif pattern_name == "hop_attack":
        for i in range(4 + int(difficulty)):
            bullets.append(Bullet(
                bx + random.randint(10, bw - 10), by + 5,
                random.uniform(-0.5, 0.5) * speed_mult,
                random.uniform(1, 2.5) * speed_mult,
                radius=7, color=ORANGE, shape="circle"))

    elif pattern_name == "carrot_rain":
        for i in range(5 + int(difficulty * 2)):
            bullets.append(Bullet(
                bx + random.randint(10, bw - 10), by + 5,
                0, random.uniform(1, 2) * speed_mult,
                radius=5, color=ORANGE, shape="diamond"))

    elif pattern_name == "spore_cloud":
        for i in range(6 + int(difficulty * 2)):
            angle = random.uniform(0, math.pi * 2)
            spd = random.uniform(0.5, 1.5) * speed_mult
            bullets.append(Bullet(
                cx + random.randint(-30, 30), cy + random.randint(-30, 30),
                math.cos(angle) * spd, math.sin(angle) * spd,
                radius=4, color=BROWN, shape="circle", lifetime=200))

    elif pattern_name == "bouncing_caps":
        for i in range(4 + int(difficulty)):
            bullets.append(Bullet(
                bx + random.randint(10, bw - 10), by + bh - 5,
                random.uniform(-1, 1) * speed_mult,
                random.uniform(-2.5, -1) * speed_mult,
                radius=8, color=(180, 120, 70), shape="circle"))

    elif pattern_name == "ghost_spiral":
        for i in range(8 + int(difficulty * 2)):
            angle = (i / 10) * math.pi * 2 + t
            r = 10 + i * 5
            bullets.append(Bullet(
                cx + math.cos(angle) * r, cy + math.sin(angle) * r,
                math.cos(angle + 1.57) * 1.2 * speed_mult,
                math.sin(angle + 1.57) * 1.2 * speed_mult,
                radius=5, color=(200, 200, 240), shape="circle", lifetime=180))

    elif pattern_name == "fade_chase":
        for i in range(3 + int(difficulty)):
            bullets.append(Bullet(
                random.choice([bx + 5, bx + bw - 5]),
                by + random.randint(20, bh - 20),
                random.choice([-1.5, 1.5]) * speed_mult,
                random.uniform(-0.5, 0.5) * speed_mult,
                radius=6, color=(180, 180, 220), shape="diamond", lifetime=220))

    elif pattern_name == "snowball_barrage":
        for i in range(5 + int(difficulty * 2)):
            bullets.append(Bullet(
                bx + random.randint(10, bw - 10), by + 5,
                random.uniform(-0.8, 0.8) * speed_mult,
                random.uniform(1.5, 3) * speed_mult,
                radius=7, color=WHITE, shape="circle"))

    elif pattern_name == "icicle_drop":
        for i in range(4 + int(difficulty * 2)):
            bullets.append(Bullet(
                bx + (i + 1) * bw // (5 + int(difficulty * 2)),
                by + 5,
                0, random.uniform(1.5, 2.5) * speed_mult,
                radius=5, color=ICE_BLUE, shape="diamond"))

    elif pattern_name == "snow_spiral":
        for i in range(6 + int(difficulty * 2)):
            angle = t * 0.5 + (i / 8) * math.pi * 2
            bullets.append(Bullet(
                cx, cy,
                math.cos(angle) * 1.8 * speed_mult,
                math.sin(angle) * 1.8 * speed_mult,
                radius=5, color=SNOW_WHITE, shape="star"))

    elif pattern_name == "freeze_wave":
        y_pos = by + random.randint(20, bh - 20)
        for i in range(6 + int(difficulty * 2)):
            bullets.append(Bullet(
                bx + 5, y_pos + i * 8 - 20,
                2 * speed_mult, 0,
                radius=4, color=ICE_BLUE, shape="rect"))

    elif pattern_name == "laser_grid":
        for i in range(3 + int(difficulty)):
            # Horizontal
            bullets.append(Bullet(
                bx + 5, by + random.randint(15, bh - 15),
                2.5 * speed_mult, 0,
                radius=4, color=RED, shape="rect"))
            # Vertical
            bullets.append(Bullet(
                bx + random.randint(15, bw - 15), by + 5,
                0, 2.5 * speed_mult,
                radius=4, color=RED, shape="rect"))

    elif pattern_name == "gear_spin":
        for i in range(8 + int(difficulty * 2)):
            angle = (i / 10) * math.pi * 2
            bullets.append(Bullet(
                cx, cy,
                math.cos(angle) * 2 * speed_mult,
                math.sin(angle) * 2 * speed_mult,
                radius=6, color=GRAY, shape="rect"))

    elif pattern_name == "fire_breath":
        for i in range(6 + int(difficulty * 3)):
            angle = random.uniform(-0.5, 0.5)
            spd = random.uniform(2, 3.5) * speed_mult
            bullets.append(Bullet(
                cx, by + 10,
                math.sin(angle) * spd,
                math.cos(angle) * spd,
                radius=6, color=ORANGE, shape="circle"))

    elif pattern_name == "wing_gust":
        for i in range(5 + int(difficulty * 2)):
            side = random.choice([bx + 5, bx + bw - 5])
            bullets.append(Bullet(
                side, by + random.randint(15, bh - 15),
                (3 if side == bx + 5 else -3) * speed_mult, 0,
                radius=5, color=YELLOW, shape="diamond"))

    elif pattern_name == "crown_toss":
        for i in range(6 + int(difficulty * 2)):
            angle = (i / 8) * math.pi * 2 + t * 0.3
            bullets.append(Bullet(
                cx, by + 20,
                math.cos(angle) * 2.5 * speed_mult,
                abs(math.sin(angle)) * 2 * speed_mult + 0.5,
                radius=7, color=GOLD, shape="star"))

    elif pattern_name == "grumble_slam":
        for i in range(8 + int(difficulty * 3)):
            bullets.append(Bullet(
                bx + random.randint(10, bw - 10), by + 5,
                random.uniform(-1, 1) * speed_mult,
                random.uniform(2, 4) * speed_mult,
                radius=8, color=PURPLE, shape="circle"))

    elif pattern_name == "rainbow_chaos":
        colors = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK]
        for i in range(10 + int(difficulty * 3)):
            angle = random.uniform(0, math.pi * 2)
            spd = random.uniform(1.5, 3) * speed_mult
            bullets.append(Bullet(
                cx + random.randint(-40, 40), cy + random.randint(-40, 40),
                math.cos(angle) * spd, math.sin(angle) * spd,
                radius=5, color=random.choice(colors),
                shape=random.choice(["circle", "star", "diamond"])))

    return bullets


# ═══════════════════════════════════════════════════════════════════════
#  PLAYER
# ═══════════════════════════════════════════════════════════════════════
class Player:
    def __init__(self):
        self.name = "Star Kid"
        self.level = 1
        self.xp = 0
        self.xp_next = 20
        self.max_hp = 50
        self.hp = 50
        self.atk = 8
        self.defense = 2
        self.gold = 0
        self.inventory = ["Star Cookie", "Star Cookie", "Star Cookie"]
        self.max_inventory = 12
        self.friends_made = 0
        self.monsters_fought = 0
        self.zone_index = 0
        self.zone_encounters_left = ZONES[0]["encounters"]
        self.x = 4
        self.y = 4
        self.facing = "down"
        self.step_timer = 0

    def gain_xp(self, amount):
        self.xp += amount
        leveled = False
        while self.xp >= self.xp_next:
            self.xp -= self.xp_next
            self.level += 1
            self.xp_next = int(self.xp_next * 1.5)
            self.max_hp += 10
            self.hp = self.max_hp
            self.atk += 2
            self.defense += 1
            leveled = True
        return leveled

    def add_item(self, item_name):
        if len(self.inventory) < self.max_inventory:
            self.inventory.append(item_name)
            return True
        return False

    def to_dict(self):
        return {
            "name": self.name, "level": self.level, "xp": self.xp,
            "xp_next": self.xp_next, "max_hp": self.max_hp, "hp": self.hp,
            "atk": self.atk, "defense": self.defense, "gold": self.gold,
            "inventory": self.inventory, "friends_made": self.friends_made,
            "monsters_fought": self.monsters_fought, "zone_index": self.zone_index,
            "zone_encounters_left": self.zone_encounters_left,
            "x": self.x, "y": self.y,
        }

    def from_dict(self, d):
        for k, v in d.items():
            if hasattr(self, k):
                setattr(self, k, v)
        self.max_inventory = 12

    def draw_overworld(self, surf, ox, oy, t):
        """Draw the player character on the overworld."""
        px = ox + self.x * OW_TILE + OW_TILE // 2
        py = oy + self.y * OW_TILE + OW_TILE // 2
        bob = math.sin(t * 5) * 2

        # Body (star shape!)
        body_color = STAR_YELLOW
        head_y = py - 12 + bob
        # Star body
        r = 14
        pts = []
        for i in range(5):
            a = math.radians(i * 72 - 90)
            pts.append((px + math.cos(a) * r, head_y + math.sin(a) * r))
            a2 = math.radians(i * 72 + 36 - 90)
            pts.append((px + math.cos(a2) * r * 0.45, head_y + math.sin(a2) * r * 0.45))
        pygame.draw.polygon(surf, body_color, pts)
        pygame.draw.polygon(surf, ORANGE, pts, 2)

        # Face
        ey = head_y + 1
        # Eyes depend on facing
        if self.facing == "down" or self.facing == "up":
            pygame.draw.circle(surf, BLACK, (px - 4, int(ey - 2)), 2)
            pygame.draw.circle(surf, BLACK, (px + 4, int(ey - 2)), 2)
            pygame.draw.arc(surf, BLACK, (px - 3, int(ey + 1), 6, 4), 3.14, 6.28, 1)
        elif self.facing == "left":
            pygame.draw.circle(surf, BLACK, (px - 5, int(ey - 2)), 2)
            pygame.draw.circle(surf, BLACK, (px - 1, int(ey - 2)), 2)
            pygame.draw.arc(surf, BLACK, (px - 5, int(ey + 1), 5, 4), 3.14, 6.28, 1)
        elif self.facing == "right":
            pygame.draw.circle(surf, BLACK, (px + 1, int(ey - 2)), 2)
            pygame.draw.circle(surf, BLACK, (px + 5, int(ey - 2)), 2)
            pygame.draw.arc(surf, BLACK, (px, int(ey + 1), 5, 4), 3.14, 6.28, 1)

        # Little feet
        pygame.draw.circle(surf, ORANGE, (px - 5, int(py + 6 + bob)), 4)
        pygame.draw.circle(surf, ORANGE, (px + 5, int(py + 6 + bob)), 4)


# ═══════════════════════════════════════════════════════════════════════
#  OVERWORLD MAP GENERATION
# ═══════════════════════════════════════════════════════════════════════
def generate_overworld_map(zone):
    """Generate a simple tile map for the given zone."""
    tiles = []
    for y in range(OW_MAP_H):
        row = []
        for x in range(OW_MAP_W):
            # Border walls
            if x == 0 or x == OW_MAP_W - 1 or y == 0 or y == OW_MAP_H - 1:
                row.append("wall")
            else:
                row.append("floor")
        tiles.append(row)

    # Add some decorations
    zone_name = zone["name"]
    rng = random.Random(hash(zone_name))
    for _ in range(15):
        x = rng.randint(2, OW_MAP_W - 3)
        y = rng.randint(2, OW_MAP_H - 3)
        tiles[y][x] = "deco"

    # Add encounters as sparkle tiles
    encounter_positions = []
    attempts = 0
    while len(encounter_positions) < zone["encounters"] and attempts < 100:
        x = rng.randint(3, OW_MAP_W - 4)
        y = rng.randint(3, OW_MAP_H - 4)
        if tiles[y][x] == "floor" and (x, y) not in encounter_positions:
            tiles[y][x] = "encounter"
            encounter_positions.append((x, y))
        attempts += 1

    # Add item pickups
    for item in zone.get("items", []):
        attempts = 0
        while attempts < 50:
            x = rng.randint(2, OW_MAP_W - 3)
            y = rng.randint(2, OW_MAP_H - 3)
            if tiles[y][x] == "floor":
                tiles[y][x] = "item"
                break
            attempts += 1

    # Exit to next zone
    if zone != ZONES[-1]:
        tiles[1][OW_MAP_W // 2] = "exit"
        tiles[0][OW_MAP_W // 2] = "exit"

    return tiles


def draw_overworld(surf, tiles, zone, player, camera_x, camera_y, t):
    """Draw the overworld map."""
    z = zone
    surf.fill(z["bg"])

    ox = -camera_x
    oy = -camera_y

    for ty in range(OW_MAP_H):
        for tx in range(OW_MAP_W):
            sx = ox + tx * OW_TILE
            sy = oy + ty * OW_TILE
            if sx > WIDTH + OW_TILE or sy > HEIGHT + OW_TILE or sx < -OW_TILE or sy < -OW_TILE:
                continue
            tile = tiles[ty][tx]
            if tile == "wall":
                pygame.draw.rect(surf, (max(0, z["tile"][0] - 30), max(0, z["tile"][1] - 30), max(0, z["tile"][2] - 30)),
                                 (sx, sy, OW_TILE, OW_TILE))
                pygame.draw.rect(surf, (max(0, z["tile"][0] - 50), max(0, z["tile"][1] - 50), max(0, z["tile"][2] - 50)),
                                 (sx, sy, OW_TILE, OW_TILE), 2)
            elif tile == "floor":
                c = z["tile"] if (tx + ty) % 2 == 0 else z["tile2"]
                pygame.draw.rect(surf, c, (sx, sy, OW_TILE, OW_TILE))
            elif tile == "deco":
                c = z["tile"] if (tx + ty) % 2 == 0 else z["tile2"]
                pygame.draw.rect(surf, c, (sx, sy, OW_TILE, OW_TILE))
                # Draw a decoration based on the zone
                dcx, dcy = sx + OW_TILE // 2, sy + OW_TILE // 2
                if "Meadow" in z["name"]:
                    # Flowers
                    for angle in range(0, 360, 72):
                        px = dcx + math.cos(math.radians(angle)) * 8
                        py = dcy + math.sin(math.radians(angle)) * 8
                        pygame.draw.circle(surf, random.choice([PINK, YELLOW, RED]), (int(px), int(py)), 4)
                    pygame.draw.circle(surf, YELLOW, (dcx, dcy), 4)
                elif "Mushroom" in z["name"]:
                    pygame.draw.rect(surf, BROWN, (dcx - 3, dcy, 6, 10))
                    pygame.draw.ellipse(surf, RED, (dcx - 8, dcy - 8, 16, 12))
                    pygame.draw.circle(surf, WHITE, (dcx - 3, dcy - 5), 2)
                    pygame.draw.circle(surf, WHITE, (dcx + 4, dcy - 3), 2)
                elif "Snowy" in z["name"]:
                    pygame.draw.circle(surf, WHITE, (dcx, dcy + 3), 7)
                    pygame.draw.circle(surf, WHITE, (dcx, dcy - 5), 5)
                    pygame.draw.circle(surf, BLACK, (dcx - 2, dcy - 6), 1)
                    pygame.draw.circle(surf, BLACK, (dcx + 2, dcy - 6), 1)
                elif "Robot" in z["name"]:
                    pygame.draw.rect(surf, GRAY, (dcx - 6, dcy - 6, 12, 12))
                    blink = math.sin(t * 3 + tx + ty) > 0
                    pygame.draw.circle(surf, GREEN if blink else RED, (dcx, dcy), 3)
                elif "Dragon" in z["name"]:
                    pygame.draw.circle(surf, LAVA_RED, (dcx, dcy), 6)
                    pygame.draw.circle(surf, ORANGE, (dcx, dcy), 3)
                else:
                    pygame.draw.rect(surf, DARK_GRAY, (dcx - 5, dcy - 5, 10, 10))
            elif tile == "encounter":
                c = z["tile"] if (tx + ty) % 2 == 0 else z["tile2"]
                pygame.draw.rect(surf, c, (sx, sy, OW_TILE, OW_TILE))
                # Sparkle
                sparkle_phase = math.sin(t * 4 + tx * 3 + ty * 7) * 0.5 + 0.5
                size = int(6 + sparkle_phase * 6)
                scx, scy = sx + OW_TILE // 2, sy + OW_TILE // 2
                sc = (int(255 * sparkle_phase), int(220 * sparkle_phase), int(100 + 155 * sparkle_phase))
                # Draw star sparkle
                for i in range(4):
                    a = math.radians(i * 90 + t * 60)
                    ex = scx + math.cos(a) * size
                    ey = scy + math.sin(a) * size
                    pygame.draw.line(surf, sc, (scx, scy), (int(ex), int(ey)), 2)
                pygame.draw.circle(surf, STAR_YELLOW, (scx, scy), 3)
            elif tile == "item":
                c = z["tile"] if (tx + ty) % 2 == 0 else z["tile2"]
                pygame.draw.rect(surf, c, (sx, sy, OW_TILE, OW_TILE))
                # Chest
                cx_t, cy_t = sx + OW_TILE // 2, sy + OW_TILE // 2
                pygame.draw.rect(surf, GOLD, (cx_t - 10, cy_t - 6, 20, 14))
                pygame.draw.rect(surf, ORANGE, (cx_t - 10, cy_t - 6, 20, 14), 2)
                pygame.draw.circle(surf, WHITE, (cx_t, cy_t + 2), 3)
            elif tile == "exit":
                pygame.draw.rect(surf, STAR_YELLOW, (sx, sy, OW_TILE, OW_TILE))
                alpha = int(128 + math.sin(t * 3) * 127)
                exit_surf = pygame.Surface((OW_TILE, OW_TILE), pygame.SRCALPHA)
                exit_surf.fill((255, 255, 200, alpha))
                surf.blit(exit_surf, (sx, sy))
                txt = font_xs.render("EXIT", True, BLACK)
                surf.blit(txt, (sx + OW_TILE // 2 - txt.get_width() // 2,
                                sy + OW_TILE // 2 - txt.get_height() // 2))
            elif tile == "collected":
                c = z["tile"] if (tx + ty) % 2 == 0 else z["tile2"]
                pygame.draw.rect(surf, c, (sx, sy, OW_TILE, OW_TILE))

    # Draw player
    player.draw_overworld(surf, ox, oy, t)

    # HUD
    # Zone name
    zone_txt = font_md.render(z["name"], True, WHITE)
    pygame.draw.rect(surf, (*PANEL_BG, 200), (10, 10, zone_txt.get_width() + 20, 35), border_radius=8)
    surf.blit(zone_txt, (20, 15))

    # HP bar
    hp_w = 200
    hp_h = 18
    hp_x, hp_y = WIDTH - hp_w - 20, 15
    pygame.draw.rect(surf, (*PANEL_BG, 200), (hp_x - 10, hp_y - 5, hp_w + 20, hp_h + 24), border_radius=8)
    hp_fill = max(0, player.hp / player.max_hp)
    bar_color = HP_GREEN_BAR if hp_fill > 0.5 else HP_YELLOW_BAR if hp_fill > 0.25 else HP_RED_BAR
    pygame.draw.rect(surf, DARK_GRAY, (hp_x, hp_y, hp_w, hp_h), border_radius=4)
    pygame.draw.rect(surf, bar_color, (hp_x, hp_y, int(hp_w * hp_fill), hp_h), border_radius=4)
    hp_txt = font_sm.render(f"HP: {player.hp}/{player.max_hp}", True, WHITE)
    surf.blit(hp_txt, (hp_x + hp_w // 2 - hp_txt.get_width() // 2, hp_y))
    lv_txt = font_xs.render(f"LV {player.level}  ATK {player.atk}  DEF {player.defense}  Gold {player.gold}", True, LIGHT_GRAY)
    surf.blit(lv_txt, (hp_x, hp_y + hp_h + 3))

    # Controls hint
    hint = font_xs.render("Arrow Keys: Move | Z: Interact | X: Menu", True, LIGHT_GRAY)
    surf.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 25))


# ═══════════════════════════════════════════════════════════════════════
#  BATTLE SYSTEM (Undertale-style)
# ═══════════════════════════════════════════════════════════════════════
class Battle:
    """Full Undertale-style battle with FIGHT/ACT/ITEM/MERCY."""

    def __init__(self, player, monster_def):
        self.player = player
        self.mdef = monster_def
        self.monster_hp = monster_def.hp
        self.monster_max_hp = monster_def.hp
        self.mercy = 0
        self.turn = "menu"  # menu, fight_anim, act_menu, item_menu, dodge, text, result
        self.menu_index = 0
        self.act_index = 0
        self.item_index = 0
        self.text_queue = []
        self.text_current = ""
        self.text_char_index = 0
        self.text_timer = 0
        self.text_speed = 2  # chars per frame
        self.result = None  # "win", "spare", "lose"
        self.dodge_timer = 0
        self.dodge_duration = 180  # 3 seconds at 60fps
        self.bullets = []
        self.heart_x = 0
        self.heart_y = 0
        self.heart_speed = 4
        self.heart_iframes = 0
        self.atk_boost = 0
        self.anim_timer = 0
        self.battle_time = 0
        self.shake = 0
        self.damage_numbers = []  # (text, x, y, timer, color)
        self.fight_bar_active = False
        self.fight_bar_pos = 0
        self.fight_bar_speed = 4
        self.fight_bar_stopped = False
        self.attack_wave = 0

        # Battle box dimensions
        self.box_x = WIDTH // 2 - 140
        self.box_y = 380
        self.box_w = 280
        self.box_h = 160

        # Center heart
        self.heart_x = self.box_x + self.box_w // 2
        self.heart_y = self.box_y + self.box_h // 2

        # Queue flavor text
        self.queue_text(monster_def.flavor)

    def queue_text(self, text):
        self.text_queue.append(text)
        if self.turn != "text" and self.turn != "dodge":
            self.start_next_text()

    def start_next_text(self):
        if self.text_queue:
            self.text_current = self.text_queue.pop(0)
            self.text_char_index = 0
            self.text_timer = 0
            self.turn = "text"
        else:
            self.turn = "menu"

    def update(self, keys_pressed, keys_just):
        self.battle_time += 1 / 60
        self.anim_timer += 1

        # Update damage numbers
        self.damage_numbers = [(t, x, y - 1, timer - 1, c) for t, x, y, timer, c in self.damage_numbers if timer > 0]

        if self.shake > 0:
            self.shake -= 1

        if self.turn == "text":
            self.text_timer += 1
            self.text_char_index = min(len(self.text_current), int(self.text_timer * self.text_speed / 3))
            if keys_just.get(pygame.K_z) or keys_just.get(pygame.K_SPACE) or keys_just.get(pygame.K_RETURN):
                if self.text_char_index < len(self.text_current):
                    self.text_char_index = len(self.text_current)
                else:
                    if self.result:
                        return self.result
                    self.start_next_text()
                    if not self.text_queue and self.turn == "text" and self.text_char_index >= len(self.text_current):
                        self.turn = "menu"

        elif self.turn == "menu":
            if keys_just.get(pygame.K_LEFT) or keys_just.get(pygame.K_a):
                self.menu_index = (self.menu_index - 1) % 4
                SFX_DODGE.play()
            if keys_just.get(pygame.K_RIGHT) or keys_just.get(pygame.K_d):
                self.menu_index = (self.menu_index + 1) % 4
                SFX_DODGE.play()
            if keys_just.get(pygame.K_z) or keys_just.get(pygame.K_SPACE):
                SFX_CONFIRM.play()
                if self.menu_index == 0:  # FIGHT
                    self.turn = "fight_anim"
                    self.fight_bar_active = True
                    self.fight_bar_pos = 0
                    self.fight_bar_stopped = False
                elif self.menu_index == 1:  # ACT
                    self.turn = "act_menu"
                    self.act_index = 0
                elif self.menu_index == 2:  # ITEM
                    if self.player.inventory:
                        self.turn = "item_menu"
                        self.item_index = 0
                    else:
                        self.queue_text("* You don't have any items!")
                elif self.menu_index == 3:  # MERCY
                    if self.mercy >= self.mdef.spare_threshold:
                        self.result = "spare"
                        self.player.friends_made += 1
                        self.player.gain_xp(self.mdef.xp // 2)
                        self.player.gold += self.mdef.gold
                        SFX_MERCY.play()
                        name = self.mdef.name
                        self.queue_text(f"* You spared {name}!")
                        self.queue_text(f"* {name} is now your friend!")
                        self.queue_text(f"* You got {self.mdef.gold} gold!")
                    else:
                        self.queue_text(f"* {self.mdef.name} isn't ready to be friends yet.")
                        self.queue_text("* Try using ACT to get closer!")
                        self.turn = "text"

        elif self.turn == "fight_anim":
            if not self.fight_bar_stopped:
                self.fight_bar_pos += self.fight_bar_speed
                if self.fight_bar_pos >= 200:
                    self.fight_bar_pos = 200
                    self.fight_bar_stopped = True
                    self._do_fight(50)  # weak hit
                if keys_just.get(pygame.K_z) or keys_just.get(pygame.K_SPACE):
                    self.fight_bar_stopped = True
                    # Calculate damage based on bar position
                    # Perfect center = 100% damage
                    center_dist = abs(self.fight_bar_pos - 100)
                    accuracy = max(0, 100 - center_dist)
                    self._do_fight(accuracy)

        elif self.turn == "act_menu":
            acts = self.mdef.act_options
            if keys_just.get(pygame.K_UP) or keys_just.get(pygame.K_w):
                self.act_index = (self.act_index - 1) % len(acts)
                SFX_DODGE.play()
            if keys_just.get(pygame.K_DOWN) or keys_just.get(pygame.K_s):
                self.act_index = (self.act_index + 1) % len(acts)
                SFX_DODGE.play()
            if keys_just.get(pygame.K_z) or keys_just.get(pygame.K_SPACE):
                act_name, act_text, mercy_gain = acts[self.act_index]
                self.mercy = min(100, self.mercy + mercy_gain)
                SFX_CONFIRM.play()
                self.queue_text(act_text)
                if self.mercy >= self.mdef.spare_threshold:
                    self.queue_text(f"* {self.mdef.name} looks like it wants to be friends!")
                self._start_dodge_phase()
            if keys_just.get(pygame.K_x) or keys_just.get(pygame.K_ESCAPE):
                SFX_CANCEL.play()
                self.turn = "menu"

        elif self.turn == "item_menu":
            inv = self.player.inventory
            if keys_just.get(pygame.K_UP) or keys_just.get(pygame.K_w):
                self.item_index = (self.item_index - 1) % len(inv)
                SFX_DODGE.play()
            if keys_just.get(pygame.K_DOWN) or keys_just.get(pygame.K_s):
                self.item_index = (self.item_index + 1) % len(inv)
                SFX_DODGE.play()
            if keys_just.get(pygame.K_z) or keys_just.get(pygame.K_SPACE):
                item_name = inv[self.item_index]
                item_data = ITEMS.get(item_name, {})
                self.player.inventory.pop(self.item_index)
                SFX_CONFIRM.play()

                if item_data.get("type") == "heal":
                    heal = item_data["value"]
                    self.player.hp = min(self.player.max_hp, self.player.hp + heal)
                    SFX_HEAL.play()
                    self.queue_text(f"* You used {item_name}! Healed {heal} HP!")
                elif item_data.get("type") == "atk_boost":
                    self.atk_boost += item_data["value"]
                    self.queue_text(f"* You used {item_name}! ATK boosted!")
                elif item_data.get("type") == "act_boost":
                    boost = item_data["value"]
                    self.mercy = min(100, self.mercy + boost * 15)
                    self.queue_text(f"* You showed {item_name}! {self.mdef.name} likes it!")

                self._start_dodge_phase()
                if self.item_index >= len(self.player.inventory):
                    self.item_index = max(0, len(self.player.inventory) - 1)
            if keys_just.get(pygame.K_x) or keys_just.get(pygame.K_ESCAPE):
                SFX_CANCEL.play()
                self.turn = "menu"

        elif self.turn == "dodge":
            self.dodge_timer += 1

            # Move heart
            move_x, move_y = 0, 0
            if keys_pressed.get(pygame.K_LEFT) or keys_pressed.get(pygame.K_a):
                move_x -= self.heart_speed
            if keys_pressed.get(pygame.K_RIGHT) or keys_pressed.get(pygame.K_d):
                move_x += self.heart_speed
            if keys_pressed.get(pygame.K_UP) or keys_pressed.get(pygame.K_w):
                move_y -= self.heart_speed
            if keys_pressed.get(pygame.K_DOWN) or keys_pressed.get(pygame.K_s):
                move_y += self.heart_speed

            self.heart_x += move_x
            self.heart_y += move_y

            # Clamp to box
            margin = 10
            self.heart_x = max(self.box_x + margin, min(self.box_x + self.box_w - margin, self.heart_x))
            self.heart_y = max(self.box_y + margin, min(self.box_y + self.box_h - margin, self.heart_y))

            # Spawn new bullets periodically
            if self.dodge_timer % 30 == 0:
                pattern = random.choice(self.mdef.attacks)
                diff = self.mdef.atk / 10
                box_rect = (self.box_x, self.box_y, self.box_w, self.box_h)
                new_bullets = generate_attack(pattern, box_rect, diff, self.battle_time)
                self.bullets.extend(new_bullets)

            # Update bullets
            self.bullets = [b for b in self.bullets if b.update()]

            # Remove bullets out of box (with margin)
            margin_out = 30
            self.bullets = [b for b in self.bullets if
                            self.box_x - margin_out < b.x < self.box_x + self.box_w + margin_out and
                            self.box_y - margin_out < b.y < self.box_y + self.box_h + margin_out]

            # Check collisions
            if self.heart_iframes > 0:
                self.heart_iframes -= 1
            else:
                for b in self.bullets:
                    if b.collides_heart(self.heart_x, self.heart_y, 8):
                        dmg = max(1, self.mdef.atk - self.player.defense // 2)
                        # Kid-friendly: reduce damage
                        dmg = max(1, dmg // 2 + random.randint(0, 2))
                        self.player.hp -= dmg
                        self.heart_iframes = 40
                        self.shake = 10
                        SFX_HIT.play()
                        self.damage_numbers.append(
                            (f"-{dmg}", int(self.heart_x), int(self.heart_y - 20), 60, RED))
                        self.bullets.remove(b)
                        break

            # Check if player lost
            if self.player.hp <= 0:
                self.player.hp = 0
                self.result = "lose"
                self.queue_text("* Oh no! You got bonked too much!")
                self.queue_text("* Don't worry, you can try again!")
                self.turn = "text"

            # End dodge phase
            if self.dodge_timer >= self.dodge_duration:
                self.bullets.clear()
                self.turn = "menu"
                self.dodge_timer = 0

        return None

    def _do_fight(self, accuracy):
        """Deal damage based on fight bar accuracy."""
        base_dmg = self.player.atk + self.atk_boost
        dmg = max(1, int(base_dmg * accuracy / 100) + random.randint(-1, 2))
        dmg = max(1, dmg - self.mdef.defense)
        self.monster_hp -= dmg
        self.shake = 15
        SFX_HIT.play()
        self.damage_numbers.append((f"-{dmg}", WIDTH // 2, 200, 60, RED))
        self.player.monsters_fought += 1

        if self.monster_hp <= 0:
            self.monster_hp = 0
            self.result = "win"
            leveled = self.player.gain_xp(self.mdef.xp)
            self.player.gold += self.mdef.gold
            self.queue_text(f"* You defeated {self.mdef.name}!")
            self.queue_text(f"* Got {self.mdef.xp} XP and {self.mdef.gold} gold!")
            if leveled:
                SFX_LEVEL_UP.play()
                self.queue_text(f"* LEVEL UP! You're now level {self.player.level}!")
                self.queue_text(f"* HP, ATK, and DEF increased!")
        else:
            quality = "Amazing!" if accuracy > 85 else "Good!" if accuracy > 50 else "OK hit."
            self.queue_text(f"* {quality} {dmg} damage!")
            self._start_dodge_phase()

    def _start_dodge_phase(self):
        """Start the bullet dodging phase."""
        self.turn = "dodge"
        self.dodge_timer = 0
        self.bullets.clear()
        self.heart_x = self.box_x + self.box_w // 2
        self.heart_y = self.box_y + self.box_h // 2
        self.heart_iframes = 30  # Brief invincibility
        # Boss has longer dodge phases
        if self.mdef.boss:
            self.dodge_duration = 240
        else:
            self.dodge_duration = 150 + self.mdef.atk * 5

    def draw(self, surf):
        """Draw the entire battle screen."""
        surf.fill(BATTLE_BG)
        t = self.battle_time

        shake_x = random.randint(-self.shake, self.shake) if self.shake else 0
        shake_y = random.randint(-self.shake, self.shake) if self.shake else 0

        # ── Monster ──
        mx = WIDTH // 2 + shake_x
        my = 170 + shake_y
        self.mdef.sprite_fn(surf, mx, my, self.mdef.color, t)

        # Monster name & HP
        name_txt = font_lg.render(self.mdef.name, True, WHITE)
        surf.blit(name_txt, (WIDTH // 2 - name_txt.get_width() // 2, 50))

        # Monster HP bar
        mhp_w = 250
        mhp_h = 12
        mhp_x = WIDTH // 2 - mhp_w // 2
        mhp_y = 85
        pygame.draw.rect(surf, DARK_GRAY, (mhp_x, mhp_y, mhp_w, mhp_h), border_radius=4)
        mhp_fill = max(0, self.monster_hp / self.monster_max_hp)
        pygame.draw.rect(surf, HP_GREEN_BAR if mhp_fill > 0.5 else HP_YELLOW_BAR if mhp_fill > 0.25 else HP_RED_BAR,
                         (mhp_x, mhp_y, int(mhp_w * mhp_fill), mhp_h), border_radius=4)
        mhp_txt = font_xs.render(f"{self.monster_hp}/{self.monster_max_hp}", True, WHITE)
        surf.blit(mhp_txt, (mhp_x + mhp_w // 2 - mhp_txt.get_width() // 2, mhp_y - 1))

        # Mercy meter
        mercy_txt = font_xs.render(f"Mercy: {self.mercy}%", True, STAR_YELLOW if self.mercy >= self.mdef.spare_threshold else LIGHT_GRAY)
        surf.blit(mercy_txt, (WIDTH // 2 - mercy_txt.get_width() // 2, mhp_y + 16))

        # ── Battle Box ──
        if self.turn == "dodge":
            # Draw box
            pygame.draw.rect(surf, BLACK, (self.box_x, self.box_y, self.box_w, self.box_h))
            pygame.draw.rect(surf, WHITE, (self.box_x, self.box_y, self.box_w, self.box_h), 3)

            # Draw bullets
            for b in self.bullets:
                b.draw(surf, (self.box_x, self.box_y, self.box_w, self.box_h))

            # Draw heart (player soul)
            if self.heart_iframes == 0 or self.heart_iframes % 4 < 2:
                hx, hy = int(self.heart_x), int(self.heart_y)
                # Heart shape
                pts = [(hx, hy + 8), (hx - 8, hy - 2), (hx - 5, hy - 8),
                       (hx, hy - 4), (hx + 5, hy - 8), (hx + 8, hy - 2)]
                pygame.draw.polygon(surf, HEART_RED, pts)

            # Timer bar
            timer_w = self.box_w - 10
            timer_fill = max(0, 1 - self.dodge_timer / self.dodge_duration)
            pygame.draw.rect(surf, DARK_GRAY, (self.box_x + 5, self.box_y + self.box_h + 5, timer_w, 6), border_radius=3)
            pygame.draw.rect(surf, CYAN, (self.box_x + 5, self.box_y + self.box_h + 5, int(timer_w * timer_fill), 6), border_radius=3)

        elif self.turn == "fight_anim":
            # Fight accuracy bar
            bar_x = WIDTH // 2 - 120
            bar_y = 320
            bar_w = 240
            bar_h = 30
            pygame.draw.rect(surf, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h), border_radius=6)
            # Center zone (green)
            center_w = 40
            pygame.draw.rect(surf, GREEN, (bar_x + bar_w // 2 - center_w // 2, bar_y, center_w, bar_h), border_radius=6)
            # Mid zone (yellow)
            pygame.draw.rect(surf, YELLOW, (bar_x + bar_w // 2 - center_w, bar_y, center_w // 2, bar_h), border_radius=4)
            pygame.draw.rect(surf, YELLOW, (bar_x + bar_w // 2 + center_w // 2, bar_y, center_w // 2, bar_h), border_radius=4)
            # Moving bar
            bar_pos_x = bar_x + int(self.fight_bar_pos / 200 * bar_w)
            pygame.draw.rect(surf, WHITE, (bar_pos_x - 3, bar_y - 5, 6, bar_h + 10), border_radius=2)
            # Instructions
            if not self.fight_bar_stopped:
                inst = font_sm.render("Press Z to stop the bar!", True, WHITE)
                surf.blit(inst, (WIDTH // 2 - inst.get_width() // 2, bar_y + bar_h + 10))

        # ── Text Box ──
        if self.turn == "text" or (self.turn != "dodge" and self.turn != "fight_anim"):
            text_box_y = 300
            text_box_h = 60
            pygame.draw.rect(surf, BLACK, (50, text_box_y, WIDTH - 100, text_box_h))
            pygame.draw.rect(surf, WHITE, (50, text_box_y, WIDTH - 100, text_box_h), 2)

            if self.text_current:
                display_text = self.text_current[:self.text_char_index]
                lines = display_text.split("\n")
                for i, line in enumerate(lines):
                    txt = font_battle.render(line, True, WHITE)
                    surf.blit(txt, (70, text_box_y + 10 + i * 22))

        # ── Menu Buttons ──
        if self.turn == "menu":
            labels = ["FIGHT", "ACT", "ITEM", "MERCY"]
            colors = [RED, YELLOW, GREEN, PURPLE]
            for i, (label, col) in enumerate(zip(labels, colors)):
                bx = 100 + i * 185
                by = 580
                bw, bh = 160, 45
                selected = (i == self.menu_index)
                bg_col = col if selected else DARK_GRAY
                pygame.draw.rect(surf, bg_col, (bx, by, bw, bh), border_radius=8)
                pygame.draw.rect(surf, WHITE if selected else GRAY, (bx, by, bw, bh), 3, border_radius=8)
                txt = font_md.render(label, True, WHITE if selected else LIGHT_GRAY)
                surf.blit(txt, (bx + bw // 2 - txt.get_width() // 2, by + bh // 2 - txt.get_height() // 2))

        # ── ACT sub-menu ──
        elif self.turn == "act_menu":
            pygame.draw.rect(surf, (20, 20, 40), (150, 400, 600, 200), border_radius=10)
            pygame.draw.rect(surf, WHITE, (150, 400, 600, 200), 2, border_radius=10)
            title = font_md.render("What do you do?", True, YELLOW)
            surf.blit(title, (WIDTH // 2 - title.get_width() // 2, 410))
            for i, (name, desc, mg) in enumerate(self.mdef.act_options):
                selected = (i == self.act_index)
                col = STAR_YELLOW if selected else LIGHT_GRAY
                prefix = "> " if selected else "  "
                txt = font_battle.render(f"{prefix}{name}", True, col)
                surf.blit(txt, (180, 445 + i * 30))
                if selected:
                    # Show mercy gain hint
                    hint = font_xs.render(f"(+{mg}% mercy)", True, CYAN)
                    surf.blit(hint, (400, 448 + i * 30))

        # ── ITEM sub-menu ──
        elif self.turn == "item_menu":
            pygame.draw.rect(surf, (20, 20, 40), (150, 380, 600, 220), border_radius=10)
            pygame.draw.rect(surf, WHITE, (150, 380, 600, 220), 2, border_radius=10)
            title = font_md.render("Use which item?", True, GREEN)
            surf.blit(title, (WIDTH // 2 - title.get_width() // 2, 390))
            if self.player.inventory:
                # Show up to 6 items with scrolling
                start = max(0, self.item_index - 3)
                for idx in range(start, min(len(self.player.inventory), start + 6)):
                    i = idx - start
                    item_name = self.player.inventory[idx]
                    selected = (idx == self.item_index)
                    col = STAR_YELLOW if selected else LIGHT_GRAY
                    prefix = "> " if selected else "  "
                    item_data = ITEMS.get(item_name, {})
                    item_col = item_data.get("color", WHITE)
                    txt = font_battle.render(f"{prefix}{item_name}", True, col)
                    surf.blit(txt, (180, 420 + i * 28))
                    if selected and item_data.get("desc"):
                        desc = font_xs.render(item_data["desc"], True, CYAN)
                        surf.blit(desc, (180, 590))

        # ── Player HP at bottom ──
        php_y = 640
        php_w = 300
        php_x = WIDTH // 2 - php_w // 2
        # Name and LV
        info = font_sm.render(f"{self.player.name}  LV {self.player.level}", True, WHITE)
        surf.blit(info, (php_x, php_y))
        # HP bar
        hp_bar_x = php_x + info.get_width() + 15
        hp_bar_w = 160
        hp_bar_h = 16
        pygame.draw.rect(surf, DARK_GRAY, (hp_bar_x, php_y + 2, hp_bar_w, hp_bar_h), border_radius=4)
        hp_fill = max(0, self.player.hp / self.player.max_hp)
        bar_color = HP_GREEN_BAR if hp_fill > 0.5 else HP_YELLOW_BAR if hp_fill > 0.25 else HP_RED_BAR
        pygame.draw.rect(surf, bar_color, (hp_bar_x, php_y + 2, int(hp_bar_w * hp_fill), hp_bar_h), border_radius=4)
        hp_txt = font_xs.render(f"{self.player.hp}/{self.player.max_hp}", True, WHITE)
        surf.blit(hp_txt, (hp_bar_x + hp_bar_w // 2 - hp_txt.get_width() // 2, php_y + 3))

        # ── Damage numbers ──
        for text, dx, dy, timer, col in self.damage_numbers:
            alpha = min(255, timer * 8)
            dtxt = font_dmg.render(text, True, col)
            surf.blit(dtxt, (dx - dtxt.get_width() // 2, dy))


# ═══════════════════════════════════════════════════════════════════════
#  SAVE / LOAD
# ═══════════════════════════════════════════════════════════════════════
def save_game(player):
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(player.to_dict(), f, indent=2)
    except Exception:
        pass

def load_game():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE) as f:
                data = json.load(f)
            p = Player()
            p.from_dict(data)
            return p
        except Exception:
            pass
    return None


# ═══════════════════════════════════════════════════════════════════════
#  PARTICLE SYSTEM
# ═══════════════════════════════════════════════════════════════════════
class Particle:
    def __init__(self, x, y, vx, vy, color, life, size=3):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05  # gravity
        self.life -= 1
        return self.life > 0

    def draw(self, surf):
        alpha = self.life / self.max_life
        size = max(1, int(self.size * alpha))
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), size)

particles = []


# ═══════════════════════════════════════════════════════════════════════
#  MAIN GAME LOOP
# ═══════════════════════════════════════════════════════════════════════
def main():
    global particles

    # ── Game state ──
    STATE_TITLE = "title"
    STATE_OVERWORLD = "overworld"
    STATE_BATTLE = "battle"
    STATE_DIALOGUE = "dialogue"
    STATE_GAME_OVER = "game_over"
    STATE_WIN = "win"
    STATE_INVENTORY = "inventory"

    state = STATE_TITLE
    title_selection = 0  # 0 = New Game, 1 = Continue
    has_save = load_game() is not None

    player = Player()
    battle = None
    current_zone = ZONES[0]
    overworld_tiles = None
    camera_x, camera_y = 0, 0
    dialogue_text = ""
    dialogue_char_idx = 0
    dialogue_timer = 0
    dialogue_callback = None
    inv_index = 0
    game_time = 0
    step_cooldown = 0
    item_positions = {}  # (x,y) -> item_name for current zone

    def start_new_game():
        nonlocal player, current_zone, overworld_tiles, camera_x, camera_y, item_positions
        player = Player()
        current_zone = ZONES[0]
        player.zone_encounters_left = current_zone["encounters"]
        overworld_tiles = generate_overworld_map(current_zone)
        # Record item positions
        item_positions = {}
        for ty in range(OW_MAP_H):
            for tx in range(OW_MAP_W):
                if overworld_tiles[ty][tx] == "item":
                    zone_items = list(current_zone.get("items", []))
                    if zone_items:
                        item_positions[(tx, ty)] = zone_items.pop(0)
        camera_x = player.x * OW_TILE - WIDTH // 2
        camera_y = player.y * OW_TILE - HEIGHT // 2

    def load_zone(idx):
        nonlocal current_zone, overworld_tiles, item_positions
        player.zone_index = idx
        current_zone = ZONES[idx]
        player.zone_encounters_left = current_zone["encounters"]
        overworld_tiles = generate_overworld_map(current_zone)
        player.x = OW_MAP_W // 2
        player.y = OW_MAP_H - 3
        item_positions = {}
        zone_items = list(current_zone.get("items", []))
        for ty in range(OW_MAP_H):
            for tx in range(OW_MAP_W):
                if overworld_tiles[ty][tx] == "item" and zone_items:
                    item_positions[(tx, ty)] = zone_items.pop(0)

    def show_dialogue(text, callback=None):
        nonlocal state, dialogue_text, dialogue_char_idx, dialogue_timer, dialogue_callback
        state = STATE_DIALOGUE
        dialogue_text = text
        dialogue_char_idx = 0
        dialogue_timer = 0
        dialogue_callback = callback

    # ── Main loop ──
    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        game_time += dt

        # ── Events ──
        keys_just = {}
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                keys_just[event.key] = True

        keys_pressed = {}
        pressed = pygame.key.get_pressed()
        for k in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN,
                   pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s,
                   pygame.K_z, pygame.K_x, pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE]:
            if pressed[k]:
                keys_pressed[k] = True

        # ── Update particles ──
        particles = [p for p in particles if p.update()]

        # ═══════════════════════════════════════════════════════════════
        #  TITLE SCREEN
        # ═══════════════════════════════════════════════════════════════
        if state == STATE_TITLE:
            if keys_just.get(pygame.K_UP) or keys_just.get(pygame.K_w):
                title_selection = (title_selection - 1) % (2 if has_save else 1)
                SFX_DODGE.play()
            if keys_just.get(pygame.K_DOWN) or keys_just.get(pygame.K_s):
                title_selection = (title_selection + 1) % (2 if has_save else 1)
                SFX_DODGE.play()
            if keys_just.get(pygame.K_z) or keys_just.get(pygame.K_SPACE) or keys_just.get(pygame.K_RETURN):
                SFX_CONFIRM.play()
                if title_selection == 0:
                    start_new_game()
                    state = STATE_OVERWORLD
                    show_dialogue("Welcome to Starlight Quest!\nYou are Star Kid, on a mission to\nrecover the Rainbow Crystal from\nthe silly Grumble King!\n\nExplore each zone, meet creatures,\nand choose to FIGHT or make FRIENDS!\n\n(Press Z / SPACE to continue)",
                                  lambda: None)
                elif title_selection == 1 and has_save:
                    loaded = load_game()
                    if loaded:
                        player = loaded
                        load_zone(player.zone_index)
                        state = STATE_OVERWORLD

            # Draw title
            screen.fill((15, 10, 30))
            # Stars background
            rng = random.Random(42)
            for _ in range(80):
                sx = rng.randint(0, WIDTH)
                sy = rng.randint(0, HEIGHT)
                br = rng.uniform(0.3, 1.0)
                twinkle = (math.sin(game_time * 2 + sx * 0.1) * 0.3 + 0.7) * br
                sz = rng.randint(1, 3)
                col = (int(200 * twinkle), int(200 * twinkle), int(255 * twinkle))
                pygame.draw.circle(screen, col, (sx, sy), sz)

            # Title
            title = font_title.render("Starlight Quest", True, STAR_YELLOW)
            shadow = font_title.render("Starlight Quest", True, ORANGE)
            screen.blit(shadow, (WIDTH // 2 - title.get_width() // 2 + 3, 143))
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 140))

            # Subtitle
            sub = font_md.render("A Kid-Friendly RPG Adventure!", True, CYAN)
            screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 210))

            # Cute star character
            cx, cy = WIDTH // 2, 320
            bob = math.sin(game_time * 2) * 10
            r = 35
            pts = []
            for i in range(5):
                a = math.radians(i * 72 - 90 + math.sin(game_time) * 5)
                pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r + bob))
                a2 = math.radians(i * 72 + 36 - 90 + math.sin(game_time) * 5)
                pts.append((cx + math.cos(a2) * r * 0.4, cy + math.sin(a2) * r * 0.4 + bob))
            pygame.draw.polygon(screen, STAR_YELLOW, pts)
            pygame.draw.polygon(screen, ORANGE, pts, 2)
            # Face
            pygame.draw.circle(screen, BLACK, (int(cx - 8), int(cy - 5 + bob)), 4)
            pygame.draw.circle(screen, BLACK, (int(cx + 8), int(cy - 5 + bob)), 4)
            pygame.draw.arc(screen, BLACK, (int(cx - 8), int(cy + 3 + bob), 16, 10), 3.14, 6.28, 2)
            # Sparkle trail
            for i in range(5):
                angle = game_time * 2 + i * 1.2
                sx = cx + math.cos(angle) * 55
                sy = cy + math.sin(angle) * 25 + bob
                sz = int(3 + math.sin(game_time * 3 + i) * 2)
                pygame.draw.circle(screen, (255, 255, int(150 + math.sin(game_time * 4 + i) * 100)), (int(sx), int(sy)), sz)

            # Menu
            options = ["New Game"]
            if has_save:
                options.append("Continue")
            for i, opt in enumerate(options):
                selected = (i == title_selection)
                col = STAR_YELLOW if selected else LIGHT_GRAY
                prefix = ">> " if selected else "   "
                txt = font_lg.render(f"{prefix}{opt}", True, col)
                screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 430 + i * 50))

            # Age rating
            age_txt = font_xs.render("Ages 4+ and 7+ | No scary content!", True, GREEN)
            screen.blit(age_txt, (WIDTH // 2 - age_txt.get_width() // 2, HEIGHT - 50))
            ctrl = font_xs.render("Arrow Keys: Navigate | Z/Space: Select", True, GRAY)
            screen.blit(ctrl, (WIDTH // 2 - ctrl.get_width() // 2, HEIGHT - 30))

        # ═══════════════════════════════════════════════════════════════
        #  DIALOGUE
        # ═══════════════════════════════════════════════════════════════
        elif state == STATE_DIALOGUE:
            dialogue_timer += 1
            dialogue_char_idx = min(len(dialogue_text), int(dialogue_timer * 1.5))

            if keys_just.get(pygame.K_z) or keys_just.get(pygame.K_SPACE) or keys_just.get(pygame.K_RETURN):
                if dialogue_char_idx < len(dialogue_text):
                    dialogue_char_idx = len(dialogue_text)
                else:
                    if dialogue_callback:
                        dialogue_callback()
                    state = STATE_OVERWORLD

            # Draw overworld behind
            if overworld_tiles:
                draw_overworld(screen, overworld_tiles, current_zone, player, camera_x, camera_y, game_time)

            # Dialogue box
            dbox_h = 150
            dbox_y = HEIGHT - dbox_h - 20
            pygame.draw.rect(screen, BLACK, (30, dbox_y, WIDTH - 60, dbox_h), border_radius=10)
            pygame.draw.rect(screen, WHITE, (30, dbox_y, WIDTH - 60, dbox_h), 3, border_radius=10)

            shown = dialogue_text[:dialogue_char_idx]
            lines = shown.split("\n")
            for i, line in enumerate(lines):
                txt = font_battle.render(line, True, WHITE)
                screen.blit(txt, (55, dbox_y + 15 + i * 24))

            # Flashing continue prompt
            if dialogue_char_idx >= len(dialogue_text) and int(game_time * 3) % 2:
                cont = font_xs.render("[Z / SPACE]", True, STAR_YELLOW)
                screen.blit(cont, (WIDTH - 150, dbox_y + dbox_h - 25))

        # ═══════════════════════════════════════════════════════════════
        #  INVENTORY
        # ═══════════════════════════════════════════════════════════════
        elif state == STATE_INVENTORY:
            if keys_just.get(pygame.K_UP) or keys_just.get(pygame.K_w):
                inv_index = max(0, inv_index - 1)
                SFX_DODGE.play()
            if keys_just.get(pygame.K_DOWN) or keys_just.get(pygame.K_s):
                inv_index = min(len(player.inventory) - 1, inv_index + 1)
                SFX_DODGE.play()
            if keys_just.get(pygame.K_z) or keys_just.get(pygame.K_SPACE):
                if player.inventory:
                    item_name = player.inventory[inv_index]
                    item_data = ITEMS.get(item_name, {})
                    if item_data.get("type") == "heal":
                        heal = item_data["value"]
                        player.hp = min(player.max_hp, player.hp + heal)
                        player.inventory.pop(inv_index)
                        SFX_HEAL.play()
                        inv_index = min(inv_index, max(0, len(player.inventory) - 1))
                        show_dialogue(f"Used {item_name}! Healed {heal} HP!", lambda: None)
                        state = STATE_DIALOGUE
            if keys_just.get(pygame.K_x) or keys_just.get(pygame.K_ESCAPE):
                SFX_CANCEL.play()
                state = STATE_OVERWORLD

            # Draw
            if overworld_tiles:
                draw_overworld(screen, overworld_tiles, current_zone, player, camera_x, camera_y, game_time)
            # Overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            # Inventory panel
            panel_w, panel_h = 500, 450
            panel_x = WIDTH // 2 - panel_w // 2
            panel_y = HEIGHT // 2 - panel_h // 2
            pygame.draw.rect(screen, (20, 15, 35), (panel_x, panel_y, panel_w, panel_h), border_radius=12)
            pygame.draw.rect(screen, STAR_YELLOW, (panel_x, panel_y, panel_w, panel_h), 3, border_radius=12)

            title = font_lg.render("Inventory", True, STAR_YELLOW)
            screen.blit(title, (panel_x + panel_w // 2 - title.get_width() // 2, panel_y + 10))

            # Stats
            stats = font_sm.render(f"LV {player.level}  HP {player.hp}/{player.max_hp}  ATK {player.atk}  DEF {player.defense}  Gold {player.gold}", True, WHITE)
            screen.blit(stats, (panel_x + 15, panel_y + 50))

            xp_txt = font_xs.render(f"XP: {player.xp}/{player.xp_next}  Friends: {player.friends_made}  Zone: {current_zone['name']}", True, LIGHT_GRAY)
            screen.blit(xp_txt, (panel_x + 15, panel_y + 72))

            # Items
            if player.inventory:
                for i, item_name in enumerate(player.inventory):
                    if i > 10:
                        more = font_xs.render(f"... and {len(player.inventory) - 10} more", True, GRAY)
                        screen.blit(more, (panel_x + 30, panel_y + 100 + i * 28))
                        break
                    selected = (i == inv_index)
                    item_data = ITEMS.get(item_name, {})
                    col = STAR_YELLOW if selected else LIGHT_GRAY
                    prefix = "> " if selected else "  "
                    txt = font_battle.render(f"{prefix}{item_name}", True, col)
                    screen.blit(txt, (panel_x + 30, panel_y + 100 + i * 28))
                    if selected and item_data.get("desc"):
                        desc = font_xs.render(item_data["desc"], True, CYAN)
                        screen.blit(desc, (panel_x + 15, panel_y + panel_h - 40))
            else:
                empty = font_battle.render("No items!", True, GRAY)
                screen.blit(empty, (panel_x + panel_w // 2 - empty.get_width() // 2, panel_y + 150))

            hint = font_xs.render("Z: Use | X: Close", True, GRAY)
            screen.blit(hint, (panel_x + panel_w // 2 - hint.get_width() // 2, panel_y + panel_h - 20))

        # ═══════════════════════════════════════════════════════════════
        #  OVERWORLD
        # ═══════════════════════════════════════════════════════════════
        elif state == STATE_OVERWORLD:
            if step_cooldown > 0:
                step_cooldown -= 1

            # Movement
            moved = False
            nx, ny = player.x, player.y
            if step_cooldown <= 0:
                if keys_pressed.get(pygame.K_LEFT) or keys_pressed.get(pygame.K_a):
                    nx -= 1; player.facing = "left"; moved = True
                elif keys_pressed.get(pygame.K_RIGHT) or keys_pressed.get(pygame.K_d):
                    nx += 1; player.facing = "right"; moved = True
                elif keys_pressed.get(pygame.K_UP) or keys_pressed.get(pygame.K_w):
                    ny -= 1; player.facing = "up"; moved = True
                elif keys_pressed.get(pygame.K_DOWN) or keys_pressed.get(pygame.K_s):
                    ny += 1; player.facing = "down"; moved = True

            if moved and 0 <= nx < OW_MAP_W and 0 <= ny < OW_MAP_H:
                tile = overworld_tiles[ny][nx]
                if tile != "wall":
                    player.x = nx
                    player.y = ny
                    step_cooldown = 8
                    SFX_STEP.play()

                    # Check tile interactions
                    if tile == "encounter" and player.zone_encounters_left > 0:
                        overworld_tiles[ny][nx] = "collected"
                        player.zone_encounters_left -= 1
                        # Start battle!
                        zone_name = current_zone["name"]
                        monster_list = MONSTERS_BY_ZONE.get(zone_name, MONSTERS_BY_ZONE["Sunny Meadow"])
                        mdef = random.choice(monster_list)
                        battle = Battle(player, mdef)
                        state = STATE_BATTLE
                        SFX_ENCOUNTER.play()
                        # Spawn particles
                        for _ in range(20):
                            particles.append(Particle(
                                WIDTH // 2 + random.randint(-50, 50),
                                HEIGHT // 2 + random.randint(-50, 50),
                                random.uniform(-2, 2), random.uniform(-3, 0),
                                random.choice([STAR_YELLOW, WHITE, CYAN]),
                                random.randint(20, 40)))

                    elif tile == "item":
                        item_name = item_positions.get((nx, ny))
                        if item_name:
                            if player.add_item(item_name):
                                overworld_tiles[ny][nx] = "collected"
                                SFX_SPARKLE.play()
                                show_dialogue(f"Found {item_name}!\n{ITEMS.get(item_name, {}).get('desc', '')}")
                            else:
                                show_dialogue("Your bag is full!")

                    elif tile == "exit":
                        next_idx = player.zone_index + 1
                        if next_idx < len(ZONES):
                            if player.zone_encounters_left <= 0:
                                load_zone(next_idx)
                                save_game(player)
                                show_dialogue(f"Welcome to {ZONES[next_idx]['name']}!\n{ZONES[next_idx]['desc']}")
                            else:
                                show_dialogue(f"There are still {player.zone_encounters_left} creature(s)\nto meet in this zone! Look for the\nsparkly tiles!")

            # Open inventory
            if keys_just.get(pygame.K_x) or keys_just.get(pygame.K_ESCAPE):
                state = STATE_INVENTORY
                inv_index = 0

            # Camera follow
            target_cx = player.x * OW_TILE - WIDTH // 2 + OW_TILE // 2
            target_cy = player.y * OW_TILE - HEIGHT // 2 + OW_TILE // 2
            camera_x += (target_cx - camera_x) * 0.15
            camera_y += (target_cy - camera_y) * 0.15

            # Draw
            draw_overworld(screen, overworld_tiles, current_zone, player, camera_x, camera_y, game_time)

            # Draw zone description if just entered
            desc_txt = font_xs.render(current_zone["desc"], True, WHITE)
            screen.blit(desc_txt, (WIDTH // 2 - desc_txt.get_width() // 2, HEIGHT - 50))

            # Encounters remaining
            enc_txt = font_xs.render(f"Creatures left: {player.zone_encounters_left}", True, STAR_YELLOW)
            screen.blit(enc_txt, (15, 52))

        # ═══════════════════════════════════════════════════════════════
        #  BATTLE
        # ═══════════════════════════════════════════════════════════════
        elif state == STATE_BATTLE:
            result = battle.update(keys_pressed, keys_just)
            battle.draw(screen)

            if result:
                if result == "win" or result == "spare":
                    save_game(player)
                    state = STATE_OVERWORLD
                    # Check if all encounters done and last zone
                    if player.zone_encounters_left <= 0 and player.zone_index == len(ZONES) - 1:
                        state = STATE_WIN
                elif result == "lose":
                    state = STATE_GAME_OVER

        # ═══════════════════════════════════════════════════════════════
        #  GAME OVER
        # ═══════════════════════════════════════════════════════════════
        elif state == STATE_GAME_OVER:
            screen.fill((15, 5, 20))
            # Big sad star
            cx, cy = WIDTH // 2, 250
            bob = math.sin(game_time * 2) * 5
            r = 40
            pts = []
            for i in range(5):
                a = math.radians(i * 72 - 90)
                pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r + bob))
                a2 = math.radians(i * 72 + 36 - 90)
                pts.append((cx + math.cos(a2) * r * 0.4, cy + math.sin(a2) * r * 0.4 + bob))
            pygame.draw.polygon(screen, (150, 150, 80), pts)  # dimmed star
            # Sad face
            pygame.draw.circle(screen, BLACK, (int(cx - 10), int(cy - 5 + bob)), 4)
            pygame.draw.circle(screen, BLACK, (int(cx + 10), int(cy - 5 + bob)), 4)
            pygame.draw.arc(screen, BLACK, (int(cx - 8), int(cy + 5 + bob), 16, 10), 0, 3.14, 2)  # frown

            title = font_xl.render("Oh no!", True, RED)
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
            sub = font_md.render("You got bonked too much!", True, PINK)
            screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 340))
            sub2 = font_md.render("Don't worry, you can try again!", True, WHITE)
            screen.blit(sub2, (WIDTH // 2 - sub2.get_width() // 2, 375))

            options = ["Try Again (heal up!)", "Return to Title"]
            for i, opt in enumerate(options):
                selected = (i == title_selection)
                col = STAR_YELLOW if selected else LIGHT_GRAY
                prefix = ">> " if selected else "   "
                txt = font_lg.render(f"{prefix}{opt}", True, col)
                screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 440 + i * 55))

            if keys_just.get(pygame.K_UP) or keys_just.get(pygame.K_w):
                title_selection = 0; SFX_DODGE.play()
            if keys_just.get(pygame.K_DOWN) or keys_just.get(pygame.K_s):
                title_selection = 1; SFX_DODGE.play()
            if keys_just.get(pygame.K_z) or keys_just.get(pygame.K_SPACE):
                SFX_CONFIRM.play()
                if title_selection == 0:
                    # Revive with half HP
                    player.hp = player.max_hp // 2
                    state = STATE_OVERWORLD
                    # Re-add the encounter tile
                    if overworld_tiles:
                        for ty in range(OW_MAP_H):
                            for tx in range(OW_MAP_W):
                                pass  # encounters stay collected on death
                else:
                    state = STATE_TITLE
                    title_selection = 0
                    has_save = load_game() is not None

        # ═══════════════════════════════════════════════════════════════
        #  WIN SCREEN
        # ═══════════════════════════════════════════════════════════════
        elif state == STATE_WIN:
            screen.fill((10, 5, 25))

            # Rainbow background effect
            for i in range(20):
                rng2 = random.Random(i * 7)
                rx = rng2.randint(0, WIDTH)
                ry = rng2.randint(0, HEIGHT)
                colors = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK]
                rc = colors[i % len(colors)]
                phase = math.sin(game_time * 2 + i * 0.5)
                sz = int(20 + phase * 15)
                pygame.draw.circle(screen, rc, (rx, ry), max(2, sz))

            # Stars
            rng = random.Random(123)
            for _ in range(60):
                sx = rng.randint(0, WIDTH)
                sy = rng.randint(0, HEIGHT)
                twinkle = math.sin(game_time * 3 + sx * 0.05) * 0.3 + 0.7
                pygame.draw.circle(screen, (int(255 * twinkle), int(255 * twinkle), int(200 * twinkle)),
                                   (sx, sy), rng.randint(1, 3))

            title = font_title.render("YOU WIN!", True, STAR_YELLOW)
            shadow = font_title.render("YOU WIN!", True, ORANGE)
            screen.blit(shadow, (WIDTH // 2 - title.get_width() // 2 + 3, 83))
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))

            # Happy star
            cx, cy = WIDTH // 2, 240
            bob = math.sin(game_time * 3) * 8
            spin = game_time * 30
            r = 40
            pts = []
            for i in range(5):
                a = math.radians(i * 72 - 90 + spin)
                pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r + bob))
                a2 = math.radians(i * 72 + 36 - 90 + spin)
                pts.append((cx + math.cos(a2) * r * 0.4, cy + math.sin(a2) * r * 0.4 + bob))
            pygame.draw.polygon(screen, STAR_YELLOW, pts)
            pygame.draw.polygon(screen, GOLD, pts, 3)
            # Happy face
            pygame.draw.circle(screen, BLACK, (int(cx - 10), int(cy - 5 + bob)), 5)
            pygame.draw.circle(screen, BLACK, (int(cx + 10), int(cy - 5 + bob)), 5)
            pygame.draw.arc(screen, BLACK, (int(cx - 10), int(cy + 3 + bob), 20, 12), 3.14, 6.28, 3)

            sub1 = font_lg.render("You got the Rainbow Crystal back!", True, CYAN)
            screen.blit(sub1, (WIDTH // 2 - sub1.get_width() // 2, 320))
            sub2 = font_md.render("The Grumble King isn't grumpy anymore!", True, PINK)
            screen.blit(sub2, (WIDTH // 2 - sub2.get_width() // 2, 365))

            # Stats
            stats_lines = [
                f"Level: {player.level}",
                f"Friends Made: {player.friends_made}",
                f"Monsters Fought: {player.monsters_fought}",
                f"Gold Collected: {player.gold}",
            ]
            for i, line in enumerate(stats_lines):
                txt = font_md.render(line, True, WHITE)
                screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 420 + i * 35))

            hint = font_sm.render("Press Z to return to title!", True, STAR_YELLOW)
            screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 50))

            if keys_just.get(pygame.K_z) or keys_just.get(pygame.K_SPACE):
                state = STATE_TITLE
                title_selection = 0
                has_save = load_game() is not None

        # ── Draw particles on top ──
        for p in particles:
            p.draw(screen)

        pygame.display.flip()

    # ── Cleanup ──
    save_game(player)
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
