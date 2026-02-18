"""
EvoWild  â€“  3D Animal Evolution Sandbox (Ursina Engine)
Infinite procedural world  Â·  Body-part mutations  Â·  Survival + Exploration
"""
from ursina import *
from ursina.color import Color
import json, math, random, time as _time
from pathlib import Path

# rgb() in this Ursina version does NOT divide by 255, so colors > 1 = white.
# We define our own helpers that properly normalize.
def rgb(r, g, b):
    return Color(r / 255, g / 255, b / 255, 1.0)

def rgba(r, g, b, a):
    return Color(r / 255, g / 255, b / 255, a / 255)

# â”€â”€ constants â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CHUNK_SIZE   = 40          # world units per chunk
LOAD_RADIUS  = 3           # chunks around player to keep loaded
SAVE_PATH    = Path("evo_wild_saves.json")
SAVE_SLOTS   = 8

# â”€â”€ helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _hash_f(ix, iy, seed=42):
    """Deterministic hash for integer grid coords, returns 0-1."""
    n = (ix * 374761393 + iy * 668265263 + seed * 1274126177) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return (n & 0xFFFF) / 0xFFFF

def smooth_noise(wx, wz, scale=300, seed=42):
    """Value noise with bilinear interpolation. Returns -1..1."""
    sx = wx / scale
    sz = wz / scale
    ix = int(math.floor(sx))
    iz = int(math.floor(sz))
    fx = sx - ix
    fz = sz - iz
    # smoothstep
    fx = fx * fx * (3 - 2 * fx)
    fz = fz * fz * (3 - 2 * fz)
    v00 = _hash_f(ix,     iz,     seed)
    v10 = _hash_f(ix + 1, iz,     seed)
    v01 = _hash_f(ix,     iz + 1, seed)
    v11 = _hash_f(ix + 1, iz + 1, seed)
    top    = v00 + (v10 - v00) * fx
    bottom = v01 + (v11 - v01) * fx
    return (top + (bottom - top) * fz) * 2 - 1

def biome_at(x, z):
    """Large-scale biomes based on smooth noise."""
    v = smooth_noise(x, z, scale=350, seed=99)
    if v < -0.2:
        return "swamp"
    if v < 0.35:
        return "forest"
    return "highlands"

def noise2d(x, y, seed=42):
    """Quick hash noise for decoration colour variation (returns -1..1)."""
    return _hash_f(int(x * 1000), int(y * 1000), seed) * 2 - 1

BIOME_COLORS = {
    "forest":    (42, 95, 48),
    "swamp":     (58, 88, 56),
    "highlands": (78, 92, 72),
}

# â”€â”€ body part builder â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class CreatureBody(Entity):
    """Modular 3D creature built from primitives."""
    def __init__(self, **kw):
        super().__init__(**kw)
        # torso
        self.torso = Entity(parent=self, model='sphere',
                            color=rgb(225, 190, 90),
                            scale=(1.0, 0.7, 1.4), y=0.55)
        # head
        self.head = Entity(parent=self, model='sphere',
                           color=rgb(235, 200, 100),
                           scale=(0.55, 0.5, 0.55),
                           position=(0, 0.9, 0.7))
        # eyes
        Entity(parent=self.head, model='sphere', color=color.white,
               scale=(0.25, 0.25, 0.15), position=(-0.25, 0.1, 0.45))
        Entity(parent=self.head, model='sphere', color=color.white,
               scale=(0.25, 0.25, 0.15), position=(0.25, 0.1, 0.45))
        self.left_pupil = Entity(parent=self.head, model='sphere', color=color.black,
               scale=(0.12, 0.12, 0.08), position=(-0.25, 0.1, 0.52))
        self.right_pupil = Entity(parent=self.head, model='sphere', color=color.black,
               scale=(0.12, 0.12, 0.08), position=(0.25, 0.1, 0.52))
        # nose
        Entity(parent=self.head, model='sphere', color=rgb(60, 40, 30),
               scale=(0.12, 0.08, 0.1), position=(0, -0.05, 0.52))
        # ears
        self.ear_l = Entity(parent=self.head, model='cube',
                            color=rgb(210, 175, 80),
                            scale=(0.12, 0.25, 0.08), position=(-0.28, 0.35, 0.0),
                            rotation_x=-15)
        self.ear_r = Entity(parent=self.head, model='cube',
                            color=rgb(210, 175, 80),
                            scale=(0.12, 0.25, 0.08), position=(0.28, 0.35, 0.0),
                            rotation_x=-15)
        # legs (4)
        self.legs = []
        for lx, lz in [(-0.35, -0.5), (0.35, -0.5), (-0.35, 0.5), (0.35, 0.5)]:
            leg = Entity(parent=self, model='cube', color=rgb(200, 165, 70),
                         scale=(0.18, 0.45, 0.18), position=(lx, 0.22, lz))
            self.legs.append(leg)
        # tail
        self.tail = Entity(parent=self, model='cube', color=rgb(210, 175, 80),
                           scale=(0.12, 0.12, 0.5), position=(0, 0.55, -0.9),
                           rotation_x=-30)

        # mutation parts (hidden until unlocked)
        self.wings = Entity(parent=self, model='cube',
                            color=rgb(180, 210, 255),
                            scale=(2.2, 0.05, 0.6), y=0.8, visible=False)
        self.claws = Entity(parent=self, model='cube',
                            color=rgb(80, 80, 80),
                            scale=(0.08, 0.15, 0.08), position=(0, -0.05, 0.85),
                            visible=False)
        self.venom_fangs = Entity(parent=self.head, model='cube',
                                  color=rgb(130, 255, 100),
                                  scale=(0.04, 0.18, 0.04), position=(0, -0.22, 0.35),
                                  rotation_x=180, visible=False)
        self.glow_ring = Entity(parent=self, model='sphere',
                                color=rgba(80, 240, 100, 0),
                                scale=1.8, y=0.55, visible=False)
        self.titan_plates = Entity(parent=self, model='cube',
                                   color=rgb(120, 110, 100),
                                   scale=(1.25, 0.3, 1.6), y=0.9, visible=False)
        self.stride_boots = []
        for leg in self.legs:
            boot = Entity(parent=leg, model='sphere',
                          color=rgb(100, 160, 220),
                          scale=(1.3, 0.5, 1.3), y=-0.5, visible=False)
            self.stride_boots.append(boot)

        self._base_scale = 1.0

    def apply_visual(self, mutation_name: str):
        if mutation_name == "Swift Legs":
            for leg in self.legs:
                leg.scale_y = 0.55
                leg.y = 0.27
        elif mutation_name == "Thick Hide":
            self.torso.color = rgb(185, 155, 75)
            self.torso.scale = (1.1, 0.8, 1.5)
        elif mutation_name == "Keen Fangs":
            self.claws.visible = True
        elif mutation_name == "Night Eyes":
            self.left_pupil.color = rgb(255, 220, 60)
            self.right_pupil.color = rgb(255, 220, 60)
        elif mutation_name == "Burrow Claws":
            self.claws.visible = True
            self.claws.scale = (0.12, 0.2, 0.12)
            self.claws.color = rgb(100, 70, 50)
        elif mutation_name == "Glide Skin":
            self.wings.visible = True
        elif mutation_name == "Amphib Lungs":
            self.torso.color = rgb(100, 180, 140)
        elif mutation_name == "Venom Bite":
            self.venom_fangs.visible = True
        elif mutation_name == "Long Stride":
            for b in self.stride_boots:
                b.visible = True
        elif mutation_name == "Regen Tissue":
            self.torso.color = rgb(200, 170, 190)
        elif mutation_name == "Echo Sense":
            self.ear_l.scale = (0.22, 0.38, 0.15)
            self.ear_r.scale = (0.22, 0.38, 0.15)
        elif mutation_name == "Rage Core":
            self.torso.color = rgb(200, 100, 80)
        elif mutation_name == "Nuclear Gland":
            self.glow_ring.visible = True
            self.glow_ring.color = rgba(80, 240, 100, 60)
        elif mutation_name == "Titan Frame":
            self.titan_plates.visible = True
            self._base_scale *= 1.15
            self.scale = self._base_scale

    def update_glow(self, nuclear_level: int):
        if nuclear_level > 0:
            self.glow_ring.visible = True
            a = min(180, 30 + nuclear_level * 18)
            self.glow_ring.color = rgba(80, 240, 100, a)
            self.glow_ring.scale = 1.8 + nuclear_level * 0.12

    def set_base_color(self, r, g, b):
        """Recolour the creature's base body parts."""
        self.torso.color = rgb(r, g, b)
        self.head.color = rgb(min(255, r + 10), min(255, g + 10), min(255, b + 10))
        self.ear_l.color = rgb(max(0, r - 15), max(0, g - 15), max(0, b - 10))
        self.ear_r.color = rgb(max(0, r - 15), max(0, g - 15), max(0, b - 10))
        for leg in self.legs:
            leg.color = rgb(max(0, r - 25), max(0, g - 25), max(0, b - 20))
        self.tail.color = rgb(max(0, r - 15), max(0, g - 15), max(0, b - 10))


