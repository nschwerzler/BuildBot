"""
╔══════════════════════════════════════════════════════════════╗
║       REALMS OF SHADOW — 2.5D DnD RPG Adventure            ║
║   Isometric dungeon crawling with AI party members          ║
╚══════════════════════════════════════════════════════════════╝
"""
import pygame, sys, math, random, json, os, time
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple

pygame.init()
pygame.mixer.init()

# ════════════════════════════════════════════════════════════
# CONSTANTS
# ════════════════════════════════════════════════════════════
SCREEN_W, SCREEN_H = 1280, 800
TILE_W, TILE_H = 64, 32  # Isometric tile dimensions
FPS = 60
SAVE_FILE = "dnd_rpg_save.json"
MAX_INVENTORY = 40  # Maximum inventory capacity

# Colors
C_BLACK = (0, 0, 0)
C_WHITE = (255, 255, 255)
C_RED = (220, 40, 40)
C_GREEN = (40, 200, 60)
C_BLUE = (50, 100, 220)
C_GOLD = (255, 215, 0)
C_PURPLE = (150, 50, 200)
C_GRAY = (120, 120, 130)
C_DARK = (20, 18, 24)
C_DARK2 = (35, 30, 42)
C_DARK3 = (50, 44, 58)
C_HP_RED = (180, 30, 30)
C_HP_BG = (60, 20, 20)
C_MP_BLUE = (30, 80, 180)
C_MP_BG = (20, 30, 60)
C_XP_GOLD = (180, 160, 30)
C_XP_BG = (50, 45, 15)
C_PANEL = (25, 22, 32)
C_PANEL_BORDER = (70, 60, 90)
C_HIGHLIGHT = (255, 220, 100)
C_SHADOW = (10, 8, 14)

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("⚔️ Realms of Shadow — 2.5D DnD RPG")
clock = pygame.time.Clock()


# ════════════════════════════════════════════════════════════
# TEXTURE GENERATION — Rich procedural pixel art
# ════════════════════════════════════════════════════════════
_tex_cache = {}

def _noise(x, y, seed=0):
    n = (x * 374761393 + y * 668265263 + seed * 1013904223) & 0xFFFFFFFF
    n = ((n >> 13) ^ n) & 0xFFFFFFFF
    return (n % 1000) / 1000.0

def _lerp(a, b, t):
    return a + (b - a) * max(0, min(1, t))

