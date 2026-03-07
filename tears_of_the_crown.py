"""
╔══════════════════════════════════════════════════════════════════════╗
║            TEARS OF THE CROWN — 3D Action Adventure                ║
║     Explore the Verdant Realm, conquer Shrines, defeat Bosses      ║
║            and overthrow the Dark Sovereign!                       ║
╚══════════════════════════════════════════════════════════════════════╝

Controls:
  WASD              — Move (camera-relative)
  Mouse Move        — Look around (hold Middle Mouse)
  Left Click        — Left hand action (Sword default)
  Right Click       — Right hand action (Shield default)
  Scroll Wheel      — Switch loadout (1 ↔ 2)
  Middle Mouse Hold — Rotate camera / Look
  Space             — Jump
  Shift             — Sprint
  E                 — Interact (enter shrine, talk, pick up)
  Tab               — Inventory / Loadout customization
  Q                 — Ability wheel
  1-4               — Quick select ability
  F                 — Use selected ability
  ESC               — Pause menu
  M                 — Toggle minimap

Loadouts:
  Loadout 1 (default): Left=Blade of Dawn (sword), Right=Aegis of Light (shield)
  Loadout 2 (customizable): Set via Tab menu
"""

import pygame
import sys
import math
import random
import json
import os
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

try:
    import OpenGL
    OpenGL.ERROR_CHECKING = False
    OpenGL.ERROR_LOGGING = False
    from OpenGL.GL import *
    from OpenGL.GLU import *
except ImportError:
    print("ERROR: PyOpenGL required. Install with: pip install PyOpenGL PyOpenGL_accelerate")
    sys.exit(1)

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# ════════════════════════════════════════════════════════════
# CONSTANTS
# ════════════════════════════════════════════════════════════
SCREEN_W, SCREEN_H = 1280, 800
FPS = 60
SAVE_FILE = "tears_crown_save.json"
WORLD_SIZE = 200
TILE_SIZE = 2.0
VIEW_DIST = 80.0
VIEW_TILES = 40
GRAVITY = -20.0
JUMP_VEL = 8.0
WALK_SPEED = 5.0
SPRINT_SPEED = 9.0
CAM_DIST_DEFAULT = 10.0
CAM_PITCH_DEFAULT = -35.0
CAM_SENSITIVITY = 0.3
PLAYER_HEIGHT = 1.8
ATTACK_RANGE = 2.5
ATTACK_COOLDOWN = 0.4
BOW_RANGE = 30.0
SHRINE_RADIUS = 3.0
INTERACT_RANGE = 3.5

# Colors (RGB tuples)
C_SKY = (0.45, 0.72, 0.95)
C_FOG = (0.55, 0.75, 0.90)
C_SUN = (1.0, 0.95, 0.8)
C_TUNIC_GREEN = (50, 140, 60)
C_TUNIC_BLUE = (40, 90, 170)
C_SKIN = (230, 190, 150)
C_HAIR_BLOND = (230, 210, 120)
C_PANTS_WHITE = (220, 215, 200)
C_BOOTS_BROWN = (120, 80, 40)
C_SWORD_SILVER = (200, 210, 220)
C_SWORD_GLOW = (100, 180, 255)
C_SHIELD_BLUE = (50, 80, 160)
C_SHIELD_GOLD = (220, 190, 60)
C_BOW_BROWN = (140, 90, 50)
C_ARROW_TIP = (180, 180, 190)
C_HEART_RED = (220, 40, 40)
C_STAMINA_GREEN = (60, 200, 90)

# ════════════════════════════════════════════════════════════
# ENUMERATIONS
# ════════════════════════════════════════════════════════════
class GameState(Enum):
    TITLE = "title"
    PLAYING = "playing"
    SHRINE = "shrine"
    BOSS_FIGHT = "boss_fight"
    INVENTORY = "inventory"
    PAUSE = "pause"
    GAME_OVER = "game_over"
    VICTORY = "victory"
    LOADOUT_EDIT = "loadout_edit"
    COOKIE_SHOP = "cookie_shop"
    GRANDMA_KITCHEN = "grandma_kitchen"
    EVIL_GRANDMA = "evil_grandma"
    ANVIL_CRAFT = "anvil_craft"
    CUTSCENE = "cutscene"
    HOUSE = "house"

class Biome(Enum):
    DEEP_WATER = 0
    SHALLOW_WATER = 1
    BEACH = 2
    PLAINS = 3
    FOREST = 4
    MOUNTAIN = 5
    SNOW = 6
    LAVA = 7

class WeaponType(Enum):
    SWORD = "Blade of Dawn"
    SHIELD = "Aegis of Light"
    BOW = "Windcutter Bow"
    SPEAR = "Storm Spear"
    FIRE_ROD = "Flame Rod"
    BOMBS = "Ancient Bombs"
    LANTERN = "Ancient Lantern"
    GREAT_SWORD = "Titan Cleaver"
    SHADOW_BOW = "Shadow Stalker Bow"
    INSANE_BLADE = "Blade of Infinite Edge"
    BROKEN_SWORD = "Decayed Blade"

class AbilityType(Enum):
    ULTRAHAND = "Ultrahand"           # Grab & move objects
    FUSE = "Fuse"                     # Attach items together
    ASCEND = "Ascend"                 # Rise through ceilings
    RECALL = "Recall"                 # Reverse time on objects

class MobType(Enum):
    GRUNKLE = "Grunkle"
    THUGNOK = "Thugnok"
    SKARVYN = "Skarvyn"
    CAVE_FIEND = "Cave Fiend"
    HUSK_CRAWLER = "Husk Crawler"
    GULPWORM = "Gulpworm"
    GRUNKLE_CHIEF = "Grunkle Chief"
    STONEBEAST = "Stonebeast"
    DOOM_GRASP = "Doom Grasp"
    THUNDERMANE = "Thundermane"
    LINUS = "Linus"
    LESSE = "Lesse"

class BossType(Enum):
    FROST_SERPENT = "Frost Serpent"
    SLUDGE_BEAST = "Sludge Beast"
    MAGMA_GOLEM = "Magma Golem"
    HIVE_MATRIARCH = "Hive Matriarch"
    CORRUPTED_AUTOMATON = "Corrupted Automaton"
    DARK_SOVEREIGN = "The Dark Sovereign"
    COOKIE_MONSTER = "Cookie Monster"
    GARDON_MOK = "Gardon Mok"

class ShrineType(Enum):
    TRIAL_OF_MIGHT = "Trial of Might"
    GRASP_TRIAL = "Grasp Trial"
    RISING_TRIAL = "Rising Trial"
    TIMEFLOW_TRIAL = "Timeflow Trial"
    FORGE_TRIAL = "Forge Trial"
    WIND_TRIAL = "Wind Trial"
    FIRE_TRIAL = "Fire Trial"
    ICE_TRIAL = "Ice Trial"
    LIGHTNING_TRIAL = "Lightning Trial"
    SHADOW_TRIAL = "Shadow Trial"
    WATER_TRIAL = "Water Trial"
    ANCIENT_GIFT = "Ancient Gift"

# ════════════════════════════════════════════════════════════
# MATH UTILITIES
# ════════════════════════════════════════════════════════════
def lerp(a, b, t):
    return a + (b - a) * max(0.0, min(1.0, t))

def dist2d(x1, z1, x2, z2):
    return math.sqrt((x2 - x1) ** 2 + (z2 - z1) ** 2)

def dist3d(x1, y1, z1, x2, y2, z2):
    return math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)

def normalize2d(x, z):
    l = math.sqrt(x*x + z*z)
    if l < 0.0001:
        return 0.0, 0.0
    return x / l, z / l

def angle_diff(a, b):
    d = (b - a) % 360
    if d > 180:
        d -= 360
    return d

# ════════════════════════════════════════════════════════════
# NOISE / TERRAIN GENERATION
# ════════════════════════════════════════════════════════════
def _hash2d(ix, iy, seed=0):
    n = (ix * 374761393 + iy * 668265263 + seed * 1013904223) & 0x7FFFFFFF
    n = ((n >> 13) ^ n) & 0x7FFFFFFF
    n = (n * (n * n * 60493 + 19990303) + 1376312589) & 0x7FFFFFFF
    return n / 0x7FFFFFFF

def smooth_noise(x, y, seed=0):
    ix = int(math.floor(x))
    iy = int(math.floor(y))
    fx = x - ix
    fy = y - iy
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    n00 = _hash2d(ix, iy, seed)
    n10 = _hash2d(ix + 1, iy, seed)
    n01 = _hash2d(ix, iy + 1, seed)
    n11 = _hash2d(ix + 1, iy + 1, seed)
    nx0 = n00 + (n10 - n00) * fx
    nx1 = n01 + (n11 - n01) * fx
    return nx0 + (nx1 - nx0) * fy

def fractal_noise(x, y, octaves=5, seed=0):
    val = 0.0
    amp = 1.0
    freq = 1.0
    total = 0.0
    for _ in range(octaves):
        val += smooth_noise(x * freq, y * freq, seed + _) * amp
        total += amp
        amp *= 0.5
        freq *= 2.0
    return val / total

def get_height(wx, wz, seed=42):
    """Get terrain height at world coordinates."""
    nx = wx / (WORLD_SIZE * TILE_SIZE) * 4.0
    nz = wz / (WORLD_SIZE * TILE_SIZE) * 4.0
    h = fractal_noise(nx, nz, 6, seed)
    # Create some flat areas
    if h > 0.35 and h < 0.55:
        h = lerp(h, 0.42, 0.6)
    return h

def get_biome_from_height(h):
    if h < 0.18:
        return Biome.DEEP_WATER
    elif h < 0.25:
        return Biome.SHALLOW_WATER
    elif h < 0.30:
        return Biome.BEACH
    elif h < 0.50:
        return Biome.PLAINS
    elif h < 0.65:
        return Biome.FOREST
    elif h < 0.80:
        return Biome.MOUNTAIN
    else:
        return Biome.SNOW

def get_biome_color(biome, h):
    """Returns (r,g,b) floats 0-1 for terrain rendering."""
    if biome == Biome.DEEP_WATER:
        return (0.1, 0.2, 0.5)
    elif biome == Biome.SHALLOW_WATER:
        return (0.15, 0.35, 0.6)
    elif biome == Biome.BEACH:
        return (0.85, 0.8, 0.55)
    elif biome == Biome.PLAINS:
        g = 0.45 + (h - 0.3) * 1.5
        return (0.25, min(0.7, g), 0.15)
    elif biome == Biome.FOREST:
        return (0.15, 0.35 + random.random() * 0.05, 0.1)
    elif biome == Biome.MOUNTAIN:
        v = 0.4 + (h - 0.65) * 2
        return (v, v * 0.95, v * 0.85)
    elif biome == Biome.SNOW:
        return (0.9, 0.92, 0.95)
    return (0.4, 0.4, 0.4)

def terrain_y(wx, wz, seed=42):
    """Get actual Y position for world coordinates."""
    h = get_height(wx, wz, seed)
    biome = get_biome_from_height(h)
    if biome in (Biome.DEEP_WATER, Biome.SHALLOW_WATER):
        return -0.5  # Below water surface
    return (h - 0.3) * 15.0  # Scale height

def walkable_y(wx, wz, seed=42):
    """Get the Y the player walks on."""
    h = get_height(wx, wz, seed)
    biome = get_biome_from_height(h)
    if biome == Biome.DEEP_WATER:
        return None  # Can't walk
    if biome == Biome.SHALLOW_WATER:
        return 0.0
    return max(0.0, (h - 0.3) * 15.0)

# ════════════════════════════════════════════════════════════
# OPENGL DRAWING HELPERS
# ════════════════════════════════════════════════════════════
_quad = None

def gl_color(r, g, b, a=1.0):
    """Set color from 0-255 ints or 0-1 floats."""
    if isinstance(r, int) or r > 1.0:
        glColor4f(r / 255.0, g / 255.0, b / 255.0, a)
    else:
        glColor4f(r, g, b, a)

def draw_cube(cx, cy, cz, sx, sy, sz, color, shade=True):
    """Draw axis-aligned cube centered at (cx,cy,cz) with half-sizes (sx,sy,sz)."""
    r, g, b = [c / 255.0 if c > 1 else c for c in color]
    x0, y0, z0 = cx - sx, cy - sy, cz - sz
    x1, y1, z1 = cx + sx, cy + sy, cz + sz

    faces = [
        # normal, vertices, shade_mult
        ((0, 0, 1), [(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)], 1.0),
        ((0, 0,-1), [(x1,y0,z0),(x0,y0,z0),(x0,y1,z0),(x1,y1,z0)], 0.85),
        ((0, 1, 0), [(x0,y1,z0),(x0,y1,z1),(x1,y1,z1),(x1,y1,z0)], 1.1),
        ((0,-1, 0), [(x0,y0,z1),(x0,y0,z0),(x1,y0,z0),(x1,y0,z1)], 0.6),
        ((1, 0, 0), [(x1,y0,z0),(x1,y0,z1),(x1,y1,z1),(x1,y1,z0)], 0.9),
        ((-1,0, 0), [(x0,y0,z1),(x0,y0,z0),(x0,y1,z0),(x0,y1,z1)], 0.75),
    ]
    glBegin(GL_QUADS)
    for normal, verts, sm in faces:
        if shade:
            glColor3f(min(1, r * sm), min(1, g * sm), min(1, b * sm))
        else:
            glColor3f(r, g, b)
        glNormal3f(*normal)
        for v in verts:
            glVertex3f(*v)
    glEnd()

def draw_sphere(cx, cy, cz, radius, color, slices=12, stacks=8):
    """Draw a colored sphere."""
    r, g, b = [c / 255.0 if c > 1 else c for c in color]
    glColor3f(r, g, b)
    glPushMatrix()
    glTranslatef(cx, cy, cz)
    q = gluNewQuadric()
    gluQuadricNormals(q, GLU_SMOOTH)
    gluSphere(q, radius, slices, stacks)
    gluDeleteQuadric(q)
    glPopMatrix()

def draw_cylinder(cx, cy, cz, radius, height, color, slices=10):
    """Draw a vertical cylinder."""
    r, g, b = [c / 255.0 if c > 1 else c for c in color]
    glColor3f(r, g, b)
    glPushMatrix()
    glTranslatef(cx, cy, cz)
    glRotatef(-90, 1, 0, 0)
    q = gluNewQuadric()
    gluQuadricNormals(q, GLU_SMOOTH)
    gluCylinder(q, radius, radius, height, slices, 1)
    gluDeleteQuadric(q)
    glPopMatrix()

def draw_cone(cx, cy, cz, radius, height, color, slices=10):
    """Draw a cone pointing up."""
    r, g, b = [c / 255.0 if c > 1 else c for c in color]
    glColor3f(r, g, b)
    glPushMatrix()
    glTranslatef(cx, cy, cz)
    glRotatef(-90, 1, 0, 0)
    q = gluNewQuadric()
    gluCylinder(q, radius, 0.0, height, slices, 1)
    gluDeleteQuadric(q)
    glPopMatrix()

def draw_flat_quad(x, z, size, y, color):
    """Draw a flat horizontal quad (for terrain tiles)."""
    r, g, b = color
    glColor3f(r, g, b)
    hs = size * 0.5
    glNormal3f(0, 1, 0)
    glVertex3f(x - hs, y, z - hs)
    glVertex3f(x + hs, y, z - hs)
    glVertex3f(x + hs, y, z + hs)
    glVertex3f(x - hs, y, z + hs)

def draw_shadow_circle(x, y, z, radius):
    """Draw a shadow circle on the ground."""
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0, 0, 0, 0.3)
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(x, y + 0.02, z)
    for i in range(21):
        a = i / 20.0 * math.pi * 2
        glVertex3f(x + math.cos(a) * radius, y + 0.02, z + math.sin(a) * radius)
    glEnd()
    glDisable(GL_BLEND)
    glEnable(GL_LIGHTING)

def draw_ground_tile_batch(tiles):
    """Draw many ground tiles efficiently."""
    glBegin(GL_QUADS)
    for (x, z, size, y, color) in tiles:
        draw_flat_quad(x, z, size, y, color)
    glEnd()

# ════════════════════════════════════════════════════════════
# PARTICLE SYSTEM
# ════════════════════════════════════════════════════════════
class Particle:
    __slots__ = ['x','y','z','vx','vy','vz','life','max_life','color','size']
    def __init__(self, x, y, z, vx, vy, vz, life, color, size=0.1):
        self.x, self.y, self.z = x, y, z
        self.vx, self.vy, self.vz = vx, vy, vz
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size

class ParticleSystem:
    def __init__(self):
        self.particles: List[Particle] = []

    def emit(self, x, y, z, count, color, spread=2.0, speed=3.0, life=1.0, size=0.1):
        for _ in range(count):
            vx = (random.random() - 0.5) * spread * speed
            vy = random.random() * speed * 1.5
            vz = (random.random() - 0.5) * spread * speed
            self.particles.append(Particle(x, y, z, vx, vy, vz, life, color, size))

    def emit_hit(self, x, y, z):
        self.emit(x, y, z, 8, (255, 100, 50), spread=1.0, speed=4.0, life=0.5, size=0.08)

    def emit_shrine_glow(self, x, y, z):
        self.emit(x, y + 2, z, 2, (100, 200, 255), spread=0.5, speed=1.5, life=2.0, size=0.06)

    def emit_death(self, x, y, z, color=(80, 0, 120)):
        self.emit(x, y + 0.5, z, 20, color, spread=2.0, speed=5.0, life=1.5, size=0.12)

    def update(self, dt):
        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += GRAVITY * 0.3 * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.z += p.vz * dt
            alive.append(p)
        self.particles = alive

    def draw(self):
        if not self.particles:
            return
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # Draw particles as small spheres
        for p in self.particles:
            alpha = p.life / p.max_life
            if alpha > 0.05:
                r, g, b = p.color
                s = p.size * alpha
                glColor4f(r/255, g/255, b/255, alpha)
                glPushMatrix()
                glTranslatef(p.x, p.y, p.z)
                q = gluNewQuadric()
                gluSphere(q, s, 4, 4)
                gluDeleteQuadric(q)
                glPopMatrix()
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

# ════════════════════════════════════════════════════════════
# SOUND GENERATOR
# ════════════════════════════════════════════════════════════
def gen_sound(freq=440, duration=0.15, volume=0.3, wave='square'):
    """Generate a simple sound effect."""
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    buf = bytearray(n_samples * 2)
    for i in range(n_samples):
        t = i / sample_rate
        env = max(0, 1.0 - t / duration)
        if wave == 'square':
            val = volume * env * (1.0 if math.sin(2.0 * math.pi * freq * t) > 0 else -1.0)
        elif wave == 'saw':
            val = volume * env * (2.0 * (t * freq % 1.0) - 1.0)
        elif wave == 'sine':
            val = volume * env * math.sin(2.0 * math.pi * freq * t)
        elif wave == 'noise':
            val = volume * env * (random.random() * 2 - 1)
        else:
            val = volume * env * math.sin(2.0 * math.pi * freq * t)
        sample = max(-32767, min(32767, int(val * 32767)))
        buf[i*2] = sample & 0xFF
        buf[i*2+1] = (sample >> 8) & 0xFF
    return pygame.mixer.Sound(buffer=bytes(buf))

# Pre-generate sounds
SFX = {}
def init_sounds():
    SFX['sword'] = gen_sound(280, 0.15, 0.25, 'saw')
    SFX['shield'] = gen_sound(180, 0.1, 0.2, 'square')
    SFX['hit'] = gen_sound(150, 0.2, 0.3, 'noise')
    SFX['bow'] = gen_sound(600, 0.12, 0.2, 'sine')
    SFX['pickup'] = gen_sound(880, 0.15, 0.2, 'sine')
    SFX['shrine_enter'] = gen_sound(440, 0.5, 0.15, 'sine')
    SFX['shrine_complete'] = gen_sound(660, 0.8, 0.2, 'sine')
    SFX['boss_roar'] = gen_sound(80, 0.6, 0.35, 'saw')
    SFX['death'] = gen_sound(100, 0.4, 0.3, 'noise')
    SFX['loadout'] = gen_sound(520, 0.1, 0.15, 'sine')
    SFX['jump'] = gen_sound(350, 0.1, 0.15, 'sine')
    SFX['menu'] = gen_sound(440, 0.08, 0.1, 'sine')
    SFX['hurt'] = gen_sound(200, 0.15, 0.25, 'noise')

def play_sfx(name):
    if name in SFX:
        SFX[name].play()

# ════════════════════════════════════════════════════════════
# WEAPON & LOADOUT DATA
# ════════════════════════════════════════════════════════════
WEAPON_DATA = {
    WeaponType.SWORD: {
        'name': 'Sword of He Not Da Man', 'damage': 15, 'range': ATTACK_RANGE,
        'cooldown': 0.4, 'type': 'melee', 'color': C_SWORD_SILVER
    },
    WeaponType.SHIELD: {
        'name': 'Aegis of Light', 'damage': 0, 'range': 0,
        'cooldown': 0.2, 'type': 'defense', 'color': C_SHIELD_BLUE
    },
    WeaponType.BOW: {
        'name': 'Windcutter Bow', 'damage': 12, 'range': BOW_RANGE,
        'cooldown': 0.8, 'type': 'ranged', 'color': C_BOW_BROWN
    },
    WeaponType.SPEAR: {
        'name': 'Storm Spear', 'damage': 18, 'range': 3.5,
        'cooldown': 0.6, 'type': 'melee', 'color': (160, 160, 200)
    },
    WeaponType.FIRE_ROD: {
        'name': 'Flame Rod', 'damage': 20, 'range': 15.0,
        'cooldown': 1.0, 'type': 'magic', 'color': (220, 80, 30)
    },
    WeaponType.BOMBS: {
        'name': 'Ancient Bombs', 'damage': 30, 'range': 8.0,
        'cooldown': 2.0, 'type': 'explosive', 'color': (100, 100, 120)
    },
    WeaponType.LANTERN: {
        'name': 'Ancient Lantern', 'damage': 8, 'range': 6.0,
        'cooldown': 0.6, 'type': 'magic', 'color': (255, 200, 80)
    },
    WeaponType.GREAT_SWORD: {
        'name': 'Titan Cleaver', 'damage': 35, 'range': 3.5,
        'cooldown': 1.0, 'type': 'melee', 'color': (160, 150, 170)
    },
    WeaponType.SHADOW_BOW: {
        'name': 'Shadow Stalker Bow', 'damage': 25, 'range': 40.0,
        'cooldown': 0.6, 'type': 'ranged', 'color': (50, 20, 80)
    },
    WeaponType.INSANE_BLADE: {
        'name': 'Blade of Infinite Edge', 'damage': 50, 'range': 4.0,
        'cooldown': 0.3, 'type': 'melee', 'color': (255, 50, 255)
    },
    WeaponType.BROKEN_SWORD: {
        'name': 'Decayed Blade', 'damage': 1, 'range': ATTACK_RANGE,
        'cooldown': 0.5, 'type': 'melee', 'color': (100, 80, 70)
    },
}

@dataclass
class Loadout:
    left: WeaponType = WeaponType.SWORD
    right: WeaponType = WeaponType.SHIELD

# ════════════════════════════════════════════════════════════
# MOB DATA
# ════════════════════════════════════════════════════════════
MOB_DATA = {
    MobType.GRUNKLE: {
        'hp': 20, 'damage': 5, 'speed': 2.5, 'xp': 10,
        'color': (100, 160, 60), 'size': 0.6, 'aggro_range': 10.0,
        'desc': 'Small goblin-like creature'
    },
    MobType.THUGNOK: {
        'hp': 45, 'damage': 12, 'speed': 2.0, 'xp': 25,
        'color': (80, 60, 140), 'size': 1.0, 'aggro_range': 12.0,
        'desc': 'Tall brutish warrior'
    },
    MobType.SKARVYN: {
        'hp': 30, 'damage': 8, 'speed': 4.0, 'xp': 20,
        'color': (60, 140, 80), 'size': 0.7, 'aggro_range': 14.0,
        'desc': 'Quick lizard-like fighter'
    },
    MobType.CAVE_FIEND: {
        'hp': 25, 'damage': 10, 'speed': 3.0, 'xp': 18,
        'color': (100, 40, 120), 'size': 0.65, 'aggro_range': 8.0,
        'desc': 'Lurks in dark places'
    },
    MobType.HUSK_CRAWLER: {
        'hp': 35, 'damage': 7, 'speed': 2.2, 'xp': 15,
        'color': (140, 120, 80), 'size': 0.5, 'aggro_range': 9.0,
        'desc': 'Undead insect creature'
    },
    MobType.GULPWORM: {
        'hp': 40, 'damage': 6, 'speed': 1.5, 'xp': 22,
        'color': (200, 130, 160), 'size': 0.8, 'aggro_range': 6.0,
        'desc': 'Blob that swallows prey'
    },
    MobType.GRUNKLE_CHIEF: {
        'hp': 60, 'damage': 15, 'speed': 2.8, 'xp': 40,
        'color': (180, 60, 50), 'size': 0.85, 'aggro_range': 14.0,
        'desc': 'Leader of the Grunkles'
    },
    MobType.STONEBEAST: {
        'hp': 100, 'damage': 20, 'speed': 1.2, 'xp': 60,
        'color': (130, 130, 130), 'size': 1.4, 'aggro_range': 10.0,
        'desc': 'Living rock golem'
    },
    MobType.DOOM_GRASP: {
        'hp': 50, 'damage': 18, 'speed': 3.5, 'xp': 45,
        'color': (40, 10, 60), 'size': 0.7, 'aggro_range': 12.0,
        'desc': 'Dark hands reaching from shadow'
    },
    MobType.THUNDERMANE: {
        'hp': 200, 'damage': 30, 'speed': 5.0, 'xp': 120,
        'color': (200, 200, 220), 'size': 1.6, 'aggro_range': 20.0,
        'desc': 'Fearsome centaur beast'
    },
    MobType.LINUS: {
        'hp': 80, 'damage': 12, 'speed': 3.5, 'xp': 50,
        'color': (200, 180, 100), 'size': 0.9, 'aggro_range': 15.0,
        'desc': 'Blanket-wielding wanderer who steals your warmth'
    },
    MobType.LESSE: {
        'hp': 30, 'damage': 0, 'speed': 1.5, 'xp': 5,
        'color': (255, 230, 180), 'size': 0.7, 'aggro_range': 0.0,
        'desc': 'Extremely fat chicken creature - can be fused!'
    },
}

