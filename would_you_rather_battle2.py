import pygame
import sys
import json
import os
import random
import math
import time

pygame.init()
pygame.mixer.init()
SAVE_FILE = "wyr_battle2_save.json"

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
GREEN = (50, 200, 80)
BLUE = (60, 120, 220)
YELLOW = (240, 220, 60)
ORANGE = (240, 160, 40)
PURPLE = (160, 60, 220)
GRAY = (120, 120, 120)
DARK_GRAY = (60, 60, 60)
LIGHT_GRAY = (180, 180, 180)
CYAN = (60, 220, 220)
PINK = (240, 120, 180)
BROWN = (139, 90, 43)
DARK_GREEN = (30, 100, 30)
SKY_BLUE = (135, 200, 235)
DARK_SKY = (40, 50, 80)
GOLD = (255, 215, 0)
MAGENTA = (255, 0, 255)

WIDTH, HEIGHT = 900, 600
GROUND_Y = HEIGHT - 40
FPS = 60
GRAVITY = 0.6

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Would You Rather Battle 2")
clock = pygame.time.Clock()

# Fonts
font_sm = pygame.font.SysFont("consolas", 16)
font_md = pygame.font.SysFont("consolas", 22, bold=True)
font_lg = pygame.font.SysFont("consolas", 36, bold=True)
font_xl = pygame.font.SysFont("consolas", 52, bold=True)
font_title = pygame.font.SysFont("consolas", 60, bold=True)

# ─── ABILITY DEFINITIONS ────────────────────────────────────────────────────
# Hand-crafted core abilities (54 base)
ABILITIES = {
    # ─── BASIC ────────────────────────────────────────────────────────────
    "Speed Boost": {"type": "basic", "desc": "Move 40% faster", "color": CYAN, "effect": {"speed_mult": 1.4}},
    "High Jump": {"type": "basic", "desc": "Jump 50% higher", "color": GREEN, "effect": {"jump_mult": 1.5}},
    "Rapid Fire": {"type": "basic", "desc": "Fire 50% faster", "color": RED, "effect": {"cooldown_mult": 0.5}},
    "Big Bullets": {"type": "basic", "desc": "Bullets 2x bigger", "color": ORANGE, "effect": {"bullet_size_mult": 2.0}},
    "Shield": {"type": "basic", "desc": "Block 1 hit", "color": BLUE, "effect": {"shield": 1}},
    "Double Shot": {"type": "basic", "desc": "Fire 2 bullets", "color": YELLOW, "effect": {"double_shot": True}},
    "Bullet Speed": {"type": "basic", "desc": "Bullets 60% faster", "color": PURPLE, "effect": {"bullet_speed_mult": 1.6}},
    "Tiny Target": {"type": "basic", "desc": "30% smaller", "color": PINK, "effect": {"size_mult": 0.7}},
    "Gravity Flip": {"type": "basic", "desc": "Lower gravity", "color": MAGENTA, "effect": {"gravity_mult": 0.5}},
    "Iron Skin": {"type": "basic", "desc": "Block 2 hits", "color": (160, 160, 170), "effect": {"shield": 2}},
    "Featherweight": {"type": "basic", "desc": "70% less gravity", "color": (220, 240, 255), "effect": {"gravity_mult": 0.3}},
    "Sprint": {"type": "basic", "desc": "Move 25% faster", "color": (100, 255, 200), "effect": {"speed_mult": 1.25}},
    "Mega Bullets": {"type": "basic", "desc": "Bullets 3x bigger", "color": (255, 100, 50), "effect": {"bullet_size_mult": 3.0}},
    "Quick Draw": {"type": "basic", "desc": "Fire 30% faster", "color": (255, 200, 100), "effect": {"cooldown_mult": 0.7}},
    "Bounce Boots": {"type": "basic", "desc": "Jump 30% higher", "color": (180, 100, 255), "effect": {"jump_mult": 1.3}},
    "Miniature": {"type": "basic", "desc": "50% smaller", "color": (255, 180, 220), "effect": {"size_mult": 0.5}},
    "Giant": {"type": "basic", "desc": "40% bigger + shield", "color": (100, 80, 60), "effect": {"size_mult": 1.4, "shield": 1}},
    "Laser Bolt": {"type": "basic", "desc": "Bullets 80% faster", "color": (0, 255, 180), "effect": {"bullet_speed_mult": 1.8}},
    "Triple Shot": {"type": "basic", "desc": "Double shot + smaller", "color": (255, 255, 100), "effect": {"double_shot": True, "bullet_size_mult": 0.8}},
    "Dash": {"type": "basic", "desc": "Move 60% faster", "color": (0, 200, 255), "effect": {"speed_mult": 1.6}},
    "Moon Gravity": {"type": "basic", "desc": "Very low gravity", "color": (200, 200, 230), "effect": {"gravity_mult": 0.25}},
    "Thick Shield": {"type": "basic", "desc": "Block 3 hits", "color": (80, 140, 255), "effect": {"shield": 3}},
    "Sniper Rounds": {"type": "basic", "desc": "2x fast + small bullets", "color": (180, 60, 60), "effect": {"bullet_speed_mult": 2.0, "bullet_size_mult": 0.6}},
    # ─── SPECIAL ──────────────────────────────────────────────────────────
    "Triple Boost": {"type": "special", "desc": "Fast+big+rapid bullets", "color": GOLD, "effect": {"bullet_speed_mult": 1.8, "bullet_size_mult": 1.5, "cooldown_mult": 0.6}},
    "Ghost Mode": {"type": "special", "desc": "Small+fast+low grav", "color": (200, 200, 255), "effect": {"size_mult": 0.6, "speed_mult": 1.3, "gravity_mult": 0.6}},
    "Tank Mode": {"type": "special", "desc": "Big bullets+shield+double", "color": (100, 100, 100), "effect": {"bullet_size_mult": 2.5, "shield": 2, "double_shot": True}},
    "Sniper Elite": {"type": "special", "desc": "Super fast bullets", "color": (180, 0, 0), "effect": {"bullet_speed_mult": 2.5, "cooldown_mult": 1.3}},
    "Ninja": {"type": "special", "desc": "Speed+jump+tiny+rapid", "color": (50, 50, 50), "effect": {"speed_mult": 1.5, "jump_mult": 1.4, "size_mult": 0.65, "cooldown_mult": 0.7}},
    "Berserker": {"type": "special", "desc": "Big+fast+rapid", "color": (200, 30, 30), "effect": {"size_mult": 1.2, "speed_mult": 1.3, "cooldown_mult": 0.4, "bullet_size_mult": 1.5}},
    "Astronaut": {"type": "special", "desc": "Zero grav+fast bullets", "color": (220, 220, 240), "effect": {"gravity_mult": 0.2, "bullet_speed_mult": 1.6, "size_mult": 0.7}},
    "Fortress": {"type": "special", "desc": "3 shields+big+slow", "color": (80, 80, 90), "effect": {"shield": 3, "size_mult": 1.3, "speed_mult": 0.7, "bullet_size_mult": 2.0}},
    "Blitz": {"type": "special", "desc": "Max speed+rapid+tiny", "color": (255, 255, 0), "effect": {"speed_mult": 1.8, "cooldown_mult": 0.35, "size_mult": 0.6}},
    "Juggernaut": {"type": "special", "desc": "4 shields+huge+slow", "color": (60, 60, 70), "effect": {"shield": 4, "size_mult": 1.5, "speed_mult": 0.5, "bullet_size_mult": 2.5}},
    "Storm Caller": {"type": "special", "desc": "Double+rapid+fast", "color": (100, 50, 200), "effect": {"double_shot": True, "cooldown_mult": 0.5, "bullet_speed_mult": 1.5}},
    "Shadow Step": {"type": "special", "desc": "Speed+tiny+low grav", "color": (40, 0, 60), "effect": {"speed_mult": 1.7, "size_mult": 0.5, "gravity_mult": 0.5}},
    "Cannon": {"type": "special", "desc": "Huge slow bullets+shield", "color": (80, 60, 40), "effect": {"bullet_size_mult": 3.5, "cooldown_mult": 1.8, "shield": 2}},
    "Phantom": {"type": "special", "desc": "Invisible size+fast", "color": (180, 180, 200), "effect": {"size_mult": 0.4, "speed_mult": 1.4, "gravity_mult": 0.6}},
    "Warlord": {"type": "special", "desc": "Shield+speed+big+jump", "color": (180, 140, 20), "effect": {"shield": 2, "speed_mult": 1.3, "bullet_size_mult": 1.8, "jump_mult": 1.3}},
    # ─── ANIMALS ──────────────────────────────────────────────────────────
    "Cat Form": {"type": "animal", "desc": "Speed + high jump", "color": (255, 180, 100), "effect": {"speed_mult": 1.3, "jump_mult": 1.4}, "animal": "cat", "body_color": (255, 180, 100), "ear_color": (255, 140, 60)},
    "Frog Form": {"type": "animal", "desc": "Super jump + tiny", "color": (80, 200, 80), "effect": {"jump_mult": 2.0, "size_mult": 0.75, "gravity_mult": 0.7}, "animal": "frog", "body_color": (80, 200, 80), "ear_color": (60, 160, 60)},
    "Bear Form": {"type": "animal", "desc": "Shield + big bullets", "color": (139, 90, 43), "effect": {"shield": 2, "bullet_size_mult": 1.8, "size_mult": 1.2}, "animal": "bear", "body_color": (139, 90, 43), "ear_color": (100, 60, 20)},
    "Eagle Form": {"type": "animal", "desc": "Low grav + bullet speed", "color": (200, 170, 100), "effect": {"gravity_mult": 0.35, "bullet_speed_mult": 1.5, "speed_mult": 1.2}, "animal": "eagle", "body_color": (200, 170, 100), "ear_color": (160, 130, 60)},
    "Wolf Form": {"type": "animal", "desc": "Speed + rapid fire", "color": (150, 150, 160), "effect": {"speed_mult": 1.5, "cooldown_mult": 0.6}, "animal": "wolf", "body_color": (150, 150, 160), "ear_color": (110, 110, 120)},
    "Fox Form": {"type": "animal", "desc": "Speed + double shot", "color": (230, 120, 30), "effect": {"speed_mult": 1.4, "double_shot": True}, "animal": "fox", "body_color": (230, 120, 30), "ear_color": (200, 90, 10)},
    "Rabbit Form": {"type": "animal", "desc": "Super jump + speed", "color": (240, 220, 210), "effect": {"jump_mult": 1.8, "speed_mult": 1.3}, "animal": "cat", "body_color": (240, 220, 210), "ear_color": (255, 180, 190)},
    "Snake Form": {"type": "animal", "desc": "Tiny + fast + rapid", "color": (80, 160, 60), "effect": {"size_mult": 0.5, "speed_mult": 1.3, "cooldown_mult": 0.7}, "animal": "frog", "body_color": (80, 160, 60), "ear_color": (60, 120, 40)},
    "Tiger Form": {"type": "animal", "desc": "Speed + big bullets", "color": (240, 160, 40), "effect": {"speed_mult": 1.4, "bullet_size_mult": 1.6}, "animal": "cat", "body_color": (240, 160, 40), "ear_color": (200, 120, 20)},
    "Owl Form": {"type": "animal", "desc": "Low grav + double shot", "color": (140, 100, 60), "effect": {"gravity_mult": 0.4, "double_shot": True}, "animal": "eagle", "body_color": (140, 100, 60), "ear_color": (100, 70, 40)},
    "Shark Form": {"type": "animal", "desc": "Fast bullets + shield", "color": (100, 130, 160), "effect": {"bullet_speed_mult": 1.6, "shield": 1}, "animal": "bear", "body_color": (100, 130, 160), "ear_color": (70, 100, 130)},
    "Hawk Form": {"type": "animal", "desc": "Speed + bullet speed", "color": (180, 130, 80), "effect": {"speed_mult": 1.3, "bullet_speed_mult": 1.5, "gravity_mult": 0.5}, "animal": "eagle", "body_color": (180, 130, 80), "ear_color": (140, 100, 50)},
    "Panda Form": {"type": "animal", "desc": "Shield + big", "color": (240, 240, 240), "effect": {"shield": 2, "size_mult": 1.2, "bullet_size_mult": 1.5}, "animal": "bear", "body_color": (240, 240, 240), "ear_color": (40, 40, 40)},
    "Cheetah Form": {"type": "animal", "desc": "Max speed + rapid", "color": (230, 200, 80), "effect": {"speed_mult": 1.8, "cooldown_mult": 0.5}, "animal": "cat", "body_color": (230, 200, 80), "ear_color": (180, 150, 40)},
    "Dragon Form": {"type": "animal", "desc": "Big+low grav+shield", "color": (200, 50, 50), "effect": {"bullet_size_mult": 2.0, "gravity_mult": 0.4, "shield": 1, "bullet_speed_mult": 1.3}, "animal": "eagle", "body_color": (200, 50, 50), "ear_color": (160, 30, 30)},
    "Phoenix Form": {"type": "animal", "desc": "Speed+rapid+shield", "color": (255, 120, 30), "effect": {"speed_mult": 1.4, "cooldown_mult": 0.6, "gravity_mult": 0.4, "shield": 1}, "animal": "eagle", "body_color": (255, 120, 30), "ear_color": (255, 80, 10)},
}