# â”€â”€ world chunk manager â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class ChunkManager:
    def __init__(self):
        self.chunks = {}
        self.decorations = {}

    def chunk_key(self, wx, wz):
        return (int(math.floor(wx / CHUNK_SIZE)), int(math.floor(wz / CHUNK_SIZE)))

    def load_around(self, px, pz):
        cx, cz = self.chunk_key(px, pz)
        needed = set()
        for dx in range(-LOAD_RADIUS, LOAD_RADIUS + 1):
            for dz in range(-LOAD_RADIUS, LOAD_RADIUS + 1):
                needed.add((cx + dx, cz + dz))

        # unload far
        for key in list(self.chunks.keys()):
            if key not in needed:
                destroy(self.chunks.pop(key))
                for e in self.decorations.pop(key, []):
                    destroy(e)

        # load new
        for key in needed:
            if key not in self.chunks:
                self._create_chunk(key)

    def _create_chunk(self, key):
        kx, kz = key
        wx = kx * CHUNK_SIZE + CHUNK_SIZE / 2
        wz = kz * CHUNK_SIZE + CHUNK_SIZE / 2
        biome = biome_at(wx, wz)
        bc = BIOME_COLORS.get(biome, (60, 80, 55))
        rv = noise2d(kx * 3.7, kz * 5.1)
        shade = int(rv * 12)
        r = max(0, min(255, bc[0] + shade))
        g = max(0, min(255, bc[1] + shade))
        b = max(0, min(255, bc[2] + shade))
        ground = Entity(model='plane', scale=CHUNK_SIZE,
                        position=(wx, 0, wz),
                        color=rgb(r, g, b),
                        collider='box')
        self.chunks[key] = ground
        # decorations
        rng = random.Random(kx * 73856093 ^ kz * 19349663)
        decs = []
        tree_count = rng.randint(2, 6) if biome == "forest" else rng.randint(0, 3)
        rock_count = rng.randint(1, 4) if biome == "highlands" else rng.randint(0, 2)
        for _ in range(tree_count):
            tx = wx + rng.uniform(-CHUNK_SIZE / 2.2, CHUNK_SIZE / 2.2)
            tz = wz + rng.uniform(-CHUNK_SIZE / 2.2, CHUNK_SIZE / 2.2)
            tree = self._make_tree(tx, tz, biome, rng)
            decs.append(tree)
        for _ in range(rock_count):
            rx = wx + rng.uniform(-CHUNK_SIZE / 2.2, CHUNK_SIZE / 2.2)
            rz = wz + rng.uniform(-CHUNK_SIZE / 2.2, CHUNK_SIZE / 2.2)
            rock = self._make_rock(rx, rz, rng)
            decs.append(rock)
        self.decorations[key] = decs

    def _make_tree(self, x, z, biome, rng):
        tree = Entity(position=(x, 0, z))
        h = rng.uniform(2.5, 4.5)
        Entity(parent=tree, model='cube', color=rgb(92, 65, 38),
               scale=(0.3, h, 0.3), y=h / 2)
        if biome == "forest":
            cc = rgb(40 + rng.randint(0, 25), 110 + rng.randint(0, 30),
                           45 + rng.randint(0, 20))
        elif biome == "swamp":
            cc = rgb(50 + rng.randint(0, 15), 90 + rng.randint(0, 20),
                           50 + rng.randint(0, 15))
        else:
            cc = rgb(65 + rng.randint(0, 20), 100 + rng.randint(0, 20),
                           65 + rng.randint(0, 15))
        for i in range(3):
            r = 2.0 - i * 0.45
            Entity(parent=tree, model='sphere', color=cc,
                   scale=(r, r * 0.7, r), y=h + i * 0.9)
        return tree

    def _make_rock(self, x, z, rng):
        s = rng.uniform(0.6, 1.8)
        rock = Entity(model='sphere', position=(x, s * 0.3, z),
                      scale=(s, s * 0.6, s * 0.8),
                      color=rgb(115 + rng.randint(-15, 15),
                                      110 + rng.randint(-15, 15),
                                      105 + rng.randint(-15, 15)))
        return rock


# â”€â”€ 3D food entity â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class FoodEntity(Entity):
    def __init__(self, kind, **kw):
        super().__init__(**kw)
        self.kind = kind
        self.bob_offset = random.random() * math.pi * 2
        if kind == "berry":
            Entity(parent=self, model='sphere', color=rgb(180, 55, 140),
                   scale=0.3, y=0.3)
            Entity(parent=self, model='sphere', color=rgb(60, 140, 55),
                   scale=(0.15, 0.06, 0.1), y=0.52)
        elif kind == "meat":
            Entity(parent=self, model='cube', color=rgb(190, 75, 75),
                   scale=(0.4, 0.15, 0.3), y=0.15)
            Entity(parent=self, model='cube', color=rgb(230, 225, 210),
                   scale=(0.04, 0.25, 0.04), y=0.15, rotation_z=45)
        else:  # stick
            Entity(parent=self, model='cube', color=rgb(140, 110, 60),
                   scale=(0.08, 0.08, 0.6), y=0.15)