BOSS_DATA = {
    BossType.FROST_SERPENT: {
        'hp': 300, 'damage': 25, 'speed': 3.0, 'xp': 500,
        'color': (150, 200, 240), 'size': 3.0,
        'phases': 2, 'desc': 'Serpentine ice dragon of the Frost Peaks'
    },
    BossType.SLUDGE_BEAST: {
        'hp': 250, 'damage': 20, 'speed': 2.0, 'xp': 450,
        'color': (80, 50, 120), 'size': 2.5,
        'phases': 2, 'desc': 'Amorphous sludge from the depths'
    },
    BossType.MAGMA_GOLEM: {
        'hp': 350, 'damage': 30, 'speed': 1.5, 'xp': 550,
        'color': (220, 100, 30), 'size': 3.5,
        'phases': 2, 'desc': 'Volcanic titan of the Scorched Wastes'
    },
    BossType.HIVE_MATRIARCH: {
        'hp': 280, 'damage': 22, 'speed': 3.5, 'xp': 480,
        'color': (180, 160, 50), 'size': 2.8,
        'phases': 2, 'desc': 'Queen of the insect horde'
    },
    BossType.CORRUPTED_AUTOMATON: {
        'hp': 400, 'damage': 28, 'speed': 2.5, 'xp': 600,
        'color': (60, 180, 160), 'size': 3.2,
        'phases': 3, 'desc': 'Ancient mechanical construct gone haywire'
    },
    BossType.DARK_SOVEREIGN: {
        'hp': 600, 'damage': 35, 'speed': 4.0, 'xp': 1000,
        'color': (30, 10, 40), 'size': 2.5,
        'phases': 3, 'desc': 'The ultimate evil, lord of darkness'
    },
    BossType.COOKIE_MONSTER: {
        'hp': 200, 'damage': 15, 'speed': 3.0, 'xp': 300,
        'color': (80, 140, 200), 'size': 2.0,
        'phases': 2, 'desc': 'Furry blue beast that devours all cookies!'
    },
    BossType.GARDON_MOK: {
        'hp': 500, 'damage': 30, 'speed': 3.5, 'xp': 0,
        'color': (50, 20, 30), 'size': 1.8,
        'phases': 2, 'desc': 'The Demon Dwarf King, unleashed from his ancient seal'
    },
}

# ════════════════════════════════════════════════════════════
# SHRINE DATA & DEFINITIONS
# ════════════════════════════════════════════════════════════
SHRINE_DEFINITIONS = [
    # (shrine_type, world_x, world_z, description)
    (ShrineType.TRIAL_OF_MIGHT, 50, 60, "Defeat all enemies to earn the Crown Shard"),
    (ShrineType.GRASP_TRIAL, 120, 40, "Use Telekinesis to move blocks onto switches"),
    (ShrineType.RISING_TRIAL, 80, 150, "Find the path upward using Phase Rise"),
    (ShrineType.TIMEFLOW_TRIAL, 160, 100, "Reverse time to solve the puzzle"),
    (ShrineType.FORGE_TRIAL, 30, 130, "Combine objects to forge the key"),
    (ShrineType.WIND_TRIAL, 140, 170, "Ride wind currents to the goal"),
    (ShrineType.FIRE_TRIAL, 170, 50, "Navigate through flames unscathed"),
    (ShrineType.ICE_TRIAL, 60, 30, "Freeze and thaw to create a path"),
    (ShrineType.LIGHTNING_TRIAL, 100, 80, "Redirect lightning to power the gate"),
    (ShrineType.SHADOW_TRIAL, 40, 90, "Navigate the darkness with only your wits"),
    (ShrineType.WATER_TRIAL, 130, 120, "Control water levels to progress"),
    (ShrineType.ANCIENT_GIFT, 100, 100, "A reward awaits the worthy explorer"),
    # Additional shrines in remote areas
    (ShrineType.TRIAL_OF_MIGHT, 180, 180, "An advanced combat challenge"),
    (ShrineType.GRASP_TRIAL, 20, 180, "Complex block puzzle in the wilds"),
    (ShrineType.RISING_TRIAL, 190, 20, "The tallest climb in the realm"),
    (ShrineType.FIRE_TRIAL, 150, 140, "Inferno gauntlet of the wastes"),
]

# Boss spawn locations
BOSS_SPAWNS = [
    (BossType.FROST_SERPENT, 40, 20),    # Northwest - snow/mountains
    (BossType.SLUDGE_BEAST, 160, 160),   # Southeast - swamp
    (BossType.MAGMA_GOLEM, 180, 30),     # Northeast - volcanic
    (BossType.HIVE_MATRIARCH, 30, 170),  # Southwest - forest
    (BossType.CORRUPTED_AUTOMATON, 100, 190),  # South - ruins
    (BossType.DARK_SOVEREIGN, 100, 10),  # North - dark castle
]

# Cookie Monster NPC location (friendly vendor)
COOKIE_MONSTER_POS = (60, 100)  # West - cookie cave

# Grandma NPC locations
GRANDMA_POS = (120, 160)      # Southeast - Grandma's cottage (good)
EVIL_GRANDMA_POS = (170, 80)  # East - Evil Grandma's hut

# House data
HOUSE_COST = 50  # Rupees to buy a house
HOUSE_POS = (95, 105)  # Near spawn

# Anvil crafting recipes
ANVIL_RECIPES = [
    {'weapon': WeaponType.LANTERN, 'cost': 15, 'desc': '5 iron + 3 glass'},
    {'weapon': WeaponType.GREAT_SWORD, 'cost': 40, 'desc': '10 iron + 5 diamond'},
    {'weapon': WeaponType.SHADOW_BOW, 'cost': 35, 'desc': '8 shadow + 4 string'},
    {'weapon': WeaponType.SPEAR, 'cost': 20, 'desc': '6 iron + 2 wood'},
    {'weapon': WeaponType.INSANE_BLADE, 'cost': 100, 'desc': '20 diamond + 10 shadow + SOUL'},
]

# Grandma recipes (3 cookies to access kitchen, makes one)
GRANDMA_RECIPES = [
    {'name': 'Cookie Cake', 'desc': 'Restores full HP + 20 bonus', 'effect': 'heal', 'value': 999},
    {'name': 'Power Cookie', 'desc': '+10 attack for 60 seconds', 'effect': 'attack_boost', 'value': 60},
    {'name': 'Speed Cookie', 'desc': 'Fully restores stamina', 'effect': 'speed_boost', 'value': 60},
    {'name': 'Shield Cookie', 'desc': '10 seconds invincibility + 30 HP', 'effect': 'shield', 'value': 30},
]

# ════════════════════════════════════════════════════════════
# ENTITY CLASSES
# ════════════════════════════════════════════════════════════
class Entity:
    """Base entity in the 3D world."""
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z
        self.vx, self.vy, self.vz = 0.0, 0.0, 0.0
        self.facing = 0.0  # degrees
        self.hp = 100
        self.max_hp = 100
        self.alive = True
        self.on_ground = True
        self.size = 0.5
        self.hurt_timer = 0.0
        self.attack_timer = 0.0

    def take_damage(self, amount):
        if not self.alive:
            return
        self.hp -= amount
        self.hurt_timer = 0.3
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

class Mob(Entity):
    """Enemy mob in the world."""
    def __init__(self, mob_type, x, y, z):
        super().__init__(x, y, z)
        self.mob_type = mob_type
        data = MOB_DATA[mob_type]
        self.hp = data['hp']
        self.max_hp = data['hp']
        self.damage = data['damage']
        self.speed = data['speed']
        self.xp = data['xp']
        self.color = data['color']
        self.size = data['size']
        self.aggro_range = data['aggro_range']
        self.state = 'idle'  # idle, patrol, chase, attack, stunned
        self.patrol_cx = x
        self.patrol_cz = z
        self.patrol_angle = random.random() * 360
        self.state_timer = 0.0
        self.attack_cooldown = 0.0
        self.stun_timer = 0.0
        self.anim_time = random.random() * 10

    def update(self, dt, player_x, player_y, player_z, seed=42):
        if not self.alive:
            return
        self.anim_time += dt
        self.hurt_timer = max(0, self.hurt_timer - dt)
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        self.state_timer += dt

        dist_to_player = dist2d(self.x, self.z, player_x, player_z)

        # State machine
        if self.stun_timer > 0:
            self.stun_timer -= dt
            self.state = 'stunned'
            return

        if dist_to_player < self.aggro_range:
            if dist_to_player < ATTACK_RANGE * 1.2:
                self.state = 'attack'
            else:
                self.state = 'chase'
        else:
            self.state = 'patrol' if self.state_timer > 2.0 else 'idle'

        if self.state == 'chase':
            dx, dz = normalize2d(player_x - self.x, player_z - self.z)
            self.x += dx * self.speed * dt
            self.z += dz * self.speed * dt
            self.facing = math.degrees(math.atan2(-dx, -dz))
        elif self.state == 'patrol':
            self.patrol_angle += dt * 20
            tx = self.patrol_cx + math.cos(math.radians(self.patrol_angle)) * 5
            tz = self.patrol_cz + math.sin(math.radians(self.patrol_angle)) * 5
            dx, dz = normalize2d(tx - self.x, tz - self.z)
            self.x += dx * self.speed * 0.4 * dt
            self.z += dz * self.speed * 0.4 * dt
            self.facing = math.degrees(math.atan2(-dx, -dz))
            if self.state_timer > 6.0:
                self.state_timer = 0
        elif self.state == 'attack':
            dx, dz = normalize2d(player_x - self.x, player_z - self.z)
            self.facing = math.degrees(math.atan2(-dx, -dz))

        # Stay on terrain
        wy = walkable_y(self.x, self.z, seed)
        if wy is not None:
            self.y = wy
        else:
            # Push back from water
            self.x = self.patrol_cx
            self.z = self.patrol_cz

    def can_attack(self):
        return self.state == 'attack' and self.attack_cooldown <= 0 and self.alive

    def do_attack(self):
        self.attack_cooldown = 1.0 + random.random() * 0.5
        return self.damage

    def draw(self):
        if not self.alive:
            return
        # Lesses use special fat chicken rendering
        if self.mob_type == MobType.LESSE:
            self._draw_as_lesse()
            return
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.facing, 0, 1, 0)

        # Flash red when hurt
        color = (255, 80, 80) if self.hurt_timer > 0 else self.color
        sz = self.size

        # Body
        draw_cube(0, sz * 0.7, 0, sz * 0.35, sz * 0.4, sz * 0.25, color)
        # Head
        head_color = tuple(min(255, c + 30) for c in color)
        draw_sphere(0, sz * 1.3, 0, sz * 0.28, head_color)
        # Arms (swing during attack)
        arm_swing = math.sin(self.anim_time * 8) * 20 if self.state == 'attack' else math.sin(self.anim_time * 3) * 10
        glPushMatrix()
        glTranslatef(sz * 0.45, sz * 0.7, 0)
        glRotatef(arm_swing, 1, 0, 0)
        draw_cube(0, -sz * 0.2, 0, sz * 0.1, sz * 0.25, sz * 0.1, color)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-sz * 0.45, sz * 0.7, 0)
        glRotatef(-arm_swing, 1, 0, 0)
        draw_cube(0, -sz * 0.2, 0, sz * 0.1, sz * 0.25, sz * 0.1, color)
        glPopMatrix()
        # Legs
        leg_swing = math.sin(self.anim_time * 6) * 15 if self.state in ('chase', 'patrol') else 0
        glPushMatrix()
        glTranslatef(sz * 0.15, sz * 0.15, 0)
        glRotatef(leg_swing, 1, 0, 0)
        draw_cube(0, -sz * 0.1, 0, sz * 0.1, sz * 0.2, sz * 0.1, tuple(max(0, c-40) for c in color))
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-sz * 0.15, sz * 0.15, 0)
        glRotatef(-leg_swing, 1, 0, 0)
        draw_cube(0, -sz * 0.1, 0, sz * 0.1, sz * 0.2, sz * 0.1, tuple(max(0, c-40) for c in color))
        glPopMatrix()

        glPopMatrix()

        # Health bar above mob
        if self.hp < self.max_hp:
            self._draw_health_bar()

        # Shadow
        draw_shadow_circle(self.x, self.y + 0.01, self.z, sz * 0.5)

    def _draw_health_bar(self):
        bar_w = self.size * 1.2
        bar_h = 0.08
        bar_y = self.y + self.size * 1.8
        hp_pct = self.hp / self.max_hp
        glDisable(GL_LIGHTING)
        # Background
        draw_cube(self.x, bar_y, self.z, bar_w * 0.5, bar_h, 0.02, (40, 0, 0))
        # Health
        hw = bar_w * 0.5 * hp_pct
        draw_cube(self.x - bar_w * 0.5 * (1 - hp_pct), bar_y, self.z + 0.01, hw, bar_h, 0.02, (220, 40, 40))
        glEnable(GL_LIGHTING)

    def _draw_as_lesse(self):
        """Draw this mob as a Lesse - extremely fat chicken creature."""
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.facing, 0, 1, 0)
        color = (255, 80, 80) if self.hurt_timer > 0 else self.color
        fused = getattr(self, 'fused', False)
        if fused:
            color = (255, 120, 50)
        # Fat round body
        draw_sphere(0, 0.5, 0, 0.6, color)
        draw_sphere(0, 0.4, 0, 0.55, tuple(max(0, c - 20) for c in color))
        # Small head
        head_c = (255, 240, 200) if not fused else (255, 180, 100)
        draw_sphere(0, 1.0, 0.15, 0.22, head_c)
        # Beak
        draw_cube(0, 0.95, 0.38, 0.06, 0.04, 0.1, (255, 180, 50))
        # Eyes
        draw_sphere(-0.08, 1.05, 0.3, 0.04, (0, 0, 0))
        draw_sphere(0.08, 1.05, 0.3, 0.04, (0, 0, 0))
        # Tiny wings
        wing_angle = math.sin(self.anim_time * 5) * 15
        glPushMatrix()
        glTranslatef(0.5, 0.5, 0)
        glRotatef(wing_angle, 0, 0, 1)
        draw_cube(0.15, 0, 0, 0.2, 0.08, 0.15, tuple(max(0, c - 30) for c in color))
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-0.5, 0.5, 0)
        glRotatef(-wing_angle, 0, 0, 1)
        draw_cube(-0.15, 0, 0, 0.2, 0.08, 0.15, tuple(max(0, c - 30) for c in color))
        glPopMatrix()
        # Tiny legs
        draw_cube(0.15, 0.05, 0, 0.05, 0.1, 0.05, (200, 160, 50))
        draw_cube(-0.15, 0.05, 0, 0.05, 0.1, 0.05, (200, 160, 50))
        # Tail feathers
        draw_cube(0, 0.5, -0.45, 0.1, 0.15, 0.1, tuple(max(0, c - 40) for c in color))
        # Fire effect when fused
        if fused:
            t = time.time()
            for i in range(3):
                fy = 1.2 + math.sin(t * 8 + i * 2) * 0.2
                fx = math.sin(t * 5 + i) * 0.15
                draw_sphere(fx, fy, 0.2, 0.12, (255, int(100 + math.sin(t * 10 + i) * 80), 20))
        glPopMatrix()
        # Health bar
        if self.hp < self.max_hp:
            self._draw_health_bar()
        draw_shadow_circle(self.x, self.y + 0.01, self.z, 0.5)


class Boss(Entity):
    """Boss enemy with phases and special attacks."""
    def __init__(self, boss_type, x, y, z):
        super().__init__(x, y, z)
        self.boss_type = boss_type
        data = BOSS_DATA[boss_type]
        self.hp = data['hp']
        self.max_hp = data['hp']
        self.damage = data['damage']
        self.speed = data['speed']
        self.xp = data['xp']
        self.color = data['color']
        self.size = data['size']
        self.num_phases = data['phases']
        self.phase = 1
        self.state = 'idle'
        self.attack_cooldown = 0.0
        self.special_timer = 0.0
        self.anim_time = 0.0
        self.spawn_x = x
        self.spawn_z = z
        self.arena_radius = 25.0
        self.defeated = False
        self.stun_timer = 0.0

    def update(self, dt, player_x, player_y, player_z, seed=42):
        if not self.alive:
            return
        self.anim_time += dt
        self.hurt_timer = max(0, self.hurt_timer - dt)
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        self.special_timer += dt

        # Phase transitions
        hp_pct = self.hp / self.max_hp
        if self.num_phases >= 2 and hp_pct < 0.5 and self.phase == 1:
            self.phase = 2
            self.speed *= 1.3
            self.damage = int(self.damage * 1.2)
        if self.num_phases >= 3 and hp_pct < 0.25 and self.phase == 2:
            self.phase = 3
            self.speed *= 1.2
            self.damage = int(self.damage * 1.3)

        if self.stun_timer > 0:
            self.stun_timer -= dt
            return

        dist = dist2d(self.x, self.z, player_x, player_z)
        if dist < self.arena_radius:
            if dist < ATTACK_RANGE * 2:
                self.state = 'attack'
                dx, dz = normalize2d(player_x - self.x, player_z - self.z)
                self.facing = math.degrees(math.atan2(-dx, -dz))
            else:
                self.state = 'chase'
                dx, dz = normalize2d(player_x - self.x, player_z - self.z)
                self.x += dx * self.speed * dt
                self.z += dz * self.speed * dt
                self.facing = math.degrees(math.atan2(-dx, -dz))
        else:
            self.state = 'idle'

        wy = walkable_y(self.x, self.z, seed)
        if wy is not None:
            self.y = wy

    def can_attack(self):
        return self.state == 'attack' and self.attack_cooldown <= 0 and self.alive

    def do_attack(self):
        self.attack_cooldown = 1.5 / self.phase
        return self.damage

    def draw(self):
        if not self.alive:
            return
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.facing, 0, 1, 0)

        color = (255, 60, 60) if self.hurt_timer > 0 else self.color
        sz = self.size
        bob = math.sin(self.anim_time * 2) * 0.2

        # Large body
        draw_cube(0, sz * 0.6 + bob, 0, sz * 0.5, sz * 0.5, sz * 0.4, color)
        # Head (sphere, larger)
        head_color = tuple(min(255, c + 20) for c in color)
        draw_sphere(0, sz * 1.3 + bob, 0, sz * 0.4, head_color)
        # Eyes (glowing)
        eye_color = (255, 50, 50) if self.phase >= 2 else (255, 200, 50)
        draw_sphere(sz * 0.15, sz * 1.35 + bob, sz * 0.35, sz * 0.08, eye_color)
        draw_sphere(-sz * 0.15, sz * 1.35 + bob, sz * 0.35, sz * 0.08, eye_color)

        # Arms
        arm_swing = math.sin(self.anim_time * 5) * 30 if self.state == 'attack' else math.sin(self.anim_time * 1.5) * 10
        for side in (1, -1):
            glPushMatrix()
            glTranslatef(side * sz * 0.6, sz * 0.6 + bob, 0)
            glRotatef(arm_swing * side, 1, 0, 0)
            draw_cube(0, -sz * 0.25, 0, sz * 0.15, sz * 0.3, sz * 0.15, color)
            glPopMatrix()

        # Legs
        leg_swing = math.sin(self.anim_time * 4) * 20 if self.state == 'chase' else 0
        for side in (1, -1):
            glPushMatrix()
            glTranslatef(side * sz * 0.2, sz * 0.05, 0)
            glRotatef(leg_swing * side, 1, 0, 0)
            draw_cube(0, -sz * 0.15, 0, sz * 0.15, sz * 0.2, sz * 0.15, tuple(max(0, c-30) for c in color))
            glPopMatrix()

        # Phase indicators (glowing orbs)
        if self.phase >= 2:
            glow_color = (255, 100, 100)
            for i in range(3):
                angle = self.anim_time * 2 + i * 2.094
                ox = math.cos(angle) * sz * 0.8
                oz = math.sin(angle) * sz * 0.8
                draw_sphere(ox, sz * 1.5 + bob, oz, 0.15, glow_color)

        glPopMatrix()

        # Boss health bar (larger, above boss)
        self._draw_boss_bar()
        draw_shadow_circle(self.x, self.y + 0.01, self.z, sz * 0.8)

    def _draw_boss_bar(self):
        bar_w = self.size * 2.0
        bar_h = 0.12
        bar_y = self.y + self.size * 2.2
        hp_pct = self.hp / self.max_hp
        glDisable(GL_LIGHTING)
        draw_cube(self.x, bar_y, self.z, bar_w * 0.5, bar_h, 0.03, (60, 0, 0))
        hw = bar_w * 0.5 * hp_pct
        phase_color = [(220, 40, 40), (220, 150, 30), (180, 40, 200)][min(self.phase - 1, 2)]
        draw_cube(self.x - bar_w * 0.5 * (1 - hp_pct), bar_y, self.z + 0.01, hw, bar_h, 0.03, phase_color)
        glEnable(GL_LIGHTING)


# ════════════════════════════════════════════════════════════
# COOKIE MONSTER NPC (giant creature made of cookies!)
# ════════════════════════════════════════════════════════════
class CookieMonsterNPC(Entity):
    """Giant Cookie Monster made entirely of cookies. Friendly shop vendor."""
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.size = 4.0  # GIANT
        self.anim_time = 0.0

    def update(self, dt, player_x, player_z):
        self.anim_time += dt
        dist = dist2d(self.x, self.z, player_x, player_z)
        if dist < INTERACT_RANGE * 3:
            dx, dz = normalize2d(player_x - self.x, player_z - self.z)
            self.facing = math.degrees(math.atan2(-dx, -dz))

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.facing, 0, 1, 0)
        sz = self.size
        t = self.anim_time
        bob = math.sin(t * 1.2) * 0.2
        cookie_c = (210, 170, 80)
        chip_c = (140, 90, 40)
        dark_c = (180, 140, 60)

        # Giant cookie body (main sphere made of cookie dough)
        draw_sphere(0, sz * 0.8 + bob, 0, sz * 0.6, cookie_c)
        # Chocolate chips all over body
        for i in range(12):
            a = i * 0.52 + t * 0.1
            cx = math.cos(a) * sz * 0.55
            cy = sz * 0.8 + bob + math.sin(a * 1.3) * sz * 0.4
            cz = math.sin(a) * sz * 0.55
            draw_sphere(cx, cy, cz, sz * 0.08, chip_c)

        # Cookie head (big round cookie)
        draw_sphere(0, sz * 1.6 + bob, 0, sz * 0.4, cookie_c)
        # Chocolate chip eyes
        draw_sphere(sz * 0.15, sz * 1.7 + bob, sz * 0.35, sz * 0.1, chip_c)
        draw_sphere(-sz * 0.15, sz * 1.7 + bob, sz * 0.35, sz * 0.1, chip_c)
        # White pupils (friendly!)
        draw_sphere(sz * 0.15, sz * 1.72 + bob, sz * 0.42, sz * 0.04, (255, 255, 255))
        draw_sphere(-sz * 0.15, sz * 1.72 + bob, sz * 0.42, sz * 0.04, (255, 255, 255))
        # Giant cookie mouth smile
        draw_sphere(0, sz * 1.45 + bob, sz * 0.35, sz * 0.12, dark_c)

        # Cookie arms (stacked cookie cylinders)
        arm_wave = math.sin(t * 1.5) * 20
        for side in (1, -1):
            glPushMatrix()
            glTranslatef(side * sz * 0.65, sz * 0.9 + bob, 0)
            glRotatef(arm_wave * side + 15, 1, 0, 0)
            draw_sphere(0, 0, 0, sz * 0.15, cookie_c)
            draw_sphere(0, -sz * 0.25, 0, sz * 0.13, cookie_c)
            draw_sphere(0, -sz * 0.45, 0, sz * 0.12, cookie_c)
            # Cookie hand
            draw_sphere(0, -sz * 0.6, 0, sz * 0.14, dark_c)
            glPopMatrix()

        # Cookie legs
        for side in (1, -1):
            draw_sphere(side * sz * 0.25, sz * 0.15, 0, sz * 0.18, dark_c)
            draw_sphere(side * sz * 0.25, -sz * 0.05, 0, sz * 0.15, cookie_c)

        # Floating cookies orbiting (shop indicator)
        for i in range(3):
            a = t * 1.5 + i * 2.094
            ox = math.cos(a) * sz * 0.9
            oz = math.sin(a) * sz * 0.9
            oy = sz * 2.2 + math.sin(t * 2 + i) * 0.3
            draw_sphere(ox, oy, oz, 0.35, cookie_c)
            draw_sphere(ox + 0.1, oy + 0.05, oz, 0.08, chip_c)

        glPopMatrix()
        draw_shadow_circle(self.x, self.y + 0.01, self.z, sz)

    def draw_name(self):
        glDisable(GL_LIGHTING)
        draw_cube(self.x, self.y + self.size * 2.6, self.z, 2.0, 0.12, 0.04, (210, 170, 80))
        glEnable(GL_LIGHTING)


# ════════════════════════════════════════════════════════════
# GRANDMA NPCs
# ════════════════════════════════════════════════════════════
class GrandmaNPC(Entity):
    """Good Grandma - use her kitchen for 3 cookies to make recipes."""
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.size = 1.2
        self.anim_time = 0.0

    def update(self, dt, player_x, player_z):
        self.anim_time += dt
        dist = dist2d(self.x, self.z, player_x, player_z)
        if dist < INTERACT_RANGE * 2:
            dx, dz = normalize2d(player_x - self.x, player_z - self.z)
            self.facing = math.degrees(math.atan2(-dx, -dz))

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.facing, 0, 1, 0)
        sz = self.size
        bob = math.sin(self.anim_time * 1.0) * 0.05
        # Grandma body (purple dress)
        draw_cube(0, sz * 0.5 + bob, 0, sz * 0.3, sz * 0.4, sz * 0.25, (140, 80, 160))
        # Head
        draw_sphere(0, sz * 1.1 + bob, 0, sz * 0.25, (230, 190, 155))
        # White hair bun
        draw_sphere(0, sz * 1.35 + bob, -sz * 0.05, sz * 0.18, (220, 220, 230))
        # Glasses (small circles)
        draw_sphere(sz * 0.1, sz * 1.15 + bob, sz * 0.22, sz * 0.06, (200, 200, 220))
        draw_sphere(-sz * 0.1, sz * 1.15 + bob, sz * 0.22, sz * 0.06, (200, 200, 220))
        # Apron
        draw_cube(0, sz * 0.5 + bob, sz * 0.2, sz * 0.22, sz * 0.3, sz * 0.05, (255, 255, 240))
        # Rolling pin in hand
        arm_wave = math.sin(self.anim_time * 0.8) * 10
        glPushMatrix()
        glTranslatef(sz * 0.35, sz * 0.5 + bob, 0)
        glRotatef(arm_wave, 1, 0, 0)
        draw_cube(0, -sz * 0.15, sz * 0.15, sz * 0.04, sz * 0.2, sz * 0.04, (180, 140, 80))
        glPopMatrix()
        glPopMatrix()
        draw_shadow_circle(self.x, self.y + 0.01, self.z, sz * 0.5)

    def draw_name(self):
        glDisable(GL_LIGHTING)
        draw_cube(self.x, self.y + self.size * 1.8, self.z, 1.0, 0.1, 0.03, (140, 80, 160))
        glEnable(GL_LIGHTING)