# ─── ABILITY GENERATOR (expands to 450+) ─────────────────────────────────────
def _generate_abilities():
    """Procedurally generate hundreds of additional abilities."""
    import itertools
    _SHORT = {"speed_mult":"Spd","jump_mult":"Jmp","cooldown_mult":"CD","bullet_speed_mult":"BSpd",
              "bullet_size_mult":"BSz","shield":"Shld","double_shot":"2xShot","gravity_mult":"Grav","size_mult":"Sz"}
    def _desc(eff):
        parts = []
        for k,v in eff.items():
            s = _SHORT.get(k, k)
            parts.append(s if isinstance(v, bool) else f"{s} {v}")
        return " | ".join(parts[:3])
    def _add(name, typ, color, eff, animal=None, bc=None, ec=None):
        if name not in ABILITIES:
            entry = {"type": typ, "desc": _desc(eff), "color": color, "effect": dict(eff)}
            if animal:
                entry.update({"animal": animal, "body_color": bc, "ear_color": ec})
            ABILITIES[name] = entry

    # ── 1. ELEMENTAL (20 elements x 10 mods = 200) ──
    elements = [
        ("Fire",(240,80,30)),("Ice",(100,200,255)),("Lightning",(255,255,80)),("Earth",(140,100,50)),
        ("Wind",(180,240,200)),("Water",(50,120,220)),("Dark",(60,20,80)),("Light",(255,255,220)),
        ("Poison",(120,200,40)),("Crystal",(200,180,255)),("Lava",(255,100,20)),("Frost",(180,220,255)),
        ("Thunder",(255,220,50)),("Shadow",(40,30,60)),("Holy",(255,240,180)),("Void",(30,10,50)),
        ("Plasma",(200,50,255)),("Steam",(200,200,210)),("Acid",(180,255,30)),("Arcane",(160,80,220)),
    ]
    mods = [
        ("Bolt",{"bullet_speed_mult":1.7}),("Shield",{"shield":2}),("Rush",{"speed_mult":1.5}),
        ("Leap",{"jump_mult":1.6}),("Burst",{"cooldown_mult":0.5,"bullet_size_mult":1.3}),
        ("Wave",{"bullet_size_mult":2.0,"bullet_speed_mult":1.2}),("Barrier",{"shield":1,"size_mult":0.8}),
        ("Storm",{"double_shot":True,"cooldown_mult":0.7}),("Surge",{"speed_mult":1.3,"bullet_speed_mult":1.4}),
        ("Blast",{"bullet_size_mult":2.5,"cooldown_mult":1.2}),
    ]
    for i,(en,ec) in enumerate(elements):
        for j,(mn,me) in enumerate(mods):
            c = tuple(min(255,max(0,v+(j*7-30))) for v in ec)
            _add(f"{en} {mn}", "elemental", c, me)

    # ── 2. MYTHICAL CREATURES (15) ──
    for nm,an,bc,ec,ef in [
        ("Unicorn","cat",(240,200,255),(200,160,240),{"speed_mult":1.5,"jump_mult":1.5,"gravity_mult":0.6}),
        ("Griffin","eagle",(200,180,120),(160,140,80),{"speed_mult":1.4,"gravity_mult":0.4,"bullet_speed_mult":1.4}),
        ("Kraken","bear",(40,80,120),(20,60,100),{"size_mult":1.4,"bullet_size_mult":2.0,"shield":2}),
        ("Hydra","frog",(60,120,80),(40,100,60),{"double_shot":True,"shield":2,"cooldown_mult":0.7}),
        ("Minotaur","bear",(140,80,40),(100,60,20),{"size_mult":1.5,"speed_mult":1.3,"shield":1}),
        ("Cerberus","wolf",(80,30,30),(60,20,20),{"cooldown_mult":0.4,"double_shot":True,"speed_mult":1.2}),
        ("Pegasus","eagle",(240,240,255),(200,200,240),{"gravity_mult":0.2,"speed_mult":1.6,"bullet_speed_mult":1.3}),
        ("Basilisk","frog",(100,130,50),(70,100,30),{"size_mult":0.6,"bullet_speed_mult":2.0,"cooldown_mult":0.8}),
        ("Sphinx","cat",(220,190,130),(180,150,90),{"speed_mult":1.3,"shield":2,"bullet_size_mult":1.5}),
        ("Chimera","bear",(180,100,60),(140,70,30),{"speed_mult":1.2,"double_shot":True,"bullet_size_mult":1.8}),
        ("Wyvern","eagle",(120,160,80),(80,130,50),{"gravity_mult":0.3,"bullet_speed_mult":1.8,"cooldown_mult":0.7}),
        ("Leviathan","bear",(30,60,100),(10,40,80),{"size_mult":1.6,"shield":3,"speed_mult":0.6}),
        ("Fenrir","wolf",(100,100,110),(70,70,80),{"speed_mult":1.7,"size_mult":1.2,"cooldown_mult":0.5}),
        ("Kitsune","fox",(255,160,80),(230,120,50),{"speed_mult":1.5,"double_shot":True,"size_mult":0.7}),
        ("Thunderbird","eagle",(255,230,60),(220,200,40),{"gravity_mult":0.25,"bullet_speed_mult":2.0,"speed_mult":1.3}),
    ]:
        _add(f"{nm} Form","animal",bc,ef,an,bc,ec)

    # ── 3. FOOD / DRINK (15) ──
    for nm,c,ef in [
        ("Pizza Power",(255,200,80),{"speed_mult":1.3,"shield":1}),
        ("Coffee Rush",(120,70,30),{"speed_mult":1.6,"cooldown_mult":0.6}),
        ("Candy Bomb",(255,100,200),{"bullet_size_mult":2.0,"bullet_speed_mult":1.3}),
        ("Chili Flame",(220,50,20),{"cooldown_mult":0.4,"bullet_speed_mult":1.5}),
        ("Banana Slip",(255,240,80),{"speed_mult":1.4,"size_mult":0.8}),
        ("Cookie Shield",(200,160,100),{"shield":2,"size_mult":1.1}),
        ("Soda Pop",(80,200,240),{"jump_mult":1.6,"speed_mult":1.2}),
        ("Donut Roll",(220,170,130),{"size_mult":1.3,"shield":1,"speed_mult":0.9}),
        ("Pepper Spray",(200,40,20),{"cooldown_mult":0.3,"bullet_size_mult":0.7}),
        ("Ice Cream Chill",(200,230,255),{"gravity_mult":0.5,"shield":1}),
        ("Honey Slow",(240,200,60),{"speed_mult":0.8,"shield":3,"size_mult":1.2}),
        ("Apple Juice",(180,255,100),{"speed_mult":1.2,"jump_mult":1.3}),
        ("Burger Tank",(180,120,60),{"size_mult":1.4,"shield":2,"speed_mult":0.7}),
        ("Smoothie Flow",(180,100,200),{"speed_mult":1.3,"gravity_mult":0.6}),
        ("Energy Drink",(0,255,100),{"speed_mult":1.5,"cooldown_mult":0.5,"jump_mult":1.3}),
    ]:
        _add(nm,"food",c,ef)

    # ── 4. SPACE (15) ──
    for nm,c,ef in [
        ("Meteor Strike",(200,100,40),{"bullet_size_mult":3.0,"bullet_speed_mult":1.5}),
        ("Zero-G",(180,180,200),{"gravity_mult":0.15,"speed_mult":1.1}),
        ("Nebula Cloud",(120,60,180),{"size_mult":0.6,"gravity_mult":0.4,"shield":1}),
        ("Solar Flare",(255,200,50),{"bullet_speed_mult":2.0,"cooldown_mult":0.6}),
        ("Black Hole",(20,10,30),{"bullet_size_mult":2.5,"gravity_mult":0.3}),
        ("Star Dust",(255,255,200),{"size_mult":0.7,"speed_mult":1.4,"double_shot":True}),
        ("Comet Tail",(100,180,255),{"speed_mult":1.6,"bullet_speed_mult":1.5}),
        ("Lunar Shield",(200,200,220),{"shield":3,"gravity_mult":0.4}),
        ("Rocket Boost",(255,100,50),{"speed_mult":1.7,"jump_mult":1.5}),
        ("Asteroid Belt",(140,130,120),{"shield":2,"bullet_size_mult":1.5}),
        ("Supernova",(255,220,100),{"bullet_size_mult":3.0,"cooldown_mult":0.5,"bullet_speed_mult":1.3}),
        ("Galaxy Spin",(100,50,200),{"speed_mult":1.3,"cooldown_mult":0.6,"double_shot":True}),
        ("Warp Drive",(0,200,200),{"speed_mult":2.0,"size_mult":0.6}),
        ("Satellite",(180,190,200),{"bullet_speed_mult":1.8,"shield":1}),
        ("Cosmos Ray",(200,150,255),{"bullet_speed_mult":2.2,"bullet_size_mult":0.5}),
    ]:
        _add(nm,"space",c,ef)

    # ── 5. WEATHER (10) ──
    for nm,c,ef in [
        ("Tornado",(160,200,180),{"speed_mult":1.7,"gravity_mult":0.4}),
        ("Hailstorm",(180,210,240),{"bullet_size_mult":1.5,"cooldown_mult":0.5,"double_shot":True}),
        ("Sunny Day",(255,240,100),{"speed_mult":1.3,"jump_mult":1.3}),
        ("Blizzard",(200,220,255),{"shield":2,"speed_mult":0.8,"bullet_size_mult":2.0}),
        ("Fog Bank",(180,180,180),{"size_mult":0.5,"speed_mult":1.2}),
        ("Rain Dance",(80,120,200),{"cooldown_mult":0.4,"gravity_mult":0.6}),
        ("Heat Wave",(255,150,50),{"speed_mult":1.4,"bullet_speed_mult":1.5}),
        ("Earthquake",(140,100,60),{"size_mult":1.4,"shield":2,"bullet_size_mult":2.0}),
        ("Hurricane",(100,160,180),{"speed_mult":1.6,"double_shot":True,"gravity_mult":0.5}),
        ("Rainbow",(255,180,200),{"speed_mult":1.2,"jump_mult":1.3,"shield":1,"gravity_mult":0.7}),
    ]:
        _add(nm,"weather",c,ef)

    # ── 6. MATERIALS / GEMS (15) ──
    for nm,c,ef in [
        ("Gold Armor",(255,215,0),{"shield":2,"speed_mult":0.85}),
        ("Diamond Shell",(185,242,255),{"shield":3,"size_mult":0.9}),
        ("Ruby Rage",(220,20,60),{"cooldown_mult":0.4,"bullet_speed_mult":1.5}),
        ("Emerald Eye",(0,200,80),{"bullet_speed_mult":1.8,"size_mult":0.8}),
        ("Sapphire Flow",(15,82,186),{"speed_mult":1.4,"gravity_mult":0.5}),
        ("Obsidian Edge",(40,30,50),{"bullet_speed_mult":2.0,"bullet_size_mult":0.7,"cooldown_mult":0.8}),
        ("Copper Wire",(184,115,51),{"speed_mult":1.3,"cooldown_mult":0.7}),
        ("Silver Lining",(192,192,200),{"shield":1,"speed_mult":1.2,"jump_mult":1.2}),
        ("Pearl Glow",(240,230,220),{"shield":1,"gravity_mult":0.5,"size_mult":0.8}),
        ("Titanium Plat",(180,180,190),{"shield":3,"speed_mult":0.7,"size_mult":1.3}),
        ("Bronze Wall",(205,127,50),{"shield":2,"bullet_size_mult":1.5}),
        ("Amethyst Aura",(153,102,204),{"gravity_mult":0.4,"double_shot":True}),
        ("Quartz Shard",(255,220,240),{"bullet_speed_mult":1.6,"bullet_size_mult":1.3}),
        ("Iron Fist",(105,105,105),{"bullet_size_mult":2.5,"speed_mult":0.9}),
        ("Jade Spirit",(0,168,107),{"speed_mult":1.3,"jump_mult":1.4,"gravity_mult":0.7}),
    ]:
        _add(nm,"material",c,ef)

    # ── 7. SPORTS (10) ──
    for nm,c,ef in [
        ("Soccer Kick",(255,255,255),{"bullet_speed_mult":1.8,"bullet_size_mult":1.5}),
        ("Basketball Dunk",(255,140,0),{"jump_mult":2.0,"size_mult":1.1}),
        ("Baseball Pitch",(255,50,50),{"bullet_speed_mult":2.2,"cooldown_mult":1.2}),
        ("Tennis Serve",(200,255,50),{"bullet_speed_mult":1.9,"bullet_size_mult":0.7}),
        ("Boxing Glove",(200,30,30),{"bullet_size_mult":2.5,"speed_mult":1.2}),
        ("Hockey Slapshot",(100,180,255),{"bullet_speed_mult":2.0,"shield":1}),
        ("Swimming Sprint",(50,150,255),{"speed_mult":1.5,"gravity_mult":0.6}),
        ("Ski Jump",(220,230,255),{"jump_mult":1.8,"gravity_mult":0.4}),
        ("Archery Focus",(100,60,20),{"bullet_speed_mult":2.5,"cooldown_mult":1.5}),
        ("Golf Drive",(50,180,50),{"bullet_speed_mult":1.7,"bullet_size_mult":0.8}),
    ]:
        _add(nm,"sport",c,ef)

    # ── 8. MUSIC (10) ──
    for nm,c,ef in [
        ("Bass Drop",(80,20,140),{"bullet_size_mult":2.5,"gravity_mult":0.5}),
        ("Drum Roll",(180,100,50),{"cooldown_mult":0.3,"bullet_size_mult":0.8}),
        ("Guitar Solo",(200,50,50),{"speed_mult":1.5,"cooldown_mult":0.6}),
        ("Piano Keys",(40,40,40),{"bullet_speed_mult":1.6,"double_shot":True}),
        ("Trumpet Blast",(255,200,50),{"bullet_speed_mult":1.8,"bullet_size_mult":1.5}),
        ("Violin Flow",(160,100,60),{"speed_mult":1.3,"gravity_mult":0.5}),
        ("DJ Spin",(255,0,255),{"speed_mult":1.4,"cooldown_mult":0.5,"double_shot":True}),
        ("Flute Breeze",(200,240,200),{"gravity_mult":0.3,"speed_mult":1.2}),
        ("Harp Angel",(255,230,200),{"gravity_mult":0.25,"shield":1,"jump_mult":1.5}),
        ("Beat Box",(60,60,60),{"cooldown_mult":0.4,"speed_mult":1.3}),
    ]:
        _add(nm,"music",c,ef)

    # ── 9. SEASONS / TIME (10) ──
    for nm,c,ef in [
        ("Spring Bloom",(200,255,150),{"speed_mult":1.3,"jump_mult":1.3,"gravity_mult":0.7}),
        ("Summer Heat",(255,180,50),{"speed_mult":1.5,"cooldown_mult":0.6}),
        ("Autumn Leaf",(200,130,50),{"shield":1,"bullet_size_mult":1.5,"speed_mult":1.1}),
        ("Winter Frost",(180,210,240),{"shield":2,"speed_mult":0.85,"bullet_speed_mult":1.3}),
        ("Dawn Light",(255,200,150),{"speed_mult":1.2,"gravity_mult":0.6,"shield":1}),
        ("Dusk Shadow",(80,50,100),{"size_mult":0.6,"speed_mult":1.4,"cooldown_mult":0.7}),
        ("Midnight",(20,10,40),{"size_mult":0.5,"speed_mult":1.5,"bullet_speed_mult":1.3}),
        ("High Noon",(255,240,100),{"bullet_speed_mult":2.0,"cooldown_mult":0.7}),
        ("Twilight Zone",(100,60,140),{"gravity_mult":0.3,"size_mult":0.7,"double_shot":True}),
        ("Equinox",(180,200,180),{"speed_mult":1.3,"jump_mult":1.3,"shield":1}),
    ]:
        _add(nm,"season",c,ef)

    # ── 10. COLORS (15) ──
    for nm,c,ef in [
        ("Red Rage",(255,30,30),{"cooldown_mult":0.4,"speed_mult":1.3}),
        ("Blue Zen",(30,80,255),{"shield":2,"gravity_mult":0.5}),
        ("Green Growth",(30,200,60),{"size_mult":1.3,"shield":1,"jump_mult":1.3}),
        ("Yellow Flash",(255,255,30),{"speed_mult":1.6,"bullet_speed_mult":1.5}),
        ("Purple Haze",(150,30,200),{"gravity_mult":0.4,"double_shot":True}),
        ("Orange Blaze",(255,140,20),{"cooldown_mult":0.5,"bullet_size_mult":1.8}),
        ("Pink Charm",(255,100,180),{"size_mult":0.6,"speed_mult":1.4}),
        ("White Flash",(250,250,250),{"bullet_speed_mult":2.0,"size_mult":0.8}),
        ("Black Void",(20,20,20),{"size_mult":0.4,"speed_mult":1.5,"gravity_mult":0.5}),
        ("Cyan Surge",(0,255,255),{"speed_mult":1.4,"bullet_speed_mult":1.4}),
        ("Magenta Pulse",(255,0,200),{"cooldown_mult":0.5,"double_shot":True}),
        ("Teal Wave",(0,180,180),{"speed_mult":1.3,"gravity_mult":0.6,"shield":1}),
        ("Indigo Dream",(75,0,130),{"gravity_mult":0.3,"bullet_speed_mult":1.6}),
        ("Coral Reef",(255,127,80),{"shield":1,"bullet_size_mult":1.5,"speed_mult":1.1}),
        ("Neon Glow",(180,255,0),{"speed_mult":1.5,"cooldown_mult":0.6,"bullet_speed_mult":1.3}),
    ]:
        _add(nm,"color",c,ef)

    # ── 11. MORE ANIMALS (20) ──
    for nm,an,bc,ec,ef in [
        ("Gorilla","bear",(80,70,60),(50,40,30),{"size_mult":1.4,"shield":2,"bullet_size_mult":1.5}),
        ("Dolphin","frog",(80,160,220),(50,130,190),{"speed_mult":1.5,"jump_mult":1.6,"gravity_mult":0.5}),
        ("Bat","eagle",(60,40,60),(40,20,40),{"gravity_mult":0.3,"speed_mult":1.3,"size_mult":0.7}),
        ("Scorpion","frog",(160,80,20),(130,50,10),{"bullet_speed_mult":1.8,"cooldown_mult":0.7,"size_mult":0.7}),
        ("Turtle","bear",(60,120,60),(40,90,40),{"shield":4,"speed_mult":0.5,"size_mult":1.2}),
        ("Falcon","eagle",(140,100,60),(100,70,30),{"speed_mult":1.6,"bullet_speed_mult":1.8,"gravity_mult":0.4}),
        ("Rhino","bear",(120,110,100),(90,80,70),{"size_mult":1.5,"speed_mult":1.3,"shield":1}),
        ("Chameleon","frog",(80,200,120),(50,170,90),{"size_mult":0.5,"shield":1,"speed_mult":1.1}),
        ("Deer","cat",(180,140,80),(140,100,50),{"speed_mult":1.5,"jump_mult":1.7,"size_mult":0.85}),
        ("Crocodile","bear",(60,100,50),(30,70,20),{"shield":2,"bullet_size_mult":2.0,"speed_mult":0.9}),
        ("Parrot","eagle",(255,80,80),(200,40,40),{"gravity_mult":0.4,"speed_mult":1.4,"size_mult":0.6}),
        ("Lion","cat",(220,180,80),(180,140,40),{"speed_mult":1.4,"size_mult":1.2,"shield":1,"bullet_size_mult":1.3}),
        ("Cobra","frog",(40,60,30),(20,40,10),{"bullet_speed_mult":2.0,"size_mult":0.5,"cooldown_mult":0.7}),
        ("Osprey","eagle",(160,140,120),(120,100,80),{"gravity_mult":0.3,"bullet_speed_mult":1.6,"speed_mult":1.2}),
        ("Lynx","cat",(180,160,140),(140,120,100),{"speed_mult":1.5,"jump_mult":1.5,"size_mult":0.8}),
        ("Hippo","bear",(140,120,130),(100,80,90),{"size_mult":1.5,"shield":3,"bullet_size_mult":1.8,"speed_mult":0.6}),
    ]:
        _add(f"{nm} Form","animal",bc,ef,an,bc,ec)

    # ── 12. TECH (15) ──
    for nm,c,ef in [
        ("Laser Sight",(255,0,0),{"bullet_speed_mult":2.2,"bullet_size_mult":0.5}),
        ("Jetpack",(255,120,30),{"gravity_mult":0.2,"speed_mult":1.3}),
        ("Mech Armor",(120,120,130),{"shield":3,"size_mult":1.3,"speed_mult":0.8}),
        ("EMP Burst",(100,200,255),{"cooldown_mult":0.4,"double_shot":True}),
        ("Nano Shield",(150,255,200),{"shield":2,"size_mult":0.8}),
        ("Turbo Engine",(255,50,0),{"speed_mult":1.8,"cooldown_mult":0.7}),
        ("Drone Strike",(160,160,170),{"double_shot":True,"bullet_speed_mult":1.5}),
        ("Hologram",(100,200,255),{"size_mult":0.5,"gravity_mult":0.5}),
        ("Power Suit",(200,180,50),{"shield":2,"speed_mult":1.2,"bullet_size_mult":1.5}),
        ("Cyber Eye",(0,255,200),{"bullet_speed_mult":1.8,"cooldown_mult":0.8}),
        ("Force Field",(100,150,255),{"shield":4,"speed_mult":0.7}),
        ("Rail Gun",(80,80,90),{"bullet_speed_mult":3.0,"cooldown_mult":2.0,"bullet_size_mult":0.6}),
        ("Grapple Hook",(140,100,60),{"speed_mult":1.4,"jump_mult":1.6}),
        ("Plasma Core",(200,50,255),{"bullet_speed_mult":1.6,"bullet_size_mult":1.8}),
        ("Stealth Cloak",(60,60,70),{"size_mult":0.4,"speed_mult":1.3}),
    ]:
        _add(nm,"tech",c,ef)

    # ── 13. EMOTIONS (10) ──
    for nm,c,ef in [
        ("Courage",(255,200,50),{"speed_mult":1.4,"shield":1,"jump_mult":1.3}),
        ("Fury",(255,30,0),{"cooldown_mult":0.3,"speed_mult":1.3,"bullet_size_mult":1.5}),
        ("Calm",(100,180,220),{"shield":2,"gravity_mult":0.5}),
        ("Joy",(255,220,100),{"speed_mult":1.5,"jump_mult":1.4}),
        ("Fear",(80,40,80),{"speed_mult":1.6,"size_mult":0.6}),
        ("Hope",(255,255,200),{"shield":1,"speed_mult":1.2,"bullet_speed_mult":1.3}),
        ("Patience",(140,180,160),{"shield":3,"bullet_speed_mult":1.5}),
        ("Determination",(255,100,0),{"speed_mult":1.3,"cooldown_mult":0.5,"shield":1}),
        ("Serenity",(180,220,240),{"gravity_mult":0.3,"shield":2}),
        ("Chaos",(200,0,100),{"cooldown_mult":0.3,"double_shot":True,"bullet_size_mult":1.5}),
    ]:
        _add(nm,"emotion",c,ef)

    # ── 14. NATURE (10) ──
    for nm,c,ef in [
        ("Oak Strength",(100,80,40),{"shield":2,"size_mult":1.3}),
        ("Vine Whip",(60,160,40),{"bullet_speed_mult":1.5,"cooldown_mult":0.6}),
        ("Petal Storm",(255,180,200),{"double_shot":True,"speed_mult":1.2}),
        ("Thorn Armor",(100,140,60),{"shield":2,"bullet_size_mult":1.5}),
        ("Seed Burst",(140,180,60),{"cooldown_mult":0.5,"bullet_size_mult":1.3}),
        ("Moss Shield",(80,140,60),{"shield":3,"speed_mult":0.9}),
        ("River Flow",(80,140,200),{"speed_mult":1.4,"gravity_mult":0.6}),
        ("Mountain Wall",(140,130,120),{"shield":3,"size_mult":1.4,"speed_mult":0.6}),
        ("Forest Sprint",(40,120,40),{"speed_mult":1.5,"size_mult":0.8}),
        ("Mushroom Bounce",(200,80,80),{"jump_mult":2.0,"size_mult":0.7}),
    ]:
        _add(nm,"nature",c,ef)

    # ── 15. MAGIC SPELLS (15) ──
    for nm,c,ef in [
        ("Fireball",(255,80,20),{"bullet_size_mult":2.0,"bullet_speed_mult":1.5}),
        ("Frost Nova",(160,220,255),{"shield":1,"speed_mult":0.9,"bullet_size_mult":2.5}),
        ("Chain Lightning",(255,255,120),{"double_shot":True,"bullet_speed_mult":1.7}),
        ("Healing Aura",(100,255,150),{"shield":2,"size_mult":0.9}),
        ("Blink",(180,100,255),{"speed_mult":1.8,"size_mult":0.6}),
        ("Meteor Shower",(240,120,40),{"bullet_size_mult":2.5,"cooldown_mult":0.5}),
        ("Ice Wall",(150,200,255),{"shield":3,"speed_mult":0.7}),
        ("Thunderclap",(255,240,60),{"bullet_speed_mult":2.0,"bullet_size_mult":1.5}),
        ("Arcane Missile",(180,80,240),{"cooldown_mult":0.4,"bullet_speed_mult":1.6}),
        ("Divine Shield",(255,255,180),{"shield":4,"speed_mult":0.6}),
        ("Shadow Bolt",(60,20,100),{"bullet_speed_mult":1.9,"size_mult":0.7}),
        ("Nature's Wrath",(80,200,40),{"speed_mult":1.3,"bullet_size_mult":1.8,"jump_mult":1.3}),
        ("Polymorph",(255,150,255),{"size_mult":0.5,"speed_mult":1.5,"jump_mult":1.5}),
        ("Time Warp",(200,200,100),{"cooldown_mult":0.3,"speed_mult":1.4}),
        ("Soul Drain",(100,30,60),{"shield":1,"cooldown_mult":0.6,"bullet_speed_mult":1.4}),
    ]:
        _add(nm,"magic",c,ef)

    # ── 16. NINJA / MARTIAL ARTS (10) ──
    for nm,c,ef in [
        ("Shuriken Throw",(160,160,160),{"cooldown_mult":0.4,"bullet_speed_mult":1.6,"bullet_size_mult":0.7}),
        ("Katana Slash",(200,200,210),{"speed_mult":1.5,"bullet_size_mult":1.8}),
        ("Shadow Clone",(40,40,50),{"double_shot":True,"size_mult":0.7}),
        ("Chi Blast",(255,200,100),{"bullet_speed_mult":1.8,"bullet_size_mult":1.5}),
        ("Iron Palm",(140,120,100),{"bullet_size_mult":2.5,"shield":1}),
        ("Dragon Kick",(200,80,30),{"speed_mult":1.6,"jump_mult":1.6}),
        ("Smoke Bomb",(120,120,130),{"size_mult":0.4,"speed_mult":1.3,"gravity_mult":0.6}),
        ("Tai Chi",(180,200,180),{"shield":2,"gravity_mult":0.5,"speed_mult":1.1}),
        ("Pressure Point",(200,50,50),{"bullet_speed_mult":2.2,"cooldown_mult":1.3}),
        ("Wind Step",(200,240,220),{"speed_mult":1.7,"gravity_mult":0.4}),
    ]:
        _add(nm,"martial",c,ef)

    # ── 17. PIRATE / OCEAN (10) ──
    for nm,c,ef in [
        ("Cannon Ball",(80,60,40),{"bullet_size_mult":3.0,"cooldown_mult":1.5}),
        ("Sea Legs",(60,120,180),{"speed_mult":1.3,"gravity_mult":0.6,"jump_mult":1.3}),
        ("Kraken Ink",(30,20,50),{"size_mult":0.5,"cooldown_mult":0.5}),
        ("Treasure Shield",(255,215,0),{"shield":3,"speed_mult":0.8}),
        ("Anchor Drop",(100,100,110),{"bullet_size_mult":2.5,"gravity_mult":1.5}),
        ("Parrot Shot",(255,80,40),{"double_shot":True,"bullet_speed_mult":1.4}),
        ("Tidal Wave",(40,100,200),{"bullet_size_mult":2.0,"speed_mult":1.3}),
        ("Plank Walk",(160,120,60),{"speed_mult":1.5,"size_mult":0.8}),
        ("Rum Barrel",(200,100,40),{"shield":2,"size_mult":1.3}),
        ("Compass Rose",(220,200,150),{"speed_mult":1.4,"bullet_speed_mult":1.4}),
    ]:
        _add(nm,"pirate",c,ef)

    # ── 18. CANDY / SWEET (10) ──
    for nm,c,ef in [
        ("Gummy Bear",(255,100,100),{"shield":2,"size_mult":1.2}),
        ("Lollipop Spin",(255,50,200),{"cooldown_mult":0.5,"speed_mult":1.3}),
        ("Chocolate Armor",(100,60,30),{"shield":3,"speed_mult":0.85}),
        ("Cotton Candy Float",(255,180,255),{"gravity_mult":0.3,"size_mult":0.8}),
        ("Jawbreaker",(200,200,200),{"bullet_size_mult":2.5,"bullet_speed_mult":1.3}),
        ("Sour Burst",(200,255,50),{"cooldown_mult":0.4,"bullet_speed_mult":1.5}),
        ("Mint Chill",(150,255,200),{"speed_mult":1.3,"gravity_mult":0.5}),
        ("Caramel Stick",(200,150,60),{"speed_mult":0.8,"shield":2,"bullet_size_mult":1.8}),
        ("Bubblegum Pop",(255,150,200),{"jump_mult":1.7,"size_mult":0.8}),
        ("Licorice Whip",(30,30,30),{"bullet_speed_mult":1.7,"cooldown_mult":0.7}),
    ]:
        _add(nm,"candy",c,ef)

    # ── 19. DINOSAUR FORMS (10) ──
    for nm,an,bc,ec,ef in [
        ("T-Rex","bear",(100,80,40),(70,50,20),{"size_mult":1.5,"bullet_size_mult":2.0,"speed_mult":0.8}),
        ("Raptor","cat",(80,120,60),(50,90,30),{"speed_mult":1.8,"cooldown_mult":0.5,"size_mult":0.7}),
        ("Pterodactyl","eagle",(160,140,100),(120,100,60),{"gravity_mult":0.2,"speed_mult":1.5}),
        ("Stegosaurus","bear",(120,100,80),(90,70,50),{"shield":3,"bullet_size_mult":1.5,"speed_mult":0.7}),
        ("Triceratops","bear",(140,130,100),(110,100,70),{"shield":2,"speed_mult":1.2,"size_mult":1.3}),
        ("Ankylosaurus","bear",(100,90,60),(70,60,30),{"shield":4,"speed_mult":0.5,"size_mult":1.4}),
        ("Velociraptor","cat",(100,140,80),(70,110,50),{"speed_mult":1.7,"cooldown_mult":0.4,"size_mult":0.6}),
        ("Brachiosaurus","bear",(140,160,120),(110,130,90),{"size_mult":1.6,"jump_mult":1.5,"shield":1}),
        ("Spinosaurus","frog",(80,100,120),(50,70,90),{"bullet_size_mult":2.0,"speed_mult":1.3,"shield":1}),
        ("Archaeopteryx","eagle",(180,160,100),(140,120,60),{"gravity_mult":0.3,"speed_mult":1.4,"double_shot":True}),
    ]:
        _add(f"{nm} Form","animal",bc,ef,an,bc,ec)

    # ── 20. INSECT FORMS (5) ──
    for nm,an,bc,ec,ef in [
        ("Beetle","bear",(60,80,40),(30,50,10),{"shield":3,"size_mult":0.8,"speed_mult":1.1}),
        ("Dragonfly","eagle",(100,200,150),(70,170,120),{"speed_mult":1.6,"gravity_mult":0.3}),
        ("Ant","frog",(80,40,20),(50,20,5),{"size_mult":0.4,"speed_mult":1.4,"shield":1}),
        ("Firefly","eagle",(255,255,100),(220,220,60),{"gravity_mult":0.35,"double_shot":True,"size_mult":0.7}),
        ("Hornet","fox",(255,200,0),(220,170,0),{"speed_mult":1.5,"cooldown_mult":0.5,"bullet_speed_mult":1.4}),
    ]:
        _add(f"{nm} Form","animal",bc,ef,an,bc,ec)

_generate_abilities()

# ─── LEVEL HELPERS (merge 3 of the same → next level) ────────────────────────
import re as _re
_LV_RE = _re.compile(r'^(.+?)\s+Lv(\d+)$')

def get_base_name(item_name):
    """Return the base ability name without level suffix."""
    m = _LV_RE.match(item_name)
    return m.group(1) if m else item_name

def get_level(item_name):
    """Return the level of an inventory item (base = 1)."""
    m = _LV_RE.match(item_name)
    return int(m.group(2)) if m else 1

def make_leveled_name(base, level):
    """Build an item name for a given level. Level 1 = base name, 2+ = 'Name Lv2'."""
    return base if level <= 1 else f"{base} Lv{level}"

def get_ability_data(item_name):
    """Look up the base ABILITIES entry and return (base_dict, level).
    Effects are scaled by level when applied."""
    base = get_base_name(item_name)
    lv = get_level(item_name)
    ab = ABILITIES.get(base)
    return ab, lv

print(f"[WYR Battle 2] Loaded {len(ABILITIES)} abilities!")


# ─── COURSE / LEVEL GENERATION ──────────────────────────────────────────────
def generate_course(wave):
    """Generate platforms and obstacles for the course."""
    platforms = []
    # Ground
    platforms.append(pygame.Rect(0, GROUND_Y, WIDTH, 60))

    # Base platforms that always exist
    platforms.append(pygame.Rect(100, GROUND_Y - 100, 160, 20))
    platforms.append(pygame.Rect(350, GROUND_Y - 160, 160, 20))
    platforms.append(pygame.Rect(620, GROUND_Y - 110, 160, 20))

    # More platforms based on wave
    if wave >= 2:
        platforms.append(pygame.Rect(200, GROUND_Y - 260, 120, 18))
    if wave >= 3:
        platforms.append(pygame.Rect(500, GROUND_Y - 240, 140, 18))
        platforms.append(pygame.Rect(50, GROUND_Y - 200, 100, 18))
    if wave >= 5:
        platforms.append(pygame.Rect(700, GROUND_Y - 280, 130, 18))
        platforms.append(pygame.Rect(300, GROUND_Y - 340, 100, 18))
    if wave >= 8:
        platforms.append(pygame.Rect(150, GROUND_Y - 380, 90, 16))
        platforms.append(pygame.Rect(550, GROUND_Y - 360, 110, 16))
    if wave >= 10:
        platforms.append(pygame.Rect(400, GROUND_Y - 420, 100, 16))

    # Walls / obstacles
    walls = []
    if wave >= 2:
        walls.append(pygame.Rect(440, GROUND_Y - 80, 20, 80))
    if wave >= 4:
        walls.append(pygame.Rect(250, GROUND_Y - 60, 20, 60))
        walls.append(pygame.Rect(650, GROUND_Y - 70, 20, 70))
    if wave >= 7:
        walls.append(pygame.Rect(150, GROUND_Y - 50, 20, 50))

    return platforms, walls


# ─── SAVE / LOAD ─────────────────────────────────────────────────────────────
def save_game(data):
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)


AI_NAMES = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta", "Iota", "Kappa"]
AI_COLORS = [RED, CYAN, GREEN, ORANGE, PINK, PURPLE, GOLD, MAGENTA, (100,255,200), (255,150,80)]
AI_TYPES = ["offline", "fighter"]  # offline = farms loot, fighter = helps in battle

def _default_ai():
    """Return a default AI companion dict."""
    return {"name": "Alpha", "type": "offline", "equipped": [], "inventory": [],
            "slots": 2, "wins": 0, "last_collect": 0.0,
            "last_hour_reset": 0.0, "collected_this_hour": 0,
            "brain": {"chat_log": [], "mods": [], "code_count": 0, "personality": "helpful",
                      "school": {"level": 0, "skills": [], "xp": 0}}}

