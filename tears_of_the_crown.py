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

class AbilityType(Enum):
    TELEKINESIS = "Telekinesis"       # Ultrahand
    FORGE_BOND = "Forge Bond"         # Fuse
    PHASE_RISE = "Phase Rise"         # Ascend
    TIME_REWIND = "Time Rewind"       # Recall

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

class BossType(Enum):
    FROST_SERPENT = "Frost Serpent"
    SLUDGE_BEAST = "Sludge Beast"
    MAGMA_GOLEM = "Magma Golem"
    HIVE_MATRIARCH = "Hive Matriarch"
    CORRUPTED_AUTOMATON = "Corrupted Automaton"
    DARK_SOVEREIGN = "The Dark Sovereign"
    COOKIE_MONSTER = "Cookie Monster"

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
    (BossType.COOKIE_MONSTER, 60, 100),   # West - cookie cave
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
        self.goal_reached = False
        self.timer = 0.0

    def get_world_y(self, seed=42):
        wy = walkable_y(self.wx, self.wz, seed)
        return wy if wy is not None else 0.0

    def generate_interior(self):
        """Generate shrine puzzle content when entered."""
        self.enemies.clear()
        self.blocks.clear()
        self.switches.clear()
        self.goal_reached = False
        self.timer = 0.0

        if self.shrine_type == ShrineType.TRIAL_OF_MIGHT:
            # Combat trial - spawn waves of enemies
            for i in range(5):
                angle = i / 5 * math.pi * 2
                mob = Mob(random.choice([MobType.GRUNKLE, MobType.SKARVYN, MobType.CAVE_FIEND]),
                         math.cos(angle) * 8, 0, math.sin(angle) * 8)
                self.enemies.append(mob)
        elif self.shrine_type == ShrineType.ANCIENT_GIFT:
            self.goal_reached = True  # Free reward!
        else:
            # Generic puzzle - kill some enemies and reach goal area
            for i in range(3):
                angle = i / 3 * math.pi * 2
                mob = Mob(MobType.GRUNKLE,
                         math.cos(angle) * 6, 0, math.sin(angle) * 6)
                self.enemies.append(mob)
            # Blocks to push
            for i in range(2):
                self.blocks.append({
                    'x': random.uniform(-5, 5),
                    'z': random.uniform(-5, 5),
                    'on_switch': False
                })
            self.switches.append({'x': 0, 'z': -8, 'activated': False})

    def check_completion(self):
        if self.completed:
            return True
        if self.shrine_type == ShrineType.ANCIENT_GIFT:
            return True
        if self.shrine_type == ShrineType.TRIAL_OF_MIGHT:
            return all(not e.alive for e in self.enemies)
        # Generic: kill enemies and get blocks on switches
        enemies_dead = all(not e.alive for e in self.enemies)
        if enemies_dead and not self.switches:
            return True
        if enemies_dead:
            # Check if any block is near any switch
            for sw in self.switches:
                for bl in self.blocks:
                    if dist2d(bl['x'], bl['z'], sw['x'], sw['z']) < 1.5:
                        sw['activated'] = True
            return all(sw['activated'] for sw in self.switches)
        return False

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

    def draw_interior(self):
        """Draw shrine interior (when player is inside)."""
        # Floor
        glBegin(GL_QUADS)
        glColor3f(0.3, 0.35, 0.4)
        glNormal3f(0, 1, 0)
        for x in range(-12, 13, 2):
            for z in range(-12, 13, 2):
                checker = ((x + z) // 2) % 2
                if checker:
                    glColor3f(0.28, 0.32, 0.38)
                else:
                    glColor3f(0.35, 0.38, 0.42)
                glVertex3f(x - 1, 0, z - 1)
                glVertex3f(x + 1, 0, z - 1)
                glVertex3f(x + 1, 0, z + 1)
                glVertex3f(x - 1, 0, z + 1)
        glEnd()

        # Walls
        wall_color = (80, 90, 100)
        for x in range(-12, 13, 2):
            draw_cube(x, 2, -12, 1, 2, 0.3, wall_color)
            draw_cube(x, 2, 12, 1, 2, 0.3, wall_color)
            draw_cube(-12, 2, x, 0.3, 2, 1, wall_color)
            draw_cube(12, 2, x, 0.3, 2, 1, wall_color)

        # Goal marker
        if not self.goal_reached:
            draw_sphere(0, 1.5, -9, 0.5, (255, 220, 50))
            draw_cone(0, 0, -9, 0.8, 0.3, (200, 180, 40))
        else:
            draw_sphere(0, 1.5 + math.sin(time.time() * 3) * 0.3, -9, 0.6, (100, 255, 100))

        # Blocks
        for bl in self.blocks:
            draw_cube(bl['x'], 0.5, bl['z'], 0.5, 0.5, 0.5, (160, 140, 100))

        # Switches
        for sw in self.switches:
            c = (100, 255, 100) if sw['activated'] else (255, 100, 100)
            draw_cube(sw['x'], 0.05, sw['z'], 0.7, 0.05, 0.7, c)

        # Enemies
        for e in self.enemies:
            e.draw()


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
        # Stats: each level costs more cookies. Lvl1=1 cookie, Lvl2=2, Lvl3(max)=3
        self.stat_levels = {'attack': 0, 'defense': 0, 'speed': 0, 'stamina': 0}
        self.max_stat_level = 3

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
        self.abilities = [AbilityType.TELEKINESIS]
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
            'stat_levels': self.stat_levels,
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
        sl = data.get('stat_levels', {})
        for k in ('attack', 'defense', 'speed', 'stamina'):
            if k in sl:
                self.stat_levels[k] = sl[k]

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

        # Arrow collision with mobs/bosses
        for arrow in player.projectiles:
            if not arrow.alive:
                continue
            for mob in self.mobs:
                if mob.alive and dist3d(arrow.x, arrow.y, arrow.z, mob.x, mob.y + mob.size * 0.5, mob.z) < mob.size:
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

        # Cookie Stat Upgrades
        self._draw_text("═══ Stat Upgrades (press key) ═══", 500, 250, self.font_med, (210, 170, 80))
        stat_keys = {'attack': 'F1', 'defense': 'F2', 'speed': 'F3', 'stamina': 'F4'}
        for i, (stat, key) in enumerate(stat_keys.items()):
            lvl = player.stat_levels[stat]
            cost = lvl + 1 if lvl < player.max_stat_level else '-'
            bars = '█' * lvl + '░' * (player.max_stat_level - lvl)
            color = (100, 255, 100) if lvl == player.max_stat_level else (200, 200, 220)
            label = f"  {key}: {stat.title()} [{bars}] Lv.{lvl}"
            if lvl < player.max_stat_level:
                label += f" (cost: {cost} cookie{'s' if cost > 1 else ''})"
            else:
                label += " MAX"
            self._draw_text(label, 500, 280 + i * 28, self.font_small, color)

        # Abilities
        self._draw_text("═══ Abilities ═══", 500, 400, self.font_med, (180, 180, 200))
        for i, ability in enumerate(player.abilities):
            self._draw_text(f"  [{i+1}] {ability.value}", 500, 430 + i * 25, self.font_small, (200, 200, 220))

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
        self.player = Player(100 * TILE_SIZE, -5.0, 100 * TILE_SIZE)
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

        # Initialize sounds
        init_sounds()

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
                self.hud.add_notification("Welcome to the Underground Castle!")
                self.hud.add_notification("Press E near the exit to leave the castle.")
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
            elif event.key == pygame.K_TAB:
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

        elif self.state == GameState.SHRINE:
            if event.key == pygame.K_ESCAPE:
                self._exit_shrine()
            elif event.key == pygame.K_SPACE:
                self.player.jump()
            elif event.key == pygame.K_e:
                if self.active_shrine and self.active_shrine.check_completion():
                    self._complete_shrine()
            elif event.key == pygame.K_TAB:
                self.state = GameState.INVENTORY
                self.selected_weapon_index = -1

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
            if event.key == pygame.K_TAB or event.key == pygame.K_ESCAPE:
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
            # F1-F4: upgrade stats with cookies
            elif event.key == pygame.K_F1:
                self._upgrade_stat('attack')
            elif event.key == pygame.K_F2:
                self._upgrade_stat('defense')
            elif event.key == pygame.K_F3:
                self._upgrade_stat('speed')
            elif event.key == pygame.K_F4:
                self._upgrade_stat('stamina')

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
            if event.button == 1:  # Left click
                self.player.use_left_hand(
                    self.world.mobs, self.world.bosses, self.particles,
                    in_shrine, self.active_shrine
                )
            elif event.button == 3:  # Right click
                self.player.use_right_hand(
                    self.world.mobs, self.world.bosses, self.particles,
                    in_shrine, self.active_shrine
                )
            elif event.button == 2:  # Middle mouse - start looking
                self.camera.looking = True
                pygame.event.set_grab(True)
                pygame.mouse.set_visible(False)

    def _interact(self):
        """Handle E key interaction."""
        # Castle exit - near the door at z=8 in the underground castle
        if self.in_castle:
            if self.player.z > 6.0:
                self.in_castle = False
                self.player.x = 100 * TILE_SIZE
                wy = walkable_y(self.player.x, 100 * TILE_SIZE, self.world.seed)
                self.player.y = (wy if wy is not None else 0) + 0.5
                self.player.z = 100 * TILE_SIZE
                self.hud.add_notification("You emerge from the underground castle!")
                play_sfx('shrine_complete')
                return

        # Check for nearby shrines
        for shrine in self.world.shrines:
            if not shrine.completed and dist2d(self.player.x, self.player.z, shrine.wx, shrine.wz) < INTERACT_RANGE:
                self._enter_shrine(shrine)
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
            wy = walkable_y(self.player.x, self.player.z, self.world.seed)
            self.player.y = wy if wy is not None else 0
            self.active_shrine = None
            self.state = GameState.PLAYING

    def _complete_shrine(self):
        """Complete the active shrine. Awards cookies!"""
        if self.active_shrine and not self.active_shrine.completed:
            self.active_shrine.completed = True
            self.player.crown_shards += 1
            self.player.cookies += 1
            play_sfx('shrine_complete')
            self.hud.add_notification(f"Cookie obtained! ({self.player.cookies} total)")
            self.hud.add_notification("Use cookies in Inventory (Tab) to upgrade stats!")

            # Unlock abilities based on shrine count
            if self.player.crown_shards == 2 and AbilityType.FORGE_BOND not in self.player.abilities:
                self.player.abilities.append(AbilityType.FORGE_BOND)
                self.hud.add_notification("Ability unlocked: Forge Bond!")
            elif self.player.crown_shards == 4 and AbilityType.PHASE_RISE not in self.player.abilities:
                self.player.abilities.append(AbilityType.PHASE_RISE)
                self.hud.add_notification("Ability unlocked: Phase Rise!")
            elif self.player.crown_shards == 8 and AbilityType.TIME_REWIND not in self.player.abilities:
                self.player.abilities.append(AbilityType.TIME_REWIND)
                self.hud.add_notification("Ability unlocked: Time Rewind!")

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
            self.player.update(self.dt, self.world.seed)
            self.world.update(self.dt, self.player)
            self.particles.update(self.dt)
            self.hud.update(self.dt)

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
                        enemy.update(self.dt, self.player.x, self.player.y, self.player.z)
                        if enemy.can_attack() and dist2d(enemy.x, enemy.z, self.player.x, self.player.z) < ATTACK_RANGE * 1.5:
                            dmg = enemy.do_attack()
                            self.player.take_damage(dmg)

                # Arrow collisions inside shrine
                for arrow in self.player.projectiles:
                    if not arrow.alive:
                        continue
                    for enemy in self.active_shrine.enemies:
                        if enemy.alive and dist3d(arrow.x, arrow.y, arrow.z, enemy.x, enemy.y + enemy.size * 0.5, enemy.z) < enemy.size:
                            enemy.take_damage(arrow.damage)
                            arrow.alive = False
                            if not enemy.alive:
                                self.player.xp += enemy.xp
                                self.particles.emit_death(enemy.x, enemy.y, enemy.z, enemy.color)
                            break

            if not self.player.alive:
                self.state = GameState.GAME_OVER
                play_sfx('death')
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

        # Clamp to world bounds
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

        if self.state == GameState.SHRINE:
            self._render_shrine()
            return

        if self.in_castle:
            self._render_castle()
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