class EvilGrandmaNPC(Entity):
    """Evil Grandma - takes your stats and gives cookies back."""
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.size = 1.3
        self.anim_time = 0.0

    def update(self, dt, player_x, player_z):
        self.anim_time += dt
        dist = dist2d(self.x, self.z, player_x, player_z)
        if dist < INTERACT_RANGE * 2:
            dx, dz = normalize2d(player_x - self.x, player_z - self.z)
            self.facing = math.degrees(math.atan2(-dx, -dz))

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.facing, 0, 1, 0)
        sz = self.size
        t = self.anim_time
        bob = math.sin(t * 1.3) * 0.08
        # Evil grandma body (dark green/black dress)
        draw_cube(0, sz * 0.5 + bob, 0, sz * 0.3, sz * 0.4, sz * 0.25, (40, 60, 30))
        # Hunched back
        draw_sphere(0, sz * 0.9 + bob, -sz * 0.15, sz * 0.2, (40, 60, 30))
        # Head (paler skin)
        draw_sphere(0, sz * 1.1 + bob, 0, sz * 0.22, (200, 180, 160))
        # Pointy witch hat
        draw_cone(0, sz * 1.35 + bob, 0, sz * 0.25, sz * 0.5, (20, 20, 30))
        # Glowing red eyes
        draw_sphere(sz * 0.08, sz * 1.15 + bob, sz * 0.2, sz * 0.04, (255, 50, 50))
        draw_sphere(-sz * 0.08, sz * 1.15 + bob, sz * 0.2, sz * 0.04, (255, 50, 50))
        # Crooked nose
        draw_sphere(0, sz * 1.05 + bob, sz * 0.22, sz * 0.04, (180, 160, 140))
        # Gnarled walking stick
        glPushMatrix()
        glTranslatef(sz * 0.4, sz * 0.1, 0)
        draw_cylinder(0, 0, 0, sz * 0.03, sz * 1.0, (80, 60, 40))
        # Crystal on top
        draw_sphere(0, sz * 1.0, 0, sz * 0.06, (180 + int(math.sin(t * 3) * 75), 50, 200))
        glPopMatrix()
        # Evil aura particles
        if int(t * 4) % 2 == 0:
            for i in range(2):
                a = t * 2 + i * 3.14
                draw_sphere(math.cos(a) * sz * 0.5, sz * 0.3 + math.sin(t * 3 + i) * 0.3, math.sin(a) * sz * 0.5, 0.1, (100, 0, 150))
        glPopMatrix()
        draw_shadow_circle(self.x, self.y + 0.01, self.z, sz * 0.5)

    def draw_name(self):
        glDisable(GL_LIGHTING)
        draw_cube(self.x, self.y + self.size * 2.0, self.z, 1.0, 0.1, 0.03, (180, 50, 50))
        glEnable(GL_LIGHTING)