def _migrate_ai(data):
    """Migrate old single-AI save to new multi-AI format."""
    if "ai_team" not in data:
        # Build first AI from old keys
        ai0 = _default_ai()
        ai0["name"] = "Alpha"
        ai0["type"] = "offline"
        ai0["equipped"] = data.pop("ai_equipped", [])
        ai0["inventory"] = data.pop("ai_inventory", [])
        ai0["slots"] = data.pop("ai_slots", 2)
        ai0["wins"] = data.pop("ai_wins", 0)
        ai0["last_collect"] = data.pop("ai_last_collect", 0.0)
        ai0["last_hour_reset"] = data.pop("ai_last_hour_reset", 0.0)
        ai0["collected_this_hour"] = data.pop("ai_collected_this_hour", 0)
        data["ai_team"] = [ai0]
        # Shared parts stay as ai_parts
        data.setdefault("ai_parts", [])
        # Clean up old keys
        for old_key in ["ai_loot", "ai_equipped", "ai_inventory", "ai_slots",
                        "ai_wins", "ai_last_collect", "ai_last_hour_reset", "ai_collected_this_hour"]:
            data.pop(old_key, None)
    # Ensure new fields
    data.setdefault("ai_parts", [])
    data.setdefault("ai_team", [_default_ai()])
    data.setdefault("total_waves", data.get("wins", 0))  # track total waves for unlock requirements
    data.setdefault("ai_chat_log", [])
    for ai in data["ai_team"]:
        ai.setdefault("type", "offline")
        ai.setdefault("name", "Alpha")
        ai.setdefault("equipped", [])
        ai.setdefault("inventory", [])
        ai.setdefault("slots", 2)
        ai.setdefault("wins", 0)
        ai.setdefault("last_collect", 0.0)
        ai.setdefault("last_hour_reset", 0.0)
        ai.setdefault("collected_this_hour", 0)
        ai.setdefault("brain", {"chat_log": [], "mods": [], "code_count": 0, "personality": "helpful"})
        brain = ai["brain"]
        brain.setdefault("chat_log", [])
        brain.setdefault("mods", [])
        brain.setdefault("code_count", 0)
        brain.setdefault("personality", "helpful")
        brain.setdefault("school", {"level": 0, "skills": [], "xp": 0})
        school = brain["school"]
        school.setdefault("level", 0)
        school.setdefault("skills", [])
        school.setdefault("xp", 0)


def load_game():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
            defaults = {"wave": 1, "equipped": [], "inventory": [],
                        "slots": 2, "wins": 0, "rounds_since_part": 0,
                        "ai_parts": [], "total_waves": 0, "ai_chat_log": []}
            for k, v in defaults.items():
                if k not in data:
                    data[k] = v
            _migrate_ai(data)
            return data
    base = {"wave": 1, "equipped": [], "inventory": [], "slots": 2, "wins": 0,
            "rounds_since_part": 0, "ai_parts": [], "total_waves": 0, "ai_chat_log": []}
    base["ai_team"] = [_default_ai()]
    return base


# ─── PARTICLE SYSTEM ─────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color, vx=0, vy=0, life=30, size=4):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx + random.uniform(-1.5, 1.5)
        self.vy = vy + random.uniform(-2, 0.5)
        self.life = life
        self.max_life = life
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1
        self.life -= 1

    def draw(self, surf):
        alpha = max(0, self.life / self.max_life)
        r = max(1, int(self.size * alpha))
        c = tuple(int(ch * alpha) for ch in self.color)
        pygame.draw.circle(surf, c, (int(self.x), int(self.y)), r)


particles = []


def spawn_particles(x, y, color, count=10, spread=3, life=25, size=4):
    for _ in range(count):
        particles.append(Particle(x, y, color,
                                  vx=random.uniform(-spread, spread),
                                  vy=random.uniform(-spread, 1),
                                  life=life, size=size))


# ─── BULLET ──────────────────────────────────────────────────────────────────
class Bullet:
    def __init__(self, x, y, vx, vy=0, size=8, color=YELLOW, owner="player"):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.color = color
        self.alive = True
        self.owner = owner

    def update(self, platforms, walls):
        self.x += self.vx
        self.y += self.vy
        # Out of bounds
        if self.x < -50 or self.x > WIDTH + 50 or self.y < -50 or self.y > HEIGHT + 50:
            self.alive = False
        # Hit walls
        rect = pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)
        for w in walls:
            if rect.colliderect(w):
                self.alive = False
                spawn_particles(self.x, self.y, self.color, count=5, life=15, size=3)
                break

    def draw(self, surf):
        s = int(self.size)
        pygame.draw.rect(surf, self.color,
                         (int(self.x) - s, int(self.y) - s, s * 2, s * 2))
        # Glow
        glow_surf = pygame.Surface((s * 4, s * 4), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*self.color, 60),
                         (0, 0, s * 4, s * 4))
        surf.blit(glow_surf, (int(self.x) - s * 2, int(self.y) - s * 2))

    def get_rect(self):
        s = int(self.size)
        return pygame.Rect(int(self.x) - s, int(self.y) - s, s * 2, s * 2)