# â”€â”€ 3D predator entity â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class PredatorEntity(Entity):
    def __init__(self, kind, hp, speed, damage, **kw):
        super().__init__(**kw)
        self.kind = kind
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.damage = damage
        self.wander_dir = Vec3(random.uniform(-1, 1), 0,
                               random.uniform(-1, 1)).normalized()
        self.wander_timer = random.uniform(1, 3)

        if kind == "wolf":
            Entity(parent=self, model='sphere', color=rgb(140, 100, 75),
                   scale=(0.7, 0.5, 1.1), y=0.5)
            head = Entity(parent=self, model='sphere', color=rgb(155, 115, 85),
                          scale=0.38, position=(0, 0.65, 0.65))
            Entity(parent=head, model='cube', color=rgb(130, 90, 65),
                   scale=(0.1, 0.18, 0.06), position=(-0.15, 0.22, 0))
            Entity(parent=head, model='cube', color=rgb(130, 90, 65),
                   scale=(0.1, 0.18, 0.06), position=(0.15, 0.22, 0))
            Entity(parent=head, model='sphere', color=color.black,
                   scale=0.06, position=(-0.1, 0.05, 0.16))
            Entity(parent=head, model='sphere', color=color.black,
                   scale=0.06, position=(0.1, 0.05, 0.16))
            for lx, lz in [(-0.25, -0.35), (0.25, -0.35),
                            (-0.25, 0.35), (0.25, 0.35)]:
                Entity(parent=self, model='cube', color=rgb(120, 85, 60),
                       scale=(0.12, 0.35, 0.12), position=(lx, 0.17, lz))
        elif kind == "gator":
            Entity(parent=self, model='sphere', color=rgb(72, 120, 70),
                   scale=(0.6, 0.35, 1.4), y=0.3)
            Entity(parent=self, model='sphere', color=rgb(82, 135, 80),
                   scale=(0.3, 0.2, 0.5), position=(0, 0.35, 0.85))
            Entity(parent=self, model='sphere', color=color.black,
                   scale=0.06, position=(-0.12, 0.45, 0.7))
            Entity(parent=self, model='sphere', color=color.black,
                   scale=0.06, position=(0.12, 0.45, 0.7))
            Entity(parent=self, model='cube', color=rgb(62, 105, 60),
                   scale=(0.15, 0.1, 0.6), position=(0, 0.25, -0.95))
        else:  # lynx
            Entity(parent=self, model='sphere', color=rgb(125, 125, 165),
                   scale=(0.55, 0.45, 0.9), y=0.45)
            head = Entity(parent=self, model='sphere', color=rgb(140, 140, 180),
                          scale=0.32, position=(0, 0.6, 0.5))
            Entity(parent=head, model='cube', color=rgb(100, 100, 140),
                   scale=(0.04, 0.25, 0.04), position=(-0.12, 0.22, 0))
            Entity(parent=head, model='cube', color=rgb(100, 100, 140),
                   scale=(0.04, 0.25, 0.04), position=(0.12, 0.22, 0))
            Entity(parent=head, model='sphere', color=color.black,
                   scale=0.06, position=(-0.08, 0.04, 0.14))
            Entity(parent=head, model='sphere', color=color.black,
                   scale=0.06, position=(0.08, 0.04, 0.14))
            for lx, lz in [(-0.2, -0.3), (0.2, -0.3),
                            (-0.2, 0.3), (0.2, 0.3)]:
                Entity(parent=self, model='cube', color=rgb(110, 110, 150),
                       scale=(0.1, 0.3, 0.1), position=(lx, 0.15, lz))

        # hp bar
        self.hp_bg = Entity(parent=self, model='quad', color=color.dark_gray,
                            scale=(0.8, 0.08, 1), y=1.2, billboard=True)
        self.hp_bar = Entity(parent=self, model='quad', color=color.red,
                             scale=(0.8, 0.08, 1), y=1.2, billboard=True)


# â”€â”€ nuclear core entity â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class NuclearCoreEntity(Entity):
    def __init__(self, radius, ttl, **kw):
        super().__init__(**kw)
        self.radius = radius
        self.ttl = ttl
        self.orb = Entity(parent=self, model='sphere',
                          color=rgb(100, 240, 110),
                          scale=1.0, y=1.5)
        Entity(parent=self, model='sphere', color=rgba(60, 220, 80, 30),
               scale=radius * 2, y=0.1)


# â”€â”€ den entity â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class DenEntity(Entity):
    def __init__(self, **kw):
        super().__init__(**kw)
        Entity(parent=self, model='sphere', color=rgb(168, 135, 88),
               scale=(2, 1.2, 2), y=0.6)
        Entity(parent=self, model='sphere', color=rgb(50, 35, 22),
               scale=(0.6, 0.5, 0.3), position=(0, 0.3, 1.0))


# ── treasure chest entity ────────────────────────────────────────
class TreasureEntity(Entity):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bob_offset = random.random() * math.pi * 2
        # golden base box
        Entity(parent=self, model='cube', color=rgb(210, 175, 55),
               scale=(0.6, 0.45, 0.5), y=0.25)
        # darker lid
        Entity(parent=self, model='cube', color=rgb(180, 145, 35),
               scale=(0.65, 0.15, 0.52), y=0.52)
        # lock jewel
        Entity(parent=self, model='sphere', color=rgb(80, 200, 255),
               scale=0.12, position=(0, 0.35, 0.27))
        # sparkle ring
        self.sparkle = Entity(parent=self, model='sphere',
                              color=rgba(255, 220, 80, 50),
                              scale=1.2, y=0.35)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  MAIN GAME
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
app = Ursina(title="EvoWild 3D", borderless=False, size=(1280, 720),
             development_mode=False)


# â”€â”€ sky â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
sky_entity = Sky(color=rgb(135, 195, 235))
scene.fog_color = rgb(170, 210, 235)
scene.fog_density = 0.008

# â”€â”€ basic lighting (simplepbr uses these Panda3D lights) â”€â”€â”€â”€â”€â”€â”€â”€â”€
from panda3d.core import DirectionalLight as PandaDL, AmbientLight as PandaAL
from panda3d.core import Vec4
dl = PandaDL('sun')
dl.set_color(Vec4(0.9, 0.87, 0.8, 1))
dl_np = base.render.attach_new_node(dl)
dl_np.set_hpr(45, -45, 0)
base.render.set_light(dl_np)

al = PandaAL('ambient')
al.set_color(Vec4(0.5, 0.5, 0.55, 1))
al_np = base.render.attach_new_node(al)
base.render.set_light(al_np)

# â”€â”€ camera setup â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
camera.position = (0, 18, -14)
camera.rotation_x = 52