def make_texture(name, w, h):
    """Generate rich procedural textures for the RPG world."""
    if name in _tex_cache:
        return _tex_cache[name]
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    if name == 'stone_floor':
        for y in range(h):
            for x in range(w):
                base = 55 + int(_noise(x, y, 1) * 30)
                # Tile grid lines
                gx = x % 16
                gy = y % 16
                if gx == 0 or gy == 0:
                    base -= 15
                # Cracks
                if _noise(x * 3, y * 3, 42) > 0.92:
                    base -= 25
                # Subtle color variation
                r = base + int(_noise(x, y, 7) * 8)
                g = base + int(_noise(x, y, 13) * 5)
                b = base + int(_noise(x, y, 19) * 12)
                surf.set_at((x, y), (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b + 5)), 255))

    elif name == 'stone_wall':
        for y in range(h):
            for x in range(w):
                # Darker stone blocks
                bx = (x // 12) % 3
                by = (y // 8) % 3
                base = 40 + bx * 5 + by * 3
                base += int(_noise(x, y, 2) * 20)
                # Mortar lines
                if x % 12 < 1 or y % 8 < 1:
                    base = 30 + int(_noise(x, y, 55) * 10)
                # Moss patches
                if _noise(x * 2, y * 2, 33) > 0.85:
                    g_add = 30
                else:
                    g_add = 0
                r = max(0, min(255, base))
                g = max(0, min(255, base + g_add + 3))
                b = max(0, min(255, base + 8))
                surf.set_at((x, y), (r, g, b, 255))

    elif name == 'grass':
        for y in range(h):
            for x in range(w):
                g_val = 80 + int(_noise(x, y, 5) * 60)
                r_val = 30 + int(_noise(x, y, 8) * 20)
                b_val = 20 + int(_noise(x, y, 11) * 15)
                # Grass blades
                if _noise(x * 5, y * 5, 22) > 0.7:
                    g_val += 30
                # Flowers
                if _noise(x * 7, y * 7, 99) > 0.97:
                    r_val = 200 + random.randint(0, 55)
                    g_val = 60
                    b_val = 100 + random.randint(0, 100)
                surf.set_at((x, y), (r_val, g_val, b_val, 255))

    elif name == 'water':
        for y in range(h):
            for x in range(w):
                wave = math.sin(x * 0.3 + y * 0.2) * 15
                b_val = 120 + int(wave) + int(_noise(x, y, 3) * 30)
                g_val = 60 + int(wave * 0.5) + int(_noise(x, y, 6) * 15)
                r_val = 20 + int(_noise(x, y, 9) * 10)
                a = 200 + int(_noise(x, y, 15) * 40)
                surf.set_at((x, y), (r_val, g_val, min(255, b_val), min(255, a)))

    elif name == 'lava':
        for y in range(h):
            for x in range(w):
                flow = math.sin(x * 0.2 + y * 0.15) * 20
                r_val = 200 + int(flow) + int(_noise(x, y, 4) * 40)
                g_val = 80 + int(flow * 0.7) + int(_noise(x, y, 7) * 30)
                b_val = 10 + int(_noise(x, y, 10) * 15)
                surf.set_at((x, y), (min(255, r_val), min(255, g_val), b_val, 255))

    elif name == 'wood_floor':
        for y in range(h):
            for x in range(w):
                plank = (x // 10) % 2
                grain = int(math.sin(y * 0.8 + _noise(x, y, 12) * 4) * 10)
                base = 90 + plank * 15 + grain
                base += int(_noise(x, y, 20) * 12)
                r = max(0, min(255, base + 20))
                g = max(0, min(255, base))
                b = max(0, min(255, base - 25))
                if x % 10 == 0:
                    r -= 20; g -= 20; b -= 15
                surf.set_at((x, y), (max(0, r), max(0, g), max(0, b), 255))

    elif name == 'dark_stone':
        for y in range(h):
            for x in range(w):
                base = 25 + int(_noise(x, y, 30) * 20)
                if _noise(x * 4, y * 4, 50) > 0.9:
                    base += 15  # veins
                r = max(0, min(255, base + 5))
                g = max(0, min(255, base))
                b = max(0, min(255, base + 10))
                surf.set_at((x, y), (r, g, b, 255))

    elif name == 'chest':
        surf.fill((0, 0, 0, 0))
        # Body
        pygame.draw.rect(surf, (120, 70, 20), (2, h // 3, w - 4, h * 2 // 3 - 2))
        pygame.draw.rect(surf, (90, 50, 10), (2, h // 3, w - 4, h * 2 // 3 - 2), 2)
        # Lid
        pygame.draw.rect(surf, (140, 85, 25), (1, h // 4, w - 2, h // 4))
        pygame.draw.rect(surf, (100, 60, 15), (1, h // 4, w - 2, h // 4), 1)
        # Metal bands
        pygame.draw.rect(surf, (180, 170, 50), (w // 2 - 3, h // 4, 6, h * 2 // 3))
        pygame.draw.rect(surf, (200, 190, 70), (w // 2 - 2, h // 3, 4, 4))
        # Lock
        pygame.draw.circle(surf, (220, 200, 60), (w // 2, h // 2 + 4), 3)

    elif name == 'stairs':
        surf.fill((0, 0, 0, 0))
        for i in range(4):
            shade = 60 + i * 15
            yy = h - (i + 1) * (h // 4)
            pygame.draw.rect(surf, (shade, shade - 5, shade + 5), (i * 3, yy, w - i * 6, h // 4))
            pygame.draw.rect(surf, (shade - 20, shade - 25, shade - 15), (i * 3, yy, w - i * 6, h // 4), 1)

    elif name == 'st_portal':
        surf.fill((0, 0, 0, 0))
        # Dark crimson swirling portal to the Upside Down
        cx, cy = w // 2, h // 2
        for y in range(h):
            for x in range(w):
                dx = x - cx
                dy = y - cy
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < w // 2:
                    angle = math.atan2(dy, dx)
                    swirl = math.sin(angle * 3 + dist * 0.5) * 0.5 + 0.5
                    r = int(120 + swirl * 80 + _noise(x, y, 66) * 40)
                    g = int(10 + swirl * 20 + _noise(x, y, 77) * 15)
                    b = int(30 + swirl * 40 + _noise(x, y, 88) * 30)
                    a = int(200 - dist * 8)
                    surf.set_at((x, y), (min(255, r), min(255, g), min(255, b), max(50, a)))

    elif name == 'upside_down_floor':
        for y in range(h):
            for x in range(w):
                base = 20 + int(_noise(x, y, 90) * 15)
                gx = x % 16
                gy = y % 16
                if gx == 0 or gy == 0:
                    base -= 5
                # Vine-like tendrils
                if _noise(x * 3, y * 3, 91) > 0.88:
                    base += 10
                r = max(0, min(255, base + int(_noise(x, y, 92) * 15)))
                g = max(0, min(255, base - 5))
                b = max(0, min(255, base + int(_noise(x, y, 93) * 20)))
                surf.set_at((x, y), (r, g, b, 255))

    else:
        surf.fill((80, 80, 80, 255))

    _tex_cache[name] = surf
    return surf


def make_iso_tile(name, wall=False):
    """Create an isometric diamond-shaped tile with texture."""
    key = f'iso_{name}_{"w" if wall else "f"}'
    if key in _tex_cache:
        return _tex_cache[key]

    tex = make_texture(name, 32, 32)
    tw, th = TILE_W, TILE_H
    wall_h = 24 if wall else 0
    surf = pygame.Surface((tw, th + wall_h), pygame.SRCALPHA)

    # Draw isometric diamond floor
    points = [(tw // 2, 0), (tw, th // 2), (tw // 2, th), (0, th // 2)]
    if wall:
        points = [(tw // 2, 0), (tw, th // 2), (tw // 2, th), (0, th // 2)]

    # Sample texture onto iso shape
    for py in range(th):
        for px in range(tw):
            # Check if point is inside diamond
            cx, cy = tw // 2, th // 2
            dx = abs(px - cx) / (tw / 2)
            dy = abs(py - cy) / (th / 2)
            if dx + dy <= 1.0:
                tx = int((px / tw) * 31) % 32
                ty = int((py / th) * 31) % 32
                col = tex.get_at((tx, ty))
                surf.set_at((px, py + wall_h), col)

    if wall:
        # Draw wall face (front-left and front-right)
        for wy in range(wall_h):
            shade = 1.0 - (wy / wall_h) * 0.3
            for px in range(tw):
                cx = tw // 2
                # Left face
                if px <= cx:
                    top_y = th // 2 + int((cx - px) * (th / tw))
                    if wy == 0:
                        pass
                    col = tex.get_at((px % 32, (wy * 2) % 32))
                    r = int(col[0] * shade * 0.7)
                    g = int(col[1] * shade * 0.7)
                    b = int(col[2] * shade * 0.7)
                    y_pos = py_from_iso_wall(px, wy, tw, th, wall_h)
                    if 0 <= y_pos < th + wall_h:
                        surf.set_at((px, y_pos), (r, g, b, 255))
                # Right face
                else:
                    col = tex.get_at((px % 32, (wy * 2) % 32))
                    r = int(col[0] * shade * 0.5)
                    g = int(col[1] * shade * 0.5)
                    b = int(col[2] * shade * 0.5)
                    y_pos = py_from_iso_wall(px, wy, tw, th, wall_h)
                    if 0 <= y_pos < th + wall_h:
                        surf.set_at((px, y_pos), (r, g, b, 255))

    _tex_cache[key] = surf
    return surf


def py_from_iso_wall(px, wy, tw, th, wall_h):
    cx = tw // 2
    if px <= cx:
        base_y = th // 2 - int((cx - px) * th / tw) + th // 2
    else:
        base_y = int((px - cx) * th / tw) + th // 2
    return base_y + wy - wall_h + th // 2


# ════════════════════════════════════════════════════════════
# SPRITE GENERATION — Character & monster sprites
# ════════════════════════════════════════════════════════════
def make_character_sprite(char_class, palette, w=24, h=32, is_enemy=False):
    """Generate a detailed character sprite with class-specific features."""
    key = f'char_{char_class}_{palette[0]}_{w}_{h}_{"e" if is_enemy else "p"}'
    if key in _tex_cache:
        return _tex_cache[key]

    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    skin = palette[0]
    primary = palette[1]
    secondary = palette[2]
    detail = palette[3] if len(palette) > 3 else (200, 200, 200)

    # Shadow
    pygame.draw.ellipse(surf, (0, 0, 0, 60), (w // 2 - 8, h - 5, 16, 5))

    # Body
    body_top = h // 3
    body_bot = h - 8
    pygame.draw.rect(surf, primary, (w // 2 - 5, body_top, 10, body_bot - body_top))
    pygame.draw.rect(surf, secondary, (w // 2 - 5, body_top, 10, body_bot - body_top), 1)

    # Head
    head_r = 5
    head_cx, head_cy = w // 2, body_top - head_r + 1
    pygame.draw.circle(surf, skin, (head_cx, head_cy), head_r)
    pygame.draw.circle(surf, (max(0, skin[0] - 30), max(0, skin[1] - 30), max(0, skin[2] - 30)), (head_cx, head_cy), head_r, 1)

    # Eyes
    eye_y = head_cy - 1
    pygame.draw.rect(surf, C_WHITE, (head_cx - 3, eye_y, 2, 2))
    pygame.draw.rect(surf, C_WHITE, (head_cx + 1, eye_y, 2, 2))
    pygame.draw.rect(surf, C_BLACK, (head_cx - 2, eye_y, 1, 2))
    pygame.draw.rect(surf, C_BLACK, (head_cx + 2, eye_y, 1, 2))

    # Legs
    pygame.draw.rect(surf, secondary, (w // 2 - 4, body_bot, 3, 6))
    pygame.draw.rect(surf, secondary, (w // 2 + 1, body_bot, 3, 6))
    # Boots
    pygame.draw.rect(surf, (60, 40, 20), (w // 2 - 5, body_bot + 4, 4, 3))
    pygame.draw.rect(surf, (60, 40, 20), (w // 2 + 1, body_bot + 4, 4, 3))

    # Arms
    pygame.draw.rect(surf, primary, (w // 2 - 7, body_top + 2, 3, 10))
    pygame.draw.rect(surf, primary, (w // 2 + 4, body_top + 2, 3, 10))
    # Hands
    pygame.draw.rect(surf, skin, (w // 2 - 7, body_top + 11, 3, 3))
    pygame.draw.rect(surf, skin, (w // 2 + 4, body_top + 11, 3, 3))

    # Class-specific features
    if char_class == 'warrior':
        # Helmet
        pygame.draw.rect(surf, (150, 150, 160), (head_cx - 5, head_cy - 6, 10, 4))
        pygame.draw.rect(surf, (180, 180, 190), (head_cx - 1, head_cy - 8, 2, 3))
        # Shield (left hand)
        pygame.draw.circle(surf, detail, (w // 2 - 9, body_top + 10), 5)
        pygame.draw.circle(surf, secondary, (w // 2 - 9, body_top + 10), 5, 1)
        pygame.draw.circle(surf, C_GOLD, (w // 2 - 9, body_top + 10), 2)
        # Sword (right hand)
        pygame.draw.rect(surf, (200, 200, 210), (w // 2 + 5, body_top - 2, 2, 14))
        pygame.draw.rect(surf, C_GOLD, (w // 2 + 3, body_top + 10, 6, 2))

    elif char_class == 'mage':
        # Wizard hat
        points = [(head_cx, head_cy - 14), (head_cx - 7, head_cy - 3), (head_cx + 7, head_cy - 3)]
        pygame.draw.polygon(surf, primary, points)
        pygame.draw.polygon(surf, secondary, points, 1)
        pygame.draw.circle(surf, C_GOLD, (head_cx, head_cy - 12), 2)
        # Staff
        pygame.draw.rect(surf, (100, 60, 20), (w // 2 + 6, body_top - 8, 2, 24))
        pygame.draw.circle(surf, (100, 150, 255), (w // 2 + 7, body_top - 8), 4)
        pygame.draw.circle(surf, (150, 200, 255), (w // 2 + 7, body_top - 8), 2)
        # Robe detail
        pygame.draw.line(surf, C_GOLD, (w // 2 - 4, body_top + 3), (w // 2 + 4, body_top + 3))

    elif char_class == 'rogue':
        # Hood
        pygame.draw.arc(surf, primary, (head_cx - 6, head_cy - 8, 12, 10), 0, math.pi, 3)
        # Daggers
        pygame.draw.rect(surf, (180, 180, 190), (w // 2 + 5, body_top + 4, 1, 10))
        pygame.draw.rect(surf, (180, 180, 190), (w // 2 - 7, body_top + 4, 1, 10))
        pygame.draw.rect(surf, (100, 60, 20), (w // 2 + 4, body_top + 13, 3, 2))
        # Cape
        cape_pts = [(w // 2 - 4, body_top), (w // 2 + 4, body_top),
                    (w // 2 + 6, body_bot - 2), (w // 2 - 6, body_bot - 2)]
        pygame.draw.polygon(surf, (*primary, 140), cape_pts)

    elif char_class == 'cleric':
        # Holy symbol on chest
        pygame.draw.rect(surf, C_GOLD, (w // 2 - 1, body_top + 2, 2, 6))
        pygame.draw.rect(surf, C_GOLD, (w // 2 - 3, body_top + 4, 6, 2))
        # Mace
        pygame.draw.rect(surf, (140, 120, 80), (w // 2 + 5, body_top, 2, 14))
        pygame.draw.rect(surf, (180, 170, 60), (w // 2 + 3, body_top - 2, 6, 4))
        # Halo
        pygame.draw.circle(surf, (255, 255, 200, 100), (head_cx, head_cy - 8), 6, 1)

    elif char_class == 'ranger':
        # Bow
        pygame.draw.arc(surf, (120, 80, 30), (w // 2 + 3, body_top - 2, 6, 16), -1.2, 1.2, 2)
        pygame.draw.line(surf, (200, 200, 200), (w // 2 + 6, body_top - 1), (w // 2 + 6, body_top + 13), 1)
        # Quiver
        pygame.draw.rect(surf, (100, 60, 20), (w // 2 - 8, body_top - 2, 3, 10))
        # Feathered cap
        pygame.draw.rect(surf, (50, 120, 50), (head_cx - 5, head_cy - 6, 10, 3))
        pygame.draw.rect(surf, (200, 50, 50), (head_cx + 3, head_cy - 10, 2, 5))

    elif char_class == 'skeleton':
        # Override body to white bones
        surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(surf, (0, 0, 0, 60), (w // 2 - 8, h - 5, 16, 5))
        # Skull
        pygame.draw.circle(surf, (220, 210, 190), (head_cx, head_cy), head_r)
        pygame.draw.rect(surf, C_BLACK, (head_cx - 3, eye_y, 2, 2))
        pygame.draw.rect(surf, C_BLACK, (head_cx + 1, eye_y, 2, 2))
        pygame.draw.rect(surf, C_BLACK, (head_cx - 2, eye_y + 4, 4, 1))
        # Ribs
        for i in range(4):
            pygame.draw.rect(surf, (200, 190, 170), (w // 2 - 4, body_top + i * 3 + 1, 8, 1))
        # Limbs
        pygame.draw.rect(surf, (200, 190, 170), (w // 2 - 6, body_top + 2, 2, 12))
        pygame.draw.rect(surf, (200, 190, 170), (w // 2 + 4, body_top + 2, 2, 12))
        pygame.draw.rect(surf, (200, 190, 170), (w // 2 - 3, body_bot, 2, 7))
        pygame.draw.rect(surf, (200, 190, 170), (w // 2 + 1, body_bot, 2, 7))
        # Rusty sword
        pygame.draw.rect(surf, (160, 120, 80), (w // 2 + 6, body_top, 2, 12))

    elif char_class == 'goblin':
        surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(surf, (0, 0, 0, 60), (w // 2 - 6, h - 4, 12, 4))
        gw, gh = 18, 24
        ox = (w - gw) // 2
        oy = h - gh - 2
        # Small green body
        pygame.draw.rect(surf, (60, 120, 40), (ox + 4, oy + 8, 10, 10))
        # Big head
        pygame.draw.circle(surf, (80, 150, 50), (w // 2, oy + 6), 6)
        # Big eyes
        pygame.draw.circle(surf, (255, 255, 50), (w // 2 - 3, oy + 5), 3)
        pygame.draw.circle(surf, (255, 255, 50), (w // 2 + 3, oy + 5), 3)
        pygame.draw.circle(surf, C_BLACK, (w // 2 - 3, oy + 5), 1)
        pygame.draw.circle(surf, C_BLACK, (w // 2 + 3, oy + 5), 1)
        # Pointy ears
        pygame.draw.polygon(surf, (80, 150, 50), [(w // 2 - 7, oy + 4), (w // 2 - 10, oy), (w // 2 - 5, oy + 2)])
        pygame.draw.polygon(surf, (80, 150, 50), [(w // 2 + 7, oy + 4), (w // 2 + 10, oy), (w // 2 + 5, oy + 2)])
        # Legs
        pygame.draw.rect(surf, (60, 120, 40), (ox + 5, oy + 17, 3, 5))
        pygame.draw.rect(surf, (60, 120, 40), (ox + 10, oy + 17, 3, 5))
        # Crude weapon
        pygame.draw.rect(surf, (100, 80, 40), (ox + 14, oy + 6, 2, 12))

    elif char_class == 'orc':
        surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(surf, (0, 0, 0, 60), (w // 2 - 9, h - 5, 18, 5))
        # Big green body
        pygame.draw.rect(surf, (50, 100, 40), (w // 2 - 7, body_top - 2, 14, body_bot - body_top + 4))
        # Head
        pygame.draw.circle(surf, (60, 110, 45), (head_cx, head_cy - 1), 7)
        # Tusks
        pygame.draw.rect(surf, (220, 220, 200), (head_cx - 4, head_cy + 3, 2, 3))
        pygame.draw.rect(surf, (220, 220, 200), (head_cx + 2, head_cy + 3, 2, 3))
        # Red eyes
        pygame.draw.rect(surf, (255, 50, 20), (head_cx - 4, head_cy - 2, 3, 2))
        pygame.draw.rect(surf, (255, 50, 20), (head_cx + 1, head_cy - 2, 3, 2))
        # Arms
        pygame.draw.rect(surf, (50, 100, 40), (w // 2 - 10, body_top, 4, 14))
        pygame.draw.rect(surf, (50, 100, 40), (w // 2 + 6, body_top, 4, 14))
        # Legs
        pygame.draw.rect(surf, (40, 80, 30), (w // 2 - 5, body_bot + 2, 4, 6))
        pygame.draw.rect(surf, (40, 80, 30), (w // 2 + 1, body_bot + 2, 4, 6))
        # Big axe
        pygame.draw.rect(surf, (100, 70, 30), (w // 2 + 9, body_top - 6, 2, 18))
        pygame.draw.polygon(surf, (170, 170, 180), [(w // 2 + 8, body_top - 6), (w // 2 + 14, body_top - 3), (w // 2 + 8, body_top)])

    elif char_class == 'dragon':
        surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(surf, (0, 0, 0, 80), (w // 2 - 10, h - 5, 20, 5))
        # Body
        pygame.draw.ellipse(surf, primary, (w // 2 - 8, h // 3, 16, 14))
        # Head
        pygame.draw.ellipse(surf, primary, (w // 2 - 5, h // 6, 10, 8))
        # Eye
        pygame.draw.circle(surf, (255, 200, 0), (w // 2 + 2, h // 6 + 3), 2)
        pygame.draw.circle(surf, C_BLACK, (w // 2 + 2, h // 6 + 3), 1)
        # Horns
        pygame.draw.polygon(surf, (180, 160, 100), [(w // 2 - 3, h // 6), (w // 2 - 6, h // 6 - 6), (w // 2 - 1, h // 6 + 1)])
        pygame.draw.polygon(surf, (180, 160, 100), [(w // 2 + 3, h // 6), (w // 2 + 6, h // 6 - 6), (w // 2 + 1, h // 6 + 1)])
        # Wings
        pygame.draw.polygon(surf, (*secondary, 180), [(w // 2 - 6, h // 3 + 2), (w // 2 - 18, h // 6), (w // 2 - 2, h // 3 + 8)])
        pygame.draw.polygon(surf, (*secondary, 180), [(w // 2 + 6, h // 3 + 2), (w // 2 + 18, h // 6), (w // 2 + 2, h // 3 + 8)])
        # Tail
        pygame.draw.arc(surf, primary, (w // 2 - 2, h // 2, 14, 10), 0.5, 2.5, 3)
        # Legs
        pygame.draw.rect(surf, primary, (w // 2 - 5, h // 2 + 6, 3, 6))
        pygame.draw.rect(surf, primary, (w // 2 + 2, h // 2 + 6, 3, 6))
        # Fire breath particles
        for i in range(3):
            fx = w // 2 + 6 + i * 3
            fy = h // 6 + 2 + random.randint(-2, 2)
            pygame.draw.circle(surf, (255, 150 - i * 30, 0), (fx, fy), 2 - (i > 1))

    elif char_class == 'slime':
        surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(surf, (0, 0, 0, 60), (w // 2 - 8, h - 4, 16, 4))
        col = primary
        # Blob body
        pygame.draw.ellipse(surf, col, (w // 2 - 9, h // 2 - 2, 18, 16))
        pygame.draw.ellipse(surf, col, (w // 2 - 7, h // 2 - 6, 14, 12))
        # Highlight
        lighter = (min(255, col[0] + 60), min(255, col[1] + 60), min(255, col[2] + 60), 120)
        pygame.draw.ellipse(surf, lighter, (w // 2 - 3, h // 2 - 4, 6, 4))
        # Eyes
        pygame.draw.circle(surf, C_WHITE, (w // 2 - 3, h // 2 + 1), 3)
        pygame.draw.circle(surf, C_WHITE, (w // 2 + 3, h // 2 + 1), 3)
        pygame.draw.circle(surf, C_BLACK, (w // 2 - 3, h // 2 + 2), 1)
        pygame.draw.circle(surf, C_BLACK, (w // 2 + 3, h // 2 + 2), 1)

    elif char_class == 'boss_lich':
        surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(surf, (0, 0, 0, 80), (w // 2 - 10, h - 5, 20, 5))
        # Dark robes
        pygame.draw.polygon(surf, (30, 10, 50), [(w // 2, body_top - 3), (w // 2 - 10, h - 6), (w // 2 + 10, h - 6)])
        pygame.draw.polygon(surf, (50, 20, 70), [(w // 2, body_top - 3), (w // 2 - 8, h - 8), (w // 2 + 8, h - 8)], 1)
        # Skull head with glow
        pygame.draw.circle(surf, (200, 200, 180), (head_cx, head_cy - 2), 6)
        # Glowing eyes
        pygame.draw.circle(surf, (100, 255, 100), (head_cx - 2, head_cy - 3), 2)
        pygame.draw.circle(surf, (100, 255, 100), (head_cx + 2, head_cy - 3), 2)
        pygame.draw.circle(surf, (200, 255, 200), (head_cx - 2, head_cy - 3), 1)
        pygame.draw.circle(surf, (200, 255, 200), (head_cx + 2, head_cy - 3), 1)
        # Crown
        for i in range(5):
            cx2 = head_cx - 5 + i * 2 + 1
            pygame.draw.polygon(surf, C_GOLD, [(cx2, head_cy - 8), (cx2 - 1, head_cy - 5), (cx2 + 1, head_cy - 5)])
        # Staff with skull
        pygame.draw.rect(surf, (60, 40, 80), (w // 2 + 7, body_top - 10, 2, 22))
        pygame.draw.circle(surf, (180, 100, 255), (w // 2 + 8, body_top - 10), 4)
        pygame.draw.circle(surf, (220, 150, 255), (w // 2 + 8, body_top - 10), 2)
        # Floating particles
        for i in range(4):
            px2 = w // 2 + random.randint(-12, 12)
            py2 = random.randint(body_top - 5, body_bot)
            pygame.draw.circle(surf, (120, 80, 200, 150), (px2, py2), 1)

    elif char_class == 'zombie':
        surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(surf, (0, 0, 0, 60), (w // 2 - 8, h - 5, 16, 5))
        # Tattered body
        pygame.draw.rect(surf, (70, 90, 50), (w // 2 - 5, body_top, 10, body_bot - body_top))
        # Torn shirt
        pygame.draw.rect(surf, (80, 70, 50), (w // 2 - 5, body_top + 2, 10, 6))
        pygame.draw.rect(surf, (60, 50, 35), (w // 2 + 2, body_top + 4, 4, 8))  # hole
        # Green-gray head
        pygame.draw.circle(surf, (90, 110, 70), (head_cx, head_cy), head_r)
        # Sunken eyes
        pygame.draw.rect(surf, (40, 20, 20), (head_cx - 3, eye_y - 1, 2, 3))
        pygame.draw.rect(surf, (40, 20, 20), (head_cx + 1, eye_y - 1, 2, 3))
        # Open mouth
        pygame.draw.rect(surf, (30, 10, 10), (head_cx - 2, head_cy + 3, 4, 2))
        # Arms reaching forward
        pygame.draw.rect(surf, (70, 90, 50), (w // 2 - 8, body_top + 3, 3, 10))
        pygame.draw.rect(surf, (70, 90, 50), (w // 2 + 5, body_top + 3, 3, 10))
        # Legs dragging
        pygame.draw.rect(surf, (60, 80, 45), (w // 2 - 4, body_bot, 3, 6))
        pygame.draw.rect(surf, (60, 80, 45), (w // 2 + 1, body_bot, 3, 5))

    elif char_class == 'spider':
        surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(surf, (0, 0, 0, 50), (w // 2 - 8, h - 3, 16, 4))
        # Body (abdomen)
        pygame.draw.ellipse(surf, (50, 30, 20), (w // 2 - 6, h // 2 + 2, 12, 10))
        # Cephalothorax
        pygame.draw.ellipse(surf, (60, 40, 25), (w // 2 - 4, h // 2 - 3, 8, 7))
        # Red markings
        pygame.draw.ellipse(surf, (180, 30, 20), (w // 2 - 2, h // 2 + 5, 4, 4))
        # Eyes (8 of them)
        for dx in [-3, -1, 1, 3]:
            pygame.draw.circle(surf, (255, 0, 0), (w // 2 + dx, h // 2 - 3), 1)
        for dx in [-2, 2]:
            pygame.draw.circle(surf, (255, 50, 0), (w // 2 + dx, h // 2 - 5), 1)
        # Legs (8)
        for side in [-1, 1]:
            for i in range(4):
                lx = w // 2 + side * (3 + i)
                ly = h // 2 + i - 1
                pygame.draw.line(surf, (40, 25, 15), (w // 2 + side * 3, h // 2 + 1), (lx + side * 4, ly + 4), 1)
        # Fangs
        pygame.draw.line(surf, (200, 200, 180), (w // 2 - 1, h // 2 - 1), (w // 2 - 2, h // 2 + 2), 1)
        pygame.draw.line(surf, (200, 200, 180), (w // 2 + 1, h // 2 - 1), (w // 2 + 2, h // 2 + 2), 1)

    elif char_class == 'mimic':
        surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(surf, (0, 0, 0, 60), (w // 2 - 8, h - 4, 16, 4))
        # Chest body
        pygame.draw.rect(surf, (130, 80, 25), (w // 2 - 8, h // 2 - 2, 16, 14))
        pygame.draw.rect(surf, (100, 60, 15), (w // 2 - 8, h // 2 - 2, 16, 14), 1)
        # Open lid with teeth
        pygame.draw.rect(surf, (140, 90, 30), (w // 2 - 9, h // 2 - 6, 18, 5))
        # Teeth along opening
        for i in range(6):
            tx2 = w // 2 - 7 + i * 3
            pygame.draw.polygon(surf, (240, 230, 210), [(tx2, h // 2 - 2), (tx2 + 1, h // 2 + 2), (tx2 + 2, h // 2 - 2)])
        # Tongue
        pygame.draw.arc(surf, (200, 50, 60), (w // 2 - 3, h // 2 - 1, 6, 8), 3.14, 6.28, 2)
        # Eye inside
        pygame.draw.circle(surf, (255, 220, 0), (w // 2, h // 2 - 4), 3)
        pygame.draw.circle(surf, C_BLACK, (w // 2, h // 2 - 4), 1)
        # Metal bands
        pygame.draw.rect(surf, (180, 170, 50), (w // 2 - 8, h // 2 + 2, 16, 2))
        pygame.draw.rect(surf, (180, 170, 50), (w // 2 - 8, h // 2 + 8, 16, 2))

    elif char_class == 'bat_swarm':
        surf.fill((0, 0, 0, 0))
        # Multiple small bats
        for bx, by in [(0, 0), (-5, 3), (5, -2), (-3, -4), (4, 5)]:
            cx2 = w // 2 + bx
            cy2 = h // 2 + by
            # Body
            pygame.draw.ellipse(surf, (40, 30, 50), (cx2 - 2, cy2 - 1, 4, 3))
            # Wings
            pygame.draw.polygon(surf, (50, 35, 60), [(cx2, cy2), (cx2 - 5, cy2 - 3), (cx2 - 3, cy2 + 1)])
            pygame.draw.polygon(surf, (50, 35, 60), [(cx2, cy2), (cx2 + 5, cy2 - 3), (cx2 + 3, cy2 + 1)])
            # Eyes
            pygame.draw.circle(surf, (255, 50, 50), (cx2 - 1, cy2 - 1), 1)
            pygame.draw.circle(surf, (255, 50, 50), (cx2 + 1, cy2 - 1), 1)

    elif char_class == 'wraith':
        surf.fill((0, 0, 0, 0))
        # Ghostly body (translucent)
        ghost_col = (80, 60, 120, 160)
        # Flowing robes
        pts = [(w // 2, body_top - 5), (w // 2 - 8, h - 4), (w // 2 - 3, h - 7),
               (w // 2, h - 3), (w // 2 + 3, h - 7), (w // 2 + 8, h - 4)]
        gs = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.polygon(gs, ghost_col, pts)
        surf.blit(gs, (0, 0))
        # Hooded head
        pygame.draw.circle(surf, (60, 45, 100, 180), (head_cx, head_cy - 2), 6)
        pygame.draw.arc(surf, (40, 30, 70), (head_cx - 6, head_cy - 8, 12, 10), 0, 3.14, 3)
        # Glowing red eyes
        pygame.draw.circle(surf, (255, 50, 50), (head_cx - 2, head_cy - 2), 2)
        pygame.draw.circle(surf, (255, 50, 50), (head_cx + 2, head_cy - 2), 2)
        pygame.draw.circle(surf, (255, 120, 120), (head_cx - 2, head_cy - 2), 1)
        pygame.draw.circle(surf, (255, 120, 120), (head_cx + 2, head_cy - 2), 1)
        # Wispy trail particles
        for i in range(5):
            px2 = w // 2 + random.randint(-8, 8)
            py2 = h - 4 + random.randint(-2, 4)
            pygame.draw.circle(surf, (80, 60, 120, 80), (px2, min(h - 1, py2)), 2)

    elif char_class == 'troll':
        surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (w // 2 - 9, h - 5, 18, 5))
        # Big hunched body
        pygame.draw.rect(surf, (50, 80, 40), (w // 2 - 7, body_top - 2, 14, body_bot - body_top + 6))
        pygame.draw.ellipse(surf, (55, 85, 45), (w // 2 - 8, body_top - 4, 16, 12))
        # Small head
        pygame.draw.circle(surf, (60, 95, 50), (head_cx, head_cy + 1), 5)
        # Beady eyes
        pygame.draw.circle(surf, (255, 200, 0), (head_cx - 2, head_cy), 2)
        pygame.draw.circle(surf, (255, 200, 0), (head_cx + 2, head_cy), 2)
        pygame.draw.circle(surf, C_BLACK, (head_cx - 2, head_cy), 1)
        pygame.draw.circle(surf, C_BLACK, (head_cx + 2, head_cy), 1)
        # Big nose
        pygame.draw.circle(surf, (70, 100, 55), (head_cx, head_cy + 2), 2)
        # Long arms with claws
        pygame.draw.rect(surf, (50, 80, 40), (w // 2 - 10, body_top + 1, 4, 16))
        pygame.draw.rect(surf, (50, 80, 40), (w // 2 + 6, body_top + 1, 4, 16))
        # Claws
        for side in [-1, 1]:
            cx2 = w // 2 + side * 8 + (1 if side == 1 else -3)
            for ci in range(3):
                pygame.draw.line(surf, (200, 190, 160), (cx2 + ci, body_top + 16), (cx2 + ci + side, body_top + 19), 1)
        # Legs
        pygame.draw.rect(surf, (45, 75, 38), (w // 2 - 5, body_bot + 2, 4, 5))
        pygame.draw.rect(surf, (45, 75, 38), (w // 2 + 1, body_bot + 2, 4, 5))

    elif char_class == 'beholder':
        surf.fill((0, 0, 0, 0))
        # Floating orb body
        pygame.draw.circle(surf, primary, (w // 2, h // 2 + 2), 10)
        pygame.draw.circle(surf, (min(255, primary[0] + 30), min(255, primary[1] + 30), min(255, primary[2] + 30)), (w // 2 - 3, h // 2 - 2), 4)
        # Central eye
        pygame.draw.circle(surf, (240, 240, 200), (w // 2, h // 2 + 2), 5)
        pygame.draw.circle(surf, (200, 50, 50), (w // 2, h // 2 + 2), 3)
        pygame.draw.circle(surf, C_BLACK, (w // 2, h // 2 + 2), 1)
        # Eye stalks
        stalk_positions = [(-6, -8), (-3, -10), (0, -11), (3, -10), (6, -8)]
        for sx2, sy2 in stalk_positions:
            ex2 = w // 2 + sx2
            ey2 = h // 2 + sy2
            pygame.draw.line(surf, (min(255, primary[0] + 10), min(255, primary[1] + 10), primary[2]), (w // 2 + sx2 // 2, h // 2 - 6), (ex2, ey2), 1)
            pygame.draw.circle(surf, (255, 255, 100), (ex2, ey2), 2)
            pygame.draw.circle(surf, C_BLACK, (ex2, ey2), 1)
        # Mouth
        pygame.draw.arc(surf, (150, 40, 40), (w // 2 - 4, h // 2 + 5, 8, 5), 3.14, 6.28, 1)
        # Teeth
        for ti in range(4):
            pygame.draw.line(surf, (220, 210, 190), (w // 2 - 3 + ti * 2, h // 2 + 7), (w // 2 - 3 + ti * 2, h // 2 + 9), 1)

    elif char_class == 'gelatinous_cube':
        surf.fill((0, 0, 0, 0))
        # Translucent cube
        gc = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(gc, (100, 200, 100, 80), (w // 2 - 10, h // 4, 20, 20))
        pygame.draw.rect(gc, (120, 220, 120, 120), (w // 2 - 10, h // 4, 20, 20), 1)
        # Things floating inside
        pygame.draw.rect(gc, (180, 170, 150, 100), (w // 2 - 3, h // 2 - 2, 4, 3))  # bone
        pygame.draw.circle(gc, (200, 200, 60, 100), (w // 2 + 4, h // 2 + 2), 2)  # coin
        pygame.draw.rect(gc, (120, 70, 30, 90), (w // 2 - 6, h // 2 + 3, 3, 5))  # sword handle
        # Highlight
        pygame.draw.line(gc, (180, 255, 180, 60), (w // 2 - 8, h // 4 + 2), (w // 2 - 6, h // 4 + 8), 2)
        surf.blit(gc, (0, 0))

    elif char_class == 'kobold':
        surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(surf, (0, 0, 0, 50), (w // 2 - 6, h - 4, 12, 4))
        oy = h - 22
        # Small reptilian body
        pygame.draw.rect(surf, (140, 90, 50), (w // 2 - 4, oy + 6, 8, 10))
        # Scaly head (pointy snout)
        pygame.draw.circle(surf, (150, 100, 55), (w // 2, oy + 4), 5)
        pygame.draw.ellipse(surf, (150, 100, 55), (w // 2 + 2, oy + 2, 5, 3))  # snout
        # Orange eyes
        pygame.draw.circle(surf, (255, 180, 0), (w // 2 - 2, oy + 3), 2)
        pygame.draw.circle(surf, C_BLACK, (w // 2 - 2, oy + 3), 1)
        # Horns
        pygame.draw.line(surf, (180, 150, 100), (w // 2 - 4, oy + 1), (w // 2 - 6, oy - 3), 1)
        pygame.draw.line(surf, (180, 150, 100), (w // 2 + 1, oy + 1), (w // 2 + 3, oy - 3), 1)
        # Tail
        pygame.draw.arc(surf, (140, 90, 50), (w // 2 + 2, oy + 10, 8, 8), 1.5, 4, 1)
        # Legs
        pygame.draw.rect(surf, (130, 85, 45), (w // 2 - 3, oy + 15, 2, 4))
        pygame.draw.rect(surf, (130, 85, 45), (w // 2 + 1, oy + 15, 2, 4))
        # Tiny spear
        pygame.draw.rect(surf, (100, 80, 40), (w // 2 + 5, oy, 1, 14))
        pygame.draw.polygon(surf, (180, 180, 190), [(w // 2 + 4, oy), (w // 2 + 6, oy), (w // 2 + 5, oy - 3)])

    elif char_class == 'mind_flayer':
        surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (w // 2 - 8, h - 5, 16, 5))
        # Robed body
        pygame.draw.polygon(surf, (60, 20, 80), [(w // 2, body_top - 1), (w // 2 - 7, h - 6), (w // 2 + 7, h - 6)])
        # Bulbous head
        pygame.draw.ellipse(surf, (140, 100, 160), (head_cx - 6, head_cy - 8, 12, 10))
        # White pupil-less eyes
        pygame.draw.circle(surf, (255, 255, 255), (head_cx - 2, head_cy - 4), 2)
        pygame.draw.circle(surf, (255, 255, 255), (head_cx + 2, head_cy - 4), 2)
        # Tentacles (face)
        for ti in range(4):
            tx2 = head_cx - 3 + ti * 2
            for seg in range(4):
                ty2 = head_cy + seg * 2
                wobble = int(math.sin(ti + seg * 0.8) * 1)
                pygame.draw.rect(surf, (130, 90, 150), (tx2 + wobble, ty2, 2, 2))
        # Psychic aura
        aura = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(aura, (180, 100, 255, 30), (w // 2, h // 2 - 2), 14)
        surf.blit(aura, (0, 0))

    elif char_class == 'st_mind_flayer':
        # Stranger Things Mind Flayer - massive shadow spider entity
        surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (w // 2 - 10, h - 5, 20, 5))
        # Semi-transparent smoky body (darker, more monstrous)
        pygame.draw.polygon(surf, (25, 15, 30), [(w // 2, body_top - 4), (w // 2 - 9, body_bot + 2), (w // 2 + 9, body_bot + 2)])
        # Shadow tendrils/spider legs extending outward
        for i in range(6):
            angle = math.pi * 0.3 + (i / 5) * math.pi * 0.4
            lx = w // 2 + int(math.cos(angle + math.pi) * (8 + i % 3))
            ly = body_top + 3 + i * 2
            ex = w // 2 + int(math.cos(angle + math.pi) * (14 + i % 2 * 3))
            ey = ly + random.randint(-2, 3)
            pygame.draw.line(surf, (40, 20, 50), (lx, ly), (ex, ey), 2)
        for i in range(6):
            angle = math.pi * 0.3 + (i / 5) * math.pi * 0.4
            lx = w // 2 - int(math.cos(angle + math.pi) * (8 + i % 3))
            ly = body_top + 3 + i * 2
            ex = w // 2 - int(math.cos(angle + math.pi) * (14 + i % 2 * 3))
            ey = ly + random.randint(-2, 3)
            pygame.draw.line(surf, (40, 20, 50), (lx, ly), (ex, ey), 2)
        # Head - elongated spider-like with split jaw
        pygame.draw.ellipse(surf, (30, 18, 40), (head_cx - 7, head_cy - 6, 14, 10))
        # Glowing red eyes (many, spider-like)
        for ex2, ey2 in [(head_cx - 4, head_cy - 3), (head_cx + 4, head_cy - 3),
                         (head_cx - 2, head_cy - 5), (head_cx + 2, head_cy - 5)]:
            pygame.draw.circle(surf, (255, 60, 60), (ex2, ey2), 1)
        # Lower jaw split
        pygame.draw.line(surf, (50, 25, 60), (head_cx - 3, head_cy + 2), (head_cx - 5, head_cy + 6), 1)
        pygame.draw.line(surf, (50, 25, 60), (head_cx + 3, head_cy + 2), (head_cx + 5, head_cy + 6), 1)
        pygame.draw.line(surf, (50, 25, 60), (head_cx, head_cy + 2), (head_cx, head_cy + 5), 1)
        # Legs (digitigrade)
        pygame.draw.rect(surf, (25, 15, 30), (w // 2 - 5, body_bot, 3, 6))
        pygame.draw.rect(surf, (25, 15, 30), (w // 2 + 2, body_bot, 3, 6))
        # Red storm / Upside Down aura
        aura = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(aura, (200, 30, 30, 25), (w // 2, h // 2 - 2), 16)
        for i in range(6):
            px2 = w // 2 + random.randint(-12, 12)
            py2 = random.randint(body_top - 6, body_bot + 4)
            pygame.draw.circle(aura, (255, 40, 40, 80), (px2, py2), 1)
        surf.blit(aura, (0, 0))

    elif char_class == 'minotaur':
        surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (w // 2 - 9, h - 5, 18, 5))
        # Muscular body
        pygame.draw.rect(surf, (120, 70, 40), (w // 2 - 7, body_top - 2, 14, body_bot - body_top + 4))
        # Bull head
        pygame.draw.circle(surf, (130, 80, 45), (head_cx, head_cy), 6)
        pygame.draw.ellipse(surf, (130, 80, 45), (head_cx - 3, head_cy + 2, 6, 4))  # snout
        # Horns
        pygame.draw.polygon(surf, (220, 210, 180), [(head_cx - 5, head_cy - 2), (head_cx - 9, head_cy - 9), (head_cx - 3, head_cy - 4)])
        pygame.draw.polygon(surf, (220, 210, 180), [(head_cx + 5, head_cy - 2), (head_cx + 9, head_cy - 9), (head_cx + 3, head_cy - 4)])
        # Red eyes
        pygame.draw.circle(surf, (255, 40, 40), (head_cx - 3, head_cy - 1), 2)
        pygame.draw.circle(surf, (255, 40, 40), (head_cx + 3, head_cy - 1), 2)
        # Nose ring
        pygame.draw.circle(surf, C_GOLD, (head_cx, head_cy + 4), 2, 1)
        # Big arms
        pygame.draw.rect(surf, (120, 70, 40), (w // 2 - 10, body_top, 4, 14))
        pygame.draw.rect(surf, (120, 70, 40), (w // 2 + 6, body_top, 4, 14))
        # Great axe
        pygame.draw.rect(surf, (80, 60, 30), (w // 2 + 9, body_top - 8, 2, 20))
        pygame.draw.polygon(surf, (170, 170, 180), [(w // 2 + 8, body_top - 8), (w // 2 + 15, body_top - 5), (w // 2 + 8, body_top - 2)])
        pygame.draw.polygon(surf, (170, 170, 180), [(w // 2 + 8, body_top - 2), (w // 2 + 15, body_top + 1), (w // 2 + 8, body_top + 4)])
        # Hooves
        pygame.draw.rect(surf, (60, 40, 20), (w // 2 - 5, body_bot + 3, 4, 4))
        pygame.draw.rect(surf, (60, 40, 20), (w // 2 + 1, body_bot + 3, 4, 4))

    elif char_class == 'dark_knight':
        surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (w // 2 - 8, h - 5, 16, 5))
        # Dark armor body
        pygame.draw.rect(surf, (30, 25, 35), (w // 2 - 5, body_top, 10, body_bot - body_top))
        pygame.draw.rect(surf, (50, 40, 55), (w // 2 - 5, body_top, 10, body_bot - body_top), 1)
        # Shoulders
        pygame.draw.rect(surf, (40, 30, 45), (w // 2 - 8, body_top, 4, 4))
        pygame.draw.rect(surf, (40, 30, 45), (w // 2 + 4, body_top, 4, 4))
        # Spike on shoulders
        pygame.draw.polygon(surf, (60, 45, 65), [(w // 2 - 8, body_top), (w // 2 - 6, body_top - 4), (w // 2 - 4, body_top)])
        pygame.draw.polygon(surf, (60, 45, 65), [(w // 2 + 4, body_top), (w // 2 + 6, body_top - 4), (w // 2 + 8, body_top)])
        # Full helm
        pygame.draw.circle(surf, (35, 28, 40), (head_cx, head_cy), head_r + 1)
        pygame.draw.rect(surf, (35, 28, 40), (head_cx - 5, head_cy - 6, 10, 4))
        # Glowing visor slit
        pygame.draw.rect(surf, (255, 40, 40), (head_cx - 3, head_cy - 1, 6, 2))
        # Dark sword
        pygame.draw.rect(surf, (50, 40, 60), (w // 2 + 5, body_top - 4, 3, 18))
        pygame.draw.rect(surf, (80, 60, 90), (w // 2 + 3, body_top + 12, 7, 3))
        # Legs
        pygame.draw.rect(surf, (28, 22, 32), (w // 2 - 4, body_bot, 3, 6))
        pygame.draw.rect(surf, (28, 22, 32), (w // 2 + 1, body_bot, 3, 6))
        # Dark aura
        aura = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(aura, (80, 0, 120, 25), (w // 2, h // 2), 14)
        surf.blit(aura, (0, 0))

    elif char_class == 'vecna':
        # DnD Vecna - skeletal lich-god with missing hand and eye
        surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(surf, (0, 0, 0, 80), (w // 2 - 10, h - 5, 20, 5))
        # Dark robes with arcane symbols
        pygame.draw.polygon(surf, (50, 20, 70), [(w // 2, body_top - 4), (w // 2 - 10, h - 6), (w // 2 + 10, h - 6)])
        pygame.draw.polygon(surf, (80, 30, 100), [(w // 2, body_top - 4), (w // 2 - 8, h - 8), (w // 2 + 8, h - 8)], 1)
        # Arcane runes on robe
        for i in range(3):
            ry2 = body_top + 6 + i * 6
            pygame.draw.circle(surf, (120, 60, 180, 150), (w // 2, ry2), 2, 1)
        # Skeletal head
        pygame.draw.circle(surf, (200, 190, 170), (head_cx, head_cy - 1), 6)
        # One glowing green eye (left), empty socket (right)
        pygame.draw.circle(surf, (0, 255, 0), (head_cx - 3, head_cy - 2), 3)
        pygame.draw.circle(surf, (150, 255, 150), (head_cx - 3, head_cy - 2), 1)
        pygame.draw.circle(surf, (20, 10, 10), (head_cx + 3, head_cy - 2), 2)  # empty socket
        # Crown of dark power
        for i in range(5):
            cx2 = head_cx - 5 + i * 2 + 1
            pygame.draw.polygon(surf, (160, 50, 200), [(cx2, head_cy - 8), (cx2 - 1, head_cy - 5), (cx2 + 1, head_cy - 5)])
        # Left arm (skeletal, missing hand - the Hand of Vecna)
        pygame.draw.rect(surf, (180, 170, 150), (w // 2 - 8, body_top + 2, 2, 10))
        pygame.draw.circle(surf, (100, 255, 100, 150), (w // 2 - 8, body_top + 12), 3)  # green stump glow
        # Right arm with staff
        pygame.draw.rect(surf, (180, 170, 150), (w // 2 + 6, body_top + 2, 2, 10))
        pygame.draw.rect(surf, (60, 30, 80), (w // 2 + 8, body_top - 12, 2, 24))
        pygame.draw.circle(surf, (200, 50, 255), (w // 2 + 9, body_top - 12), 5)
        pygame.draw.circle(surf, (255, 150, 255), (w // 2 + 9, body_top - 12), 2)
        # Necrotic aura
        aura = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(aura, (100, 0, 150, 35), (w // 2, h // 2 - 2), 16)
        for i in range(6):
            px2 = w // 2 + random.randint(-14, 14)
            py2 = random.randint(body_top - 6, body_bot + 2)
            pygame.draw.circle(aura, (150, 50, 255, 80), (px2, py2), 1)
        surf.blit(aura, (0, 0))

    elif char_class == 'demogorgon':
        # DnD Demogorgon - two-headed demon prince, massive and terrifying
        surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(surf, (0, 0, 0, 90), (w // 2 - 10, h - 5, 20, 5))
        # Massive reptilian body
        pygame.draw.rect(surf, (40, 80, 40), (w // 2 - 8, body_top - 2, 16, body_bot - body_top + 6))
        pygame.draw.rect(surf, (50, 100, 50), (w // 2 - 8, body_top - 2, 16, body_bot - body_top + 6), 1)
        # TWO heads on long necks
        # Left head
        pygame.draw.line(surf, (45, 85, 45), (w // 2 - 3, body_top - 2), (w // 2 - 6, body_top - 10), 3)
        pygame.draw.circle(surf, (50, 90, 45), (w // 2 - 6, body_top - 12), 5)
        pygame.draw.circle(surf, (255, 50, 0), (w // 2 - 8, body_top - 13), 2)  # red eye
        pygame.draw.rect(surf, (200, 180, 150), (w // 2 - 9, body_top - 10, 4, 1))  # teeth
        # Right head
        pygame.draw.line(surf, (45, 85, 45), (w // 2 + 3, body_top - 2), (w // 2 + 6, body_top - 10), 3)
        pygame.draw.circle(surf, (50, 90, 45), (w // 2 + 6, body_top - 12), 5)
        pygame.draw.circle(surf, (255, 50, 0), (w // 2 + 8, body_top - 13), 2)  # red eye
        pygame.draw.rect(surf, (200, 180, 150), (w // 2 + 5, body_top - 10, 4, 1))  # teeth
        # Tentacle arms
        for side in [-1, 1]:
            sx2 = w // 2 + side * 7
            for seg in range(6):
                wobble = int(math.sin(seg * 1.2 + side) * 2)
                pygame.draw.rect(surf, (45, 85, 45), (sx2 + wobble + side * seg, body_top + seg * 2, 3, 3))
        # Forked tail
        pygame.draw.arc(surf, (40, 80, 40), (w // 2, body_bot, 10, 8), 0.5, 2.5, 2)
        pygame.draw.line(surf, (40, 80, 40), (w // 2 + 8, body_bot + 5), (w // 2 + 12, body_bot + 2), 1)
        pygame.draw.line(surf, (40, 80, 40), (w // 2 + 8, body_bot + 5), (w // 2 + 12, body_bot + 8), 1)
        # Legs with claws
        pygame.draw.rect(surf, (35, 70, 35), (w // 2 - 5, body_bot + 2, 4, 6))
        pygame.draw.rect(surf, (35, 70, 35), (w // 2 + 1, body_bot + 2, 4, 6))
        # Demonic aura
        aura = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(aura, (80, 0, 0, 30), (w // 2, h // 2 - 4), 16)
        surf.blit(aura, (0, 0))

    elif char_class == 'st_vecna':
        # Stranger Things Vecna (001/Henry Creel) - humanoid covered in vines/tendrils
        surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (w // 2 - 9, h - 5, 18, 5))
        # Desiccated humanoid body - dark red/brown flesh
        pygame.draw.rect(surf, (80, 40, 40), (w // 2 - 5, body_top, 10, body_bot - body_top))
        # Vine-like tendrils all over body
        for i in range(8):
            vx = w // 2 + random.randint(-6, 6)
            vy = body_top + random.randint(0, body_bot - body_top)
            pygame.draw.line(surf, (50, 25, 20), (vx, vy), (vx + random.randint(-4, 4), vy + random.randint(2, 6)), 1)
        # Head - grotesque, nose-less face
        pygame.draw.circle(surf, (90, 45, 40), (head_cx, head_cy), 6)
        # Sunken glowing eyes
        pygame.draw.circle(surf, (200, 0, 0), (head_cx - 3, head_cy - 1), 2)
        pygame.draw.circle(surf, (200, 0, 0), (head_cx + 3, head_cy - 1), 2)
        pygame.draw.circle(surf, (255, 100, 100), (head_cx - 3, head_cy - 1), 1)
        pygame.draw.circle(surf, (255, 100, 100), (head_cx + 3, head_cy - 1), 1)
        # No nose - just a slit
        pygame.draw.line(surf, (50, 20, 20), (head_cx, head_cy + 1), (head_cx, head_cy + 3), 1)
        # Cracked texture on head
        pygame.draw.line(surf, (60, 30, 25), (head_cx - 4, head_cy - 4), (head_cx - 1, head_cy + 2), 1)
        pygame.draw.line(surf, (60, 30, 25), (head_cx + 2, head_cy - 3), (head_cx + 4, head_cy + 1), 1)
        # Extended clawed hands
        pygame.draw.rect(surf, (70, 35, 35), (w // 2 - 9, body_top + 2, 3, 12))
        pygame.draw.rect(surf, (70, 35, 35), (w // 2 + 6, body_top + 2, 3, 12))
        # Claws
        for side in [-1, 1]:
            cx2 = w // 2 + side * 8 + (1 if side == 1 else -2)
            for ci in range(3):
                pygame.draw.line(surf, (40, 20, 15), (cx2 + ci, body_top + 14), (cx2 + ci + side * 2, body_top + 18), 1)
        # Legs
        pygame.draw.rect(surf, (70, 35, 35), (w // 2 - 4, body_bot, 3, 6))
        pygame.draw.rect(surf, (70, 35, 35), (w // 2 + 1, body_bot, 3, 6))
        # Psychic/Upside Down red particle aura
        aura = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(aura, (150, 0, 0, 30), (w // 2, h // 2 - 2), 14)
        for i in range(5):
            px2 = w // 2 + random.randint(-10, 10)
            py2 = random.randint(body_top - 4, body_bot + 4)
            pygame.draw.circle(aura, (255, 50, 50, 100), (px2, py2), 1)
        surf.blit(aura, (0, 0))

    elif char_class == 'st_demogorgon':
        # Stranger Things Demogorgon - tall, faceless with petal-mouth head
        surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (w // 2 - 9, h - 5, 18, 5))
        # Tall thin grey-brown body
        pygame.draw.rect(surf, (90, 60, 50), (w // 2 - 5, body_top - 2, 10, body_bot - body_top + 4))
        # Muscular texture
        pygame.draw.line(surf, (80, 50, 40), (w // 2 - 3, body_top + 2), (w // 2 - 3, body_bot - 2), 1)
        pygame.draw.line(surf, (80, 50, 40), (w // 2 + 3, body_top + 2), (w // 2 + 3, body_bot - 2), 1)
        # PETAL-MOUTH HEAD (signature look - flower-like opening)
        # Closed head base
        pygame.draw.circle(surf, (100, 65, 50), (head_cx, head_cy - 1), 6)
        # Petal flaps opening outward
        petals = 5
        for i in range(petals):
            angle = (i / petals) * math.pi * 2 - math.pi / 2
            px2 = head_cx + int(math.cos(angle) * 7)
            py2 = head_cy - 1 + int(math.sin(angle) * 7)
            pygame.draw.polygon(surf, (110, 70, 55), [
                (head_cx + int(math.cos(angle) * 3), head_cy - 1 + int(math.sin(angle) * 3)),
                (px2 - 1, py2), (px2 + 1, py2)
            ])
        # Inner mouth - red/pink
        pygame.draw.circle(surf, (180, 40, 50), (head_cx, head_cy - 1), 3)
        # Tiny teeth ring
        for i in range(6):
            angle = (i / 6) * math.pi * 2
            tx2 = head_cx + int(math.cos(angle) * 2)
            ty2 = head_cy - 1 + int(math.sin(angle) * 2)
            pygame.draw.rect(surf, (220, 210, 190), (tx2, ty2, 1, 1))
        # Long clawed arms
        pygame.draw.rect(surf, (85, 55, 45), (w // 2 - 9, body_top, 3, 14))
        pygame.draw.rect(surf, (85, 55, 45), (w // 2 + 6, body_top, 3, 14))
        # Large claws
        for side in [-1, 1]:
            cx2 = w // 2 + side * 8 + (1 if side == 1 else -2)
            for ci in range(4):
                pygame.draw.line(surf, (60, 40, 30), (cx2 + ci, body_top + 13), (cx2 + ci + side * 2, body_top + 18), 1)
        # Digitigrade legs
        pygame.draw.rect(surf, (85, 55, 45), (w // 2 - 4, body_bot, 3, 5))
        pygame.draw.rect(surf, (85, 55, 45), (w // 2 + 1, body_bot, 3, 5))
        pygame.draw.rect(surf, (70, 40, 30), (w // 2 - 5, body_bot + 4, 4, 3))
        pygame.draw.rect(surf, (70, 40, 30), (w // 2 + 1, body_bot + 4, 4, 3))

    _tex_cache[key] = surf
    return surf


# ════════════════════════════════════════════════════════════
# PARTICLE SYSTEM
# ════════════════════════════════════════════════════════════
class Particle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'life', 'max_life', 'color', 'size', 'kind']
    def __init__(self, x, y, vx, vy, life, color, size=2, kind='normal'):
        self.x = x; self.y = y; self.vx = vx; self.vy = vy
        self.life = life; self.max_life = life; self.color = color
        self.size = size; self.kind = kind

particles: List[Particle] = []

def spawn_particles(x, y, color, count=8, speed=2, life=30, kind='normal'):
    for _ in range(count):
        angle = random.uniform(0, math.pi * 2)
        spd = random.uniform(0.5, speed)
        particles.append(Particle(
            x + random.randint(-4, 4), y + random.randint(-4, 4),
            math.cos(angle) * spd, math.sin(angle) * spd - 1,
            life + random.randint(-5, 5), color, random.randint(1, 3), kind
        ))

def update_particles():
    for p in particles[:]:
        p.x += p.vx; p.y += p.vy
        p.vy += 0.05  # gravity
        p.life -= 1
        if p.life <= 0:
            particles.remove(p)

def draw_particles(surface, cam_x, cam_y):
    for p in particles:
        alpha = max(0, min(255, int(255 * (p.life / p.max_life))))
        col = (*p.color[:3], alpha) if len(p.color) >= 3 else (*p.color, alpha)
        sx = int(p.x - cam_x)
        sy = int(p.y - cam_y)
        if 0 <= sx < SCREEN_W and 0 <= sy < SCREEN_H:
            sz = max(1, int(p.size * (p.life / p.max_life)))
            if sz > 1:
                ps = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
                pygame.draw.circle(ps, col, (sz, sz), sz)
                surface.blit(ps, (sx - sz, sy - sz))
            else:
                surface.set_at((sx, sy), col[:3])


# ════════════════════════════════════════════════════════════
# FLOATING DAMAGE TEXT
# ════════════════════════════════════════════════════════════
@dataclass
class FloatText:
    x: float
    y: float
    text: str
    color: tuple
    life: int = 45
    max_life: int = 45

float_texts: List[FloatText] = []

def spawn_float_text(x, y, text, color=C_WHITE):
    float_texts.append(FloatText(x, y, text, color))

def update_float_texts():
    for ft in float_texts[:]:
        ft.y -= 0.8
        ft.life -= 1
        if ft.life <= 0:
            float_texts.remove(ft)

def draw_float_texts(surface, cam_x, cam_y, font):
    for ft in float_texts:
        alpha = max(0, min(255, int(255 * (ft.life / ft.max_life))))
        sx = int(ft.x - cam_x)
        sy = int(ft.y - cam_y)
        txt = font.render(ft.text, True, ft.color)
        txt.set_alpha(alpha)
        surface.blit(txt, (sx - txt.get_width() // 2, sy))


# ════════════════════════════════════════════════════════════
# DnD CORE — Stats, Classes, Dice Rolling
# ════════════════════════════════════════════════════════════
def roll(dice_str):
    """Roll dice: '2d6+3' -> result"""
    total = 0
    parts = dice_str.replace('-', '+-').split('+')
    for part in parts:
        part = part.strip()
        if 'd' in part:
            num, sides = part.split('d')
            num = int(num) if num else 1
            sides = int(sides)
            for _ in range(abs(num)):
                r = random.randint(1, sides)
                total += r if num > 0 else -r
        else:
            total += int(part)
    return max(0, total)

def roll_stat():
    """4d6 drop lowest — classic DnD stat generation."""
    rolls = [random.randint(1, 6) for _ in range(4)]
    rolls.sort()
    return sum(rolls[1:])

def modifier(stat):
    return (stat - 10) // 2


class DnDClass:
    """DnD character class definitions."""
    CLASSES = {
        'warrior': {'hp_die': 10, 'primary': 'STR', 'skills': ['Power Strike', 'Shield Bash', 'Rally'],
                    'desc': 'Stalwart defender with heavy armor and weapons',
                    'palette': [(210, 170, 130), (100, 40, 40), (60, 30, 30), (180, 180, 190)]},
        'mage': {'hp_die': 6, 'primary': 'INT', 'skills': ['Fireball', 'Ice Shard', 'Arcane Shield'],
                 'desc': 'Master of the arcane arts',
                 'palette': [(210, 170, 130), (40, 40, 130), (80, 60, 160), (200, 200, 255)]},
        'rogue': {'hp_die': 8, 'primary': 'DEX', 'skills': ['Backstab', 'Smoke Bomb', 'Steal'],
                  'desc': 'Silent shadow dealing deadly strikes',
                  'palette': [(210, 170, 130), (50, 50, 50), (30, 30, 30), (150, 120, 80)]},
        'cleric': {'hp_die': 8, 'primary': 'WIS', 'skills': ['Heal', 'Smite', 'Bless'],
                   'desc': 'Divine healer and undead bane',
                   'palette': [(210, 170, 130), (200, 200, 220), (150, 130, 100), (255, 255, 200)]},
        'ranger': {'hp_die': 8, 'primary': 'DEX', 'skills': ['Arrow Rain', 'Trap', 'Nature\'s Blessing'],
                   'desc': 'Woodland hunter with deadly aim',
                   'palette': [(210, 170, 130), (40, 90, 40), (60, 50, 30), (120, 100, 60)]},
    }


# ════════════════════════════════════════════════════════════
# ENTITY CLASSES
# ════════════════════════════════════════════════════════════
class Entity:
    def __init__(self, name, char_class, level=1, is_ai=False, is_enemy=False):
        self.name = name
        self.char_class = char_class
        self.level = level
        self.is_ai = is_ai
        self.is_enemy = is_enemy
        self.x = 0
        self.y = 0
        self.target_x = 0
        self.target_y = 0
        self.moving = False
        self.alive = True
        self.xp = 0
        self.xp_to_level = 100
        self.skill_points = 0
        self.skill_tree = {}  # {node_id: rank}

        # Generate stats
        cls_data = DnDClass.CLASSES.get(char_class, DnDClass.CLASSES['warrior'])
        self.stats = {
            'STR': roll_stat(), 'DEX': roll_stat(), 'CON': roll_stat(),
            'INT': roll_stat(), 'WIS': roll_stat(), 'CHA': roll_stat()
        }
        # Boost primary stat
        primary = cls_data['primary']
        self.stats[primary] = max(self.stats[primary], 14 + random.randint(0, 4))

        self.max_hp = cls_data['hp_die'] + modifier(self.stats['CON']) + (level - 1) * (cls_data['hp_die'] // 2 + modifier(self.stats['CON']))
        self.hp = self.max_hp
        self.max_mp = 10 + modifier(self.stats['INT']) * 2 + modifier(self.stats['WIS'])
        self.mp = self.max_mp
        self.ac = 10 + modifier(self.stats['DEX'])
        self.skills = cls_data['skills'][:]
        self.inventory: List[dict] = []
        self.equipment = {'weapon': None, 'armor': None, 'accessory': None}

        # Determine attack damage
        if char_class == 'warrior':
            self.attack_dice = '1d8'
            self.ac += 4  # Heavy armor
        elif char_class == 'mage':
            self.attack_dice = '1d4'
        elif char_class == 'rogue':
            self.attack_dice = '1d6'
            self.ac += 2  # Light armor
        elif char_class == 'cleric':
            self.attack_dice = '1d6'
            self.ac += 3  # Medium armor
        elif char_class == 'ranger':
            self.attack_dice = '1d8'
            self.ac += 1
        else:
            self.attack_dice = '1d6'

        # AI personality for companion chat
        self.ai_personality = random.choice(['brave', 'cautious', 'witty', 'wise', 'fierce'])
        self.ai_lines = []

        # Visual
        self.palette = cls_data.get('palette', [(180, 150, 120), (80, 80, 80), (60, 60, 60)])
        self.sprite = None
        self.anim_frame = 0
        self.anim_timer = 0
        self.flash_timer = 0
        self.facing = 'right'

    def get_sprite(self):
        if not self.sprite:
            self.sprite = make_character_sprite(self.char_class, self.palette, is_enemy=self.is_enemy)
        return self.sprite

    def get_attack_bonus(self):
        cls = DnDClass.CLASSES.get(self.char_class, {})
        primary = cls.get('primary', 'STR')
        base = modifier(self.stats[primary]) + (self.level - 1) // 2
        base += get_skill_tree_bonus(self, 'attack_bonus')
        return base

    def attack_roll(self):
        """Roll d20 + attack bonus."""
        d20 = random.randint(1, 20)
        bonus = self.get_attack_bonus()
        return d20, d20 + bonus

    def damage_roll(self):
        base = roll(self.attack_dice)
        cls = DnDClass.CLASSES.get(self.char_class, {})
        primary = cls.get('primary', 'STR')
        dmg = max(1, base + modifier(self.stats[primary]))
        # Skill tree damage bonuses
        dmg_pct = get_skill_tree_bonus(self, 'damage_pct')
        crit_pct = get_skill_tree_bonus(self, 'crit_damage_pct')
        magic_pct = get_skill_tree_bonus(self, 'magic_damage_pct')
        total_pct = dmg_pct + (magic_pct if self.char_class == 'mage' else 0)
        dmg = int(dmg * (1 + total_pct / 100))
        return max(1, dmg)

    def take_damage(self, dmg):
        self.hp = max(0, self.hp - dmg)
        self.flash_timer = 10
        if self.hp <= 0:
            self.alive = False

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def gain_xp(self, amount):
        # Apply XP bonus from skill tree
        xp_bonus = get_skill_tree_bonus(self, 'xp_pct')
        amount = int(amount * (1 + xp_bonus / 100))
        self.xp += amount
        leveled = False
        while self.xp >= self.xp_to_level:
            self.xp -= self.xp_to_level
            self.level += 1
            self.xp_to_level = int(self.xp_to_level * 1.5)
            # Level up stats
            cls_data = DnDClass.CLASSES.get(self.char_class, DnDClass.CLASSES['warrior'])
            hp_gain = cls_data['hp_die'] // 2 + 1 + modifier(self.stats['CON'])
            self.max_hp += max(1, hp_gain)
            self.hp = self.max_hp
            self.max_mp += 2 + modifier(self.stats['INT'])
            self.mp = self.max_mp
            self.skill_points += 2  # 2 skill tree points per level
            leveled = True
        return leveled

    def use_skill(self, skill_idx, target=None, allies=None):
        """Use a class skill. Returns (success, message, damage/heal)."""
        if skill_idx >= len(self.skills):
            return False, "No such skill!", 0
        skill = self.skills[skill_idx]
        cost = max(1, 3 + skill_idx * 2 - get_skill_tree_bonus(self, 'mp_cost_reduction'))

        if self.mp < cost:
            return False, f"Not enough MP! ({cost} needed)", 0

        self.mp -= cost
        # Skill tree multipliers
        _skill_pct = get_skill_tree_bonus(self, 'skill_power_pct')
        _heal_pct = get_skill_tree_bonus(self, 'heal_power_pct')
        _smite_pct = get_skill_tree_bonus(self, 'smite_damage_pct')

        if skill == 'Power Strike':
            dmg = roll('2d8') + modifier(self.stats['STR']) + self.level
            dmg = int(dmg * (1 + _skill_pct / 100))
            return True, f"{self.name} unleashes a POWER STRIKE!", dmg
        elif skill == 'Shield Bash':
            dmg = roll('1d6') + modifier(self.stats['STR'])
            return True, f"{self.name} bashes with their shield! Target is stunned!", dmg
        elif skill == 'Rally':
            heal_amt = roll('1d6') + self.level
            if allies:
                for a in allies:
                    if a.alive:
                        a.heal(heal_amt // 2)
            return True, f"{self.name} rallies the party! Everyone heals {heal_amt // 2} HP!", 0
        elif skill == 'Fireball':
            dmg = roll('3d6') + modifier(self.stats['INT']) + self.level
            dmg = int(dmg * (1 + _skill_pct / 100))
            return True, f"{self.name} hurls a FIREBALL! 🔥", dmg
        elif skill == 'Ice Shard':
            dmg = roll('2d6') + modifier(self.stats['INT'])
            dmg = int(dmg * (1 + _skill_pct / 100))
            return True, f"{self.name} launches ICE SHARDS! ❄️", dmg
        elif skill == 'Arcane Shield':
            if allies:
                for a in allies:
                    if a.alive:
                        a.ac += 2
            return True, f"{self.name} raises an ARCANE SHIELD! Party AC +2!", 0
        elif skill == 'Backstab':
            dmg = roll('3d6') + modifier(self.stats['DEX']) + self.level * 2
            dmg = int(dmg * (1 + _skill_pct / 100))
            return True, f"{self.name} strikes from the shadows! BACKSTAB! 🗡️", dmg
        elif skill == 'Smoke Bomb':
            return True, f"{self.name} throws a smoke bomb! Party evasion UP!", 0
        elif skill == 'Steal':
            gold = random.randint(5, 25) * self.level
            return True, f"{self.name} steals {gold} gold!", 0
        elif skill == 'Heal':
            heal_amt = roll('2d8') + modifier(self.stats['WIS']) + self.level
            heal_amt = int(heal_amt * (1 + _heal_pct / 100))
            if target and target.alive:
                target.heal(heal_amt)
            return True, f"{self.name} channels divine light! Heals {heal_amt} HP! ✨", 0
        elif skill == 'Smite':
            dmg = roll('2d8') + modifier(self.stats['WIS']) + self.level
            dmg = int(dmg * (1 + _smite_pct / 100 + _skill_pct / 100))
            return True, f"{self.name} calls down DIVINE SMITE! ⚡", dmg
        elif skill == 'Bless':
            if allies:
                for a in allies:
                    if a.alive:
                        a.stats['STR'] += 1
                        a.stats['DEX'] += 1
            return True, f"{self.name} blesses the party! Stats UP! 🙏", 0
        elif skill == 'Arrow Rain':
            dmg = roll('2d6') + modifier(self.stats['DEX']) + self.level
            dmg = int(dmg * (1 + _skill_pct / 100))
            return True, f"{self.name} rains arrows from above! 🏹", dmg
        elif skill == 'Trap':
            dmg = roll('1d8') + modifier(self.stats['DEX'])
            dmg = int(dmg * (1 + _skill_pct / 100))
            return True, f"{self.name} sets a cunning trap! 🪤", dmg
        elif skill == "Nature's Blessing":
            heal_amt = roll('1d8') + modifier(self.stats['WIS'])
            if allies:
                for a in allies:
                    if a.alive:
                        a.heal(heal_amt)
            return True, f"{self.name} calls upon nature! Party heals {heal_amt}! 🌿", 0
        return False, "Skill failed!", 0


class Enemy(Entity):
    TYPES = {
        'slime': {'hp': 8, 'ac': 8, 'atk': '1d4', 'xp': 15, 'gold': (2, 8),
                  'palette': [(60, 180, 60), (80, 200, 80), (40, 140, 40)]},
        'kobold': {'hp': 10, 'ac': 10, 'atk': '1d4+1', 'xp': 20, 'gold': (3, 10),
                   'palette': [(150, 100, 55), (140, 90, 50), (130, 85, 45)]},
        'bat_swarm': {'hp': 10, 'ac': 12, 'atk': '1d4', 'xp': 18, 'gold': (1, 5),
                      'palette': [(50, 35, 60), (40, 30, 50), (60, 40, 70)]},
        'goblin': {'hp': 12, 'ac': 11, 'atk': '1d6', 'xp': 25, 'gold': (5, 15),
                   'palette': [(80, 150, 50), (100, 70, 30), (60, 40, 20)]},
        'zombie': {'hp': 16, 'ac': 9, 'atk': '1d6+1', 'xp': 30, 'gold': (2, 8),
                   'palette': [(90, 110, 70), (80, 70, 50), (60, 50, 35)]},
        'spider': {'hp': 14, 'ac': 12, 'atk': '1d6', 'xp': 28, 'gold': (3, 10),
                   'palette': [(50, 30, 20), (60, 40, 25), (40, 25, 15)]},
        'skeleton': {'hp': 18, 'ac': 12, 'atk': '1d8', 'xp': 40, 'gold': (3, 12),
                     'palette': [(220, 210, 190), (180, 170, 150), (140, 130, 110)]},
        'mimic': {'hp': 25, 'ac': 13, 'atk': '1d8+2', 'xp': 55, 'gold': (20, 50),
                  'palette': [(130, 80, 25), (140, 90, 30), (100, 60, 15)]},
        'orc': {'hp': 30, 'ac': 13, 'atk': '1d10', 'xp': 60, 'gold': (10, 30),
                'palette': [(60, 110, 45), (80, 50, 20), (40, 30, 15)]},
        'wraith': {'hp': 28, 'ac': 14, 'atk': '1d8+2', 'xp': 65, 'gold': (8, 25),
                   'palette': [(80, 60, 120), (60, 45, 100), (100, 80, 140)]},
        'troll': {'hp': 45, 'ac': 13, 'atk': '1d10+2', 'xp': 80, 'gold': (15, 40),
                  'palette': [(50, 80, 40), (55, 85, 45), (45, 75, 38)]},
        'minotaur': {'hp': 50, 'ac': 14, 'atk': '2d6+2', 'xp': 90, 'gold': (20, 50),
                     'palette': [(120, 70, 40), (130, 80, 45), (100, 60, 30)]},
        'gelatinous_cube': {'hp': 40, 'ac': 8, 'atk': '1d10+3', 'xp': 70, 'gold': (15, 60),
                            'palette': [(100, 200, 100), (120, 220, 120), (80, 180, 80)]},
        'mind_flayer': {'hp': 55, 'ac': 15, 'atk': '2d6+3', 'xp': 120, 'gold': (30, 80),
                        'palette': [(140, 100, 160), (130, 90, 150), (120, 80, 140)]},
        'dark_knight': {'hp': 60, 'ac': 16, 'atk': '2d6+4', 'xp': 130, 'gold': (25, 70),
                        'palette': [(30, 25, 35), (40, 30, 45), (50, 40, 55)]},
        'dragon': {'hp': 80, 'ac': 16, 'atk': '2d8', 'xp': 200, 'gold': (50, 150),
                   'palette': [(180, 40, 40), (140, 30, 30), (100, 20, 20)]},
        'boss_lich': {'hp': 120, 'ac': 17, 'atk': '2d10', 'xp': 500, 'gold': (100, 300),
                      'palette': [(40, 10, 60), (60, 20, 80), (30, 5, 50)]},
        # Classic DnD Vecna - undead god of secrets
        'vecna': {'hp': 150, 'ac': 18, 'atk': '2d10+4', 'xp': 700, 'gold': (150, 400),
                  'palette': [(50, 20, 70), (80, 30, 100), (30, 10, 50)]},
        # Classic DnD Demogorgon - two-headed demon prince
        'demogorgon': {'hp': 180, 'ac': 19, 'atk': '2d12+5', 'xp': 800, 'gold': (200, 500),
                       'palette': [(40, 80, 40), (60, 100, 50), (30, 60, 30)]},
        # Stranger Things Vecna (001/Henry Creel) — THE HARDEST BOSS
        'st_vecna': {'hp': 350, 'ac': 22, 'atk': '3d12+8', 'xp': 2000, 'gold': (500, 1000),
                     'palette': [(80, 40, 40), (60, 25, 30), (100, 50, 45)]},
        # Stranger Things Demogorgon (faceless predator)
        'st_demogorgon': {'hp': 130, 'ac': 16, 'atk': '2d8+4', 'xp': 600, 'gold': (100, 300),
                          'palette': [(90, 60, 50), (70, 45, 35), (110, 70, 55)]},
        # Stranger Things Mind Flayer (shadow spider entity)
        'st_mind_flayer': {'hp': 160, 'ac': 18, 'atk': '2d10+4', 'xp': 750, 'gold': (150, 400),
                           'palette': [(30, 18, 40), (25, 15, 30), (50, 25, 60)]},
        # === SECRET ST ENEMIES (only spawn on Upside Down floors) ===
        # Demodogs — pack hunters from the Upside Down
        'demodog': {'hp': 45, 'ac': 14, 'atk': '1d10+3', 'xp': 80, 'gold': (15, 40),
                    'palette': [(100, 65, 50), (80, 50, 35), (120, 75, 55)]},
        # Demobats — swarms that attack from above
        'demobat': {'hp': 25, 'ac': 15, 'atk': '1d8+2', 'xp': 50, 'gold': (10, 25),
                    'palette': [(70, 40, 50), (55, 30, 40), (85, 50, 60)]},
        # Flayed — possessed humans with super strength
        'flayed': {'hp': 55, 'ac': 13, 'atk': '2d6+3', 'xp': 90, 'gold': (20, 50),
                   'palette': [(160, 120, 100), (130, 90, 70), (100, 60, 45)]},
        # Shadow Tendril — living vine creature of the Upside Down
        'shadow_tendril': {'hp': 35, 'ac': 12, 'atk': '1d8+4', 'xp': 60, 'gold': (10, 30),
                           'palette': [(25, 15, 35), (20, 10, 25), (40, 25, 50)]},
        # The Creel Phantom — ghostly echo of Vecna's past victims
        'creel_phantom': {'hp': 70, 'ac': 16, 'atk': '2d8+3', 'xp': 120, 'gold': (30, 70),
                          'palette': [(150, 150, 170), (120, 120, 145), (180, 180, 200)]},
    }

    def __init__(self, enemy_type, level=1):
        data = self.TYPES.get(enemy_type, self.TYPES['slime'])
        super().__init__(
            name=enemy_type.replace('_', ' ').title(),
            char_class=enemy_type,
            level=level,
            is_enemy=True
        )
        self.enemy_type = enemy_type
        self.max_hp = data['hp'] + (level - 1) * (data['hp'] // 3)
        self.hp = self.max_hp
        self.ac = data['ac'] + (level - 1)
        self.attack_dice = data['atk']
        self.xp_reward = data['xp'] + (level - 1) * 10
        self.gold_range = data['gold']
        self.palette = data['palette']
        self.sprite = None
        self.stunned = 0

    def ai_action(self, targets):
        """Enemy picks an action."""
        if self.stunned > 0:
            self.stunned -= 1
            return None, "is stunned!", 0
        alive_targets = [t for t in targets if t.alive]
        if not alive_targets:
            return None, "has no targets", 0

        # Special abilities for powerful enemies
        if self.enemy_type == 'vecna' and random.random() < 0.4:
            # Vecna's necrotic grasp - targets random party member
            target = random.choice(alive_targets)
            dmg = roll('3d6') + 4
            return target, f"unleashes Necrotic Grasp on {target.name}! {dmg} necrotic damage!", dmg

        if self.enemy_type == 'st_vecna' and random.random() < 0.50:
            # ST Vecna has multiple devastating abilities
            ability = random.choice(['psychic', 'curse', 'telekinesis', 'mind_lair'])
            if ability == 'psychic':
                target = max(alive_targets, key=lambda t: t.max_hp)
                dmg = roll('3d10') + 6
                return target, f"invades {target.name}'s mind! PSYCHIC ANNIHILATION for {dmg} damage!", dmg
            elif ability == 'curse':
                target = random.choice(alive_targets)
                dmg = roll('2d12') + 5
                target.stunned = getattr(target, 'stunned', 0)
                return target, f"curses {target.name} with Vecna's Wrath! {dmg} necrotic damage!", dmg
            elif ability == 'telekinesis':
                target = min(alive_targets, key=lambda t: t.hp)
                dmg = roll('3d8') + 4
                return target, f"HURLS {target.name} with telekinetic force! {dmg} damage!", dmg
            else:  # mind_lair
                target = random.choice(alive_targets)
                dmg = roll('4d6') + 8
                return target, f"traps {target.name} in a Mind Lair! {dmg} psychic damage! \"You cannot escape me.\"", dmg

        if self.enemy_type == 'demogorgon' and random.random() < 0.3:
            # DnD Demogorgon's twin bite - attacks two targets
            target = random.choice(alive_targets)
            dmg = roll('2d10') + 5
            return target, f"bites with BOTH heads at {target.name}! {dmg} damage!", dmg

        if self.enemy_type == 'st_demogorgon' and random.random() < 0.35:
            # ST Demogorgon's petal-mouth lunge
            target = min(alive_targets, key=lambda t: t.hp)
            dmg = roll('2d8') + 3
            return target, f"opens its petal-mouth and lunges at {target.name}! {dmg} damage!", dmg

        if self.enemy_type == 'st_mind_flayer' and random.random() < 0.4:
            # ST Mind Flayer's shadow storm - hits random target with massive psychic shadow damage
            target = random.choice(alive_targets)
            dmg = roll('3d8') + 4
            return target, f"summons a SHADOW STORM engulfing {target.name}! {dmg} shadow damage!", dmg

        # Secret ST enemy abilities
        if self.enemy_type == 'demodog' and random.random() < 0.3:
            target = min(alive_targets, key=lambda t: t.hp)
            dmg = roll('2d6') + 3
            return target, f"PACK LUNGES at {target.name}! {dmg} damage!", dmg

        if self.enemy_type == 'demobat' and random.random() < 0.35:
            target = random.choice(alive_targets)
            dmg = roll('1d8') + 2
            return target, f"LATCHES onto {target.name}'s face! {dmg} damage!", dmg

        if self.enemy_type == 'flayed' and random.random() < 0.3:
            target = random.choice(alive_targets)
            dmg = roll('2d8') + 2
            return target, f"convulses and SLAMS {target.name}! {dmg} damage!", dmg

        if self.enemy_type == 'creel_phantom' and random.random() < 0.35:
            target = max(alive_targets, key=lambda t: t.max_hp)
            dmg = roll('2d8') + 4
            return target, f"whispers \"Tick tock...\" and strikes {target.name}! {dmg} psychic damage!", dmg

        # Default: Target lowest HP
        target = min(alive_targets, key=lambda t: t.hp)
        d20, attack_total = self.attack_roll()
        if attack_total >= target.ac:
            dmg = max(1, self.damage_roll())
            if d20 == 20:
                dmg *= 2  # CRIT
                return target, f"CRITICAL HIT on {target.name}! {dmg} damage!", dmg
            return target, f"hits {target.name} for {dmg} damage!", dmg
        return target, f"misses {target.name}!", 0


# ════════════════════════════════════════════════════════════
# ITEMS & LOOT
# ════════════════════════════════════════════════════════════
ITEM_TEMPLATES = {
    'health_potion': {'name': 'Health Potion', 'type': 'consumable', 'icon': '🧪', 'effect': 'heal', 'value': 20, 'price': 15, 'desc': 'Restores 2d8+4 HP'},
    'mana_potion': {'name': 'Mana Potion', 'type': 'consumable', 'icon': '💧', 'effect': 'mana', 'value': 15, 'price': 20, 'desc': 'Restores 2d6+3 MP'},
    'iron_sword': {'name': 'Iron Sword', 'type': 'weapon', 'icon': '⚔️', 'attack': '1d8+1', 'price': 50, 'desc': '+1 attack damage'},
    'steel_sword': {'name': 'Steel Sword', 'type': 'weapon', 'icon': '🗡️', 'attack': '1d10+2', 'price': 120, 'desc': '+2 attack damage'},
    'magic_staff': {'name': 'Arcane Staff', 'type': 'weapon', 'icon': '🪄', 'attack': '1d6+3', 'price': 100, 'desc': '+3 magic damage'},
    'leather_armor': {'name': 'Leather Armor', 'type': 'armor', 'icon': '🛡️', 'ac_bonus': 2, 'price': 40, 'desc': '+2 AC'},
    'chain_mail': {'name': 'Chain Mail', 'type': 'armor', 'icon': '⛓️', 'ac_bonus': 4, 'price': 100, 'desc': '+4 AC'},
    'ring_of_power': {'name': 'Ring of Power', 'type': 'accessory', 'icon': '💍', 'stat_bonus': {'STR': 2, 'INT': 2}, 'price': 200, 'desc': '+2 STR, +2 INT'},
    'amulet_of_life': {'name': 'Amulet of Life', 'type': 'accessory', 'icon': '📿', 'hp_bonus': 20, 'price': 150, 'desc': '+20 Max HP'},
    'scroll_fireball': {'name': 'Scroll of Fireball', 'type': 'consumable', 'icon': '📜', 'effect': 'fireball', 'value': 30, 'price': 60, 'desc': 'Deals 3d6 fire damage'},
    'revive_potion': {'name': 'Potion of Revive', 'type': 'consumable', 'icon': '💖', 'effect': 'revive', 'value': 0, 'price': 200, 'desc': 'Revives a fallen party member with 50% HP'},
    # Boss accessories
    'minotaur_horn': {'name': 'Minotaur Horn', 'type': 'accessory', 'icon': '🐂', 'stat_bonus': {'STR': 3}, 'hp_bonus': 10, 'price': 150, 'desc': '+3 STR, +10 Max HP'},
    'mind_crystal': {'name': 'Mind Crystal', 'type': 'accessory', 'icon': '🔮', 'stat_bonus': {'INT': 4, 'WIS': 2}, 'price': 250, 'desc': '+4 INT, +2 WIS'},
    'dark_sigil': {'name': 'Dark Sigil', 'type': 'accessory', 'icon': '⚜️', 'stat_bonus': {'STR': 2, 'DEX': 2}, 'ac_bonus': 1, 'price': 200, 'desc': '+2 STR, +2 DEX, +1 AC'},
    'dragon_scale': {'name': 'Dragon Scale', 'type': 'accessory', 'icon': '🐉', 'stat_bonus': {'CON': 4}, 'hp_bonus': 25, 'price': 350, 'desc': '+4 CON, +25 Max HP'},
    'lich_phylactery': {'name': 'Lich Phylactery', 'type': 'accessory', 'icon': '💀', 'stat_bonus': {'INT': 5}, 'hp_bonus': 15, 'price': 400, 'desc': '+5 INT, +15 Max HP'},
    'eye_of_vecna': {'name': 'Eye of Vecna', 'type': 'accessory', 'icon': '👁️', 'stat_bonus': {'INT': 6, 'WIS': 4}, 'price': 600, 'desc': '+6 INT, +4 WIS'},
    'demogorgon_fang': {'name': 'Demogorgon Fang', 'type': 'accessory', 'icon': '🦷', 'stat_bonus': {'STR': 5, 'CON': 3}, 'price': 650, 'desc': '+5 STR, +3 CON'},
    'shadow_heart': {'name': 'Shadow Heart', 'type': 'accessory', 'icon': '🖤', 'stat_bonus': {'INT': 4, 'DEX': 4}, 'hp_bonus': 20, 'price': 700, 'desc': '+4 INT, +4 DEX, +20 Max HP'},
    # ST-specific drops
    'eleven_bracelet': {'name': "Eleven's Bracelet", 'type': 'accessory', 'icon': '🔗', 'stat_bonus': {'INT': 8, 'WIS': 6}, 'hp_bonus': 30, 'price': 1200, 'desc': '+8 INT, +6 WIS, +30 Max HP — The best drop'},
    'upside_down_vine': {'name': 'Upside Down Vine', 'type': 'accessory', 'icon': '🌿', 'stat_bonus': {'CON': 4, 'DEX': 3}, 'hp_bonus': 15, 'price': 350, 'desc': '+4 CON, +3 DEX, +15 Max HP'},
    'demobat_wing': {'name': 'Demobat Wing', 'type': 'accessory', 'icon': '🦇', 'stat_bonus': {'DEX': 5}, 'ac_bonus': 2, 'price': 300, 'desc': '+5 DEX, +2 AC'},
    'flayed_essence': {'name': 'Flayed Essence', 'type': 'accessory', 'icon': '💉', 'stat_bonus': {'STR': 4, 'CON': 4}, 'price': 400, 'desc': '+4 STR, +4 CON'},
    'creel_locket': {'name': "Creel's Locket", 'type': 'accessory', 'icon': '🎵', 'stat_bonus': {'WIS': 6, 'CHA': 4}, 'hp_bonus': 10, 'price': 500, 'desc': '+6 WIS, +4 CHA, +10 Max HP — Running Up That Hill...'},
    'hawkins_lab_keycard': {'name': 'Hawkins Lab Keycard', 'type': 'accessory', 'icon': '🪪', 'stat_bonus': {'INT': 3, 'DEX': 3, 'WIS': 3}, 'price': 450, 'desc': '+3 INT, +3 DEX, +3 WIS'},
    'st_sword_of_kas': {'name': 'Sword of Kas', 'type': 'weapon', 'icon': '⚔️', 'attack': '3d8+6', 'stat_bonus': {'STR': 6}, 'price': 1500, 'desc': 'The legendary blade that can slay Vecna'},
}

def generate_loot(level, enemy_type='normal'):
    """Generate random loot appropriate for the player's level."""
    loot = []
    # Gold
    gold = random.randint(5, 15) * level
    if enemy_type in ('dragon', 'boss_lich', 'mind_flayer', 'vecna', 'demogorgon'):
        gold *= 5
    elif enemy_type in ('minotaur', 'dark_knight', 'troll', 'st_vecna', 'st_demogorgon', 'st_mind_flayer'):
        gold *= 3
    elif enemy_type == 'mimic':
        gold *= 4  # Mimics are treasure

    # Items (chance-based)
    roll_val = random.random()
    if roll_val < 0.45:
        loot.append(dict(ITEM_TEMPLATES['health_potion']))
    if roll_val < 0.25:
        loot.append(dict(ITEM_TEMPLATES['mana_potion']))
    if random.random() < 0.15:
        loot.append(dict(ITEM_TEMPLATES['scroll_fireball']))

    # Equipment drop chance (boosted for early game)
    equip_chance = 0.40 if level <= 2 else (0.25 + level * 0.03)
    if random.random() < equip_chance:
        equip_pool = ['iron_sword', 'leather_armor']
        if level >= 3:
            equip_pool.extend(['steel_sword', 'chain_mail', 'magic_staff'])
        if level >= 5:
            equip_pool.extend(['ring_of_power', 'amulet_of_life'])
        loot.append(dict(ITEM_TEMPLATES[random.choice(equip_pool)]))

    # Potion of Revive — 1 in 10 chance
    if random.random() < 0.10:
        loot.append(dict(ITEM_TEMPLATES['revive_potion']))

    # ST enemies drop special ST items
    ST_ENEMIES = {'st_vecna', 'st_demogorgon', 'st_mind_flayer', 'demodog', 'demobat', 'flayed', 'shadow_tendril', 'creel_phantom'}
    if enemy_type in ST_ENEMIES:
        st_drop_pool = ['hawkins_lab_keycard', 'upside_down_vine', 'demobat_wing', 'flayed_essence']
        if random.random() < 0.25:
            loot.append(dict(ITEM_TEMPLATES[random.choice(st_drop_pool)]))
        # Sword of Kas — ultra rare (5% from any ST enemy)
        if random.random() < 0.05:
            loot.append(dict(ITEM_TEMPLATES['st_sword_of_kas']))

    return gold, loot


# ════════════════════════════════════════════════════════════
# DUNGEON GENERATION
# ════════════════════════════════════════════════════════════
class TileType(Enum):
    VOID = 0
    FLOOR = 1
    WALL = 2
    DOOR = 3
    CHEST = 4
    STAIRS = 5
    WATER = 6
    LAVA = 7
    TRAP = 8
    GRASS = 9
    ST_PORTAL = 10

class DungeonGenerator:
    def __init__(self, width=40, height=30, floor_num=1):
        self.width = width
        self.height = height
        self.floor_num = floor_num
        self.tiles = [[TileType.VOID] * width for _ in range(height)]
        self.rooms = []
        self.spawn_point = (5, 5)
        self.enemy_spawns = []
        self.chest_positions = []
        self.stairs_pos = None
        self.st_portal_pos = None
        self.explored = [[False] * width for _ in range(height)]

    def generate(self):
        """Generate a dungeon with rooms and corridors."""
        num_rooms = 6 + self.floor_num * 2
        max_attempts = 200

        for _ in range(max_attempts):
            if len(self.rooms) >= num_rooms:
                break
            rw = random.randint(4, 9)
            rh = random.randint(4, 7)
            rx = random.randint(1, self.width - rw - 1)
            ry = random.randint(1, self.height - rh - 1)

            # Check overlap
            overlap = False
            for (orx, ory, orw, orh) in self.rooms:
                if (rx - 1 < orx + orw and rx + rw + 1 > orx and
                    ry - 1 < ory + orh and ry + rh + 1 > ory):
                    overlap = True
                    break
            if overlap:
                continue

            # Carve room
            floor_type = TileType.FLOOR
            # Special rooms
            if random.random() < 0.15 and self.floor_num > 1:
                floor_type = TileType.GRASS  # overgrown room
            for yy in range(ry, ry + rh):
                for xx in range(rx, rx + rw):
                    self.tiles[yy][xx] = floor_type
            self.rooms.append((rx, ry, rw, rh))

        # Connect rooms with corridors
        for i in range(len(self.rooms) - 1):
            r1 = self.rooms[i]
            r2 = self.rooms[i + 1]
            x1 = r1[0] + r1[2] // 2
            y1 = r1[1] + r1[3] // 2
            x2 = r2[0] + r2[2] // 2
            y2 = r2[1] + r2[3] // 2

            # L-shaped corridor
            if random.random() < 0.5:
                self._carve_h_corridor(x1, x2, y1)
                self._carve_v_corridor(y1, y2, x2)
            else:
                self._carve_v_corridor(y1, y2, x1)
                self._carve_h_corridor(x1, x2, y2)

        # Place walls around all floor tiles
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x] == TileType.VOID:
                    # Check if adjacent to floor
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < self.height and 0 <= nx < self.width:
                            if self.tiles[ny][nx] in (TileType.FLOOR, TileType.GRASS, TileType.DOOR):
                                self.tiles[y][x] = TileType.WALL
                                break

        # Spawn point in first room
        if self.rooms:
            r = self.rooms[0]
            self.spawn_point = (r[0] + r[2] // 2, r[1] + r[3] // 2)

        # Stairs in last room
        if len(self.rooms) > 1:
            r = self.rooms[-1]
            sx, sy = r[0] + r[2] // 2, r[1] + r[3] // 2
            self.tiles[sy][sx] = TileType.STAIRS
            self.stairs_pos = (sx, sy)

        # Chests in corners of random rooms
        for room in self.rooms[1:-1]:
            if random.random() < 0.5:
                cx = room[0] + random.randint(1, room[2] - 2)
                cy = room[1] + random.randint(1, room[3] - 2)
                if self.tiles[cy][cx] == TileType.FLOOR:
                    self.tiles[cy][cx] = TileType.CHEST
                    self.chest_positions.append((cx, cy))

        # Enemy spawns in rooms (not first room)
        for room in self.rooms[1:]:
            num_enemies = random.randint(1, 2 + self.floor_num // 2)
            for _ in range(num_enemies):
                ex = room[0] + random.randint(1, room[2] - 2)
                ey = room[1] + random.randint(1, room[3] - 2)
                if self.tiles[ey][ex] in (TileType.FLOOR, TileType.GRASS):
                    self.enemy_spawns.append((ex, ey))

        # Water/lava features
        if self.floor_num >= 2 and len(self.rooms) > 3:
            feature_room = random.choice(self.rooms[1:-1])
            feature = TileType.WATER if self.floor_num < 4 else TileType.LAVA
            fcx = feature_room[0] + feature_room[2] // 2
            fcy = feature_room[1] + feature_room[3] // 2
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    ny, nx = fcy + dy, fcx + dx
                    if 0 <= ny < self.height and 0 <= nx < self.width:
                        if self.tiles[ny][nx] == TileType.FLOOR and random.random() < 0.6:
                            self.tiles[ny][nx] = feature

        # Traps
        for room in self.rooms[1:]:
            if random.random() < 0.3:
                tx = room[0] + random.randint(1, room[2] - 2)
                ty = room[1] + random.randint(1, room[3] - 2)
                if self.tiles[ty][tx] == TileType.FLOOR:
                    self.tiles[ty][tx] = TileType.TRAP

        # Stranger Things Portal — 30% chance on floors 3+, placed in a middle room
        self.st_portal_pos = None
        if self.floor_num >= 3 and random.random() < 0.30 and len(self.rooms) > 2:
            portal_room = random.choice(self.rooms[1:-1])
            px = portal_room[0] + portal_room[2] // 2
            py = portal_room[1] + portal_room[3] // 2
            if self.tiles[py][px] == TileType.FLOOR:
                self.tiles[py][px] = TileType.ST_PORTAL
                self.st_portal_pos = (px, py)

        return self

    def _carve_h_corridor(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= y < self.height and 0 <= x < self.width:
                if self.tiles[y][x] == TileType.VOID:
                    self.tiles[y][x] = TileType.FLOOR

    def _carve_v_corridor(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= y < self.height and 0 <= x < self.width:
                if self.tiles[y][x] == TileType.VOID:
                    self.tiles[y][x] = TileType.FLOOR

    def is_walkable(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x] in (TileType.FLOOR, TileType.DOOR, TileType.STAIRS, TileType.GRASS, TileType.TRAP, TileType.CHEST, TileType.LAVA, TileType.WATER, TileType.ST_PORTAL)
        return False

    def reveal_around(self, x, y, radius=6):
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if dx * dx + dy * dy <= radius * radius:
                        self.explored[ny][nx] = True


# ════════════════════════════════════════════════════════════
# AI COMPANION BRAIN
# ════════════════════════════════════════════════════════════
AI_NAMES = {
    'warrior': ['Ironheart', 'Thorin', 'Valeria', 'Bjorn', 'Gretchen'],
    'mage': ['Elara', 'Zephyr', 'Morgana', 'Aldric', 'Lyria'],
    'rogue': ['Shadow', 'Vex', 'Nyx', 'Kael', 'Whisper'],
    'cleric': ['Solara', 'Brother Cedric', 'Lumina', 'Theron', 'Grace'],
    'ranger': ['Hawkeye', 'Fern', 'Ashwood', 'Talon', 'Willow'],
}

AI_CHAT = {
    'brave': {
        'combat_start': ["Let's show them what we're made of!", "For glory!", "Stand your ground!"],
        'low_hp': ["I won't go down easily!", "Just a scratch!"],
        'victory': ["Another victory for the party!", "Who's next?!", "We are unstoppable!"],
        'idle': ["My blade hungers for battle.", "I sense danger ahead...", "Ready for anything!"],
        'heal': ["Thanks, I needed that!", "Back in the fight!"],
        'level_up': ["I grow STRONGER!", "Feel this power!"],
        'explore': ["What lurks in this dungeon?", "Stay sharp, friends.", "I'll take point."],
    },
    'cautious': {
        'combat_start': ["Careful, everyone...", "Let's approach this wisely.", "Watch the flanks!"],
        'low_hp': ["I could use some healing...", "Falling back!"],
        'victory': ["Phew, that was close!", "Let's not push our luck.", "Everyone okay?"],
        'idle': ["I have a bad feeling about this...", "Let's rest here a moment.", "Check your gear."],
        'heal': ["Much appreciated!", "Good timing!"],
        'level_up': ["Every bit of experience counts.", "Slowly but surely..."],
        'explore': ["Let me check for traps...", "Tread carefully here.", "I smell danger."],
    },
    'witty': {
        'combat_start': ["Time to party! 🎉", "Let's dance!", "I didn't sign up for this... oh wait."],
        'low_hp': ["Tis but a flesh wound!", "'I'm fine', the bleeding person said."],
        'victory': ["Loot first, questions later!", "All in a day's work!", "GG no re!"],
        'idle': ["So... nice dungeon. Very... damp.", "Anyone bring snacks?", "This torch is my best friend."],
        'heal': ["Like a spa day in a dungeon!", "Health potion > coffee!"],
        'level_up': ["Ding! Level up! 🎵", "*gains 2 brain cells*"],
        'explore': ["Plot twist incoming!", "According to my map... we're lost.", "Let me Instagram this dungeon."],
    },
    'wise': {
        'combat_start': ["Knowledge is our weapon.", "Study their patterns.", "Patience wins battles."],
        'low_hp': ["I must retreat to recover.", "My strength wanes..."],
        'victory': ["The light prevails.", "As the prophecy foretold.", "A hard-won battle."],
        'idle': ["The ancient texts spoke of this place.", "I sense magical energy here.", "Knowledge protects."],
        'heal': ["The divine guides your hand.", "Gratitude, friend."],
        'level_up': ["Wisdom grows with experience.", "Enlightenment approaches."],
        'explore': ["These runes tell a story...", "The architecture is ancient.", "I feel the dungeon's breath."],
    },
    'fierce': {
        'combat_start': ["RAAAGH!", "CRUSH THEM!", "Blood and steel!"],
        'low_hp': ["PAIN FUELS MY RAGE!", "I'LL TAKE YOU WITH ME!"],
        'victory': ["DOMINANT!", "THEY ARE NOTHING!", "SMASHED!"],
        'idle': ["*sharpens weapon aggressively*", "WHEN DO WE FIGHT?!", "I'm getting restless..."],
        'heal': ["BACK AT FULL POWER!", "NOW I'M ANGRY AND HEALED!"],
        'level_up': ["UNLIMITED POWER!", "FEEL MY WRATH GROW!"],
        'explore': ["I SMELL ENEMIES!", "BRING ME BATTLE!", "This dungeon fears US."],
    },
}


def ai_companion_say(entity, situation):
    """Get a context-aware AI companion chat line."""
    personality = entity.ai_personality
    lines = AI_CHAT.get(personality, AI_CHAT['brave'])
    pool = lines.get(situation, lines.get('idle', ['...']))
    return random.choice(pool)


# ════════════════════════════════════════════════════════════
# COMBAT SYSTEM
# ════════════════════════════════════════════════════════════
class CombatState:
    def __init__(self, party: List[Entity], enemies: List[Enemy]):
        self.party = party
        self.enemies = enemies
        self.turn_order: List[Entity] = []
        self.current_turn = 0
        self.log: List[Tuple[str, tuple]] = []
        self.phase = 'start'  # start, player_turn, ai_turn, enemy_turn, victory, defeat
        self.selected_action = None
        self.selected_skill = -1
        self.selected_target = -1
        self.round_num = 1
        self.anim_timer = 0
        self.shake_timer = 0
        self.shake_offset = (0, 0)

        # Roll initiative
        self._roll_initiative()

    def _roll_initiative(self):
        all_entities = [(e, random.randint(1, 20) + modifier(e.stats['DEX'])) for e in self.party + self.enemies if e.alive]
        all_entities.sort(key=lambda x: -x[1])
        self.turn_order = [e[0] for e in all_entities]
        self.add_log("⚔️ Combat begins! Rolling initiative...", C_GOLD)
        for e, init in all_entities:
            prefix = "🟢" if not e.is_enemy else "🔴"
            self.add_log(f"  {prefix} {e.name}: {init}", C_WHITE)
        self.current_turn = 0
        self._advance_to_next_alive()

    def add_log(self, msg, color=C_WHITE):
        self.log.append((msg, color))
        if len(self.log) > 50:
            self.log = self.log[-50:]

    def get_current(self):
        if self.current_turn < len(self.turn_order):
            return self.turn_order[self.current_turn]
        return None

    def _advance_to_next_alive(self):
        attempts = 0
        while attempts < len(self.turn_order) * 2:
            if self.current_turn >= len(self.turn_order):
                self.current_turn = 0
                self.round_num += 1
                self.add_log(f"\n═══ Round {self.round_num} ═══", C_GOLD)
            current = self.turn_order[self.current_turn]
            if current.alive:
                if current.is_enemy:
                    self.phase = 'enemy_turn'
                elif current.is_ai:
                    self.phase = 'ai_turn'
                else:
                    self.phase = 'player_turn'
                return
            self.current_turn += 1
            attempts += 1

    def next_turn(self):
        self.current_turn += 1
        self.selected_action = None
        self.selected_skill = -1
        self.selected_target = -1

        # Check victory/defeat
        if not any(e.alive for e in self.enemies):
            self.phase = 'victory'
            return
        if not any(e.alive for e in self.party):
            self.phase = 'defeat'
            return

        self._advance_to_next_alive()

    def do_attack(self, attacker, target):
        d20, attack_total = attacker.attack_roll()
        if d20 == 20:
            dmg = attacker.damage_roll() * 2
            target.take_damage(dmg)
            self.add_log(f"🎯 CRITICAL HIT! {attacker.name} → {target.name} for {dmg}!", C_GOLD)
            spawn_float_text(target.x * TILE_W + TILE_W // 2, target.y * TILE_H, f"CRIT! {dmg}", C_GOLD)
            spawn_particles(target.x * TILE_W + TILE_W // 2, target.y * TILE_H + 16, C_RED, 12, 3)
            self.shake_timer = 8
        elif d20 == 1:
            self.add_log(f"💨 Critical MISS! {attacker.name} fumbles!", (150, 150, 150))
            spawn_float_text(attacker.x * TILE_W + TILE_W // 2, attacker.y * TILE_H, "MISS!", (150, 150, 150))
        elif attack_total >= target.ac:
            dmg = max(1, attacker.damage_roll())
            target.take_damage(dmg)
            self.add_log(f"⚔️ {attacker.name} hits {target.name} for {dmg}! (d20: {d20}+{attack_total - d20}={attack_total} vs AC {target.ac})", C_WHITE)
            spawn_float_text(target.x * TILE_W + TILE_W // 2, target.y * TILE_H, f"-{dmg}", C_RED)
            spawn_particles(target.x * TILE_W + TILE_W // 2, target.y * TILE_H + 16, C_RED, 6, 2)
            self.shake_timer = 4
        else:
            self.add_log(f"🛡️ {attacker.name} misses {target.name}. (d20: {d20}+{attack_total - d20}={attack_total} vs AC {target.ac})", (150, 150, 150))
            spawn_float_text(target.x * TILE_W + TILE_W // 2, target.y * TILE_H, "MISS", (150, 150, 150))

        if not target.alive:
            self.add_log(f"💀 {target.name} has been defeated!", C_RED)

    def do_ai_turn(self):
        """AI companion takes their turn automatically."""
        current = self.get_current()
        if not current or not current.alive:
            self.next_turn()
            return

        alive_enemies = [e for e in self.enemies if e.alive]
        alive_party = [p for p in self.party if p.alive]

        # AI Decision making
        # Healers prioritize healing hurt allies
        if current.char_class == 'cleric':
            hurt_allies = [a for a in alive_party if a.hp < a.max_hp * 0.5]
            if hurt_allies and current.mp >= 3:
                target = min(hurt_allies, key=lambda a: a.hp / a.max_hp)
                success, msg, _ = current.use_skill(0, target, alive_party)  # Heal
                if success:
                    self.add_log(f"✨ {msg}", C_GREEN)
                    spawn_float_text(target.x * TILE_W + TILE_W // 2, target.y * TILE_H, f"+HP", C_GREEN)
                    spawn_particles(target.x * TILE_W + TILE_W // 2, target.y * TILE_H + 16, C_GREEN, 8, 2, 20, 'heal')
                    line = ai_companion_say(current, 'heal')
                    self.add_log(f"  💬 {current.name}: \"{line}\"", (150, 200, 255))
                    self.next_turn()
                    return

        # Use skills if MP available (30% chance)
        if current.mp >= 3 and random.random() < 0.35 and alive_enemies:
            skill_idx = random.randint(0, min(len(current.skills) - 1, 1))
            target = random.choice(alive_enemies)
            success, msg, dmg = current.use_skill(skill_idx, target, alive_party)
            if success:
                self.add_log(f"💫 {msg}", C_PURPLE)
                if dmg > 0 and target:
                    target.take_damage(dmg)
                    spawn_float_text(target.x * TILE_W + TILE_W // 2, target.y * TILE_H, f"-{dmg}", C_PURPLE)
                    spawn_particles(target.x * TILE_W + TILE_W // 2, target.y * TILE_H + 16, C_PURPLE, 8, 2)
                    if not target.alive:
                        self.add_log(f"💀 {target.name} defeated!", C_RED)
                self.next_turn()
                return

        # Default: basic attack on random enemy
        if alive_enemies:
            target = random.choice(alive_enemies)
            self.do_attack(current, target)
            # Occasionally chat
            if random.random() < 0.25:
                line = ai_companion_say(current, 'combat_start')
                self.add_log(f"  💬 {current.name}: \"{line}\"", (150, 200, 255))

        self.next_turn()

    def do_enemy_turn(self):
        """Enemy takes their turn."""
        current = self.get_current()
        if not current or not current.alive:
            self.next_turn()
            return

        alive_party = [p for p in self.party if p.alive]
        target, msg, dmg = current.ai_action(alive_party)
        if target and dmg > 0:
            target.take_damage(dmg)
            self.add_log(f"🔴 {current.name} {msg}", C_RED)
            spawn_float_text(target.x * TILE_W + TILE_W // 2, target.y * TILE_H, f"-{dmg}", C_RED)
            spawn_particles(target.x * TILE_W + TILE_W // 2, target.y * TILE_H + 16, C_RED, 6)
            self.shake_timer = 4
            if not target.alive:
                self.add_log(f"💀 {target.name} has fallen!", (255, 100, 100))
                # AI react
                for companion in self.party:
                    if companion.is_ai and companion.alive and random.random() < 0.5:
                        line = ai_companion_say(companion, 'low_hp')
                        self.add_log(f"  💬 {companion.name}: \"{line}\"", (150, 200, 255))
        elif target:
            self.add_log(f"🔵 {current.name} {msg}", (150, 150, 150))
            spawn_float_text(target.x * TILE_W + TILE_W // 2, target.y * TILE_H, "MISS", (150, 150, 150))
        else:
            self.add_log(f"⏸️ {current.name} {msg}", (100, 100, 100))

        self.next_turn()


# ════════════════════════════════════════════════════════════
# GAME STATE MANAGER
# ════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════
# SKILL TREES (per class)
# ════════════════════════════════════════════════════════════
SKILL_TREES = {
    'warrior': [
        {'id': 'fortitude',    'name': 'Fortitude',      'icon': '❤️',  'desc': '+10% Max HP per rank',          'max_rank': 3, 'row': 0, 'col': 1, 'requires': []},
        {'id': 'iron_will',    'name': 'Iron Will',      'icon': '🛡️',  'desc': '+1 AC per rank',                'max_rank': 3, 'row': 1, 'col': 0, 'requires': ['fortitude']},
        {'id': 'berserker',    'name': 'Berserker',      'icon': '🔥',  'desc': '+15% weapon damage per rank',   'max_rank': 3, 'row': 1, 'col': 2, 'requires': ['fortitude']},
        {'id': 'cleave',       'name': 'Cleave',         'icon': '⚔️',  'desc': '+20% skill power per rank',     'max_rank': 3, 'row': 2, 'col': 0, 'requires': ['iron_will']},
        {'id': 'titans_grip',  'name': "Titan's Grip",   'icon': '💪',  'desc': '+2 STR per rank',               'max_rank': 3, 'row': 2, 'col': 2, 'requires': ['berserker']},
        {'id': 'warlord',      'name': 'Warlord',        'icon': '👑',  'desc': '+3 all stats per rank',         'max_rank': 2, 'row': 3, 'col': 1, 'requires': ['cleave', 'titans_grip']},
    ],
    'mage': [
        {'id': 'arcane_mind',  'name': 'Arcane Mind',    'icon': '🧠',  'desc': '+20% Max MP per rank',          'max_rank': 3, 'row': 0, 'col': 1, 'requires': []},
        {'id': 'spell_power',  'name': 'Spell Power',    'icon': '✨',  'desc': '+15% magic damage per rank',    'max_rank': 3, 'row': 1, 'col': 0, 'requires': ['arcane_mind']},
        {'id': 'quick_cast',   'name': 'Quick Cast',     'icon': '⚡',  'desc': '-1 MP cost per rank',           'max_rank': 3, 'row': 1, 'col': 2, 'requires': ['arcane_mind']},
        {'id': 'elem_focus',   'name': 'Elemental Focus','icon': '🌀',  'desc': '+20% skill power per rank',     'max_rank': 3, 'row': 2, 'col': 0, 'requires': ['spell_power']},
        {'id': 'int_mastery',  'name': 'INT Mastery',    'icon': '📚',  'desc': '+2 INT per rank',               'max_rank': 3, 'row': 2, 'col': 2, 'requires': ['quick_cast']},
        {'id': 'archmage',     'name': 'Archmage',       'icon': '🌟',  'desc': '+3 all stats per rank',         'max_rank': 2, 'row': 3, 'col': 1, 'requires': ['elem_focus', 'int_mastery']},
    ],
    'rogue': [
        {'id': 'shadow_step',  'name': 'Shadow Step',    'icon': '👤',  'desc': '+2 DEX per rank',               'max_rank': 3, 'row': 0, 'col': 1, 'requires': []},
        {'id': 'lethal_edge',  'name': 'Lethal Edge',    'icon': '🗡️',  'desc': '+15% crit damage per rank',     'max_rank': 3, 'row': 1, 'col': 0, 'requires': ['shadow_step']},
        {'id': 'evasion',      'name': 'Evasion',        'icon': '💨',  'desc': '+2 AC per rank',                'max_rank': 3, 'row': 1, 'col': 2, 'requires': ['shadow_step']},
        {'id': 'poison_tips',  'name': 'Poison Tips',    'icon': '☠️',  'desc': '+10% damage per rank',          'max_rank': 3, 'row': 2, 'col': 0, 'requires': ['lethal_edge']},
        {'id': 'nimble',       'name': 'Nimble Fingers', 'icon': '🪙',  'desc': '+20% gold found per rank',      'max_rank': 3, 'row': 2, 'col': 2, 'requires': ['evasion']},
        {'id': 'assassin',     'name': 'Assassin',       'icon': '🥷',  'desc': '+3 all stats per rank',         'max_rank': 2, 'row': 3, 'col': 1, 'requires': ['poison_tips', 'nimble']},
    ],
    'cleric': [
        {'id': 'divine_grace', 'name': 'Divine Grace',   'icon': '🙏',  'desc': '+25% heal power per rank',      'max_rank': 3, 'row': 0, 'col': 1, 'requires': []},
        {'id': 'holy_shield',  'name': 'Holy Shield',    'icon': '🛡️',  'desc': '+2 AC per rank',                'max_rank': 3, 'row': 1, 'col': 0, 'requires': ['divine_grace']},
        {'id': 'blessed_hp',   'name': 'Blessed Vitality','icon': '💛', 'desc': '+15% Max HP per rank',          'max_rank': 3, 'row': 1, 'col': 2, 'requires': ['divine_grace']},
        {'id': 'smite_power',  'name': 'Smite Power',    'icon': '⚡',  'desc': '+15% smite damage per rank',    'max_rank': 3, 'row': 2, 'col': 0, 'requires': ['holy_shield']},
        {'id': 'wis_mastery',  'name': 'WIS Mastery',    'icon': '📿',  'desc': '+2 WIS per rank',               'max_rank': 3, 'row': 2, 'col': 2, 'requires': ['blessed_hp']},
        {'id': 'high_priest',  'name': 'High Priest',    'icon': '✝️',  'desc': '+3 all stats per rank',         'max_rank': 2, 'row': 3, 'col': 1, 'requires': ['smite_power', 'wis_mastery']},
    ],
    'ranger': [
        {'id': 'eagle_eye',    'name': 'Eagle Eye',      'icon': '🦅',  'desc': '+2 attack bonus per rank',      'max_rank': 3, 'row': 0, 'col': 1, 'requires': []},
        {'id': 'swift_quiver', 'name': 'Swift Quiver',   'icon': '🏹',  'desc': '+10% damage per rank',          'max_rank': 3, 'row': 1, 'col': 0, 'requires': ['eagle_eye']},
        {'id': 'natures_ward', 'name': "Nature's Ward",  'icon': '🌿',  'desc': '+10% Max HP per rank',          'max_rank': 3, 'row': 1, 'col': 2, 'requires': ['eagle_eye']},
        {'id': 'beast_lore',   'name': 'Beast Lore',     'icon': '🐾',  'desc': '+15% XP gained per rank',       'max_rank': 3, 'row': 2, 'col': 0, 'requires': ['swift_quiver']},
        {'id': 'dex_mastery',  'name': 'DEX Mastery',    'icon': '🎯',  'desc': '+2 DEX per rank',               'max_rank': 3, 'row': 2, 'col': 2, 'requires': ['natures_ward']},
        {'id': 'beastmaster',  'name': 'Beastmaster',    'icon': '🐺',  'desc': '+3 all stats per rank',         'max_rank': 2, 'row': 3, 'col': 1, 'requires': ['beast_lore', 'dex_mastery']},
    ],
}

# Mapping: node_id → {bonus_type: value_per_rank}
SKILL_NODE_BONUSES = {
    # Warrior
    'fortitude':    {'max_hp_pct': 10},
    'iron_will':    {'ac': 1},
    'berserker':    {'damage_pct': 15},
    'cleave':       {'skill_power_pct': 20},
    'titans_grip':  {'str': 2},
    'warlord':      {'all_stats': 3},
    # Mage
    'arcane_mind':  {'max_mp_pct': 20},
    'spell_power':  {'magic_damage_pct': 15},
    'quick_cast':   {'mp_cost_reduction': 1},
    'elem_focus':   {'skill_power_pct': 20},
    'int_mastery':  {'int': 2},
    'archmage':     {'all_stats': 3},
    # Rogue
    'shadow_step':  {'dex': 2},
    'lethal_edge':  {'crit_damage_pct': 15},
    'evasion':      {'ac': 2},
    'poison_tips':  {'damage_pct': 10},
    'nimble':       {'gold_pct': 20},
    'assassin':     {'all_stats': 3},
    # Cleric
    'divine_grace': {'heal_power_pct': 25},
    'holy_shield':  {'ac': 2},
    'blessed_hp':   {'max_hp_pct': 15},
    'smite_power':  {'smite_damage_pct': 15},
    'wis_mastery':  {'wis': 2},
    'high_priest':  {'all_stats': 3},
    # Ranger
    'eagle_eye':    {'attack_bonus': 2},
    'swift_quiver': {'damage_pct': 10},
    'natures_ward': {'max_hp_pct': 10},
    'beast_lore':   {'xp_pct': 15},
    'dex_mastery':  {'dex': 2},
    'beastmaster':  {'all_stats': 3},
}

def get_skill_tree_bonus(entity, bonus_type):
    """Get total bonus from skill tree upgrades for a given bonus_type."""
    if not hasattr(entity, 'skill_tree'):
        return 0
    total = 0
    for node_id, rank in entity.skill_tree.items():
        if rank <= 0:
            continue
        bonuses = SKILL_NODE_BONUSES.get(node_id, {})
        if bonus_type in bonuses:
            total += bonuses[bonus_type] * rank
        # 'all_stats' contributes to individual stat queries
        if bonus_type in ('str', 'dex', 'int', 'wis', 'con', 'cha') and 'all_stats' in bonuses:
            total += bonuses['all_stats'] * rank
    return total

def apply_skill_tree_stats(entity):
    """Recalculate HP/MP/AC with skill tree bonuses. Call after loading or spending points."""
    hp_pct = get_skill_tree_bonus(entity, 'max_hp_pct')
    mp_pct = get_skill_tree_bonus(entity, 'max_mp_pct')
    ac_bonus = get_skill_tree_bonus(entity, 'ac')

    # Recalculate base HP/MP from class + level
    cls_data = DnDClass.CLASSES.get(entity.char_class, DnDClass.CLASSES['warrior'])
    base_hp = cls_data['hp_die'] + modifier(entity.stats['CON']) + (entity.level - 1) * (cls_data['hp_die'] // 2 + modifier(entity.stats['CON']))
    base_mp = 10 + modifier(entity.stats['INT']) * 2 + modifier(entity.stats['WIS'])
    base_mp += (entity.level - 1) * (2 + modifier(entity.stats['INT']))

    # Apply % bonuses
    entity.max_hp = max(1, int(base_hp * (1 + hp_pct / 100)))
    entity.max_mp = max(1, int(base_mp * (1 + mp_pct / 100)))
    entity.hp = min(entity.hp, entity.max_hp)
    entity.mp = min(entity.mp, entity.max_mp)

    # AC: base 10 + DEX + class armor + skill tree
    base_ac = 10 + modifier(entity.stats['DEX'])
    if entity.char_class == 'warrior': base_ac += 4
    elif entity.char_class == 'rogue': base_ac += 2
    elif entity.char_class == 'cleric': base_ac += 3
    elif entity.char_class == 'ranger': base_ac += 1
    # Re-add equipment AC
    if entity.equipment.get('armor') and 'ac_bonus' in entity.equipment['armor']:
        base_ac += entity.equipment['armor']['ac_bonus']
    entity.ac = base_ac + ac_bonus

def can_upgrade_node(entity, node_id):
    """Check if an entity can upgrade a skill tree node."""
    tree = SKILL_TREES.get(entity.char_class, [])
    node = next((n for n in tree if n['id'] == node_id), None)
    if not node:
        return False
    current_rank = entity.skill_tree.get(node_id, 0)
    if current_rank >= node['max_rank']:
        return False
    if entity.skill_points <= 0:
        return False
    # Check prerequisites
    for req_id in node['requires']:
        if entity.skill_tree.get(req_id, 0) <= 0:
            return False
    return True

def upgrade_node(entity, node_id):
    """Spend a skill point to upgrade a node. Returns True on success."""
    if not can_upgrade_node(entity, node_id):
        return False
    entity.skill_tree[node_id] = entity.skill_tree.get(node_id, 0) + 1
    entity.skill_points -= 1
    # Apply stat bonuses immediately
    bonuses = SKILL_NODE_BONUSES.get(node_id, {})
    for stat in ('str', 'dex', 'int', 'wis', 'con', 'cha'):
        if stat in bonuses:
            entity.stats[stat.upper()] += bonuses[stat]
        if 'all_stats' in bonuses:
            entity.stats[stat.upper()] += bonuses['all_stats']
    apply_skill_tree_stats(entity)
    return True


class GameState(Enum):
    TITLE = 'title'
    CLASS_SELECT = 'class_select'
    EXPLORING = 'exploring'
    COMBAT = 'combat'
    INVENTORY = 'inventory'
    GAME_OVER = 'game_over'
    VICTORY = 'victory'
    LEVEL_UP = 'level_up'
    SHOP = 'shop'
    SKILL_TREE = 'skill_tree'


class Game:
    def __init__(self):
        self.state = GameState.TITLE
        self.player: Optional[Entity] = None
        self.party: List[Entity] = []
        self.dungeon: Optional[DungeonGenerator] = None
        self.enemies: List[Enemy] = []
        self.combat: Optional[CombatState] = None
        self.floor_num = 1
        self.gold = 50
        self.camera_x = 0
        self.camera_y = 0
        self.target_cam_x = 0
        self.target_cam_y = 0
        self.message_log: List[Tuple[str, tuple]] = []
        self.selected_class = 0
        self.minimap_open = False
        self.opened_chests = set()
        self.game_time = 0
        self.ai_chat_timer = 0
        self.ai_chat_bubble = None
        self.ai_chat_display_time = 0
        self.anim_tick = 0
        self.title_anim = 0
        self.move_cooldown = 0  # Frame counter for held-key movement
        self.skill_tree_member_idx = 0  # Which party member's tree to view
        self.skill_tree_selected = 0  # Currently highlighted node index
        self._title_opts = []  # Title screen options
        self.in_upside_down = False  # Whether current floor is an Upside Down version
        self.st_portal_announced = False  # Whether AI has reacted to portal
        self.inv_scroll = 0  # Inventory scroll offset
        self.inv_sort_mode = 0  # 0=type, 1=name, 2=rarity
        self.inv_selected = -1  # Currently selected item index (-1 = none)

        # Fonts
        self.font_lg = pygame.font.SysFont('Segoe UI', 32, bold=True)
        self.font_md = pygame.font.SysFont('Segoe UI', 18)
        self.font_sm = pygame.font.SysFont('Segoe UI', 14)
        self.font_xs = pygame.font.SysFont('Segoe UI', 11)
        self.font_title = pygame.font.SysFont('Georgia', 52, bold=True)
        self.font_subtitle = pygame.font.SysFont('Georgia', 20)

        # Pre-generate textures
        self.iso_tiles = {}
        for name in ['stone_floor', 'stone_wall', 'grass', 'water', 'lava', 'wood_floor', 'dark_stone']:
            self.iso_tiles[name] = make_iso_tile(name, wall=(name == 'stone_wall'))
        self.iso_tiles['chest'] = make_texture('chest', 20, 20)
        self.iso_tiles['stairs'] = make_texture('stairs', 20, 20)
        self.iso_tiles['st_portal'] = make_texture('st_portal', 20, 20)
        self.iso_tiles['upside_down_floor'] = make_iso_tile('upside_down_floor')

    def add_message(self, msg, color=C_WHITE):
        self.message_log.append((msg, color))
        if len(self.message_log) > 100:
            self.message_log = self.message_log[-100:]

    def new_game(self, char_class):
        """Start a new game with the selected class, carrying over saved levels."""
        # Load saved level/XP if a save exists (carry over progression)
        saved_level = 1
        saved_xp = 0
        saved_xp_to_level = 100
        saved_skill_points = 0
        saved_skill_tree = {}
        saved_companions = []
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, 'r') as f:
                    old_data = json.load(f)
                p = old_data.get('player', {})
                saved_level = p.get('level', 1)
                saved_xp = p.get('xp', 0)
                saved_xp_to_level = p.get('xp_to_level', 100)
                saved_skill_points = p.get('skill_points', 0)
                saved_skill_tree = p.get('skill_tree', {})
                saved_companions = old_data.get('companions', [])
            except Exception:
                pass

        self.player = Entity("Hero", char_class)
        self.party = [self.player]
        self.gold = 50

        # Apply carried-over levels to player
        if saved_level > 1:
            self.player.level = saved_level
            self.player.xp = saved_xp
            self.player.xp_to_level = saved_xp_to_level
            self.player.skill_points = saved_skill_points
            self.player.skill_tree = saved_skill_tree
            # Scale HP/MP for level
            cls_data = DnDClass.CLASSES.get(char_class, DnDClass.CLASSES['warrior'])
            for _ in range(saved_level - 1):
                hp_gain = cls_data['hp_die'] // 2 + 1 + modifier(self.player.stats['CON'])
                self.player.max_hp += max(1, hp_gain)
                self.player.max_mp += 2 + modifier(self.player.stats['INT'])
            self.player.hp = self.player.max_hp
            self.player.mp = self.player.max_mp

        # Starter gear based on class
        starter_gear = {
            'warrior': ['iron_sword', 'leather_armor'],
            'mage': ['magic_staff'],
            'rogue': ['iron_sword'],
            'cleric': ['leather_armor'],
            'ranger': ['iron_sword', 'leather_armor'],
        }
        for item_key in starter_gear.get(char_class, []):
            item = dict(ITEM_TEMPLATES[item_key])
            self.player.inventory.append(item)
            # Auto-equip starter gear
            if item['type'] == 'weapon':
                self.player.equipment['weapon'] = item
            elif item['type'] == 'armor':
                self.player.equipment['armor'] = item

        # Give 2 starting health potions
        for _ in range(2):
            self.player.inventory.append(dict(ITEM_TEMPLATES['health_potion']))

        # Add AI companions (carry over saved levels)
        available_classes = [c for c in DnDClass.CLASSES.keys() if c != char_class]
        random.shuffle(available_classes)
        # Find max saved companion level to apply to new companions
        comp_level = max((c.get('level', 1) for c in saved_companions), default=1) if saved_companions else saved_level
        for i, cls in enumerate(available_classes[:2]):
            name = random.choice(AI_NAMES.get(cls, ['Companion']))
            companion = Entity(name, cls, is_ai=True)
            if comp_level > 1:
                companion.level = comp_level
                companion.xp = 0
                companion.xp_to_level = int(100 * (1.5 ** (comp_level - 1)))
                companion.skill_points = 2 * (comp_level - 1)
                cls_data = DnDClass.CLASSES.get(cls, DnDClass.CLASSES['warrior'])
                for _ in range(comp_level - 1):
                    hp_gain = cls_data['hp_die'] // 2 + 1 + modifier(companion.stats['CON'])
                    companion.max_hp += max(1, hp_gain)
                    companion.max_mp += 2 + modifier(companion.stats['INT'])
                companion.hp = companion.max_hp
                companion.mp = companion.max_mp
            self.party.append(companion)

        self.floor_num = 1
        self.generate_floor()
        self.state = GameState.EXPLORING
        self.add_message(f"⚔️ {self.player.name} the {char_class.title()} enters the dungeon!", C_GOLD)
        self.add_message(f"🤝 Joined by AI companions: {', '.join(c.name for c in self.party[1:])}", C_GREEN)
        for c in self.party[1:]:
            line = ai_companion_say(c, 'explore')
            self.add_message(f"  💬 {c.name}: \"{line}\"", (150, 200, 255))

        # Save baseline immediately so progress is never lost
        self.save_game()

    def generate_floor(self):
        """Generate a new dungeon floor."""
        self.dungeon = DungeonGenerator(40, 30, self.floor_num).generate()
        self.enemies = []
        self.opened_chests = set()
        self.st_portal_announced = False

        # Place player
        sx, sy = self.dungeon.spawn_point
        self.player.x = sx
        self.player.y = sy
        # Place companions near player (offset so they don't overlap)
        offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for i, companion in enumerate(self.party[1:]):
            ox, oy = offsets[i % len(offsets)]
            cx, cy = sx + ox, sy + oy
            if self.dungeon.is_walkable(cx, cy):
                companion.x = cx
                companion.y = cy
            else:
                companion.x = sx
                companion.y = sy
            companion.alive = True
            companion.hp = companion.max_hp

        # Spawn enemies
        if self.in_upside_down:
            # UPSIDE DOWN FLOOR — all ST and secret ST enemies!
            st_regular = ['demodog', 'demobat', 'flayed', 'shadow_tendril']
            st_bosses = ['st_demogorgon', 'st_mind_flayer', 'creel_phantom']
            boss_spawned = set()

            for ex, ey in self.dungeon.enemy_spawns:
                if st_bosses and random.random() < 0.10 and not boss_spawned:
                    etype = random.choice(st_bosses)
                    boss_spawned.add(etype)
                else:
                    etype = random.choice(st_regular)
                enemy = Enemy(etype, max(1, self.floor_num + random.randint(-1, 1)))
                enemy.x = ex
                enemy.y = ey
                self.enemies.append(enemy)

            # ST Vecna as boss on Upside Down floors (always!)
            if self.dungeon.rooms:
                boss_room = self.dungeon.rooms[-2] if len(self.dungeon.rooms) > 2 else self.dungeon.rooms[-1]
                boss = Enemy('st_vecna', self.floor_num + 3)
                boss.max_hp = int(boss.max_hp * 2.5)  # Even harder
                boss.hp = boss.max_hp
                boss.name = "💀 ST Vecna, The One"
                boss.x = boss_room[0] + boss_room[2] // 2
                boss.y = boss_room[1] + boss_room[3] // 2
                self.enemies.append(boss)

            # Exit back to normal on stairs (next floor will be normal)
            self.in_upside_down = False
        else:
            enemy_types_by_floor = {
                1: ['slime', 'kobold', 'bat_swarm'],
                2: ['goblin', 'kobold', 'spider'],
                3: ['goblin', 'zombie', 'skeleton'],
                4: ['skeleton', 'spider', 'mimic'],
                5: ['orc', 'wraith', 'skeleton'],
                6: ['orc', 'troll', 'gelatinous_cube'],
                7: ['troll', 'minotaur', 'wraith'],
                8: ['minotaur', 'mind_flayer', 'dark_knight'],
                9: ['mind_flayer', 'dark_knight', 'dragon', 'demogorgon'],
                10: ['dragon', 'dark_knight', 'vecna', 'demogorgon'],
            }
            available_types = enemy_types_by_floor.get(min(self.floor_num, 10), ['dragon', 'mind_flayer', 'dark_knight'])

            # Boss-tier enemies should only spawn once per floor (they're bosses, not regular mobs)
            BOSS_TIER = {'minotaur', 'mind_flayer', 'dark_knight', 'dragon', 'vecna', 'demogorgon',
                         'boss_lich', 'st_demogorgon', 'st_vecna', 'st_mind_flayer'}
            regular_types = [t for t in available_types if t not in BOSS_TIER]
            boss_types_in_pool = [t for t in available_types if t in BOSS_TIER]
            boss_spawned = set()

            for ex, ey in self.dungeon.enemy_spawns:
                if boss_types_in_pool and random.random() < 0.08 and not boss_spawned:
                    etype = random.choice(boss_types_in_pool)
                    boss_spawned.add(etype)
                elif regular_types:
                    etype = random.choice(regular_types)
                else:
                    etype = random.choice(available_types)
                enemy = Enemy(etype, max(1, self.floor_num + random.randint(-1, 1)))
                enemy.x = ex
                enemy.y = ey
                self.enemies.append(enemy)

            # Boss on every 3rd floor
            if self.floor_num % 3 == 0 and self.dungeon.rooms:
                boss_room = self.dungeon.rooms[-2] if len(self.dungeon.rooms) > 2 else self.dungeon.rooms[-1]
                boss_types = {
                    3: 'minotaur', 6: 'demogorgon', 9: 'vecna', 12: 'vecna',
                }
                boss_type = boss_types.get(self.floor_num, 'boss_lich')
                boss = Enemy(boss_type, self.floor_num + 2)
                boss.max_hp = int(boss.max_hp * 2.0)
                boss.hp = boss.max_hp
                boss.name = f"Boss {boss.name}"
                boss.x = boss_room[0] + boss_room[2] // 2
                boss.y = boss_room[1] + boss_room[3] // 2
                self.enemies.append(boss)

        # Mimic hidden in a random chest position
        if self.floor_num >= 3 and random.random() < 0.25:
            walkable_spots = [(x, y) for y in range(self.dungeon.height) for x in range(self.dungeon.width)
                              if self.dungeon.tiles[y][x] == TileType.FLOOR and (x, y) != self.dungeon.spawn_point]
            if walkable_spots:
                mx2, my2 = random.choice(walkable_spots)
                mimic = Enemy('mimic', self.floor_num)
                mimic.x = mx2
                mimic.y = my2
                self.enemies.append(mimic)

        self.dungeon.reveal_around(sx, sy)
        if self.in_upside_down:
            self.add_message(f"\n☠️ Floor {self.floor_num} — THE UPSIDE DOWN", (200, 50, 80))
            self.add_message(f"  Dark vines crawl across every surface. Ash drifts from the sky.", (150, 40, 60))
        else:
            self.add_message(f"\n📍 Floor {self.floor_num} — The dungeon deepens...", C_GOLD)

        # Snap camera to player immediately
        iso_x = (self.player.x - self.player.y) * TILE_W // 2
        iso_y = (self.player.x + self.player.y) * TILE_H // 2
        self.camera_x = iso_x - SCREEN_W // 2 + TILE_W // 2
        self.camera_y = iso_y - SCREEN_H // 2
        self.target_cam_x = self.camera_x
        self.target_cam_y = self.camera_y

    def try_move(self, dx, dy):
        """Attempt to move the player."""
        if self.state != GameState.EXPLORING:
            return
        nx = self.player.x + dx
        ny = self.player.y + dy

        if not self.dungeon.is_walkable(nx, ny):
            return

        self.player.x = nx
        self.player.y = ny
        if dx > 0:
            self.player.facing = 'right'
        elif dx < 0:
            self.player.facing = 'left'

        # Move companions to follow
        for i, companion in enumerate(self.party[1:]):
            if companion.alive:
                # Follow player with slight delay
                tdx = self.player.x - companion.x
                tdy = self.player.y - companion.y
                dist = abs(tdx) + abs(tdy)
                if dist > 2:
                    mx = 1 if tdx > 0 else (-1 if tdx < 0 else 0)
                    my = 1 if tdy > 0 else (-1 if tdy < 0 else 0)
                    nnx, nny = companion.x + mx, companion.y + my
                    if self.dungeon.is_walkable(nnx, nny):
                        companion.x = nnx
                        companion.y = nny

        self.dungeon.reveal_around(nx, ny)

        # Check tile interactions
        tile = self.dungeon.tiles[ny][nx]

        if tile == TileType.CHEST and (nx, ny) not in self.opened_chests:
            self.opened_chests.add((nx, ny))
            g, loot = generate_loot(self.player.level)
            self.gold += g
            self.add_message(f"📦 Opened chest! Found {g} gold!", C_GOLD)
            for item in loot:
                if not self.try_add_item(item):
                    break  # Inventory full
                self.add_message(f"  {item.get('icon', '📦')} {item['name']}", C_GREEN)
            spawn_particles(nx * TILE_W + TILE_W // 2, ny * TILE_H, C_GOLD, 15, 3, 40)

        elif tile == TileType.STAIRS:
            self.floor_num += 1
            self.save_game()
            self.generate_floor()
            return

        elif tile == TileType.TRAP:
            trap_dmg = roll('1d6') + self.floor_num
            self.player.take_damage(trap_dmg)
            self.dungeon.tiles[ny][nx] = TileType.FLOOR  # Disarm after triggering
            self.add_message(f"⚠️ Trap! {self.player.name} takes {trap_dmg} damage!", C_RED)
            spawn_particles(nx * TILE_W + TILE_W // 2, ny * TILE_H, (255, 150, 0), 10, 2, 25)
            if not self.player.alive:
                self.save_game()
                self.state = GameState.GAME_OVER
                return

        elif tile == TileType.LAVA:
            lava_dmg = roll('1d4') + self.floor_num
            self.player.take_damage(lava_dmg)
            self.add_message(f"🔥 Lava burns! {lava_dmg} damage!", C_RED)
            if not self.player.alive:
                self.save_game()
                self.state = GameState.GAME_OVER
                return

        elif tile == TileType.ST_PORTAL:
            # Enter the Upside Down version of the next floor!
            self.add_message(f"🌀 You step into the Stranger Things portal...", (200, 50, 80))
            self.add_message(f"  ☠️ The world twists and darkens. You enter the UPSIDE DOWN!", (180, 40, 60))
            self.floor_num += 1
            self.in_upside_down = True
            self.st_portal_announced = False
            self.save_game()
            self.generate_floor()
            return

        # Check enemy encounters
        for enemy in self.enemies:
            if enemy.alive and abs(enemy.x - nx) <= 1 and abs(enemy.y - ny) <= 1:
                self.start_combat([enemy])
                break

        # AI companion chat
        self.ai_chat_timer += 1

        # AI reacts to seeing an ST Portal nearby
        if not self.st_portal_announced and self.dungeon.st_portal_pos:
            ppx, ppy = self.dungeon.st_portal_pos
            if abs(nx - ppx) <= 3 and abs(ny - ppy) <= 3:
                self.st_portal_announced = True
                companions = [c for c in self.party[1:] if c.alive]
                if companions:
                    talker = random.choice(companions)
                    portal_lines = [
                        "What's this?! Some kind of... rift?",
                        "That's weird... I can feel something dark on the other side.",
                        "Whoa... is that a portal? This gives me chills.",
                        "Something's not right about that portal... I sense the Upside Down.",
                        "Do you see that? It looks like a tear in reality!",
                        "That's... definitely not normal. Should we go through?",
                    ]
                    line = random.choice(portal_lines)
                    self.ai_chat_bubble = (talker.name, line)
                    self.ai_chat_display_time = 300  # 5 seconds
                    self.add_message(f"💬 {talker.name}: \"{line}\"", (200, 100, 150))

        if self.ai_chat_timer >= 12:
            self.ai_chat_timer = 0
            companions = [c for c in self.party[1:] if c.alive]
            if companions and random.random() < 0.3:
                talker = random.choice(companions)
                # Special dialogue when in the Upside Down
                if self.in_upside_down:
                    ud_lines = [
                        "This place feels... wrong. Like the world is rotting.",
                        "I can barely breathe... the air is thick with ash.",
                        "Those vines... they're everywhere. Don't touch them!",
                        "We need to find a way out of this nightmare.",
                        "I hear something moving in the shadows...",
                        "The Upside Down... it's like a dark mirror of the dungeon.",
                        "Stay close. Creatures are lurking everywhere here.",
                    ]
                    line = random.choice(ud_lines)
                else:
                    line = ai_companion_say(talker, 'explore')
                self.ai_chat_bubble = (talker.name, line)
                self.ai_chat_display_time = 180  # 3 seconds at 60fps
                self.add_message(f"💬 {talker.name}: \"{line}\"", (150, 200, 255))

    def start_combat(self, triggered_enemies):
        """Start a combat encounter."""
        # Include nearby enemies too
        combat_enemies = list(triggered_enemies)
        for enemy in self.enemies:
            if enemy.alive and enemy not in combat_enemies:
                for te in triggered_enemies:
                    if abs(enemy.x - te.x) <= 3 and abs(enemy.y - te.y) <= 3:
                        combat_enemies.append(enemy)
                        break

        alive_party = [p for p in self.party if p.alive]
        self.combat = CombatState(alive_party, combat_enemies)
        self.state = GameState.COMBAT

        # AI companions react
        for companion in self.party[1:]:
            if companion.alive:
                line = ai_companion_say(companion, 'combat_start')
                self.combat.add_log(f"💬 {companion.name}: \"{line}\"", (150, 200, 255))

    def use_item(self, item_idx):
        """Use an item from inventory."""
        if item_idx >= len(self.player.inventory):
            return
        item = self.player.inventory[item_idx]

        if item['type'] == 'consumable':
            if item.get('effect') == 'heal':
                heal_amt = roll('2d8') + 4
                self.player.heal(heal_amt)
                self.add_message(f"🧪 Used {item['name']}! Healed {heal_amt} HP!", C_GREEN)
                spawn_particles(self.player.x * TILE_W + TILE_W // 2, self.player.y * TILE_H, C_GREEN, 10, 2, 25)
            elif item.get('effect') == 'mana':
                mana_amt = roll('2d6') + 3
                self.player.mp = min(self.player.max_mp, self.player.mp + mana_amt)
                self.add_message(f"💧 Used {item['name']}! Restored {mana_amt} MP!", C_BLUE)
            elif item.get('effect') == 'fireball':
                self.add_message(f"📜 Used {item['name']}! (Use in combat for 3d6 damage)", C_PURPLE)
            elif item.get('effect') == 'revive':
                dead_members = [m for m in self.party if not m.alive]
                if dead_members:
                    target = dead_members[0]
                    target.alive = True
                    target.hp = target.max_hp // 2
                    self.add_message(f"💖 {target.name} has been revived with {target.hp} HP!", C_GOLD)
                    spawn_particles(target.x * TILE_W + TILE_W // 2, target.y * TILE_H, C_GOLD, 20, 3, 40)
                else:
                    self.add_message(f"💖 No one needs reviving right now!", (150, 150, 150))
                    return  # Don't consume the potion
            self.player.inventory.pop(item_idx)

        elif item['type'] in ('weapon', 'armor', 'accessory'):
            slot = item['type'] if item['type'] != 'weapon' else 'weapon'
            old = self.player.equipment.get(slot)
            # Remove old item bonuses
            if old:
                if 'ac_bonus' in old:
                    self.player.ac -= old['ac_bonus']
                if 'stat_bonus' in old:
                    for stat, val in old['stat_bonus'].items():
                        self.player.stats[stat] -= val
                if 'hp_bonus' in old:
                    self.player.max_hp -= old['hp_bonus']
                    self.player.hp = min(self.player.hp, self.player.max_hp)
                self.player.inventory.append(old)
            self.player.equipment[slot] = item
            self.player.inventory.pop(item_idx)
            self.add_message(f"⚔️ Equipped {item['name']}!", C_GOLD)
            # Apply new item bonuses
            if 'ac_bonus' in item:
                self.player.ac += item['ac_bonus']
            if 'stat_bonus' in item:
                for stat, val in item['stat_bonus'].items():
                    self.player.stats[stat] += val
            if 'hp_bonus' in item:
                self.player.max_hp += item['hp_bonus']
                self.player.hp += item['hp_bonus']

    def can_pickup(self):
        """Check if player has room in inventory."""
        return len(self.player.inventory) < MAX_INVENTORY

    def try_add_item(self, item):
        """Try to add an item to inventory. Returns True if successful."""
        if self.can_pickup():
            self.player.inventory.append(item)
            return True
        else:
            self.add_message(f"🎒 Inventory full! ({MAX_INVENTORY}/{MAX_INVENTORY}) — Drop items to make room!", C_RED)
            return False

    def drop_item(self, item_idx):
        """Drop an item from inventory."""
        if 0 <= item_idx < len(self.player.inventory):
            item = self.player.inventory[item_idx]
            self.player.inventory.pop(item_idx)
            self.add_message(f"🗑️ Dropped {item.get('icon', '📦')} {item['name']}", (180, 120, 120))
            # Adjust scroll if needed
            self.inv_scroll = max(0, min(self.inv_scroll, max(0, len(self.player.inventory) - 14)))
            if self.inv_selected >= len(self.player.inventory):
                self.inv_selected = len(self.player.inventory) - 1

    def get_sorted_inventory(self):
        """Return inventory sorted by current sort mode. Returns list of (original_idx, item) tuples."""
        if not self.player or not self.player.inventory:
            return []
        TYPE_ORDER = {'weapon': 0, 'armor': 1, 'accessory': 2, 'consumable': 3}
        RARITY_ORDER = {'legendary': 0, 'epic': 1, 'rare': 2, 'uncommon': 3, 'common': 4}
        indexed = list(enumerate(self.player.inventory))
        if self.inv_sort_mode == 0:  # Sort by type
            indexed.sort(key=lambda x: (TYPE_ORDER.get(x[1].get('type', ''), 9), x[1].get('name', '')))
        elif self.inv_sort_mode == 1:  # Sort by name
            indexed.sort(key=lambda x: x[1].get('name', '').lower())
        elif self.inv_sort_mode == 2:  # Sort by rarity/value
            indexed.sort(key=lambda x: (RARITY_ORDER.get(x[1].get('rarity', 'common'), 4), x[1].get('name', '')))
        return indexed

    SORT_MODE_NAMES = ['Type', 'Name', 'Rarity']

    def update(self):
        self.anim_tick += 1
        self.title_anim += 1
        self.game_time += 1

        # Held-key movement for smooth exploring
        if self.state == GameState.EXPLORING and self.player:
            if self.move_cooldown > 0:
                self.move_cooldown -= 1
            else:
                keys = pygame.key.get_pressed()
                moved = False
                if keys[pygame.K_w] or keys[pygame.K_UP]:
                    self.try_move(0, -1)
                    moved = True
                elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
                    self.try_move(0, 1)
                    moved = True
                elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
                    self.try_move(-1, 0)
                    moved = True
                elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                    self.try_move(1, 0)
                    moved = True
                if moved:
                    self.move_cooldown = 8  # ~133ms delay between moves at 60fps

        # Update camera
        if self.state == GameState.EXPLORING and self.player:
            iso_x = (self.player.x - self.player.y) * TILE_W // 2
            iso_y = (self.player.x + self.player.y) * TILE_H // 2
            self.target_cam_x = iso_x - SCREEN_W // 2 + TILE_W // 2
            self.target_cam_y = iso_y - SCREEN_H // 2
            self.camera_x += (self.target_cam_x - self.camera_x) * 0.25
            self.camera_y += (self.target_cam_y - self.camera_y) * 0.25

        update_particles()
        update_float_texts()

        # AI chat bubble timer
        if self.ai_chat_display_time > 0:
            self.ai_chat_display_time -= 1
            if self.ai_chat_display_time <= 0:
                self.ai_chat_bubble = None

        # Combat auto-advance
        if self.state == GameState.COMBAT and self.combat:
            if self.combat.shake_timer > 0:
                self.combat.shake_timer -= 1
                self.combat.shake_offset = (random.randint(-3, 3), random.randint(-3, 3))
            else:
                self.combat.shake_offset = (0, 0)

            if self.combat.anim_timer > 0:
                self.combat.anim_timer -= 1
            elif self.combat.phase == 'enemy_turn':
                self.combat.anim_timer = 20
                self.combat.do_enemy_turn()
            elif self.combat.phase == 'ai_turn':
                self.combat.anim_timer = 25
                self.combat.do_ai_turn()
            elif self.combat.phase == 'victory':
                self._handle_victory()
            elif self.combat.phase == 'defeat':
                self.save_game()
                self.state = GameState.GAME_OVER

    def _handle_victory(self):
        """Handle combat victory: XP, loot, etc."""
        total_xp = sum(e.xp_reward for e in self.combat.enemies)
        total_gold = sum(random.randint(*e.gold_range) for e in self.combat.enemies)
        # Apply gold bonus from skill tree
        gold_pct = get_skill_tree_bonus(self.player, 'gold_pct')
        total_gold = int(total_gold * (1 + gold_pct / 100))
        self.gold += total_gold
        self.add_message(f"\n🏆 Victory! Earned {total_xp} XP and {total_gold} gold!", C_GOLD)

        # Remove defeated enemies
        for e in self.combat.enemies:
            if e in self.enemies:
                self.enemies.remove(e)

        # Distribute XP (all party members get XP, even dead ones)
        xp_share = total_xp // max(1, len(self.party))
        for member in self.party:
            leveled = member.gain_xp(xp_share)
            if leveled:
                self.add_message(f"🎉 {member.name} leveled up to {member.level}! (+2 skill points)", C_GOLD)
                if member.is_ai:
                    line = ai_companion_say(member, 'level_up')
                    self.add_message(f"  💬 {member.name}: \"{line}\"", (150, 200, 255))
                spawn_particles(member.x * TILE_W + TILE_W // 2, member.y * TILE_H, C_GOLD, 20, 3, 40)

        # Boss rewards: bonus levels + guaranteed accessory
        BOSS_REWARDS = {
            'minotaur':       {'levels': 2, 'accessory': 'minotaur_horn'},
            'mind_flayer':    {'levels': 3, 'accessory': 'mind_crystal'},
            'dark_knight':    {'levels': 3, 'accessory': 'dark_sigil'},
            'dragon':         {'levels': 5, 'accessory': 'dragon_scale'},
            'boss_lich':      {'levels': 5, 'accessory': 'lich_phylactery'},
            'vecna':          {'levels': 7, 'accessory': 'eye_of_vecna'},
            'demogorgon':     {'levels': 7, 'accessory': 'demogorgon_fang'},
            'st_vecna':       {'levels': 10, 'accessory': 'eleven_bracelet'},
            'st_demogorgon':  {'levels': 5, 'accessory': 'upside_down_vine'},
            'st_mind_flayer': {'levels': 8, 'accessory': 'shadow_heart'},
            # Secret ST enemies
            'demodog':        {'levels': 1, 'accessory': 'flayed_essence'},
            'demobat':        {'levels': 1, 'accessory': 'demobat_wing'},
            'creel_phantom':  {'levels': 2, 'accessory': 'creel_locket'},
        }
        for enemy in self.combat.enemies:
            reward = BOSS_REWARDS.get(enemy.enemy_type)
            if reward:
                bonus_lvls = reward['levels']
                acc_key = reward['accessory']
                acc_item = dict(ITEM_TEMPLATES[acc_key])
                self.try_add_item(acc_item)
                self.add_message(f"🏅 BOSS DEFEATED! +{bonus_lvls} bonus levels!", (255, 215, 0))
                self.add_message(f"  {acc_item['icon']} Boss drop: {acc_item['name']}!", (255, 215, 0))
                # Grant bonus levels to all party members
                for member in self.party:
                    for _ in range(bonus_lvls):
                        member.gain_xp(member.xp_to_level - member.xp)  # instantly level up
                    self.add_message(f"  ⬆️ {member.name} → Level {member.level}!", C_GOLD)
                spawn_particles(self.player.x * TILE_W + TILE_W // 2, self.player.y * TILE_H, (255, 215, 0), 30, 5, 60)

        # Loot drops
        for enemy in self.combat.enemies:
            _, loot = generate_loot(self.player.level, enemy.enemy_type)
            for item in loot:
                if self.try_add_item(item):
                    self.add_message(f"  {item.get('icon', '📦')} Found: {item['name']}", C_GREEN)

        # Auto-revive: if a revive potion was obtained and someone is dead, auto-use it
        dead_members = [m for m in self.party if not m.alive]
        if dead_members:
            revive_idx = None
            for i, item in enumerate(self.player.inventory):
                if item.get('effect') == 'revive':
                    revive_idx = i
                    break
            if revive_idx is not None:
                target = dead_members[0]
                target.alive = True
                target.hp = target.max_hp // 2
                self.player.inventory.pop(revive_idx)
                self.add_message(f"💖 Potion of Revive auto-used! {target.name} is back with {target.hp} HP!", C_GOLD)
                spawn_particles(target.x * TILE_W + TILE_W // 2, target.y * TILE_H, (255, 100, 200), 20, 3, 40)

        # AI victory chat
        for companion in self.party[1:]:
            if companion.alive and random.random() < 0.5:
                line = ai_companion_say(companion, 'victory')
                self.add_message(f"💬 {companion.name}: \"{line}\"", (150, 200, 255))

        # Heal party slightly after combat
        for member in self.party:
            if member.alive:
                member.heal(member.max_hp // 10)
                member.mp = min(member.max_mp, member.mp + 3)

        # Auto-save progress
        self.save_game()

        self.combat = None
        self.state = GameState.EXPLORING

    def save_game(self):
        """Save player progress to disk."""
        if not self.player:
            return
        try:
            def serialize_entity(e):
                return {
                    'name': e.name,
                    'char_class': e.char_class,
                    'level': e.level,
                    'xp': e.xp,
                    'xp_to_level': e.xp_to_level,
                    'hp': e.hp,
                    'max_hp': e.max_hp,
                    'mp': e.mp,
                    'max_mp': e.max_mp,
                    'ac': e.ac,
                    'stats': dict(e.stats),
                    'skill_points': e.skill_points,
                    'skill_tree': dict(e.skill_tree),
                    'inventory': list(e.inventory),
                    'equipment': {k: (dict(v) if v else None) for k, v in e.equipment.items()},
                    'skills': list(e.skills),
                    'attack_dice': e.attack_dice,
                    'is_ai': e.is_ai,
                    'alive': e.alive,
                    'ai_personality': getattr(e, 'ai_personality', 'brave'),
                }

            data = {
                'version': 2,
                'player': serialize_entity(self.player),
                'companions': [serialize_entity(c) for c in self.party[1:]],
                'gold': self.gold,
                'floor_num': self.floor_num,
                'in_upside_down': self.in_upside_down,
            }
            with open(SAVE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.add_message(f"⚠️ Save failed: {e}", C_RED)

    def load_game(self):
        """Load saved progress and start on a fresh floor with saved stats."""
        if not os.path.exists(SAVE_FILE):
            return False
        try:
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)

            def deserialize_entity(d, is_ai=False):
                ent = Entity(d['name'], d['char_class'], level=d.get('level', 1), is_ai=is_ai)
                ent.xp = d.get('xp', 0)
                ent.xp_to_level = d.get('xp_to_level', 100)
                ent.stats = d.get('stats', ent.stats)
                ent.max_hp = d.get('max_hp', ent.max_hp)
                ent.hp = d.get('hp', ent.max_hp)
                ent.max_mp = d.get('max_mp', ent.max_mp)
                ent.mp = d.get('mp', ent.max_mp)
                ent.ac = d.get('ac', ent.ac)
                ent.skill_points = d.get('skill_points', 0)
                ent.skill_tree = d.get('skill_tree', {})
                ent.inventory = d.get('inventory', [])
                ent.equipment = {k: (dict(v) if v else None) for k, v in d.get('equipment', {}).items()}
                ent.skills = d.get('skills', ent.skills)
                ent.attack_dice = d.get('attack_dice', ent.attack_dice)
                ent.alive = d.get('alive', True)
                ent.ai_personality = d.get('ai_personality', 'brave')
                ent.level = d.get('level', 1)
                return ent

            self.player = deserialize_entity(data['player'], is_ai=False)
            self.party = [self.player]
            for cd in data.get('companions', []):
                companion = deserialize_entity(cd, is_ai=True)
                self.party.append(companion)

            self.gold = data.get('gold', 50)
            self.floor_num = data.get('floor_num', 1)
            self.in_upside_down = data.get('in_upside_down', False)

            # Revive all party members to full HP/MP (respawn after death)
            for member in self.party:
                member.alive = True
                member.hp = member.max_hp
                member.mp = member.max_mp

            # Generate a fresh floor with saved progress
            self.generate_floor()
            self.state = GameState.EXPLORING
            self.add_message(f"💾 Save loaded! {self.player.name} the {self.player.char_class.title()} — Level {self.player.level}", C_GOLD)
            self.add_message(f"📍 Floor {self.floor_num} — Continuing adventure...", C_GOLD)
            return True
        except Exception as e:
            self.add_message(f"⚠️ Load failed: {e}", C_RED)
            return False

    # ════════════════════════════════════════════════════════
    # RENDERING
    # ════════════════════════════════════════════════════════
    def draw(self):
        screen.fill(C_DARK)

        if self.state == GameState.TITLE:
            self.draw_title()
        elif self.state == GameState.CLASS_SELECT:
            self.draw_class_select()
        elif self.state == GameState.EXPLORING:
            self.draw_exploring()
        elif self.state == GameState.COMBAT:
            self.draw_combat()
        elif self.state == GameState.INVENTORY:
            self.draw_inventory()
        elif self.state == GameState.SKILL_TREE:
            self.draw_skill_tree()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()

        pygame.display.flip()

    def draw_title(self):
        # Animated background
        for i in range(60):
            x = (i * 97 + self.title_anim) % (SCREEN_W + 40) - 20
            y = (i * 67 + self.title_anim // 2) % (SCREEN_H + 40) - 20
            size = 2 + int(math.sin(self.title_anim * 0.02 + i) * 2)
            alpha = 30 + int(math.sin(self.title_anim * 0.03 + i * 0.7) * 20)
            col = (100 + i % 50, 60 + i % 40, 150 + i % 50)
            pygame.draw.circle(screen, col, (int(x), int(y)), max(1, size))

        # Title
        title_y = 150 + int(math.sin(self.title_anim * 0.03) * 8)
        # Shadow
        t = self.font_title.render("Realms of Shadow", True, (30, 10, 50))
        screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2 + 3, title_y + 3))
        # Main
        t = self.font_title.render("Realms of Shadow", True, C_GOLD)
        screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, title_y))

        # Subtitle
        sub = self.font_subtitle.render("A 2.5D DnD RPG Adventure with AI Companions", True, (180, 160, 200))
        screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, title_y + 65))

        # Decorative line
        pygame.draw.line(screen, C_GOLD, (SCREEN_W // 2 - 200, title_y + 100), (SCREEN_W // 2 + 200, title_y + 100), 2)

        # Menu options
        pulse = int(math.sin(self.title_anim * 0.06) * 20 + 235)
        has_save = os.path.exists(SAVE_FILE)
        opts = []
        if has_save:
            opts.append(("💾  Continue", (100, pulse, 100)))
        opts.append(("⚔️  New Adventure", (pulse, pulse - 20, 100)))
        opts.append(("📖  How to Play", (150, 180, 200)))
        opts.append(("🚪  Quit", (180, 150, 150)))
        self._title_opts = opts  # Store for click handling
        for i, (text, col) in enumerate(opts):
            y = 340 + i * 50
            t = self.font_md.render(text, True, col)
            screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, y))
            # Hover hint
            mx, my = pygame.mouse.get_pos()
            if SCREEN_W // 2 - 120 < mx < SCREEN_W // 2 + 120 and y - 5 < my < y + 30:
                pygame.draw.rect(screen, C_GOLD, (SCREEN_W // 2 - 125, y - 3, 250, 32), 1, border_radius=6)

        # Version
        v = self.font_xs.render("v2.0 — Skill Trees • Save/Load • Revive Potions • AI Party", True, (80, 70, 100))
        screen.blit(v, (SCREEN_W // 2 - v.get_width() // 2, SCREEN_H - 40))

        # Animated torches on sides
        for side in (-1, 1):
            tx = SCREEN_W // 2 + side * 280
            ty = title_y + 30
            for p in range(8):
                fx = tx + random.randint(-3, 3)
                fy = ty - p * 3 + random.randint(-2, 2)
                fc = (255, 200 - p * 20, 50 - p * 5)
                pygame.draw.circle(screen, fc, (fx, fy), max(1, 4 - p // 2))

    def draw_class_select(self):
        # Background
        screen.fill(C_DARK)

        t = self.font_lg.render("Choose Your Class", True, C_GOLD)
        screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, 30))

        classes = list(DnDClass.CLASSES.keys())
        card_w = 210
        card_h = 340
        total_w = len(classes) * (card_w + 15) - 15
        start_x = (SCREEN_W - total_w) // 2

        mx, my = pygame.mouse.get_pos()

        for i, cls_name in enumerate(classes):
            cls = DnDClass.CLASSES[cls_name]
            x = start_x + i * (card_w + 15)
            y = 90

            is_selected = i == self.selected_class
            is_hovered = x <= mx <= x + card_w and y <= my <= y + card_h

            # Card background
            bg = C_DARK2 if not is_selected else (40, 35, 55)
            border = C_GOLD if is_selected else (C_PANEL_BORDER if not is_hovered else (120, 100, 160))
            pygame.draw.rect(screen, bg, (x, y, card_w, card_h), border_radius=10)
            pygame.draw.rect(screen, border, (x, y, card_w, card_h), 2, border_radius=10)

            # Glow effect for selected
            if is_selected:
                glow = pygame.Surface((card_w + 8, card_h + 8), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*C_GOLD, 30), (0, 0, card_w + 8, card_h + 8), border_radius=12)
                screen.blit(glow, (x - 4, y - 4))

            # Character sprite preview
            sprite = make_character_sprite(cls_name, cls['palette'], 32, 42)
            scaled = pygame.transform.scale(sprite, (64, 84))
            screen.blit(scaled, (x + card_w // 2 - 32, y + 15))

            # Class name
            name_t = self.font_md.render(cls_name.upper(), True, C_GOLD if is_selected else C_WHITE)
            screen.blit(name_t, (x + card_w // 2 - name_t.get_width() // 2, y + 105))

            # Description
            desc_t = self.font_xs.render(cls['desc'], True, (160, 155, 170))
            screen.blit(desc_t, (x + card_w // 2 - desc_t.get_width() // 2, y + 128))

            # Stats
            stats_y = y + 155
            info = [
                f"HP Die: d{cls['hp_die']}",
                f"Primary: {cls['primary']}",
            ]
            for si, line in enumerate(info):
                st = self.font_sm.render(line, True, (180, 175, 190))
                screen.blit(st, (x + 15, stats_y + si * 18))

            # Skills
            sk_y = stats_y + 50
            self.font_sm.render("Skills:", True, C_GOLD)
            sk_label = self.font_sm.render("Skills:", True, C_GOLD)
            screen.blit(sk_label, (x + 15, sk_y))
            for si, skill in enumerate(cls['skills']):
                sk_t = self.font_xs.render(f"• {skill}", True, (150, 180, 220))
                screen.blit(sk_t, (x + 20, sk_y + 18 + si * 16))

        # Instructions
        inst = self.font_md.render("Click a class or press 1-5 to select, ENTER to start", True, (130, 120, 150))
        screen.blit(inst, (SCREEN_W // 2 - inst.get_width() // 2, SCREEN_H - 60))

        # AI companions preview
        info2 = self.font_sm.render("🤝 Two AI companions will join you with complementary classes!", True, (150, 200, 250))
        screen.blit(info2, (SCREEN_W // 2 - info2.get_width() // 2, SCREEN_H - 85))

    def draw_exploring(self):
        if not self.dungeon or not self.player:
            return

        # Draw isometric dungeon
        cam_x = int(self.camera_x)
        cam_y = int(self.camera_y)

        # Determine visible tiles range
        for ty in range(self.dungeon.height):
            for tx in range(self.dungeon.width):
                if not self.dungeon.explored[ty][tx]:
                    continue

                tile = self.dungeon.tiles[ty][tx]
                if tile == TileType.VOID:
                    continue

                # Isometric transformation
                iso_x = (tx - ty) * TILE_W // 2
                iso_y = (tx + ty) * TILE_H // 2
                sx = iso_x - cam_x
                sy = iso_y - cam_y

                # Frustum culling
                if sx < -TILE_W or sx > SCREEN_W + TILE_W or sy < -80 or sy > SCREEN_H + TILE_H:
                    continue

                # Distance-based fog of war
                dx = abs(tx - self.player.x)
                dy = abs(ty - self.player.y)
                dist = math.sqrt(dx * dx + dy * dy)
                in_sight = dist <= 8

                if tile == TileType.WALL:
                    surf = self.iso_tiles['stone_wall']
                elif tile == TileType.GRASS:
                    surf = self.iso_tiles['grass']
                elif tile == TileType.WATER:
                    surf = self.iso_tiles['water']
                elif tile == TileType.LAVA:
                    surf = self.iso_tiles['lava']
                elif tile == TileType.ST_PORTAL:
                    # Draw floor first, then portal effect
                    screen.blit(self.iso_tiles['stone_floor'], (sx, sy))
                    portal_surf = self.iso_tiles['st_portal']
                    screen.blit(portal_surf, (sx + TILE_W // 2 - 10, sy - 10))
                    # Pulsing crimson glow
                    glow = pygame.Surface((32, 32), pygame.SRCALPHA)
                    pulse_a = 50 + int(math.sin(self.anim_tick * 0.06) * 40)
                    pygame.draw.circle(glow, (200, 30, 60, pulse_a), (16, 16), 16)
                    screen.blit(glow, (sx + TILE_W // 2 - 16, sy - 16))
                    # Floating particles around portal
                    if random.random() < 0.3:
                        spawn_particles(sx + TILE_W // 2, sy, (200, 40, 60), 2, 1, 20)
                    continue
                elif tile == TileType.CHEST:
                    # Draw floor first, then chest
                    screen.blit(self.iso_tiles['stone_floor'], (sx, sy))
                    if (tx, ty) not in self.opened_chests:
                        chest_surf = self.iso_tiles['chest']
                        screen.blit(chest_surf, (sx + TILE_W // 2 - 10, sy - 8))
                    continue
                elif tile == TileType.STAIRS:
                    screen.blit(self.iso_tiles['stone_floor'], (sx, sy))
                    stairs_surf = self.iso_tiles['stairs']
                    screen.blit(stairs_surf, (sx + TILE_W // 2 - 10, sy - 8))
                    # Glow effect
                    glow = pygame.Surface((24, 24), pygame.SRCALPHA)
                    pulse_a = 60 + int(math.sin(self.anim_tick * 0.08) * 30)
                    pygame.draw.circle(glow, (255, 255, 100, pulse_a), (12, 12), 12)
                    screen.blit(glow, (sx + TILE_W // 2 - 12, sy - 12))
                    continue
                elif tile == TileType.TRAP:
                    # Hidden trap looks like floor unless you're close
                    surf = self.iso_tiles['stone_floor']
                    if dist <= 2:
                        # Show trap hint
                        trap_s = pygame.Surface((8, 8), pygame.SRCALPHA)
                        pygame.draw.rect(trap_s, (200, 50, 0, 100), (0, 0, 8, 8))
                        screen.blit(surf, (sx, sy))
                        screen.blit(trap_s, (sx + TILE_W // 2 - 4, sy + TILE_H // 2 - 4))
                        continue
                else:
                    # Use dark Upside Down floor texture when in the Upside Down
                    if self.in_upside_down:
                        surf = self.iso_tiles['upside_down_floor']
                    else:
                        surf = self.iso_tiles['stone_floor']

                # Apply fog
                if not in_sight:
                    fog_surf = surf.copy()
                    dark_overlay = pygame.Surface(fog_surf.get_size(), pygame.SRCALPHA)
                    dark_overlay.fill((0, 0, 0, 120))
                    fog_surf.blit(dark_overlay, (0, 0))
                    screen.blit(fog_surf, (sx, sy))
                else:
                    screen.blit(surf, (sx, sy))

        # Draw entities (sorted by y for proper overlap)
        all_entities = [(e, False) for e in self.enemies if e.alive]
        all_entities += [(e, True) for e in self.party if e.alive]
        all_entities.sort(key=lambda e: e[0].y)

        for entity, is_party in all_entities:
            iso_x = (entity.x - entity.y) * TILE_W // 2
            iso_y = (entity.x + entity.y) * TILE_H // 2
            sx = iso_x - cam_x + TILE_W // 2 - 12
            sy = iso_y - cam_y - 20

            # Only draw if explored
            if not (0 <= entity.x < self.dungeon.width and 0 <= entity.y < self.dungeon.height):
                continue
            if not self.dungeon.explored[entity.y][entity.x]:
                continue

            # Check if in player's sight
            dx = abs(entity.x - self.player.x)
            dy = abs(entity.y - self.player.y)
            if math.sqrt(dx * dx + dy * dy) > 8:
                continue

            sprite = entity.get_sprite()

            # Flash effect when taking damage
            if entity.flash_timer > 0:
                entity.flash_timer -= 1
                if entity.flash_timer % 3 == 0:
                    continue  # Blink

            # Player highlight indicator (glowing circle under feet)
            if entity == self.player:
                glow_surf = pygame.Surface((28, 14), pygame.SRCALPHA)
                glow_alpha = 120 + int(math.sin(self.anim_tick * 0.08) * 40)
                pygame.draw.ellipse(glow_surf, (255, 215, 0, glow_alpha), (0, 0, 28, 14))
                pygame.draw.ellipse(glow_surf, (255, 255, 150, min(255, glow_alpha + 40)), (4, 2, 20, 10))
                screen.blit(glow_surf, (sx - 2, sy + sprite.get_height() - 8))

            # Bobbing animation
            bob = int(math.sin(self.anim_tick * 0.1 + hash(entity.name)) * 2)
            sy += bob

            # Flip sprite based on facing
            draw_sprite = sprite
            if hasattr(entity, 'facing') and entity.facing == 'left':
                draw_sprite = pygame.transform.flip(sprite, True, False)

            screen.blit(draw_sprite, (sx, sy))

            # HP bar for enemies
            if entity.is_enemy:
                bar_w = 24
                bar_h = 3
                bar_x = sx
                bar_y = sy - 5
                hp_pct = entity.hp / entity.max_hp
                pygame.draw.rect(screen, C_HP_BG, (bar_x, bar_y, bar_w, bar_h))
                pygame.draw.rect(screen, C_RED if hp_pct < 0.3 else C_GREEN, (bar_x, bar_y, int(bar_w * hp_pct), bar_h))

            # Name label for party
            if is_party:
                name_col = C_GOLD if entity == self.player else (150, 200, 255)
                name_t = self.font_xs.render(entity.name, True, name_col)
                screen.blit(name_t, (sx + 12 - name_t.get_width() // 2, sy - 12))

        # Particles & float text
        draw_particles(screen, cam_x, cam_y)
        draw_float_texts(screen, cam_x, cam_y, self.font_sm)

        # UI Overlays
        self.draw_hud()
        self.draw_message_log()
        self.draw_minimap()

        # AI chat bubble
        if self.ai_chat_bubble and self.ai_chat_display_time > 0:
            self.draw_chat_bubble(*self.ai_chat_bubble)

    def draw_hud(self):
        """Draw the heads-up display with party info."""
        panel_h = 80
        panel = pygame.Surface((SCREEN_W, panel_h), pygame.SRCALPHA)
        panel.fill((*C_PANEL, 220))
        pygame.draw.line(panel, C_PANEL_BORDER, (0, 0), (SCREEN_W, 0), 2)
        screen.blit(panel, (0, SCREEN_H - panel_h))

        y = SCREEN_H - panel_h + 8
        bar_w = 120
        bar_h = 8

        for i, member in enumerate(self.party):
            x = 15 + i * 240

            # Name and level
            alive_col = C_WHITE if member.alive else (100, 60, 60)
            role_icon = {'warrior': '⚔️', 'mage': '🔮', 'rogue': '🗡️', 'cleric': '✨', 'ranger': '🏹'}.get(member.char_class, '👤')
            name_str = f"{role_icon} {member.name} Lv{member.level}"
            if member.is_ai:
                name_str += " (AI)"
            nt = self.font_sm.render(name_str, True, alive_col)
            screen.blit(nt, (x, y))

            if not member.alive:
                dead = self.font_xs.render("💀 DEAD", True, C_RED)
                screen.blit(dead, (x, y + 16))
                continue

            # HP bar
            hp_pct = member.hp / member.max_hp
            pygame.draw.rect(screen, C_HP_BG, (x, y + 18, bar_w, bar_h), border_radius=3)
            pygame.draw.rect(screen, C_HP_RED if hp_pct < 0.3 else C_GREEN, (x, y + 18, int(bar_w * hp_pct), bar_h), border_radius=3)
            hp_t = self.font_xs.render(f"HP {member.hp}/{member.max_hp}", True, C_WHITE)
            screen.blit(hp_t, (x + bar_w + 5, y + 14))

            # MP bar
            if member.max_mp > 0:
                mp_pct = member.mp / member.max_mp
                pygame.draw.rect(screen, C_MP_BG, (x, y + 29, bar_w, bar_h - 2), border_radius=3)
                pygame.draw.rect(screen, C_MP_BLUE, (x, y + 29, int(bar_w * mp_pct), bar_h - 2), border_radius=3)
                mp_t = self.font_xs.render(f"MP {member.mp}/{member.max_mp}", True, (150, 180, 255))
                screen.blit(mp_t, (x + bar_w + 5, y + 26))

            # XP bar
            xp_pct = member.xp / member.xp_to_level if member.xp_to_level > 0 else 0
            pygame.draw.rect(screen, C_XP_BG, (x, y + 40, bar_w, 4), border_radius=2)
            pygame.draw.rect(screen, C_XP_GOLD, (x, y + 40, int(bar_w * xp_pct), 4), border_radius=2)

        # Gold and floor
        gold_t = self.font_md.render(f"💰 {self.gold}   📍 Floor {self.floor_num}", True, C_GOLD)
        screen.blit(gold_t, (SCREEN_W - gold_t.get_width() - 15, SCREEN_H - 30))

        # Controls hint
        ctrl = self.font_xs.render("WASD:Move  I:Inventory  T:Skills  M:Map  1-3:Skills  ESC:Menu", True, (100, 90, 120))
        screen.blit(ctrl, (SCREEN_W - ctrl.get_width() - 15, SCREEN_H - 50))

        # Skill points notification
        total_sp = sum(m.skill_points for m in self.party)
        if total_sp > 0:
            sp_note = self.font_sm.render(f"🌟 {total_sp} skill point{'s' if total_sp != 1 else ''} available! (T)", True, C_GOLD)
            screen.blit(sp_note, (SCREEN_W - sp_note.get_width() - 15, SCREEN_H - 68))

    def draw_message_log(self):
        """Draw the scrolling message log."""
        log_x = 10
        log_y = 10
        log_w = 380
        log_h = 200

        panel = pygame.Surface((log_w, log_h), pygame.SRCALPHA)
        panel.fill((10, 8, 16, 160))
        pygame.draw.rect(panel, (60, 50, 80, 100), (0, 0, log_w, log_h), 1, border_radius=6)
        screen.blit(panel, (log_x, log_y))

        # Show last N messages
        visible = self.message_log[-10:]
        for i, (msg, color) in enumerate(visible):
            t = self.font_xs.render(msg[:60], True, color)
            screen.blit(t, (log_x + 8, log_y + 6 + i * 18))

    def draw_minimap(self):
        """Draw a minimap in the top-right corner."""
        if not self.dungeon:
            return
        mm_size = 4
        mm_w = self.dungeon.width * mm_size
        mm_h = self.dungeon.height * mm_size
        mm_x = SCREEN_W - mm_w - 15
        mm_y = 15

        panel = pygame.Surface((mm_w + 8, mm_h + 8), pygame.SRCALPHA)
        panel.fill((10, 8, 16, 180))
        pygame.draw.rect(panel, C_PANEL_BORDER, (0, 0, mm_w + 8, mm_h + 8), 1, border_radius=4)
        screen.blit(panel, (mm_x - 4, mm_y - 4))

        for ty in range(self.dungeon.height):
            for tx in range(self.dungeon.width):
                if not self.dungeon.explored[ty][tx]:
                    continue
                tile = self.dungeon.tiles[ty][tx]
                if tile == TileType.VOID:
                    continue
                px = mm_x + tx * mm_size
                py = mm_y + ty * mm_size
                if tile == TileType.WALL:
                    col = (60, 55, 70)
                elif tile == TileType.FLOOR:
                    col = (90, 85, 100)
                elif tile == TileType.GRASS:
                    col = (50, 100, 50)
                elif tile == TileType.WATER:
                    col = (30, 60, 150)
                elif tile == TileType.LAVA:
                    col = (200, 80, 20)
                elif tile == TileType.CHEST:
                    col = C_GOLD
                elif tile == TileType.STAIRS:
                    col = (200, 200, 255)
                elif tile == TileType.ST_PORTAL:
                    # Pulsing red portal on minimap
                    pulse = int(math.sin(self.anim_tick * 0.1) * 40)
                    col = (200 + pulse, 30, 60)
                else:
                    col = (80, 75, 90)
                pygame.draw.rect(screen, col, (px, py, mm_size, mm_size))

        # Player dot
        px = mm_x + self.player.x * mm_size
        py = mm_y + self.player.y * mm_size
        pygame.draw.rect(screen, C_GREEN, (px, py, mm_size, mm_size))

        # Companion dots
        for c in self.party[1:]:
            if c.alive:
                pygame.draw.rect(screen, C_BLUE, (mm_x + c.x * mm_size, mm_y + c.y * mm_size, mm_size, mm_size))

        # Enemy dots (only if in sight)
        for e in self.enemies:
            if e.alive:
                dx = abs(e.x - self.player.x)
                dy = abs(e.y - self.player.y)
                if math.sqrt(dx * dx + dy * dy) <= 6:
                    pygame.draw.rect(screen, C_RED, (mm_x + e.x * mm_size, mm_y + e.y * mm_size, mm_size, mm_size))

    def draw_chat_bubble(self, name, text):
        """Draw an AI companion chat bubble."""
        bubble_w = min(350, len(text) * 8 + 30)
        bubble_h = 45
        bx = SCREEN_W // 2 - bubble_w // 2
        by = SCREEN_H - 160

        alpha = min(255, self.ai_chat_display_time * 5)
        surf = pygame.Surface((bubble_w, bubble_h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (20, 18, 35, min(220, alpha)), (0, 0, bubble_w, bubble_h), border_radius=10)
        pygame.draw.rect(surf, (100, 80, 160, min(200, alpha)), (0, 0, bubble_w, bubble_h), 1, border_radius=10)
        screen.blit(surf, (bx, by))

        if alpha > 50:
            nt = self.font_sm.render(f"💬 {name}:", True, (150, 200, 255))
            nt.set_alpha(alpha)
            screen.blit(nt, (bx + 10, by + 5))
            tt = self.font_xs.render(text[:50], True, C_WHITE)
            tt.set_alpha(alpha)
            screen.blit(tt, (bx + 10, by + 24))

    def draw_combat(self):
        """Draw the combat screen."""
        if not self.combat:
            return

        sx, sy = self.combat.shake_offset

        # Background
        # Gradient dark background with subtle pattern
        for y in range(0, SCREEN_H, 4):
            shade = 15 + int(y / SCREEN_H * 15)
            pygame.draw.rect(screen, (shade, shade - 2, shade + 5), (0, y, SCREEN_W, 4))

        # Arena floor
        floor_y = 350
        pygame.draw.ellipse(screen, (40, 35, 50), (100 + sx, floor_y + 30 + sy, SCREEN_W - 200, 200))
        pygame.draw.ellipse(screen, (50, 45, 60), (100 + sx, floor_y + 30 + sy, SCREEN_W - 200, 200), 2)

        # Draw party (left side)
        for i, member in enumerate(self.combat.party):
            mx = 180 + i * 90 + sx
            my = floor_y - 40 + (i % 2) * 30 + sy

            if not member.alive:
                # Draw X mark
                dead_t = self.font_md.render("💀", True, C_RED)
                screen.blit(dead_t, (mx, my + 20))
                continue

            sprite = member.get_sprite()
            scaled = pygame.transform.scale(sprite, (40, 52))

            # Flash on damage
            if member.flash_timer > 0:
                member.flash_timer -= 1
                if member.flash_timer % 3 == 0:
                    continue

            # Highlight current turn
            is_current = self.combat.get_current() == member
            if is_current:
                glow = pygame.Surface((48, 60), pygame.SRCALPHA)
                pulse_a = 40 + int(math.sin(self.anim_tick * 0.1) * 20)
                pygame.draw.rect(glow, (*C_GOLD, pulse_a), (0, 0, 48, 60), border_radius=8)
                screen.blit(glow, (mx - 4, my - 4))

            screen.blit(scaled, (mx, my))

            # Name and HP
            nt = self.font_xs.render(member.name, True, C_GOLD if is_current else C_WHITE)
            screen.blit(nt, (mx + 20 - nt.get_width() // 2, my - 14))

            # HP bar
            hp_pct = member.hp / member.max_hp
            pygame.draw.rect(screen, C_HP_BG, (mx - 2, my + 55, 44, 5), border_radius=2)
            pygame.draw.rect(screen, C_GREEN if hp_pct > 0.3 else C_RED, (mx - 2, my + 55, int(44 * hp_pct), 5), border_radius=2)

        # Draw enemies (right side)
        for i, enemy in enumerate(self.combat.enemies):
            ex = SCREEN_W - 250 - i * 90 + sx
            ey = floor_y - 50 + (i % 2) * 30 + sy

            if not enemy.alive:
                dead_t = self.font_md.render("💀", True, (100, 60, 60))
                screen.blit(dead_t, (ex + 10, ey + 20))
                continue

            sprite = enemy.get_sprite()
            scaled = pygame.transform.scale(sprite, (48, 64))
            flipped = pygame.transform.flip(scaled, True, False)

            if enemy.flash_timer > 0:
                enemy.flash_timer -= 1
                if enemy.flash_timer % 3 == 0:
                    continue

            is_current = self.combat.get_current() == enemy
            if is_current:
                glow = pygame.Surface((56, 72), pygame.SRCALPHA)
                pulse_a = 40 + int(math.sin(self.anim_tick * 0.1) * 20)
                pygame.draw.rect(glow, (*C_RED, pulse_a), (0, 0, 56, 72), border_radius=8)
                screen.blit(glow, (ex - 4, ey - 4))

            screen.blit(flipped, (ex, ey))

            # Name and HP
            nt = self.font_xs.render(f"{enemy.name} Lv{enemy.level}", True, C_RED if is_current else (200, 150, 150))
            screen.blit(nt, (ex + 24 - nt.get_width() // 2, ey - 14))

            hp_pct = enemy.hp / enemy.max_hp
            pygame.draw.rect(screen, C_HP_BG, (ex, ey + 67, 48, 5), border_radius=2)
            pygame.draw.rect(screen, C_RED, (ex, ey + 67, int(48 * hp_pct), 5), border_radius=2)
            hp_text = self.font_xs.render(f"{enemy.hp}/{enemy.max_hp}", True, (200, 150, 150))
            screen.blit(hp_text, (ex + 24 - hp_text.get_width() // 2, ey + 74))

        # Particles and float text
        draw_particles(screen, 0, 0)
        draw_float_texts(screen, 0, 0, self.font_sm)

        # Combat log (right panel)
        log_x = SCREEN_W - 400
        log_y = 10
        log_w = 385
        log_h = 300

        panel = pygame.Surface((log_w, log_h), pygame.SRCALPHA)
        panel.fill((10, 8, 18, 200))
        pygame.draw.rect(panel, C_PANEL_BORDER, (0, 0, log_w, log_h), 1, border_radius=8)
        screen.blit(panel, (log_x, log_y))

        header = self.font_sm.render(f"⚔️ Combat Log — Round {self.combat.round_num}", True, C_GOLD)
        screen.blit(header, (log_x + 10, log_y + 6))

        visible_log = self.combat.log[-14:]
        for i, (msg, col) in enumerate(visible_log):
            lt = self.font_xs.render(msg[:56], True, col)
            screen.blit(lt, (log_x + 10, log_y + 26 + i * 18))

        # Action panel (Player's turn)
        if self.combat.phase == 'player_turn':
            self.draw_combat_actions()
        elif self.combat.phase == 'ai_turn':
            current = self.combat.get_current()
            thinking = self.font_md.render(f"🤖 {current.name if current else 'AI'} is thinking...", True, (150, 200, 255))
            screen.blit(thinking, (20, SCREEN_H - 60))
        elif self.combat.phase == 'enemy_turn':
            current = self.combat.get_current()
            acting = self.font_md.render(f"🔴 {current.name if current else 'Enemy'} attacks!", True, C_RED)
            screen.blit(acting, (20, SCREEN_H - 60))

    def draw_combat_actions(self):
        """Draw action buttons during player's turn."""
        current = self.combat.get_current()
        if not current:
            return

        panel_y = SCREEN_H - 180
        panel = pygame.Surface((500, 170), pygame.SRCALPHA)
        panel.fill((15, 12, 25, 230))
        pygame.draw.rect(panel, C_GOLD, (0, 0, 500, 170), 2, border_radius=10)
        screen.blit(panel, (10, panel_y))

        # Turn indicator
        turn_t = self.font_md.render(f"⚔️ {current.name}'s Turn", True, C_GOLD)
        screen.blit(turn_t, (25, panel_y + 8))

        mx, my = pygame.mouse.get_pos()

        if self.combat.selected_action:
            # TARGET SELECTION MODE
            alive_enemies = [e for e in self.combat.enemies if e.alive]
            action_name = "Attack" if self.combat.selected_action == 'attack' else self.combat.selected_action.replace('skill_', 'Skill ')
            prompt = self.font_md.render(f"🎯 Select target for {action_name}:", True, C_GOLD)
            screen.blit(prompt, (25, panel_y + 35))

            for i, enemy in enumerate(alive_enemies):
                ty = panel_y + 60 + i * 28
                tx = 40
                is_hov = tx <= mx <= tx + 400 and ty - 2 <= my <= ty + 24
                hp_pct = enemy.hp / enemy.max_hp
                hp_col = C_RED if hp_pct < 0.3 else C_GREEN
                col = C_RED if is_hov else (220, 180, 180)
                label = f"[{i + 1}] {enemy.name}  (HP: {enemy.hp}/{enemy.max_hp})"
                et = self.font_sm.render(label, True, col)
                screen.blit(et, (tx, ty))

            hint = self.font_xs.render("Press 1-9 to pick target | Enter = first | Esc = cancel", True, (150, 140, 170))
            screen.blit(hint, (25, panel_y + 150))
        else:
            # ACTION SELECTION MODE
            actions = [
                ("[1] ⚔️ Attack", "Basic attack (d20 + bonus vs AC)", 'attack'),
                ("[2] 🛡️ Defend", "Raise AC by 2 this round", 'defend'),
            ]

            for i, skill_name in enumerate(current.skills):
                cost = 3 + i * 2
                actions.append((f"[{i+3}] ✨ {skill_name} ({cost} MP)", f"Use {skill_name}", f'skill_{i}'))

            potions = [it for it in current.inventory if it['type'] == 'consumable']
            if potions:
                actions.append(("[H] 🧪 Use Potion", "Use a healing potion", 'potion'))

            btn_x = 25
            btn_y = panel_y + 35
            btn_w = 230
            btn_h = 28

            for i, (label, desc, action_id) in enumerate(actions):
                col_idx = i // 3
                row_idx = i % 3
                bx = btn_x + col_idx * (btn_w + 10)
                by = btn_y + row_idx * (btn_h + 5)

                is_hovered = bx <= mx <= bx + btn_w and by <= my <= by + btn_h
                bg = (50, 40, 70) if is_hovered else (30, 25, 45)
                border = C_GOLD if is_hovered else (60, 50, 80)

                pygame.draw.rect(screen, bg, (bx, by, btn_w, btn_h), border_radius=5)
                pygame.draw.rect(screen, border, (bx, by, btn_w, btn_h), 1, border_radius=5)

                lt = self.font_xs.render(label, True, C_WHITE if is_hovered else (180, 175, 190))
                screen.blit(lt, (bx + 8, by + 7))

            hint = self.font_xs.render("Press number keys or click to select action", True, (130, 120, 150))
            screen.blit(hint, (25, panel_y + 150))

    def draw_inventory(self):
        """Draw the inventory screen with sorting, scrolling, capacity."""
        screen.fill(C_DARK)

        # Title with capacity
        inv_count = len(self.player.inventory)
        cap_col = C_RED if inv_count >= MAX_INVENTORY else C_GOLD if inv_count >= MAX_INVENTORY - 5 else C_WHITE
        t = self.font_lg.render("📦 Inventory", True, C_GOLD)
        screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2 - 60, 20))
        cap_t = self.font_md.render(f"[{inv_count}/{MAX_INVENTORY}]", True, cap_col)
        screen.blit(cap_t, (SCREEN_W // 2 + t.get_width() // 2 - 40, 28))

        # Capacity bar
        bar_x = SCREEN_W // 2 - 100
        bar_w = 200
        bar_h = 6
        bar_y = 55
        fill_pct = min(1.0, inv_count / MAX_INVENTORY)
        bar_col = C_RED if fill_pct >= 1.0 else C_GOLD if fill_pct >= 0.85 else C_GREEN
        pygame.draw.rect(screen, C_DARK3, (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        pygame.draw.rect(screen, bar_col, (bar_x, bar_y, int(bar_w * fill_pct), bar_h), border_radius=3)

        # Stats panel
        stats_x = 50
        stats_y = 80
        pygame.draw.rect(screen, C_DARK2, (stats_x, stats_y, 300, 320), border_radius=10)
        pygame.draw.rect(screen, C_PANEL_BORDER, (stats_x, stats_y, 300, 320), 1, border_radius=10)

        st = self.font_md.render(f"⚔️ {self.player.name} — Level {self.player.level} {self.player.char_class.title()}", True, C_GOLD)
        screen.blit(st, (stats_x + 15, stats_y + 15))

        stats_info = [
            f"HP: {self.player.hp}/{self.player.max_hp}",
            f"MP: {self.player.mp}/{self.player.max_mp}",
            f"AC: {self.player.ac}",
            f"Attack: {self.player.attack_dice} + {self.player.get_attack_bonus()}",
            "",
            f"STR: {self.player.stats['STR']} ({'+' if modifier(self.player.stats['STR']) >= 0 else ''}{modifier(self.player.stats['STR'])})",
            f"DEX: {self.player.stats['DEX']} ({'+' if modifier(self.player.stats['DEX']) >= 0 else ''}{modifier(self.player.stats['DEX'])})",
            f"CON: {self.player.stats['CON']} ({'+' if modifier(self.player.stats['CON']) >= 0 else ''}{modifier(self.player.stats['CON'])})",
            f"INT: {self.player.stats['INT']} ({'+' if modifier(self.player.stats['INT']) >= 0 else ''}{modifier(self.player.stats['INT'])})",
            f"WIS: {self.player.stats['WIS']} ({'+' if modifier(self.player.stats['WIS']) >= 0 else ''}{modifier(self.player.stats['WIS'])})",
            f"CHA: {self.player.stats['CHA']} ({'+' if modifier(self.player.stats['CHA']) >= 0 else ''}{modifier(self.player.stats['CHA'])})",
            "",
            f"💰 Gold: {self.gold}",
            f"XP: {self.player.xp}/{self.player.xp_to_level}",
        ]
        for i, line in enumerate(stats_info):
            col = C_WHITE if line else C_WHITE
            st2 = self.font_sm.render(line, True, col)
            screen.blit(st2, (stats_x + 20, stats_y + 45 + i * 19))

        # Equipment
        equip_x = stats_x
        equip_y = stats_y + 330
        eq_label = self.font_md.render("Equipment:", True, C_GOLD)
        screen.blit(eq_label, (equip_x, equip_y))
        for i, (slot, item) in enumerate(self.player.equipment.items()):
            item_name = f"{item['icon']} {item['name']}" if item else "Empty"
            et = self.font_sm.render(f"{slot.title()}: {item_name}", True, C_WHITE if item else (100, 90, 110))
            screen.blit(et, (equip_x + 10, equip_y + 25 + i * 20))

        # Items list panel
        items_x = 400
        items_y = 80
        panel_w = 450
        panel_h = 530
        pygame.draw.rect(screen, C_DARK2, (items_x, items_y, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(screen, C_PANEL_BORDER, (items_x, items_y, panel_w, panel_h), 1, border_radius=10)

        # Header row: Items label + Sort button
        il = self.font_md.render("🎒 Items", True, C_GOLD)
        screen.blit(il, (items_x + 15, items_y + 10))
        sort_name = self.SORT_MODE_NAMES[self.inv_sort_mode]
        sort_btn_x = items_x + panel_w - 140
        sort_btn_y = items_y + 8
        sort_btn_w = 125
        sort_btn_h = 24
        pygame.draw.rect(screen, (60, 50, 80), (sort_btn_x, sort_btn_y, sort_btn_w, sort_btn_h), border_radius=5)
        pygame.draw.rect(screen, C_PANEL_BORDER, (sort_btn_x, sort_btn_y, sort_btn_w, sort_btn_h), 1, border_radius=5)
        sort_t = self.font_sm.render(f"Sort: {sort_name} [S]", True, (180, 170, 200))
        screen.blit(sort_t, (sort_btn_x + 8, sort_btn_y + 5))

        # Type category headers color map
        TYPE_COLORS = {
            'weapon': (220, 120, 80),
            'armor': (100, 160, 220),
            'accessory': (200, 160, 255),
            'consumable': (100, 200, 100),
        }

        mx, my = pygame.mouse.get_pos()

        # Item list area with scroll
        list_top = items_y + 38
        list_bottom = items_y + panel_h - 10
        item_h = 30
        max_visible = (list_bottom - list_top) // item_h  # ~16 items visible

        sorted_items = self.get_sorted_inventory()
        total_items = len(sorted_items)
        max_scroll = max(0, total_items - max_visible)
        self.inv_scroll = max(0, min(self.inv_scroll, max_scroll))

        if not self.player.inventory:
            empty = self.font_sm.render("No items. Explore dungeons to find loot!", True, (100, 90, 110))
            screen.blit(empty, (items_x + 20, list_top + 15))
        else:
            # Clip rendering to panel area
            visible_start = self.inv_scroll
            visible_end = min(total_items, visible_start + max_visible)

            # Track prev type for category separators when sorting by type
            prev_type = None

            for vi, idx in enumerate(range(visible_start, visible_end)):
                orig_idx, item = sorted_items[idx]
                y = list_top + vi * item_h
                item_type = item.get('type', '')

                # Category separator line when sorting by type
                if self.inv_sort_mode == 0 and item_type != prev_type:
                    type_label = item_type.title() + 's'
                    type_col = TYPE_COLORS.get(item_type, (150, 140, 160))
                    sep_t = self.font_xs.render(f"── {type_label} ──", True, type_col)
                    screen.blit(sep_t, (items_x + 15, y + 2))
                    prev_type = item_type

                is_sel = self.inv_selected == idx
                is_hov = items_x + 10 <= mx <= items_x + panel_w - 10 and y <= my <= y + item_h - 2

                bg = (70, 50, 90) if is_sel else (50, 40, 65) if is_hov else C_DARK3
                border_col = C_GOLD if is_sel else None
                pygame.draw.rect(screen, bg, (items_x + 10, y, panel_w - 20, item_h - 2), border_radius=5)
                if border_col:
                    pygame.draw.rect(screen, border_col, (items_x + 10, y, panel_w - 20, item_h - 2), 1, border_radius=5)

                # Type color indicator dot
                type_col = TYPE_COLORS.get(item_type, (150, 140, 160))
                pygame.draw.circle(screen, type_col, (items_x + 22, y + item_h // 2 - 1), 4)

                icon = item.get('icon', '📦')
                name = item['name']
                desc = item.get('desc', '')
                # Truncate desc if too long
                display_desc = desc[:30] + '...' if len(desc) > 33 else desc
                it = self.font_sm.render(f"{icon} {name}", True, C_WHITE if (is_hov or is_sel) else (170, 165, 180))
                screen.blit(it, (items_x + 32, y + 3))

                # Show desc on hover/select
                if is_hov or is_sel:
                    desc_t = self.font_xs.render(display_desc, True, (140, 135, 155))
                    screen.blit(desc_t, (items_x + 32, y + 17))
                    action_t = self.font_xs.render("[Click:Equip] [D:Drop]", True, C_GOLD)
                    screen.blit(action_t, (items_x + panel_w - 140, y + 7))

            # Scroll indicator
            if max_scroll > 0:
                scroll_track_h = list_bottom - list_top
                scroll_bar_h = max(20, int(scroll_track_h * max_visible / total_items))
                scroll_bar_y = list_top + int((scroll_track_h - scroll_bar_h) * (self.inv_scroll / max_scroll))
                pygame.draw.rect(screen, (60, 50, 75), (items_x + panel_w - 8, list_top, 5, scroll_track_h), border_radius=2)
                pygame.draw.rect(screen, (120, 110, 140), (items_x + panel_w - 8, scroll_bar_y, 5, scroll_bar_h), border_radius=2)

        # Party info
        party_y = items_y + panel_h + 15
        pt = self.font_md.render("🤝 Party", True, C_GOLD)
        screen.blit(pt, (items_x + 15, party_y))
        for i, member in enumerate(self.party[1:]):
            y = party_y + 28 + i * 22
            status = "💀 Dead" if not member.alive else f"HP:{member.hp}/{member.max_hp}"
            mt = self.font_sm.render(f"{'🤖' if member.is_ai else '👤'} {member.name} ({member.char_class}) — {status}", True, C_WHITE if member.alive else C_RED)
            screen.blit(mt, (items_x + 20, y))

        # Instructions
        inst = self.font_sm.render("I/ESC:Close | Click:Use/Equip | S:Sort | D:Drop | ↑↓/Scroll:Navigate | T:Skill Tree", True, (100, 90, 120))
        screen.blit(inst, (SCREEN_W // 2 - inst.get_width() // 2, SCREEN_H - 30))

    def draw_skill_tree(self):
        """Draw the skill tree screen for the currently selected party member."""
        screen.fill(C_DARK)

        # Get current member
        member_idx = self.skill_tree_member_idx % len(self.party)
        member = self.party[member_idx]
        tree = SKILL_TREES.get(member.char_class, [])

        # Title bar
        title_text = f"🌳 Skill Tree — {member.name} ({member.char_class.title()}) — Level {member.level}"
        t = self.font_lg.render(title_text, True, C_GOLD)
        screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, 15))

        # Skill points display
        sp_col = C_GOLD if member.skill_points > 0 else (100, 90, 110)
        sp_text = f"✨ Skill Points: {member.skill_points}"
        sp = self.font_md.render(sp_text, True, sp_col)
        screen.blit(sp, (SCREEN_W // 2 - sp.get_width() // 2, 55))

        # Party member tabs
        tab_y = 85
        tab_x_start = 50
        for i, m in enumerate(self.party):
            col = C_GOLD if i == member_idx else (100, 90, 110)
            bg = (50, 40, 65) if i == member_idx else C_DARK2
            tab_w = 200
            tx = tab_x_start + i * (tab_w + 10)
            pygame.draw.rect(screen, bg, (tx, tab_y, tab_w, 30), border_radius=6)
            pygame.draw.rect(screen, col, (tx, tab_y, tab_w, 30), 1, border_radius=6)
            status = "" if m.alive else " 💀"
            pts = f" ({m.skill_points}pts)" if m.skill_points > 0 else ""
            tab_label = f"{'👤' if not m.is_ai else '🤖'} {m.name}{pts}{status}"
            tt = self.font_sm.render(tab_label, True, col)
            screen.blit(tt, (tx + 10, tab_y + 7))

        # Draw skill tree nodes
        tree_area_x = 100
        tree_area_y = 140
        node_w = 220
        node_h = 65
        col_spacing = 260
        row_spacing = 100

        mx, my = pygame.mouse.get_pos()

        # Draw connection lines first
        for node in tree:
            if not node['requires']:
                continue
            nx = tree_area_x + node['col'] * col_spacing + node_w // 2
            ny = tree_area_y + node['row'] * row_spacing + node_h // 2
            for req_id in node['requires']:
                req_node = next((n for n in tree if n['id'] == req_id), None)
                if req_node:
                    rx = tree_area_x + req_node['col'] * col_spacing + node_w // 2
                    ry = tree_area_y + req_node['row'] * row_spacing + node_h // 2
                    req_rank = member.skill_tree.get(req_id, 0)
                    line_col = (80, 180, 80) if req_rank > 0 else (60, 50, 70)
                    pygame.draw.line(screen, line_col, (rx, ry), (nx, ny), 2)

        # Draw nodes
        for i, node in enumerate(tree):
            nx = tree_area_x + node['col'] * col_spacing
            ny = tree_area_y + node['row'] * row_spacing
            rank = member.skill_tree.get(node['id'], 0)
            can_up = can_upgrade_node(member, node['id'])
            is_selected = (i == self.skill_tree_selected)
            is_hovered = nx <= mx <= nx + node_w and ny <= my <= ny + node_h

            # Node color
            if rank >= node['max_rank']:
                bg_col = (30, 70, 30)  # Maxed — green
                border_col = (80, 200, 80)
            elif rank > 0:
                bg_col = (40, 50, 70)  # Partially filled — blue
                border_col = (100, 150, 220)
            elif can_up:
                bg_col = (55, 45, 35)  # Available — warm
                border_col = C_GOLD
            else:
                bg_col = (30, 28, 35)  # Locked — dim
                border_col = (60, 55, 70)

            if is_selected or is_hovered:
                bg_col = tuple(min(255, c + 20) for c in bg_col)
                border_col = C_WHITE

            pygame.draw.rect(screen, bg_col, (nx, ny, node_w, node_h), border_radius=8)
            pygame.draw.rect(screen, border_col, (nx, ny, node_w, node_h), 2, border_radius=8)

            # Icon + name
            icon_name = f"{node['icon']} {node['name']}"
            nt = self.font_sm.render(icon_name, True, C_WHITE if rank > 0 or can_up else (120, 110, 130))
            screen.blit(nt, (nx + 10, ny + 8))

            # Rank
            rank_text = f"{rank}/{node['max_rank']}"
            rank_col = C_GREEN if rank >= node['max_rank'] else (C_GOLD if rank > 0 else (100, 90, 110))
            rt = self.font_sm.render(rank_text, True, rank_col)
            screen.blit(rt, (nx + node_w - 40, ny + 8))

            # Description
            dt = self.font_xs.render(node['desc'], True, (160, 150, 175))
            screen.blit(dt, (nx + 10, ny + 30))

            # Upgrade hint
            if can_up and (is_selected or is_hovered):
                hint = self.font_xs.render("[Click or ENTER to upgrade]", True, C_GOLD)
                screen.blit(hint, (nx + 10, ny + 48))

        # Stats summary on the right
        stats_x = SCREEN_W - 350
        stats_y = tree_area_y
        pygame.draw.rect(screen, C_DARK2, (stats_x, stats_y, 320, 420), border_radius=10)
        pygame.draw.rect(screen, C_PANEL_BORDER, (stats_x, stats_y, 320, 420), 1, border_radius=10)
        sh = self.font_md.render("📊 Skill Tree Bonuses", True, C_GOLD)
        screen.blit(sh, (stats_x + 15, stats_y + 10))

        bonus_lines = []
        hp_pct = get_skill_tree_bonus(member, 'max_hp_pct')
        mp_pct = get_skill_tree_bonus(member, 'max_mp_pct')
        ac = get_skill_tree_bonus(member, 'ac')
        dmg = get_skill_tree_bonus(member, 'damage_pct')
        skill_pwr = get_skill_tree_bonus(member, 'skill_power_pct')
        magic_dmg = get_skill_tree_bonus(member, 'magic_damage_pct')
        heal_pwr = get_skill_tree_bonus(member, 'heal_power_pct')
        mp_red = get_skill_tree_bonus(member, 'mp_cost_reduction')
        crit_dmg = get_skill_tree_bonus(member, 'crit_damage_pct')
        gold_b = get_skill_tree_bonus(member, 'gold_pct')
        xp_b = get_skill_tree_bonus(member, 'xp_pct')
        atk_b = get_skill_tree_bonus(member, 'attack_bonus')

        if hp_pct: bonus_lines.append(f"❤️ Max HP: +{hp_pct}%")
        if mp_pct: bonus_lines.append(f"💧 Max MP: +{mp_pct}%")
        if ac: bonus_lines.append(f"🛡️ AC: +{ac}")
        if dmg: bonus_lines.append(f"⚔️ Damage: +{dmg}%")
        if skill_pwr: bonus_lines.append(f"✨ Skill Power: +{skill_pwr}%")
        if magic_dmg: bonus_lines.append(f"🔮 Magic Damage: +{magic_dmg}%")
        if heal_pwr: bonus_lines.append(f"🙏 Heal Power: +{heal_pwr}%")
        if mp_red: bonus_lines.append(f"⚡ MP Cost: -{mp_red}")
        if crit_dmg: bonus_lines.append(f"🗡️ Crit Damage: +{crit_dmg}%")
        if gold_b: bonus_lines.append(f"🪙 Gold Found: +{gold_b}%")
        if xp_b: bonus_lines.append(f"📈 XP Gained: +{xp_b}%")
        if atk_b: bonus_lines.append(f"🎯 Attack Bonus: +{atk_b}")

        # Stat bonuses
        for stat in ('STR', 'DEX', 'INT', 'WIS', 'CON', 'CHA'):
            st_bonus = get_skill_tree_bonus(member, stat.lower())
            if st_bonus: bonus_lines.append(f"📊 {stat}: +{st_bonus}")

        if not bonus_lines:
            bonus_lines.append("No skills upgraded yet")

        for i, line in enumerate(bonus_lines):
            col = C_WHITE if "No skills" not in line else (100, 90, 110)
            bt = self.font_sm.render(line, True, col)
            screen.blit(bt, (stats_x + 20, stats_y + 40 + i * 22))

        # Member stats summary
        ms_y = stats_y + 40 + max(len(bonus_lines), 1) * 22 + 15
        ms_lines = [
            f"Level {member.level} {member.char_class.title()}",
            f"HP: {member.hp}/{member.max_hp}  MP: {member.mp}/{member.max_mp}",
            f"AC: {member.ac}  XP: {member.xp}/{member.xp_to_level}",
        ]
        for i, line in enumerate(ms_lines):
            mst = self.font_sm.render(line, True, (160, 150, 175))
            screen.blit(mst, (stats_x + 20, ms_y + i * 20))

        # Instructions
        inst_lines = [
            "← → Switch party member | ↑ ↓ Select node | ENTER Upgrade",
            "T or ESC to close | Numbers 1-6 to upgrade nodes directly",
        ]
        for i, line in enumerate(inst_lines):
            inst = self.font_sm.render(line, True, (100, 90, 120))
            screen.blit(inst, (SCREEN_W // 2 - inst.get_width() // 2, SCREEN_H - 50 + i * 20))

    def draw_game_over(self):
        # Fade overlay
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Title
        t = self.font_title.render("GAME OVER", True, C_RED)
        screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, SCREEN_H // 2 - 80))

        # Stats
        stats = [
            f"Floor Reached: {self.floor_num}",
            f"Level: {self.player.level if self.player else 1}",
            f"Gold Collected: {self.gold}",
        ]
        for i, line in enumerate(stats):
            st = self.font_md.render(line, True, C_WHITE)
            screen.blit(st, (SCREEN_W // 2 - st.get_width() // 2, SCREEN_H // 2 + i * 30))

        # Retry
        pulse = int(math.sin(self.anim_tick * 0.06) * 20 + 235)
        retry = self.font_md.render("Press ENTER to continue (progress saved!) or ESC for title", True, (pulse, pulse - 20, 100))
        screen.blit(retry, (SCREEN_W // 2 - retry.get_width() // 2, SCREEN_H // 2 + 120))


# ════════════════════════════════════════════════════════════
# MAIN GAME LOOP
# ════════════════════════════════════════════════════════════
def main():
    game = Game()

    while True:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                # ─── TITLE SCREEN ───
                if game.state == GameState.TITLE:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if os.path.exists(SAVE_FILE):
                            game.load_game()
                        else:
                            game.state = GameState.CLASS_SELECT
                    elif event.key == pygame.K_n:
                        game.state = GameState.CLASS_SELECT
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

                # ─── CLASS SELECT ───
                elif game.state == GameState.CLASS_SELECT:
                    classes = list(DnDClass.CLASSES.keys())
                    if event.key == pygame.K_LEFT:
                        game.selected_class = (game.selected_class - 1) % len(classes)
                    elif event.key == pygame.K_RIGHT:
                        game.selected_class = (game.selected_class + 1) % len(classes)
                    elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
                        idx = event.key - pygame.K_1
                        if idx < len(classes):
                            game.selected_class = idx
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        game.new_game(classes[game.selected_class])
                    elif event.key == pygame.K_ESCAPE:
                        game.state = GameState.TITLE

                # ─── EXPLORING ─── (movement handled via held-keys in update())
                elif game.state == GameState.EXPLORING:
                    if event.key == pygame.K_i:
                        game.state = GameState.INVENTORY
                    elif event.key == pygame.K_t:
                        game.skill_tree_member_idx = 0
                        game.skill_tree_selected = 0
                        game.state = GameState.SKILL_TREE
                    elif event.key == pygame.K_m:
                        game.minimap_open = not game.minimap_open
                    elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                        # Quick skill use
                        skill_idx = event.key - pygame.K_1
                        if skill_idx < len(game.player.skills):
                            success, msg, _ = game.player.use_skill(skill_idx, game.player, [p for p in game.party if p.alive])
                            if success:
                                game.add_message(f"✨ {msg}", C_PURPLE)
                            else:
                                game.add_message(f"❌ {msg}", C_RED)
                    elif event.key == pygame.K_ESCAPE:
                        game.state = GameState.TITLE

                # ─── COMBAT ───
                elif game.state == GameState.COMBAT and game.combat:
                    if game.combat.phase == 'player_turn':
                        current = game.combat.get_current()
                        if not current:
                            continue

                        alive_enemies = [e for e in game.combat.enemies if e.alive]

                        # If an action is selected and waiting for target
                        if game.combat.selected_action:
                            target = None
                            # Number keys to pick target (1-9)
                            target_keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                                           pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]
                            for ki, tk in enumerate(target_keys):
                                if event.key == tk and ki < len(alive_enemies):
                                    target = alive_enemies[ki]
                                    break
                            # Enter/Space auto-targets first enemy
                            if event.key in (pygame.K_RETURN, pygame.K_SPACE) and alive_enemies:
                                target = alive_enemies[0]
                            # Escape cancels action
                            if event.key == pygame.K_ESCAPE:
                                game.combat.selected_action = None
                                game.combat.add_log("Action cancelled.", (150, 150, 150))

                            if target:
                                if game.combat.selected_action == 'attack':
                                    game.combat.do_attack(current, target)
                                elif game.combat.selected_action and game.combat.selected_action.startswith('skill_'):
                                    si = int(game.combat.selected_action.split('_')[1])
                                    success, msg, dmg = current.use_skill(si, target, [p for p in game.party if p.alive])
                                    if success:
                                        game.combat.add_log(f"✨ {msg}", C_PURPLE)
                                        if dmg > 0:
                                            target.take_damage(dmg)
                                            spawn_float_text(target.x * TILE_W, target.y * TILE_H, f"-{dmg}", C_PURPLE)
                                            if not target.alive:
                                                game.combat.add_log(f"💀 {target.name} defeated!", C_RED)
                                    else:
                                        game.combat.add_log(f"❌ {msg}", C_RED)
                                game.combat.next_turn()
                                game.combat.selected_action = None
                        else:
                            # Select action
                            if event.key == pygame.K_1 or event.key == pygame.K_a:
                                game.combat.selected_action = 'attack'
                                # Auto-execute if single enemy
                                if len(alive_enemies) == 1:
                                    game.combat.do_attack(current, alive_enemies[0])
                                    game.combat.next_turn()
                                    game.combat.selected_action = None
                                else:
                                    game.combat.add_log(f"⚔️ Select target (1-{len(alive_enemies)})", C_GOLD)
                            elif event.key == pygame.K_2 or event.key == pygame.K_s:
                                # Defend
                                current.ac += 2
                                game.combat.add_log(f"🛡️ {current.name} takes a defensive stance! AC +2", C_BLUE)
                                game.combat.next_turn()
                            elif event.key in (pygame.K_3, pygame.K_4, pygame.K_5):
                                skill_idx = event.key - pygame.K_3
                                if skill_idx < len(current.skills):
                                    game.combat.selected_action = f'skill_{skill_idx}'
                                    if len(alive_enemies) == 1:
                                        si = skill_idx
                                        target = alive_enemies[0]
                                        success, msg, dmg = current.use_skill(si, target, [p for p in game.party if p.alive])
                                        if success:
                                            game.combat.add_log(f"✨ {msg}", C_PURPLE)
                                            if dmg > 0:
                                                target.take_damage(dmg)
                                                spawn_float_text(target.x * TILE_W, target.y * TILE_H, f"-{dmg}", C_PURPLE)
                                                if not target.alive:
                                                    game.combat.add_log(f"💀 {target.name} defeated!", C_RED)
                                        else:
                                            game.combat.add_log(f"❌ {msg}", C_RED)
                                        game.combat.next_turn()
                                        game.combat.selected_action = None
                                    else:
                                        game.combat.add_log(f"✨ Select target (1-{len(alive_enemies)})", C_PURPLE)
                            elif event.key == pygame.K_h:
                                # Use health potion
                                potions = [i for i, it in enumerate(current.inventory) if it.get('effect') == 'heal']
                                if potions:
                                    game.use_item(potions[0])
                                    game.combat.add_log(f"🧪 {current.name} drinks a health potion!", C_GREEN)
                                    game.combat.next_turn()

                # ─── INVENTORY ───
                elif game.state == GameState.INVENTORY:
                    if event.key in (pygame.K_i, pygame.K_ESCAPE):
                        game.state = GameState.EXPLORING
                        game.inv_scroll = 0
                        game.inv_selected = -1
                    elif event.key == pygame.K_t:
                        game.skill_tree_member_idx = 0
                        game.skill_tree_selected = 0
                        game.state = GameState.SKILL_TREE
                    elif event.key == pygame.K_s:
                        game.inv_sort_mode = (game.inv_sort_mode + 1) % 3
                        game.inv_scroll = 0
                        game.inv_selected = -1
                    elif event.key == pygame.K_UP:
                        if game.inv_selected > 0:
                            game.inv_selected -= 1
                        elif game.inv_selected == -1 and game.player.inventory:
                            game.inv_selected = 0
                        # Auto-scroll if selection above visible area
                        if game.inv_selected >= 0 and game.inv_selected < game.inv_scroll:
                            game.inv_scroll = game.inv_selected
                    elif event.key == pygame.K_DOWN:
                        total = len(game.player.inventory)
                        if game.inv_selected < total - 1:
                            game.inv_selected += 1
                        elif game.inv_selected == -1 and game.player.inventory:
                            game.inv_selected = 0
                        # Auto-scroll if selection below visible area
                        max_vis = 16
                        if game.inv_selected >= game.inv_scroll + max_vis:
                            game.inv_scroll = game.inv_selected - max_vis + 1
                    elif event.key == pygame.K_d:
                        # Drop selected item
                        if game.inv_selected >= 0:
                            sorted_inv = game.get_sorted_inventory()
                            if game.inv_selected < len(sorted_inv):
                                orig_idx, _ = sorted_inv[game.inv_selected]
                                game.drop_item(orig_idx)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        # Use/equip selected item
                        if game.inv_selected >= 0:
                            sorted_inv = game.get_sorted_inventory()
                            if game.inv_selected < len(sorted_inv):
                                orig_idx, _ = sorted_inv[game.inv_selected]
                                game.use_item(orig_idx)

                # ─── SKILL TREE ───
                elif game.state == GameState.SKILL_TREE:
                    member = game.party[game.skill_tree_member_idx % len(game.party)]
                    tree = SKILL_TREES.get(member.char_class, [])
                    if event.key in (pygame.K_t, pygame.K_ESCAPE):
                        game.state = GameState.EXPLORING
                    elif event.key == pygame.K_LEFT:
                        game.skill_tree_member_idx = (game.skill_tree_member_idx - 1) % len(game.party)
                        game.skill_tree_selected = 0
                    elif event.key == pygame.K_RIGHT:
                        game.skill_tree_member_idx = (game.skill_tree_member_idx + 1) % len(game.party)
                        game.skill_tree_selected = 0
                    elif event.key == pygame.K_UP:
                        game.skill_tree_selected = (game.skill_tree_selected - 1) % max(1, len(tree))
                    elif event.key == pygame.K_DOWN:
                        game.skill_tree_selected = (game.skill_tree_selected + 1) % max(1, len(tree))
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        if tree and game.skill_tree_selected < len(tree):
                            node_id = tree[game.skill_tree_selected]['id']
                            if upgrade_node(member, node_id):
                                game.add_message(f"🌟 {member.name} upgraded {tree[game.skill_tree_selected]['name']}!", C_GOLD)
                                game.save_game()
                    elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6):
                        idx = event.key - pygame.K_1
                        if idx < len(tree):
                            node_id = tree[idx]['id']
                            if upgrade_node(member, node_id):
                                game.add_message(f"🌟 {member.name} upgraded {tree[idx]['name']}!", C_GOLD)
                                game.save_game()

                # ─── GAME OVER ───
                elif game.state == GameState.GAME_OVER:
                    if event.key == pygame.K_RETURN:
                        if os.path.exists(SAVE_FILE):
                            game.load_game()
                        else:
                            game.state = GameState.CLASS_SELECT
                    elif event.key == pygame.K_ESCAPE:
                        game.state = GameState.TITLE

            # ─── MOUSE WHEEL (Inventory scroll) ───
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
                if game.state == GameState.INVENTORY:
                    if event.button == 4:  # Scroll up
                        game.inv_scroll = max(0, game.inv_scroll - 3)
                    elif event.button == 5:  # Scroll down
                        max_scroll = max(0, len(game.player.inventory) - 16)
                        game.inv_scroll = min(max_scroll, game.inv_scroll + 3)

            # ─── MOUSE CLICKS ───
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if game.state == GameState.TITLE:
                    title_opts = getattr(game, '_title_opts', [])
                    for i, (label, _) in enumerate(title_opts):
                        y = 340 + i * 50
                        if SCREEN_W // 2 - 120 < mx < SCREEN_W // 2 + 120 and y - 5 < my < y + 30:
                            if 'Continue' in label:
                                game.load_game()
                            elif 'New Adventure' in label:
                                game.state = GameState.CLASS_SELECT
                            elif 'Quit' in label:
                                pygame.quit()
                                sys.exit()
                            break

                elif game.state == GameState.CLASS_SELECT:
                    classes = list(DnDClass.CLASSES.keys())
                    total_w = len(classes) * 225 - 15
                    start_x = (SCREEN_W - total_w) // 2
                    for i in range(len(classes)):
                        cx = start_x + i * 225
                        if cx <= mx <= cx + 210 and 90 <= my <= 430:
                            game.selected_class = i
                            game.new_game(classes[i])
                            break

                elif game.state == GameState.INVENTORY:
                    # Click items to use/equip (with scroll offset)
                    items_x = 400
                    items_y = 80
                    list_top = items_y + 38
                    item_h = 30
                    panel_w = 450
                    sorted_inv = game.get_sorted_inventory()
                    max_visible = 16
                    visible_start = game.inv_scroll
                    visible_end = min(len(sorted_inv), visible_start + max_visible)

                    # Sort button click
                    sort_btn_x = items_x + panel_w - 140
                    sort_btn_y = items_y + 8
                    if sort_btn_x <= mx <= sort_btn_x + 125 and sort_btn_y <= my <= sort_btn_y + 24:
                        game.inv_sort_mode = (game.inv_sort_mode + 1) % 3
                        game.inv_scroll = 0
                        game.inv_selected = -1
                    else:
                        for vi, idx in enumerate(range(visible_start, visible_end)):
                            y = list_top + vi * item_h
                            if items_x + 10 <= mx <= items_x + panel_w - 10 and y <= my <= y + item_h - 2:
                                orig_idx, _ = sorted_inv[idx]
                                game.inv_selected = idx
                                game.use_item(orig_idx)
                                break

                elif game.state == GameState.SKILL_TREE:
                    # Click party member tabs
                    tab_y = 85
                    tab_x_start = 50
                    tab_w = 200
                    for i in range(len(game.party)):
                        tx = tab_x_start + i * (tab_w + 10)
                        if tx <= mx <= tx + tab_w and tab_y <= my <= tab_y + 30:
                            game.skill_tree_member_idx = i
                            game.skill_tree_selected = 0
                            break
                    else:
                        # Click skill tree nodes
                        member = game.party[game.skill_tree_member_idx % len(game.party)]
                        tree = SKILL_TREES.get(member.char_class, [])
                        tree_area_x = 100
                        tree_area_y = 140
                        node_w = 220
                        node_h = 65
                        col_spacing = 260
                        row_spacing = 100
                        for i, node in enumerate(tree):
                            nx = tree_area_x + node['col'] * col_spacing
                            ny = tree_area_y + node['row'] * row_spacing
                            if nx <= mx <= nx + node_w and ny <= my <= ny + node_h:
                                game.skill_tree_selected = i
                                if upgrade_node(member, node['id']):
                                    game.add_message(f"🌟 {member.name} upgraded {node['name']}!", C_GOLD)
                                    game.save_game()
                                break

                elif game.state == GameState.COMBAT and game.combat and game.combat.phase == 'player_turn':
                    current = game.combat.get_current()
                    if current:
                        panel_y = SCREEN_H - 180

                        if game.combat.selected_action:
                            # TARGET SELECTION via mouse
                            alive_enemies = [e for e in game.combat.enemies if e.alive]
                            for i, enemy in enumerate(alive_enemies):
                                ty = panel_y + 60 + i * 28
                                tx = 40
                                if tx <= mx <= tx + 400 and ty - 2 <= my <= ty + 24:
                                    if game.combat.selected_action == 'attack':
                                        game.combat.do_attack(current, enemy)
                                    elif game.combat.selected_action.startswith('skill_'):
                                        si = int(game.combat.selected_action.split('_')[1])
                                        success, msg, dmg = current.use_skill(si, enemy, [p for p in game.party if p.alive])
                                        if success:
                                            game.combat.add_log(f"✨ {msg}", C_PURPLE)
                                            if dmg > 0:
                                                enemy.take_damage(dmg)
                                                spawn_float_text(enemy.x * TILE_W, enemy.y * TILE_H, f"-{dmg}", C_PURPLE)
                                                if not enemy.alive:
                                                    game.combat.add_log(f"💀 {enemy.name} defeated!", C_RED)
                                        else:
                                            game.combat.add_log(f"❌ {msg}", C_RED)
                                    game.combat.next_turn()
                                    game.combat.selected_action = None
                                    break
                        else:
                            # ACTION SELECTION via mouse
                            actions_list = ['attack', 'defend']
                            for si in range(len(current.skills)):
                                actions_list.append(f'skill_{si}')
                            potions = [it for it in current.inventory if it.get('effect') == 'heal']
                            if potions:
                                actions_list.append('potion')

                            btn_x = 25
                            btn_y = panel_y + 35
                            btn_w = 230
                            btn_h = 28

                            for i, action_id in enumerate(actions_list):
                                col_idx = i // 3
                                row_idx = i % 3
                                bx = btn_x + col_idx * (btn_w + 10)
                                by = btn_y + row_idx * (btn_h + 5)

                                if bx <= mx <= bx + btn_w and by <= my <= by + btn_h:
                                    if action_id == 'defend':
                                        current.ac += 2
                                        game.combat.add_log(f"🛡️ {current.name} defends! AC +2", C_BLUE)
                                        game.combat.next_turn()
                                    elif action_id == 'potion':
                                        potions_list = [idx for idx, it in enumerate(current.inventory) if it.get('effect') == 'heal']
                                        if potions_list:
                                            game.use_item(potions_list[0])
                                            game.combat.add_log(f"🧪 {current.name} uses a potion!", C_GREEN)
                                            game.combat.next_turn()
                                    else:
                                        game.combat.selected_action = action_id
                                        # Auto-target if single enemy
                                        alive_enemies = [e for e in game.combat.enemies if e.alive]
                                        if len(alive_enemies) == 1:
                                            target = alive_enemies[0]
                                            if action_id == 'attack':
                                                game.combat.do_attack(current, target)
                                            elif action_id.startswith('skill_'):
                                                si = int(action_id.split('_')[1])
                                                success, msg, dmg = current.use_skill(si, target, [p for p in game.party if p.alive])
                                                if success:
                                                    game.combat.add_log(f"✨ {msg}", C_PURPLE)
                                                    if dmg > 0:
                                                        target.take_damage(dmg)
                                                        spawn_float_text(target.x * TILE_W, target.y * TILE_H, f"-{dmg}", C_PURPLE)
                                                        if not target.alive:
                                                            game.combat.add_log(f"💀 {target.name} defeated!", C_RED)
                                                else:
                                                    game.combat.add_log(f"❌ {msg}", C_RED)
                                            game.combat.next_turn()
                                            game.combat.selected_action = None
                                    break

        game.update()
        game.draw()


if __name__ == '__main__':
    main()