# ════════════════════════════════════════════════════════════
# SHRINE INSTANCE
# ════════════════════════════════════════════════════════════
class Shrine:
    """A shrine in the world that the player can enter."""
    def __init__(self, shrine_type, wx, wz, description):
        self.shrine_type = shrine_type
        self.wx = wx * TILE_SIZE
        self.wz = wz * TILE_SIZE
        self.description = description
        self.completed = False
        self.active = False  # Player is inside
        self.anim_time = random.random() * 10

        # Shrine interior state
        self.enemies: List[Mob] = []
        self.blocks = []  # Puzzle blocks
        self.switches = []  # Puzzle switches
        self.chests = []  # Treasure chests: {'x', 'z', 'opened', 'reward'}
        self.goal_reached = False
        self.timer = 0.0

    def get_world_y(self, seed=42):
        wy = walkable_y(self.wx, self.wz, seed)
        return wy if wy is not None else 0.0

    def _make_weak_mob(self, mob_type, x, z):
        """Create a weaker shrine mob (half HP, lower damage)."""
        mob = Mob(mob_type, x, 0, z)
        mob.hp = max(10, mob.hp // 2)
        mob.max_hp = mob.hp
        mob.damage = max(3, mob.damage // 2)
        mob.speed = min(mob.speed, 2.5)
        return mob

    def generate_interior(self):
        """Generate shrine puzzle content when entered."""
        self.enemies.clear()
        self.blocks.clear()
        self.switches.clear()
        self.chests.clear()
        self.goal_reached = False
        self.timer = 0.0

        st = self.shrine_type
        if st == ShrineType.GRASP_TRIAL:
            # Ultrahand shrine - push blocks onto switches, find chests
            # Room has scattered blocks and switches in a maze-like layout
            self.blocks.append({'x': -6, 'z': 5, 'on_switch': False})
            self.blocks.append({'x': 4, 'z': 3, 'on_switch': False})
            self.switches.append({'x': -6, 'z': -7, 'activated': False})
            self.switches.append({'x': 6, 'z': -7, 'activated': False})
            # Chest rewards
            self.chests.append({'x': 8, 'z': 8, 'opened': False, 'reward': 'cookie'})
            # One weak guard
            self.enemies.append(self._make_weak_mob(MobType.GRUNKLE, 0, -3))
            # Fat Lesse chickens wandering around
            self.enemies.append(self._make_weak_mob(MobType.LESSE, -3, 6))
            self.enemies.append(self._make_weak_mob(MobType.LESSE, 5, 0))

        elif st == ShrineType.FORGE_TRIAL:
            # Fuse shrine - has Lesses to fuse with, block+switch gate, chest
            self.blocks.append({'x': 7, 'z': 7, 'on_switch': False})
            self.switches.append({'x': 0, 'z': -8, 'activated': False})
            # Lesses to fuse (they become fire allies!)
            self.enemies.append(self._make_weak_mob(MobType.LESSE, -4, 4))
            self.enemies.append(self._make_weak_mob(MobType.LESSE, 4, 4))
            self.enemies.append(self._make_weak_mob(MobType.LESSE, 0, 6))
            # One enemy to defeat
            self.enemies.append(self._make_weak_mob(MobType.CAVE_FIEND, 3, -5))
            self.chests.append({'x': -8, 'z': -8, 'opened': False, 'reward': 'cookie'})
            self.chests.append({'x': 8, 'z': 0, 'opened': False, 'reward': 'rupee'})

        elif st == ShrineType.RISING_TRIAL:
            # Ascend shrine - platforms at different heights, jump puzzles
            # Enemies on raised platforms (but weak)
            self.enemies.append(self._make_weak_mob(MobType.SKARVYN, -5, -4))
            self.enemies.append(self._make_weak_mob(MobType.GRUNKLE, 5, -6))
            # Blocks to climb on
            self.blocks.append({'x': -3, 'z': 0, 'on_switch': False})
            self.blocks.append({'x': 3, 'z': -3, 'on_switch': False})
            self.switches.append({'x': 0, 'z': -9, 'activated': False})
            self.chests.append({'x': -9, 'z': 5, 'opened': False, 'reward': 'cookie'})
            self.chests.append({'x': 9, 'z': -5, 'opened': False, 'reward': 'rupee'})
            # Lesses for fun
            self.enemies.append(self._make_weak_mob(MobType.LESSE, 0, 7))

        elif st == ShrineType.TIMEFLOW_TRIAL:
            # Recall shrine - hit switches in correct order, timed puzzle
            self.switches.append({'x': -6, 'z': 6, 'activated': False})
            self.switches.append({'x': 6, 'z': 6, 'activated': False})
            self.switches.append({'x': 0, 'z': -6, 'activated': False})
            self.blocks.append({'x': -6, 'z': 0, 'on_switch': False})
            self.blocks.append({'x': 6, 'z': 0, 'on_switch': False})
            self.blocks.append({'x': 0, 'z': 3, 'on_switch': False})
            self.enemies.append(self._make_weak_mob(MobType.HUSK_CRAWLER, 0, 0))
            self.chests.append({'x': -9, 'z': -9, 'opened': False, 'reward': 'cookie'})
            self.enemies.append(self._make_weak_mob(MobType.LESSE, 5, 5))

        elif st == ShrineType.TRIAL_OF_MIGHT:
            # Combat arena - but balanced enemies
            for i in range(3):
                angle = i / 3 * math.pi * 2
                self.enemies.append(self._make_weak_mob(
                    random.choice([MobType.GRUNKLE, MobType.SKARVYN]),
                    math.cos(angle) * 7, math.sin(angle) * 7))
            self.chests.append({'x': 0, 'z': 8, 'opened': False, 'reward': 'cookie'})

        elif st == ShrineType.ANCIENT_GIFT:
            self.goal_reached = True  # Free reward!
            self.chests.append({'x': 3, 'z': 0, 'opened': False, 'reward': 'cookie'})
            self.chests.append({'x': -3, 'z': 0, 'opened': False, 'reward': 'rupee'})

        elif st == ShrineType.WIND_TRIAL:
            # Wind - dodge and push blocks in windy room
            self.enemies.append(self._make_weak_mob(MobType.HUSK_CRAWLER, -5, 0))
            self.enemies.append(self._make_weak_mob(MobType.HUSK_CRAWLER, 5, 0))
            self.blocks.append({'x': 0, 'z': 5, 'on_switch': False})
            self.switches.append({'x': 0, 'z': -8, 'activated': False})
            self.chests.append({'x': 8, 'z': 8, 'opened': False, 'reward': 'rupee'})

        elif st == ShrineType.FIRE_TRIAL:
            # Fire - Lesses that can be fused, dodge fire
            self.enemies.append(self._make_weak_mob(MobType.GRUNKLE, -4, -3))
            self.enemies.append(self._make_weak_mob(MobType.LESSE, 3, 5))
            self.enemies.append(self._make_weak_mob(MobType.LESSE, -3, 5))
            self.blocks.append({'x': 5, 'z': 5, 'on_switch': False})
            self.switches.append({'x': -5, 'z': -8, 'activated': False})
            self.chests.append({'x': -9, 'z': 9, 'opened': False, 'reward': 'cookie'})

        elif st == ShrineType.ICE_TRIAL:
            # Ice - slippery blocks, weaker enemies
            self.enemies.append(self._make_weak_mob(MobType.GULPWORM, 0, 3))
            self.blocks.append({'x': -5, 'z': 4, 'on_switch': False})
            self.blocks.append({'x': 5, 'z': 4, 'on_switch': False})
            self.switches.append({'x': -5, 'z': -8, 'activated': False})
            self.switches.append({'x': 5, 'z': -8, 'activated': False})
            self.chests.append({'x': 9, 'z': 9, 'opened': False, 'reward': 'rupee'})

        elif st == ShrineType.LIGHTNING_TRIAL:
            # Lightning - quick weak enemies
            for i in range(3):
                angle = i / 3 * math.pi * 2
                self.enemies.append(self._make_weak_mob(
                    MobType.GRUNKLE, math.cos(angle) * 6, math.sin(angle) * 6))
            self.chests.append({'x': 0, 'z': 9, 'opened': False, 'reward': 'cookie'})

        elif st == ShrineType.SHADOW_TRIAL:
            # Shadow - one strong-ish enemy, dark atmosphere
            self.enemies.append(self._make_weak_mob(MobType.THUGNOK, 0, -4))
            self.chests.append({'x': -8, 'z': 8, 'opened': False, 'reward': 'cookie'})
            self.chests.append({'x': 8, 'z': 8, 'opened': False, 'reward': 'rupee'})

        elif st == ShrineType.WATER_TRIAL:
            # Water - push blocks across water to switches
            self.blocks.append({'x': -4, 'z': 5, 'on_switch': False})
            self.blocks.append({'x': 4, 'z': 5, 'on_switch': False})
            self.switches.append({'x': -3, 'z': -8, 'activated': False})
            self.switches.append({'x': 3, 'z': -8, 'activated': False})
            self.enemies.append(self._make_weak_mob(MobType.GULPWORM, 0, 0))
            self.chests.append({'x': 0, 'z': 9, 'opened': False, 'reward': 'cookie'})

        else:
            # Fallback - simple combat
            for i in range(2):
                angle = i / 2 * math.pi * 2
                self.enemies.append(self._make_weak_mob(
                    MobType.GRUNKLE, math.cos(angle) * 5, math.sin(angle) * 5))
            self.chests.append({'x': 0, 'z': 8, 'opened': False, 'reward': 'cookie'})

    def check_completion(self):
        if self.completed:
            return True
        if self.shrine_type == ShrineType.ANCIENT_GIFT:
            return True
        # Check non-Lesse enemies dead (Lesses are allies)
        combat_enemies = [e for e in self.enemies if e.mob_type != MobType.LESSE]
        enemies_dead = len(combat_enemies) == 0 or all(not e.alive for e in combat_enemies)
        # Pure block puzzles (GRASP, WATER, ICE) - blocks on switches
        if self.switches:
            for sw in self.switches:
                sw['activated'] = False
                for bl in self.blocks:
                    if dist2d(bl['x'], bl['z'], sw['x'], sw['z']) < 1.5:
                        sw['activated'] = True
                        break
            switches_done = all(sw['activated'] for sw in self.switches)
            return enemies_dead and switches_done
        # Pure combat shrines
        return enemies_dead

    def draw_exterior(self, seed=42):
        """Draw shrine marker in the overworld."""
        if self.completed:
            color = (100, 200, 100)  # Green = done
        else:
            color = (100, 180, 240)  # Blue = active
        y = self.get_world_y(seed)
        self.anim_time += 0.016

        # Stone base
        draw_cube(self.wx, y + 0.5, self.wz, 1.5, 0.5, 1.5, (120, 110, 100))
        # Pillars
        for dx, dz in [(-1.2, -1.2), (1.2, -1.2), (-1.2, 1.2), (1.2, 1.2)]:
            draw_cube(self.wx + dx, y + 1.5, self.wz + dz, 0.2, 1.0, 0.2, (140, 130, 120))
        # Glowing orb on top
        glow = 0.5 + 0.5 * math.sin(self.anim_time * 3)
        orb_color = tuple(int(c * (0.7 + glow * 0.3)) for c in color)
        draw_sphere(self.wx, y + 3.0 + math.sin(self.anim_time * 2) * 0.2, self.wz, 0.4, orb_color)
        # Symbol
        if not self.completed:
            draw_cone(self.wx, y + 2.2, self.wz, 0.3, 0.6, color)

    def _get_theme_colors(self):
        """Return floor/wall/accent colors based on shrine type."""
        st = self.shrine_type
        if st == ShrineType.FIRE_TRIAL:
            return (0.4, 0.15, 0.1), (0.35, 0.12, 0.08), (140, 50, 30), (255, 120, 30)
        elif st == ShrineType.ICE_TRIAL:
            return (0.3, 0.38, 0.45), (0.25, 0.33, 0.42), (120, 150, 180), (150, 220, 255)
        elif st == ShrineType.LIGHTNING_TRIAL:
            return (0.35, 0.35, 0.2), (0.3, 0.3, 0.18), (130, 130, 70), (255, 255, 80)
        elif st == ShrineType.SHADOW_TRIAL:
            return (0.12, 0.1, 0.15), (0.1, 0.08, 0.12), (40, 30, 50), (160, 80, 200)
        elif st == ShrineType.WATER_TRIAL:
            return (0.15, 0.25, 0.4), (0.12, 0.22, 0.35), (60, 100, 150), (80, 180, 255)
        elif st == ShrineType.WIND_TRIAL:
            return (0.3, 0.4, 0.3), (0.25, 0.35, 0.25), (100, 140, 100), (180, 255, 180)
        elif st == ShrineType.ANCIENT_GIFT:
            return (0.4, 0.35, 0.2), (0.35, 0.3, 0.18), (160, 140, 80), (255, 220, 100)
        else:
            return (0.3, 0.35, 0.4), (0.28, 0.32, 0.38), (80, 90, 100), (255, 220, 50)

    def draw_interior(self):
        """Draw shrine interior (when player is inside)."""
        floor1, floor2, wall_color, accent = self._get_theme_colors()

        # Floor
        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        for x in range(-12, 13, 2):
            for z in range(-12, 13, 2):
                checker = ((x + z) // 2) % 2
                c = floor1 if checker else floor2
                glColor3f(*c)
                glVertex3f(x - 1, 0, z - 1)
                glVertex3f(x + 1, 0, z - 1)
                glVertex3f(x + 1, 0, z + 1)
                glVertex3f(x - 1, 0, z + 1)
        glEnd()

        # Walls
        for x in range(-12, 13, 2):
            draw_cube(x, 2, -12, 1, 2, 0.3, wall_color)
            draw_cube(x, 2, 12, 1, 2, 0.3, wall_color)
            draw_cube(-12, 2, x, 0.3, 2, 1, wall_color)
            draw_cube(12, 2, x, 0.3, 2, 1, wall_color)

        # Shrine-specific decorations
        st = self.shrine_type
        t = time.time()
        if st == ShrineType.FIRE_TRIAL:
            for i in range(6):
                fx = math.sin(t * 2 + i) * 8
                fz = math.cos(t * 1.5 + i * 1.1) * 8
                draw_sphere(fx, 0.5 + math.sin(t * 3 + i) * 0.3, fz, 0.3, (255, 100 + int(math.sin(t + i) * 50), 20))
        elif st == ShrineType.ICE_TRIAL:
            for i in range(4):
                ix = (i - 1.5) * 5
                draw_cube(ix, 1.5, 8, 0.8, 1.5, 0.8, (180, 210, 240))
        elif st == ShrineType.LIGHTNING_TRIAL:
            for i in range(3):
                lx = (i - 1) * 6
                draw_cylinder(lx, 0, -6, 0.15, 4, (200, 200, 60))
                if int(t * 5) % 3 == i:
                    draw_sphere(lx, 4, -6, 0.5, (255, 255, 100))
        elif st == ShrineType.SHADOW_TRIAL:
            for i in range(8):
                sx = math.sin(i * 0.8 + t * 0.5) * 9
                sz = math.cos(i * 0.8 + t * 0.5) * 9
                draw_sphere(sx, 1, sz, 0.4, (60, 20, 80))
        elif st == ShrineType.WATER_TRIAL:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glColor4f(0.1, 0.3, 0.6, 0.4)
            glBegin(GL_QUADS)
            glNormal3f(0, 1, 0)
            glVertex3f(-12, 0.15, -4)
            glVertex3f(12, 0.15, -4)
            glVertex3f(12, 0.15, 4)
            glVertex3f(-12, 0.15, 4)
            glEnd()
            glDisable(GL_BLEND)
        elif st == ShrineType.WIND_TRIAL:
            for i in range(5):
                wy = 1 + math.sin(t * 4 + i * 1.3) * 0.5
                wx = math.sin(t * 2 + i * 1.5) * 10
                wz = math.cos(t * 2 + i * 1.5) * 10
                draw_sphere(wx, wy, wz, 0.2, (200, 255, 200))
        elif st == ShrineType.ANCIENT_GIFT:
            draw_sphere(0, 2 + math.sin(t * 2) * 0.5, 0, 1.0, (255, 220, 80))
            for i in range(4):
                angle = t + i * math.pi / 2
                draw_sphere(math.cos(angle) * 3, 1.5, math.sin(angle) * 3, 0.3, (255, 200, 50))

        # Goal marker (cookie!)
        if self.check_completion() and not self.completed:
            bob = math.sin(t * 3) * 0.3
            draw_sphere(0, 1.5 + bob, -9, 0.5, (210, 170, 80))  # Cookie color
            draw_sphere(0.15, 1.6 + bob, -8.8, 0.08, (120, 80, 30))  # Choc chips
            draw_sphere(-0.1, 1.4 + bob, -8.85, 0.07, (120, 80, 30))
            draw_sphere(0.05, 1.35 + bob, -8.82, 0.06, (120, 80, 30))
        elif not self.completed:
            draw_sphere(0, 1.5, -9, 0.5, accent)
            draw_cone(0, 0, -9, 0.8, 0.3, accent)

        # Blocks
        for bl in self.blocks:
            draw_cube(bl['x'], 0.5, bl['z'], 0.5, 0.5, 0.5, (160, 140, 100))

        # Switches
        for sw in self.switches:
            c = (100, 255, 100) if sw.get('activated') else (255, 100, 100)
            draw_cube(sw['x'], 0.05, sw['z'], 0.7, 0.05, 0.7, c)

        # Chests
        for ch in self.chests:
            if ch['opened']:
                # Open chest
                draw_cube(ch['x'], 0.25, ch['z'], 0.4, 0.25, 0.3, (120, 80, 30))
                # Open lid (tilted back)
                draw_cube(ch['x'], 0.6, ch['z'] - 0.25, 0.4, 0.05, 0.3, (140, 90, 35))
            else:
                # Closed chest (glowing)
                glow_c = 0.5 + 0.5 * math.sin(t * 3)
                draw_cube(ch['x'], 0.25, ch['z'], 0.4, 0.25, 0.3, (140, 90, 35))
                draw_cube(ch['x'], 0.5, ch['z'], 0.42, 0.05, 0.32, (160, 110, 40))
                # Gold trim glow
                draw_cube(ch['x'], 0.3, ch['z'] + 0.31, 0.1, 0.1, 0.02,
                         (int(200 + glow_c * 55), int(180 + glow_c * 55), 50))

        # Enemies (Lesses draw as fat chickens)
        for e in self.enemies:
            if e.mob_type == MobType.LESSE:
                self._draw_lesse(e)
            else:
                e.draw()

    def _draw_lesse(self, lesse):
        """Draw a Lesse - extremely fat chicken creature."""
        if not lesse.alive:
            return
        glPushMatrix()
        glTranslatef(lesse.x, lesse.y, lesse.z)
        glRotatef(lesse.facing, 0, 1, 0)
        color = (255, 80, 80) if lesse.hurt_timer > 0 else lesse.color
        fused = getattr(lesse, 'fused', False)
        if fused:
            color = (255, 120, 50)  # Orange-red when fused
        # Fat round body (very wide)
        draw_sphere(0, 0.5, 0, 0.6, color)
        draw_sphere(0, 0.4, 0, 0.55, tuple(max(0, c - 20) for c in color))
        # Small head on top
        head_c = (255, 240, 200) if not fused else (255, 180, 100)
        draw_sphere(0, 1.0, 0.15, 0.22, head_c)
        # Beak
        draw_cube(0, 0.95, 0.38, 0.06, 0.04, 0.1, (255, 180, 50))
        # Eyes
        draw_sphere(-0.08, 1.05, 0.3, 0.04, (0, 0, 0))
        draw_sphere(0.08, 1.05, 0.3, 0.04, (0, 0, 0))
        # Tiny wings (flap)
        wing_angle = math.sin(lesse.anim_time * 5) * 15
        glPushMatrix()
        glTranslatef(0.5, 0.5, 0)
        glRotatef(wing_angle, 0, 0, 1)
        draw_cube(0.15, 0, 0, 0.2, 0.08, 0.15, tuple(max(0, c - 30) for c in color))
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-0.5, 0.5, 0)
        glRotatef(-wing_angle, 0, 0, 1)
        draw_cube(-0.15, 0, 0, 0.2, 0.08, 0.15, tuple(max(0, c - 30) for c in color))
        glPopMatrix()
        # Tiny legs
        draw_cube(0.15, 0.05, 0, 0.05, 0.1, 0.05, (200, 160, 50))
        draw_cube(-0.15, 0.05, 0, 0.05, 0.1, 0.05, (200, 160, 50))
        # Tail feathers
        draw_cube(0, 0.5, -0.45, 0.1, 0.15, 0.1, tuple(max(0, c - 40) for c in color))
        # Fire effect when fused
        if fused:
            t = time.time()
            for i in range(3):
                fy = 1.2 + math.sin(t * 8 + i * 2) * 0.2
                fx = math.sin(t * 5 + i) * 0.15
                draw_sphere(fx, fy, 0.2, 0.12, (255, int(100 + math.sin(t * 10 + i) * 80), 20))
        glPopMatrix()
        # Health bar
        if lesse.hp < lesse.max_hp:
            lesse._draw_health_bar()
        draw_shadow_circle(lesse.x, lesse.y + 0.01, lesse.z, 0.5)


# ════════════════════════════════════════════════════════════
# ARROW PROJECTILE
# ════════════════════════════════════════════════════════════
class Arrow:
    def __init__(self, x, y, z, dx, dy, dz, damage=12):
        self.x, self.y, self.z = x, y, z
        speed = 25.0
        self.vx, self.vy, self.vz = dx * speed, dy * speed, dz * speed
        self.damage = damage
        self.life = 2.0
        self.alive = True

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt
        self.vy += GRAVITY * 0.3 * dt
        self.life -= dt
        if self.life <= 0 or self.y < -1:
            self.alive = False

    def draw(self):
        if not self.alive:
            return
        glDisable(GL_LIGHTING)
        glColor3f(0.7, 0.5, 0.2)
        glBegin(GL_LINES)
        # Arrow shaft
        speed = math.sqrt(self.vx**2 + self.vy**2 + self.vz**2)
        if speed > 0.1:
            nx, ny, nz = self.vx/speed, self.vy/speed, self.vz/speed
        else:
            nx, ny, nz = 0, 0, -1
        glVertex3f(self.x, self.y, self.z)
        glVertex3f(self.x - nx * 0.8, self.y - ny * 0.8, self.z - nz * 0.8)
        glEnd()
        # Arrow tip
        glColor3f(0.8, 0.8, 0.85)
        glBegin(GL_TRIANGLES)
        glVertex3f(self.x + nx * 0.15, self.y + ny * 0.15, self.z + nz * 0.15)
        glVertex3f(self.x - 0.05, self.y - 0.05, self.z)
        glVertex3f(self.x + 0.05, self.y + 0.05, self.z)
        glEnd()
        glEnable(GL_LIGHTING)

# ════════════════════════════════════════════════════════════
# PLAYER CLASS
# ════════════════════════════════════════════════════════════
class Player(Entity):
    """The hero with blocky body and sphere head."""
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.hp = 60  # 3 hearts * 20
        self.max_hp = 60
        self.stamina = 100.0
        self.max_stamina = 100.0
        self.xp = 0
        self.level = 1
        self.crown_shards = 0
        self.cookies = 0  # Shrine rewards
        self.rupees = 0   # Currency for house/anvil
        # Stats: each level costs more cookies. Lvl1=1 cookie, Lvl2=2, Lvl3(max)=3
        self.stat_levels = {'attack': 0, 'defense': 0, 'speed': 0, 'stamina': 0}
        self.max_stat_level = 3
        # House
        self.has_house = False
        self.house_items = []  # list of item names placed in house
        self.has_anvil = False
        self.has_tablet = False  # Purah Pad - obtained on descent from Sky Island

        # Loadouts
        self.loadout1 = Loadout(WeaponType.SWORD, WeaponType.SHIELD)
        self.loadout2 = Loadout(WeaponType.BOW, WeaponType.SHIELD)
        self.current_loadout = 1  # 1 or 2
        self.available_weapons = [WeaponType.SWORD, WeaponType.SHIELD, WeaponType.BOW]

        # Combat
        self.left_cooldown = 0.0
        self.right_cooldown = 0.0
        self.blocking = False
        self.attack_anim = 0.0  # 0 = idle, > 0 = attacking
        self.block_anim = 0.0

        # Movement
        self.speed = WALK_SPEED
        self.sprinting = False
        self.crouching = False
        self.walk_anim = 0.0
        self.jump_count = 0

        # Abilities
        self.abilities = [AbilityType.ULTRAHAND]
        self.selected_ability = 0

        # Inventory
        self.inventory = {
            'materials': {},
            'food': {},
            'special': {},
        }
        self.arrows = 30

        # Arrows in flight
        self.projectiles: List[Arrow] = []

        # Status
        self.invincible_timer = 3.0  # Spawn protection

    @property
    def loadout(self):
        return self.loadout1 if self.current_loadout == 1 else self.loadout2

    @property
    def left_weapon(self):
        return WEAPON_DATA[self.loadout.left]

    @property
    def right_weapon(self):
        return WEAPON_DATA[self.loadout.right]

    def switch_loadout(self):
        self.current_loadout = 2 if self.current_loadout == 1 else 1
        play_sfx('loadout')

    def use_left_hand(self, mobs, bosses, particles, in_shrine=False, shrine=None):
        """Left click action."""
        if self.left_cooldown > 0:
            return
        weapon = self.loadout.left
        data = WEAPON_DATA[weapon]
        self.left_cooldown = data['cooldown']
        self.attack_anim = 0.4

        if data['type'] == 'melee':
            play_sfx('sword')
            self._melee_attack(data, mobs, bosses, particles, in_shrine, shrine)
        elif data['type'] == 'ranged':
            self._ranged_attack(data)
        elif data['type'] == 'magic':
            play_sfx('bow')
            self._magic_attack(data, mobs, bosses, particles, in_shrine, shrine)
        elif data['type'] == 'explosive':
            play_sfx('hit')
            self._explosive_attack(data, mobs, bosses, particles, in_shrine, shrine)

    def use_right_hand(self, mobs, bosses, particles, in_shrine=False, shrine=None):
        """Right click action."""
        if self.right_cooldown > 0:
            return
        weapon = self.loadout.right
        data = WEAPON_DATA[weapon]
        self.right_cooldown = data['cooldown']

        if data['type'] == 'defense':
            play_sfx('shield')
            self.blocking = True
            self.block_anim = 0.3
        elif data['type'] == 'melee':
            play_sfx('sword')
            self.attack_anim = 0.4
            self._melee_attack(data, mobs, bosses, particles, in_shrine, shrine)
        elif data['type'] == 'ranged':
            self._ranged_attack(data)
        elif data['type'] == 'magic':
            play_sfx('bow')
            self._magic_attack(data, mobs, bosses, particles, in_shrine, shrine)

    def _melee_attack(self, data, mobs, bosses, particles, in_shrine, shrine):
        rad = math.radians(self.facing)
        ax = self.x - math.sin(rad) * 1.5
        az = self.z - math.cos(rad) * 1.5

        targets = []
        if in_shrine and shrine:
            targets = shrine.enemies
        else:
            targets = mobs + bosses

        for e in targets:
            if not e.alive:
                continue
            if dist2d(ax, az, e.x, e.z) < data['range']:
                dmg = data['damage'] + self.stat_levels['attack'] * 5
                e.take_damage(dmg)
                particles.emit_hit(e.x, e.y + e.size * 0.5, e.z)
                play_sfx('hit')
                if not e.alive:
                    self.xp += e.xp
                    self.rupees += random.randint(1, 5)
                    particles.emit_death(e.x, e.y, e.z, e.color)

    def _ranged_attack(self, data):
        if self.arrows <= 0:
            return
        self.arrows -= 1
        play_sfx('bow')
        rad = math.radians(self.facing)
        dx = -math.sin(rad)
        dz = -math.cos(rad)
        arrow = Arrow(self.x, self.y + 1.2, self.z, dx, 0.1, dz, data['damage'] + self.stat_levels['attack'] * 5)
        self.projectiles.append(arrow)

    def _magic_attack(self, data, mobs, bosses, particles, in_shrine, shrine):
        rad = math.radians(self.facing)
        targets = shrine.enemies if (in_shrine and shrine) else mobs + bosses
        for e in targets:
            if not e.alive:
                continue
            if dist2d(self.x, self.z, e.x, e.z) < data['range']:
                angle_to = math.degrees(math.atan2(-(e.x - self.x), -(e.z - self.z)))
                if abs(angle_diff(self.facing, angle_to)) < 45:
                    dmg = data['damage'] + self.stat_levels['attack'] * 5
                    e.take_damage(dmg)
                    particles.emit_hit(e.x, e.y + e.size * 0.5, e.z)
                    if not e.alive:
                        self.xp += e.xp
                        self.rupees += random.randint(1, 5)
                        particles.emit_death(e.x, e.y, e.z, e.color)

    def _explosive_attack(self, data, mobs, bosses, particles, in_shrine, shrine):
        rad = math.radians(self.facing)
        bx = self.x - math.sin(rad) * 4
        bz = self.z - math.cos(rad) * 4
        targets = shrine.enemies if (in_shrine and shrine) else mobs + bosses
        particles.emit(bx, self.y + 0.5, bz, 15, (255, 150, 50), spread=2, speed=5, life=0.8, size=0.15)
        for e in targets:
            if not e.alive:
                continue
            if dist2d(bx, bz, e.x, e.z) < data['range']:
                e.take_damage(data['damage'])
                if not e.alive:
                    self.xp += e.xp
                    self.rupees += random.randint(1, 5)
                    particles.emit_death(e.x, e.y, e.z, e.color)

    def take_damage(self, amount):
        if self.invincible_timer > 0:
            return
        if self.blocking:
            defense_reduction = 4 + self.stat_levels['defense'] * 2
            amount = max(1, amount // defense_reduction)  # Shield blocks most damage
            play_sfx('shield')
        super().take_damage(amount)
        self.invincible_timer = 0.5
        if self.alive:
            play_sfx('hurt')

    def update(self, dt, seed=42):
        self.left_cooldown = max(0, self.left_cooldown - dt)
        self.right_cooldown = max(0, self.right_cooldown - dt)
        self.attack_anim = max(0, self.attack_anim - dt)
        self.block_anim = max(0, self.block_anim - dt)
        self.invincible_timer = max(0, self.invincible_timer - dt)
        self.hurt_timer = max(0, self.hurt_timer - dt)

        if self.block_anim <= 0:
            self.blocking = False

        # Stamina regen
        if not self.sprinting:
            self.stamina = min(self.max_stamina, self.stamina + 15 * dt)

        # Gravity / vertical movement
        self.vy += GRAVITY * dt
        self.y += self.vy * dt

        wy = walkable_y(self.x, self.z, seed)
        if wy is None:
            wy = 0
        if self.y <= wy:
            self.y = wy
            self.vy = 0
            self.on_ground = True
            self.jump_count = 0
        else:
            self.on_ground = False

        # Horizontal movement  (speed stat bonus)
        speed_mult = 1.0 + self.stat_levels['speed'] * 0.15
        self.x += self.vx * dt * speed_mult
        self.z += self.vz * dt * speed_mult
        self.vx *= 0.85
        self.vz *= 0.85

        # Walking animation
        if abs(self.vx) > 0.1 or abs(self.vz) > 0.1:
            self.walk_anim += dt * (12 if self.sprinting else 8)
        else:
            self.walk_anim *= 0.9

        # Projectile updates
        alive_proj = []
        for arrow in self.projectiles:
            arrow.update(dt)
            if arrow.alive:
                alive_proj.append(arrow)
        self.projectiles = alive_proj

        # Level up check
        xp_needed = self.level * 100
        if self.xp >= xp_needed:
            self.xp -= xp_needed
            self.level += 1
            self.max_hp += 20
            self.hp = self.max_hp

    def jump(self):
        if self.on_ground or self.jump_count < 2:
            self.vy = JUMP_VEL
            self.on_ground = False
            self.jump_count += 1
            play_sfx('jump')
            if self.stamina >= 5:
                self.stamina -= 5

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.facing + 180, 0, 1, 0)

        # Invincibility flash
        if self.invincible_timer > 0 and int(self.invincible_timer * 10) % 2 == 0:
            glPopMatrix()
            return

        walk_swing = math.sin(self.walk_anim) * 25
        attack_swing = 0
        if self.attack_anim > 0:
            attack_swing = math.sin(self.attack_anim / 0.4 * math.pi) * 80

        # Crouch offset
        crouch_y = -0.3 if self.crouching else 0.0

        # === LEGS ===
        leg_color = C_PANTS_WHITE
        leg_h = 0.15 if self.crouching else 0.2
        for side, swing_dir in [(0.15, 1), (-0.15, -1)]:
            glPushMatrix()
            glTranslatef(side, 0.35 + crouch_y, 0)
            glRotatef(walk_swing * swing_dir, 1, 0, 0)
            draw_cube(0, -0.15, 0, 0.1, leg_h, 0.1, leg_color)
            # Boots
            draw_cube(0, -0.35 + (0.05 if self.crouching else 0), 0.02, 0.11, 0.05, 0.14, C_BOOTS_BROWN)
            glPopMatrix()

        # === TORSO ===
        tunic = C_TUNIC_GREEN if self.hurt_timer <= 0 else (255, 100, 100)
        draw_cube(0, 0.75 + crouch_y, 0, 0.25, 0.25, 0.15, tunic)
        # Belt
        draw_cube(0, 0.52 + crouch_y, 0, 0.26, 0.03, 0.16, C_BOOTS_BROWN)
        # Chest detail
        draw_cube(0, 0.80 + crouch_y, 0.14, 0.15, 0.10, 0.02, (180, 150, 60))

        # === LEFT ARM (weapon hand) ===
        glPushMatrix()
        glTranslatef(-0.38, 0.75 + crouch_y, 0)
        glRotatef(-walk_swing * 0.5 + attack_swing, 1, 0, 0)
        draw_cube(0, -0.15, 0, 0.08, 0.2, 0.08, C_SKIN)
        # Draw left weapon
        self._draw_weapon_in_hand(self.loadout.left, -0.38, 0.75 - 0.35 + crouch_y, 0, attack_swing > 20)
        glPopMatrix()

        # === RIGHT ARM (other hand) ===
        block_raise = 0
        if self.blocking:
            block_raise = 60
        glPushMatrix()
        glTranslatef(0.38, 0.75 + crouch_y, 0)
        glRotatef(walk_swing * 0.5 + block_raise, 1, 0, 0)
        draw_cube(0, -0.15, 0, 0.08, 0.2, 0.08, C_SKIN)
        # Draw right weapon
        self._draw_weapon_in_hand(self.loadout.right, 0.38, 0.75 - 0.35 + crouch_y, 0, self.blocking)
        glPopMatrix()

        # === HEAD (SPHERE) ===
        head_y = 1.2 + crouch_y
        draw_sphere(0, head_y, 0, 0.22, C_SKIN, 16, 12)
        # Hair
        draw_sphere(0, head_y + 0.12, -0.05, 0.2, C_HAIR_BLOND, 12, 8)
        # Eye whites (behind pupils)
        draw_sphere(0.08, head_y + 0.02, 0.17, 0.05, (240, 240, 240))
        draw_sphere(-0.08, head_y + 0.02, 0.17, 0.05, (240, 240, 240))
        # Pupils (in front of whites)
        draw_sphere(0.08, head_y + 0.02, 0.20, 0.03, (30, 50, 110))
        draw_sphere(-0.08, head_y + 0.02, 0.20, 0.03, (30, 50, 110))
        # Mouth
        draw_cube(0, head_y - 0.08, 0.19, 0.06, 0.015, 0.01, (180, 100, 90))

        glPopMatrix()

        # Shadow
        draw_shadow_circle(self.x, self.y + 0.01, self.z, 0.4)

        # Draw projectiles
        for arrow in self.projectiles:
            arrow.draw()

    def _draw_weapon_in_hand(self, weapon_type, hx, hy, hz, active):
        """Draw weapon model relative to hand position."""
        if weapon_type == WeaponType.SWORD:
            # Blade
            blade_len = 0.8
            glPushMatrix()
            if active:
                glRotatef(-30, 0, 0, 1)
            draw_cube(0, -0.3, -0.3, 0.04, blade_len * 0.5, 0.04, C_SWORD_SILVER)
            # Glow
            draw_cube(0, -0.3, -0.3, 0.05, blade_len * 0.5 + 0.02, 0.01, C_SWORD_GLOW)
            # Handle
            draw_cube(0, 0.1, -0.3, 0.05, 0.08, 0.05, C_BOOTS_BROWN)
            # Crossguard
            draw_cube(0, 0.0, -0.3, 0.12, 0.02, 0.02, C_SHIELD_GOLD)
            glPopMatrix()
        elif weapon_type == WeaponType.SHIELD:
            # Shield
            glPushMatrix()
            if active:
                glTranslatef(0, 0, 0.3)
            draw_cube(0, 0, 0.15, 0.02, 0.3, 0.25, C_SHIELD_BLUE)
            # Shield emblem
            draw_cube(0, 0.02, 0.17, 0.03, 0.08, 0.08, C_SHIELD_GOLD)
            # Shield border
            draw_cube(0, 0, 0.15, 0.01, 0.32, 0.27, C_SHIELD_GOLD)
            glPopMatrix()
        elif weapon_type == WeaponType.BOW:
            draw_cube(0, -0.05, -0.2, 0.03, 0.35, 0.03, C_BOW_BROWN)
            # Bowstring
            glDisable(GL_LIGHTING)
            glColor3f(0.9, 0.9, 0.9)
            glBegin(GL_LINES)
            glVertex3f(0, 0.3, -0.2)
            glVertex3f(0, -0.1, -0.1)
            glVertex3f(0, -0.1, -0.1)
            glVertex3f(0, -0.4, -0.2)
            glEnd()
            glEnable(GL_LIGHTING)
        elif weapon_type == WeaponType.SPEAR:
            draw_cube(0, -0.2, -0.3, 0.03, 0.6, 0.03, (140, 100, 60))
            draw_cone(0, -0.85, -0.3, 0.06, 0.2, (180, 180, 200))
        elif weapon_type == WeaponType.FIRE_ROD:
            draw_cube(0, -0.1, -0.3, 0.04, 0.4, 0.04, (100, 40, 20))
            draw_sphere(0, -0.55, -0.3, 0.1, (255, 120, 30))
        elif weapon_type == WeaponType.BOMBS:
            draw_sphere(0, -0.1, -0.2, 0.15, (100, 100, 120))
            draw_cylinder(0, -0.1, -0.2, 0.02, 0.15, (140, 80, 30))

    def get_save_data(self):
        return {
            'x': self.x, 'y': self.y, 'z': self.z,
            'hp': self.hp, 'max_hp': self.max_hp,
            'stamina': self.stamina, 'max_stamina': self.max_stamina,
            'xp': self.xp, 'level': self.level,
            'crown_shards': self.crown_shards,
            'arrows': self.arrows,
            'loadout1_left': self.loadout1.left.name,
            'loadout1_right': self.loadout1.right.name,
            'loadout2_left': self.loadout2.left.name,
            'loadout2_right': self.loadout2.right.name,
            'available_weapons': [w.name for w in self.available_weapons],
            'abilities': [a.name for a in self.abilities],
            'cookies': self.cookies,
            'rupees': self.rupees,
            'stat_levels': self.stat_levels,
            'has_house': self.has_house,
            'house_items': self.house_items,
            'has_anvil': self.has_anvil,
        }

    def load_save_data(self, data):
        self.x = data.get('x', self.x)
        self.y = data.get('y', self.y)
        self.z = data.get('z', self.z)
        self.hp = data.get('hp', self.hp)
        self.max_hp = data.get('max_hp', self.max_hp)
        self.stamina = data.get('stamina', self.stamina)
        self.max_stamina = data.get('max_stamina', self.max_stamina)
        self.xp = data.get('xp', self.xp)
        self.level = data.get('level', self.level)
        self.crown_shards = data.get('crown_shards', self.crown_shards)
        self.arrows = data.get('arrows', self.arrows)
        try:
            self.loadout1.left = WeaponType[data.get('loadout1_left', 'SWORD')]
            self.loadout1.right = WeaponType[data.get('loadout1_right', 'SHIELD')]
            self.loadout2.left = WeaponType[data.get('loadout2_left', 'BOW')]
            self.loadout2.right = WeaponType[data.get('loadout2_right', 'SHIELD')]
        except (KeyError, ValueError):
            pass
        try:
            self.available_weapons = [WeaponType[w] for w in data.get('available_weapons', [])]
        except (KeyError, ValueError):
            pass
        try:
            self.abilities = [AbilityType[a] for a in data.get('abilities', [])]
        except (KeyError, ValueError):
            pass
        self.cookies = data.get('cookies', 0)
        self.rupees = data.get('rupees', 0)
        sl = data.get('stat_levels', {})
        for k in ('attack', 'defense', 'speed', 'stamina'):
            if k in sl:
                self.stat_levels[k] = sl[k]
        self.has_house = data.get('has_house', False)
        self.house_items = data.get('house_items', [])
        self.has_anvil = data.get('has_anvil', False)

# ════════════════════════════════════════════════════════════
# CAMERA
# ════════════════════════════════════════════════════════════
class Camera:
    def __init__(self):
        self.yaw = 0.0      # horizontal rotation (degrees)
        self.pitch = CAM_PITCH_DEFAULT  # vertical angle (negative = looking down)
        self.dist = CAM_DIST_DEFAULT
        self.looking = True  # Always free mouse look
        self.target_x = 0.0
        self.target_y = 0.0
        self.target_z = 0.0

    def get_position(self, player):
        """Calculate camera position looking at player."""
        self.target_x = player.x
        self.target_y = player.y + 1.0
        self.target_z = player.z

        yaw_rad = math.radians(self.yaw)
        pitch_rad = math.radians(self.pitch)

        cam_x = self.target_x + math.sin(yaw_rad) * math.cos(pitch_rad) * self.dist
        cam_y = self.target_y - math.sin(pitch_rad) * self.dist
        cam_z = self.target_z + math.cos(yaw_rad) * math.cos(pitch_rad) * self.dist

        return cam_x, cam_y, cam_z

    def apply(self, player):
        """Set up the OpenGL view matrix."""
        cx, cy, cz = self.get_position(player)
        gluLookAt(cx, cy, cz,
                  self.target_x, self.target_y, self.target_z,
                  0, 1, 0)

    def get_forward(self):
        """Get the forward direction vector (on XZ plane)."""
        yaw_rad = math.radians(self.yaw)
        return -math.sin(yaw_rad), -math.cos(yaw_rad)

    def get_right(self):
        """Get the right direction vector."""
        yaw_rad = math.radians(self.yaw)
        return math.cos(yaw_rad), -math.sin(yaw_rad)

# ════════════════════════════════════════════════════════════
# WORLD
# ════════════════════════════════════════════════════════════
class World:
    """Manages terrain, decorations, mobs, bosses, shrines."""
    def __init__(self, seed=42):
        self.seed = seed
        self.mobs: List[Mob] = []
        self.bosses: List[Boss] = []
        self.shrines: List[Shrine] = []
        self.cookie_monster: CookieMonsterNPC = None
        self.grandma: GrandmaNPC = None
        self.evil_grandma: EvilGrandmaNPC = None
        self.trees = []  # (x, z, type, height)
        self.rocks = []  # (x, z, size)
        self.pickups = []  # (x, y, z, type, collected)
        self._terrain_cache = {}
        self._generate()

    def _generate(self):
        """Generate world content."""
        # Generate shrines
        for stype, wx, wz, desc in SHRINE_DEFINITIONS:
            self.shrines.append(Shrine(stype, wx, wz, desc))

        # Generate bosses
        for btype, bx, bz in BOSS_SPAWNS:
            wy = walkable_y(bx * TILE_SIZE, bz * TILE_SIZE, self.seed)
            if wy is None:
                wy = 0
            self.bosses.append(Boss(btype, bx * TILE_SIZE, wy, bz * TILE_SIZE))

        # Spawn Cookie Monster NPC (friendly vendor)
        cm_x = COOKIE_MONSTER_POS[0] * TILE_SIZE
        cm_z = COOKIE_MONSTER_POS[1] * TILE_SIZE
        cm_y = walkable_y(cm_x, cm_z, self.seed)
        if cm_y is None:
            cm_y = 0
        self.cookie_monster = CookieMonsterNPC(cm_x, cm_y, cm_z)

        # Spawn Grandma NPC
        gm_x = GRANDMA_POS[0] * TILE_SIZE
        gm_z = GRANDMA_POS[1] * TILE_SIZE
        gm_y = walkable_y(gm_x, gm_z, self.seed)
        if gm_y is None:
            gm_y = 0
        self.grandma = GrandmaNPC(gm_x, gm_y, gm_z)

        # Spawn Evil Grandma NPC
        eg_x = EVIL_GRANDMA_POS[0] * TILE_SIZE
        eg_z = EVIL_GRANDMA_POS[1] * TILE_SIZE
        eg_y = walkable_y(eg_x, eg_z, self.seed)
        if eg_y is None:
            eg_y = 0
        self.evil_grandma = EvilGrandmaNPC(eg_x, eg_y, eg_z)

        # Generate mob camps (keep spawn area clear: 90-110 range)
        random.seed(self.seed)
        for _ in range(60):
            cx = random.randint(10, WORLD_SIZE - 10)
            cz = random.randint(10, WORLD_SIZE - 10)
            # Skip spawn area so player doesn't get camped
            if 85 <= cx <= 115 and 85 <= cz <= 115:
                continue
            wx, wz = cx * TILE_SIZE, cz * TILE_SIZE
            h = get_height(wx, wz, self.seed)
            biome = get_biome_from_height(h)
            if biome in (Biome.DEEP_WATER, Biome.SHALLOW_WATER):
                continue
            wy = walkable_y(wx, wz, self.seed)
            if wy is None:
                continue

            # Choose mob type based on biome
            if biome == Biome.SNOW:
                mob_choices = [MobType.HUSK_CRAWLER, MobType.STONEBEAST]
            elif biome == Biome.MOUNTAIN:
                mob_choices = [MobType.STONEBEAST, MobType.CAVE_FIEND, MobType.THUGNOK]
            elif biome == Biome.FOREST:
                mob_choices = [MobType.GRUNKLE, MobType.SKARVYN, MobType.DOOM_GRASP]
            elif biome == Biome.PLAINS:
                mob_choices = [MobType.GRUNKLE, MobType.THUGNOK, MobType.GULPWORM]
            else:
                mob_choices = [MobType.GRUNKLE, MobType.HUSK_CRAWLER]

            camp_size = random.randint(2, 5)
            for i in range(camp_size):
                ox = random.uniform(-6, 6)
                oz = random.uniform(-6, 6)
                mx, mz = wx + ox, wz + oz
                my = walkable_y(mx, mz, self.seed)
                if my is None:
                    my = wy
                mob = Mob(random.choice(mob_choices), mx, my, mz)
                self.mobs.append(mob)

        # Spawn some Thundermanes (rare, in plains)
        for _ in range(4):
            tx = random.randint(30, 170) * TILE_SIZE
            tz = random.randint(30, 170) * TILE_SIZE
            ty = walkable_y(tx, tz, self.seed)
            if ty is not None:
                self.mobs.append(Mob(MobType.THUNDERMANE, tx, ty, tz))

        # Spawn Linus mobs (wanders everywhere)
        for _ in range(6):
            lx = random.randint(20, 180) * TILE_SIZE
            lz = random.randint(20, 180) * TILE_SIZE
            ly = walkable_y(lx, lz, self.seed)
            if ly is not None:
                self.mobs.append(Mob(MobType.LINUS, lx, ly, lz))

        # Spawn Lesses (fat chickens, friendly, can be fused)
        for _ in range(10):
            lx = random.randint(20, 180) * TILE_SIZE
            lz = random.randint(20, 180) * TILE_SIZE
            ly = walkable_y(lx, lz, self.seed)
            if ly is not None:
                h = get_height(lx, lz, self.seed)
                biome = get_biome_from_height(h)
                if biome in (Biome.PLAINS, Biome.FOREST):
                    self.mobs.append(Mob(MobType.LESSE, lx, ly, lz))

        # Generate trees
        for _ in range(400):
            tx = random.randint(5, WORLD_SIZE - 5) * TILE_SIZE
            tz = random.randint(5, WORLD_SIZE - 5) * TILE_SIZE
            h = get_height(tx, tz, self.seed)
            biome = get_biome_from_height(h)
            if biome in (Biome.FOREST, Biome.PLAINS) and random.random() < 0.7:
                ty = walkable_y(tx, tz, self.seed)
                if ty is not None:
                    tree_h = random.uniform(2.5, 5.0)
                    tree_type = random.choice(['oak', 'pine', 'birch'])
                    self.trees.append((tx, tz, tree_type, tree_h))

        # Generate rocks
        for _ in range(150):
            rx = random.randint(5, WORLD_SIZE - 5) * TILE_SIZE
            rz = random.randint(5, WORLD_SIZE - 5) * TILE_SIZE
            h = get_height(rx, rz, self.seed)
            biome = get_biome_from_height(h)
            if biome in (Biome.MOUNTAIN, Biome.PLAINS, Biome.FOREST):
                self.rocks.append((rx, rz, random.uniform(0.3, 1.2)))

        # Pickups (weapons, materials)
        pickup_types = ['arrows', 'heart', 'material', 'weapon_spear', 'weapon_fire_rod', 'weapon_bombs']
        for _ in range(80):
            px = random.randint(10, WORLD_SIZE - 10) * TILE_SIZE
            pz = random.randint(10, WORLD_SIZE - 10) * TILE_SIZE
            py = walkable_y(px, pz, self.seed)
            if py is not None:
                self.pickups.append([px, py, pz, random.choice(pickup_types), False])

    def get_terrain_tile(self, tx, tz):
        """Get cached terrain data for a tile."""
        key = (tx, tz)
        if key not in self._terrain_cache:
            wx = tx * TILE_SIZE
            wz = tz * TILE_SIZE
            h = get_height(wx, wz, self.seed)
            biome = get_biome_from_height(h)
            color = get_biome_color(biome, h)
            y = max(-0.3, (h - 0.3) * 15.0)
            if biome in (Biome.DEEP_WATER, Biome.SHALLOW_WATER):
                y = -0.3
            self._terrain_cache[key] = (wx, wz, y, color, biome)
        return self._terrain_cache[key]

    def draw_terrain(self, player_x, player_z):
        """Draw visible terrain tiles around the player."""
        ptx = int(player_x / TILE_SIZE)
        ptz = int(player_z / TILE_SIZE)

        # Batch draw terrain
        glBegin(GL_QUADS)
        for tx in range(max(0, ptx - VIEW_TILES), min(WORLD_SIZE, ptx + VIEW_TILES)):
            for tz in range(max(0, ptz - VIEW_TILES), min(WORLD_SIZE, ptz + VIEW_TILES)):
                wx, wz, y, color, biome = self.get_terrain_tile(tx, tz)
                # Distance check
                dx = wx - player_x
                dz = wz - player_z
                if dx * dx + dz * dz > VIEW_DIST * VIEW_DIST:
                    continue
                draw_flat_quad(wx, wz, TILE_SIZE, y, color)
        glEnd()

        # Water plane
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.1, 0.3, 0.6, 0.6)
        water_y = -0.1
        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        extent = VIEW_TILES * TILE_SIZE
        glVertex3f(player_x - extent, water_y, player_z - extent)
        glVertex3f(player_x + extent, water_y, player_z - extent)
        glVertex3f(player_x + extent, water_y, player_z + extent)
        glVertex3f(player_x - extent, water_y, player_z + extent)
        glEnd()
        glDisable(GL_BLEND)

    def draw_objects(self, player_x, player_z):
        """Draw trees, rocks, pickups near player."""
        vd2 = VIEW_DIST * VIEW_DIST * 0.5

        # Trees
        for tx, tz, tree_type, tree_h in self.trees:
            dx = tx - player_x
            dz = tz - player_z
            if dx * dx + dz * dz > vd2:
                continue
            ty = walkable_y(tx, tz, self.seed)
            if ty is None:
                ty = 0
            # Trunk
            trunk_color = (100, 70, 40) if tree_type != 'birch' else (200, 195, 180)
            draw_cylinder(tx, ty, tz, 0.2, tree_h * 0.6, trunk_color, 6)
            # Canopy
            if tree_type == 'pine':
                for i in range(3):
                    cy = ty + tree_h * 0.4 + i * tree_h * 0.2
                    cr = (tree_h * 0.4) * (1 - i * 0.3)
                    draw_cone(tx, cy, tz, cr, tree_h * 0.25, (30, 100 + i * 15, 30))
            elif tree_type == 'oak':
                draw_sphere(tx, ty + tree_h * 0.7, tz, tree_h * 0.35, (40, 120, 35))
            else:
                draw_sphere(tx, ty + tree_h * 0.7, tz, tree_h * 0.3, (60, 140, 50))

        # Rocks
        for rx, rz, rs in self.rocks:
            dx = rx - player_x
            dz = rz - player_z
            if dx * dx + dz * dz > vd2:
                continue
            ry = walkable_y(rx, rz, self.seed)
            if ry is None:
                ry = 0
            draw_sphere(rx, ry + rs * 0.3, rz, rs * 0.5, (130, 125, 115))

        # Pickups
        for pickup in self.pickups:
            if pickup[4]:  # collected
                continue
            px, py, pz, ptype, _ = pickup
            dx = px - player_x
            dz = pz - player_z
            if dx * dx + dz * dz > vd2 * 0.3:
                continue
            bob = math.sin(time.time() * 3 + px) * 0.15
            if ptype == 'arrows':
                draw_cube(px, py + 0.5 + bob, pz, 0.15, 0.3, 0.05, (140, 100, 50))
            elif ptype == 'heart':
                draw_sphere(px, py + 0.5 + bob, pz, 0.2, (255, 50, 80))
            elif ptype == 'material':
                draw_cube(px, py + 0.4 + bob, pz, 0.15, 0.15, 0.15, (200, 180, 50))
            elif ptype.startswith('weapon_'):
                draw_sphere(px, py + 0.6 + bob, pz, 0.25, (150, 100, 220))

    def draw_shrines(self, player_x, player_z):
        """Draw shrine exteriors."""
        for shrine in self.shrines:
            dx = shrine.wx - player_x
            dz = shrine.wz - player_z
            if dx * dx + dz * dz < VIEW_DIST * VIEW_DIST:
                shrine.draw_exterior(self.seed)

    def update(self, dt, player):
        """Update all world entities."""
        for mob in self.mobs:
            if mob.alive:
                d = dist2d(mob.x, mob.z, player.x, player.z)
                if d < VIEW_DIST:
                    # Lesses are peaceful - handle separately
                    if mob.mob_type == MobType.LESSE:
                        mob.anim_time += dt
                        # Fused Lesse shoots fire at nearby enemies
                        if getattr(mob, 'fused', False):
                            mob.fuse_timer = getattr(mob, 'fuse_timer', 0) - dt
                            mob.fire_cooldown = getattr(mob, 'fire_cooldown', 0) - dt
                            if mob.fuse_timer <= 0:
                                mob.fused = False
                            elif mob.fire_cooldown <= 0:
                                for target in self.mobs:
                                    if target.alive and target.mob_type != MobType.LESSE and target is not mob:
                                        td = dist2d(mob.x, mob.z, target.x, target.z)
                                        if td < 15:
                                            target.take_damage(8)
                                            if not target.alive:
                                                player.xp += target.xp
                                            mob.fire_cooldown = 1.5
                                            break
                        else:
                            # Wander randomly
                            if random.random() < 0.01:
                                mob.x += random.uniform(-0.3, 0.3)
                                mob.z += random.uniform(-0.3, 0.3)
                        continue
                    mob.update(dt, player.x, player.y, player.z, self.seed)
                    # Mob attacks player
                    if mob.can_attack() and dist2d(mob.x, mob.z, player.x, player.z) < ATTACK_RANGE * 1.5:
                        dmg = mob.do_attack()
                        player.take_damage(dmg)

        for boss in self.bosses:
            if boss.alive:
                d = dist2d(boss.x, boss.z, player.x, player.z)
                if d < boss.arena_radius:
                    boss.update(dt, player.x, player.y, player.z, self.seed)
                    if boss.can_attack() and dist2d(boss.x, boss.z, player.x, player.z) < ATTACK_RANGE * 2.5:
                        dmg = boss.do_attack()
                        player.take_damage(dmg)

        # Update Cookie Monster NPC
        if self.cookie_monster:
            self.cookie_monster.update(dt, player.x, player.z)
        # Update Grandma NPCs
        if self.grandma:
            self.grandma.update(dt, player.x, player.z)
        if self.evil_grandma:
            self.evil_grandma.update(dt, player.x, player.z)

        # Arrow collision with mobs/bosses (skip Lesses)
        for arrow in player.projectiles:
            if not arrow.alive:
                continue
            for mob in self.mobs:
                if mob.alive and mob.mob_type != MobType.LESSE and dist3d(arrow.x, arrow.y, arrow.z, mob.x, mob.y + mob.size * 0.5, mob.z) < mob.size:
                    mob.take_damage(arrow.damage)
                    arrow.alive = False
                    if not mob.alive:
                        player.xp += mob.xp
                    break
            for boss in self.bosses:
                if boss.alive and dist3d(arrow.x, arrow.y, arrow.z, boss.x, boss.y + boss.size * 0.5, boss.z) < boss.size:
                    boss.take_damage(arrow.damage)
                    arrow.alive = False
                    break

        # Pickup collection
        for pickup in self.pickups:
            if pickup[4]:
                continue
            if dist2d(pickup[0], pickup[2], player.x, player.z) < 2.0:
                pickup[4] = True
                ptype = pickup[3]
                play_sfx('pickup')
                if ptype == 'arrows':
                    player.arrows += 5
                elif ptype == 'heart':
                    player.hp = min(player.max_hp, player.hp + 20)
                elif ptype == 'material':
                    player.xp += 5
                elif ptype == 'weapon_spear' and WeaponType.SPEAR not in player.available_weapons:
                    player.available_weapons.append(WeaponType.SPEAR)
                elif ptype == 'weapon_fire_rod' and WeaponType.FIRE_ROD not in player.available_weapons:
                    player.available_weapons.append(WeaponType.FIRE_ROD)
                elif ptype == 'weapon_bombs' and WeaponType.BOMBS not in player.available_weapons:
                    player.available_weapons.append(WeaponType.BOMBS)

    def draw_mobs(self, player_x, player_z):
        for mob in self.mobs:
            if mob.alive and dist2d(mob.x, mob.z, player_x, player_z) < VIEW_DIST:
                mob.draw()

    def draw_bosses(self, player_x, player_z):
        for boss in self.bosses:
            if boss.alive and dist2d(boss.x, boss.z, player_x, player_z) < VIEW_DIST:
                boss.draw()

    def draw_cookie_monster(self, player_x, player_z):
        if self.cookie_monster and dist2d(self.cookie_monster.x, self.cookie_monster.z, player_x, player_z) < VIEW_DIST:
            self.cookie_monster.draw()
            self.cookie_monster.draw_name()

    def draw_npcs(self, player_x, player_z):
        for npc in (self.grandma, self.evil_grandma):
            if npc and dist2d(npc.x, npc.z, player_x, player_z) < VIEW_DIST:
                npc.draw()
                npc.draw_name()

    def draw_house(self, player_x, player_z):
        """Draw the player's house in the world."""
        hx, hz = HOUSE_POS[0] * TILE_SIZE, HOUSE_POS[1] * TILE_SIZE
        if dist2d(hx, hz, player_x, player_z) > VIEW_DIST:
            return
        hy = walkable_y(hx, hz, self.seed)
        if hy is None:
            hy = 0
        glPushMatrix()
        glTranslatef(hx, hy, hz)
        # House base (wooden walls)
        glColor3f(0.6, 0.4, 0.2)
        glBegin(GL_QUADS)
        s = 2.0  # house half-size
        h = 3.0  # house height
        # Front
        glVertex3f(-s, 0, s); glVertex3f(s, 0, s); glVertex3f(s, h, s); glVertex3f(-s, h, s)
        # Back
        glVertex3f(-s, 0, -s); glVertex3f(-s, h, -s); glVertex3f(s, h, -s); glVertex3f(s, 0, -s)
        # Left
        glVertex3f(-s, 0, -s); glVertex3f(-s, 0, s); glVertex3f(-s, h, s); glVertex3f(-s, h, -s)
        # Right
        glVertex3f(s, 0, -s); glVertex3f(s, h, -s); glVertex3f(s, h, s); glVertex3f(s, 0, s)
        glEnd()
        # Roof (red triangle)
        glColor3f(0.7, 0.15, 0.1)
        glBegin(GL_TRIANGLES)
        # Front roof
        glVertex3f(-s - 0.3, h, s + 0.3); glVertex3f(s + 0.3, h, s + 0.3); glVertex3f(0, h + 2, 0)
        # Back roof
        glVertex3f(-s - 0.3, h, -s - 0.3); glVertex3f(0, h + 2, 0); glVertex3f(s + 0.3, h, -s - 0.3)
        # Left roof
        glVertex3f(-s - 0.3, h, -s - 0.3); glVertex3f(-s - 0.3, h, s + 0.3); glVertex3f(0, h + 2, 0)
        # Right roof
        glVertex3f(s + 0.3, h, s + 0.3); glVertex3f(s + 0.3, h, -s - 0.3); glVertex3f(0, h + 2, 0)
        glEnd()
        # Door
        glColor3f(0.35, 0.2, 0.1)
        glBegin(GL_QUADS)
        glVertex3f(-0.5, 0, s + 0.01); glVertex3f(0.5, 0, s + 0.01)
        glVertex3f(0.5, 1.8, s + 0.01); glVertex3f(-0.5, 1.8, s + 0.01)
        glEnd()
        # Windows
        glColor3f(0.5, 0.7, 0.9)
        glBegin(GL_QUADS)
        # Left window
        glVertex3f(-1.5, 1.5, s + 0.01); glVertex3f(-0.8, 1.5, s + 0.01)
        glVertex3f(-0.8, 2.3, s + 0.01); glVertex3f(-1.5, 2.3, s + 0.01)
        # Right window
        glVertex3f(0.8, 1.5, s + 0.01); glVertex3f(1.5, 1.5, s + 0.01)
        glVertex3f(1.5, 2.3, s + 0.01); glVertex3f(0.8, 2.3, s + 0.01)
        glEnd()
        glPopMatrix()


# ════════════════════════════════════════════════════════════
# HUD RENDERING (Pygame overlay on OpenGL)
# ════════════════════════════════════════════════════════════
class HUD:
    def __init__(self):
        self.font_large = pygame.font.SysFont('Arial', 28, bold=True)
        self.font_med = pygame.font.SysFont('Arial', 20, bold=True)
        self.font_small = pygame.font.SysFont('Arial', 16)
        self.font_title = pygame.font.SysFont('Arial', 64, bold=True)
        self.font_subtitle = pygame.font.SysFont('Arial', 32)
        self.surface = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self.notifications = []  # (text, timer)
        self._tex_id = None

    def add_notification(self, text, duration=3.0):
        self.notifications.append([text, duration])

    def update(self, dt):
        alive = []
        for notif in self.notifications:
            notif[1] -= dt
            if notif[1] > 0:
                alive.append(notif)
        self.notifications = alive

    def draw_game_hud(self, player, camera, state, world=None):
        """Draw complete game HUD."""
        self.surface.fill((0, 0, 0, 0))

        # Hearts (HP)
        hearts = player.max_hp // 20
        current_hearts = player.hp / 20.0
        hx, hy = 20, 20
        for i in range(hearts):
            if current_hearts >= i + 1:
                color = (220, 40, 40)
            elif current_hearts > i:
                color = (180, 80, 80)
            else:
                color = (60, 30, 30)
            pygame.draw.polygon(self.surface, color, [
                (hx + i * 28 + 10, hy + 2),
                (hx + i * 28 + 18, hy - 4),
                (hx + i * 28 + 22, hy + 2),
                (hx + i * 28 + 10, hy + 14),
            ])
            pygame.draw.polygon(self.surface, color, [
                (hx + i * 28 + 10, hy + 2),
                (hx + i * 28 + 2, hy - 4),
                (hx + i * 28 - 2, hy + 2),
                (hx + i * 28 + 10, hy + 14),
            ])

        # Stamina wheel
        stam_x, stam_y = 20, 55
        stam_w = 150
        stam_pct = player.stamina / player.max_stamina
        pygame.draw.rect(self.surface, (30, 30, 30, 180), (stam_x, stam_y, stam_w, 10), border_radius=5)
        pygame.draw.rect(self.surface, (60, 200, 90), (stam_x, stam_y, int(stam_w * stam_pct), 10), border_radius=5)

        # Loadout display
        lx, ly = SCREEN_W - 250, SCREEN_H - 100
        pygame.draw.rect(self.surface, (20, 20, 30, 180), (lx, ly, 230, 80), border_radius=8)
        loadout_text = f"Loadout {player.current_loadout}"
        self._draw_text(loadout_text, lx + 10, ly + 5, self.font_small, (200, 200, 220))

        left_name = WEAPON_DATA[player.loadout.left]['name']
        right_name = WEAPON_DATA[player.loadout.right]['name']
        self._draw_text(f"L: {left_name}", lx + 10, ly + 28, self.font_small, (255, 220, 100))
        self._draw_text(f"R: {right_name}", lx + 10, ly + 48, self.font_small, (100, 200, 255))
        self._draw_text("Scroll to switch", lx + 10, ly + 65, self.font_small, (150, 150, 150))

        # Level & XP
        self._draw_text(f"Lv.{player.level}", 20, 75, self.font_med, (255, 220, 100))
        xp_needed = player.level * 100
        xp_pct = player.xp / xp_needed
        pygame.draw.rect(self.surface, (30, 30, 10, 180), (20, 100, 100, 8), border_radius=4)
        pygame.draw.rect(self.surface, (200, 180, 50), (20, 100, int(100 * xp_pct), 8), border_radius=4)

        # Crown shards
        self._draw_text(f"Crown Shards: {player.crown_shards}", 20, 115, self.font_small, (180, 220, 255))

        # Arrows
        self._draw_text(f"Arrows: {player.arrows}", 20, 135, self.font_small, (200, 170, 100))

        # Rupees
        self._draw_text(f"Rupees: {player.rupees}", 20, 155, self.font_small, (100, 255, 100))

        # Cookies
        self._draw_text(f"Cookies: {player.cookies}", 20, 175, self.font_small, (255, 220, 100))

        # Minimap
        self._draw_minimap(player, world)

        # Crosshair
        cx, cy = SCREEN_W // 2, SCREEN_H // 2
        pygame.draw.line(self.surface, (255, 255, 255, 120), (cx - 10, cy), (cx + 10, cy), 1)
        pygame.draw.line(self.surface, (255, 255, 255, 120), (cx, cy - 10), (cx, cy + 10), 1)

        # Notifications
        for i, (text, timer) in enumerate(self.notifications):
            alpha = min(255, int(timer * 255))
            self._draw_text(text, SCREEN_W // 2 - 150, 160 + i * 30, self.font_med, (255, 255, 220, alpha))

        # Interaction prompts
        if world and world.cookie_monster:
            cm = world.cookie_monster
            if dist2d(player.x, player.z, cm.x, cm.z) < INTERACT_RANGE:
                self._draw_text_centered("[E] Talk to Cookie Monster", SCREEN_H // 2 + 60, self.font_med, (210, 170, 80))
        if world and world.grandma:
            gm = world.grandma
            if dist2d(player.x, player.z, gm.x, gm.z) < INTERACT_RANGE:
                self._draw_text_centered("[E] Visit Grandma's Kitchen", SCREEN_H // 2 + 60, self.font_med, (255, 200, 150))
        if world and world.evil_grandma:
            eg = world.evil_grandma
            if dist2d(player.x, player.z, eg.x, eg.z) < INTERACT_RANGE:
                self._draw_text_centered("[E] Talk to Evil Grandma", SCREEN_H // 2 + 60, self.font_med, (150, 255, 100))
        if player.has_house:
            hx, hz = HOUSE_POS[0] * TILE_SIZE, HOUSE_POS[1] * TILE_SIZE
            if dist2d(player.x, player.z, hx, hz) < INTERACT_RANGE:
                self._draw_text_centered("[E] Enter Your House", SCREEN_H // 2 + 60, self.font_med, (255, 220, 150))

        # Controls hint
        self._draw_text("WASD:Move  L/R Click:Attack/Defend  Scroll:Loadout  E:Interact  Tab:Inventory  MMB:Look",
                       10, SCREEN_H - 25, self.font_small, (150, 150, 160))

        self._render_to_gl()

    def _draw_minimap(self, player, world):
        """Draw a minimap in the top-right corner."""
        mm_x, mm_y = SCREEN_W - 170, 10
        mm_size = 150
        pygame.draw.rect(self.surface, (10, 10, 20, 200), (mm_x, mm_y, mm_size, mm_size), border_radius=5)
        pygame.draw.rect(self.surface, (80, 80, 100), (mm_x, mm_y, mm_size, mm_size), 2, border_radius=5)

        # Scale: map each pixel to ~4 tiles
        scale = mm_size / (VIEW_TILES * 2 * TILE_SIZE)
        cx = player.x
        cz = player.z

        if world:
            # Draw shrines as dots
            for shrine in world.shrines:
                sx = mm_x + mm_size // 2 + int((shrine.wx - cx) * scale)
                sz = mm_y + mm_size // 2 + int((shrine.wz - cz) * scale)
                if mm_x < sx < mm_x + mm_size and mm_y < sz < mm_y + mm_size:
                    c = (100, 255, 100) if shrine.completed else (100, 180, 255)
                    pygame.draw.circle(self.surface, c, (sx, sz), 3)

            # Draw bosses
            for boss in world.bosses:
                if boss.alive:
                    bx = mm_x + mm_size // 2 + int((boss.x - cx) * scale)
                    bz = mm_y + mm_size // 2 + int((boss.z - cz) * scale)
                    if mm_x < bx < mm_x + mm_size and mm_y < bz < mm_y + mm_size:
                        pygame.draw.circle(self.surface, (255, 50, 50), (bx, bz), 4)

            # Draw Cookie Monster NPC
            if world.cookie_monster:
                cm = world.cookie_monster
                cmx = mm_x + mm_size // 2 + int((cm.x - cx) * scale)
                cmz = mm_y + mm_size // 2 + int((cm.z - cz) * scale)
                if mm_x < cmx < mm_x + mm_size and mm_y < cmz < mm_y + mm_size:
                    pygame.draw.circle(self.surface, (210, 170, 80), (cmx, cmz), 4)

            # Draw Grandma NPC
            if world.grandma:
                gm = world.grandma
                gmx = mm_x + mm_size // 2 + int((gm.x - cx) * scale)
                gmz = mm_y + mm_size // 2 + int((gm.z - cz) * scale)
                if mm_x < gmx < mm_x + mm_size and mm_y < gmz < mm_y + mm_size:
                    pygame.draw.circle(self.surface, (200, 100, 200), (gmx, gmz), 4)

            # Draw Evil Grandma NPC
            if world.evil_grandma:
                eg = world.evil_grandma
                egx = mm_x + mm_size // 2 + int((eg.x - cx) * scale)
                egz = mm_y + mm_size // 2 + int((eg.z - cz) * scale)
                if mm_x < egx < mm_x + mm_size and mm_y < egz < mm_y + mm_size:
                    pygame.draw.circle(self.surface, (100, 200, 80), (egx, egz), 4)

            # Draw House
            hx_w, hz_w = HOUSE_POS[0] * TILE_SIZE, HOUSE_POS[1] * TILE_SIZE
            hsx = mm_x + mm_size // 2 + int((hx_w - cx) * scale)
            hsz = mm_y + mm_size // 2 + int((hz_w - cz) * scale)
            if mm_x < hsx < mm_x + mm_size and mm_y < hsz < mm_y + mm_size:
                pygame.draw.rect(self.surface, (200, 180, 100), (hsx - 3, hsz - 3, 6, 6))

        # Player dot
        pygame.draw.circle(self.surface, (255, 255, 100), (mm_x + mm_size // 2, mm_y + mm_size // 2), 3)
        # Direction indicator
        rad = math.radians(player.facing)
        dx = -math.sin(rad) * 8
        dz = -math.cos(rad) * 8
        pygame.draw.line(self.surface, (255, 255, 100),
                        (mm_x + mm_size // 2, mm_y + mm_size // 2),
                        (mm_x + mm_size // 2 + int(dx), mm_y + mm_size // 2 + int(dz)), 2)

    def draw_title_screen(self):
        self.surface.fill((0, 0, 0, 200))
        # Title
        self._draw_text_centered("TEARS OF THE CROWN", SCREEN_H // 3, self.font_title, (255, 220, 100))
        self._draw_text_centered("A 3D Action Adventure", SCREEN_H // 3 + 70, self.font_subtitle, (200, 200, 220))
        self._draw_text_centered("Press ENTER to Start", SCREEN_H // 2 + 60, self.font_med, (180, 180, 200))
        self._draw_text_centered("Press L to Load Game", SCREEN_H // 2 + 95, self.font_med, (150, 150, 170))
        self._draw_text_centered("ESC to Quit", SCREEN_H // 2 + 130, self.font_small, (120, 120, 140))

        # Credits
        self._draw_text_centered("Explore the Verdant Realm • Conquer 16 Shrines • Defeat 6 Bosses", SCREEN_H - 80, self.font_small, (140, 140, 160))
        self._draw_text_centered("Overthrow the Dark Sovereign and claim the Crown!", SCREEN_H - 55, self.font_small, (140, 140, 160))
        self._render_to_gl()

    def draw_pause_screen(self):
        self.surface.fill((0, 0, 0, 150))
        self._draw_text_centered("PAUSED", SCREEN_H // 3, self.font_title, (255, 255, 255))
        self._draw_text_centered("Press ESC to Resume", SCREEN_H // 2, self.font_med, (200, 200, 220))
        self._draw_text_centered("Press S to Save Game", SCREEN_H // 2 + 35, self.font_med, (200, 200, 220))
        self._draw_text_centered("Press Q to Quit", SCREEN_H // 2 + 70, self.font_med, (200, 200, 220))
        self._render_to_gl()

    def draw_game_over(self):
        self.surface.fill((80, 0, 0, 200))
        self._draw_text_centered("YOU HAVE FALLEN", SCREEN_H // 3, self.font_title, (255, 100, 100))
        self._draw_text_centered("Press R to Respawn", SCREEN_H // 2 + 40, self.font_med, (200, 200, 220))
        self._draw_text_centered("Press ESC to Quit", SCREEN_H // 2 + 75, self.font_med, (150, 150, 170))
        self._render_to_gl()

    def draw_dialogue(self, speaker, text):
        """Draw a dialogue box at the bottom of the screen."""
        self.surface.fill((0, 0, 0, 0))
        overlay = pygame.Surface((SCREEN_W, 120), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.surface.blit(overlay, (0, SCREEN_H - 130))
        self._draw_text(speaker + ":", 30, SCREEN_H - 120, self.font_large, (255, 200, 100))
        self._draw_text(text, 30, SCREEN_H - 85, self.font_med, (220, 220, 240))
        self._render_to_gl()

    def draw_victory(self):
        self.surface.fill((0, 0, 0, 180))
        self._draw_text_centered("VICTORY!", SCREEN_H // 4, self.font_title, (255, 220, 100))
        self._draw_text_centered("The Dark Sovereign has been defeated!", SCREEN_H // 3 + 40, self.font_subtitle, (200, 220, 255))
        self._draw_text_centered("The Crown is restored to the realm!", SCREEN_H // 3 + 80, self.font_med, (200, 200, 220))
        self._draw_text_centered("Press ENTER to Continue Playing", SCREEN_H // 2 + 60, self.font_med, (180, 180, 200))
        self._render_to_gl()

    def draw_inventory(self, player):
        """Draw inventory and loadout customization screen."""
        self.surface.fill((0, 0, 0, 200))
        self._draw_text_centered("INVENTORY & LOADOUT", 30, self.font_large, (255, 220, 100))

        # Loadout 1
        self._draw_text("═══ Loadout 1 (Default) ═══", 50, 80, self.font_med, (180, 180, 200))
        self._draw_text(f"  Left Hand:  {WEAPON_DATA[player.loadout1.left]['name']}", 50, 110, self.font_med, (255, 220, 100))
        self._draw_text(f"  Right Hand: {WEAPON_DATA[player.loadout1.right]['name']}", 50, 140, self.font_med, (100, 200, 255))

        # Loadout 2
        self._draw_text("═══ Loadout 2 (Custom) ═══", 50, 190, self.font_med, (180, 180, 200))
        self._draw_text(f"  Left Hand:  {WEAPON_DATA[player.loadout2.left]['name']}", 50, 220, self.font_med, (255, 220, 100))
        self._draw_text(f"  Right Hand: {WEAPON_DATA[player.loadout2.right]['name']}", 50, 250, self.font_med, (100, 200, 255))

        # Available weapons
        self._draw_text("═══ Available Weapons ═══", 50, 310, self.font_med, (180, 180, 200))
        for i, wtype in enumerate(player.available_weapons):
            data = WEAPON_DATA[wtype]
            y = 345 + i * 30
            self._draw_text(f"  [{i+1}] {data['name']} - {data['type'].upper()} - Dmg: {data['damage']}",
                          50, y, self.font_small, (200, 200, 220))

        # Instructions
        self._draw_text("Press number key to select weapon, then:", 50, 560, self.font_small, (150, 150, 170))
        self._draw_text("  Z = Set as Loadout 2 LEFT hand", 50, 585, self.font_small, (255, 220, 100))
        self._draw_text("  X = Set as Loadout 2 RIGHT hand", 50, 610, self.font_small, (100, 200, 255))
        self._draw_text("  Tab = Close inventory", 50, 640, self.font_small, (150, 150, 170))

        # Stats
        self._draw_text("═══ Stats ═══", 500, 80, self.font_med, (180, 180, 200))
        self._draw_text(f"  Level: {player.level}", 500, 110, self.font_small, (200, 200, 220))
        self._draw_text(f"  HP: {player.hp}/{player.max_hp}", 500, 135, self.font_small, (220, 80, 80))
        self._draw_text(f"  Cookies: {player.cookies}", 500, 160, self.font_small, (210, 170, 80))
        self._draw_text(f"  Arrows: {player.arrows}", 500, 185, self.font_small, (200, 170, 100))
        self._draw_text(f"  XP: {player.xp}/{player.level * 100}", 500, 210, self.font_small, (200, 180, 50))

        # Stat levels (view only - upgrade at Cookie Monster)
        self._draw_text("═══ Stat Levels ═══", 500, 250, self.font_med, (180, 180, 200))
        stat_names = ['attack', 'defense', 'speed', 'stamina']
        for i, stat in enumerate(stat_names):
            lvl = player.stat_levels[stat]
            bars = '█' * lvl + '░' * (player.max_stat_level - lvl)
            color = (100, 255, 100) if lvl == player.max_stat_level else (200, 200, 220)
            self._draw_text(f"  {stat.title()} [{bars}] Lv.{lvl}", 500, 280 + i * 28, self.font_small, color)
        self._draw_text("  Visit Cookie Monster to upgrade!", 500, 280 + 4 * 28, self.font_small, (210, 170, 80))

        # Abilities
        self._draw_text("═══ Abilities ═══", 500, 420, self.font_med, (180, 180, 200))
        for i, ability in enumerate(player.abilities):
            self._draw_text(f"  [{i+1}] {ability.value}", 500, 450 + i * 25, self.font_small, (200, 200, 220))

        self._render_to_gl()

    def draw_cookie_shop(self, player):
        """Draw Cookie Monster stat shop overlay."""
        self.surface.fill((0, 0, 0, 0))

        # Semi-transparent background
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((20, 10, 5, 180))
        self.surface.blit(overlay, (0, 0))

        # Title
        self._draw_text_centered("Cookie Monster's Shop", 40, self.font_title, (210, 170, 80))
        self._draw_text_centered("\"ME WANT COOKIES! Give cookies, me make you STRONG!\"", 110, self.font_small, (80, 180, 255))
        self._draw_text_centered(f"Your Cookies: {player.cookies}", 150, self.font_med, (255, 220, 100))

        # Stat upgrades
        self._draw_text_centered("═══ Trade Cookies for Power ═══", 200, self.font_med, (210, 170, 80))
        stat_keys = {'attack': 'F1', 'defense': 'F2', 'speed': 'F3', 'stamina': 'F4'}
        stat_desc = {
            'attack': '+5 weapon damage',
            'defense': '+20 max HP',
            'speed': '+1 move speed',
            'stamina': '+25 max stamina',
        }
        y = 240
        for stat, key in stat_keys.items():
            lvl = player.stat_levels[stat]
            cost = lvl + 1 if lvl < player.max_stat_level else '-'
            bars = '█' * lvl + '░' * (player.max_stat_level - lvl)
            if lvl >= player.max_stat_level:
                color = (100, 255, 100)
                label = f"  [{key}] {stat.title()} [{bars}] — MAX"
            elif player.cookies >= (lvl + 1):
                color = (255, 255, 200)
                label = f"  [{key}] {stat.title()} [{bars}] — {cost} cookie{'s' if cost > 1 else ''} → {stat_desc[stat]}"
            else:
                color = (120, 120, 120)
                label = f"  [{key}] {stat.title()} [{bars}] — {cost} cookie{'s' if cost > 1 else ''} (not enough!)"
            self._draw_text_centered(label, y, self.font_small, color)
            y += 35

        # House and Anvil shop section
        y += 10
        self._draw_text_centered("═══ Real Estate & Tools ═══", y, self.font_med, (210, 170, 80))
        y += 35
        if not player.has_house:
            color = (255, 255, 200) if player.rupees >= HOUSE_COST else (120, 120, 120)
            self._draw_text_centered(f"  [F5] Buy House — {HOUSE_COST} rupees (have {player.rupees})", y, self.font_small, color)
        else:
            self._draw_text_centered("  [F5] House — OWNED", y, self.font_small, (100, 255, 100))
        y += 30
        if player.has_house and not player.has_anvil:
            color = (255, 255, 200) if player.rupees >= 30 else (120, 120, 120)
            self._draw_text_centered(f"  [F6] Buy Anvil — 30 rupees (have {player.rupees})", y, self.font_small, color)
        elif player.has_anvil:
            self._draw_text_centered("  [F6] Anvil — OWNED", y, self.font_small, (100, 255, 100))
        else:
            self._draw_text_centered("  [F6] Anvil — Need house first", y, self.font_small, (120, 120, 120))
        y += 40

        self._draw_text_centered("[ESC] or [TAB] to leave", y, self.font_small, (150, 150, 150))

        self._render_to_gl()

    def draw_grandma_kitchen(self, player):
        """Draw Grandma's Kitchen cooking overlay."""
        self.surface.fill((0, 0, 0, 0))
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((30, 15, 5, 180))
        self.surface.blit(overlay, (0, 0))

        self._draw_text_centered("Grandma's Kitchen", 40, self.font_title, (255, 200, 150))
        self._draw_text_centered("\"Come in dear! Let grandma cook something nice for you!\"", 110, self.font_small, (255, 220, 180))
        self._draw_text_centered(f"Your Cookies: {player.cookies}  (each recipe costs 3 cookies)", 150, self.font_med, (255, 220, 100))

        self._draw_text_centered("═══ Recipes ═══", 200, self.font_med, (255, 200, 150))
        y = 240
        for i, recipe in enumerate(GRANDMA_RECIPES):
            key = f"F{i+1}"
            can_afford = player.cookies >= 3
            color = (255, 255, 200) if can_afford else (120, 120, 120)
            self._draw_text_centered(f"  [{key}] {recipe['name']} — {recipe['desc']}", y, self.font_small, color)
            y += 35

        self._draw_text_centered("[ESC] or [TAB] to leave", y + 30, self.font_small, (150, 150, 150))
        self._render_to_gl()

    def draw_evil_grandma(self, player):
        """Draw Evil Grandma's stat drain overlay."""
        self.surface.fill((0, 0, 0, 0))
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((10, 20, 10, 200))
        self.surface.blit(overlay, (0, 0))

        self._draw_text_centered("The Evil Grandma", 40, self.font_title, (150, 255, 100))
        self._draw_text_centered("\"Hehehehe... Let me take those pesky upgrades off your hands...\"", 110, self.font_small, (180, 255, 150))
        self._draw_text_centered(f"Your Cookies: {player.cookies}", 150, self.font_med, (255, 220, 100))

        self._draw_text_centered("═══ Drain Stats (get cookies back) ═══", 200, self.font_med, (150, 255, 100))
        stat_keys = {'attack': 'F1', 'defense': 'F2', 'speed': 'F3', 'stamina': 'F4'}
        y = 240
        for stat, key in stat_keys.items():
            lvl = player.stat_levels[stat]
            bars = '█' * lvl + '░' * (player.max_stat_level - lvl)
            if lvl > 0:
                refund = lvl
                color = (255, 200, 200)
                label = f"  [{key}] Drain {stat.title()} [{bars}] — get {refund} cookie{'s' if refund > 1 else ''} back"
            else:
                color = (120, 120, 120)
                label = f"  [{key}] {stat.title()} [{bars}] — nothing to drain"
            self._draw_text_centered(label, y, self.font_small, color)
            y += 35

        self._draw_text_centered("[ESC] or [TAB] to leave", y + 30, self.font_small, (150, 150, 150))
        self._render_to_gl()

    def draw_anvil_craft(self, player):
        """Draw Anvil crafting overlay."""
        self.surface.fill((0, 0, 0, 0))
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((15, 15, 25, 200))
        self.surface.blit(overlay, (0, 0))

        self._draw_text_centered("The Anvil", 40, self.font_title, (200, 200, 255))
        self._draw_text_centered("\"Forge powerful weapons with rupees!\"", 110, self.font_small, (180, 200, 255))
        self._draw_text_centered(f"Your Rupees: {player.rupees}", 150, self.font_med, (100, 255, 100))

        self._draw_text_centered("═══ Forge Weapons ═══", 200, self.font_med, (200, 200, 255))
        y = 240
        for i, recipe in enumerate(ANVIL_RECIPES):
            key = f"F{i+1}"
            wtype = recipe['weapon']
            wname = WEAPON_DATA[wtype]['name']
            cost = recipe['cost']
            owned = wtype in player.available_weapons
            if owned:
                color = (100, 255, 100)
                label = f"  [{key}] {wname} — OWNED"
            elif player.rupees >= cost:
                color = (255, 255, 200)
                label = f"  [{key}] {wname} (dmg:{WEAPON_DATA[wtype]['damage']}) — {cost} rupees"
            else:
                color = (120, 120, 120)
                label = f"  [{key}] {wname} (dmg:{WEAPON_DATA[wtype]['damage']}) — {cost} rupees (not enough!)"
            self._draw_text_centered(label, y, self.font_small, color)
            y += 35

        self._draw_text_centered("[ESC] or [TAB] to go back", y + 30, self.font_small, (150, 150, 150))
        self._render_to_gl()

    def draw_house(self, player):
        """Draw house interior view."""
        self.surface.fill((0, 0, 0, 0))
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((25, 20, 15, 200))
        self.surface.blit(overlay, (0, 0))

        self._draw_text_centered("Your House", 40, self.font_title, (255, 220, 150))
        self._draw_text_centered("\"Home sweet home!\"", 110, self.font_small, (255, 220, 180))

        y = 180
        self._draw_text_centered("═══ Your Items ═══", y, self.font_med, (255, 220, 150))
        y += 40
        if player.has_anvil:
            self._draw_text_centered("[F1] Use Anvil — forge weapons", y, self.font_small, (200, 200, 255))
            y += 35
        else:
            self._draw_text_centered("No anvil yet — buy one from Cookie Monster!", y, self.font_small, (150, 150, 150))
            y += 35

        # Show owned weapons
        y += 20
        self._draw_text_centered("═══ Weapon Collection ═══", y, self.font_med, (255, 220, 150))
        y += 35
        for wtype in player.available_weapons:
            wdata = WEAPON_DATA[wtype]
            self._draw_text_centered(f"• {wdata['name']} (dmg:{wdata['damage']}, range:{wdata['range']})", y, self.font_small, (200, 200, 200))
            y += 25

        self._draw_text_centered("[ESC] or [TAB] to leave", SCREEN_H - 40, self.font_small, (150, 150, 150))
        self._render_to_gl()

    def draw_cutscene(self, timer):
        """Draw TotK-style cutscene: Gardon Mok rises, sword decays, princess falls."""
        self.surface.fill((0, 0, 0, 0))
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

        progress = min(timer / 12.0, 1.0)  # 12 second cutscene

        if progress < 0.2:
            # Phase 1: Gardon Mok unleashes Gloom
            overlay.fill((10, 0, 15, 240))
            self.surface.blit(overlay, (0, 0))
            alpha = int(min(progress / 0.05, 1.0) * 255)
            self._draw_text_centered("GARDON MOK UNLEASHES THE GLOOM!", SCREEN_H // 2 - 60, self.font_title, (180, 50, 50, alpha))
            self._draw_text_centered("Dark power surges through the castle...", SCREEN_H // 2 + 10, self.font_large, (150, 100, 180, alpha))
            # Gloom tendrils
            for i in range(8):
                ox = SCREEN_W // 2 + int(math.sin(timer * 4 + i * 0.8) * 150)
                oy = SCREEN_H // 2 + 60 + int(math.cos(timer * 3 + i) * 40)
                self._draw_text("~", ox, oy, self.font_med, (80, 20, 100))
        elif progress < 0.4:
            # Phase 2: Sword decays
            overlay.fill((5, 0, 0, 220))
            self.surface.blit(overlay, (0, 0))
            self._draw_text_centered("The blade blocks the attack...", SCREEN_H // 2 - 80, self.font_large, (220, 220, 255))
            # Sword with decay cracks
            sword_lines = [
                "        /\\",
                "       / ~\\",
                "      / ~  \\",
                "     /  ~~  \\",
                "    / ~ || ~ \\",
                "       ~||~",
                "        ||",
                "      ==%%==",
                "        %%",
            ]
            sy = SCREEN_H // 2 - 20
            for line in sword_lines:
                self._draw_text_centered(line, sy, self.font_small, (120, 80, 60))
                sy += 18
            self._draw_text_centered("*The ancient blade DECAYS!*", SCREEN_H // 2 + 160, self.font_large, (255, 80, 50))
        elif progress < 0.6:
            # Phase 3: Castle shakes, Gardon sends surge
            overlay.fill((20, 0, 10, 230))
            self.surface.blit(overlay, (0, 0))
            shake_x = int(math.sin(timer * 20) * 5)
            self._draw_text_centered("The castle TREMBLES!", SCREEN_H // 2 - 60 + shake_x, self.font_title, (255, 100, 100))
            self._draw_text_centered("Gardon Mok: \"You cannot stop what has begun!\"", SCREEN_H // 2 + 10, self.font_large, (200, 150, 200))
        elif progress < 0.8:
            # Phase 4: Princess falls into the pit
            overlay.fill((0, 0, 0, 240))
            self.surface.blit(overlay, (0, 0))
            fall_progress = (progress - 0.6) / 0.2
            fall_y = int(fall_progress * SCREEN_H)
            # Draw the pit/chasm
            pit_cx, pit_cy = SCREEN_W // 2, SCREEN_H // 2 + 80
            pit_w, pit_h = 200, 60
            pygame.draw.ellipse(self.surface, (20, 0, 30), (pit_cx - pit_w // 2, pit_cy - pit_h // 2, pit_w, pit_h))
            pygame.draw.ellipse(self.surface, (60, 10, 80), (pit_cx - pit_w // 2, pit_cy - pit_h // 2, pit_w, pit_h), 3)
            # Gloom tendrils rising from pit
            for i in range(6):
                tx = pit_cx + int(math.sin(timer * 3 + i * 1.1) * (pit_w // 2 - 10))
                ty = pit_cy - int(abs(math.sin(timer * 2 + i * 0.7)) * 30)
                self._draw_text("~", tx, ty, self.font_med, (80, 20, 100))
            self._draw_text_centered("The Princess falls into the pit!", SCREEN_H // 2 - 80, self.font_title, (200, 180, 255))
            # Princess falling into the pit
            princess_y = min(SCREEN_H // 2 - 20 + fall_y, pit_cy - 10)
            princess_alpha = max(0, 255 - int(fall_progress * 300))
            self._draw_text_centered("O", princess_y, self.font_large, (255, 200, 220, max(princess_alpha, 30)))
            if fall_progress > 0.3:
                self._draw_text_centered("|\n/\\", princess_y + 20, self.font_small, (255, 180, 200, max(princess_alpha, 20)))
            self._draw_text_centered("He Na Man reaches out... but she falls into the darkness!", SCREEN_H // 2 + 140, self.font_med, (180, 160, 200))
        else:
            # Phase 5: Teleported to Sky Island
            sky_alpha = int((progress - 0.8) / 0.2 * 255)
            overlay.fill((100, 180, 255, min(sky_alpha, 200)))
            self.surface.blit(overlay, (0, 0))
            self._draw_text_centered("A mysterious force grabs you...", SCREEN_H // 2 - 60, self.font_large, (255, 255, 255))
            self._draw_text_centered("You awaken above the clouds.", SCREEN_H // 2, self.font_title, (255, 255, 200))
            self._draw_text_centered("The Great Sky Island", SCREEN_H // 2 + 60, self.font_large, (200, 230, 255))

        self._draw_text_centered("[ENTER/ESC/SPACE] Skip", SCREEN_H - 30, self.font_small, (100, 100, 100))
        self._render_to_gl()

    def draw_shrine_hud(self, shrine, player):
        """Draw HUD when inside a shrine."""
        self.surface.fill((0, 0, 0, 0))

        # Shrine name
        self._draw_text_centered(shrine.shrine_type.value, 20, self.font_large, (100, 200, 255))
        self._draw_text_centered(shrine.description, 55, self.font_small, (180, 180, 200))

        # Hearts
        hearts = player.max_hp // 20
        current_hearts = player.hp / 20.0
        hx, hy = 20, 90
        for i in range(hearts):
            color = (220, 40, 40) if current_hearts >= i + 1 else (60, 30, 30)
            pygame.draw.circle(self.surface, color, (hx + i * 25 + 10, hy), 8)

        # Status
        enemies_alive = sum(1 for e in shrine.enemies if e.alive)
        if enemies_alive > 0:
            self._draw_text(f"Enemies remaining: {enemies_alive}", 20, 115, self.font_med, (255, 100, 100))
        elif shrine.check_completion():
            self._draw_text("SHRINE CLEARED! Press E to claim reward", 20, 115, self.font_med, (100, 255, 100))
        else:
            self._draw_text("Solve the puzzle!", 20, 115, self.font_med, (255, 220, 100))

        self._draw_text("Press ESC to exit shrine", 20, SCREEN_H - 30, self.font_small, (150, 150, 160))
        self._render_to_gl()

    def _draw_text(self, text, x, y, font, color):
        if len(color) == 4:
            surf = font.render(text, True, color[:3])
            surf.set_alpha(color[3])
        else:
            surf = font.render(text, True, color)
        self.surface.blit(surf, (x, y))

    def _draw_text_centered(self, text, y, font, color):
        surf = font.render(text, True, color[:3] if len(color) > 3 else color)
        x = (SCREEN_W - surf.get_width()) // 2
        if len(color) == 4:
            surf.set_alpha(color[3])
        self.surface.blit(surf, (x, y))

    def _render_to_gl(self):
        """Render the pygame HUD surface as an OpenGL overlay."""
        data = pygame.image.tostring(self.surface, "RGBA", True)

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, SCREEN_W, 0, SCREEN_H, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        if self._tex_id is None:
            self._tex_id = glGenTextures(1)

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self._tex_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, SCREEN_W, SCREEN_H, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        glColor4f(1, 1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(0, 0)
        glTexCoord2f(1, 0); glVertex2f(SCREEN_W, 0)
        glTexCoord2f(1, 1); glVertex2f(SCREEN_W, SCREEN_H)
        glTexCoord2f(0, 1); glVertex2f(0, SCREEN_H)
        glEnd()

        glDisable(GL_TEXTURE_2D)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glDisable(GL_BLEND)


# ════════════════════════════════════════════════════════════
# SAVE / LOAD
# ════════════════════════════════════════════════════════════
def save_game(player, world, filepath=SAVE_FILE):
    data = {
        'player': player.get_save_data(),
        'completed_shrines': [i for i, s in enumerate(world.shrines) if s.completed],
        'defeated_bosses': [i for i, b in enumerate(world.bosses) if not b.alive],
        'collected_pickups': [i for i, p in enumerate(world.pickups) if p[4]],
    }
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def load_game(player, world, filepath=SAVE_FILE):
    if not os.path.exists(filepath):
        return False
    with open(filepath, 'r') as f:
        data = json.load(f)
    player.load_save_data(data.get('player', {}))
    for i in data.get('completed_shrines', []):
        if 0 <= i < len(world.shrines):
            world.shrines[i].completed = True
    for i in data.get('defeated_bosses', []):
        if 0 <= i < len(world.bosses):
            world.bosses[i].alive = False
            world.bosses[i].defeated = True
    for i in data.get('collected_pickups', []):
        if 0 <= i < len(world.pickups):
            world.pickups[i][4] = True
    return True


# ════════════════════════════════════════════════════════════
# MAIN GAME CLASS
# ════════════════════════════════════════════════════════════
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.OPENGL | pygame.DOUBLEBUF)
        pygame.display.set_caption("⚔️ Tears of the Crown — 3D Action Adventure")
        self.clock = pygame.time.Clock()

        # OpenGL setup
        self._init_gl()

        # Game objects - player spawns in underground castle
        self.player = Player(0, 0.5, 5)  # Castle-local coords: near the door
        self.camera = Camera()
        self.world = World(seed=42)
        self.particles = ParticleSystem()
        self.hud = HUD()
        self.in_castle = True  # Start in underground castle

        # State
        self.state = GameState.TITLE
        self.running = True
        self.dt = 0.016
        self.active_shrine = None
        self.shrine_player_x = 0
        self.shrine_player_z = 0

        # Inventory UI state
        self.selected_weapon_index = -1

        # Cutscene
        self.cutscene_timer = 0.0
        self.cutscene_done = False
        self.cutscene_phase = 'none'  # 'none', 'gardon_talk', 'fight', 'sword_break', 'princess_fall', 'sky_teleport'

        # Castle intro state (TotK-style)
        self.princess_x = 1.5    # Princess companion position in castle
        self.princess_z = 4.0    # Near the player's starting position
        self.princess_alive = True
        self.gardon_mok = None           # Boss entity, spawns when player reaches throne
        self.gardon_mok_triggered = False # Has Gardon Mok awakened?
        self.gardon_mok_defeated = False
        self.gardon_talk_timer = 0.0
        self.gardon_talk_lines = [
            "Gardon Mok: So... He Na Man and his princess have come.",
            "Gardon Mok: You think that rusted blade can harm ME?",
            "Gardon Mok: Rauru placed his trust in the wrong hero!",
            "Gardon Mok: Now... FEEL THE GLOOM!",
        ]
        self.gardon_talk_index = 0
        self.sword_broken = False
        # Castle Linus mob guards
        self.castle_mobs = []
        self._spawn_castle_mobs()

        # Sky Island
        self.on_sky_island = False
        self.sky_island_shrines_done = 0
        # Sky shrine positions (relative to sky island center at 100*TILE_SIZE)
        sky_cx = 100 * TILE_SIZE
        sky_cz = 100 * TILE_SIZE
        # Sky shrines are real Shrine objects so they are playable
        self.sky_shrines_data = [
            {'shrine_type': ShrineType.GRASP_TRIAL, 'ability': AbilityType.ULTRAHAND, 'ox': 40, 'oz': 0, 'name': 'Shrine of Ultrahand'},
            {'shrine_type': ShrineType.FORGE_TRIAL, 'ability': AbilityType.FUSE, 'ox': -40, 'oz': 0, 'name': 'Shrine of Fuse'},
            {'shrine_type': ShrineType.RISING_TRIAL, 'ability': AbilityType.ASCEND, 'ox': 0, 'oz': 40, 'name': 'Shrine of Ascend'},
            {'shrine_type': ShrineType.TIMEFLOW_TRIAL, 'ability': AbilityType.RECALL, 'ox': 0, 'oz': -40, 'name': 'Shrine of Recall'},
        ]
        self.sky_shrines = []
        for sd in self.sky_shrines_data:
            s = Shrine(sd['shrine_type'], 0, 0, sd['name'])
            s.wx = sky_cx + sd['ox']
            s.wz = sky_cz + sd['oz']
            s.completed = False
            s._sky_ability = sd['ability']
            s._sky_name = sd['name']
            self.sky_shrines.append(s)
        self.sky_cookie_monster_x = sky_cx + 20
        self.sky_cookie_monster_z = sky_cz + 20

        # Initialize sounds
        init_sounds()

    def _spawn_castle_mobs(self):
        """Spawn Linus guard mobs inside the castle for the intro."""
        positions = [(-5, 0, 0), (5, 0, 0), (-7, 0, -4), (7, 0, -4)]
        for px, py, pz in positions:
            mob = Mob(MobType.LINUS, px, py, pz)
            mob.aggro_range = 6.0  # Don't all rush at once
            mob.damage = 5  # Reduced for intro
            mob.speed = 2.0  # Slower guards
            self.castle_mobs.append(mob)

    def _init_gl(self):
        """Initialize OpenGL settings."""
        glClearColor(*C_SKY, 1.0)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)

        # Lighting
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # Light properties
        light_pos = [0.5, 1.0, 0.3, 0.0]  # Directional light
        light_ambient = [0.3, 0.3, 0.35, 1.0]
        light_diffuse = [0.9, 0.85, 0.8, 1.0]
        light_specular = [0.3, 0.3, 0.3, 1.0]
        glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
        glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
        glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular)

        # Fog
        glEnable(GL_FOG)
        glFogfv(GL_FOG_COLOR, [*C_FOG, 1.0])
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogf(GL_FOG_START, VIEW_DIST * 0.6)
        glFogf(GL_FOG_END, VIEW_DIST)

        # Projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60, SCREEN_W / SCREEN_H, 0.1, VIEW_DIST * 1.5)
        glMatrixMode(GL_MODELVIEW)

        glEnable(GL_NORMALIZE)

    def run(self):
        """Main game loop."""
        while self.running:
            self.dt = self.clock.tick(FPS) / 1000.0
            self.dt = min(self.dt, 0.05)  # Cap delta time

            self._handle_events()
            self._update()
            self._render()

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LSHIFT:
                    self.player.sprinting = False
                elif event.key in (pygame.K_LCTRL, pygame.K_RCTRL):
                    self.player.crouching = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mousedown(event)

            elif event.type == pygame.MOUSEBUTTONUP:
                pass  # Free mouse look always on

            elif event.type == pygame.MOUSEWHEEL:
                if self.state in (GameState.PLAYING, GameState.SHRINE, GameState.BOSS_FIGHT):
                    self.player.switch_loadout()
                    self.hud.add_notification(f"Loadout {self.player.current_loadout}")

            elif event.type == pygame.MOUSEMOTION:
                if self.state in (GameState.PLAYING, GameState.SHRINE, GameState.BOSS_FIGHT):
                    self.camera.yaw += event.rel[0] * CAM_SENSITIVITY
                    self.camera.pitch -= event.rel[1] * CAM_SENSITIVITY
                    self.camera.pitch = max(-80, min(-5, self.camera.pitch))

    def _handle_keydown(self, event):
        if self.state == GameState.TITLE:
            if event.key == pygame.K_RETURN:
                self.state = GameState.PLAYING
                self.camera.dist = 6.0  # Closer camera for castle interior
                self.player.invincible_timer = 8.0  # Spawn protection to explore
                self.hud.add_notification("You and the Princess explore beneath the Castle...")
                self.hud.add_notification("Defeat the Linus guards. Approach the throne.")
                play_sfx('menu')
                pygame.event.set_grab(True)
                pygame.mouse.set_visible(False)
            elif event.key == pygame.K_l:
                if load_game(self.player, self.world):
                    self.state = GameState.PLAYING
                    self.hud.add_notification("Game loaded!")
                    play_sfx('shrine_complete')
                    pygame.event.set_grab(True)
                    pygame.mouse.set_visible(False)
                    self.in_castle = False
                else:
                    self.hud.add_notification("No save file found!")
            elif event.key == pygame.K_ESCAPE:
                self.running = False

        elif self.state == GameState.PLAYING or self.state == GameState.BOSS_FIGHT:
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.PAUSE
                pygame.event.set_grab(False)
                pygame.mouse.set_visible(True)
                play_sfx('menu')
            elif event.key == pygame.K_TAB or event.key == pygame.K_i:
                self.state = GameState.INVENTORY
                self.selected_weapon_index = -1
                play_sfx('menu')
            elif event.key == pygame.K_SPACE:
                self.player.jump()
            elif event.key == pygame.K_LSHIFT:
                self.player.sprinting = True
            elif event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                self.player.crouching = True
            elif event.key == pygame.K_e:
                self._interact()
            elif event.key == pygame.K_q:
                # Cycle ability
                if self.player.abilities:
                    self.player.selected_ability = (self.player.selected_ability + 1) % len(self.player.abilities)
                    ability = self.player.abilities[self.player.selected_ability]
                    self.hud.add_notification(f"Ability: {ability.value}")
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                idx = event.key - pygame.K_1
                if idx < len(self.player.abilities):
                    self.player.selected_ability = idx
                    self.hud.add_notification(f"Ability: {self.player.abilities[idx].value}")
            elif event.key == pygame.K_f:
                self._use_ability()

        elif self.state == GameState.SHRINE:
            if event.key == pygame.K_ESCAPE:
                self._exit_shrine()
            elif event.key == pygame.K_SPACE:
                self.player.jump()
            elif event.key == pygame.K_e:
                # Check for chest interaction first
                opened_chest = False
                if self.active_shrine:
                    for ch in self.active_shrine.chests:
                        if not ch['opened'] and dist2d(self.player.x, self.player.z, ch['x'], ch['z']) < 2.0:
                            ch['opened'] = True
                            opened_chest = True
                            play_sfx('shrine_complete')
                            if ch['reward'] == 'cookie':
                                self.player.cookies += 2
                                self.hud.add_notification("Chest opened! Got 2 cookies!")
                            elif ch['reward'] == 'rupee':
                                self.player.rupees += 5
                                self.hud.add_notification("Chest opened! Got 5 rupees!")
                            else:
                                self.player.hp = min(self.player.hp + 20, self.player.max_hp)
                                self.hud.add_notification("Chest opened! Healed 20 HP!")
                            break
                if not opened_chest and self.active_shrine and self.active_shrine.check_completion():
                    self._complete_shrine()
            elif event.key == pygame.K_TAB or event.key == pygame.K_i:
                self.state = GameState.INVENTORY
                self.selected_weapon_index = -1
            elif event.key == pygame.K_f:
                self._use_ability()

        elif self.state == GameState.PAUSE:
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.PLAYING
                pygame.event.set_grab(True)
                pygame.mouse.set_visible(False)
                play_sfx('menu')
            elif event.key == pygame.K_s:
                save_game(self.player, self.world)
                self.hud.add_notification("Game saved!")
                play_sfx('shrine_complete')
            elif event.key == pygame.K_q:
                self.running = False

        elif self.state == GameState.INVENTORY:
            if event.key in (pygame.K_TAB, pygame.K_ESCAPE, pygame.K_i):
                self.state = GameState.PLAYING if not self.active_shrine else GameState.SHRINE
                pygame.event.set_grab(True)
                pygame.mouse.set_visible(False)
                play_sfx('menu')
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6):
                idx = event.key - pygame.K_1
                if idx < len(self.player.available_weapons):
                    self.selected_weapon_index = idx
                    wname = WEAPON_DATA[self.player.available_weapons[idx]]['name']
                    self.hud.add_notification(f"Selected: {wname}")
            elif event.key == pygame.K_z:
                if 0 <= self.selected_weapon_index < len(self.player.available_weapons):
                    wtype = self.player.available_weapons[self.selected_weapon_index]
                    self.player.loadout2.left = wtype
                    self.hud.add_notification(f"Loadout 2 LEFT: {WEAPON_DATA[wtype]['name']}")
                    play_sfx('loadout')
            elif event.key == pygame.K_x:
                if 0 <= self.selected_weapon_index < len(self.player.available_weapons):
                    wtype = self.player.available_weapons[self.selected_weapon_index]
                    self.player.loadout2.right = wtype
                    self.hud.add_notification(f"Loadout 2 RIGHT: {WEAPON_DATA[wtype]['name']}")
                    play_sfx('loadout')

        elif self.state == GameState.COOKIE_SHOP:
            if event.key in (pygame.K_TAB, pygame.K_ESCAPE):
                self.state = GameState.PLAYING
                pygame.event.set_grab(True)
                pygame.mouse.set_visible(False)
                play_sfx('menu')
            elif event.key == pygame.K_F1:
                self._upgrade_stat('attack')
            elif event.key == pygame.K_F2:
                self._upgrade_stat('defense')
            elif event.key == pygame.K_F3:
                self._upgrade_stat('speed')
            elif event.key == pygame.K_F4:
                self._upgrade_stat('stamina')
            elif event.key == pygame.K_F5:
                self._buy_house_item('furniture')
            elif event.key == pygame.K_F6:
                self._buy_anvil()

        elif self.state == GameState.GRANDMA_KITCHEN:
            if event.key in (pygame.K_TAB, pygame.K_ESCAPE):
                self.state = GameState.PLAYING
                pygame.event.set_grab(True)
                pygame.mouse.set_visible(False)
                play_sfx('menu')
            elif event.key == pygame.K_F1:
                self._grandma_cook(0)
            elif event.key == pygame.K_F2:
                self._grandma_cook(1)
            elif event.key == pygame.K_F3:
                self._grandma_cook(2)
            elif event.key == pygame.K_F4:
                self._grandma_cook(3)

        elif self.state == GameState.EVIL_GRANDMA:
            if event.key in (pygame.K_TAB, pygame.K_ESCAPE):
                self.state = GameState.PLAYING
                pygame.event.set_grab(True)
                pygame.mouse.set_visible(False)
                play_sfx('menu')
            elif event.key == pygame.K_F1:
                self._evil_grandma_drain('attack')
            elif event.key == pygame.K_F2:
                self._evil_grandma_drain('defense')
            elif event.key == pygame.K_F3:
                self._evil_grandma_drain('speed')
            elif event.key == pygame.K_F4:
                self._evil_grandma_drain('stamina')

        elif self.state == GameState.ANVIL_CRAFT:
            if event.key in (pygame.K_TAB, pygame.K_ESCAPE):
                self.state = GameState.HOUSE
                play_sfx('menu')
            elif event.key == pygame.K_F1:
                self._anvil_craft(0)
            elif event.key == pygame.K_F2:
                self._anvil_craft(1)
            elif event.key == pygame.K_F3:
                self._anvil_craft(2)
            elif event.key == pygame.K_F4:
                self._anvil_craft(3)
            elif event.key == pygame.K_F5:
                self._anvil_craft(4)

        elif self.state == GameState.HOUSE:
            if event.key in (pygame.K_TAB, pygame.K_ESCAPE):
                self.state = GameState.PLAYING
                pygame.event.set_grab(True)
                pygame.mouse.set_visible(False)
                play_sfx('menu')
            elif event.key == pygame.K_F1 and self.player.has_anvil:
                self.state = GameState.ANVIL_CRAFT
                play_sfx('menu')

        elif self.state == GameState.CUTSCENE:
            if event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                # Skip cutscene - teleport to sky island
                self._teleport_to_sky_island()
                play_sfx('menu')

        elif self.state == GameState.GAME_OVER:
            if event.key == pygame.K_r:
                self._respawn()
            elif event.key == pygame.K_ESCAPE:
                self.running = False

        elif self.state == GameState.VICTORY:
            if event.key == pygame.K_RETURN:
                self.state = GameState.PLAYING

    def _handle_mousedown(self, event):
        if self.state in (GameState.PLAYING, GameState.SHRINE, GameState.BOSS_FIGHT):
            in_shrine = self.state == GameState.SHRINE
            # Use castle mobs when in castle, otherwise world mobs
            if self.in_castle:
                mobs = self.castle_mobs
                bosses = [self.gardon_mok] if (self.gardon_mok and self.gardon_mok.alive and self.cutscene_phase == 'fight') else []
            else:
                mobs = self.world.mobs
                bosses = self.world.bosses
            if event.button == 1:  # Left click
                self.player.use_left_hand(
                    mobs, bosses, self.particles,
                    in_shrine, self.active_shrine
                )
            elif event.button == 3:  # Right click
                self.player.use_right_hand(
                    mobs, bosses, self.particles,
                    in_shrine, self.active_shrine
                )
            elif event.button == 2:  # Middle mouse - start looking
                self.camera.looking = True
                pygame.event.set_grab(True)
                pygame.mouse.set_visible(False)

    def _interact(self):
        """Handle E key interaction."""

        # Sky Island shrine interaction
        if self.on_sky_island:
            for shrine in self.sky_shrines:
                if not shrine.completed and dist2d(self.player.x, self.player.z, shrine.wx, shrine.wz) < INTERACT_RANGE:
                    # Enter the shrine as a playable level
                    self._sky_shrine_being_played = shrine
                    self._enter_shrine(shrine)
                    return
            # Sky Cookie Monster
            if dist2d(self.player.x, self.player.z, self.sky_cookie_monster_x, self.sky_cookie_monster_z) < INTERACT_RANGE:
                self.state = GameState.COOKIE_SHOP
                play_sfx('shrine_enter')
                return
            # Rauru stone - descend to surface (center of sky island)
            sky_cx = 100 * TILE_SIZE
            sky_cz = 100 * TILE_SIZE
            if dist2d(self.player.x, self.player.z, sky_cx, sky_cz) < INTERACT_RANGE:
                if self.sky_island_shrines_done >= 4:
                    self.on_sky_island = False
                    self.player.x = sky_cx
                    self.player.z = sky_cz
                    wy = walkable_y(self.player.x, self.player.z, self.world.seed)
                    self.player.y = (wy if wy is not None else 0) + 0.5
                    self.player.vy = 0
                    self.player.has_tablet = True
                    play_sfx('shrine_complete')
                    self.hud.add_notification("You descend from the Great Sky Island to Hyrule!")
                    self.hud.add_notification("You received the Purah Pad! Press [I] for inventory.")
                else:
                    remaining = 4 - self.sky_island_shrines_done
                    self.hud.add_notification(f"Complete {remaining} more shrine(s) before descending!")
                return
            return

        # Check for nearby shrines
        for shrine in self.world.shrines:
            if not shrine.completed and dist2d(self.player.x, self.player.z, shrine.wx, shrine.wz) < INTERACT_RANGE:
                self._enter_shrine(shrine)
                return

        # Check for Cookie Monster NPC
        cm = self.world.cookie_monster
        if cm and dist2d(self.player.x, self.player.z, cm.x, cm.z) < INTERACT_RANGE:
            self.state = GameState.COOKIE_SHOP
            play_sfx('shrine_enter')
            return

        # Check for Grandma NPC
        gm = self.world.grandma
        if gm and dist2d(self.player.x, self.player.z, gm.x, gm.z) < INTERACT_RANGE:
            self.state = GameState.GRANDMA_KITCHEN
            play_sfx('shrine_enter')
            return

        # Check for Evil Grandma NPC
        eg = self.world.evil_grandma
        if eg and dist2d(self.player.x, self.player.z, eg.x, eg.z) < INTERACT_RANGE:
            self.state = GameState.EVIL_GRANDMA
            play_sfx('shrine_enter')
            return

        # Check for House interaction
        hx, hz = HOUSE_POS[0] * TILE_SIZE, HOUSE_POS[1] * TILE_SIZE
        if self.player.has_house and dist2d(self.player.x, self.player.z, hx, hz) < INTERACT_RANGE:
            self.state = GameState.HOUSE
            play_sfx('shrine_enter')
            return

    def _enter_shrine(self, shrine):
        """Enter a shrine."""
        self.active_shrine = shrine
        shrine.active = True
        shrine.generate_interior()
        # Save player world position
        self.shrine_player_x = self.player.x
        self.shrine_player_z = self.player.z
        # Move player to shrine interior
        self.player.x = 0
        self.player.y = 0
        self.player.z = 8
        self.player.vy = 0
        self.state = GameState.SHRINE
        play_sfx('shrine_enter')
        self.hud.add_notification(f"Entered: {shrine.shrine_type.value}")

    def _exit_shrine(self):
        """Exit current shrine."""
        if self.active_shrine:
            self.active_shrine.active = False
            self.player.x = self.shrine_player_x
            self.player.z = self.shrine_player_z
            if self.on_sky_island:
                self.player.y = 78.5
            else:
                wy = walkable_y(self.player.x, self.player.z, self.world.seed)
                self.player.y = wy if wy is not None else 0
            self.active_shrine = None
            self.state = GameState.PLAYING

    def _update_castle_intro(self):
        """Update castle intro sequence: mobs, princess, Gardon Mok trigger."""
        p = self.player

        # Princess follows player at a distance
        if self.princess_alive:
            dx = p.x - self.princess_x
            dz = p.z - self.princess_z
            pdist = math.sqrt(dx*dx + dz*dz)
            if pdist > 2.5:
                nx, nz = dx / pdist, dz / pdist
                self.princess_x += nx * 2.5 * self.dt
                self.princess_z += nz * 2.5 * self.dt

        # Update castle Linus mobs
        for mob in self.castle_mobs:
            if mob.alive:
                mob.update(self.dt, p.x, p.y, p.z)
                mob.y = 0  # Castle floor is at y=0
                # Keep mobs inside castle bounds
                mob.x = max(-9, min(9, mob.x))
                mob.z = max(-9, min(9, mob.z))
                if mob.can_attack() and dist2d(mob.x, mob.z, p.x, p.z) < ATTACK_RANGE * 1.5:
                    dmg = mob.do_attack()
                    p.take_damage(dmg)

        # Melee hits on castle mobs already handled by use_left_hand
        # but we need to pass castle mobs to combat - handled in _handle_mousedown

        # Trigger Gardon Mok when player approaches throne (z < -4)
        if not self.gardon_mok_triggered and p.z < -4.0:
            self.gardon_mok_triggered = True
            self.cutscene_phase = 'gardon_talk'
            self.gardon_talk_timer = 0.0
            self.gardon_talk_index = 0
            self.hud.add_notification("Something stirs beneath the throne...")
            play_sfx('boss_roar')
            # Spawn Gardon Mok at throne
            self.gardon_mok = Mob(MobType.LINUS, 0, 0, -6)  # Use Linus as base, override
            self.gardon_mok.hp = 500
            self.gardon_mok.max_hp = 500
            self.gardon_mok.damage = 30
            self.gardon_mok.speed = 3.5
            self.gardon_mok.size = 1.8
            self.gardon_mok.color = (50, 20, 30)
            self.gardon_mok.aggro_range = 20.0
            self.gardon_mok.xp = 0

        # Gardon Mok talk phase
        if self.cutscene_phase == 'gardon_talk':
            self.gardon_talk_timer += self.dt
            if self.gardon_talk_timer > 2.5:
                self.gardon_talk_timer = 0.0
                if self.gardon_talk_index < len(self.gardon_talk_lines):
                    self.hud.add_notification(self.gardon_talk_lines[self.gardon_talk_index])
                    self.gardon_talk_index += 1
                else:
                    # Done talking, start fight
                    self.cutscene_phase = 'fight'
                    self.hud.add_notification("GARDON MOK attacks!")
                    play_sfx('boss_roar')

        # Gardon Mok fight phase
        if self.cutscene_phase == 'fight' and self.gardon_mok and self.gardon_mok.alive:
            gm = self.gardon_mok
            gm.update(self.dt, p.x, p.y, p.z)
            gm.y = 0  # Castle floor
            gm.x = max(-9, min(9, gm.x))
            gm.z = max(-9, min(9, gm.z))
            # Gardon Mok doesn't damage player during fight - cinematic moment
            # Player is meant to hit him once to trigger the cutscene

            # If player hit Gardon Mok at all, trigger the full cutscene
            if gm.hp < gm.max_hp:
                self.sword_broken = True
                self._break_sword()
                self.cutscene_phase = 'sword_break'
                self._trigger_castle_cutscene()

        # Keep player inside castle during intro
        if self.in_castle and not self.cutscene_done:
            p.x = max(-9, min(9, p.x))
            p.z = max(-9, min(9, p.z))
            p.y = max(0, min(5, p.y))

    def _break_sword(self):
        """Decay the sword - replace with Broken Sword (1 damage)."""
        p = self.player
        # Replace SWORD with BROKEN_SWORD in available weapons
        if WeaponType.SWORD in p.available_weapons:
            idx = p.available_weapons.index(WeaponType.SWORD)
            p.available_weapons[idx] = WeaponType.BROKEN_SWORD
        # Update loadouts
        if p.loadout1.left == WeaponType.SWORD:
            p.loadout1.left = WeaponType.BROKEN_SWORD
        if p.loadout2.left == WeaponType.SWORD:
            p.loadout2.left = WeaponType.BROKEN_SWORD
        self.hud.add_notification("Your sword DECAYS from dark power!")
        self.hud.add_notification("The Decayed Blade deals only 1 damage!")
        self.particles.emit(p.x, p.y + 1, p.z, 20, (255, 80, 30), spread=2, speed=5)
        play_sfx('hurt')

    def _trigger_castle_cutscene(self):
        """Trigger the TotK-style cutscene: Gardon rises, princess falls, sky teleport."""
        self.cutscene_done = True
        self.state = GameState.CUTSCENE
        self.cutscene_timer = 0.0
        self.princess_alive = False  # Princess falls into the chasm
        # Strip abilities - player starts fresh on Sky Island
        self.player.abilities = []
        self.player.selected_ability = 0
        self.camera.dist = CAM_DIST_DEFAULT  # Restore normal camera
        pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)

    def _teleport_to_sky_island(self):
        """Teleport player to the Sky Island above the clouds."""
        self.state = GameState.PLAYING
        self.in_castle = False
        self.on_sky_island = True
        self.camera.dist = CAM_DIST_DEFAULT
        # Sky island position: high up, center of map area
        self.player.x = 100 * TILE_SIZE
        self.player.y = 80.0  # Way above the clouds
        self.player.z = 100 * TILE_SIZE
        self.player.vy = 0
        self.player.hp = self.player.max_hp
        self.player.invincible_timer = 5.0
        self.hud.add_notification("You awaken on the Great Sky Island...")
        self.hud.add_notification("A voice speaks: Visit the shrines to restore your power.")
        self.hud.add_notification("Press E near shrines to enter them.")
        play_sfx('shrine_complete')
        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)

    def _complete_shrine(self):
        """Complete the active shrine. Awards cookies!"""
        if self.active_shrine and not self.active_shrine.completed:
            self.active_shrine.completed = True
            self.player.crown_shards += 1
            self.player.cookies += 1
            play_sfx('shrine_complete')
            self.hud.add_notification(f"Cookie obtained! ({self.player.cookies} total)")

            # Check if this is a sky shrine - award the specific ability
            if hasattr(self.active_shrine, '_sky_ability'):
                ability = self.active_shrine._sky_ability
                if ability not in self.player.abilities:
                    self.player.abilities.append(ability)
                self.sky_island_shrines_done += 1
                self.hud.add_notification(f"{self.active_shrine._sky_name} complete! Gained {ability.value}!")
                if self.sky_island_shrines_done >= 4:
                    self.hud.add_notification("All shrines complete! You may descend to the surface.")
            else:
                self.hud.add_notification("Visit Cookie Monster (West) to trade cookies for stats!")
                # Unlock abilities based on shrine count (overworld shrines)
                if self.player.crown_shards == 2 and AbilityType.FUSE not in self.player.abilities:
                    self.player.abilities.append(AbilityType.FUSE)
                    self.hud.add_notification("Ability unlocked: Fuse!")
                elif self.player.crown_shards == 4 and AbilityType.ASCEND not in self.player.abilities:
                    self.player.abilities.append(AbilityType.ASCEND)
                    self.hud.add_notification("Ability unlocked: Ascend!")
                elif self.player.crown_shards == 8 and AbilityType.RECALL not in self.player.abilities:
                    self.player.abilities.append(AbilityType.RECALL)
                    self.hud.add_notification("Ability unlocked: Recall!")

            self._exit_shrine()

    def _upgrade_stat(self, stat_name):
        """Spend cookies to upgrade a stat. Cost = next_level (1,2,3). Max level 3."""
        p = self.player
        current = p.stat_levels[stat_name]
        if current >= p.max_stat_level:
            self.hud.add_notification(f"{stat_name.title()} is already MAX level!")
            return
        cost = current + 1  # Level 0->1 costs 1, 1->2 costs 2, 2->3 costs 3
        if p.cookies < cost:
            self.hud.add_notification(f"Need {cost} cookies! (have {p.cookies})")
            return
        p.cookies -= cost
        p.stat_levels[stat_name] = current + 1
        play_sfx('shrine_complete')
        # Apply stat bonuses
        if stat_name == 'attack':
            self.hud.add_notification(f"Attack upgraded to Lv.{current+1}! (+5 damage)")
        elif stat_name == 'defense':
            p.max_hp += 20
            p.hp = min(p.hp + 20, p.max_hp)
            self.hud.add_notification(f"Defense upgraded to Lv.{current+1}! (+20 max HP)")
        elif stat_name == 'speed':
            self.hud.add_notification(f"Speed upgraded to Lv.{current+1}! (+1 move speed)")
        elif stat_name == 'stamina':
            p.max_stamina += 25
            p.stamina = p.max_stamina
            self.hud.add_notification(f"Stamina upgraded to Lv.{current+1}! (+25 max stamina)")

    def _grandma_cook(self, recipe_index):
        """Cook a recipe at Grandma's kitchen for 3 cookies."""
        if recipe_index >= len(GRANDMA_RECIPES):
            return
        recipe = GRANDMA_RECIPES[recipe_index]
        p = self.player
        if p.cookies < 3:
            self.hud.add_notification(f"Need 3 cookies! (have {p.cookies})")
            return
        p.cookies -= 3
        play_sfx('shrine_complete')
        name = recipe['name']
        if recipe['effect'] == 'heal':
            p.hp = min(p.hp + recipe['value'], p.max_hp)
            self.hud.add_notification(f"Grandma made {name}! Healed {recipe['value']} HP!")
        elif recipe['effect'] == 'attack_boost':
            p.invincible_timer = max(p.invincible_timer, recipe['value'])
            self.hud.add_notification(f"Grandma made {name}! Power boost for {recipe['value']}s!")
        elif recipe['effect'] == 'speed_boost':
            p.stamina = p.max_stamina
            self.hud.add_notification(f"Grandma made {name}! Stamina fully restored!")
        elif recipe['effect'] == 'shield':
            p.hp = min(p.hp + recipe['value'], p.max_hp)
            p.invincible_timer = max(p.invincible_timer, 3.0)
            self.hud.add_notification(f"Grandma made {name}! Shield + {recipe['value']} HP!")

    def _evil_grandma_drain(self, stat_name):
        """Evil Grandma takes back a stat level, refunding cookies."""
        p = self.player
        current = p.stat_levels[stat_name]
        if current <= 0:
            self.hud.add_notification(f"{stat_name.title()} already at base level! Nothing to take!")
            return
        refund = current  # Refunds same cost as upgrade
        p.stat_levels[stat_name] = current - 1
        p.cookies += refund
        play_sfx('hit')
        # Reverse stat bonuses
        if stat_name == 'defense':
            p.max_hp = max(100, p.max_hp - 20)
            p.hp = min(p.hp, p.max_hp)
        elif stat_name == 'stamina':
            p.max_stamina = max(100, p.max_stamina - 25)
            p.stamina = min(p.stamina, p.max_stamina)
        self.hud.add_notification(f"Evil Grandma drained {stat_name.title()}! Got {refund} cookies back...")

    def _buy_house_item(self, item_type):
        """Buy a house furniture item from Cookie Shop."""
        p = self.player
        if not p.has_house:
            cost = HOUSE_COST
            if p.rupees < cost:
                self.hud.add_notification(f"Need {cost} rupees for a house! (have {p.rupees})")
                return
            p.rupees -= cost
            p.has_house = True
            play_sfx('shrine_complete')
            self.hud.add_notification("House purchased! Find it near the castle!")
            return
        self.hud.add_notification("You already own a house!")

    def _buy_anvil(self):
        """Buy an anvil from Cookie Shop for the house."""
        p = self.player
        if not p.has_house:
            self.hud.add_notification("You need a house first!")
            return
        if p.has_anvil:
            self.hud.add_notification("You already have an anvil!")
            return
        cost = 30
        if p.rupees < cost:
            self.hud.add_notification(f"Need {cost} rupees for anvil! (have {p.rupees})")
            return
        p.rupees -= cost
        p.has_anvil = True
        play_sfx('shrine_complete')
        self.hud.add_notification("Anvil purchased! Use it in your house!")

    def _anvil_craft(self, recipe_index):
        """Craft a weapon at the anvil using rupees."""
        if recipe_index >= len(ANVIL_RECIPES):
            return
        recipe = ANVIL_RECIPES[recipe_index]
        p = self.player
        if p.rupees < recipe['cost']:
            self.hud.add_notification(f"Need {recipe['cost']} rupees! (have {p.rupees})")
            return
        wtype = recipe['weapon']
        if wtype in p.available_weapons:
            self.hud.add_notification(f"You already have {WEAPON_DATA[wtype]['name']}!")
            return
        p.rupees -= recipe['cost']
        p.available_weapons.append(wtype)
        play_sfx('shrine_complete')
        self.hud.add_notification(f"Forged {WEAPON_DATA[wtype]['name']}!")

    def _use_ability(self):
        """Activate the currently selected ability with F key."""
        if not self.player.abilities:
            self.hud.add_notification("No abilities unlocked!")
            return
        ability = self.player.abilities[self.player.selected_ability]
        p = self.player

        if ability == AbilityType.ULTRAHAND:
            # Ultrahand: grab and move blocks/push enemies
            if self.state == GameState.SHRINE and self.active_shrine:
                best_bl = None
                best_d = 999
                for bl in self.active_shrine.blocks:
                    d = dist2d(p.x, p.z, bl['x'], bl['z'])
                    if d < best_d:
                        best_d = d
                        best_bl = bl
                if best_bl and best_d < 10:
                    dx, dz = normalize2d(p.x - best_bl['x'], p.z - best_bl['z'])
                    best_bl['x'] += dx * 2
                    best_bl['z'] += dz * 2
                    best_bl['x'] = max(-10, min(10, best_bl['x']))
                    best_bl['z'] = max(-10, min(10, best_bl['z']))
                    play_sfx('hit')
                    self.hud.add_notification("Ultrahand!")
                else:
                    self.hud.add_notification("No block in range!")
            else:
                targets = self.world.mobs + self.world.bosses
                best_e = None
                best_d = 999
                for e in targets:
                    if not e.alive:
                        continue
                    d = dist2d(p.x, p.z, e.x, e.z)
                    if d < best_d and d < 12:
                        best_d = d
                        best_e = e
                if best_e:
                    dx, dz = normalize2d(best_e.x - p.x, best_e.z - p.z)
                    best_e.x += dx * 5
                    best_e.z += dz * 5
                    self.particles.emit(best_e.x, best_e.y + 1, best_e.z, 8, (100, 180, 255), spread=1, speed=3)
                    play_sfx('hit')
                    self.hud.add_notification("Ultrahand!")
                else:
                    self.hud.add_notification("No target in range!")

        elif ability == AbilityType.FUSE:
            # Fuse: fuse nearby Lesses to make them shoot fire, or weapon boost
            fused_lesse = False
            # Check for nearby Lesse mobs to fuse
            all_mobs = []
            if self.state == GameState.SHRINE and self.active_shrine:
                all_mobs = self.active_shrine.enemies
            else:
                all_mobs = self.world.mobs
            for mob in all_mobs:
                if mob.alive and mob.mob_type == MobType.LESSE and not getattr(mob, 'fused', False):
                    d = dist2d(p.x, p.z, mob.x, mob.z)
                    if d < 5.0:
                        mob.fused = True
                        mob.fuse_timer = 30.0  # Fire lasts 30 seconds
                        mob.fire_cooldown = 0.0
                        self.particles.emit(mob.x, mob.y + 1, mob.z, 20, (255, 100, 30), spread=2, speed=5)
                        play_sfx('shrine_complete')
                        self.hud.add_notification("Fused Lesse! It's shooting fire now!")
                        fused_lesse = True
                        break
            if not fused_lesse:
                # No Lesse nearby - regular weapon boost
                rad = math.radians(p.facing)
                fx = p.x - math.sin(rad) * 3
                fz = p.z - math.cos(rad) * 3
                p.invincible_timer = max(p.invincible_timer, 5.0)
                self.particles.emit(fx, p.y + 1, fz, 15, (255, 150, 50), spread=1.5, speed=4)
                self.particles.emit(p.x, p.y + 1, p.z, 10, (255, 200, 50), spread=1, speed=3)
                play_sfx('shrine_complete')
                self.hud.add_notification("Fuse! Weapon powered up for 5 seconds!")

        elif ability == AbilityType.ASCEND:
            # Ascend: launch upward through ceilings
            p.vy = JUMP_VEL * 2.5
            p.on_ground = False
            self.particles.emit(p.x, p.y, p.z, 12, (180, 255, 180), spread=1, speed=5)
            play_sfx('jump')
            self.hud.add_notification("Ascend!")

        elif ability == AbilityType.RECALL:
            # Recall: rewind time, heal to full and reset cooldowns
            p.hp = p.max_hp
            p.stamina = p.max_stamina
            p.left_cooldown = 0
            p.right_cooldown = 0
            self.particles.emit(p.x, p.y + 1, p.z, 20, (150, 100, 255), spread=2, speed=3)
            play_sfx('shrine_complete')
            self.hud.add_notification("Recall! Fully restored!")

    def _render_castle(self):
        """Render underground castle spawn room."""
        glClearColor(0.05, 0.04, 0.08, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.camera.apply(self.player)

        glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 1.0, 0.0, 0.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.15, 0.12, 0.18, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.5, 0.4, 0.3, 1.0])

        t = time.time()

        # Stone floor
        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        for x in range(-10, 11, 2):
            for z in range(-10, 11, 2):
                checker = ((x + z) // 2) % 2
                if checker:
                    glColor3f(0.2, 0.18, 0.22)
                else:
                    glColor3f(0.25, 0.22, 0.26)
                glVertex3f(x - 1, 0, z - 1)
                glVertex3f(x + 1, 0, z - 1)
                glVertex3f(x + 1, 0, z + 1)
                glVertex3f(x - 1, 0, z + 1)
        glEnd()

        # Ceiling
        glBegin(GL_QUADS)
        glColor3f(0.1, 0.08, 0.12)
        glNormal3f(0, -1, 0)
        glVertex3f(-10, 6, -10)
        glVertex3f(10, 6, -10)
        glVertex3f(10, 6, 10)
        glVertex3f(-10, 6, 10)
        glEnd()

        # Stone walls
        wall_c = (60, 55, 70)
        for x in range(-10, 11, 2):
            draw_cube(x, 3, -10, 1, 3, 0.5, wall_c)
            draw_cube(-10, 3, x, 0.5, 3, 1, wall_c)
            draw_cube(10, 3, x, 0.5, 3, 1, wall_c)
        # Back wall (sealed, no exit)
        for x in range(-10, 11, 2):
            draw_cube(x, 3, 10, 1, 3, 0.5, wall_c)

        # Pillars
        for px, pz in [(-6, -6), (6, -6), (-6, 6), (6, 6)]:
            draw_cylinder(px, 0, pz, 0.5, 6, (80, 75, 90))
            draw_cube(px, 6, pz, 0.7, 0.2, 0.7, (90, 85, 100))

        # Throne at center-back
        draw_cube(0, 0.75, -6, 1.5, 0.75, 1, (100, 80, 60))
        draw_cube(0, 2.5, -7, 1.5, 1.0, 0.3, (100, 80, 60))
        draw_cube(-1.5, 1.5, -6.5, 0.2, 0.8, 0.5, (100, 80, 60))
        draw_cube(1.5, 1.5, -6.5, 0.2, 0.8, 0.5, (100, 80, 60))

        # Weapon rack with "Sword of He Not Da Man" on throne
        draw_cube(0, 1.8, -5.8, 0.05, 0.6, 0.05, C_SWORD_SILVER)
        draw_cube(0, 2.5, -5.8, 0.1, 0.1, 0.1, (200, 170, 50))

        # Torches on walls
        for tx, tz in [(-8, -5), (8, -5), (-8, 5), (8, 5)]:
            draw_cylinder(tx, 2.5, tz, 0.1, 1, (100, 80, 40))
            flicker = 0.8 + 0.2 * math.sin(t * 8 + tx)
            draw_sphere(tx, 3.7, tz, 0.25, (int(255 * flicker), int(180 * flicker), 40))

        # Banner on back wall
        draw_cube(-7, 3.5, -9.5, 0.8, 1.5, 0.05, (120, 30, 30))
        draw_cube(7, 3.5, -9.5, 0.8, 1.5, 0.05, (30, 30, 120))

        # Chains on back wall (no escape)
        for cx in [-3, 3]:
            for cy in range(1, 5):
                draw_sphere(cx, cy, 9.5, 0.08, (90, 85, 80))

        # Draw Princess NPC
        if self.princess_alive:
            glPushMatrix()
            glTranslatef(self.princess_x, 0, self.princess_z)
            # Dress (pink)
            draw_cube(0, 0.8, 0, 0.3, 0.5, 0.25, (255, 180, 200))
            # Head
            draw_sphere(0, 1.5, 0, 0.25, (255, 220, 200))
            # Hair (golden)
            draw_cube(0, 1.7, -0.1, 0.2, 0.15, 0.2, (255, 220, 100))
            # Crown
            draw_cube(0, 1.85, 0, 0.15, 0.1, 0.15, (255, 200, 50))
            glPopMatrix()

        # Draw castle mobs (Linus guards)
        for mob in self.castle_mobs:
            if mob.alive:
                mob.draw()

        # Draw Gardon Mok
        if self.gardon_mok_triggered and self.gardon_mok and self.gardon_mok.alive:
            self.gardon_mok.draw()
            # Draw gloom aura around Gardon Mok
            gloom_pulse = 0.5 + 0.5 * math.sin(t * 4)
            draw_sphere(self.gardon_mok.x, 1.0, self.gardon_mok.z,
                       1.5 + gloom_pulse * 0.5, (50, 20, 60))

        self.player.draw()
        self.particles.draw()

        # Reset lighting
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.35, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.9, 0.85, 0.8, 1.0])
        glClearColor(*C_SKY, 1.0)

        self.hud.draw_game_hud(self.player, self.camera, self.state, self.world)

        # Draw Gardon Mok dialogue during talk phase
        if self.cutscene_phase == 'gardon_talk':
            line_idx = min(self.gardon_talk_index, len(self.gardon_talk_lines) - 1)
            self.hud.draw_dialogue("Gardon Mok", self.gardon_talk_lines[line_idx])

    def _render_sky_island(self):
        """Render the Great Sky Island floating above clouds."""
        glClearColor(0.55, 0.78, 1.0, 1.0)  # Bright ethereal sky
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # Enable fog for sky feel
        glEnable(GL_FOG)
        glFogfv(GL_FOG_COLOR, [0.55, 0.78, 1.0, 1.0])
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogf(GL_FOG_START, 80.0)
        glFogf(GL_FOG_END, 250.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.camera.apply(self.player)

        glLightfv(GL_LIGHT0, GL_POSITION, [0.5, 1.0, 0.3, 0.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.4, 0.4, 0.5, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 0.95, 0.9, 1.0])

        t = time.time()
        sky_cx = 100 * TILE_SIZE
        sky_cz = 100 * TILE_SIZE

        # Floating island platform (stone slab)
        # Main platform (big island)
        draw_cube(sky_cx, 77.0, sky_cz, 60, 1.5, 60, (100, 130, 90))
        # Grass top
        draw_cube(sky_cx, 78.6, sky_cz, 60, 0.1, 60, (80, 160, 60))
        # Rocky underside details
        for i in range(12):
            angle = i * 30
            rx = sky_cx + math.cos(math.radians(angle)) * 45
            rz = sky_cz + math.sin(math.radians(angle)) * 45
            draw_cube(rx, 74.5, rz, 5, 3, 5, (90, 85, 75))
        # Extra rock formations underneath
        for i in range(8):
            angle = i * 45 + 15
            rx = sky_cx + math.cos(math.radians(angle)) * 30
            rz = sky_cz + math.sin(math.radians(angle)) * 30
            draw_cube(rx, 73.0, rz, 4, 4, 4, (80, 75, 65))

        # Cloud layer below (decorative - lots of clouds for sky feel)
        for i in range(30):
            cx = sky_cx + math.cos(math.radians(i * 12 + t * 3)) * (60 + i * 3)
            cz = sky_cz + math.sin(math.radians(i * 12 + t * 2)) * (60 + i * 3)
            cy = 60 + math.sin(t * 0.5 + i) * 3
            cloud_sz = 5 + math.sin(i * 1.3) * 3
            draw_sphere(cx, cy, cz, cloud_sz, (240, 240, 250))
        # Second cloud layer (lower, distant)
        for i in range(20):
            cx = sky_cx + math.cos(math.radians(i * 18 + t * 1.5 + 90)) * (100 + i * 5)
            cz = sky_cz + math.sin(math.radians(i * 18 + t * 1.0 + 90)) * (100 + i * 5)
            cy = 45 + math.sin(t * 0.3 + i * 0.5) * 4
            cloud_sz = 8 + math.sin(i * 0.9) * 4
            draw_sphere(cx, cy, cz, cloud_sz, (220, 225, 240))
        # Wispy high clouds above
        for i in range(10):
            cx = sky_cx + math.cos(math.radians(i * 36 + t * 0.8)) * (50 + i * 8)
            cz = sky_cz + math.sin(math.radians(i * 36 + t * 0.6)) * (50 + i * 8)
            cy = 100 + math.sin(t * 0.2 + i) * 5
            draw_sphere(cx, cy, cz, 6 + i * 0.5, (200, 210, 240))

        # Draw sky shrines (bigger, more visible)
        for shrine in self.sky_shrines:
            sx, sz = shrine.wx, shrine.wz
            if shrine.completed:
                # Completed shrine (dimmed)
                draw_cube(sx, 79.5, sz, 3, 3, 3, (60, 80, 60))
                draw_sphere(sx, 84, sz, 1.0, (100, 150, 100))
            else:
                # Active shrine (glowing, large)
                glow = 0.5 + 0.5 * math.sin(t * 3)
                shrine_color = (int(80 + glow * 60), int(150 + glow * 50), int(200 + glow * 55))
                draw_cube(sx, 79.5, sz, 3, 3, 3, shrine_color)
                draw_sphere(sx, 84.0 + math.sin(t * 2) * 0.5, sz, 1.2, (150, 220, 255))
                # Pillar accents (larger)
                draw_cube(sx - 3.5, 80, sz - 3.5, 0.4, 4, 0.4, (120, 160, 200))
                draw_cube(sx + 3.5, 80, sz - 3.5, 0.4, 4, 0.4, (120, 160, 200))
                draw_cube(sx - 3.5, 80, sz + 3.5, 0.4, 4, 0.4, (120, 160, 200))
                draw_cube(sx + 3.5, 80, sz + 3.5, 0.4, 4, 0.4, (120, 160, 200))

        # Cookie Monster NPC on sky island
        cmx, cmz = self.sky_cookie_monster_x, self.sky_cookie_monster_z
        draw_sphere(cmx, 79.8, cmz, 0.8, (50, 100, 200))  # Body
        draw_sphere(cmx, 80.8, cmz, 0.5, (60, 120, 220))   # Head
        # Eyes
        draw_sphere(cmx - 0.2, 81.0, cmz + 0.4, 0.15, (255, 255, 255))
        draw_sphere(cmx + 0.2, 81.0, cmz + 0.4, 0.15, (255, 255, 255))
        draw_sphere(cmx - 0.2, 81.0, cmz + 0.48, 0.08, (0, 0, 0))
        draw_sphere(cmx + 0.2, 81.0, cmz + 0.48, 0.08, (0, 0, 0))

        # Decorative trees on island (spread across bigger island)
        tree_positions = [
            (sky_cx + 15, sky_cz + 12), (sky_cx - 18, sky_cz - 8),
            (sky_cx + 8, sky_cz - 20), (sky_cx - 12, sky_cz + 18),
            (sky_cx + 30, sky_cz + 15), (sky_cx - 25, sky_cz - 20),
            (sky_cx + 20, sky_cz - 30), (sky_cx - 30, sky_cz + 10),
            (sky_cx + 35, sky_cz - 10), (sky_cx - 10, sky_cz + 35),
        ]
        for i, (tx, tz) in enumerate(tree_positions):
            draw_cylinder(tx, 78.5, tz, 0.4, 4, (100, 70, 40))
            draw_sphere(tx, 83.5, tz, 2.5, (40, 130 + (i * 7) % 40, 50))

        # Central Rauru stone
        draw_cube(sky_cx, 79.5, sky_cz, 1, 1, 1, (180, 170, 150))
        draw_cube(sky_cx, 81, sky_cz, 0.6, 0.5, 0.6, (200, 190, 160))
        # Arm symbol on top
        glow2 = 0.5 + 0.5 * math.sin(t * 2)
        draw_sphere(sky_cx, 81.8, sky_cz, 0.35, (int(100 + glow2 * 100), int(200 + glow2 * 55), int(100 + glow2 * 100)))

        self.player.draw()
        self.particles.draw()

        # Reset lighting
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.35, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.9, 0.85, 0.8, 1.0])
        glClearColor(*C_SKY, 1.0)

        self.hud.draw_game_hud(self.player, self.camera, self.state, self.world)

    def _respawn(self):
        """Respawn player after death."""
        self.player.hp = self.player.max_hp
        self.player.stamina = self.player.max_stamina
        self.player.alive = True
        self.player.x = 100 * TILE_SIZE
        self.player.y = 5.0
        self.player.z = 100 * TILE_SIZE
        self.player.vy = 0
        self.player.invincible_timer = 5.0  # 5 seconds spawn protection
        self.state = GameState.PLAYING
        self.hud.add_notification("Respawned with 5s protection!")
        # Clear nearby mobs from spawn
        spawn_safe = 25 * TILE_SIZE
        for mob in self.world.mobs:
            if mob.alive and dist2d(mob.x, mob.z, self.player.x, self.player.z) < spawn_safe:
                mob.patrol_cx = mob.x + random.choice([-1, 1]) * spawn_safe
                mob.patrol_cz = mob.z + random.choice([-1, 1]) * spawn_safe
                mob.x = mob.patrol_cx
                mob.z = mob.patrol_cz

    def _update(self):
        """Update game logic."""
        if self.state in (GameState.PLAYING, GameState.BOSS_FIGHT):
            self._update_movement()
            self.player.update(self.dt, self.world.seed if not self.in_castle else 42)

            # Castle: force player to castle floor (terrain height is wrong here)
            if self.in_castle:
                self.player.y = 0
                self.player.vy = 0
                self.player.on_ground = True
                self.player.jump_count = 0

            # Sky island: clamp player to island platform
            elif self.on_sky_island:
                sky_cx = 100 * TILE_SIZE
                sky_cz = 100 * TILE_SIZE
                sky_r = 60.0
                # Keep player on the floating island
                dx = self.player.x - sky_cx
                dz = self.player.z - sky_cz
                d = math.sqrt(dx * dx + dz * dz)
                if d > sky_r:
                    self.player.x = sky_cx + dx / d * sky_r
                    self.player.z = sky_cz + dz / d * sky_r
                if self.player.y < 78.0:
                    self.player.y = 78.0
                    self.player.vy = 0
                    self.player.on_ground = True
                    self.player.jump_count = 0

            if not self.in_castle:
                self.world.update(self.dt, self.player)
            self.particles.update(self.dt)
            self.hud.update(self.dt)

            # Castle-specific logic
            if self.in_castle and not self.cutscene_done:
                self._update_castle_intro()

            # Check for death
            if not self.player.alive:
                self.state = GameState.GAME_OVER
                play_sfx('death')

            # Check if near a boss
            for boss in self.world.bosses:
                if boss.alive and dist2d(self.player.x, self.player.z, boss.x, boss.z) < boss.arena_radius:
                    if self.state != GameState.BOSS_FIGHT:
                        self.state = GameState.BOSS_FIGHT
                        self.hud.add_notification(f"BOSS: {boss.boss_type.value}!")
                        play_sfx('boss_roar')
                    break
            else:
                if self.state == GameState.BOSS_FIGHT:
                    self.state = GameState.PLAYING

            # Check boss defeat
            for boss in self.world.bosses:
                if not boss.alive and not boss.defeated:
                    boss.defeated = True
                    self.particles.emit_death(boss.x, boss.y + boss.size, boss.z, boss.color)
                    self.hud.add_notification(f"{boss.boss_type.value} DEFEATED!")
                    self.player.xp += boss.xp
                    if boss.boss_type == BossType.DARK_SOVEREIGN:
                        self.state = GameState.VICTORY

            # Shrine glow particles
            for shrine in self.world.shrines:
                if not shrine.completed and dist2d(shrine.wx, shrine.wz, self.player.x, self.player.z) < VIEW_DIST * 0.5:
                    if random.random() < 0.1:
                        self.particles.emit_shrine_glow(shrine.wx, shrine.get_world_y(self.world.seed), shrine.wz)

        elif self.state == GameState.SHRINE:
            self._update_movement_shrine()
            self.player.update(self.dt)
            self.particles.update(self.dt)
            self.hud.update(self.dt)

            # Update shrine enemies
            if self.active_shrine:
                for enemy in self.active_shrine.enemies:
                    if enemy.alive:
                        # Lesses don't attack the player
                        if enemy.mob_type == MobType.LESSE:
                            enemy.anim_time = getattr(enemy, 'anim_time', 0) + self.dt
                            # Fused Lesse shoots fire at non-Lesse enemies
                            if getattr(enemy, 'fused', False):
                                enemy.fuse_timer = getattr(enemy, 'fuse_timer', 0) - self.dt
                                enemy.fire_cooldown = getattr(enemy, 'fire_cooldown', 0) - self.dt
                                if enemy.fuse_timer <= 0:
                                    enemy.fused = False
                                elif enemy.fire_cooldown <= 0:
                                    # Find nearest non-Lesse enemy to shoot
                                    best_target = None
                                    best_d = 999
                                    for target in self.active_shrine.enemies:
                                        if target.alive and target.mob_type != MobType.LESSE:
                                            d = dist2d(enemy.x, enemy.z, target.x, target.z)
                                            if d < best_d and d < 15:
                                                best_d = d
                                                best_target = target
                                    if best_target:
                                        best_target.take_damage(8)
                                        self.particles.emit(best_target.x, best_target.y + 0.5, best_target.z, 6, (255, 100, 30), spread=0.5, speed=3)
                                        self.particles.emit(enemy.x, enemy.y + 1.2, enemy.z, 4, (255, 150, 50), spread=0.3, speed=4)
                                        if not best_target.alive:
                                            self.player.xp += best_target.xp
                                            self.particles.emit_death(best_target.x, best_target.y, best_target.z, best_target.color)
                                        enemy.fire_cooldown = 1.5  # Fire every 1.5s
                            else:
                                # Unfused Lesse wanders randomly
                                if random.random() < 0.02:
                                    enemy.x += random.uniform(-0.5, 0.5)
                                    enemy.z += random.uniform(-0.5, 0.5)
                                    enemy.x = max(-10, min(10, enemy.x))
                                    enemy.z = max(-10, min(10, enemy.z))
                            continue
                        enemy.update(self.dt, self.player.x, self.player.y, self.player.z)
                        if enemy.can_attack() and dist2d(enemy.x, enemy.z, self.player.x, self.player.z) < ATTACK_RANGE * 1.5:
                            dmg = enemy.do_attack()
                            self.player.take_damage(dmg)

                # Arrow collisions inside shrine (skip Lesses)
                for arrow in self.player.projectiles:
                    if not arrow.alive:
                        continue
                    for enemy in self.active_shrine.enemies:
                        if enemy.alive and enemy.mob_type != MobType.LESSE and dist3d(arrow.x, arrow.y, arrow.z, enemy.x, enemy.y + enemy.size * 0.5, enemy.z) < enemy.size:
                            enemy.take_damage(arrow.damage)
                            arrow.alive = False
                            if not enemy.alive:
                                self.player.xp += enemy.xp
                                self.particles.emit_death(enemy.x, enemy.y, enemy.z, enemy.color)
                            break

            if not self.player.alive:
                self.state = GameState.GAME_OVER
                play_sfx('death')

        elif self.state == GameState.CUTSCENE:
            self.cutscene_timer += self.dt
            self.hud.update(self.dt)
            if self.cutscene_timer >= 12.0:
                self._teleport_to_sky_island()

        else:
            self.hud.update(self.dt)

    def _update_movement(self):
        """Update player movement from keyboard input."""
        keys = pygame.key.get_pressed()
        fx, fz = self.camera.get_forward()
        rx, rz = self.camera.get_right()

        move_x, move_z = 0.0, 0.0
        if keys[pygame.K_w]:
            move_x += fx
            move_z += fz
        if keys[pygame.K_s]:
            move_x -= fx
            move_z -= fz
        if keys[pygame.K_a]:
            move_x -= rx
            move_z -= rz
        if keys[pygame.K_d]:
            move_x += rx
            move_z += rz

        length = math.sqrt(move_x * move_x + move_z * move_z)
        if length > 0.01:
            move_x /= length
            move_z /= length
            self.player.facing = math.degrees(math.atan2(-move_x, -move_z))

            speed = SPRINT_SPEED if self.player.sprinting else WALK_SPEED
            if self.player.sprinting:
                self.player.stamina -= 20 * self.dt
                if self.player.stamina <= 0:
                    self.player.sprinting = False
                    self.player.stamina = 0

            self.player.vx = move_x * speed
            self.player.vz = move_z * speed

        # Clamp to world bounds (skip when in castle or sky island - local coords)
        if not self.in_castle and not self.on_sky_island:
            margin = 5 * TILE_SIZE
            max_coord = (WORLD_SIZE - 5) * TILE_SIZE
            self.player.x = max(margin, min(max_coord, self.player.x))
            self.player.z = max(margin, min(max_coord, self.player.z))

    def _update_movement_shrine(self):
        """Movement inside a shrine (simpler, flat ground)."""
        keys = pygame.key.get_pressed()
        fx, fz = self.camera.get_forward()
        rx, rz = self.camera.get_right()

        move_x, move_z = 0.0, 0.0
        if keys[pygame.K_w]:
            move_x += fx; move_z += fz
        if keys[pygame.K_s]:
            move_x -= fx; move_z -= fz
        if keys[pygame.K_a]:
            move_x -= rx; move_z -= rz
        if keys[pygame.K_d]:
            move_x += rx; move_z += rz

        length = math.sqrt(move_x * move_x + move_z * move_z)
        if length > 0.01:
            move_x /= length; move_z /= length
            self.player.facing = math.degrees(math.atan2(-move_x, -move_z))
            self.player.vx = move_x * WALK_SPEED
            self.player.vz = move_z * WALK_SPEED

        # Clamp to shrine bounds
        self.player.x = max(-11, min(11, self.player.x))
        self.player.z = max(-11, min(11, self.player.z))

        # Push blocks
        if self.active_shrine:
            for bl in self.active_shrine.blocks:
                if dist2d(self.player.x, self.player.z, bl['x'], bl['z']) < 1.2:
                    dx, dz = normalize2d(bl['x'] - self.player.x, bl['z'] - self.player.z)
                    bl['x'] += dx * WALK_SPEED * self.dt * 0.5
                    bl['z'] += dz * WALK_SPEED * self.dt * 0.5
                    bl['x'] = max(-10, min(10, bl['x']))
                    bl['z'] = max(-10, min(10, bl['z']))

    def _render(self):
        """Render the current frame."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.state == GameState.TITLE:
            self._render_title_bg()
            self.hud.draw_title_screen()
            return

        if self.state == GameState.CUTSCENE:
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.hud.draw_cutscene(self.cutscene_timer)
            return

        if self.state == GameState.SHRINE:
            self._render_shrine()
            return

        if self.in_castle:
            self._render_castle()
            return

        if self.on_sky_island:
            self._render_sky_island()
            # Draw overlay UIs on top of sky island scene
            if self.state == GameState.COOKIE_SHOP:
                self.hud.draw_cookie_shop(self.player)
            elif self.state == GameState.INVENTORY:
                self.hud.draw_inventory(self.player)
            elif self.state == GameState.PAUSE:
                self.hud.draw_pause_screen()
            return

        # ── 3D World rendering ──
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.camera.apply(self.player)

        # Set light position (follows camera somewhat)
        glLightfv(GL_LIGHT0, GL_POSITION, [0.4, 1.0, 0.3, 0.0])

        # Draw terrain
        self.world.draw_terrain(self.player.x, self.player.z)
        self.world.draw_objects(self.player.x, self.player.z)
        self.world.draw_shrines(self.player.x, self.player.z)
        self.world.draw_mobs(self.player.x, self.player.z)
        self.world.draw_bosses(self.player.x, self.player.z)
        self.world.draw_cookie_monster(self.player.x, self.player.z)
        self.world.draw_npcs(self.player.x, self.player.z)
        self.world.draw_house(self.player.x, self.player.z)

        # Draw player
        self.player.draw()

        # Draw particles
        self.particles.draw()

        # ── HUD ──
        if self.state == GameState.PAUSE:
            self.hud.draw_game_hud(self.player, self.camera, self.state, self.world)
            self.hud.draw_pause_screen()
        elif self.state == GameState.INVENTORY:
            self.hud.draw_inventory(self.player)
        elif self.state == GameState.COOKIE_SHOP:
            self.hud.draw_cookie_shop(self.player)
        elif self.state == GameState.GRANDMA_KITCHEN:
            self.hud.draw_grandma_kitchen(self.player)
        elif self.state == GameState.EVIL_GRANDMA:
            self.hud.draw_evil_grandma(self.player)
        elif self.state == GameState.ANVIL_CRAFT:
            self.hud.draw_anvil_craft(self.player)
        elif self.state == GameState.HOUSE:
            self.hud.draw_house(self.player)
        elif self.state == GameState.CUTSCENE:
            self.hud.draw_cutscene(self.cutscene_timer)
        elif self.state == GameState.GAME_OVER:
            self.hud.draw_game_over()
        elif self.state == GameState.VICTORY:
            self.hud.draw_victory()
        else:
            self.hud.draw_game_hud(self.player, self.camera, self.state, self.world)

    def _render_shrine(self):
        """Render shrine interior."""
        glClearColor(0.15, 0.12, 0.2, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.camera.apply(self.player)

        glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 1.0, 0.0, 0.0])
        # Slightly dimmer ambient for shrine atmosphere
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.25, 0.25, 0.35, 1.0])

        if self.active_shrine:
            self.active_shrine.draw_interior()

        self.player.draw()
        self.particles.draw()

        # Reset ambient
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.35, 1.0])
        glClearColor(*C_SKY, 1.0)

        if self.active_shrine:
            self.hud.draw_shrine_hud(self.active_shrine, self.player)

    def _render_title_bg(self):
        """Render a simple background for the title screen."""
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0, 20, 30, 0, 0, 0, 0, 1, 0)

        t = time.time()
        # Rotating ground
        glPushMatrix()
        glRotatef(t * 5, 0, 1, 0)

        # Ground
        glBegin(GL_QUADS)
        glColor3f(0.2, 0.4, 0.15)
        glNormal3f(0, 1, 0)
        glVertex3f(-20, 0, -20)
        glVertex3f(20, 0, -20)
        glVertex3f(20, 0, 20)
        glVertex3f(-20, 0, 20)
        glEnd()

        # Some decorative structures
        draw_cube(0, 2, 0, 1.5, 2, 1.5, (120, 110, 100))
        draw_sphere(0, 5, 0, 0.8, (255, 220, 100))
        for i in range(4):
            angle = i * math.pi / 2 + t * 0.5
            x = math.cos(angle) * 8
            z = math.sin(angle) * 8
            draw_cube(x, 1, z, 0.5, 1, 0.5, (100, 160, 80))
            draw_sphere(x, 2.5, z, 0.6, (60, 130, 50))

        # Player figure on pedestal
        draw_cube(0, 5, 5, 0.25, 0.25, 0.15, C_TUNIC_GREEN)
        draw_sphere(0, 5.7, 5, 0.2, C_SKIN)

        glPopMatrix()


# ════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    try:
        game = Game()
        game.run()
    except Exception as e:
        pygame.quit()
        print(f"\n{'='*50}")
        print(f"ERROR: {e}")
        print(f"{'='*50}")
        import traceback
        traceback.print_exc()
        print("\nMake sure you have PyOpenGL installed:")
        print("  pip install PyOpenGL PyOpenGL_accelerate")
        sys.exit(1)