# â”€â”€ game state â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
state = {
    "hp": 20, "max_hp": 20,
    "hunger": 100, "max_hunger": 100,
    "attack_damage": 4.0, "attack_range": 3.5,
    "attack_cooldown": 0.0,
    "speed": 8.0,
    "level": 1, "xp": 0, "next_xp": 25,
    "dna": 0,
    "meat_strength": 0,
    "nuclear_level": 0, "nuclear_dot_damage": 0,
    "exposure_meter": 0.0,
    "wood": 0,
    "mutations_owned": set(),
    "current_slot": 1,
    "carrying": None,
    "menu_open": False,
    "body_color_idx": 0,
    "day_time": 0.0,
    "biomes_discovered": set(),
    "kills": 0,
}

# (name, dna_cost)
MUTATIONS = [
    ("Swift Legs", 8), ("Thick Hide", 8), ("Keen Fangs", 10),
    ("Night Eyes", 6), ("Burrow Claws", 10), ("Glide Skin", 18),
    ("Amphib Lungs", 15), ("Venom Bite", 18), ("Scavenger Gut", 8),
    ("Iron Stomach", 8), ("Long Stride", 15), ("Regen Tissue", 18),
    ("Echo Sense", 25), ("Rage Core", 25), ("Nuclear Gland", 30),
    ("Titan Frame", 30),
]

MUTATION_STATS = {
    "Swift Legs": "+2.5 Spd",
    "Thick Hide": "+6 Max HP",
    "Keen Fangs": "+2 Atk",
    "Night Eyes": "Glow Eyes",
    "Burrow Claws": "+1 Range",
    "Glide Skin": "+1.5 Spd, Wings",
    "Amphib Lungs": "+30 Max Hunger",
    "Venom Bite": "+1.5 Atk",
    "Scavenger Gut": "-25% Drain",
    "Iron Stomach": "+30 Food",
    "Long Stride": "+2 Spd",
    "Regen Tissue": "+4 HP, Regen",
    "Echo Sense": "+1.5 Range",
    "Rage Core": "+4 Atk",
    "Nuclear Gland": "+6 Nuke, +1 HP",
    "Titan Frame": "+12 HP, -1 Spd",
}

BODY_COLORS = [
    ("Default",  225, 190, 90),
    ("Arctic",   220, 230, 240),
    ("Forest",   70, 145, 65),
    ("Scarlet",  195, 70, 55),
    ("Shadow",   65, 60, 75),
    ("Aqua",     70, 185, 195),
    ("Golden",   235, 195, 45),
    ("Violet",   145, 85, 175),
]


# â”€â”€ player â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
player = CreatureBody(position=(0, 0.5, 0))

# â”€â”€ world systems â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
chunk_mgr = ChunkManager()
foods = []
predators = []
dens = []
nuclear_cores = []
core_timer = random.uniform(25, 40)
food_timer = 0.0
pred_check = 0.0
leg_anim_time = 0.0
treasures = []
treasure_timer = random.uniform(20, 40)
dust_particles = []
popup_texts = []
dust_spawn_cd = 0.0

# â”€â”€ HUD â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
hp_text = Text(text="", position=(-0.87, 0.48), scale=1.2, color=color.white)
hunger_text = Text(text="", position=(-0.87, 0.44), scale=1.2, color=color.white)
stats_text = Text(text="", position=(-0.87, 0.40), scale=1.0, color=color.white)
msg_text = Text(text="Explore, evolve, survive. Click to grab/eat.",
                position=(-0.5, -0.42), scale=1.2, color=color.yellow)
help_text = Text(
    text=("[WASD] move  [Click] grab/eat  [Space] attack  [C] customize  "
          "[B] den  [F5/F9] save/load  [[/]] slot  [R] restart"),
    position=(-0.87, -0.46), scale=0.85, color=rgb(200, 200, 200))
msg_timer = 5.0

# ── Customization Menu ──────────────────────────────────────────
cust_menu = {"elements": [], "mut_buttons": [], "color_buttons": [], "dna_text": None}


def _build_customization_menu():
    els = cust_menu["elements"]

    # dark overlay
    bg = Entity(parent=camera.ui, model='quad', color=rgba(10, 10, 20, 210),
                scale=(3, 2), z=-5, enabled=False)
    els.append(bg)

    # title
    t = Text("CHARACTER CUSTOMIZATION", parent=camera.ui,
             position=(0, 0.44), origin=(0, 0), scale=2.2,
             color=rgb(255, 220, 80), z=-6, enabled=False)
    els.append(t)

    # dna counter
    dna_t = Text("", parent=camera.ui, position=(0, 0.385),
                 origin=(0, 0), scale=1.5, color=rgb(100, 255, 180),
                 z=-6, enabled=False)
    els.append(dna_t)
    cust_menu["dna_text"] = dna_t

    # section headers
    lh = Text("MUTATIONS", parent=camera.ui,
              position=(-0.35, 0.335), origin=(0, 0), scale=1.1,
              color=rgb(180, 180, 200), z=-6, enabled=False)
    els.append(lh)
    rh = Text("MUTATIONS", parent=camera.ui,
              position=(0.18, 0.335), origin=(0, 0), scale=1.1,
              color=rgb(180, 180, 200), z=-6, enabled=False)
    els.append(rh)

    # mutation buttons (2 columns of 8)
    for i, (name, cost) in enumerate(MUTATIONS):
        col = 0 if i < 8 else 1
        row = i if i < 8 else i - 8
        x = -0.35 + col * 0.53
        y = 0.28 - row * 0.068
        stat = MUTATION_STATS.get(name, "")
        label = f"{name}  [{cost} DNA]  {stat}"

        btn = Button(
            text=label,
            parent=camera.ui,
            position=(x, y),
            scale=(0.50, 0.058),
            color=rgb(35, 35, 50),
            highlight_color=rgb(55, 55, 75),
            pressed_color=rgb(70, 70, 90),
            z=-6,
            enabled=False,
        )
        btn.text_entity.scale = Vec2(0.65, 0.65)
        btn.text_entity.color = color.white
        btn._mut_name = name
        btn._mut_cost = cost
        btn.on_click = lambda n=name, c=cost: _buy_mutation_click(n, c)
        cust_menu["mut_buttons"].append(btn)
        els.append(btn)

    # COLOR section header
    col_header = Text("BODY COLOR", parent=camera.ui,
                      position=(0, -0.28), origin=(0, 0), scale=1.2,
                      color=rgb(200, 200, 220), z=-6, enabled=False)
    els.append(col_header)

    # color buttons
    for i, (cname, cr, cg, cb) in enumerate(BODY_COLORS):
        x = -0.52 + i * 0.153
        btn = Button(
            text=cname,
            parent=camera.ui,
            position=(x, -0.35),
            scale=(0.14, 0.055),
            color=rgb(cr, cg, cb),
            highlight_color=rgb(min(255, cr + 35), min(255, cg + 35), min(255, cb + 35)),
            z=-6,
            enabled=False,
        )
        btn.text_entity.scale = Vec2(0.55, 0.55)
        brightness = (cr + cg + cb) / 3
        btn.text_entity.color = color.black if brightness > 140 else color.white
        btn._color_idx = i
        btn.on_click = lambda idx=i: _set_color_click(idx)
        cust_menu["color_buttons"].append(btn)
        els.append(btn)

    # close hint
    close_t = Text("[C] Close", parent=camera.ui,
                   position=(0, -0.44), origin=(0, 0), scale=1.3,
                   color=rgb(160, 160, 160), z=-6, enabled=False)
    els.append(close_t)