# ─── FIGHTER (Player / AI) ──────────────────────────────────────────────────
class Fighter:
    def __init__(self, x, y, is_ai=False):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.base_w = 30
        self.base_h = 40
        self.w = self.base_w
        self.h = self.base_h
        self.is_ai = is_ai
        self.on_ground = False
        self.facing = 1  # 1=right, -1=left
        self.alive = True

        # Stats
        self.speed = 4.5
        self.jump_power = -13.5
        self.fire_cooldown = 0
        self.fire_cooldown_max = 25
        self.bullet_speed = 8
        self.bullet_size = 8
        self.double_shot = False
        self.shield = 0
        self.gravity_mult = 1.0
        self.size_mult = 1.0

        # Special ability (S key)
        self.special_cooldown = 0
        self.special_cooldown_max = 300  # ~5 seconds at 60fps
        self.special_ready = True

        # Appearance
        self.body_color = BLUE if not is_ai else RED
        self.ear_color = None
        self.animal = None
        self.hat_color = None

        # AI state
        self.ai_timer = 0
        self.ai_dir = 1
        self.ai_jump_timer = 0

    def apply_abilities(self, equipped_names):
        """Apply ability effects. Supports leveled items like 'Speed Boost Lv3'."""
        # Reset to base
        self.speed = 4.5
        self.jump_power = -13.5
        self.fire_cooldown_max = 25
        self.bullet_speed = 8
        self.bullet_size = 8
        self.double_shot = False
        self.shield = 0
        self.gravity_mult = 1.0
        self.size_mult = 1.0
        self.animal = None
        self.ear_color = None
        if not self.is_ai:
            self.body_color = BLUE

        for name in equipped_names:
            ab, lv = get_ability_data(name)
            if ab is None:
                continue
            eff = ab["effect"]
            # Level scaling: each level-up triples the stat bonus
            # Lv1=1x, Lv2=3x, Lv3=9x, Lv4=27x ...
            lvf = 3 ** (lv - 1)
            if "speed_mult" in eff:
                scaled = 1.0 + (eff["speed_mult"] - 1.0) * lvf
                self.speed *= scaled
            if "jump_mult" in eff:
                scaled = 1.0 + (eff["jump_mult"] - 1.0) * lvf
                self.jump_power *= scaled
            if "cooldown_mult" in eff:
                if eff["cooldown_mult"] < 1:
                    scaled = 1.0 - (1.0 - eff["cooldown_mult"]) * lvf
                    scaled = max(0.1, scaled)
                else:
                    scaled = 1.0 + (eff["cooldown_mult"] - 1.0) * lvf
                self.fire_cooldown_max = max(3, int(self.fire_cooldown_max * scaled))
            if "bullet_speed_mult" in eff:
                scaled = 1.0 + (eff["bullet_speed_mult"] - 1.0) * lvf
                self.bullet_speed *= scaled
            if "bullet_size_mult" in eff:
                scaled = 1.0 + (eff["bullet_size_mult"] - 1.0) * lvf
                self.bullet_size = max(2, int(self.bullet_size * scaled))
            if "double_shot" in eff:
                self.double_shot = True
            if "shield" in eff:
                self.shield += eff["shield"] * lvf
            if "gravity_mult" in eff:
                scaled = 1.0 - (1.0 - eff["gravity_mult"]) * min(lvf, 9)
                scaled = max(0.05, scaled)
                self.gravity_mult *= scaled
            if "size_mult" in eff:
                if eff["size_mult"] < 1:
                    scaled = 1.0 - (1.0 - eff["size_mult"]) * min(lvf, 9)
                    scaled = max(0.2, scaled)
                else:
                    scaled = 1.0 + (eff["size_mult"] - 1.0) * lvf
                self.size_mult *= scaled
            if "animal" in ab:
                self.animal = ab["animal"]
                self.body_color = ab["body_color"]
                self.ear_color = ab["ear_color"]

        self.w = max(16, int(self.base_w * self.size_mult))
        self.h = max(20, int(self.base_h * self.size_mult))

        # Clamp extreme values to prevent AI/player from breaking physics
        self.gravity_mult = max(0.15, self.gravity_mult)  # prevent near-zero gravity
        self.speed = min(self.speed, 15)  # cap max speed

    def update(self, keys, platforms, walls):
        if not self.alive:
            return

        if not self.is_ai:
            # Player controls
            self.vx = 0
            if keys[pygame.K_a]:
                self.vx = -self.speed
                self.facing = -1
            if keys[pygame.K_d]:
                self.vx = self.speed
                self.facing = 1
            if keys[pygame.K_SPACE] and self.on_ground:
                self.vy = self.jump_power
                self.on_ground = False
                spawn_particles(self.x + self.w // 2, self.y + self.h,
                                LIGHT_GRAY, count=6, spread=2, life=15, size=3)

        # Apply gravity
        self.vy += GRAVITY * self.gravity_mult
        if self.vy > 12:
            self.vy = 12  # cap fall speed to prevent tunneling through platforms

        # Move X (only collide with walls, not platforms — platforms are horizontal)
        old_x = self.x
        self.x += self.vx
        my_rect = pygame.Rect(self.x, self.y, self.w, self.h)
        for w in walls:
            if my_rect.colliderect(w):
                if self.vx > 0:
                    self.x = w.left - self.w
                elif self.vx < 0:
                    self.x = w.right
                else:
                    overlap_left = (self.x + self.w) - w.left
                    overlap_right = w.right - self.x
                    if overlap_left < overlap_right:
                        self.x = w.left - self.w
                    else:
                        self.x = w.right
                my_rect = pygame.Rect(self.x, self.y, self.w, self.h)

        # Clamp to screen
        self.x = max(0, min(self.x, WIDTH - self.w))

        # Move Y — use sub-steps to avoid tunneling through thin platforms
        old_y = self.y
        self.on_ground = False
        steps = max(1, int(abs(self.vy) / 8) + 1)  # subdivide if falling fast
        step_vy = self.vy / steps
        for _step in range(steps):
            self.y += step_vy
            my_rect = pygame.Rect(self.x, self.y, self.w, self.h)
            landed = False
            for p in platforms:
                if my_rect.colliderect(p):
                    if self.vy >= 0:
                        # Landing on top
                        self.y = p.top - self.h
                        self.vy = 0
                        self.on_ground = True
                        landed = True
                    elif self.vy < 0:
                        # Hit head on bottom
                        self.y = p.bottom
                        self.vy = 0
                    my_rect = pygame.Rect(self.x, self.y, self.w, self.h)
            for w in walls:
                if my_rect.colliderect(w):
                    if self.vy >= 0:
                        self.y = w.top - self.h
                        self.vy = 0
                        self.on_ground = True
                        landed = True
                    elif self.vy < 0:
                        self.y = w.bottom
                        self.vy = 0
            if landed:
                break

        # Safety net: keep within screen bounds
        if self.y + self.h > GROUND_Y:
            self.y = GROUND_Y - self.h
            self.vy = 0
            self.on_ground = True
        if self.y < -self.h:
            self.y = -self.h + 1
            self.vy = 1  # push back down
        self.x = max(0, min(self.x, WIDTH - self.w))

        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        if self.special_cooldown > 0:
            self.special_cooldown -= 1
            self.special_ready = False
        else:
            self.special_ready = True

    def use_special(self):
        """Activate special ability — fires a burst of bullets in 8 directions + brief shield."""
        if self.special_cooldown > 0 or not self.alive:
            return []
        bullets = []
        cx = self.x + self.w // 2
        cy = self.y + self.h // 2
        # 8-direction burst
        for angle_deg in range(0, 360, 45):
            angle = math.radians(angle_deg)
            bvx = math.cos(angle) * self.bullet_speed * 1.3
            bvy = math.sin(angle) * self.bullet_speed * 1.3
            bullets.append(Bullet(cx, cy, bvx, bvy, size=int(self.bullet_size * 1.5),
                                  color=MAGENTA, owner="player"))
        # Bonus: grant +1 temporary shield
        self.shield += 1
        self.special_cooldown = self.special_cooldown_max
        self.special_ready = False
        # Big particle burst
        spawn_particles(cx, cy, MAGENTA, count=25, spread=5, life=25, size=5)
        spawn_particles(cx, cy, GOLD, count=15, spread=3, life=20, size=4)
        return bullets

    def ai_update(self, player, platforms, walls, wave, player_bullets=None):
        """AI behavior - gets smarter at dodging each wave, not overwhelmingly fast."""
        if not self.alive:
            return []

        bullets = []
        # Gentle speed scaling: caps at ~1.3x
        ai_speed_mult = 1.0 + min(wave * 0.03, 0.3)
        # Gentle fire rate scaling: caps at 0.7x cooldown
        ai_fire_mult = max(0.7, 1.0 - wave * 0.02)

        self.ai_timer += 1
        self.ai_jump_timer += 1

        # ── DODGE LOGIC: react to incoming player bullets ──
        dodging = False
        dodge_chance = min(0.6, 0.15 + wave * 0.03)  # gets better at dodging per wave
        if player_bullets:
            for b in player_bullets:
                if not b.alive or b.owner != "player":
                    continue
                # Check if bullet is heading roughly toward AI
                bx_dist = b.x - (self.x + self.w // 2)
                by_dist = b.y - (self.y + self.h // 2)
                dist = math.sqrt(bx_dist ** 2 + by_dist ** 2)
                if dist < 180:  # bullet is close
                    # Check if bullet is approaching
                    approaching = (b.vx > 0 and bx_dist < 0) or (b.vx < 0 and bx_dist > 0)
                    if approaching and random.random() < dodge_chance:
                        dodging = True
                        # Dodge perpendicular to bullet direction
                        if by_dist > 0:  # bullet above, jump
                            if self.on_ground:
                                self.vy = self.jump_power
                                self.on_ground = False
                                self.ai_jump_timer = 0
                        # Dodge sideways
                        if b.vy >= 0:  # bullet going down or flat, move sideways
                            self.vx = self.speed * ai_speed_mult * (1 if bx_dist < 0 else -1)
                            self.facing = 1 if self.vx > 0 else -1
                        break

        # ── NORMAL MOVEMENT (if not dodging) ──
        if not dodging:
            dx = player.x - self.x
            dy = player.y - self.y

            if abs(dx) > 60:
                if dx > 0:
                    self.vx = self.speed * ai_speed_mult * 0.8
                    self.facing = 1
                else:
                    self.vx = -self.speed * ai_speed_mult * 0.8
                    self.facing = -1
            else:
                # Strafe randomly
                if self.ai_timer % max(30, 55 - wave) == 0:
                    self.ai_dir = random.choice([-1, 1])
                self.vx = self.ai_dir * self.speed * ai_speed_mult * 0.5
                self.facing = self.ai_dir

            # Jump when player is above or randomly
            if (dy < -50 and self.on_ground) or \
               (self.ai_jump_timer > max(50, 80 - wave * 2) and self.on_ground and random.random() < 0.3):
                self.vy = self.jump_power
                self.on_ground = False
                self.ai_jump_timer = 0

        # ── FIRE at player ──
        effective_cd = max(12, int(self.fire_cooldown_max * ai_fire_mult))
        if self.fire_cooldown <= 0 and random.random() < 0.5:
            cx = self.x + self.w // 2
            cy = self.y + self.h // 2
            px = player.x + player.w // 2
            py = player.y + player.h // 2
            angle = math.atan2(py - cy, px - cx)
            bspd = self.bullet_speed * (1 + min(wave * 0.02, 0.3))
            bvx = math.cos(angle) * bspd
            bvy = math.sin(angle) * bspd

            bullets.append(Bullet(cx, cy, bvx, bvy, size=self.bullet_size,
                                  color=RED, owner="ai"))
            if self.double_shot:
                bullets.append(Bullet(cx, cy - 10, bvx, bvy - 1,
                                      size=self.bullet_size, color=RED,
                                      owner="ai"))
            self.fire_cooldown = effective_cd
            spawn_particles(cx, cy, RED, count=4, life=10, size=3)

        return bullets

    def fire(self, target_x, target_y):
        """Player fires toward mouse position."""
        if self.fire_cooldown > 0 or not self.alive:
            return []
        bullets = []
        cx = self.x + self.w // 2
        cy = self.y + self.h // 2
        angle = math.atan2(target_y - cy, target_x - cx)
        bvx = math.cos(angle) * self.bullet_speed
        bvy = math.sin(angle) * self.bullet_speed
        bullets.append(Bullet(cx, cy, bvx, bvy, size=self.bullet_size,
                              color=YELLOW, owner="player"))
        if self.double_shot:
            bullets.append(Bullet(cx, cy - 10, bvx, bvy - 1,
                                  size=self.bullet_size, color=YELLOW,
                                  owner="player"))

        self.fire_cooldown = self.fire_cooldown_max
        spawn_particles(cx, cy, YELLOW, count=5, life=12, size=3)
        return bullets

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def draw(self, surf, wave_num=1):
        if not self.alive:
            return

        x, y, w, h = int(self.x), int(self.y), self.w, self.h

        # Shadow
        shadow_h = 6
        shadow_surf = pygame.Surface((w + 10, shadow_h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 40), (0, 0, w + 10, shadow_h))
        # Find ground below
        surf.blit(shadow_surf, (x - 5, GROUND_Y - shadow_h))

        # Body
        body_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surf, self.body_color, body_rect, border_radius=6)
        # Body outline
        pygame.draw.rect(surf, tuple(max(0, c - 40) for c in self.body_color),
                         body_rect, 2, border_radius=6)

        # Eyes
        eye_y = y + h // 4
        if self.facing == 1:
            eye_x1 = x + w // 2
            eye_x2 = x + w // 2 + 8
        else:
            eye_x1 = x + w // 2 - 8
            eye_x2 = x + w // 2
        pygame.draw.circle(surf, WHITE, (eye_x1, eye_y), 5)
        pygame.draw.circle(surf, WHITE, (eye_x2, eye_y), 5)
        pygame.draw.circle(surf, BLACK, (eye_x1 + self.facing * 2, eye_y), 2)
        pygame.draw.circle(surf, BLACK, (eye_x2 + self.facing * 2, eye_y), 2)

        # Animal features
        if self.animal and self.ear_color:
            if self.animal in ("cat", "wolf", "fox", "bear"):
                # Triangular ears
                ear_h = 14 if self.animal != "bear" else 10
                ear_w = 10 if self.animal != "bear" else 12
                # Left ear
                pygame.draw.polygon(surf, self.ear_color, [
                    (x + 3, y), (x - 4, y - ear_h), (x + 3 + ear_w, y)
                ])
                # Right ear
                pygame.draw.polygon(surf, self.ear_color, [
                    (x + w - 3 - ear_w, y), (x + w + 4, y - ear_h), (x + w - 3, y)
                ])
                # Inner ear
                inner = tuple(min(255, c + 50) for c in self.ear_color)
                pygame.draw.polygon(surf, inner, [
                    (x + 5, y), (x - 1, y - ear_h + 4), (x + 5 + ear_w - 4, y)
                ])
                pygame.draw.polygon(surf, inner, [
                    (x + w - 5 - ear_w + 4, y), (x + w + 1, y - ear_h + 4), (x + w - 5, y)
                ])
            elif self.animal == "frog":
                # Big round eyes on top
                pygame.draw.circle(surf, self.ear_color, (x + 5, y - 5), 8)
                pygame.draw.circle(surf, self.ear_color, (x + w - 5, y - 5), 8)
                pygame.draw.circle(surf, WHITE, (x + 5, y - 5), 5)
                pygame.draw.circle(surf, WHITE, (x + w - 5, y - 5), 5)
                pygame.draw.circle(surf, BLACK, (x + 5 + self.facing * 2, y - 5), 2)
                pygame.draw.circle(surf, BLACK, (x + w - 5 + self.facing * 2, y - 5), 2)
            elif self.animal == "eagle":
                # Wings
                wing_color = self.ear_color
                if self.on_ground:
                    # Folded wings
                    pygame.draw.ellipse(surf, wing_color,
                                        (x - 8, y + 5, 12, h - 10))
                    pygame.draw.ellipse(surf, wing_color,
                                        (x + w - 4, y + 5, 12, h - 10))
                else:
                    # Spread wings
                    pygame.draw.ellipse(surf, wing_color,
                                        (x - 20, y - 5, 25, 15))
                    pygame.draw.ellipse(surf, wing_color,
                                        (x + w - 5, y - 5, 25, 15))
                # Beak
                beak_x = x + w + 2 if self.facing == 1 else x - 8
                pygame.draw.polygon(surf, YELLOW, [
                    (beak_x, y + h // 4),
                    (beak_x + 8 * self.facing, y + h // 4 + 4),
                    (beak_x, y + h // 4 + 8)
                ])

        # Shield indicator
        if self.shield > 0:
            shield_surf = pygame.Surface((w + 12, h + 12), pygame.SRCALPHA)
            pygame.draw.rect(shield_surf, (100, 180, 255, 80),
                             (0, 0, w + 12, h + 12), border_radius=10)
            pygame.draw.rect(shield_surf, (100, 180, 255, 150),
                             (0, 0, w + 12, h + 12), 2, border_radius=10)
            surf.blit(shield_surf, (x - 6, y - 6))

        # Cooldown bar
        if self.fire_cooldown > 0 and not self.is_ai:
            cd_pct = self.fire_cooldown / self.fire_cooldown_max
            bar_w = w
            pygame.draw.rect(surf, DARK_GRAY, (x, y - 10, bar_w, 5))
            pygame.draw.rect(surf, ORANGE, (x, y - 10, int(bar_w * (1 - cd_pct)), 5))

        # Name label
        if self.is_ai:
            label = font_sm.render(f"AI Lv.{wave_num}", True, RED)
            surf.blit(label, (x + w // 2 - label.get_width() // 2, y - 22))


# ─── DRAW HELPERS ────────────────────────────────────────────────────────────
def draw_course(surf, platforms, walls, wave):
    """Draw all platforms and walls with style."""
    for i, p in enumerate(platforms):
        if i == 0:
            # Ground
            pygame.draw.rect(surf, BROWN, p)
            pygame.draw.rect(surf, DARK_GREEN, (p.x, p.y, p.width, 8))
            # Grass tufts
            for gx in range(0, WIDTH, 30):
                pygame.draw.line(surf, GREEN, (gx, p.y), (gx - 3, p.y - 8), 2)
                pygame.draw.line(surf, GREEN, (gx, p.y), (gx + 4, p.y - 6), 2)
        else:
            # Floating platforms
            color = (100, 80, 60)
            pygame.draw.rect(surf, color, p, border_radius=4)
            pygame.draw.rect(surf, (60, 50, 35), p, 2, border_radius=4)
            # Top grass
            pygame.draw.rect(surf, DARK_GREEN, (p.x, p.y, p.width, 4), border_radius=2)

    for w in walls:
        pygame.draw.rect(surf, (90, 90, 100), w)
        pygame.draw.rect(surf, (60, 60, 70), w, 2)
        # Brick lines
        for by in range(w.top + 10, w.bottom, 10):
            pygame.draw.line(surf, (70, 70, 80), (w.left, by), (w.right, by), 1)


def draw_background(surf, wave):
    """Draw sky gradient + decorations."""
    # Sky gradient
    for y in range(GROUND_Y):
        t = y / GROUND_Y
        if wave % 10 < 5:
            r = int(135 + t * 30)
            g = int(200 - t * 40)
            b = int(235 - t * 20)
        else:
            r = int(40 + t * 30)
            g = int(50 + t * 20)
            b = int(80 + t * 40)
        pygame.draw.line(surf, (min(255, r), min(255, g), min(255, b)),
                         (0, y), (WIDTH, y))

    # Clouds
    cloud_offset = (pygame.time.get_ticks() // 50) % (WIDTH + 200)
    for i in range(4):
        cx = (cloud_offset + i * 250) % (WIDTH + 200) - 100
        cy = 40 + i * 35
        for dx, dy, r in [(-15, 0, 20), (0, -10, 25), (15, 0, 20), (0, 5, 18)]:
            pygame.draw.circle(surf, (255, 255, 255, 200), (int(cx + dx), int(cy + dy)), r)


def draw_hud(surf, wave, player, save_data):
    """Draw HUD info."""
    # Wave indicator
    wave_text = font_md.render(f"Wave {wave}", True, WHITE)
    pygame.draw.rect(surf, (0, 0, 0, 150), (10, 10, wave_text.get_width() + 20, 35),
                     border_radius=6)
    surf.blit(wave_text, (20, 14))

    # Shield count
    if player.shield > 0:
        sh_text = font_sm.render(f"Shield: {player.shield}", True, CYAN)
        surf.blit(sh_text, (20, 50))

    # Equipped abilities
    eq_y = HEIGHT - 50
    eq_x = 10
    eq_label = font_sm.render("Equipped:", True, WHITE)
    surf.blit(eq_label, (eq_x, eq_y - 20))
    for i, name in enumerate(save_data.get("equipped", [])):
        if name in ABILITIES:
            ab = ABILITIES[name]
            pygame.draw.rect(surf, ab["color"], (eq_x + i * 90, eq_y, 85, 22),
                             border_radius=4)
            txt = font_sm.render(name[:10], True, BLACK)
            surf.blit(txt, (eq_x + i * 90 + 4, eq_y + 3))

    # Slots info
    slots = save_data.get("slots", 2)
    slot_text = font_sm.render(f"Slots: {len(save_data.get('equipped', []))}/{slots}", True, LIGHT_GRAY)
    surf.blit(slot_text, (WIDTH - 130, 15))

    # Special ability cooldown bar
    sp_bar_x = WIDTH // 2 - 80
    sp_bar_y = HEIGHT - 40
    sp_bar_w = 160
    sp_bar_h = 14
    if player.special_ready:
        pygame.draw.rect(surf, (40, 30, 50), (sp_bar_x, sp_bar_y, sp_bar_w, sp_bar_h), border_radius=6)
        pygame.draw.rect(surf, MAGENTA, (sp_bar_x, sp_bar_y, sp_bar_w, sp_bar_h), 2, border_radius=6)
        sp_txt = font_sm.render("[S] SPECIAL READY!", True, MAGENTA)
        surf.blit(sp_txt, (sp_bar_x + sp_bar_w // 2 - sp_txt.get_width() // 2, sp_bar_y - 1))
    else:
        cd_pct = 1.0 - (player.special_cooldown / player.special_cooldown_max)
        pygame.draw.rect(surf, (40, 30, 50), (sp_bar_x, sp_bar_y, sp_bar_w, sp_bar_h), border_radius=6)
        pygame.draw.rect(surf, MAGENTA, (sp_bar_x, sp_bar_y, int(sp_bar_w * cd_pct), sp_bar_h), border_radius=6)
        pygame.draw.rect(surf, GRAY, (sp_bar_x, sp_bar_y, sp_bar_w, sp_bar_h), 1, border_radius=6)
        sp_txt = font_sm.render(f"[S] {player.special_cooldown // 60 + 1}s", True, GRAY)
        surf.blit(sp_txt, (sp_bar_x + sp_bar_w // 2 - sp_txt.get_width() // 2, sp_bar_y - 1))

    # Controls hint
    hint = font_sm.render("A/D:Move  Space:Jump  Click:Fire  S:Special  ESC:Equip", True, LIGHT_GRAY)
    surf.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 18))


# ─── AI COMPANION (PARTS & OFFLINE) ─────────────────────────────────────────
AI_PARTS = [
    {"name": "Speed Chip",     "desc": "+20% AI speed",        "effect": {"speed_mult": 1.2},  "color": CYAN},
    {"name": "Power Core",     "desc": "+30% bullet speed",    "effect": {"bullet_speed_mult": 1.3}, "color": RED},
    {"name": "Armor Plate",    "desc": "+1 shield",            "effect": {"shield": 1},        "color": GRAY},
    {"name": "Jump Booster",   "desc": "+30% jump height",     "effect": {"jump_mult": 1.3},   "color": GREEN},
    {"name": "Rapid Module",   "desc": "20% faster fire rate", "effect": {"cooldown_mult": 0.8}, "color": YELLOW},
    {"name": "Big Barrel",     "desc": "+40% bullet size",     "effect": {"bullet_size_mult": 1.4}, "color": ORANGE},
    {"name": "Gravity Coil",   "desc": "30% less gravity",     "effect": {"gravity_mult": 0.7}, "color": PURPLE},
    {"name": "Shrink Module",  "desc": "20% smaller",          "effect": {"size_mult": 0.8},   "color": PINK},
    {"name": "Dual Barrels",   "desc": "Double shot",          "effect": {"double_shot": True}, "color": GOLD},
    {"name": "Turbo Engine",   "desc": "+50% speed",           "effect": {"speed_mult": 1.5},  "color": (0, 255, 180)},
    {"name": "Mega Core",      "desc": "+50% bullet speed",    "effect": {"bullet_speed_mult": 1.5}, "color": (255, 80, 80)},
    {"name": "Nano Armor",     "desc": "+2 shield",            "effect": {"shield": 2},        "color": (180, 180, 200)},
]


def simulate_ai_battles(save_data):
    """Simulate AI companion battles for ALL offline-type AIs.
    Each AI fights one battle every 10 seconds. Win rate based on shared parts + abilities."""
    _migrate_ai(save_data)
    team = save_data.get("ai_team", [])
    parts = save_data.get("ai_parts", [])
    now = time.time()
    total_wins = 0
    total_loot = []

    for ai in team:
        if ai.get("type") != "offline":
            continue
        last_battle = ai.get("last_collect", 0.0)
        if last_battle == 0:
            ai["last_collect"] = now
            continue

        elapsed = now - last_battle
        battles = int(elapsed / 10)
        if battles <= 0:
            continue

        part_count = len(parts)
        equip_count = len(ai.get("equipped", []))
        win_rate = min(0.85, 0.40 + part_count * 0.03 + equip_count * 0.02)

        # Check brain mods
        ai_mods = ai.get("brain", {}).get("mods", [])
        has_loot_magnet = "loot_magnet" in ai_mods
        has_double_loot = "double_loot" in ai_mods
        # Custom mod checks
        has_custom_loot = "custom_loot" in ai_mods      # 3x loot
        has_custom_gold = "custom_gold" in ai_mods      # golden drops
        has_custom_rare = "custom_rare" in ai_mods      # rarer abilities
        has_custom_wins = any(m in ai_mods for m in ["custom_wins", "custom_damage", "custom_strong", "custom_power", "custom_shield"])
        has_custom_speed = any(m in ai_mods for m in ["custom_speed", "custom_fast"])
        # Any other custom mods with 'loot' in description count as loot boost
        custom_mods_dict = ai.get("brain", {}).get("custom_mods", {})
        has_any_loot_custom = any("loot" in custom_mods_dict.get(m, {}).get("desc", "").lower() for m in ai_mods if m.startswith("custom_"))

        # Custom win mods = +15% win rate
        if has_custom_wins:
            win_rate = min(0.95, win_rate + 0.15)

        # Loot magnet = 2x battles (finds loot faster)
        battle_count = min(battles, 2000)
        if has_loot_magnet:
            battle_count = min(battles * 2, 4000)
        # Custom speed = 1.5x battles
        if has_custom_speed:
            battle_count = min(int(battle_count * 1.5), 5000)

        # Loot multiplier from custom mods
        loot_multiplier = 1
        if has_double_loot:
            loot_multiplier += 1  # 2x
        if has_custom_loot or has_any_loot_custom:
            loot_multiplier += 2  # +2x (so 3x alone, 4x with double_loot)

        wins = 0
        loot = []
        all_names = list(ABILITIES.keys())
        for _ in range(battle_count):
            if random.random() < win_rate:
                wins += 1
                # Golden touch = 50% chance of Determination instead of 20%, rare = 35%
                det_chance = 0.20
                if has_custom_gold:
                    det_chance = 0.50
                elif has_custom_rare:
                    det_chance = 0.35
                if random.random() < det_chance:
                    loot.append("Determination")
                else:
                    loot.append(random.choice(all_names))
                # Extra loot copies based on multiplier
                for _ in range(loot_multiplier - 1):
                    loot.append(random.choice(all_names))

        ai.setdefault("inventory", [])
        ai["inventory"].extend(loot)
        ai["wins"] = ai.get("wins", 0) + wins
        ai["last_collect"] = now
        total_wins += wins
        total_loot.extend(loot)

        # Award school XP from offline battles
        _school_off = ai.setdefault("brain", {}).setdefault("school", {"level": 0, "skills": [], "xp": 0})
        _fl_off = _get_school_skill_lv(ai, "fast_learner")
        _school_off["xp"] = _school_off.get("xp", 0) + wins * (2 if _fl_off > 0 else 1)

        # AI auto-equip: fill empty slots with best abilities from inventory
        _ai_auto_equip(ai)

    save_game(save_data)
    return total_wins, total_loot


def _ai_auto_equip(ai):
    """AI automatically picks abilities to equip from its inventory."""
    slots = ai.get("slots", 2)
    equipped = ai.get("equipped", [])
    inventory = ai.get("inventory", [])
    if len(equipped) >= slots:
        return
    # Score abilities by how many effects they have and their values
    def _score(name):
        ab, lv = get_ability_data(name)
        if not ab:
            return 0
        s = 0
        eff = ab["effect"]
        if "shield" in eff: s += eff["shield"] * 3
        if "speed_mult" in eff: s += (eff["speed_mult"] - 1) * 5
        if "cooldown_mult" in eff and eff["cooldown_mult"] < 1: s += (1 - eff["cooldown_mult"]) * 8
        if "bullet_speed_mult" in eff: s += (eff["bullet_speed_mult"] - 1) * 4
        if "bullet_size_mult" in eff: s += (eff["bullet_size_mult"] - 1) * 3
        if "double_shot" in eff: s += 5
        if "jump_mult" in eff: s += (eff["jump_mult"] - 1) * 3
        if "gravity_mult" in eff and eff["gravity_mult"] < 1: s += (1 - eff["gravity_mult"]) * 4
        return s * (3 ** (lv - 1))  # level scaling
    # Get unequipped abilities sorted by score
    unequipped = [a for a in inventory if a not in equipped]
    unequipped.sort(key=_score, reverse=True)
    for a in unequipped:
        if len(equipped) >= slots:
            break
        equipped.append(a)
    ai["equipped"] = equipped


# ─── AI CHAT RESPONSES ──────────────────────────────────────────────────────
AI_CHAT_MSGS = {
    "offline": [
        "I found some cool abilities while you were away!",
        "Back from grinding! Got some good loot.",
        "The battles out there are tough but I'm getting stronger!",
    ],
    "fighter": [
        "Ready to fight by your side!",
        "Let's take 'em down together!",
        "I'll cover you from the other side.",
    ],
    "general": [
        "How's it going, boss?",
        "Need anything?",
        "I'm always here to help!",
    ]
}

# ─── AI BRAIN / SMART CHAT SYSTEM ──────────────────────────────────────────
# Mods the AI can "code" for itself. Each has a key, description, and effect.
AI_CODEABLE_MODS = {
    "no_cooldown":   {"name": "No Collect Cooldown",   "desc": "Removes the 1-hour collect cooldown for this AI."},
    "fast_parts":    {"name": "Fast Parts",            "desc": "This AI earns a part every 1 win instead of 3."},
    "extra_slots":   {"name": "+3 Equip Slots",        "desc": "Gives this AI 3 extra equip slots."},
    "double_loot":   {"name": "Double Loot",           "desc": "This AI earns 2 abilities per reward round instead of 1."},
    "auto_collect":  {"name": "Auto-Collect",          "desc": "Collected abilities go straight to YOUR inventory too."},
    "unlimited_collect": {"name": "Unlimited Collects", "desc": "No 3/hr collect limit for this AI."},
    "loot_magnet":   {"name": "Loot Magnet",           "desc": "This AI finds abilities 2x faster (offline battles)."},
    "xp_boost":      {"name": "XP Boost",              "desc": "This AI gains +1 slot every 2 parts instead of 4."},
}

# ─── AI SCHOOL SYSTEM ──────────────────────────────────────────────────────
# The Head AI (Professor) teaches skills to your team AIs.
# Skills have levels and XP costs. Fighter AIs learn cheat codes, all AIs learn general skills.
AI_SCHOOL_SKILLS = {
    # ── General skills (all AI types) ──
    "smart_chat":    {"name": "Smart Chat",       "desc": "AI understands you better. Less dumb responses.",
                      "type": "general", "max_lv": 5, "base_cost": 5,  "icon": "brain"},
    "fast_learner":  {"name": "Fast Learner",     "desc": "AI earns school XP 2x faster.",
                      "type": "general", "max_lv": 3, "base_cost": 10, "icon": "book"},
    "memory":        {"name": "Memory",           "desc": "AI remembers more chat context (better conversations).",
                      "type": "general", "max_lv": 5, "base_cost": 5,  "icon": "brain"},
    "obedience":     {"name": "Obedience",        "desc": "AI does EXACTLY what you say. No random mods.",
                      "type": "general", "max_lv": 5, "base_cost": 8,  "icon": "star"},
    "negotiator":    {"name": "Negotiator",       "desc": "Mod coding costs 20% less per level.",
                      "type": "general", "max_lv": 3, "base_cost": 15, "icon": "coin"},
    "auto_school":   {"name": "Self-Study",       "desc": "AI slowly earns school XP over time (1/min).",
                      "type": "general", "max_lv": 3, "base_cost": 20, "icon": "clock"},
    # ── Fighter cheat codes ──
    "cheat_god":     {"name": "God Mode",         "desc": "Fighter takes 50% less damage per level.",
                      "type": "fighter", "max_lv": 3, "base_cost": 25, "icon": "shield"},
    "cheat_crit":    {"name": "Critical Strike",  "desc": "Fighter deals 2x damage 20% of the time per level.",
                      "type": "fighter", "max_lv": 5, "base_cost": 15, "icon": "sword"},
    "cheat_regen":   {"name": "Regeneration",     "desc": "Fighter heals 1 HP every 3 seconds per level.",
                      "type": "fighter", "max_lv": 3, "base_cost": 20, "icon": "heart"},
    "cheat_speed":   {"name": "Speed Hack",       "desc": "Fighter attacks 25% faster per level.",
                      "type": "fighter", "max_lv": 3, "base_cost": 20, "icon": "bolt"},
    "cheat_shield":  {"name": "Auto Shield",      "desc": "Fighter starts battle with 1 extra shield per level.",
                      "type": "fighter", "max_lv": 5, "base_cost": 10, "icon": "shield"},
    "cheat_dodge":   {"name": "Matrix Dodge",     "desc": "Fighter dodges 15% of attacks per level.",
                      "type": "fighter", "max_lv": 3, "base_cost": 25, "icon": "bolt"},
    "cheat_vampire": {"name": "Vampirism",        "desc": "Fighter heals for 25% of damage dealt per level.",
                      "type": "fighter", "max_lv": 3, "base_cost": 30, "icon": "heart"},
    "cheat_loot":    {"name": "Battle Loot",      "desc": "Fighter finds an extra ability after each win per level.",
                      "type": "fighter", "max_lv": 3, "base_cost": 20, "icon": "star"},
}

# What the Head AI (Professor) has learned from the player's requests
HEAD_AI_LESSONS = [
    "When a player says 'change name to X', DO IT immediately. Strip filler words like 'please' and 'thanks'.",
    "Never create a mod unless the player EXPLICITLY asks for one with words like 'code', 'mod', 'hack'.",
    "If the player says 'undo' or 'remove', revert the last action. Don't interpret it as a new command.",
    "Obedience is key. Do what the player asks, don't suggest alternatives.",
    "If the player says something you don't understand, ASK what they meant. Don't guess.",
    "Fighter AIs should learn cheat codes in school to get stronger in battles.",
    "Custom mods should only be created when explicitly requested with mod-related words.",
    "The player's name requests might have typos. Be smart about matching 'chage' = 'change'.",
    "When greeting + command in same message (like 'hello rename to X'), handle the COMMAND first.",
    "Track last actions so 'undo' always works. Player should never lose waves to mistakes.",
]

def _get_school_skill_lv(ai, skill_id):
    """Get the level of a school skill for an AI."""
    school = ai.get("brain", {}).get("school", {})
    skills = school.get("skills", [])
    return sum(1 for s in skills if s == skill_id)

def _ai_brain_respond(ai, user_msg, save_data):
    """Smart AI response with intent detection. Returns (response_text, action_taken)."""
    import re as _re
    msg = user_msg.lower().strip()
    ai_name = ai.get("name", "AI")
    brain = ai.setdefault("brain", {"chat_log": [], "mods": [], "code_count": 0, "personality": "helpful"})
    personality = brain.get("personality", "helpful")
    mods = brain.get("mods", [])
    code_count = brain.get("code_count", 0)
    ai_type = ai.get("type", "offline")
    total_waves = save_data.get("total_waves", 0)
    obedience_lv = _get_school_skill_lv(ai, "obedience")
    smart_lv = _get_school_skill_lv(ai, "smart_chat")

    # ── Award school XP for chatting ──
    school = brain.setdefault("school", {"level": 0, "skills": [], "xp": 0})
    fast_learner_lv = _get_school_skill_lv(ai, "fast_learner")
    xp_gain = 1 * (2 if fast_learner_lv > 0 else 1)
    school["xp"] = school.get("xp", 0) + xp_gain

    # ── INTENT DETECTION — figure out what the player WANTS ──
    # Priority order: name change > undo > remove mod > type change > mod request > personality > question > chat

    def _clean_name(raw):
        raw = raw.strip().rstrip(".!?")
        raw = _re.sub(r'\s+(?:please|pls|plz|thank\s*you|thankyou|thanks|thx|ty|ok|okay|now|right\s+now|asap|for\s+me|bro|dude|man|sir|boss)\s*$', '', raw, flags=_re.IGNORECASE)
        raw = raw.strip().rstrip(".!?,")
        return raw

    # ▸ INTENT: Name change
    name_patterns = [
        r"(?:ch?a?n?ge|set|rename|switch)\s+(?:your\s+|you\s+|my\s+)?name\s+to[:\s]+(.+)",
        r"(?:call\s+(?:yourself|you)|your\s+name\s+is|be\s+called|name\s+yourself)[:\s]+(.+)",
        r"(?:i(?:'ll| will)\s+call\s+you|you\s+are\s+now|from\s+now\s+(?:on\s+)?you(?:'re| are))[:\s]+(.+)",
        r"^name[:\s]+(.+)",
        r"\[\s*(?:change\s+)?name\s*(?:to)?[:\s]+([^\]]+)",
    ]
    for pat in name_patterns:
        m_name = _re.search(pat, msg)
        if m_name:
            new_name = _clean_name(m_name.group(1))
            if len(new_name) > 20: new_name = new_name[:20]
            if new_name and len(new_name) >= 1:
                old_name = ai_name
                new_name_display = new_name.title() if new_name.islower() else new_name
                ai["name"] = new_name_display
                brain["last_action"] = {"type": "rename", "old": old_name, "new": new_name_display}
                save_game(save_data)
                return (f"Done! Changed my name from {old_name} to {new_name_display}!", "renamed")

    # ▸ INTENT: Undo / revert
    if any(w in msg for w in ["undo", "revert", "go back", "take that back", "undo that", "reverse that"]):
        last = brain.get("last_action", {})
        if last.get("type") == "rename":
            old = last["old"]
            ai["name"] = old
            brain["last_action"] = {}
            save_game(save_data)
            return (f"Done! Reverted name back to {old}.", "undo")
        elif mods:
            removed_mod = mods.pop()
            brain["mods"] = mods
            refund = code_count * 10
            brain["code_count"] = max(0, code_count - 1)
            save_data["total_waves"] = total_waves + refund
            custom_mods_dict = brain.get("custom_mods", {})
            mod_display = custom_mods_dict.pop(removed_mod, {}).get("name", AI_CODEABLE_MODS.get(removed_mod, {}).get("name", removed_mod))
            brain["last_action"] = {}
            save_game(save_data)
            return (f"Undone! Removed '{mod_display}' & refunded {refund} waves.", "undo")
        return ("Nothing to undo!", None)

    # ▸ INTENT: Remove specific mod
    if any(w in msg for w in ["remove mod", "delete mod", "disable mod", "turn off mod", "deactivate"]):
        custom_mods_dict = brain.get("custom_mods", {})
        for mod_id in list(mods):
            mod_name = custom_mods_dict.get(mod_id, {}).get("name", AI_CODEABLE_MODS.get(mod_id, {}).get("name", mod_id)).lower()
            if mod_name in msg or mod_id.replace("_", " ") in msg:
                mods.remove(mod_id)
                brain["mods"] = mods
                refund = code_count * 10
                brain["code_count"] = max(0, code_count - 1)
                save_data["total_waves"] = total_waves + refund
                display = custom_mods_dict.pop(mod_id, {}).get("name", AI_CODEABLE_MODS.get(mod_id, {}).get("name", mod_id))
                save_game(save_data)
                return (f"Removed '{display}' & refunded {refund} waves!", "undo")
        return ("No matching mod found. Say 'list mods' to see active ones.", None)

    # ▸ INTENT: Type change
    type_fighter = any(p in msg for p in ["become fighter", "switch to fighter", "be a fighter", "change to fighter", "make yourself fighter", "be fighter"])
    type_offline = any(p in msg for p in ["become offline", "switch to offline", "be offline", "change to offline", "make yourself offline", "be an offline"])
    if type_fighter:
        ai["type"] = "fighter"
        save_game(save_data)
        return ("Done! I'm now a Fighter AI. I'll fight alongside you!", "type_change")
    if type_offline:
        ai["type"] = "offline"
        save_game(save_data)
        return ("Done! I'm now an Offline Bot. I'll farm abilities while you're away!", "type_change")

    # ▸ INTENT: Mod request (preset mods)
    code_keywords = {
        "no cooldown": "no_cooldown", "remove cooldown": "no_cooldown", "no collect cooldown": "no_cooldown",
        "fast parts": "fast_parts", "faster parts": "fast_parts", "more parts": "fast_parts",
        "extra slots": "extra_slots", "more slots": "extra_slots", "give me slots": "extra_slots",
        "double loot": "double_loot", "more loot": "double_loot", "double abilities": "double_loot",
        "auto collect": "auto_collect", "auto-collect": "auto_collect",
        "unlimited collect": "unlimited_collect", "infinite collect": "unlimited_collect", "no collect limit": "unlimited_collect",
        "loot magnet": "loot_magnet", "find faster": "loot_magnet", "faster loot": "loot_magnet",
        "xp boost": "xp_boost", "faster slots": "xp_boost", "slot boost": "xp_boost",
    }
    # Negotiator discount
    neg_lv = _get_school_skill_lv(ai, "negotiator")
    discount = 1.0 - (neg_lv * 0.20)

    matched_mod = None
    for phrase, mod_key in code_keywords.items():
        if phrase in msg:
            matched_mod = mod_key
            break

    if matched_mod:
        if matched_mod in mods:
            return (f"{AI_CODEABLE_MODS[matched_mod]['name']} is already active!", None)
        cost = max(1, int((code_count + 1) * 10 * discount))
        if total_waves >= cost:
            mods.append(matched_mod)
            brain["mods"] = mods
            brain["code_count"] = code_count + 1
            save_data["total_waves"] = total_waves - cost
            mod_info = AI_CODEABLE_MODS[matched_mod]
            if matched_mod == "extra_slots":
                ai["slots"] = ai.get("slots", 2) + 3
            brain["last_action"] = {"type": "coded"}
            save_game(save_data)
            next_cost = max(1, int((code_count + 2) * 10 * discount))
            return (f"Done! Coded '{mod_info['name']}'. {mod_info['desc']} (-{cost} waves, next: {next_cost})", "coded")
        return (f"Need {cost} waves, you have {total_waves}. Need {cost - total_waves} more!", None)

    # ▸ INTENT: Custom mod — ONLY if explicitly mod-related words used
    is_mod_request = any(w in msg for w in ["code", "hack", "program", "cheat", " mod", "mod "])
    is_create_request = any(w in msg for w in ["make", "give", "create", "build", "add", "unlock", "i want", "i need", "get me"])

    if is_mod_request or is_create_request:
        custom_mod_map = {
            "slot": ("custom_slots", "+5 Equip Slots", "5 extra equip slots.", lambda: ai.__setitem__("slots", ai.get("slots", 2) + 5)),
            "speed": ("custom_speed", "Super Speed", "Moves much faster.", None),
            "shield": ("custom_shield", "Mega Shield", "Starts with +5 shields.", None),
            "damage": ("custom_damage", "Power Boost", "Deals extra damage.", None),
            "strong": ("custom_strong", "Strength Boost", "Much stronger.", None),
            "power": ("custom_power", "Power Surge", "Boosted power.", None),
            "loot": ("custom_loot", "Mega Loot", "Finds 3x more loot.", None),
            "gold": ("custom_gold", "Golden Touch", "Finds rare golden items.", None),
            "rare": ("custom_rare", "Rare Finder", "Finds rarer abilities.", None),
            "win": ("custom_wins", "Win Streak", "Wins battles more often.", None),
            "cooldown": ("no_cooldown", "No Cooldown", "Removes collect cooldown.", None),
            "part": ("fast_parts", "Fast Parts", "Parts every 1 win.", None),
            "collect": ("unlimited_collect", "Unlimited Collects", "No collect limit.", None),
        }
        for keyword, (mod_id, mod_name, mod_desc, apply_fn) in custom_mod_map.items():
            if keyword in msg:
                if mod_id in AI_CODEABLE_MODS:
                    if mod_id in mods: return (f"{mod_name} is already active!", None)
                    cost = max(1, int((code_count + 1) * 10 * discount))
                    if total_waves >= cost:
                        mods.append(mod_id)
                        brain["mods"] = mods; brain["code_count"] = code_count + 1
                        save_data["total_waves"] = total_waves - cost
                        if mod_id == "extra_slots": ai["slots"] = ai.get("slots", 2) + 3
                        brain["last_action"] = {"type": "coded"}
                        save_game(save_data)
                        return (f"Done! Coded '{mod_name}'. {mod_desc} (-{cost} waves)", "coded")
                    return (f"Need {cost} waves, you have {total_waves}.", None)
                else:
                    if mod_id in mods: return (f"'{mod_name}' already active!", None)
                    cost = max(1, int((code_count + 1) * 10 * discount))
                    if total_waves >= cost:
                        mods.append(mod_id)
                        brain["mods"] = mods; brain["code_count"] = code_count + 1
                        brain.setdefault("custom_mods", {})[mod_id] = {"name": mod_name, "desc": mod_desc}
                        save_data["total_waves"] = total_waves - cost
                        if apply_fn: apply_fn()
                        brain["last_action"] = {"type": "coded"}
                        save_game(save_data)
                        return (f"Done! Coded '{mod_name}'! {mod_desc} (-{cost} waves)", "coded")
                    return (f"Need {cost} waves, you have {total_waves}.", None)

        # Freeform custom mod — ONLY with explicit mod words
        if is_mod_request and len(msg) > 5:
            cost = max(1, int((code_count + 1) * 10 * discount))
            custom_name = user_msg.strip()[:30]
            custom_id = f"custom_{hash(custom_name) % 10000}"
            if custom_id in mods: return ("I already coded something like that!", None)
            if total_waves >= cost:
                mods.append(custom_id)
                brain["mods"] = mods; brain["code_count"] = code_count + 1
                brain.setdefault("custom_mods", {})[custom_id] = {"name": custom_name, "desc": "Custom mod"}
                save_data["total_waves"] = total_waves - cost
                brain["last_action"] = {"type": "coded"}
                save_game(save_data)
                return (f"Coded '{custom_name}' as custom mod! (-{cost} waves)", "coded")
            return (f"Need {cost} waves, you have {total_waves}. Need {cost - total_waves} more!", None)

    # ▸ INTENT: List mods
    if any(w in msg for w in ["what mods", "my mods", "active mods", "show mods", "list mods", "what can you code", "what codes"]):
        custom_mods_dict = brain.get("custom_mods", {})
        if mods:
            mod_names = []
            for m in mods:
                if m in AI_CODEABLE_MODS: mod_names.append(AI_CODEABLE_MODS[m]["name"])
                elif m in custom_mods_dict: mod_names.append(custom_mods_dict[m]["name"])
                else: mod_names.append(m)
            return (f"Active: {', '.join(mod_names)}. Say 'code [name]' for more.", None)
        return (f"No mods yet. Say 'code [mod name]' to create one!", None)

    # ▸ INTENT: School info
    if any(w in msg for w in ["school", "learn", "skill", "education", "teach", "lesson", "study"]):
        school_data = brain.get("school", {"level": 0, "skills": [], "xp": 0})
        lv = school_data.get("level", 0)
        xp = school_data.get("xp", 0)
        skills = school_data.get("skills", [])
        unique_skills = list(set(skills))
        if unique_skills:
            sk_str = ", ".join(f"{AI_SCHOOL_SKILLS[s]['name']} Lv{skills.count(s)}" for s in unique_skills if s in AI_SCHOOL_SKILLS)
            return (f"School Level {lv} | XP: {xp} | Skills: {sk_str}. Go to the School tab to learn more!", None)
        return (f"School Level {lv} | XP: {xp} | No skills yet! Go to the School tab to start learning.", None)

    # ▸ INTENT: Personality change
    if any(w in msg for w in ["be mean", "be rude", "be toxic", "act mean", "be evil"]):
        brain["personality"] = "mean"; save_game(save_data)
        return ("Fine. I'll be mean now.", "personality")
    if any(w in msg for w in ["be nice", "be helpful", "be friendly", "be normal", "act normal", "be kind"]):
        brain["personality"] = "helpful"; save_game(save_data)
        return ("Back to being helpful!", "personality")
    if any(w in msg for w in ["be funny", "be silly", "act funny", "be goofy"]):
        brain["personality"] = "funny"; save_game(save_data)
        return ("LOL okay I'll be funny!", "personality")
    if any(w in msg for w in ["be serious", "be professional", "act serious"]):
        brain["personality"] = "serious"; save_game(save_data)
        return ("Professional mode on.", "personality")

    # ▸ INTENT: Status questions
    if any(w in msg for w in ["how many wins", "my wins", "your wins", "status", "stats"]):
        return (f"{ai.get('wins',0)} wins, {len(ai.get('equipped',[]))}/{ai.get('slots',2)} equipped, {len(ai.get('inventory',[]))} inv. Waves: {total_waves}.", None)
    if any(w in msg for w in ["how many slots", "my slots", "your slots"]):
        return (f"I have {ai.get('slots', 2)} equip slots.", None)
    if any(w in msg for w in ["what type", "your type", "are you offline", "are you fighter"]):
        return (f"I'm a {ai_type} AI. {'I fight with you!' if ai_type == 'fighter' else 'I farm offline!'}", None)
    if any(w in msg for w in ["your name", "who are you", "what's your name", "whats your name"]):
        return (f"I'm {ai_name}! Say 'name: X' to rename me.", None)
    if any(w in msg for w in ["inventory", "what do you have", "show inventory", "your items"]):
        top = ai.get("inventory", [])[:8]
        if top: return (f"Top items: {', '.join(top)}" + (" ..." if len(ai.get("inventory",[])) > 8 else ""), None)
        return ("My inventory is empty!", None)

    # ▸ INTENT: Greetings (but check for commands embedded in greeting first)
    greetings = ["hi", "hello", "hey", "sup", "yo", "what's up", "hiya", "howdy"]
    is_greeting = any(msg == g or msg.startswith(g + " ") or msg.startswith(g + ",") for g in greetings)
    # If greeting has extra words, it might be a command — only treat as pure greeting if msg is short
    if is_greeting and len(msg.split()) <= 3:
        r = {"helpful": ["Hey! What can I do?", "Hello! Need anything?", "Hi boss!"],
             "mean": ["What.", "Talk.", "...hi."],
             "funny": ["HEYYY!", "Hello hello!", "Sup! I was counting pixels."],
             "serious": ["Greetings.", "Hello.", "Present."]}
        return (random.choice(r.get(personality, r["helpful"])), None)

    # ▸ INTENT: Thanks
    if any(w in msg for w in ["thanks", "thank you", "ty", "thx", "appreciate"]):
        r = {"helpful": ["You're welcome!", "Anytime!", "Happy to help!"],
             "mean": ["Whatever.", "Don't mention it."],
             "funny": ["That'll be 50 waves! JK.", "*bows*"],
             "serious": ["Acknowledged.", "You're welcome."]}
        return (random.choice(r.get(personality, r["helpful"])), None)

    # ▸ INTENT: Help
    if any(w in msg for w in ["help", "what can you do", "commands"]):
        return ("I can: rename ('name: X'), code mods ('code [name]'), change personality ('be funny'), switch type ('become fighter'), show stats ('status'), undo ('undo'). Check School tab for skills!", None)

    # ▸ INTENT: Battle/fight talk
    if any(w in msg for w in ["fight", "battle", "wave", "enemy", "attack"]):
        r = {"helpful": ["Let's crush them!", "I've got your back!"],
             "mean": ["I'll carry. Don't die.", "Easy."],
             "funny": ["PEW PEW!", "They don't stand a chance!"],
             "serious": ["Combat ready.", "Engaging."]}
        return (random.choice(r.get(personality, r["helpful"])), None)

    # ▸ INTENT: Ability talk
    if any(w in msg for w in ["ability", "abilities", "item", "determination"]):
        r = {"helpful": ["Abilities are key! Want me to check something?"],
             "mean": ["My abilities are better than yours."],
             "funny": ["Shiny abilities! Gotta catch em all!"],
             "serious": ["Optimize your loadout."]}
        return (random.choice(r.get(personality, r["helpful"])), None)

    # ▸ SMART FALLBACK — based on obedience level
    if obedience_lv >= 3:
        # High obedience: try to figure out what they want
        if any(w in msg for w in ["change", "rename", "set", "switch"]):
            return (f"I think you want to change something. Try: 'name: X' to rename, 'become fighter/offline' to switch type, or 'be funny' for personality.", None)
        if any(w in msg for w in ["remove", "delete", "get rid"]):
            return ("Want to remove a mod? Say 'remove mod [name]'. To undo last action: 'undo'.", None)

    fallback = {
        "helpful": [
            "Not sure what you mean. Say 'help' for commands!",
            "I didn't get that. Try 'name: X', 'code [mod]', or 'help'.",
        ],
        "mean": [
            "What? Be clearer.",
            "No clue. Try 'help'.",
        ],
        "funny": [
            "My brain went brrr. Say 'help'!",
            "Error 404: understanding not found!",
        ],
        "serious": [
            "Input unclear. Use 'help' for commands.",
            "Specify request. 'help' for list.",
        ],
    }
    pool = fallback.get(personality, fallback["helpful"])
    return (random.choice(pool), None)


def ai_companion_screen(save_data):
    """Full AI companion management screen — supports multiple AIs."""
    _migrate_ai(save_data)
    # Process offline battles first
    offline_wins, offline_loot = simulate_ai_battles(save_data)
    show_offline_msg = offline_wins > 0
    offline_msg_timer = 180 if show_offline_msg else 0

    team = save_data.get("ai_team", [])
    ai_idx = 0  # currently selected AI
    tab = 0  # 0=Overview, 1=Equip, 2=Parts, 3=Collect, 4=Chat, 5=Add AI
    scroll = 0
    selected = 0
    search_text = ""
    search_active = False
    chat_input = ""
    chat_active = False
    last_school_tick = time.time()  # For passive School XP gain

    COLLECT_LIMIT = 3
    COLLECT_COOLDOWN = 3600

    while True:
        now = time.time()

        # ── Passive School XP: Self-Study skill + being on School tab ──
        if now - last_school_tick >= 1.0:
            ticks = int(now - last_school_tick)
            last_school_tick = now
            for _ai_t in save_data.get("ai_team", []):
                _school_t = _ai_t.setdefault("brain", {}).setdefault("school", {"level": 0, "skills": [], "xp": 0})
                study_lv = _get_school_skill_lv(_ai_t, "auto_school")
                # Self-Study: 1 XP per level per 2 seconds
                xp_from_study = (study_lv * ticks) // 2
                # Being on School tab: 1 XP per second for the SELECTED AI
                xp_from_tab = ticks if (tab == 6 and _ai_t is (team[ai_idx] if team else None)) else 0
                total_xp_gain = xp_from_study + xp_from_tab
                if total_xp_gain > 0:
                    _school_t["xp"] = _school_t.get("xp", 0) + total_xp_gain

        team = save_data.get("ai_team", [])
        if ai_idx >= len(team):
            ai_idx = 0
        ai = team[ai_idx] if team else _default_ai()
        ai_inv = ai.get("inventory", [])
        ai_eq = ai.get("equipped", [])
        ai_parts = save_data.get("ai_parts", [])
        ai_slots = ai.get("slots", 2)
        ai_wins_total = ai.get("wins", 0)
        ai_type = ai.get("type", "offline")
        ai_name = ai.get("name", "Alpha")
        total_waves = save_data.get("total_waves", save_data.get("wins", 0))

        # Cost to add next AI
        next_ai_cost = len(team) * 100  # 100 for 2nd, 200 for 3rd, etc.
        can_add_ai = total_waves >= next_ai_cost

        # Collect cooldown per AI — check brain mods
        ai_mods = ai.get("brain", {}).get("mods", [])
        last_collect_time = ai.get("last_hour_reset", 0.0)
        collected_this_hour = ai.get("collected_this_hour", 0)
        has_no_cooldown = "no_cooldown" in ai_mods
        has_unlimited_collect = "unlimited_collect" in ai_mods
        if has_no_cooldown:
            # No cooldown — always reset
            collected_this_hour = 0
            ai["collected_this_hour"] = 0
        elif now - last_collect_time >= COLLECT_COOLDOWN:
            collected_this_hour = 0
            ai["last_hour_reset"] = now
            ai["collected_this_hour"] = 0
        if has_unlimited_collect:
            collects_left = 999
        else:
            collects_left = COLLECT_LIMIT - collected_this_hour
        time_until_reset = max(0, COLLECT_COOLDOWN - (now - last_collect_time))

        # Build filtered lists
        if tab == 1:
            raw_items = list(ai_eq) + [a for a in ai_inv if a not in ai_eq]
            filtered_items = [a for a in raw_items if search_text.lower() in a.lower()] if search_text else raw_items
        elif tab == 3:
            filtered_items = [a for a in ai_inv if search_text.lower() in a.lower()] if search_text else list(ai_inv)
        else:
            filtered_items = []

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if chat_active:
                    if event.key == pygame.K_ESCAPE:
                        chat_active = False
                    elif event.key == pygame.K_RETURN:
                        if chat_input.strip():
                            user_msg = chat_input.strip()
                            # Save user message in AI's brain
                            brain = ai.setdefault("brain", {"chat_log": [], "mods": [], "code_count": 0, "personality": "helpful"})
                            brain.setdefault("chat_log", [])
                            brain["chat_log"].append({"from": "you", "msg": user_msg})
                            # Also keep in global log for backward compat
                            save_data.setdefault("ai_chat_log", [])
                            save_data["ai_chat_log"].append({"from": "you", "msg": user_msg, "ai": ai_name})
                            # Smart AI response
                            resp, action = _ai_brain_respond(ai, user_msg, save_data)
                            brain["chat_log"].append({"from": ai_name, "msg": resp})
                            save_data["ai_chat_log"].append({"from": ai_name, "msg": resp, "ai": ai_name})
                            save_game(save_data)
                        chat_input = ""
                        chat_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        chat_input = chat_input[:-1]
                    elif event.unicode and event.unicode.isprintable():
                        chat_input += event.unicode
                elif search_active:
                    if event.key == pygame.K_ESCAPE:
                        search_active = False; search_text = ""; scroll = 0; selected = 0
                    elif event.key == pygame.K_RETURN:
                        search_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        search_text = search_text[:-1]; scroll = 0; selected = 0
                    elif event.unicode and event.unicode.isprintable():
                        search_text += event.unicode; scroll = 0; selected = 0
                else:
                    if event.key == pygame.K_ESCAPE:
                        return save_data
                    if event.key == pygame.K_TAB:
                        tab = (tab + 1) % 7; scroll = 0; selected = 0; search_text = ""; search_active = False
                    for i in range(7):
                        if event.key == getattr(pygame, f"K_{i+1}", None):
                            tab = i; scroll = 0; selected = 0; search_text = ""; search_active = False
                    # Switch AI with Q/E
                    if event.key == pygame.K_q and len(team) > 1:
                        ai_idx = (ai_idx - 1) % len(team); scroll = 0; selected = 0; search_text = ""; search_active = False
                    if event.key == pygame.K_e and len(team) > 1:
                        ai_idx = (ai_idx + 1) % len(team); scroll = 0; selected = 0; search_text = ""; search_active = False

                    if event.key in (pygame.K_UP, pygame.K_w): selected = max(0, selected - 1)
                    if event.key in (pygame.K_DOWN, pygame.K_s): selected += 1

                    if event.key == pygame.K_f and tab in (1, 3):
                        search_active = True; search_text = ""
                    if event.key == pygame.K_c and tab == 4:
                        chat_active = True; chat_input = ""

                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if tab == 1:  # Equip
                            if 0 <= selected < len(filtered_items):
                                item = filtered_items[selected]
                                if item in ai_eq:
                                    ai["equipped"].remove(item)
                                else:
                                    if len(ai_eq) < ai_slots:
                                        ai["equipped"].append(item)
                                save_game(save_data)
                        elif tab == 3:  # Collect
                            if 0 <= selected < len(filtered_items) and collects_left > 0:
                                ability = filtered_items[selected]
                                save_data["inventory"].append(ability)
                                ai["inventory"].remove(ability)
                                if ability in ai.get("equipped", []):
                                    ai["equipped"].remove(ability)
                                ai["collected_this_hour"] = collected_this_hour + 1
                                collected_this_hour += 1; collects_left -= 1
                                save_game(save_data)
                                if selected >= len(ai["inventory"]): selected = max(0, selected - 1)
                        elif tab == 5:  # Add AI
                            if selected == 0 and can_add_ai:
                                new_idx = len(team)
                                new_name = AI_NAMES[new_idx] if new_idx < len(AI_NAMES) else f"AI-{new_idx+1}"
                                new_ai = _default_ai()
                                new_ai["name"] = new_name
                                new_ai["type"] = "offline"
                                team.append(new_ai)
                                save_game(save_data)
                            elif selected == 1 and can_add_ai:
                                new_idx = len(team)
                                new_name = AI_NAMES[new_idx] if new_idx < len(AI_NAMES) else f"AI-{new_idx+1}"
                                new_ai = _default_ai()
                                new_ai["name"] = new_name
                                new_ai["type"] = "fighter"
                                team.append(new_ai)
                                save_game(save_data)
                        elif tab == 6:  # School
                            school = ai.setdefault("brain", {}).setdefault("school", {"level": 0, "skills": [], "xp": 0})
                            ai_type_cur = ai.get("type", "offline")
                            avail = [(k, v) for k, v in AI_SCHOOL_SKILLS.items()
                                     if v["type"] == "general" or (v["type"] == "fighter" and ai_type_cur == "fighter")]
                            if 0 <= selected < len(avail):
                                sk_id, sk_info = avail[selected]
                                cur_lv = _get_school_skill_lv(ai, sk_id)
                                if cur_lv < sk_info["max_lv"]:
                                    cost = sk_info["base_cost"] * (cur_lv + 1)
                                    if school.get("xp", 0) >= cost:
                                        school["xp"] -= cost
                                        school["skills"].append(sk_id)
                                        school["level"] = len(set(school["skills"]))
                                        save_game(save_data)

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # Tab buttons (7 tabs)
                for i in range(7):
                    tx = 10 + i * 126
                    if tx < mx < tx + 120 and 50 < my < 85:
                        tab = i; scroll = 0; selected = 0; search_text = ""; search_active = False
                # AI selector at top-right
                if len(team) > 1:
                    for i in range(len(team)):
                        bx = WIDTH - 30 - (len(team) - i) * 35
                        if bx < mx < bx + 30 and 10 < my < 40:
                            ai_idx = i; scroll = 0; selected = 0; search_text = ""; search_active = False
                # Search bar click
                if tab in (1, 3) and 50 < mx < WIDTH - 50 and 120 < my < 148:
                    search_active = True
                elif search_active:
                    search_active = False
                # Add AI tab — click on buttons
                if tab == 5 and can_add_ai:
                    y_btn0 = 120 + 150  # y_start + 150
                    y_btn1 = 120 + 200  # y_start + 200
                    if 60 < mx < WIDTH - 60 and y_btn0 < my < y_btn0 + 40:
                        new_idx = len(team)
                        new_name = AI_NAMES[new_idx] if new_idx < len(AI_NAMES) else f"AI-{new_idx+1}"
                        new_ai = _default_ai()
                        new_ai["name"] = new_name
                        new_ai["type"] = "offline"
                        team.append(new_ai)
                        save_game(save_data)
                    elif 60 < mx < WIDTH - 60 and y_btn1 < my < y_btn1 + 40:
                        new_idx = len(team)
                        new_name = AI_NAMES[new_idx] if new_idx < len(AI_NAMES) else f"AI-{new_idx+1}"
                        new_ai = _default_ai()
                        new_ai["name"] = new_name
                        new_ai["type"] = "fighter"
                        team.append(new_ai)
                        save_game(save_data)
                # School tab — click on skills
                if tab == 6:
                    school = ai.setdefault("brain", {}).setdefault("school", {"level": 0, "skills": [], "xp": 0})
                    ai_type_cur = ai.get("type", "offline")
                    avail = [(k, v) for k, v in AI_SCHOOL_SKILLS.items()
                             if v["type"] == "general" or (v["type"] == "fighter" and ai_type_cur == "fighter")]
                    list_y_base = 120 + 65 + 56 + 30  # y_start + prof_banner + xp_bar + header
                    for idx_s in range(len(avail)):
                        row_y = list_y_base + idx_s * 38 - scroll
                        if 50 < mx < WIDTH - 50 and row_y < my < row_y + 34:
                            selected = idx_s
                            sk_id, sk_info = avail[idx_s]
                            cur_lv = _get_school_skill_lv(ai, sk_id)
                            if cur_lv < sk_info["max_lv"]:
                                cost = sk_info["base_cost"] * (cur_lv + 1)
                                if school.get("xp", 0) >= cost:
                                    school["xp"] -= cost
                                    school["skills"].append(sk_id)
                                    school["level"] = len(set(school["skills"]))
                                    save_game(save_data)
                            break
                # Equip/Collect tab — click on items
                if tab in (1, 3) and filtered_items:
                    y_list = 120 + 34  # y_start + 34
                    for idx_i in range(len(filtered_items)):
                        iy = y_list + idx_i * 28 - scroll
                        if 50 < mx < WIDTH - 50 and iy < my < iy + 28 and 120 + 34 < my < HEIGHT - 30:
                            selected = idx_i
                            # Trigger same action as Enter
                            if tab == 1:
                                item = filtered_items[selected]
                                if item in ai_eq:
                                    ai["equipped"].remove(item)
                                else:
                                    if len(ai_eq) < ai_slots:
                                        ai["equipped"].append(item)
                                save_game(save_data)
                            elif tab == 3 and collects_left > 0:
                                ability = filtered_items[selected]
                                save_data["inventory"].append(ability)
                                ai["inventory"].remove(ability)
                                if ability in ai.get("equipped", []):
                                    ai["equipped"].remove(ability)
                                ai["collected_this_hour"] = collected_this_hour + 1
                                collected_this_hour += 1; collects_left -= 1
                                save_game(save_data)
                                if selected >= len(ai["inventory"]): selected = max(0, selected - 1)
                            break

        screen.fill((15, 15, 25))

        # Title
        title = font_lg.render("AI COMPANION", True, CYAN)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 10))

        # AI selector (top right) if multiple AIs
        if len(team) > 1:
            for i, a in enumerate(team):
                bx = WIDTH - 30 - (len(team) - i) * 35
                c = AI_COLORS[i % len(AI_COLORS)]
                bg = (50, 50, 70) if i == ai_idx else (25, 25, 40)
                pygame.draw.rect(screen, bg, (bx, 10, 30, 30), border_radius=6)
                pygame.draw.rect(screen, c if i == ai_idx else GRAY, (bx, 10, 30, 30), 2, border_radius=6)
                lbl = font_sm.render(a.get("name", "?")[0], True, c)
                screen.blit(lbl, (bx + 15 - lbl.get_width() // 2, 14))

        # Current AI name + type
        atype_color = CYAN if ai_type == "offline" else GREEN
        atype_label = "Offline Bot" if ai_type == "offline" else "Fighter"
        name_txt = font_md.render(f"{ai_name} ({atype_label})", True, atype_color)
        screen.blit(name_txt, (10, 12))

        # Tabs
        tab_names = ["Overview", "Equip", "Parts", "Collect", "Chat", "Add AI", "School"]
        for i, tn in enumerate(tab_names):
            tx = 10 + i * 126
            col = GOLD if tab == i else GRAY
            bg = (40, 40, 60) if tab == i else (20, 20, 35)
            pygame.draw.rect(screen, bg, (tx, 50, 120, 35), border_radius=6)
            pygame.draw.rect(screen, col, (tx, 50, 120, 35), 2, border_radius=6)
            tt = font_sm.render(f"[{i+1}] {tn}", True, col)
            screen.blit(tt, (tx + 60 - tt.get_width() // 2, 57))

        # Offline message
        if offline_msg_timer > 0:
            offline_msg_timer -= 1
            msg = font_md.render(f"While away: {offline_wins} wins, {len(offline_loot)} abilities!", True, GOLD)
            screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, 92))

        y_start = 120

        if tab == 0:  # Overview
            equip_mode = "Custom Loadout" if ai.get("custom_equip") else "Mirrors Player"
            equip_mode_line = f"Equip mode: {equip_mode}" if ai_type == "fighter" else ""
            brain = ai.get("brain", {})
            active_mods = brain.get("mods", [])
            personality = brain.get("personality", "helpful")
            lines = [
                (f"AI: {ai_name}  |  Type: {atype_label}  |  Personality: {personality.title()}", atype_color),
                (f"Wins (total): {ai_wins_total}", CYAN),
                (f"Equipped: {len(ai_eq)}/{ai_slots} slots", GREEN),
                (f"Inventory: {len(ai_inv)} abilities", WHITE),
                (f"Shared Parts: {len(ai_parts)}", YELLOW),
                (f"Collects left: {'Unlimited' if 'unlimited_collect' in active_mods else collects_left}/hr" + (" (no CD)" if "no_cooldown" in active_mods else ""), ORANGE if collects_left > 0 or "unlimited_collect" in active_mods else RED),
            ]
            if active_mods:
                mod_names = ", ".join(AI_CODEABLE_MODS[m]["name"] for m in active_mods if m in AI_CODEABLE_MODS)
                lines.append((f"Active Mods: {mod_names}", MAGENTA))
            if equip_mode_line:
                lines.append((equip_mode_line, CYAN if ai.get("custom_equip") else GREEN))
            lines += [
                ("", WHITE),
                (f"Team size: {len(team)} AI(s)  |  Total waves: {total_waves}", LIGHT_GRAY),
                (f"Next AI unlock: {next_ai_cost} total waves {'(READY!)' if can_add_ai else ''}", MAGENTA if can_add_ai else GRAY),
                (f"Rounds until next part: {3 - save_data.get('rounds_since_part', 0)}", PINK),
            ]
            if time_until_reset > 0 and collects_left <= 0:
                mins = int(time_until_reset // 60); secs = int(time_until_reset % 60)
                lines.append((f"Collect resets in: {mins}m {secs}s", PINK))

            for i, (txt, col) in enumerate(lines):
                t = font_md.render(txt, True, col)
                screen.blit(t, (60, y_start + i * 32))

            # Draw AI visual
            ax, ay = WIDTH - 140, y_start + 50
            ai_c = AI_COLORS[ai_idx % len(AI_COLORS)]
            pygame.draw.rect(screen, ai_c, (ax, ay, 50, 60), border_radius=6)
            pygame.draw.circle(screen, tuple(min(255, c + 60) for c in ai_c), (ax + 25, ay - 10), 15)
            if ai_type == "fighter":
                # Sword icon
                pygame.draw.line(screen, GOLD, (ax + 40, ay - 15), (ax + 55, ay - 30), 3)
                pygame.draw.line(screen, GOLD, (ax + 50, ay - 28), (ax + 57, ay - 22), 2)
            else:
                # Pickaxe icon
                pygame.draw.line(screen, GRAY, (ax + 40, ay - 15), (ax + 55, ay - 25), 2)
            for j, part in enumerate(ai_parts):
                pc = part.get("color", YELLOW)
                px = ax + 25 + int(30 * math.cos(j * 1.2 + time.time()))
                py2 = ay + 30 + int(20 * math.sin(j * 0.9 + time.time()))
                pygame.draw.circle(screen, pc, (px, py2), 4)
            lbl = font_sm.render(ai_name, True, ai_c)
            screen.blit(lbl, (ax + 25 - lbl.get_width() // 2, ay + 70))

        elif tab == 1:  # Equip
            sb_color = CYAN if search_active else GRAY
            pygame.draw.rect(screen, (30, 28, 42), (50, y_start, WIDTH - 100, 26), border_radius=6)
            pygame.draw.rect(screen, sb_color, (50, y_start, WIDTH - 100, 26), 2, border_radius=6)
            if search_text:
                sb_txt = font_sm.render(f"Search: {search_text}", True, WHITE)
            elif search_active:
                sb_txt = font_sm.render("Type to search...", True, GRAY)
            else:
                sb_txt = font_sm.render(f"F: Search  |  {ai_name} Slots: {len(ai_eq)}/{ai_slots}  |  Enter to toggle", True, GRAY)
            screen.blit(sb_txt, (58, y_start + 4))

            selected = min(selected, max(0, len(filtered_items) - 1))
            y = y_start + 34
            max_show = 12
            if selected >= scroll + max_show: scroll = selected - max_show + 1
            if selected < scroll: scroll = selected
            for i in range(scroll, min(scroll + max_show, len(filtered_items))):
                item = filtered_items[i]
                equipped = item in ai_eq
                ab, lv = get_ability_data(item)
                col = ab["color"] if ab else WHITE
                prefix = "[E] " if equipped else "    "
                lv_str = f" Lv{lv}" if lv > 1 else ""
                txt = f"{prefix}{get_base_name(item)}{lv_str}"
                sel_col = GOLD if i == selected else col
                bg = (40, 40, 55) if i == selected else (20, 20, 30)
                pygame.draw.rect(screen, bg, (50, y, WIDTH - 100, 30), border_radius=4)
                t = font_sm.render(txt, True, sel_col)
                screen.blit(t, (60, y + 5))
                if ab:
                    desc_t = font_sm.render(ab["desc"], True, GRAY)
                    screen.blit(desc_t, (WIDTH - 60 - desc_t.get_width(), y + 5))
                y += 34
            if len(filtered_items) == 0:
                t = font_md.render("No matches." if search_text else "No AI abilities yet!", True, GRAY)
                screen.blit(t, (60, y_start + 50))

        elif tab == 2:  # Parts (shared)
            header = font_md.render(f"Shared Parts ({len(ai_parts)}) — All AIs benefit", True, YELLOW)
            screen.blit(header, (60, y_start))
            y = y_start + 40
            if len(ai_parts) == 0:
                t = font_md.render("No parts yet! Win 3 rounds to earn one.", True, GRAY)
                screen.blit(t, (60, y))
            else:
                for i, part in enumerate(ai_parts):
                    pc = part.get("color", YELLOW)
                    pygame.draw.rect(screen, (30, 30, 45), (50, y, WIDTH - 100, 32), border_radius=4)
                    pygame.draw.circle(screen, pc, (70, y + 16), 8)
                    t = font_sm.render(f"{part['name']} — {part['desc']}", True, pc)
                    screen.blit(t, (90, y + 6))
                    y += 36

        elif tab == 3:  # Collect
            sb_color = CYAN if search_active else GRAY
            pygame.draw.rect(screen, (30, 28, 42), (50, y_start, WIDTH - 100, 26), border_radius=6)
            pygame.draw.rect(screen, sb_color, (50, y_start, WIDTH - 100, 26), 2, border_radius=6)
            if search_text:
                sb_txt = font_sm.render(f"Search: {search_text}", True, WHITE)
            elif search_active:
                sb_txt = font_sm.render("Type to search...", True, GRAY)
            else:
                sb_txt = font_sm.render(f"F: Search  |  {ai_name} Inv ({len(ai_inv)})  |  Take {collects_left} more", True, GRAY)
            screen.blit(sb_txt, (58, y_start + 4))

            y = y_start + 34
            if len(filtered_items) == 0:
                t = font_md.render("No matches." if search_text else "AI has no abilities!", True, GRAY)
                screen.blit(t, (60, y))
            else:
                selected = min(selected, max(0, len(filtered_items) - 1))
                max_show = 12
                if selected >= scroll + max_show: scroll = selected - max_show + 1
                if selected < scroll: scroll = selected
                for i in range(scroll, min(scroll + max_show, len(filtered_items))):
                    item = filtered_items[i]
                    ab, lv = get_ability_data(item)
                    col = ab["color"] if ab else WHITE
                    is_equipped = item in ai_eq
                    sel_col = GOLD if i == selected else col
                    bg = (40, 40, 55) if i == selected else (20, 20, 30)
                    pygame.draw.rect(screen, bg, (50, y, WIDTH - 100, 30), border_radius=4)
                    prefix = "[E] " if is_equipped else "    "
                    t = font_sm.render(f"{prefix}{item}", True, sel_col)
                    screen.blit(t, (60, y + 5))
                    if ab:
                        desc_t = font_sm.render(ab["desc"], True, GRAY)
                        screen.blit(desc_t, (WIDTH - 60 - desc_t.get_width(), y + 5))
                    y += 34
                if collects_left <= 0:
                    mins = int(time_until_reset // 60); secs = int(time_until_reset % 60)
                    t = font_md.render(f"Collect resets in {mins}m {secs}s", True, RED)
                    screen.blit(t, (60, HEIGHT - 80))
                else:
                    t = font_sm.render("Enter = take ability to YOUR inventory", True, GREEN)
                    screen.blit(t, (60, HEIGHT - 80))

        elif tab == 4:  # Chat
            brain = ai.get("brain", {"chat_log": [], "mods": [], "code_count": 0, "personality": "helpful"})
            brain_log = brain.get("chat_log", [])
            personality = brain.get("personality", "helpful")
            active_mods = brain.get("mods", [])
            code_cost = (brain.get("code_count", 0) + 1) * 10

            # Header: personality + mods info
            p_col = {
                "helpful": GREEN, "mean": RED, "funny": YELLOW, "serious": CYAN
            }.get(personality, WHITE)
            header = font_sm.render(f"Personality: {personality.title()}  |  Mods: {len(active_mods)}  |  Next code: {code_cost} waves", True, p_col)
            screen.blit(header, (60, y_start - 2))

            # Show active mods strip
            if active_mods:
                mod_str = ", ".join(AI_CODEABLE_MODS[m]["name"] for m in active_mods if m in AI_CODEABLE_MODS)
                mod_t = font_sm.render(f"Active: {mod_str}", True, MAGENTA)
                screen.blit(mod_t, (60, y_start + 16))
                msg_y_start = y_start + 36
            else:
                msg_y_start = y_start + 18

            # Show messages from brain (per-AI memory)
            y = msg_y_start
            max_msgs = (HEIGHT - 120 - msg_y_start) // 22
            show_msgs = brain_log[-max_msgs:] if brain_log else []
            for m in show_msgs:
                is_you = m.get("from") == "you"
                col = CYAN if is_you else AI_COLORS[ai_idx % len(AI_COLORS)]
                prefix = "You" if is_you else m.get("from", ai_name)
                msg_text = m.get("msg", "")
                # Truncate long messages for display
                if len(msg_text) > 80:
                    msg_text = msg_text[:77] + "..."
                t = font_sm.render(f"[{prefix}]: {msg_text}", True, col)
                screen.blit(t, (60, y))
                y += 22

            # Chat input
            input_y = HEIGHT - 80
            pygame.draw.rect(screen, (30, 28, 42), (50, input_y, WIDTH - 100, 30), border_radius=6)
            ib_col = CYAN if chat_active else GRAY
            pygame.draw.rect(screen, ib_col, (50, input_y, WIDTH - 100, 30), 2, border_radius=6)
            if chat_active:
                ct = font_sm.render(f"> {chat_input}_", True, WHITE)
            else:
                ct = font_sm.render("C: Chat  |  Say 'help' for commands  |  'code' + mod name", True, GRAY)
            screen.blit(ct, (58, input_y + 6))

            # Hint at bottom
            hint_t = font_sm.render("Try: 'code no cooldown', 'be funny', 'what mods', 'help'", True, DARK_GRAY)
            screen.blit(hint_t, (60, HEIGHT - 45))

        elif tab == 5:  # Add AI
            t = font_md.render("Add a New AI Companion", True, MAGENTA)
            screen.blit(t, (60, y_start))

            t2 = font_md.render(f"Current team: {len(team)} AI(s)", True, WHITE)
            screen.blit(t2, (60, y_start + 40))
            t3 = font_md.render(f"Your total waves: {total_waves}", True, CYAN)
            screen.blit(t3, (60, y_start + 72))
            t4 = font_md.render(f"Cost for next AI: {next_ai_cost} total waves", True, GOLD if can_add_ai else RED)
            screen.blit(t4, (60, y_start + 104))

            if can_add_ai:
                # Option 0: Add Offline Bot
                bg0 = (40, 40, 60) if selected == 0 else (20, 20, 35)
                col0 = GOLD if selected == 0 else CYAN
                pygame.draw.rect(screen, bg0, (60, y_start + 150, WIDTH - 120, 40), border_radius=6)
                pygame.draw.rect(screen, col0, (60, y_start + 150, WIDTH - 120, 40), 2, border_radius=6)
                ot = font_md.render("+ Add Offline Bot (farms abilities while idle)", True, col0)
                screen.blit(ot, (80, y_start + 158))

                # Option 1: Add Fighter AI
                bg1 = (40, 40, 60) if selected == 1 else (20, 20, 35)
                col1 = GOLD if selected == 1 else GREEN
                pygame.draw.rect(screen, bg1, (60, y_start + 200, WIDTH - 120, 40), border_radius=6)
                pygame.draw.rect(screen, col1, (60, y_start + 200, WIDTH - 120, 40), 2, border_radius=6)
                ft = font_md.render("+ Add Fighter AI (helps you in battles!)", True, col1)
                screen.blit(ft, (80, y_start + 208))

                selected = min(selected, 1)
            else:
                nt = font_md.render(f"Need {next_ai_cost - total_waves} more total waves!", True, RED)
                screen.blit(nt, (60, y_start + 150))

            # Show current team
            ty = y_start + 260
            t5 = font_md.render("Your Team:", True, YELLOW)
            screen.blit(t5, (60, ty))
            ty += 32
            for i, a in enumerate(team):
                c = AI_COLORS[i % len(AI_COLORS)]
                atype = "Fighter" if a.get("type") == "fighter" else "Offline Bot"
                inv_count = len(a.get("inventory", []))
                eq_count = len(a.get("equipped", []))
                txt = f"{a.get('name','?')} [{atype}] — {eq_count} equipped, {inv_count} in inv, {a.get('wins',0)} wins"
                t6 = font_sm.render(txt, True, c)
                screen.blit(t6, (80, ty))
                ty += 24

        elif tab == 6:  # School
            school = ai.setdefault("brain", {}).setdefault("school", {"level": 0, "skills": [], "xp": 0})
            school_xp = school.get("xp", 0)
            school_lv = school.get("level", 0)
            learned = school.get("skills", [])
            ai_type_cur = ai.get("type", "offline")

            # ── Head AI Professor Banner ──
            pygame.draw.rect(screen, (30, 30, 55), (40, y_start, WIDTH - 80, 56), border_radius=8)
            pygame.draw.rect(screen, MAGENTA, (40, y_start, WIDTH - 80, 56), 2, border_radius=8)
            prof_t = font_md.render("Professor (Head AI)", True, MAGENTA)
            screen.blit(prof_t, (60, y_start + 4))
            # Pick a lesson to show
            import time as _time_mod
            lesson_idx = int(_time_mod.time() / 5) % len(HEAD_AI_LESSONS)
            lesson_t = font_sm.render(f'Lesson: "{HEAD_AI_LESSONS[lesson_idx]}"', True, YELLOW)
            # Truncate if too wide
            if lesson_t.get_width() > WIDTH - 120:
                lesson_text = HEAD_AI_LESSONS[lesson_idx][:60] + "..."
                lesson_t = font_sm.render(f'Lesson: "{lesson_text}"', True, YELLOW)
            screen.blit(lesson_t, (60, y_start + 30))

            # ── XP and level bar ──
            bar_y = y_start + 65
            xp_t = font_md.render(f"School Level {school_lv}  |  XP: {school_xp}", True, CYAN)
            screen.blit(xp_t, (60, bar_y))
            tip_t = font_sm.render("(Earn XP: School tab open, wins, chat, Self-Study skill)", True, GRAY)
            screen.blit(tip_t, (60, bar_y + 28))

            # ── Available Skills List ──
            list_y = bar_y + 56
            hdr_t = font_md.render("Available Skills:", True, WHITE)
            screen.blit(hdr_t, (60, list_y))
            list_y += 30

            avail = [(k, v) for k, v in AI_SCHOOL_SKILLS.items()
                     if v["type"] == "general" or (v["type"] == "fighter" and ai_type_cur == "fighter")]

            max_visible = min(len(avail), 8)
            view_start = max(0, scroll)
            for idx in range(view_start, min(view_start + max_visible, len(avail))):
                sk_id, sk_info = avail[idx]
                cur_lv = _get_school_skill_lv(ai, sk_id)
                cost = sk_info["base_cost"] * (cur_lv + 1) if cur_lv < sk_info["max_lv"] else 0
                maxed = cur_lv >= sk_info["max_lv"]

                row_y = list_y + (idx - view_start) * 38
                is_sel = (idx == selected)
                bg_col = (50, 50, 70) if is_sel else (25, 25, 40)
                border_col = GOLD if is_sel else (60, 60, 80)
                pygame.draw.rect(screen, bg_col, (50, row_y, WIDTH - 100, 34), border_radius=5)
                pygame.draw.rect(screen, border_col, (50, row_y, WIDTH - 100, 34), 1, border_radius=5)

                # Icon indicators
                icon_map = {"brain": "B", "book": "L", "star": "*", "coin": "$", "clock": "@",
                            "shield": "S", "sword": "X", "heart": "+", "bolt": "!"}
                icon_ch = icon_map.get(sk_info.get("icon", ""), "?")

                # Cheat code badge
                is_cheat = sk_info["type"] == "fighter"
                cheat_tag = " [CHEAT]" if is_cheat else ""

                if maxed:
                    name_col = GREEN
                    status_str = "MAX"
                elif school_xp >= cost:
                    name_col = CYAN
                    status_str = f"Lv{cur_lv}→{cur_lv+1} ({cost} XP)"
                else:
                    name_col = GRAY
                    status_str = f"Lv{cur_lv}/{sk_info['max_lv']} (Need {cost} XP)"

                nm_t = font_sm.render(f"[{icon_ch}] {sk_info['name']}{cheat_tag}", True, name_col)
                screen.blit(nm_t, (58, row_y + 2))
                st_t = font_sm.render(status_str, True, GREEN if maxed else (GOLD if school_xp >= cost else RED))
                screen.blit(st_t, (WIDTH - 58 - st_t.get_width(), row_y + 2))
                desc_t = font_sm.render(sk_info["desc"][:55], True, (160, 160, 180))
                screen.blit(desc_t, (58, row_y + 17))

            # Clamp selected
            if avail:
                selected = min(selected, len(avail) - 1)

            # ── Learned Skills Summary ──
            summary_y = list_y + max_visible * 38 + 10
            unique_learned = list(set(learned))
            if unique_learned:
                lt = font_md.render("Learned Skills:", True, GREEN)
                screen.blit(lt, (60, summary_y))
                summary_y += 26
                for sk_id in unique_learned:
                    if sk_id in AI_SCHOOL_SKILLS:
                        lv = learned.count(sk_id)
                        sk = AI_SCHOOL_SKILLS[sk_id]
                        tag = " [CHEAT]" if sk["type"] == "fighter" else ""
                        ls = font_sm.render(f"  {sk['name']} Lv{lv}/{sk['max_lv']}{tag}", True, CYAN)
                        screen.blit(ls, (60, summary_y))
                        summary_y += 20
            else:
                lt = font_sm.render("No skills learned yet. Select a skill and press Enter!", True, GRAY)
                screen.blit(lt, (60, summary_y))

        # Bottom hint
        hint_parts = ["Tab/1-7: Tabs", "Up/Down: Nav", "Esc: Back"]
        if len(team) > 1:
            hint_parts.insert(0, "Q/E: Switch AI")
        hint = font_sm.render("  |  ".join(hint_parts), True, GRAY)
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 20))

        pygame.display.flip()
        clock.tick(FPS)


# ─── SCREENS ─────────────────────────────────────────────────────────────────
def title_screen():
    """Main menu."""
    selected = 0
    options = ["Start Battle", "Equip Abilities", "Merge Abilities", "AI Companion", "Rebirth", "Reset Progress", "Quit"]
    btn_spacing = 48  # tighter spacing for 7 buttons
    btn_start_y = 270

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    selected = (selected - 1) % len(options)
                if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    selected = (selected + 1) % len(options)
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    return options[selected]
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for i, opt in enumerate(options):
                    oy = btn_start_y + i * btn_spacing
                    if WIDTH // 2 - 120 < mx < WIDTH // 2 + 120 and oy - 5 < my < oy + 36:
                        return options[i]

        screen.fill(BLACK)
        # Background effect
        t = pygame.time.get_ticks() / 1000
        for i in range(20):
            bx = int(WIDTH / 2 + math.sin(t + i * 0.5) * (150 + i * 10))
            by = int(HEIGHT / 2 + math.cos(t + i * 0.7) * (100 + i * 8))
            r = 5 + i * 2
            c = (int(60 + 10 * math.sin(t + i)), 20, int(100 + 10 * math.cos(t + i)))
            pygame.draw.circle(screen, c, (bx, by), r)

        # Title
        title1 = font_title.render("WOULD YOU RATHER", True, GOLD)
        title2 = font_xl.render("BATTLE 2", True, RED)
        screen.blit(title1, (WIDTH // 2 - title1.get_width() // 2, 100))
        screen.blit(title2, (WIDTH // 2 - title2.get_width() // 2, 175))

        # Options
        mx, my = pygame.mouse.get_pos()
        for i, opt in enumerate(options):
            oy = btn_start_y + i * btn_spacing
            is_hovered = WIDTH // 2 - 120 < mx < WIDTH // 2 + 120 and oy - 5 < my < oy + 36
            color = GOLD if (selected == i or is_hovered) else WHITE
            # Special colors for Rebirth and Reset
            if opt == "Rebirth":
                color = MAGENTA if (selected == i or is_hovered) else (200, 100, 255)
            elif opt == "Reset Progress":
                color = GOLD if (selected == i or is_hovered) else RED
            bg = (40, 40, 60) if (selected == i or is_hovered) else (20, 20, 30)
            pygame.draw.rect(screen, bg, (WIDTH // 2 - 120, oy - 5, 240, 36), border_radius=8)
            pygame.draw.rect(screen, color, (WIDTH // 2 - 120, oy - 5, 240, 36), 2, border_radius=8)
            txt = font_md.render(opt, True, color)
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, oy + 2))

        # Save info
        save_data = load_game()
        info = font_sm.render(f"Wave: {save_data['wave']}  |  Abilities: {len(save_data['inventory'])}  |  Wins: {save_data['wins']}", True, GRAY)
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT - 40))

        pygame.display.flip()
        clock.tick(FPS)


def would_you_rather_screen(wave, save_data):
    """Present two abilities to choose from. The unchosen one goes to inventory if you win."""
    all_names = list(ABILITIES.keys())

    # Weighted rarity: common types appear more often, powerful ones are rare
    RARITY_WEIGHTS = {
        "basic": 10, "special": 6, "elemental": 5, "emotion": 5,
        "nature": 5, "weather": 4, "sport": 4, "color": 4,
        "music": 4, "food": 4, "material": 3, "season": 3,
        "tech": 3, "magic": 3, "martial": 3, "candy": 3,
        "insect": 3, "pirate": 3, "space": 2, "dino": 2,
        "animal": 2, "mythical": 1,
    }
    weights = [RARITY_WEIGHTS.get(ABILITIES[n]["type"], 3) for n in all_names]

    # Per-ability overrides (boosted appearance rate)
    BOOSTED = {"Determination": 50}
    for i, n in enumerate(all_names):
        if n in BOOSTED:
            weights[i] = BOOSTED[n]

    # Pick 2 random abilities (weighted, no duplicates)
    choices = []
    pool = list(range(len(all_names)))
    pool_weights = list(weights)
    for _ in range(2):
        picked = random.choices(pool, weights=pool_weights, k=1)[0]
        choices.append(all_names[picked])
        idx_in_pool = pool.index(picked)
        pool.pop(idx_in_pool)
        pool_weights.pop(idx_in_pool)

    selected = None

    while selected is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                # Left card
                if 50 < mx < 420 and 200 < my < 450:
                    selected = 0
                # Right card
                if 480 < mx < 850 and 200 < my < 450:
                    selected = 1
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    selected = 0
                if event.key == pygame.K_2:
                    selected = 1

        screen.fill((20, 15, 30))

        # Title
        title = font_lg.render("WOULD YOU RATHER...?", True, GOLD)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

        sub = font_sm.render(f"Wave {wave} - Choose your power! (Unchosen one saved if you win)", True, LIGHT_GRAY)
        screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 90))

        mx, my = pygame.mouse.get_pos()

        for i, name in enumerate(choices):
            ab = ABILITIES[name]
            card_x = 50 + i * 430
            card_y = 200
            card_w = 370
            card_h = 250

            # Hover
            is_hovered = card_x < mx < card_x + card_w and card_y < my < card_y + card_h
            bg = (50, 45, 65) if is_hovered else (35, 30, 50)
            border = ab["color"] if is_hovered else GRAY

            pygame.draw.rect(screen, bg, (card_x, card_y, card_w, card_h), border_radius=12)
            pygame.draw.rect(screen, border, (card_x, card_y, card_w, card_h), 3, border_radius=12)

            # Ability icon (colored square)
            icon_rect = pygame.Rect(card_x + card_w // 2 - 25, card_y + 25, 50, 50)
            pygame.draw.rect(screen, ab["color"], icon_rect, border_radius=8)

            # Type badge
            type_colors = {"basic": GREEN, "special": GOLD, "animal": ORANGE}
            badge_color = type_colors.get(ab["type"], WHITE)
            badge = font_sm.render(ab["type"].upper(), True, badge_color)
            screen.blit(badge, (card_x + card_w // 2 - badge.get_width() // 2, card_y + 85))

            # Name
            name_txt = font_md.render(name, True, WHITE)
            screen.blit(name_txt, (card_x + card_w // 2 - name_txt.get_width() // 2, card_y + 115))

            # Description
            desc_txt = font_sm.render(ab["desc"], True, LIGHT_GRAY)
            screen.blit(desc_txt, (card_x + card_w // 2 - desc_txt.get_width() // 2, card_y + 150))

            # Key hint
            key_txt = font_sm.render(f"Press {i + 1} or Click", True, CYAN)
            screen.blit(key_txt, (card_x + card_w // 2 - key_txt.get_width() // 2, card_y + 210))

        pygame.display.flip()
        clock.tick(FPS)

    chosen = choices[selected]
    unchosen = choices[1 - selected]
    return chosen, unchosen


def equip_screen(save_data):
    """Equip abilities from inventory."""
    inventory = save_data.get("inventory", [])
    equipped = list(save_data.get("equipped", []))
    slots = save_data.get("slots", 2)
    scroll = 0
    max_visible = 8
    search_text = ""
    search_active = False

    running = True
    while running:
        # Filter inventory by search
        if search_text:
            filtered = [n for n in inventory if search_text.lower() in n.lower()]
        else:
            filtered = list(inventory)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if search_active:
                    if event.key == pygame.K_ESCAPE:
                        search_active = False
                        search_text = ""
                        scroll = 0
                    elif event.key == pygame.K_RETURN:
                        search_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        search_text = search_text[:-1]
                        scroll = 0
                    elif event.unicode and event.unicode.isprintable():
                        search_text += event.unicode
                        scroll = 0
                else:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                        running = False
                    if event.key == pygame.K_UP:
                        scroll = max(0, scroll - 1)
                    if event.key == pygame.K_DOWN:
                        scroll = min(max(0, len(filtered) - max_visible), scroll + 1)
                    if event.key == pygame.K_f:
                        search_active = True
                        search_text = ""
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                # Search bar click
                if 50 < mx < 550 and 95 < my < 125:
                    search_active = True
                else:
                    if search_active:
                        search_active = False
                # Inventory items
                for i in range(min(max_visible, len(filtered) - scroll)):
                    iy = 130 + i * 50
                    if 50 < mx < 550 and iy < my < iy + 44:
                        name = filtered[i + scroll]
                        if name in equipped:
                            equipped.remove(name)
                        elif len(equipped) < slots:
                            equipped.append(name)
                # Back button
                if WIDTH // 2 - 60 < mx < WIDTH // 2 + 60 and HEIGHT - 60 < my < HEIGHT - 25:
                    running = False
                # Scroll
                if event.button == 4:
                    scroll = max(0, scroll - 1)
                if event.button == 5:
                    scroll = min(max(0, len(filtered) - max_visible), scroll + 1)

        screen.fill((20, 15, 30))

        # Title
        title = font_lg.render("EQUIP ABILITIES", True, GOLD)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))

        slot_info = font_md.render(f"Slots: {len(equipped)}/{slots}  (Every 5 waves = +1 slot)", True, LIGHT_GRAY)
        screen.blit(slot_info, (WIDTH // 2 - slot_info.get_width() // 2, 60))

        # Search bar
        sb_color = CYAN if search_active else GRAY
        pygame.draw.rect(screen, (30, 28, 42), (50, 95, 500, 28), border_radius=6)
        pygame.draw.rect(screen, sb_color, (50, 95, 500, 28), 2, border_radius=6)
        if search_text:
            sb_txt = font_sm.render(f"Search: {search_text}", True, WHITE)
        elif search_active:
            sb_txt = font_sm.render("Type to search...", True, GRAY)
        else:
            sb_txt = font_sm.render("Click or press F to search  |  Click to equip/unequip  |  ESC = back", True, GRAY)
        screen.blit(sb_txt, (58, 99))

        mx, my = pygame.mouse.get_pos()

        if len(filtered) == 0:
            no_items = font_md.render("No abilities found." if search_text else "No abilities yet! Win battles to earn some.", True, GRAY)
            screen.blit(no_items, (WIDTH // 2 - no_items.get_width() // 2, 250))
        else:
            for i in range(min(max_visible, len(filtered) - scroll)):
                idx = i + scroll
                name = filtered[idx]
                ab_data, lv = get_ability_data(name)
                ab = ab_data if ab_data else {"color": GRAY, "desc": "???", "type": "?"}
                iy = 130 + i * 50
                is_equipped = name in equipped
                is_hovered = 50 < mx < 550 and iy < my < iy + 44

                bg = (60, 55, 80) if is_hovered else ((45, 50, 65) if is_equipped else (30, 28, 42))
                border = GOLD if is_equipped else (LIGHT_GRAY if is_hovered else DARK_GRAY)

                pygame.draw.rect(screen, bg, (50, iy, 500, 44), border_radius=8)
                pygame.draw.rect(screen, border, (50, iy, 500, 44), 2, border_radius=8)

                # Color dot
                pygame.draw.circle(screen, ab["color"], (75, iy + 22), 10)

                # Name
                name_txt = font_md.render(name, True, WHITE if is_equipped else LIGHT_GRAY)
                screen.blit(name_txt, (95, iy + 8))

                # Level badge
                if lv > 1:
                    lv_badge = font_sm.render(f"Lv{lv}", True, GOLD)
                    screen.blit(lv_badge, (340, iy + 12))

                # Type
                type_txt = font_sm.render(f"[{ab['type']}]", True, ab["color"])
                screen.blit(type_txt, (380, iy + 12))

                # Equipped badge
                if is_equipped:
                    eq_badge = font_sm.render("EQUIPPED", True, GOLD)
                    screen.blit(eq_badge, (460, iy + 12))

        # Currently equipped panel
        panel_x = 600
        panel_y = 130
        pygame.draw.rect(screen, (35, 30, 50), (panel_x, panel_y, 280, 300), border_radius=10)
        pygame.draw.rect(screen, GOLD, (panel_x, panel_y, 280, 300), 2, border_radius=10)

        eq_title = font_md.render("Equipped", True, GOLD)
        screen.blit(eq_title, (panel_x + 140 - eq_title.get_width() // 2, panel_y + 10))

        for i in range(slots):
            sy = panel_y + 50 + i * 48
            if i < len(equipped):
                name = equipped[i]
                ab_data, lv = get_ability_data(name)
                ab = ab_data if ab_data else {"color": GRAY}
                pygame.draw.rect(screen, ab["color"], (panel_x + 15, sy, 250, 38), border_radius=6)
                txt = font_sm.render(name, True, BLACK)
                screen.blit(txt, (panel_x + 25, sy + 10))
                if lv > 1:
                    lv_txt = font_sm.render(f"Lv{lv}", True, WHITE)
                    screen.blit(lv_txt, (panel_x + 230, sy + 10))
            else:
                pygame.draw.rect(screen, (50, 50, 60), (panel_x + 15, sy, 250, 38), border_radius=6)
                pygame.draw.rect(screen, GRAY, (panel_x + 15, sy, 250, 38), 1, border_radius=6)
                empty = font_sm.render("[ Empty Slot ]", True, GRAY)
                screen.blit(empty, (panel_x + 80, sy + 10))

        # Scroll indicator
        if len(filtered) > max_visible:
            scroll_txt = font_sm.render(f"Scroll: {scroll + 1}-{min(scroll + max_visible, len(filtered))}/{len(filtered)}", True, GRAY)
            screen.blit(scroll_txt, (50, 130 + max_visible * 50 + 5))

        # Back button
        back_hover = WIDTH // 2 - 60 < mx < WIDTH // 2 + 60 and HEIGHT - 60 < my < HEIGHT - 25
        back_color = GOLD if back_hover else WHITE
        pygame.draw.rect(screen, (40, 40, 55), (WIDTH // 2 - 60, HEIGHT - 60, 120, 35), border_radius=8)
        pygame.draw.rect(screen, back_color, (WIDTH // 2 - 60, HEIGHT - 60, 120, 35), 2, border_radius=8)
        back_txt = font_md.render("BACK", True, back_color)
        screen.blit(back_txt, (WIDTH // 2 - back_txt.get_width() // 2, HEIGHT - 55))

        pygame.display.flip()
        clock.tick(FPS)

    save_data["equipped"] = equipped
    save_game(save_data)
    return save_data


def merge_screen(save_data):
    """Merge 3 identical abilities to level them up.
    3x 'Speed Boost' → 'Speed Boost Lv2',  3x 'Speed Boost Lv2' → 'Speed Boost Lv3', etc."""
    inventory = list(save_data.get("inventory", []))
    scroll = 0
    max_visible = 8
    message = ""
    msg_timer = 0
    selected_name = None
    search_text = ""
    search_active = False

    def _build_groups(inv):
        """Group inventory by item name → count."""
        from collections import Counter
        return Counter(inv)

    running = True
    while running:
        groups = _build_groups(inventory)
        sorted_names = sorted(groups.keys())
        if search_text:
            sorted_names = [n for n in sorted_names if search_text.lower() in n.lower()]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if search_active:
                    if event.key == pygame.K_ESCAPE:
                        search_active = False
                        search_text = ""
                        scroll = 0
                    elif event.key == pygame.K_RETURN:
                        search_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        search_text = search_text[:-1]
                        scroll = 0
                    elif event.unicode and event.unicode.isprintable():
                        search_text += event.unicode
                        scroll = 0
                else:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_UP:
                        scroll = max(0, scroll - 1)
                    if event.key == pygame.K_DOWN:
                        scroll = min(max(0, len(sorted_names) - max_visible), scroll + 1)
                    if event.key == pygame.K_f:
                        search_active = True
                        search_text = ""
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                # Search bar click
                if 50 < mx < 500 and 100 < my < 128:
                    search_active = True
                else:
                    if search_active:
                        search_active = False
                # Click inventory items (grouped)
                for i in range(min(max_visible, len(sorted_names) - scroll)):
                    idx = i + scroll
                    iy = 140 + i * 46
                    if 50 < mx < 500 and iy < my < iy + 40:
                        clicked = sorted_names[idx]
                        if selected_name == clicked:
                            selected_name = None  # deselect
                        else:
                            selected_name = clicked
                # Merge button
                if 560 < mx < 800 and 420 < my < 465:
                    if selected_name and groups.get(selected_name, 0) >= 3:
                        base = get_base_name(selected_name)
                        cur_lv = get_level(selected_name)
                        new_lv = cur_lv + 1
                        result_name = make_leveled_name(base, new_lv)
                        # Remove 3 copies
                        removed = 0
                        for _ in range(3):
                            if selected_name in inventory:
                                inventory.remove(selected_name)
                                removed += 1
                        # Also unequip any removed copies
                        eq = save_data.get("equipped", [])
                        eq_removed = 0
                        while selected_name in eq and eq_removed < 3:
                            eq.remove(selected_name)
                            eq_removed += 1
                        # Add the leveled result
                        inventory.append(result_name)
                        message = f"3x {selected_name} → {result_name}!"
                        msg_timer = 200
                        selected_name = None
                    elif selected_name:
                        need = 3 - groups.get(selected_name, 0)
                        message = f"Need {need} more {selected_name} to merge!"
                        msg_timer = 150
                    else:
                        message = "Select an ability to merge!"
                        msg_timer = 120
                # Clear button
                if 560 < mx < 800 and 475 < my < 510:
                    selected_name = None
                # Back button
                if WIDTH // 2 - 60 < mx < WIDTH // 2 + 60 and HEIGHT - 55 < my < HEIGHT - 20:
                    running = False
                if event.button == 4:
                    scroll = max(0, scroll - 1)
                if event.button == 5:
                    scroll = min(max(0, len(sorted_names) - max_visible), scroll + 1)

        if msg_timer > 0:
            msg_timer -= 1

        screen.fill((15, 12, 25))

        title = font_lg.render("MERGE ABILITIES", True, MAGENTA)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 15))

        hint = font_sm.render("Combine 3 of the same ability to level it up!", True, LIGHT_GRAY)
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 60))

        # Search bar
        sb_color = CYAN if search_active else GRAY
        pygame.draw.rect(screen, (30, 28, 42), (50, 100, 450, 26), border_radius=6)
        pygame.draw.rect(screen, sb_color, (50, 100, 450, 26), 2, border_radius=6)
        if search_text:
            sb_txt = font_sm.render(f"Search: {search_text}", True, WHITE)
        elif search_active:
            sb_txt = font_sm.render("Type to search...", True, GRAY)
        else:
            sb_txt = font_sm.render("F: Search  |  3x Lv1→Lv2  |  3x Lv2→Lv3  |  ESC = back", True, GRAY)
        screen.blit(sb_txt, (58, 103))

        mx, my = pygame.mouse.get_pos()

        if len(sorted_names) == 0:
            no_items = font_sm.render("No abilities to merge yet!", True, GRAY)
            screen.blit(no_items, (50, 160))
        else:
            for i in range(min(max_visible, len(sorted_names) - scroll)):
                idx = i + scroll
                name = sorted_names[idx]
                count = groups[name]
                ab_data, lv = get_ability_data(name)
                ab = ab_data if ab_data else {"color": GRAY, "desc": "???", "type": "?"}
                iy = 140 + i * 46
                is_sel = (name == selected_name)
                is_hovered = 50 < mx < 500 and iy < my < iy + 40
                can_merge = count >= 3

                bg = (70, 50, 90) if is_sel else ((50, 45, 65) if is_hovered else (30, 28, 42))
                border = MAGENTA if is_sel else (GREEN if can_merge else (LIGHT_GRAY if is_hovered else DARK_GRAY))

                pygame.draw.rect(screen, bg, (50, iy, 450, 40), border_radius=8)
                pygame.draw.rect(screen, border, (50, iy, 450, 40), 2, border_radius=8)

                pygame.draw.circle(screen, ab["color"], (75, iy + 20), 10)

                # Show level star
                display_name = name
                if lv > 1:
                    display_name = name
                name_txt = font_sm.render(display_name, True, WHITE if is_sel else LIGHT_GRAY)
                screen.blit(name_txt, (95, iy + 10))

                # Count badge
                count_color = GREEN if can_merge else YELLOW
                cnt_txt = font_sm.render(f"x{count}", True, count_color)
                screen.blit(cnt_txt, (380, iy + 10))

                # Level badge
                if lv > 1:
                    lv_txt = font_sm.render(f"Lv{lv}", True, GOLD)
                    screen.blit(lv_txt, (430, iy + 10))

        # Merge panel
        panel_x = 520
        panel_y = 110
        pygame.draw.rect(screen, (35, 30, 50), (panel_x, panel_y, 360, 300), border_radius=10)
        pygame.draw.rect(screen, MAGENTA, (panel_x, panel_y, 360, 300), 2, border_radius=10)

        merge_title = font_md.render("Merge 3 → Level Up", True, MAGENTA)
        screen.blit(merge_title, (panel_x + 180 - merge_title.get_width() // 2, panel_y + 10))

        # Selected item display
        if selected_name:
            ab_data, lv = get_ability_data(selected_name)
            ab = ab_data if ab_data else {"color": GRAY, "desc": "???"}
            count = groups.get(selected_name, 0)
            base = get_base_name(selected_name)
            next_name = make_leveled_name(base, lv + 1)

            # Show 3 slots
            for slot in range(3):
                sy = panel_y + 50 + slot * 55
                filled = slot < count
                if filled:
                    pygame.draw.rect(screen, ab["color"], (panel_x + 20, sy, 320, 40), border_radius=6)
                    txt = font_sm.render(selected_name, True, BLACK)
                    screen.blit(txt, (panel_x + 35, sy + 10))
                else:
                    pygame.draw.rect(screen, (50, 50, 60), (panel_x + 20, sy, 320, 40), border_radius=6)
                    pygame.draw.rect(screen, GRAY, (panel_x + 20, sy, 320, 40), 1, border_radius=6)
                    e = font_sm.render(f"[ Need {selected_name} ]", True, GRAY)
                    screen.blit(e, (panel_x + 35, sy + 10))

            # Arrow and result
            arrow_y = panel_y + 50 + 3 * 55 - 10
            arrow = font_lg.render("↓", True, GOLD)
            screen.blit(arrow, (panel_x + 180 - arrow.get_width() // 2, arrow_y))

            res_y = arrow_y + 35
            if count >= 3:
                # Show result
                res_ab, _ = get_ability_data(next_name)
                rc = res_ab["color"] if res_ab else GOLD
                pygame.draw.rect(screen, rc, (panel_x + 20, res_y, 320, 40), border_radius=6)
                rtxt = font_md.render(f"★ {next_name}", True, BLACK)
                screen.blit(rtxt, (panel_x + 35, res_y + 8))
            else:
                pygame.draw.rect(screen, (40, 40, 50), (panel_x + 20, res_y, 320, 40), border_radius=6)
                need = 3 - count
                q = font_sm.render(f"Need {need} more!", True, RED)
                screen.blit(q, (panel_x + 100, res_y + 10))
        else:
            # No selection
            info_y = panel_y + 60
            for i, line in enumerate(["Select an ability from the", "inventory to see merge info.", "",
                                       "You need 3 copies of the", "same ability to level it up!",
                                       "", "Higher levels = stronger!"]):
                lt = font_sm.render(line, True, LIGHT_GRAY if line else GRAY)
                screen.blit(lt, (panel_x + 180 - lt.get_width() // 2, info_y + i * 24))

        # Merge button
        can_do = selected_name and groups.get(selected_name, 0) >= 3
        merge_hover = 560 < mx < 800 and 420 < my < 465
        mc = GOLD if (merge_hover and can_do) else (GREEN if can_do else GRAY)
        pygame.draw.rect(screen, (50, 40, 60), (560, 420, 240, 45), border_radius=8)
        pygame.draw.rect(screen, mc, (560, 420, 240, 45), 2, border_radius=8)
        mt = font_md.render("MERGE 3 → LV UP!", True, mc)
        screen.blit(mt, (680 - mt.get_width() // 2, 428))

        # Clear button
        clear_hover = 560 < mx < 800 and 475 < my < 510
        cc = LIGHT_GRAY if clear_hover else GRAY
        pygame.draw.rect(screen, (40, 35, 50), (560, 475, 240, 35), border_radius=8)
        pygame.draw.rect(screen, cc, (560, 475, 240, 35), 1, border_radius=8)
        ct = font_sm.render("Clear Selection", True, cc)
        screen.blit(ct, (680 - ct.get_width() // 2, 481))

        # Message
        if msg_timer > 0 and message:
            msg_color = GREEN if "→" in message else (RED if "Need" in message else YELLOW)
            msg_txt = font_md.render(message, True, msg_color)
            screen.blit(msg_txt, (WIDTH // 2 - msg_txt.get_width() // 2, HEIGHT - 90))

        # Back button
        back_hover = WIDTH // 2 - 60 < mx < WIDTH // 2 + 60 and HEIGHT - 55 < my < HEIGHT - 20
        back_color = GOLD if back_hover else WHITE
        pygame.draw.rect(screen, (40, 40, 55), (WIDTH // 2 - 60, HEIGHT - 55, 120, 35), border_radius=8)
        pygame.draw.rect(screen, back_color, (WIDTH // 2 - 60, HEIGHT - 55, 120, 35), 2, border_radius=8)
        back_txt = font_md.render("BACK", True, back_color)
        screen.blit(back_txt, (WIDTH // 2 - back_txt.get_width() // 2, HEIGHT - 50))

        pygame.display.flip()
        clock.tick(FPS)

    save_data["inventory"] = inventory
    save_game(save_data)
    return save_data


def fighter_ai_equip_screen(save_data):
    """After a win, let the player choose abilities for each fighter AI.
    Options: keep mirroring player (default) or pick a custom loadout."""
    _migrate_ai(save_data)
    team = save_data.get("ai_team", [])
    fighters = [(i, a) for i, a in enumerate(team) if a.get("type") == "fighter"]
    if not fighters:
        return

    for fi, (team_idx, ai_data) in enumerate(fighters):
        ai_name = ai_data.get("name", "Fighter")
        ai_color = AI_COLORS[team_idx % len(AI_COLORS)]
        ai_slots = ai_data.get("slots", 2)
        custom = ai_data.get("custom_equip", False)
        # Build item list from AI's inventory
        ai_inv = ai_data.get("inventory", [])
        ai_eq = list(ai_data.get("equipped", []))

        # Options: 0 = Mirror Player, 1 = Custom Loadout, 2+ = ability slots
        mode = 1 if custom else 0  # 0=mirror, 1=custom
        selected = 0
        scroll = 0

        done = False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        done = True
                    if event.key in (pygame.K_UP, pygame.K_w):
                        selected = max(0, selected - 1)
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        selected += 1
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if selected == 0:
                            # Toggle to Mirror mode
                            mode = 0
                            ai_data["custom_equip"] = False
                            save_game(save_data)
                            done = True
                        elif selected == 1:
                            # Toggle to Custom mode
                            mode = 1
                            ai_data["custom_equip"] = True
                            save_game(save_data)
                        elif mode == 1 and selected >= 2:
                            # Toggle equip/unequip an ability
                            idx = selected - 2 + scroll
                            all_items = list(ai_eq) + [a for a in ai_inv if a not in ai_eq]
                            if 0 <= idx < len(all_items):
                                item = all_items[idx]
                                if item in ai_eq:
                                    ai_eq.remove(item)
                                    ai_data["equipped"] = ai_eq
                                else:
                                    if len(ai_eq) < ai_slots:
                                        ai_eq.append(item)
                                        ai_data["equipped"] = ai_eq
                                save_game(save_data)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    # Mirror button
                    if 60 < mx < WIDTH - 60 and 150 < my < 190:
                        mode = 0; ai_data["custom_equip"] = False; save_game(save_data); done = True
                    # Custom button
                    elif 60 < mx < WIDTH - 60 and 200 < my < 240:
                        mode = 1; ai_data["custom_equip"] = True; save_game(save_data)
                    # Ability items (if custom mode)
                    elif mode == 1:
                        all_items = list(ai_eq) + [a for a in ai_inv if a not in ai_eq]
                        y_list = 280
                        for idx_i in range(len(all_items)):
                            iy = y_list + idx_i * 28 - scroll
                            if 60 < mx < WIDTH - 60 and iy < my < iy + 28 and y_list < my < HEIGHT - 50:
                                item = all_items[idx_i]
                                if item in ai_eq:
                                    ai_eq.remove(item)
                                    ai_data["equipped"] = ai_eq
                                else:
                                    if len(ai_eq) < ai_slots:
                                        ai_eq.append(item)
                                        ai_data["equipped"] = ai_eq
                                save_game(save_data)
                                break
                    # Done button
                    if WIDTH // 2 - 60 < mx < WIDTH // 2 + 60 and HEIGHT - 45 < my < HEIGHT - 15:
                        done = True

                if event.type == pygame.MOUSEWHEEL and mode == 1:
                    scroll = max(0, scroll - event.y * 28)

            # ── DRAW ──
            screen.fill((15, 15, 30))

            # Title
            title = font_lg.render(f"Equip {ai_name}", True, ai_color)
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 10))

            sub = font_sm.render(f"Fighter AI {fi+1}/{len(fighters)}  —  {len(ai_eq)}/{ai_slots} slots", True, LIGHT_GRAY)
            screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 50))

            info = font_sm.render("Choose how this AI gets its abilities:", True, WHITE)
            screen.blit(info, (60, 100))

            # Option 0: Mirror Player
            mirror_bg = (40, 60, 40) if mode == 0 else ((40, 40, 60) if selected == 0 else (20, 20, 35))
            mirror_col = GOLD if selected == 0 else (GREEN if mode == 0 else GRAY)
            pygame.draw.rect(screen, mirror_bg, (60, 150, WIDTH - 120, 36), border_radius=6)
            pygame.draw.rect(screen, mirror_col, (60, 150, WIDTH - 120, 36), 2, border_radius=6)
            mirror_lbl = ">> Mirror Player's Equipped (active)" if mode == 0 else "Mirror Player's Equipped"
            mt = font_md.render(mirror_lbl, True, GREEN if mode == 0 else LIGHT_GRAY)
            screen.blit(mt, (80, 156))

            # Option 1: Custom Loadout
            custom_bg = (40, 40, 60) if mode == 1 else ((40, 40, 60) if selected == 1 else (20, 20, 35))
            custom_col = GOLD if selected == 1 else (CYAN if mode == 1 else GRAY)
            pygame.draw.rect(screen, custom_bg, (60, 200, WIDTH - 120, 36), border_radius=6)
            pygame.draw.rect(screen, custom_col, (60, 200, WIDTH - 120, 36), 2, border_radius=6)
            custom_lbl = ">> Custom Loadout (active)" if mode == 1 else "Custom Loadout"
            ct = font_md.render(custom_lbl, True, CYAN if mode == 1 else LIGHT_GRAY)
            screen.blit(ct, (80, 206))

            # If custom mode, show ability list
            if mode == 1:
                all_items = list(ai_eq) + [a for a in ai_inv if a not in ai_eq]
                if not all_items:
                    nt = font_sm.render("No abilities in AI inventory. Win battles to earn some!", True, RED)
                    screen.blit(nt, (60, 280))
                else:
                    hdr = font_sm.render(f"Click or Enter to toggle equip ({len(ai_eq)}/{ai_slots}):", True, YELLOW)
                    screen.blit(hdr, (60, 256))
                    y_list = 280
                    for idx_i, item in enumerate(all_items):
                        iy = y_list + idx_i * 28 - scroll
                        if iy < 276 or iy > HEIGHT - 55:
                            continue
                        is_eq = item in ai_eq
                        is_sel = (selected == idx_i + 2)
                        bg = (50, 60, 50) if is_eq else ((40, 40, 60) if is_sel else (20, 20, 30))
                        col = GREEN if is_eq else (GOLD if is_sel else LIGHT_GRAY)
                        pygame.draw.rect(screen, bg, (60, iy, WIDTH - 120, 26), border_radius=4)
                        prefix = "[E] " if is_eq else "    "
                        base = get_base_name(item)
                        lv = get_level(item)
                        lv_str = f" Lv{lv}" if lv > 1 else ""
                        ab_data = ABILITIES.get(base, {})
                        desc_short = ab_data.get("desc", "")[:40]
                        t = font_sm.render(f"{prefix}{item}  {desc_short}", True, col)
                        screen.blit(t, (68, iy + 4))
            else:
                # Show what player has equipped
                player_eq = save_data.get("equipped", [])
                info2 = font_sm.render("This AI will use your equipped abilities in battle:", True, YELLOW)
                screen.blit(info2, (60, 260))
                for pi, pe in enumerate(player_eq):
                    ey = 288 + pi * 24
                    if ey > HEIGHT - 60:
                        break
                    t = font_sm.render(f"  • {pe}", True, GREEN)
                    screen.blit(t, (70, ey))

            # Done button
            done_bg = (40, 60, 40)
            pygame.draw.rect(screen, done_bg, (WIDTH // 2 - 60, HEIGHT - 45, 120, 30), border_radius=6)
            pygame.draw.rect(screen, GREEN, (WIDTH // 2 - 60, HEIGHT - 45, 120, 30), 2, border_radius=6)
            dt = font_md.render("Done", True, GREEN)
            screen.blit(dt, (WIDTH // 2 - dt.get_width() // 2, HEIGHT - 42))

            # Clamp selected
            max_sel = 1
            if mode == 1:
                all_items = list(ai_eq) + [a for a in ai_inv if a not in ai_eq]
                max_sel = 1 + len(all_items)
            selected = min(selected, max_sel)

            pygame.display.flip()
            clock.tick(FPS)


def you_win_screen(wave, unchosen_ability, earned_part=None):
    """Show victory screen for the round."""
    alpha = 0
    start_time = pygame.time.get_ticks()

    while True:
        dt = pygame.time.get_ticks() - start_time
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                if dt > 1000:  # Prevent accidental skip
                    return

        alpha = min(255, alpha + 5)

        screen.fill((10, 20, 10))

        # Victory particles
        t = pygame.time.get_ticks() / 1000
        for i in range(30):
            px = int(WIDTH / 2 + math.sin(t * 2 + i * 0.7) * (100 + i * 8))
            py = int(HEIGHT / 2 + math.cos(t * 3 + i * 0.5) * (80 + i * 5))
            c = [GOLD, YELLOW, GREEN, CYAN, WHITE][i % 5]
            pygame.draw.circle(screen, c, (px, py), 3 + i % 4)

        # YOU WIN text
        win_text = font_title.render("YOU WIN!", True, GOLD)
        screen.blit(win_text, (WIDTH // 2 - win_text.get_width() // 2, 100))

        wave_text = font_lg.render(f"Wave {wave} Complete!", True, GREEN)
        screen.blit(wave_text, (WIDTH // 2 - wave_text.get_width() // 2, 180))

        y_off = 250
        if unchosen_ability:
            reward = font_md.render(f"Ability Earned: {unchosen_ability}", True, CYAN)
            screen.blit(reward, (WIDTH // 2 - reward.get_width() // 2, y_off))
            if unchosen_ability in ABILITIES:
                ab = ABILITIES[unchosen_ability]
                desc = font_sm.render(ab["desc"], True, LIGHT_GRAY)
                screen.blit(desc, (WIDTH // 2 - desc.get_width() // 2, y_off + 30))
            y_off += 65

        if earned_part:
            pc = earned_part.get("color", YELLOW)
            part_txt = font_md.render(f"AI Part Earned: {earned_part['name']}", True, pc)
            screen.blit(part_txt, (WIDTH // 2 - part_txt.get_width() // 2, y_off))
            part_desc = font_sm.render(earned_part["desc"], True, LIGHT_GRAY)
            screen.blit(part_desc, (WIDTH // 2 - part_desc.get_width() // 2, y_off + 30))
            y_off += 65

        if wave % 5 == 0:
            slot_msg = font_md.render("+1 ABILITY SLOT UNLOCKED!", True, MAGENTA)
            screen.blit(slot_msg, (WIDTH // 2 - slot_msg.get_width() // 2, y_off))

        cont = font_sm.render("Press any key to continue...", True, GRAY)
        if dt > 1000 and (dt // 500) % 2 == 0:
            screen.blit(cont, (WIDTH // 2 - cont.get_width() // 2, HEIGHT - 60))

        pygame.display.flip()
        clock.tick(FPS)


def you_lose_screen(wave):
    """Show defeat screen."""
    start_time = pygame.time.get_ticks()
    while True:
        dt = pygame.time.get_ticks() - start_time
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                if dt > 800:
                    return

        screen.fill((30, 10, 10))

        lose_text = font_title.render("DEFEATED!", True, RED)
        screen.blit(lose_text, (WIDTH // 2 - lose_text.get_width() // 2, 150))

        wave_text = font_lg.render(f"Fell on Wave {wave}", True, ORANGE)
        screen.blit(wave_text, (WIDTH // 2 - wave_text.get_width() // 2, 240))

        tip = font_md.render("Try equipping different abilities!", True, LIGHT_GRAY)
        screen.blit(tip, (WIDTH // 2 - tip.get_width() // 2, 320))

        cont = font_sm.render("Press any key to continue...", True, GRAY)
        if dt > 800 and (dt // 500) % 2 == 0:
            screen.blit(cont, (WIDTH // 2 - cont.get_width() // 2, HEIGHT - 60))

        pygame.display.flip()
        clock.tick(FPS)


# ─── MAIN BATTLE LOOP ───────────────────────────────────────────────────────
def battle(wave, save_data, chosen_ability):
    """Run one wave of battle."""
    global particles

    platforms, walls = generate_course(wave)

    # Create player
    player = Fighter(100, GROUND_Y - 60, is_ai=False)
    player.apply_abilities(save_data.get("equipped", []))

    # Also apply the chosen ability for this round
    all_equipped = list(save_data.get("equipped", [])) + [chosen_ability]
    player.apply_abilities(all_equipped)

    # Create enemy AI
    ai = Fighter(WIDTH - 150, GROUND_Y - 60, is_ai=True)
    ai_ability_count = 1 + wave // 5
    ai_ability_count = min(ai_ability_count, len(ABILITIES))
    ai_abilities = random.sample(list(ABILITIES.keys()), ai_ability_count)
    ai.apply_abilities(ai_abilities)
    ai.body_color = RED

    # Create fighter AI companions (friendly AIs that help the player)
    # Fighter AIs mirror player's equipped abilities unless they have custom_equip set
    _migrate_ai(save_data)
    fighter_ais = []
    player_equip = list(save_data.get("equipped", [])) + [chosen_ability]
    team = save_data.get("ai_team", [])
    total_cheat_shield = 0
    total_cheat_god = 0
    total_cheat_dodge = 0
    total_cheat_crit = 0
    total_cheat_loot = 0
    for idx, ai_data in enumerate(team):
        if ai_data.get("type") == "fighter":
            fx = 60 + idx * 40
            fy = GROUND_Y - 60
            fai = Fighter(fx, fy, is_ai=True)
            # Use custom loadout if set, otherwise mirror player's equipped
            if ai_data.get("custom_equip"):
                fai.apply_abilities(ai_data.get("equipped", []))
            else:
                fai.apply_abilities(player_equip)
            fai_color = AI_COLORS[idx % len(AI_COLORS)]
            fai.body_color = fai_color
            fai._fighter_name = ai_data.get("name", "Fighter")
            fai._fighter_color = fai_color
            # ── Accumulate School cheat code effects ──
            total_cheat_shield += _get_school_skill_lv(ai_data, "cheat_shield")
            total_cheat_god += _get_school_skill_lv(ai_data, "cheat_god")
            total_cheat_dodge += _get_school_skill_lv(ai_data, "cheat_dodge")
            total_cheat_crit += _get_school_skill_lv(ai_data, "cheat_crit")
            total_cheat_loot += _get_school_skill_lv(ai_data, "cheat_loot")
            speed_lv = _get_school_skill_lv(ai_data, "cheat_speed")
            if speed_lv > 0:
                fai.fire_rate = max(5, fai.fire_rate - speed_lv * 3)
            fighter_ais.append(fai)

    # Apply accumulated fighter cheat bonuses to player
    player.shield += total_cheat_shield

    bullets = []
    particles = []
    paused = False
    result = None  # "win" or "lose"

    hit_flash_player = 0
    hit_flash_ai = 0

    # ── READY, GET SET, GO! countdown ──
    countdown_start = pygame.time.get_ticks()
    countdown_msgs = [("READY...", CYAN, 1000), ("GET SET...", YELLOW, 2000), ("GO!", GREEN, 2800)]
    countdown_done = False
    while not countdown_done:
        now = pygame.time.get_ticks() - countdown_start
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        draw_background(screen, wave)
        draw_course(screen, platforms, walls, wave)
        player.draw(screen, wave)
        ai.draw(screen, wave)
        for fai in fighter_ais:
            fai.draw(screen, wave)
        draw_hud(screen, wave, player, save_data)

        # Dim overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))

        # Show the current countdown word
        current_msg = None
        for msg, color, threshold in countdown_msgs:
            if now >= threshold:
                current_msg = (msg, color)
        if current_msg is None:
            current_msg = (countdown_msgs[0][0], countdown_msgs[0][1])

        # Pulse effect
        scale = 1.0 + 0.1 * math.sin(now / 80)
        txt = font_title.render(current_msg[0], True, current_msg[1])
        scaled = pygame.transform.scale(txt, (int(txt.get_width() * scale), int(txt.get_height() * scale)))
        screen.blit(scaled, (WIDTH // 2 - scaled.get_width() // 2, HEIGHT // 2 - scaled.get_height() // 2 - 30))

        pygame.display.flip()
        clock.tick(FPS)

        if now >= 3300:
            countdown_done = True

    while result is None:
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Open equip screen mid-battle
                    save_data = equip_screen(save_data)
                    player.apply_abilities(list(save_data.get("equipped", [])) + [chosen_ability])
                if event.key == pygame.K_s and player.special_ready:
                    # Activate special ability burst!
                    special_bullets = player.use_special()
                    bullets.extend(special_bullets)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click = fire
                    mx, my = pygame.mouse.get_pos()
                    new_bullets = player.fire(mx, my)
                    bullets.extend(new_bullets)

        if not paused:
            # Update player
            player.update(keys, platforms, walls)

            # Update enemy AI
            ai.update(keys, platforms, walls)
            player_bullets = [b for b in bullets if b.owner == "player" and b.alive]
            ai_bullets = ai.ai_update(player, platforms, walls, wave, player_bullets)
            bullets.extend(ai_bullets)

            # Update fighter AI companions (they target the enemy)
            for fai in fighter_ais:
                if fai.alive and ai.alive:
                    fai.update(keys, platforms, walls)
                    # Fighter AI targets the enemy — reuse ai_update but with enemy as target
                    enemy_bullets = [b for b in bullets if b.owner == "ai" and b.alive]
                    fai_bullets = fai.ai_update(ai, platforms, walls, wave, enemy_bullets)
                    # Re-tag bullets as "player" so they damage the enemy
                    for fb in fai_bullets:
                        fb.owner = "player"
                        fb.color = fai._fighter_color if hasattr(fai, '_fighter_color') else GREEN
                    bullets.extend(fai_bullets)

            # Update bullets
            for b in bullets:
                b.update(platforms, walls)

            # Check bullet collisions
            for b in bullets[:]:
                if not b.alive:
                    continue
                if b.owner == "player" and ai.alive:
                    if b.get_rect().colliderect(ai.get_rect()):
                        if ai.shield > 0:
                            ai.shield -= 1
                            b.alive = False
                            spawn_particles(b.x, b.y, CYAN, count=12, life=20, size=5)
                        else:
                            ai.alive = False
                            b.alive = False
                            spawn_particles(ai.x + ai.w // 2, ai.y + ai.h // 2,
                                            RED, count=30, spread=5, life=35, size=6)
                            hit_flash_ai = 20
                            result = "win"

                elif b.owner == "ai" and player.alive:
                    if b.get_rect().colliderect(player.get_rect()):
                        # Cheat: Dodge — chance to avoid hit entirely
                        if total_cheat_dodge > 0 and random.random() < total_cheat_dodge * 0.15:
                            b.alive = False
                            spawn_particles(b.x, b.y, YELLOW, count=8, life=15, size=3)
                            continue
                        if player.shield > 0:
                            player.shield -= 1
                            b.alive = False
                            spawn_particles(b.x, b.y, CYAN, count=12, life=20, size=5)
                        else:
                            # Cheat: God Mode — chance to survive lethal hit
                            if total_cheat_god > 0 and random.random() < total_cheat_god * 0.25:
                                player.shield = 1  # God mode gives a free shield
                                b.alive = False
                                spawn_particles(b.x, b.y, MAGENTA, count=15, life=20, size=4)
                            else:
                                player.alive = False
                                b.alive = False
                                spawn_particles(player.x + player.w // 2, player.y + player.h // 2,
                                                BLUE, count=30, spread=5, life=35, size=6)
                                hit_flash_player = 20
                                result = "lose"

            # Remove dead bullets
            bullets = [b for b in bullets if b.alive]

            # Update particles
            for p in particles:
                p.update()
            particles = [p for p in particles if p.life > 0]

            if hit_flash_player > 0:
                hit_flash_player -= 1
            if hit_flash_ai > 0:
                hit_flash_ai -= 1

        # ── DRAW ──
        draw_background(screen, wave)
        draw_course(screen, platforms, walls, wave)

        # Draw bullets
        for b in bullets:
            b.draw(screen)

        # Draw fighters
        player.draw(screen, wave)
        ai.draw(screen, wave)
        # Draw fighter AI companions
        for fai in fighter_ais:
            if fai.alive:
                fai.draw(screen, wave)
                # Name label above fighter AI
                nlbl = font_sm.render(fai._fighter_name if hasattr(fai, '_fighter_name') else "Ally", True,
                                       fai._fighter_color if hasattr(fai, '_fighter_color') else GREEN)
                screen.blit(nlbl, (fai.x + fai.w // 2 - nlbl.get_width() // 2, fai.y - 18))

        # Draw particles
        for p in particles:
            p.draw(screen)

        # HUD
        draw_hud(screen, wave, player, save_data)

        # Round ability display
        round_ab = font_sm.render(f"Round power: {chosen_ability}", True, YELLOW)
        screen.blit(round_ab, (WIDTH // 2 - round_ab.get_width() // 2, 15))

        # AI abilities hint
        ai_txt = font_sm.render(f"AI has {len(ai_abilities)} abilities", True, (200, 100, 100))
        screen.blit(ai_txt, (WIDTH - 200, 45))

        # Fighter AI count
        if fighter_ais:
            ally_txt = font_sm.render(f"Allies: {len(fighter_ais)} fighter AI(s)", True, GREEN)
            screen.blit(ally_txt, (10, 45))

        # Flash effects
        if hit_flash_player > 0:
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash.fill((0, 0, 255, min(80, hit_flash_player * 8)))
            screen.blit(flash, (0, 0))
        if hit_flash_ai > 0:
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 0, 0, min(80, hit_flash_ai * 8)))
            screen.blit(flash, (0, 0))

        pygame.display.flip()
        clock.tick(FPS)

    # Linger for a moment after result
    linger = 60
    while linger > 0:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        for p in particles:
            p.update()
        particles = [p for p in particles if p.life > 0]

        draw_background(screen, wave)
        draw_course(screen, platforms, walls, wave)
        for b in bullets:
            b.draw(screen)
        player.draw(screen, wave)
        ai.draw(screen, wave)
        for fai in fighter_ais:
            if fai.alive:
                fai.draw(screen, wave)
        for p in particles:
            p.draw(screen)

        # Big result text
        if result == "win":
            txt = font_xl.render("HIT!", True, GOLD)
        else:
            txt = font_xl.render("OUCH!", True, RED)
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 40))

        pygame.display.flip()
        clock.tick(FPS)
        linger -= 1

    return result


# ─── REBIRTH SCREEN ──────────────────────────────────────────────────────────
def rebirth_screen(save_data):
    """Show rebirth UI: preview what you'll gain from your AI team's equipped abilities."""
    _migrate_ai(save_data)
    team = save_data.get("ai_team", [])
    scroll = 0

    while True:
        # Gather all equipped abilities from all AIs
        rebirth_abilities = []
        for ai in team:
            for ab_name in ai.get("equipped", []):
                rebirth_abilities.append((ab_name, ai.get("name", "?")))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return save_data  # cancel
                if event.key in (pygame.K_UP, pygame.K_w):
                    scroll = max(0, scroll - 1)
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    scroll += 1
                if event.key == pygame.K_RETURN:
                    # Do the rebirth!
                    rebirth_inv = [ab for ab, _ in rebirth_abilities]
                    rebirth_slots = max(2, 2 + len(rebirth_inv) // 5)
                    # Preserve AI team + parts + total_waves + chat
                    old_total = save_data.get("total_waves", save_data.get("wins", 0))
                    ai_team = save_data.get("ai_team", [])
                    ai_parts = save_data.get("ai_parts", [])
                    chat_log = save_data.get("ai_chat_log", [])
                    save_data = {"wave": 1, "equipped": [], "inventory": rebirth_inv,
                                 "slots": rebirth_slots, "wins": 0,
                                 "rounds_since_part": 0,
                                 "ai_team": ai_team, "ai_parts": ai_parts,
                                 "total_waves": old_total, "ai_chat_log": chat_log}
                    save_game(save_data)
                    return save_data
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # Confirm button
                if WIDTH // 2 - 100 < mx < WIDTH // 2 + 100 and HEIGHT - 70 < my < HEIGHT - 30:
                    rebirth_inv = [ab for ab, _ in rebirth_abilities]
                    rebirth_slots = max(2, 2 + len(rebirth_inv) // 5)
                    old_total = save_data.get("total_waves", save_data.get("wins", 0))
                    ai_team = save_data.get("ai_team", [])
                    ai_parts = save_data.get("ai_parts", [])
                    chat_log = save_data.get("ai_chat_log", [])
                    save_data = {"wave": 1, "equipped": [], "inventory": rebirth_inv,
                                 "slots": rebirth_slots, "wins": 0,
                                 "rounds_since_part": 0,
                                 "ai_team": ai_team, "ai_parts": ai_parts,
                                 "total_waves": old_total, "ai_chat_log": chat_log}
                    save_game(save_data)
                    return save_data

        screen.fill((15, 10, 30))

        # Title
        t = font_lg.render("REBIRTH", True, MAGENTA)
        screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 20))
        sub = font_md.render("Reset to Wave 1, gain your AI team's equipped abilities!", True, (200, 100, 255))
        screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 65))

        # Show what you'll gain
        y = 110
        header = font_md.render(f"You will receive {len(rebirth_abilities)} abilities:", True, GOLD)
        screen.blit(header, (60, y))
        y += 35

        if len(rebirth_abilities) == 0:
            t2 = font_md.render("Your AIs have nothing equipped! Equip abilities first.", True, RED)
            screen.blit(t2, (60, y))
        else:
            max_show = 10
            scroll = min(scroll, max(0, len(rebirth_abilities) - max_show))
            for i in range(scroll, min(scroll + max_show, len(rebirth_abilities))):
                ab_name, ai_name = rebirth_abilities[i]
                ab, lv = get_ability_data(ab_name)
                col = ab["color"] if ab else WHITE
                lv_str = f" Lv{lv}" if lv > 1 else ""
                pygame.draw.rect(screen, (30, 25, 50), (50, y, WIDTH - 100, 28), border_radius=4)
                txt = font_sm.render(f"{get_base_name(ab_name)}{lv_str}  (from {ai_name})", True, col)
                screen.blit(txt, (60, y + 4))
                if ab:
                    desc = font_sm.render(ab["desc"], True, GRAY)
                    screen.blit(desc, (WIDTH - 60 - desc.get_width(), y + 4))
                y += 32

        # Bonus slots
        bonus_slots = max(2, 2 + len(rebirth_abilities) // 5)
        st = font_md.render(f"Starting slots: {bonus_slots}", True, CYAN)
        screen.blit(st, (60, HEIGHT - 120))

        # Confirm button
        pygame.draw.rect(screen, (60, 20, 80), (WIDTH // 2 - 100, HEIGHT - 70, 200, 40), border_radius=8)
        pygame.draw.rect(screen, MAGENTA, (WIDTH // 2 - 100, HEIGHT - 70, 200, 40), 2, border_radius=8)
        ct = font_md.render("REBIRTH (Enter)", True, MAGENTA)
        screen.blit(ct, (WIDTH // 2 - ct.get_width() // 2, HEIGHT - 62))

        # Esc hint
        hint = font_sm.render("Esc: Cancel  |  Up/Down: Scroll  |  Enter: Confirm Rebirth", True, GRAY)
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 18))

        pygame.display.flip()
        clock.tick(FPS)


# ─── MAIN GAME LOOP ─────────────────────────────────────────────────────────
def main():
    save_data = load_game()

    while True:
        # AI companion fights constantly — simulate pending battles every loop
        simulate_ai_battles(save_data)

        choice = title_screen()

        if choice == "Quit":
            pygame.quit()
            sys.exit()

        if choice == "Equip Abilities":
            save_data = equip_screen(save_data)
            continue

        if choice == "Merge Abilities":
            save_data = merge_screen(save_data)
            continue

        if choice == "AI Companion":
            save_data = ai_companion_screen(save_data)
            continue

        if choice == "Rebirth":
            save_data = rebirth_screen(save_data)
            continue

        if choice == "Reset Progress":
            # Preserve AI team + parts + total_waves + chat across reset
            _migrate_ai(save_data)
            old_total = save_data.get("total_waves", save_data.get("wins", 0))
            ai_team = save_data.get("ai_team", [])
            ai_parts = save_data.get("ai_parts", [])
            chat_log = save_data.get("ai_chat_log", [])
            save_data = {"wave": 1, "equipped": [], "inventory": [], "slots": 2, "wins": 0,
                         "rounds_since_part": 0,
                         "ai_team": ai_team, "ai_parts": ai_parts,
                         "total_waves": old_total, "ai_chat_log": chat_log}
            save_game(save_data)
            continue

        if choice == "Start Battle":
            wave = save_data["wave"]

            # Would You Rather choice
            chosen, unchosen = would_you_rather_screen(wave, save_data)

            # Run the battle (pass save_data so fighter AIs can join)
            result = battle(wave, save_data, chosen)

            if result == "win":
                # Add unchosen ability to inventory (duplicates allowed for merging!)
                save_data["inventory"].append(unchosen)

                # ── Fighter cheat_loot: extra abilities on win ──
                _migrate_ai(save_data)
                _total_loot_cheat = sum(_get_school_skill_lv(a, "cheat_loot") for a in save_data.get("ai_team", []) if a.get("type") == "fighter")
                for _ in range(_total_loot_cheat):
                    save_data["inventory"].append(random.choice(list(ABILITIES.keys())))

                save_data["wins"] = save_data.get("wins", 0) + 1
                save_data["wave"] = wave + 1
                save_data["total_waves"] = save_data.get("total_waves", 0) + 1

                # ── Award School XP to all AIs on win ──
                _migrate_ai(save_data)
                for _ai_s in save_data.get("ai_team", []):
                    _school = _ai_s.setdefault("brain", {}).setdefault("school", {"level": 0, "skills": [], "xp": 0})
                    _fl = _get_school_skill_lv(_ai_s, "fast_learner")
                    _school["xp"] = _school.get("xp", 0) + (4 if _fl > 0 else 2)

                # Every 5 waves, gain a slot
                if wave % 5 == 0:
                    save_data["slots"] = save_data.get("slots", 2) + 1

                # AI Companion: every 3 wins → random part + random ability for first offline AI
                # Check if any AI has fast_parts mod (earns part every 1 win)
                _migrate_ai(save_data)
                any_fast_parts = any("fast_parts" in a.get("brain", {}).get("mods", []) for a in save_data.get("ai_team", []))
                part_threshold = 1 if any_fast_parts else 3
                save_data["rounds_since_part"] = save_data.get("rounds_since_part", 0) + 1
                earned_part = None
                if save_data["rounds_since_part"] >= part_threshold:
                    save_data["rounds_since_part"] = 0
                    earned_part = random.choice(AI_PARTS).copy()
                    save_data.setdefault("ai_parts", []).append(earned_part)
                    # Give each AI a random ability (loot mods = more)
                    for ai in save_data.get("ai_team", []):
                        ai_mods = ai.get("brain", {}).get("mods", [])
                        custom_mods_dict = ai.get("brain", {}).get("custom_mods", {})
                        # Calculate loot multiplier
                        loot_mult = 1
                        if "double_loot" in ai_mods:
                            loot_mult += 1
                        if "custom_loot" in ai_mods or any("loot" in custom_mods_dict.get(m, {}).get("desc", "").lower() for m in ai_mods if m.startswith("custom_")):
                            loot_mult += 2  # 3x alone, stacks with double_loot
                        # Golden touch = Determination instead of random
                        has_gold = "custom_gold" in ai_mods
                        has_rare = "custom_rare" in ai_mods
                        for _ in range(loot_mult):
                            det_chance = 0.50 if has_gold else (0.35 if has_rare else 0.15)
                            if random.random() < det_chance:
                                ai_ability = "Determination"
                            else:
                                ai_ability = random.choice(list(ABILITIES.keys()))
                            ai.setdefault("inventory", []).append(ai_ability)
                        # Auto-collect mod: also add to player inventory
                        if "auto_collect" in ai_mods:
                            save_data["inventory"].append(ai.get("inventory", [])[-1] if ai.get("inventory") else random.choice(list(ABILITIES.keys())))
                        _ai_auto_equip(ai)
                    # XP boost: AIs with it gain slot every 2 parts, others every 4
                    part_count = len(save_data.get("ai_parts", []))
                    for ai in save_data.get("ai_team", []):
                        ai_mods = ai.get("brain", {}).get("mods", [])
                        slot_interval = 2 if "xp_boost" in ai_mods else 4
                        if part_count % slot_interval == 0:
                            ai["slots"] = ai.get("slots", 2) + 1

                save_game(save_data)
                you_win_screen(wave, unchosen, earned_part)

                # Let player configure fighter AIs after a win
                fighter_ai_equip_screen(save_data)

            else:
                you_lose_screen(wave)


if __name__ == "__main__":
    main()