def _refresh_customization():
    """Update button colours/text to reflect current owned mutations & DNA."""
    if cust_menu["dna_text"]:
        cust_menu["dna_text"].text = f"DNA: {state['dna']}"

    for btn in cust_menu["mut_buttons"]:
        name = btn._mut_name
        cost = btn._mut_cost
        owned = name in state["mutations_owned"]
        can_afford = state["dna"] >= cost
        stat = MUTATION_STATS.get(name, "")

        if owned:
            btn.color = rgb(25, 65, 30)
            btn.highlight_color = rgb(25, 65, 30)
            btn.text_entity.text = f"[OWNED]  {name}  {stat}"
            btn.text_entity.color = rgb(120, 255, 120)
        elif can_afford:
            btn.color = rgb(35, 35, 60)
            btn.highlight_color = rgb(60, 60, 90)
            btn.text_entity.text = f"{name}  [{cost} DNA]  {stat}"
            btn.text_entity.color = color.white
        else:
            btn.color = rgb(50, 30, 30)
            btn.highlight_color = rgb(60, 40, 40)
            btn.text_entity.text = f"{name}  [{cost} DNA]  {stat}"
            btn.text_entity.color = rgb(140, 100, 100)

    # highlight active colour
    for btn in cust_menu["color_buttons"]:
        idx = btn._color_idx
        _, cr, cg, cb = BODY_COLORS[idx]
        if idx == state["body_color_idx"]:
            btn.color = rgb(min(255, cr + 50), min(255, cg + 50), min(255, cb + 50))
        else:
            btn.color = rgb(cr, cg, cb)


def _buy_mutation_click(name, cost):
    if name in state["mutations_owned"]:
        push_msg(f"{name} already owned")
        return
    if state["dna"] < cost:
        push_msg(f"Need {cost} DNA for {name} (have {state['dna']})")
        return
    state["dna"] -= cost
    state["mutations_owned"].add(name)
    apply_mutation_stats(name)
    player.apply_visual(name)
    push_msg(f"Mutation acquired: {name}")
    _refresh_customization()


def _set_color_click(idx):
    state["body_color_idx"] = idx
    _, cr, cg, cb = BODY_COLORS[idx]
    player.set_base_color(cr, cg, cb)
    push_msg(f"Color: {BODY_COLORS[idx][0]}")
    _refresh_customization()


def open_customization():
    state["menu_open"] = True
    _refresh_customization()
    for el in cust_menu["elements"]:
        el.enabled = True


def close_customization():
    state["menu_open"] = False
    for el in cust_menu["elements"]:
        el.enabled = False


_build_customization_menu()




# â”€â”€ food spawner â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def spawn_food_around(px, pz, count=1):
    for _ in range(count):
        r = random.random()
        kind = "berry" if r < 0.5 else ("stick" if r < 0.8 else "meat")
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(8, CHUNK_SIZE * LOAD_RADIUS * 0.8)
        fx = px + math.cos(angle) * dist
        fz = pz + math.sin(angle) * dist
        f = FoodEntity(kind, position=(fx, 0, fz))
        foods.append(f)


def spawn_predator_around(px, pz):
    angle = random.uniform(0, math.pi * 2)
    dist = random.uniform(25, CHUNK_SIZE * LOAD_RADIUS * 0.7)
    ex = px + math.cos(angle) * dist
    ez = pz + math.sin(angle) * dist
    biome = biome_at(ex, ez)
    if biome == "forest":
        p = PredatorEntity("wolf", hp=16, speed=5, damage=4,
                           position=(ex, 0, ez))
    elif biome == "swamp":
        p = PredatorEntity("gator", hp=20, speed=3.5, damage=5,
                           position=(ex, 0, ez))
    else:
        p = PredatorEntity("lynx", hp=14, speed=6, damage=3,
                           position=(ex, 0, ez))
    predators.append(p)


# initial spawns
for _ in range(50):
    spawn_food_around(0, 0)
for _ in range(5):
    spawn_predator_around(0, 0)


# â”€â”€ push message â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def spawn_popup(txt, world_pos, col=color.yellow, rise_speed=3.0, lifetime=1.2):
    """Spawn a floating text that rises and fades."""
    t = Text(text=txt, scale=1.8, color=col, billboard=True,
             position=world_pos + Vec3(random.uniform(-0.3, 0.3), 1.5, 0))
    popup_texts.append({"entity": t, "life": lifetime, "max_life": lifetime,
                        "rise": rise_speed})


def spawn_dust(pos, move_dir):
    """Spawn a small dust puff behind the player."""
    offset = Vec3(random.uniform(-0.3, 0.3), 0, random.uniform(-0.3, 0.3))
    d = Entity(model='cube', color=rgba(180, 160, 130, 160),
               scale=random.uniform(0.08, 0.18),
               position=pos + offset - move_dir * 0.5)
    d.y = random.uniform(0.05, 0.2)
    dust_particles.append({"entity": d, "life": 0.6})


def spawn_treasure_around(px, pz):
    angle = random.uniform(0, math.pi * 2)
    dist = random.uniform(15, CHUNK_SIZE * LOAD_RADIUS * 0.6)
    tx = px + math.cos(angle) * dist
    tz = pz + math.sin(angle) * dist
    t = TreasureEntity(position=(tx, 0, tz))
    treasures.append(t)

def push_msg(txt, sec=4.0):
    global msg_timer
    msg_text.text = txt
    msg_timer = sec


# â”€â”€ gain xp â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def gain_xp(amount):
    state["xp"] += amount
    while state["xp"] >= state["next_xp"]:
        state["xp"] -= state["next_xp"]
        state["level"] += 1
        state["next_xp"] = int(state["next_xp"] * 1.25)
        push_msg(f"Level {state['level']}!")


# â”€â”€ mutations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def try_mutate():
    candidates = [m for m in MUTATIONS if m[0] not in state["mutations_owned"]]
    if not candidates:
        push_msg("All mutations unlocked")
        return
    random.shuffle(candidates)
    name, dna_cost = candidates[0]
    if state["dna"] < dna_cost:
        push_msg(f"Need {dna_cost} DNA for {name} (have {state['dna']})")
        return
    state["dna"] -= dna_cost
    state["mutations_owned"].add(name)
    apply_mutation_stats(name)
    player.apply_visual(name)
    push_msg(f"Mutation: {name}")


def apply_mutation_stats(name):
    s = state
    if name == "Swift Legs":      s["speed"] += 2.5
    elif name == "Thick Hide":    s["max_hp"] += 6; s["hp"] += 6
    elif name == "Keen Fangs":    s["attack_damage"] += 2
    elif name == "Burrow Claws":  s["attack_range"] += 1
    elif name == "Glide Skin":    s["speed"] += 1.5
    elif name == "Amphib Lungs":  s["max_hunger"] += 30; s["hunger"] += 20
    elif name == "Venom Bite":    s["attack_damage"] += 1.5
    elif name == "Scavenger Gut": s["max_hunger"] += 20
    elif name == "Iron Stomach":  s["hunger"] = min(s["max_hunger"],
                                                     s["hunger"] + 30)
    elif name == "Long Stride":   s["speed"] += 2
    elif name == "Regen Tissue":  s["max_hp"] += 4
    elif name == "Echo Sense":    s["attack_range"] += 1.5
    elif name == "Rage Core":     s["attack_damage"] += 4
    elif name == "Nuclear Gland":
        s["nuclear_dot_damage"] += 6; s["max_hp"] += 1; s["hp"] += 1
    elif name == "Titan Frame":
        s["max_hp"] += 12; s["hp"] += 12; s["speed"] -= 1


# â”€â”€ attack â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_cam_shake = {"power": 0.0, "decay": 8.0}

def camera_shake(power=0.4):
    _cam_shake["power"] = power


def do_attack():
    if state["attack_cooldown"] > 0:
        return
    state["attack_cooldown"] = 0.35
    hits = 0
    for p in predators:
        d = distance(player.position, p.position)
        if d <= state["attack_range"]:
            dmg = state["attack_damage"] + state["meat_strength"] * 0.6
            if state["nuclear_dot_damage"] > 0:
                dmg += state["nuclear_dot_damage"]
            p.hp -= dmg
            hits += 1
    if hits == 0:
        push_msg("Attack missed", 1.0)
    else:
        push_msg(f"Hit {hits} target{'s' if hits > 1 else ''}!", 1.0)
        camera_shake(0.35)


# â”€â”€ grab / eat â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def try_grab_eat():
    if state["carrying"] is not None:
        kind = state["carrying"]
        state["carrying"] = None
        if kind == "berry":
            state["hunger"] = min(state["max_hunger"], state["hunger"] + 16)
            state["dna"] += 1
            gain_xp(2); push_msg("Ate berry (+1 DNA)", 2)
            spawn_popup("+1 DNA", player.position, rgb(100, 255, 180))
        elif kind == "meat":
            state["hunger"] = min(state["max_hunger"], state["hunger"] + 24)
            state["meat_strength"] = min(30, state["meat_strength"] + 1)
            state["attack_damage"] += 0.15
            state["dna"] += 3
            gain_xp(5); push_msg("Meat consumed: +3 DNA, stronger")
            spawn_popup("+3 DNA", player.position, rgb(255, 180, 100))
        elif kind == "stick":
            state["wood"] += 1
            gain_xp(1); push_msg("Collected stick", 1.5)
        return

    # check for treasure first
    for tr in treasures[:]:
        if distance(player.position, tr.position) < 4.0:
            reward = random.randint(8, 18)
            state["dna"] += reward
            gain_xp(10)
            spawn_popup(f"+{reward} DNA!", tr.position, rgb(255, 220, 60))
            push_msg(f"Treasure! +{reward} DNA", 3)
            treasures.remove(tr)
            destroy(tr)
            return

    best, best_d = None, 5.0
    for f in foods:
        d = distance(player.position, f.position)
        if d < best_d:
            best_d = d
            best = f
    if best:
        state["carrying"] = best.kind
        foods.remove(best)
        destroy(best)
        push_msg(f"Grabbed {state['carrying']} â€“ click again to eat/use", 2.5)
    else:
        push_msg("Nothing nearby to grab", 1.0)


# â”€â”€ save / load â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _load_raw():
    base = {"slots": {str(i): None for i in range(1, SAVE_SLOTS + 1)}}
    if not SAVE_PATH.exists():
        return base
    try:
        loaded = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
        slots = loaded.get("slots", {})
        for i in range(1, SAVE_SLOTS + 1):
            slots.setdefault(str(i), None)
        return {"slots": slots}
    except Exception:
        return base


def save_game():
    raw = _load_raw()
    slot_data = {k: v for k, v in state.items() if k not in ("menu_open", "day_time")}
    slot_data["mutations_owned"] = list(state["mutations_owned"])
    slot_data["biomes_discovered"] = list(state["biomes_discovered"])
    slot_data["px"] = player.x
    slot_data["pz"] = player.z
    slot_data["dens"] = [(d.x, d.z) for d in dens]
    raw["slots"][str(state["current_slot"])] = slot_data
    SAVE_PATH.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    push_msg(f"Saved slot {state['current_slot']}")


def load_game():
    raw = _load_raw()
    sd = raw["slots"].get(str(state["current_slot"]))
    if not sd:
        push_msg(f"Slot {state['current_slot']} empty")
        return
    for k in ["hp", "max_hp", "hunger", "max_hunger", "attack_damage",
              "attack_range", "speed", "level", "xp", "next_xp",
              "dna", "meat_strength", "nuclear_level",
              "nuclear_dot_damage", "exposure_meter", "wood",
              "current_slot", "body_color_idx", "kills"]:
        if k in sd:
            state[k] = sd[k]
    state["mutations_owned"] = set(sd.get("mutations_owned", []))
    state["biomes_discovered"] = set(sd.get("biomes_discovered", []))
    state["carrying"] = sd.get("carrying")
    player.position = (sd.get("px", 0), 0, sd.get("pz", 0))
    for m in state["mutations_owned"]:
        player.apply_visual(m)
    player.update_glow(state["nuclear_level"])
    # restore body colour
    cidx = state.get("body_color_idx", 0)
    state["body_color_idx"] = cidx
    if cidx > 0 and cidx < len(BODY_COLORS):
        _, cr, cg, cb = BODY_COLORS[cidx]
        player.set_base_color(cr, cg, cb)
    for d in dens:
        destroy(d)
    dens.clear()
    for dx, dz in sd.get("dens", []):
        dens.append(DenEntity(position=(dx, 0, dz)))
    push_msg(f"Loaded slot {state['current_slot']}")


# â”€â”€ reset â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def reset_game():
    global core_timer
    state.update({
        "hp": 20, "max_hp": 20, "hunger": 100, "max_hunger": 100,
        "attack_damage": 4.0, "attack_range": 3.5, "attack_cooldown": 0.0,
        "speed": 8.0, "level": 1, "xp": 0, "next_xp": 25,
        "dna": 0, "meat_strength": 0, "nuclear_level": 0,
        "nuclear_dot_damage": 0, "exposure_meter": 0.0, "wood": 0,
        "mutations_owned": set(), "current_slot": 1, "carrying": None,
        "menu_open": False, "body_color_idx": 0,
        "day_time": 0.0, "biomes_discovered": set(), "kills": 0,
    })
    player.position = (0, 0.5, 0)
    player.scale = 1
    player._base_scale = 1.0
    player.set_base_color(225, 190, 90)  # default colour
    close_customization()
    for f in foods[:]:
        destroy(f)
    foods.clear()
    for p in predators[:]:
        destroy(p)
    predators.clear()
    for d in dens[:]:
        destroy(d)
    dens.clear()
    for c in nuclear_cores[:]:
        destroy(c)
    nuclear_cores.clear()
    for tr in treasures[:]:
        destroy(tr)
    treasures.clear()
    for dp in dust_particles[:]:
        destroy(dp['entity'])
    dust_particles.clear()
    for pp in popup_texts[:]:
        destroy(pp['entity'])
    popup_texts.clear()
    core_timer = random.uniform(25, 40)
    for _ in range(50):
        spawn_food_around(0, 0)
    for _ in range(5):
        spawn_predator_around(0, 0)
    push_msg("World reset")


# â”€â”€ input handler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def input(key):
    global core_timer
    if key == "space":
        if not state["menu_open"]:
            do_attack()
    elif key == "c":
        if state["menu_open"]:
            close_customization()
        else:
            open_customization()
    elif key == "b":
        if state["wood"] >= 5:
            state["wood"] -= 5
            d = DenEntity(position=(player.x, 0, player.z))
            dens.append(d)
            push_msg("Den built")
        else:
            push_msg("Need 5 wood")
    elif key in ("left mouse down", "right mouse down"):
        if not state["menu_open"]:
            try_grab_eat()
    elif key == "f5":
        save_game()
    elif key == "f9":
        load_game()
    elif key == "]":
        state["current_slot"] = state["current_slot"] % SAVE_SLOTS + 1
        push_msg(f"Slot: {state['current_slot']}")
    elif key == "[":
        state["current_slot"] = (state["current_slot"] - 2) % SAVE_SLOTS + 1
        push_msg(f"Slot: {state['current_slot']}")
    elif key == "r":
        reset_game()


# â”€â”€ main update â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def update():
    global core_timer, food_timer, pred_check, msg_timer, leg_anim_time, treasure_timer, dust_spawn_cd
    dt = time.dt
    s = state

    if s["hp"] <= 0:
        push_msg("You perished. [R] restart")
        return

    # skip gameplay when customization menu is open
    if s["menu_open"]:
        msg_timer -= dt
        if msg_timer <= 0:
            msg_text.text = ""
        return

    # â”€â”€ movement â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    move = Vec3(0, 0, 0)
    if held_keys['w'] or held_keys['up arrow']:    move.z += 1
    if held_keys['s'] or held_keys['down arrow']:  move.z -= 1
    if held_keys['a'] or held_keys['left arrow']:  move.x -= 1
    if held_keys['d'] or held_keys['right arrow']: move.x += 1
    moving = move.length() > 0.01
    if moving:
        move = move.normalized() * s["speed"] * dt
        player.position += move
        target_angle = math.degrees(math.atan2(move.x, move.z))
        diff = (target_angle - player.rotation_y + 180) % 360 - 180
        player.rotation_y += diff * min(1, dt * 12)
    player.y = 0.5

    # â”€â”€ leg animation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if moving:
        leg_anim_time += dt * 10
        swing = math.sin(leg_anim_time) * 22
        for i, leg in enumerate(player.legs):
            sign = 1 if i % 2 == 0 else -1
            leg.rotation_x = swing * sign
    else:
        for leg in player.legs:
            leg.rotation_x = lerp(leg.rotation_x, 0, dt * 8)

    # â”€â”€ food bobbing â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    t = _time.time()
    for f in foods:
        f.y = 0.1 + math.sin(t * 2 + f.bob_offset) * 0.1

    # â”€â”€ nuclear core bobbing â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    for nc in nuclear_cores:
        nc.orb.y = 1.5 + math.sin(t * 3) * 0.3

    # â”€â”€ camera follow â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    cam_target = player.position + Vec3(0, 18, -14)
    camera.position = lerp(camera.position, cam_target, dt * 5)
    camera.rotation_x = 52

    # â”€â”€ chunks â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    chunk_mgr.load_around(player.x, player.z)

    # â”€â”€ hunger â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    drain = 2.2
    if "Scavenger Gut" in s["mutations_owned"]:
        drain *= 0.75
    s["hunger"] = max(0, s["hunger"] - drain * dt)
    if s["hunger"] <= 0:
        s["hp"] -= 4.2 * dt

    # â”€â”€ regen â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if "Regen Tissue" in s["mutations_owned"] and s["hunger"] > 35:
        s["hp"] = min(s["max_hp"], s["hp"] + 1.8 * dt)

    s["attack_cooldown"] = max(0, s["attack_cooldown"] - dt)

    # â”€â”€ predator AI â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    for p in predators[:]:
        d = distance(player.position, p.position)
        chase_r = 14
        if d < chase_r:
            direction = (player.position - p.position)
            direction.y = 0
            if direction.length() > 0.01:
                direction = direction.normalized()
            p.position += direction * p.speed * dt
            target_a = math.degrees(math.atan2(direction.x, direction.z))
            p.rotation_y = target_a
        else:
            p.wander_timer -= dt
            if p.wander_timer <= 0:
                p.wander_dir = Vec3(random.uniform(-1, 1), 0,
                                    random.uniform(-1, 1)).normalized()
                p.wander_timer = random.uniform(1.5, 4)
            p.position += p.wander_dir * p.speed * 0.4 * dt
        p.y = 0
        # contact damage
        if d <= 1.5:
            s["hp"] -= p.damage * dt
        # hp bar
        ratio = max(0, p.hp / p.max_hp)
        p.hp_bar.scale_x = 0.8 * ratio
        # death
        if p.hp <= 0:
            predators.remove(p)
            state["dna"] += 5
            state["kills"] += 1
            gain_xp(8)
            push_msg(f"Predator slain! +5 DNA", 2)
            spawn_popup("+5 DNA", Vec3(p.x, 1, p.z), rgb(100, 255, 180))
            if random.random() < 0.5:
                foods.append(FoodEntity("meat", position=(p.x, 0, p.z)))
            destroy(p)

    # cull far predators, maintain count
    for p in predators[:]:
        if distance(player.position, p.position) > CHUNK_SIZE * LOAD_RADIUS * 1.5:
            predators.remove(p)
            destroy(p)
    pred_check -= dt
    if pred_check <= 0:
        pred_check = 3.0
        while len(predators) < 5:
            spawn_predator_around(player.x, player.z)

    # â”€â”€ food respawn â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    food_timer -= dt
    if food_timer <= 0:
        food_timer = 2.0
        for f in foods[:]:
            if distance(player.position, f.position) > CHUNK_SIZE * LOAD_RADIUS * 1.5:
                foods.remove(f)
                destroy(f)
        while len(foods) < 40:
            spawn_food_around(player.x, player.z)

    # â”€â”€ nuclear core â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    core_timer -= dt
    if not nuclear_cores and core_timer <= 0:
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(12, 30)
        cx = player.x + math.cos(angle) * dist
        cz = player.z + math.sin(angle) * dist
        nc = NuclearCoreEntity(radius=8, ttl=random.uniform(20, 30),
                               position=(cx, 0, cz))
        nuclear_cores.append(nc)
        core_timer = random.uniform(30, 50)
        push_msg("Nuclear core emerged!")

    for nc in nuclear_cores[:]:
        nc.ttl -= dt
        d = distance(player.position, nc.position)
        if d <= nc.radius:
            s["hp"] -= 4.0 * dt
            s["exposure_meter"] += 1.4 * dt
            if s["exposure_meter"] >= 1:
                s["exposure_meter"] = 0
                s["max_hp"] += 1
                s["hp"] = min(s["max_hp"], s["hp"] + 1)
                s["nuclear_level"] += 1
                s["nuclear_dot_damage"] += 2
                player.update_glow(s["nuclear_level"])
                push_msg("Nuclear adaptation! +1 max HP, stronger nuclear attack")
        if nc.ttl <= 0:
            nuclear_cores.remove(nc)
            destroy(nc)

    # â”€â”€ HUD â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # -- day/night cycle (120s full cycle) --------------------------
    s["day_time"] = (s["day_time"] + dt / 120.0) % 1.0
    dval = s["day_time"]
    # 0.0-0.25 = day, 0.25-0.3 = sunset, 0.3-0.7 = night, 0.7-0.8 = sunrise
    if dval < 0.25:
        sky_mix = 0.0
    elif dval < 0.3:
        sky_mix = (dval - 0.25) / 0.05
    elif dval < 0.7:
        sky_mix = 1.0
    elif dval < 0.8:
        sky_mix = 1.0 - (dval - 0.7) / 0.1
    else:
        sky_mix = 0.0
    day_sky = Vec3(135, 195, 235)
    night_sky = Vec3(15, 15, 40)
    sky_c = day_sky + (night_sky - day_sky) * sky_mix
    sky_entity.color = rgb(int(sky_c.x), int(sky_c.y), int(sky_c.z))
    fog_day = Vec3(170, 210, 235)
    fog_night = Vec3(20, 20, 45)
    fog_c = fog_day + (fog_night - fog_day) * sky_mix
    scene.fog_color = rgb(int(fog_c.x), int(fog_c.y), int(fog_c.z))
    sun_day = Vec4(0.9, 0.87, 0.8, 1)
    sun_night = Vec4(0.1, 0.1, 0.2, 1)
    dl.set_color(sun_day + (sun_night - sun_day) * sky_mix)
    amb_day = Vec4(0.5, 0.5, 0.55, 1)
    amb_night = Vec4(0.08, 0.08, 0.15, 1)
    al.set_color(amb_day + (amb_night - amb_day) * sky_mix)

    # -- camera shake application ----------------------------------
    if _cam_shake["power"] > 0.01:
        _cam_shake["power"] *= (1.0 - _cam_shake["decay"] * dt)
        p = _cam_shake["power"]
        camera.x += random.uniform(-p, p)
        camera.y += random.uniform(-p, p)
    else:
        _cam_shake["power"] = 0.0

    # -- dust particles when running -------------------------------
    dust_spawn_cd = max(0, dust_spawn_cd - dt)
    if moving and dust_spawn_cd <= 0:
        dust_spawn_cd = 0.08
        move_dir_back = -move.normalized() if move.length() > 0.01 else Vec3(0, 0, 0)
        spawn_dust(player.position, move_dir_back)
    for dp in dust_particles[:]:
        dp["life"] -= dt
        dp["entity"].y += dt * 0.5
        a = max(0, dp["life"] / 0.6)
        dp["entity"].color = Color(0.7, 0.65, 0.55, a)
        if dp["life"] <= 0:
            destroy(dp["entity"])
            dust_particles.remove(dp)

    # -- popup texts tick ------------------------------------------
    for pp in popup_texts[:]:
        pp["life"] -= dt
        pp["entity"].y += pp.get("rise", 3.0) * dt
        frac = max(0, pp["life"] / pp["max_life"])
        pp["entity"].color = Color(1, 1, 1, frac)
        if pp["life"] <= 0:
            destroy(pp["entity"])
            popup_texts.remove(pp)

    # -- treasure spawning + bobbing -------------------------------
    treasure_timer -= dt
    if treasure_timer <= 0:
        treasure_timer = random.uniform(25, 50)
        if len(treasures) < 3:
            spawn_treasure_around(player.x, player.z)
    for tr in treasures:
        tr.y = 0.35 + math.sin(t * 2.5 + id(tr) * 0.3) * 0.15

    # -- biome discovery bonus (first visit) -----------------------
    cur_biome = biome_at(player.x, player.z)
    if cur_biome not in s["biomes_discovered"]:
        s["biomes_discovered"].add(cur_biome)
        gain_xp(15)
        push_msg(f"Discovered {cur_biome.upper()} biome! +15 XP", 3)
        spawn_popup(f"NEW BIOME!", player.position + Vec3(0, 2, 0), rgb(255, 255, 100))

    # -- den healing zone ------------------------------------------
    for den in dens:
        if distance(player.position, den.position) < 5:
            heal_rate = 3.0
            if s["hp"] < s["max_hp"]:
                s["hp"] = min(s["max_hp"], s["hp"] + heal_rate * dt)

    # -- tail wag near food ----------------------------------------
    nearest_food_dist = 999
    for fd in foods:
        dd = distance(player.position, fd.position)
        if dd < nearest_food_dist:
            nearest_food_dist = dd
    if nearest_food_dist < 8 and hasattr(player, 'tail'):
        wag_speed = 14 - nearest_food_dist
        player.tail.rotation_y = math.sin(t * wag_speed) * 30
    elif hasattr(player, 'tail'):
        player.tail.rotation_y = lerp(player.tail.rotation_y, 0, dt * 5)

    hp_text.text = (f"HP {int(s['hp'])}/{s['max_hp']}  |  "
                    f"Hunger {int(s['hunger'])}/{s['max_hunger']}")
    hunger_text.text = (f"Lvl {s['level']}  XP {s['xp']}/{s['next_xp']}  "
                        f"DNA {s['dna']}")
    carry_str = f"  Carrying: {s['carrying']}" if s['carrying'] else ""
    biome = biome_at(player.x, player.z)
    # time of day label
    dt_val = s['day_time']
    if 0.25 <= dt_val < 0.3:   tod = 'SUNSET'
    elif 0.3 <= dt_val < 0.7:  tod = 'NIGHT'
    elif 0.7 <= dt_val < 0.8:  tod = 'SUNRISE'
    else:                       tod = 'DAY'
    stats_text.text = (
        f"Atk {s['attack_damage']:.1f}  Meat {s['meat_strength']}  "
        f"Nuke Lv{s['nuclear_level']}  Wood {s['wood']}  Kills {s['kills']}  "
        f"Dens {len(dens)}  Slot {s['current_slot']}/{SAVE_SLOTS}  "
        f"[{biome.upper()}] [{tod}]{carry_str}"
    )

    msg_timer -= dt
    if msg_timer <= 0:
        msg_text.text = ""


app.run()

