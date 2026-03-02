"""
Grandma's Random Clicker - A cozy clicker game for grandmas!
Click cookies, buy upgrades, and become the ultimate grandma baker!
"""

import pygame
import sys
import math
import random
import json
import os
import time
import struct
import array as arr_mod

# Pre-init mixer BEFORE pygame.init() so mono config is respected
pygame.mixer.pre_init(frequency=44100, size=-16, channels=1, buffer=512)
pygame.init()
pygame.mixer.quit()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

# ── Window ──────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 900, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🍪 Grandma's Random Clicker 🍪")
clock = pygame.time.Clock()

# ── Colours ─────────────────────────────────────────────────────────────
BG           = (255, 243, 224)
PANEL_BG     = (255, 235, 205)
PANEL_BORDER = (205, 170, 125)
COOKIE_BROWN = (180, 110, 50)
COOKIE_DARK  = (140, 80, 30)
COOKIE_CHIP  = (90, 55, 20)
TEXT_DARK     = (80, 50, 20)
TEXT_LIGHT    = (140, 100, 60)
GOLD         = (255, 200, 50)
BTN_GREEN    = (100, 180, 80)
BTN_GREEN_H  = (120, 200, 100)
BTN_RED      = (200, 80, 80)
BTN_RED_H    = (220, 100, 100)
BTN_BLUE     = (80, 140, 200)
BTN_BLUE_H   = (100, 160, 220)
BTN_PURPLE   = (150, 90, 180)
BTN_PURPLE_H = (170, 110, 200)
BTN_ORANGE   = (220, 150, 50)
BTN_ORANGE_H = (240, 170, 70)
BTN_TEAL     = (40, 170, 160)
BTN_TEAL_H   = (60, 190, 180)
BTN_PINK     = (200, 80, 150)
BTN_PINK_H   = (220, 100, 170)
BTN_GOLD     = (200, 170, 40)
BTN_GOLD_H   = (220, 190, 60)
BTN_CYAN     = (50, 160, 210)
BTN_CYAN_H   = (70, 180, 230)
BTN_LIME     = (130, 200, 50)
BTN_LIME_H   = (150, 220, 70)
WHITE        = (255, 255, 255)
BLACK        = (0, 0, 0)
SHADOW       = (0, 0, 0, 60)

# ── Fonts ───────────────────────────────────────────────────────────────
font_xl   = pygame.font.SysFont("Segoe UI", 48, bold=True)
font_lg   = pygame.font.SysFont("Segoe UI", 32, bold=True)
font_md   = pygame.font.SysFont("Segoe UI", 22)
font_sm   = pygame.font.SysFont("Segoe UI", 18)
font_xs   = pygame.font.SysFont("Segoe UI", 14)
font_emoji = pygame.font.SysFont("Segoe UI Emoji", 36)

# ── Sound Effects (generated programmatically) ─────────────────────────
def _clamp(v):
    return max(-32767, min(32767, int(v)))

def _make_sound(freq, duration=0.12, volume=0.35, wave="sine", freq_end=None):
    """Generate a short sound effect from a waveform."""
    sr = 44100; n = int(sr * duration)
    buf = arr_mod.array("h")
    for i in range(n):
        t = i / sr
        f = freq + (freq_end - freq) * (i / n) if freq_end is not None else freq
        if wave == "sine":
            val = math.sin(2 * math.pi * f * t)
        elif wave == "square":
            val = 1.0 if math.sin(2 * math.pi * f * t) >= 0 else -1.0
        elif wave == "saw":
            val = 2.0 * (f * t % 1.0) - 1.0
        else:
            val = math.sin(2 * math.pi * f * t)
        env = max(0, 1.0 - (i / n) * 0.8)
        buf.append(_clamp(val * volume * 32767 * env))
    return pygame.mixer.Sound(buffer=buf)


# ─── CLICK SOUNDS (low-pitched, goofy, over-the-top) ───────────────────

def _make_mega_fart():
    """Massive, deep, rumbly fart that could shake a room."""
    sr = 44100; dur = 0.55; n = int(sr * dur)
    buf = arr_mod.array("h")
    for i in range(n):
        t = i / sr
        # Very low base frequency with wobble
        base_f = 35 + 15 * math.sin(2 * math.pi * 4 * t)
        rumble = math.sin(2 * math.pi * base_f * t)
        # Flappy lips vibration
        flap = math.sin(2 * math.pi * 18 * t) * math.sin(2 * math.pi * 45 * t)
        # Noisy crackle
        noise = random.uniform(-0.4, 0.4)
        val = rumble * 0.5 + flap * 0.3 + noise * 0.2
        # Big attack, slow taper
        if t < 0.04:
            env = t / 0.04
        elif t < 0.2:
            env = 1.0
        else:
            env = max(0, 1.0 - (t - 0.2) / 0.35)
        buf.append(_clamp(val * 0.9 * 32767 * env))
    return pygame.mixer.Sound(buffer=buf)


def _make_tuba_blast():
    """Obnoxious tuba BWAAAH — deep brass honk."""
    sr = 44100; dur = 0.3; n = int(sr * dur)
    buf = arr_mod.array("h")
    for i in range(n):
        t = i / sr
        f = 58  # very low Bb
        # Rich brass harmonics
        val = (math.sin(2 * math.pi * f * t) * 0.5 +
               math.sin(2 * math.pi * f * 2 * t) * 0.3 +
               math.sin(2 * math.pi * f * 3 * t) * 0.15 +
               math.sin(2 * math.pi * f * 4 * t) * 0.05)
        env = min(1, t / 0.02) * max(0, 1 - t / dur * 0.5)
        buf.append(_clamp(val * 0.85 * 32767 * env))
    return pygame.mixer.Sound(buffer=buf)


def _make_deep_bonk():
    """Heavy cartoon bonk — like getting hit with an anvil."""
    sr = 44100; dur = 0.25; n = int(sr * dur)
    buf = arr_mod.array("h")
    for i in range(n):
        t = i / sr
        # Very low impact tone that drops
        f = 120 * max(0, 1 - t / dur * 2) + 40
        val = (1.0 if math.sin(2 * math.pi * f * t) > 0 else -1.0)
        noise = random.uniform(-0.3, 0.3) if t < 0.05 else 0
        val = val * 0.7 + noise
        env = max(0, 1.0 - t / dur)
        buf.append(_clamp(val * 0.9 * 32767 * env))
    return pygame.mixer.Sound(buffer=buf)


def _make_belly_flop():
    """Belly flop splat — heavy impact + wobble."""
    sr = 44100; dur = 0.3; n = int(sr * dur)
    buf = arr_mod.array("h")
    for i in range(n):
        t = i / sr
        if t < 0.03:
            # Initial slap — burst of noise
            val = random.uniform(-1, 1)
            env = 1.0
        else:
            # Deep wobbling aftermath
            f = 50 + 30 * math.sin(2 * math.pi * 6 * t)
            val = math.sin(2 * math.pi * f * t)
            noise = random.uniform(-0.15, 0.15)
            val = val * 0.7 + noise
            env = max(0, 1.0 - (t - 0.03) / (dur - 0.03))
        buf.append(_clamp(val * 0.85 * 32767 * env))
    return pygame.mixer.Sound(buffer=buf)


def _make_toilet_flush():
    """Toilet swirl sound — descending warble into gurgle."""
    sr = 44100; dur = 0.5; n = int(sr * dur)
    buf = arr_mod.array("h")
    for i in range(n):
        t = i / sr
        progress = t / dur
        # Descending swirl
        f = 200 * (1 - progress * 0.8) + 30
        swirl = math.sin(2 * math.pi * f * t + 5 * math.sin(2 * math.pi * 3 * t))
        gurgle = random.uniform(-0.3, 0.3) * (0.3 + progress * 0.7)
        val = swirl * 0.6 + gurgle
        env = min(1, t / 0.03) * max(0, 1 - progress * 0.4)
        buf.append(_clamp(val * 0.8 * 32767 * env))
    return pygame.mixer.Sound(buffer=buf)


def _make_grandpa_snore():
    """One big snore — inhale + vibrate exhale."""
    sr = 44100; dur = 0.5; n = int(sr * dur)
    buf = arr_mod.array("h")
    for i in range(n):
        t = i / sr
        if t < 0.2:
            # Inhale — rising noise
            noise = random.uniform(-0.5, 0.5)
            tone = math.sin(2 * math.pi * 90 * t) * 0.3
            env = (t / 0.2) * 0.7
            val = noise * 0.5 + tone
        else:
            # Exhale — deep vibrating buzz
            f = 55 + 10 * math.sin(2 * math.pi * 12 * t)
            val = math.sin(2 * math.pi * f * t)
            rattle = (1.0 if math.sin(2 * math.pi * 25 * t) > 0 else -1.0) * 0.3
            val = val * 0.5 + rattle
            env = max(0, 1.0 - (t - 0.2) / 0.3) * 0.8
        buf.append(_clamp(val * 0.85 * 32767 * env))
    return pygame.mixer.Sound(buffer=buf)


def _make_foghorn():
    """Deep foghorn BWOOOOO — low and loud."""
    sr = 44100; dur = 0.4; n = int(sr * dur)
    buf = arr_mod.array("h")
    for i in range(n):
        t = i / sr
        f = 75  # very deep
        val = (math.sin(2 * math.pi * f * t) * 0.6 +
               math.sin(2 * math.pi * f * 1.5 * t) * 0.25 +
               math.sin(2 * math.pi * f * 2 * t) * 0.15)
        # Slight wobble
        val *= (1 + 0.2 * math.sin(2 * math.pi * 2 * t))
        env = min(1, t / 0.04) * max(0, 1 - (t / dur) * 0.3)
        buf.append(_clamp(val * 0.85 * 32767 * env))
    return pygame.mixer.Sound(buffer=buf)


def _make_cartoon_fall():
    """Long cartoon falling whistle — starts mid, goes DEEP."""
    sr = 44100; dur = 0.4; n = int(sr * dur)
    buf = arr_mod.array("h")
    for i in range(n):
        t = i / sr
        progress = t / dur
        f = 400 * (1 - progress) ** 2 + 30  # exponential drop to bass
        val = math.sin(2 * math.pi * f * t)
        env = min(1, t / 0.02) * max(0.2, 1 - progress * 0.5)
        buf.append(_clamp(val * 0.8 * 32767 * env))
    return pygame.mixer.Sound(buffer=buf)


def _make_deep_boing():
    """Super deep cartoon boing — DOIOIOIOING."""
    sr = 44100; dur = 0.4; n = int(sr * dur)
    buf = arr_mod.array("h")
    for i in range(n):
        t = i / sr
        # Low frequency that bounces
        bounce = abs(math.sin(2 * math.pi * 6 * t))
        f = 60 + 80 * bounce * max(0, 1 - t / dur)
        val = math.sin(2 * math.pi * f * t)
        env = max(0, 1.0 - t / dur * 0.6)
        buf.append(_clamp(val * 0.85 * 32767 * env))
    return pygame.mixer.Sound(buffer=buf)


def _make_explosion():
    """Cartoon explosion — KABOOM bass hit + rumble."""
    sr = 44100; dur = 0.35; n = int(sr * dur)
    buf = arr_mod.array("h")
    for i in range(n):
        t = i / sr
        if t < 0.04:
            # Initial blast — noise + bass
            val = random.uniform(-1, 1) * 0.6 + math.sin(2 * math.pi * 40 * t) * 0.4
            env = 1.0
        else:
            # Deep rumbling decay
            f = 35 + 10 * random.uniform(-1, 1)
            val = math.sin(2 * math.pi * f * t) * 0.5 + random.uniform(-0.3, 0.3)
            env = max(0, 1 - (t - 0.04) / (dur - 0.04))
        buf.append(_clamp(val * 0.9 * 32767 * env))
    return pygame.mixer.Sound(buffer=buf)


def _make_deep_honk():
    """Deep clown horn — comically low HONK HONK."""
    sr = 44100; dur = 0.3; n = int(sr * dur)
    buf = arr_mod.array("h")
    for i in range(n):
        t = i / sr
        f = 90  # much lower than before
        val = (math.sin(2 * math.pi * f * t) +
               0.4 * math.sin(2 * math.pi * f * 3 * t) +
               0.2 * math.sin(2 * math.pi * f * 5 * t))
        # Two honks
        if t < 0.12:
            env = 0.9
        elif t < 0.16:
            env = 0.05
        else:
            env = max(0, 0.9 - (t - 0.16) / 0.14)
        buf.append(_clamp(val * 0.7 * 32767 * env))
    return pygame.mixer.Sound(buffer=buf)


def _make_bass_drop():
    """Dubstep bass drop — BWWWWUB."""
    sr = 44100; dur = 0.3; n = int(sr * dur)
    buf = arr_mod.array("h")
    for i in range(n):
        t = i / sr
        # Rapidly descending into sub bass
        f = 300 * max(0, 1 - t / dur * 3) + 30
        val = 1.0 if math.sin(2 * math.pi * f * t) > 0 else -1.0
        # Add wobble
        val *= (1 + 0.5 * math.sin(2 * math.pi * 8 * t))
        env = max(0, 1 - t / dur * 0.6)
        buf.append(_clamp(val * 0.6 * 32767 * env))
    return pygame.mixer.Sound(buffer=buf)


# ─── UI / EVENT SOUNDS ─────────────────────────────────────────────────

def _make_cha_ching():
    """Ka-ching purchase — lower, punchier."""
    sr = 44100; dur = 0.2; n = int(sr * dur)
    buf = arr_mod.array("h")
    for i in range(n):
        t = i / sr
        f = 600 if t < 0.08 else 800
        val = math.sin(2 * math.pi * f * t) + 0.3 * math.sin(2 * math.pi * f * 2 * t)
        env = max(0, 1.0 - t / dur * 0.7)
        buf.append(_clamp(val * 0.75 * 32767 * env))
    return pygame.mixer.Sound(buffer=buf)


def _make_fail():
    """Tuba sad trombone — wah wah wah wahhh (LOW)."""
    sr = 44100
    notes = [(175, 0.2), (165, 0.2), (156, 0.2), (147, 0.45)]  # one octave lower
    buf = arr_mod.array("h")
    for freq, dur in notes:
        n = int(sr * dur)
        for i in range(n):
            t = i / sr
            val = (math.sin(2 * math.pi * freq * t) * 0.5 +
                   math.sin(2 * math.pi * freq * 2 * t) * 0.3 +
                   math.sin(2 * math.pi * freq * 3 * t) * 0.15 +
                   math.sin(2 * math.pi * freq * 4 * t) * 0.05)
            if freq == 147:
                val *= (1 + 0.4 * math.sin(2 * math.pi * 4 * t))
            env = max(0, 1.0 - (i / n) * 0.3)
            buf.append(_clamp(val * 0.7 * 32767 * env))
    return pygame.mixer.Sound(buffer=buf)


def _make_golden():
    """Low magical sparkle — deep chimes."""
    sr = 44100; dur = 0.5; n = int(sr * dur)
    buf = arr_mod.array("h")
    for i in range(n):
        t = i / sr
        val = (math.sin(2 * math.pi * (400 + 80 * math.sin(2 * math.pi * 5 * t)) * t) * 0.4 +
               math.sin(2 * math.pi * (600 + 100 * math.sin(2 * math.pi * 7 * t)) * t) * 0.35 +
               math.sin(2 * math.pi * (200 + 50 * math.sin(2 * math.pi * 3 * t)) * t) * 0.25)
        env = max(0, 1.0 - t / dur * 0.5)
        buf.append(_clamp(val * 0.75 * 32767 * env))
    return pygame.mixer.Sound(buffer=buf)


def _make_milestone():
    """Deep air horn — three blasts + long BWAAAAH."""
    sr = 44100; buf = arr_mod.array("h")
    pattern = [(0.1, True), (0.05, False), (0.1, True), (0.05, False),
               (0.1, True), (0.06, False), (0.35, True)]
    for dur, on in pattern:
        n = int(sr * dur)
        for i in range(n):
            t = i / sr
            if on:
                f = 180  # low air horn
                val = (math.sin(2 * math.pi * f * t) * 0.5 +
                       math.sin(2 * math.pi * f * 1.5 * t) * 0.3 +
                       math.sin(2 * math.pi * f * 2 * t) * 0.2)
                env = 0.9
            else:
                val = 0; env = 0
            buf.append(_clamp(val * 0.8 * 32767 * env))
    return pygame.mixer.Sound(buffer=buf)


def _make_save():
    """Chunky save sound — low bloop bloop."""
    sr = 44100; buf = arr_mod.array("h")
    for freq, dur in [(250, 0.08), (350, 0.15)]:
        n = int(sr * dur)
        for i in range(n):
            t = i / sr
            val = math.sin(2 * math.pi * freq * t) + 0.25 * math.sin(2 * math.pi * freq * 2 * t)
            env = max(0, 1 - (i / n) * 0.5)
            buf.append(_clamp(val * 0.75 * 32767 * env))
    return pygame.mixer.Sound(buffer=buf)


def _make_rebirth():
    """Deep epic rebirth — ascending from sub bass."""
    sr = 44100
    notes = [(110, 0.08), (147, 0.08), (165, 0.08), (220, 0.1),
             (262, 0.1), (330, 0.12), (440, 0.2)]
    buf = arr_mod.array("h")
    for freq, dur in notes:
        n = int(sr * dur)
        for i in range(n):
            t = i / sr
            val = (math.sin(2 * math.pi * freq * t) +
                   0.3 * math.sin(2 * math.pi * freq * 2 * t) +
                   0.15 * math.sin(2 * math.pi * freq * 3 * t))
            env = max(0, 1.0 - (i / n) * 0.3)
            buf.append(_clamp(val * 0.7 * 32767 * env))
    return pygame.mixer.Sound(buffer=buf)


def _make_rainbow():
    """Epic ascending sparkle sound for rainbow cookie."""
    sr = 44100
    buf = arr_mod.array("h")
    total = int(sr * 1.2)
    for i in range(total):
        t = i / sr
        progress = i / total
        # Rising frequency sweep
        freq = 100 + 600 * progress
        val = (math.sin(2 * math.pi * freq * t) * 0.5 +
               math.sin(2 * math.pi * freq * 1.5 * t) * 0.25 +
               math.sin(2 * math.pi * freq * 2 * t) * 0.15 +
               math.sin(2 * math.pi * 30 * t) * 0.3 * (1 - progress))  # sub bass rumble
        # Sparkle pings layered on top
        sparkle = math.sin(2 * math.pi * (800 + 400 * math.sin(t * 12)) * t) * 0.15 * progress
        env = min(1.0, i / (sr * 0.05)) * max(0, 1.0 - max(0, progress - 0.7) / 0.3)
        buf.append(_clamp((val + sparkle) * 0.8 * 32767 * env))
    return pygame.mixer.Sound(buffer=buf)

# Build SFX dict
SFX = {
    "buy": _make_cha_ching(),
    "fail": _make_fail(),
    "golden": _make_golden(),
    "milestone": _make_milestone(),
    "save": _make_save(),
    "rebirth": _make_rebirth(),
    "rainbow": _make_rainbow(),
}

# All the funny click sounds — deep, goofy, ridiculous
# Weighted list – boing, burp (mega fart), and honk are 3× more common
_boing   = _make_deep_boing()
_burp    = _make_mega_fart()
_honk    = _make_deep_honk()

_click_sounds = [
    _burp, _burp, _burp,       # burp  – common
    _boing, _boing, _boing,    # boing – common
    _honk, _honk, _honk,       # honk  – common
    _make_tuba_blast(),
    _make_deep_bonk(),
    _make_belly_flop(),
    _make_toilet_flush(),
    _make_grandpa_snore(),
    _make_foghorn(),
    _make_cartoon_fall(),
    _make_explosion(),
    _make_bass_drop(),
]

def play_sfx(name):
    """Play a named sound effect."""
    if name in SFX:
        SFX[name].play()

def play_click_sfx():
    """Play a random funny sound on every click."""
    random.choice(_click_sounds).play()

# ── Save file ───────────────────────────────────────────────────────────
SAVE_FILE = "grandma_clicker_save.json"

# ── Upgrades definition ────────────────────────────────────────────────
UPGRADES = [
    {
        "name": "Wooden Spoon",
        "emoji": "🥄",
        "desc": "+1 per click",
        "base_cost": 15,
        "cost_mult": 1.15,
        "click_bonus": 1,
        "cps_bonus": 0,
        "color": BTN_GREEN,
        "color_h": BTN_GREEN_H,
    },
    {
        "name": "Grandma Helper",
        "emoji": "👵",
        "desc": "+0.5 cookies/sec",
        "base_cost": 50,
        "cost_mult": 1.18,
        "click_bonus": 0,
        "cps_bonus": 0.5,
        "color": BTN_BLUE,
        "color_h": BTN_BLUE_H,
    },
    {
        "name": "Oven",
        "emoji": "🔥",
        "desc": "+2 cookies/sec",
        "base_cost": 200,
        "cost_mult": 1.20,
        "click_bonus": 0,
        "cps_bonus": 2,
        "color": BTN_RED,
        "color_h": BTN_RED_H,
    },
    {
        "name": "Recipe Book",
        "emoji": "📖",
        "desc": "+5 per click",
        "base_cost": 500,
        "cost_mult": 1.22,
        "click_bonus": 5,
        "cps_bonus": 0,
        "color": BTN_PURPLE,
        "color_h": BTN_PURPLE_H,
    },
    {
        "name": "Cookie Factory",
        "emoji": "🏭",
        "desc": "+10 cookies/sec",
        "base_cost": 2000,
        "cost_mult": 1.25,
        "click_bonus": 0,
        "cps_bonus": 10,
        "color": BTN_ORANGE,
        "color_h": BTN_ORANGE_H,
    },
    {
        "name": "Magic Rolling Pin",
        "emoji": "✨",
        "desc": "+25 per click",
        "base_cost": 8000,
        "cost_mult": 1.28,
        "click_bonus": 25,
        "cps_bonus": 0,
        "color": BTN_GREEN,
        "color_h": BTN_GREEN_H,
    },
    {
        "name": "Cookie Portal",
        "emoji": "🌀",
        "desc": "+50 cookies/sec",
        "base_cost": 25000,
        "cost_mult": 1.30,
        "click_bonus": 0,
        "cps_bonus": 50,
        "color": BTN_BLUE,
        "color_h": BTN_BLUE_H,
    },
    {
        "name": "Time Machine",
        "emoji": "⏰",
        "desc": "+200 cookies/sec",
        "base_cost": 100000,
        "cost_mult": 1.35,
        "click_bonus": 0,
        "cps_bonus": 200,
        "color": BTN_PURPLE,
        "color_h": BTN_PURPLE_H,
    },
    # ── Tier 2: Getting serious ─────────────────────────
    {
        "name": "Cookie Cloner",
        "emoji": "🧬",
        "desc": "+100 per click",
        "base_cost": 350000,
        "cost_mult": 1.30,
        "click_bonus": 100,
        "cps_bonus": 0,
        "color": BTN_TEAL,
        "color_h": BTN_TEAL_H,
    },
    {
        "name": "Grandma Army",
        "emoji": "👵👵",
        "desc": "+500 cookies/sec",
        "base_cost": 800000,
        "cost_mult": 1.35,
        "click_bonus": 0,
        "cps_bonus": 500,
        "color": BTN_PINK,
        "color_h": BTN_PINK_H,
    },
    {
        "name": "Cookie Satellite",
        "emoji": "🛰️",
        "desc": "+1,500 cookies/sec",
        "base_cost": 2500000,
        "cost_mult": 1.38,
        "click_bonus": 0,
        "cps_bonus": 1500,
        "color": BTN_CYAN,
        "color_h": BTN_CYAN_H,
    },
    {
        "name": "Golden Spatula",
        "emoji": "🥇",
        "desc": "+500 per click",
        "base_cost": 5000000,
        "cost_mult": 1.32,
        "click_bonus": 500,
        "cps_bonus": 0,
        "color": BTN_GOLD,
        "color_h": BTN_GOLD_H,
    },
    {
        "name": "Cookie Planet",
        "emoji": "🪐",
        "desc": "+5,000 cookies/sec",
        "base_cost": 15000000,
        "cost_mult": 1.40,
        "click_bonus": 0,
        "cps_bonus": 5000,
        "color": BTN_ORANGE,
        "color_h": BTN_ORANGE_H,
    },
    {
        "name": "Quantum Whisk",
        "emoji": "⚛️",
        "desc": "+2,000 per click",
        "base_cost": 40000000,
        "cost_mult": 1.35,
        "click_bonus": 2000,
        "cps_bonus": 0,
        "color": BTN_PURPLE,
        "color_h": BTN_PURPLE_H,
    },
    {
        "name": "Cookie Dimension",
        "emoji": "🌌",
        "desc": "+15,000 cookies/sec",
        "base_cost": 100000000,
        "cost_mult": 1.42,
        "click_bonus": 0,
        "cps_bonus": 15000,
        "color": BTN_BLUE,
        "color_h": BTN_BLUE_H,
    },
    # ── Tier 3: Going crazy ─────────────────────────────
    {
        "name": "Butter Blaster",
        "emoji": "🧈",
        "desc": "+8,000 per click",
        "base_cost": 300000000,
        "cost_mult": 1.38,
        "click_bonus": 8000,
        "cps_bonus": 0,
        "color": BTN_LIME,
        "color_h": BTN_LIME_H,
    },
    {
        "name": "Grandma Singularity",
        "emoji": "🕳️",
        "desc": "+50,000 cookies/sec",
        "base_cost": 800000000,
        "cost_mult": 1.45,
        "click_bonus": 0,
        "cps_bonus": 50000,
        "color": BTN_RED,
        "color_h": BTN_RED_H,
    },
    {
        "name": "Sugar Nuke",
        "emoji": "☢️",
        "desc": "+25,000 per click",
        "base_cost": 2000000000,
        "cost_mult": 1.40,
        "click_bonus": 25000,
        "cps_bonus": 0,
        "color": BTN_GREEN,
        "color_h": BTN_GREEN_H,
    },
    {
        "name": "Cookie God",
        "emoji": "👼",
        "desc": "+150,000 cookies/sec",
        "base_cost": 5000000000,
        "cost_mult": 1.48,
        "click_bonus": 0,
        "cps_bonus": 150000,
        "color": BTN_GOLD,
        "color_h": BTN_GOLD_H,
    },
    {
        "name": "Flour Power",
        "emoji": "💪",
        "desc": "+80,000 per click",
        "base_cost": 12000000000,
        "cost_mult": 1.42,
        "click_bonus": 80000,
        "cps_bonus": 0,
        "color": BTN_TEAL,
        "color_h": BTN_TEAL_H,
    },
    {
        "name": "Cookie Multiverse",
        "emoji": "🔮",
        "desc": "+500,000 cookies/sec",
        "base_cost": 30000000000,
        "cost_mult": 1.50,
        "click_bonus": 0,
        "cps_bonus": 500000,
        "color": BTN_PURPLE,
        "color_h": BTN_PURPLE_H,
    },
    # ── Tier 4: Absurdly powerful ───────────────────────
    {
        "name": "Dough Dragon",
        "emoji": "🐉",
        "desc": "+300,000 per click",
        "base_cost": 80000000000,
        "cost_mult": 1.45,
        "click_bonus": 300000,
        "cps_bonus": 0,
        "color": BTN_RED,
        "color_h": BTN_RED_H,
    },
    {
        "name": "Infinity Oven",
        "emoji": "♾️",
        "desc": "+2M cookies/sec",
        "base_cost": 200000000000,
        "cost_mult": 1.52,
        "click_bonus": 0,
        "cps_bonus": 2000000,
        "color": BTN_ORANGE,
        "color_h": BTN_ORANGE_H,
    },
    {
        "name": "Grandma Matrix",
        "emoji": "🤖",
        "desc": "+1M per click",
        "base_cost": 500000000000,
        "cost_mult": 1.48,
        "click_bonus": 1000000,
        "cps_bonus": 0,
        "color": BTN_CYAN,
        "color_h": BTN_CYAN_H,
    },
    {
        "name": "Cookie Nebula",
        "emoji": "🌠",
        "desc": "+8M cookies/sec",
        "base_cost": 1500000000000,
        "cost_mult": 1.55,
        "click_bonus": 0,
        "cps_bonus": 8000000,
        "color": BTN_BLUE,
        "color_h": BTN_BLUE_H,
    },
    {
        "name": "Anti-Matter Mixer",
        "emoji": "⚗️",
        "desc": "+4M per click",
        "base_cost": 5000000000000,
        "cost_mult": 1.50,
        "click_bonus": 4000000,
        "cps_bonus": 0,
        "color": BTN_PINK,
        "color_h": BTN_PINK_H,
    },
    {
        "name": "Cookie Big Bang",
        "emoji": "💥",
        "desc": "+30M cookies/sec",
        "base_cost": 15000000000000,
        "cost_mult": 1.58,
        "click_bonus": 0,
        "cps_bonus": 30000000,
        "color": BTN_LIME,
        "color_h": BTN_LIME_H,
    },
    # ── Tier 5: Endgame ─────────────────────────────────
    {
        "name": "Chrono Cookie",
        "emoji": "⌛",
        "desc": "+15M per click",
        "base_cost": 50000000000000,
        "cost_mult": 1.52,
        "click_bonus": 15000000,
        "cps_bonus": 0,
        "color": BTN_GOLD,
        "color_h": BTN_GOLD_H,
    },
    {
        "name": "Cookie Overlord",
        "emoji": "👑",
        "desc": "+100M cookies/sec",
        "base_cost": 150000000000000,
        "cost_mult": 1.60,
        "click_bonus": 0,
        "cps_bonus": 100000000,
        "color": BTN_RED,
        "color_h": BTN_RED_H,
    },
    {
        "name": "Chocolate Void",
        "emoji": "🍫",
        "desc": "+50M per click",
        "base_cost": 500000000000000,
        "cost_mult": 1.55,
        "click_bonus": 50000000,
        "cps_bonus": 0,
        "color": BTN_TEAL,
        "color_h": BTN_TEAL_H,
    },
    {
        "name": "Cookie Afterlife",
        "emoji": "👻",
        "desc": "+500M cookies/sec",
        "base_cost": 2000000000000000,
        "cost_mult": 1.62,
        "click_bonus": 0,
        "cps_bonus": 500000000,
        "color": BTN_PURPLE,
        "color_h": BTN_PURPLE_H,
    },
    {
        "name": "Grandma Ascension",
        "emoji": "🧓✨",
        "desc": "+200M per click",
        "base_cost": 8000000000000000,
        "cost_mult": 1.58,
        "click_bonus": 200000000,
        "cps_bonus": 0,
        "color": BTN_PINK,
        "color_h": BTN_PINK_H,
    },
]

# ── Random grandma quotes ──────────────────────────────────────────────
GRANDMA_QUOTES = [
    # Classic grandma
    "Have another cookie, dear!",
    "Back in my day, we baked uphill both ways!",
    "You look thin, eat more cookies!",
    "My secret ingredient? Love! ...and butter.",
    "These cookies won't bake themselves!",
    "Oh, you remind me of your grandfather.",
    "More cookies? Of course, sweetie!",
    "Don't tell your mother about these cookies.",
    "I've been baking since before you were born!",
    "A cookie a day keeps the doctor away!",
    "Want some milk with that, dear?",
    "Grandma knows best!",
    "Click faster, dear! Grandpa's hungry!",
    "That's the spirit, sweetheart!",
    "Oh my, look at all those cookies!",
    # Funny / sassy grandma
    "I put my back out baking. Worth it.",
    "My WiFi password? It's COOKIES123, dear.",
    "I didn't survive the Great Depression for weak clicks!",
    "Grandpa says I bake too much. Grandpa is wrong.",
    "I could out-click you with my eyes closed.",
    "These cookies are bussin', as the kids say.",
    "I asked Alexa to bake cookies. She's useless.",
    "My doctor said less sugar. I said less doctor.",
    "You call THAT a click? Put some elbow into it!",
    "I've got more cookies than your GPA, sweetie.",
    "One does not simply stop clicking.",
    "I'm not old, I'm vintage. Like fine cookie dough.",
    "I Googled 'how to bake faster'. It said buy upgrades!",
    "Back in '62, cookies cost a nickel. Good times.",
    "My cat walked on my keyboard and bought 50 ovens.",
    "I showed this game to Ethel. She's already ahead.",
    "You're clicking like grandpa eats — too slow!",
    "Is this what they call 'gaming'? I love it.",
    "My grandson taught me to say 'GG'. GG, dear!",
    "If clicking burned calories, I'd be a supermodel.",
    "Don't make me get the rolling pin.",
    "I've seen things, dear... terrible cookie shortages.",
    "This is more fun than my book club. Don't tell Marge.",
    "I once baked 400 cookies in a day. Amateurs.",
    "Arthritis? Never heard of her.",
    "Cookies are just happiness in circle form.",
    "My therapist says I click too much. I say not enough.",
    "Why go outside? There are no cookies out there.",
    "I'm on a seafood diet. I see food, I bake cookies.",
    "Grandpa's asleep. Quick, click louder!",
    "Plot twist: the cookies were inside us all along.",
    "If you're reading this, you should be clicking.",
    "I trained for this my whole life.",
    "Error 404: Cookie not found. Just kidding, here!",
    "My cookie recipe is classified. Top secret.",
    "Hold my dentures, I'm going in!",
    "I bake, therefore I am.",
    "These cookies aren't gonna click themselves!",
    "Just five more minutes... said grandma 3 hours ago.",
    "Legend says if you click 1 million times, I smile.",
]

# ── Milestones ──────────────────────────────────────────────────────────
MILESTONES = [100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000, 10000000]

# ── Game State ──────────────────────────────────────────────────────────
class GameState:
    def __init__(self):
        self.cookies = 0.0
        self.total_cookies = 0.0
        self.total_clicks = 0
        self.click_power = 1
        self.cps = 0.0  # cookies per second
        self.owned = [0] * len(UPGRADES)
        self.milestone_idx = 0
        self.quote = random.choice(GRANDMA_QUOTES)
        self.quote_timer = 0
        self.particles = []
        self.cookie_scale = 1.0
        self.cookie_target_scale = 1.0
        self.golden_cookie = None  # (x, y, timer, type)
        self.golden_timer = 0
        self.golden_next_spawn = random.uniform(30, 60)
        self.rainbow_cookie = None  # {x, y, timer, type}
        self.rainbow_timer = 0
        self.rainbow_next_spawn = random.uniform(45, 120)
        self.multiplier = 1.0
        self.multiplier_timer = 0.0
        self.frenzy_timer = 0.0
        self.scroll_offset = 0
        self.notification = None
        self.notif_timer = 0
        self.start_time = time.time()
        # Rebirth system
        self.rebirths = 0
        self.rebirth_multiplier = 1.0  # permanent 2x per rebirth
        self.lifetime_cookies = 0.0  # never resets
        # Dev mode
        self.dev_mode = False
        self.dev_panel_open = False
        self.dev_code_buffer = ""  # tracks typed keys
        self.dev_code = "cookies12346"
        self.dev_undo_stack = []  # list of snapshots for undo

    def _snapshot(self):
        """Capture current state for undo."""
        import copy
        return {
            "cookies": self.cookies,
            "total_cookies": self.total_cookies,
            "total_clicks": self.total_clicks,
            "click_power": self.click_power,
            "cps": self.cps,
            "owned": list(self.owned),
            "milestone_idx": self.milestone_idx,
            "rebirths": self.rebirths,
            "rebirth_multiplier": self.rebirth_multiplier,
            "lifetime_cookies": self.lifetime_cookies,
            "multiplier": self.multiplier,
            "multiplier_timer": self.multiplier_timer,
            "golden_cookie": copy.deepcopy(self.golden_cookie),
            "rainbow_cookie": copy.deepcopy(self.rainbow_cookie),
        }

    def _restore(self, snap):
        """Restore state from snapshot."""
        self.cookies = snap["cookies"]
        self.total_cookies = snap["total_cookies"]
        self.total_clicks = snap["total_clicks"]
        self.click_power = snap["click_power"]
        self.cps = snap["cps"]
        self.owned = list(snap["owned"])
        self.milestone_idx = snap["milestone_idx"]
        self.rebirths = snap["rebirths"]
        self.rebirth_multiplier = snap["rebirth_multiplier"]
        self.lifetime_cookies = snap["lifetime_cookies"]
        self.multiplier = snap["multiplier"]
        self.multiplier_timer = snap["multiplier_timer"]
        self.golden_cookie = snap["golden_cookie"]
        self.rainbow_cookie = snap["rainbow_cookie"]

    def get_cost(self, idx):
        up = UPGRADES[idx]
        return int(up["base_cost"] * (up["cost_mult"] ** self.owned[idx]))

    def buy(self, idx):
        cost = self.get_cost(idx)
        if self.cookies >= cost:
            self.cookies -= cost
            self.owned[idx] += 1
            up = UPGRADES[idx]
            self.click_power += up["click_bonus"]
            self.cps += up["cps_bonus"]
            return True
        return False

    def click(self):
        amount = self.click_power * self.multiplier * self.rebirth_multiplier
        if amount != amount or amount == float('inf'):
            amount = 1e300
        self.cookies += amount
        self.total_cookies += amount
        self.lifetime_cookies += amount
        self.total_clicks += 1
        self._cap_values()
        return amount

    def get_rebirth_cost(self):
        try:
            cost = 1_000_000 * (2 ** min(self.rebirths, 1000))
            if cost == float('inf') or cost != cost:
                cost = 1e300
        except (OverflowError, ValueError):
            cost = 1e300
        return cost

    def can_rebirth(self):
        return self.cookies >= self.get_rebirth_cost()

    def _cap_values(self):
        """Prevent values from becoming actual inf/nan."""
        cap = 1e300
        if self.cookies != self.cookies or self.cookies == float('inf'):
            self.cookies = cap
        if self.total_cookies != self.total_cookies or self.total_cookies == float('inf'):
            self.total_cookies = cap
        if self.lifetime_cookies != self.lifetime_cookies or self.lifetime_cookies == float('inf'):
            self.lifetime_cookies = cap
        if self.rebirth_multiplier != self.rebirth_multiplier or self.rebirth_multiplier == float('inf'):
            self.rebirth_multiplier = 1e200

    def rebirth(self):
        cost = self.get_rebirth_cost()
        if self.cookies < cost:
            return False
        self.rebirths += 1
        self.rebirth_multiplier = min(2.0 ** min(self.rebirths, 1000), 1e200)
        # Reset progress but keep lifetime stats & rebirths
        self.cookies = 0.0
        self.total_cookies = 0.0
        self.click_power = 1
        self.cps = 0.0
        self.owned = [0] * len(UPGRADES)
        self.milestone_idx = 0
        self.golden_cookie = None
        self.golden_timer = 0
        self.golden_next_spawn = random.uniform(30, 60)
        self.rainbow_cookie = None
        self.rainbow_timer = 0
        self.rainbow_next_spawn = random.uniform(45, 120)
        self.multiplier = 1.0
        self.multiplier_timer = 0.0
        self.scroll_offset = 0
        return True

    def update(self, dt):
        # CPS
        earned = self.cps * self.multiplier * self.rebirth_multiplier * dt
        if earned != earned or earned == float('inf'):
            earned = 1e300
        self.cookies += earned
        self.total_cookies += earned
        self.lifetime_cookies += earned
        self._cap_values()

        # Cookie bounce animation
        if self.cookie_scale != self.cookie_target_scale:
            self.cookie_scale += (self.cookie_target_scale - self.cookie_scale) * 0.2
            if abs(self.cookie_scale - self.cookie_target_scale) < 0.005:
                self.cookie_scale = self.cookie_target_scale

        # Particles
        for p in self.particles[:]:
            p["y"] -= p["speed"] * dt
            p["alpha"] -= 120 * dt
            p["life"] -= dt
            if p["life"] <= 0:
                self.particles.remove(p)

        # Quote timer
        self.quote_timer += dt
        if self.quote_timer > 8:
            self.quote = random.choice(GRANDMA_QUOTES)
            self.quote_timer = 0

        # Golden cookie spawning
        self.golden_timer += dt
        if self.golden_cookie is None and self.golden_timer > self.golden_next_spawn:
            self.golden_timer = 0
            self.golden_next_spawn = random.uniform(30, 60)
            gx = random.randint(50, 400)
            gy = random.randint(100, 500)
            self.golden_cookie = {"x": gx, "y": gy, "timer": 10.0, "type": random.choice(["x2", "x5", "frenzy", "bonus"])}

        if self.golden_cookie:
            self.golden_cookie["timer"] -= dt
            if self.golden_cookie["timer"] <= 0:
                self.golden_cookie = None

        # Rainbow cookie spawning (rare — every 45-120s)
        self.rainbow_timer += dt
        if self.rainbow_cookie is None and self.rainbow_timer > self.rainbow_next_spawn:
            self.rainbow_timer = 0
            self.rainbow_next_spawn = random.uniform(45, 120)
            rx = random.randint(60, 390)
            ry = random.randint(120, 420)
            rtype = random.choice(["mega_click", "mega_production"])
            self.rainbow_cookie = {"x": rx, "y": ry, "timer": 6.0, "type": rtype}

        if self.rainbow_cookie:
            self.rainbow_cookie["timer"] -= dt
            if self.rainbow_cookie["timer"] <= 0:
                self.rainbow_cookie = None

        # Multiplier timer
        if self.multiplier_timer > 0:
            self.multiplier_timer -= dt
            if self.multiplier_timer <= 0:
                self.multiplier = 1.0
                self.multiplier_timer = 0

        # Notification timer
        if self.notif_timer > 0:
            self.notif_timer -= dt

        # Milestones
        if self.milestone_idx < len(MILESTONES) and self.total_cookies >= MILESTONES[self.milestone_idx]:
            self.notification = f"🎉 Milestone: {format_number(MILESTONES[self.milestone_idx])} cookies baked!"
            self.notif_timer = 4.0
            self.milestone_idx += 1
            play_sfx("milestone")

    def save(self):
        data = {
            "cookies": self.cookies,
            "total_cookies": self.total_cookies,
            "total_clicks": self.total_clicks,
            "click_power": self.click_power,
            "cps": self.cps,
            "owned": self.owned,
            "milestone_idx": self.milestone_idx,
            "multiplier": self.multiplier,
            "multiplier_timer": self.multiplier_timer,
            "rebirths": self.rebirths,
            "rebirth_multiplier": self.rebirth_multiplier,
            "lifetime_cookies": self.lifetime_cookies,
        }
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
            self.cookies = data.get("cookies", 0)
            self.total_cookies = data.get("total_cookies", 0)
            self.total_clicks = data.get("total_clicks", 0)
            self.click_power = data.get("click_power", 1)
            self.cps = data.get("cps", 0)
            self.owned = data.get("owned", [0] * len(UPGRADES))
            self.milestone_idx = data.get("milestone_idx", 0)
            self.multiplier = data.get("multiplier", 1.0)
            self.multiplier_timer = data.get("multiplier_timer", 0)
            self.rebirths = data.get("rebirths", 0)
            self.rebirth_multiplier = data.get("rebirth_multiplier", 1.0)
            self.lifetime_cookies = data.get("lifetime_cookies", 0)
            # Pad owned if new upgrades were added
            while len(self.owned) < len(UPGRADES):
                self.owned.append(0)


# ── Helpers ─────────────────────────────────────────────────────────────
# Number suffixes up to 1e+100 and beyond
_SUFFIXES = [
    (1e303, "Centillion"),
    (1e100, "Googol"),
    (1e93, "Trigintillion"), (1e90, "Novemvigintillion"), (1e87, "Octovigintillion"),
    (1e84, "Septenvigintillion"), (1e81, "Sexvigintillion"), (1e78, "Quinvigintillion"),
    (1e75, "Quattuorvigintillion"), (1e72, "Trevigintillion"), (1e69, "Duovigintillion"),
    (1e66, "Unvigintillion"),
    (1e63, "Vigintillion"), (1e60, "Novemdecillion"), (1e57, "Octodecillion"),
    (1e54, "Septendecillion"), (1e51, "Sexdecillion"), (1e48, "Quindecillion"),
    (1e45, "Quattuordecillion"), (1e42, "Tredecillion"), (1e39, "Duodecillion"),
    (1e36, "Undecillion"), (1e33, "Decillion"), (1e30, "Nonillion"),
    (1e27, "Octillion"), (1e24, "Septillion"), (1e21, "Sextillion"),
    (1e18, "Quintillion"), (1e15, "Quadrillion"), (1e12, "Trillion"),
    (1e9, "Billion"), (1e6, "Million"),
]

def format_number(n):
    if n != n or n == float('inf') or n == float('-inf'):
        return "∞"
    n = float(n)
    for threshold, name in _SUFFIXES:
        if abs(n) >= threshold:
            return f"{n / threshold:.1f} {name}"
    if abs(n) >= 1e3:
        return f"{n / 1e3:.1f}K"
    return f"{int(n)}"


def draw_rounded_rect(surface, color, rect, radius=12, border=0, border_color=None):
    r = pygame.Rect(rect)
    pygame.draw.rect(surface, color, r, border_radius=radius)
    if border > 0 and border_color:
        pygame.draw.rect(surface, border_color, r, width=border, border_radius=radius)


def draw_cookie(surface, cx, cy, radius, scale=1.0):
    """Draw a cute pixel-art style cookie."""
    r = int(radius * scale)
    # Shadow
    pygame.draw.circle(surface, (0, 0, 0, 40), (cx + 3, cy + 3), r)
    # Main cookie body
    pygame.draw.circle(surface, COOKIE_BROWN, (cx, cy), r)
    # Darker edge ring
    pygame.draw.circle(surface, COOKIE_DARK, (cx, cy), r, 4)
    # Chocolate chips
    chip_positions = [
        (0.3, -0.3), (-0.25, 0.35), (0.0, -0.05),
        (-0.35, -0.2), (0.25, 0.3), (0.0, 0.4),
        (-0.1, -0.4), (0.35, 0.0),
    ]
    for fx, fy in chip_positions:
        cx2 = cx + int(fx * r)
        cy2 = cy + int(fy * r)
        chip_r = max(3, int(r * 0.08))
        pygame.draw.circle(surface, COOKIE_CHIP, (cx2, cy2), chip_r)
        # Tiny highlight
        pygame.draw.circle(surface, (120, 80, 40), (cx2 - 1, cy2 - 1), max(1, chip_r - 2))
    # Shine highlight
    highlight_r = max(4, int(r * 0.18))
    pygame.draw.circle(surface, (220, 170, 100), (cx - int(r * 0.25), cy - int(r * 0.25)), highlight_r)


def spawn_particles(gs, x, y, amount):
    texts = ["+"+format_number(amount)]
    emojis = ["🍪", "⭐", "💛", "✨"]
    for t in texts:
        gs.particles.append({
            "x": x + random.randint(-30, 30),
            "y": y + random.randint(-20, 0),
            "speed": random.uniform(60, 120),
            "alpha": 255,
            "life": 1.2,
            "text": t,
            "is_emoji": False,
        })
    # Scatter a couple emoji particles
    for _ in range(random.randint(1, 3)):
        gs.particles.append({
            "x": x + random.randint(-50, 50),
            "y": y + random.randint(-30, 10),
            "speed": random.uniform(40, 100),
            "alpha": 255,
            "life": 1.0,
            "text": random.choice(emojis),
            "is_emoji": True,
        })


def handle_rainbow_click(gs, mx, my):
    """Handle clicking the ultra-rare rainbow cookie."""
    if gs.rainbow_cookie is None:
        return
    rc = gs.rainbow_cookie
    dx = mx - rc["x"]
    dy = my - rc["y"]
    if dx * dx + dy * dy < 35 * 35:
        if rc["type"] == "mega_click":
            bonus = max(1000, gs.click_power * 100000 * gs.rebirth_multiplier)
            gs.cookies += bonus
            gs.total_cookies += bonus
            gs.lifetime_cookies += bonus
            gs.notification = f"🌈 RAINBOW COOKIE! 100,000x CLICK = +{format_number(bonus)}!!!"
        else:  # mega_production
            bonus = max(1000, gs.cps * 100000)
            gs.cookies += bonus
            gs.total_cookies += bonus
            gs.lifetime_cookies += bonus
            gs.notification = f"🌈 RAINBOW COOKIE! 100,000x PRODUCTION = +{format_number(bonus)}!!!"
        gs.notif_timer = 6.0
        gs.rainbow_cookie = None
        # MASSIVE particle explosion
        for _ in range(30):
            gs.particles.append({
                "x": rc["x"] + random.randint(-60, 60),
                "y": rc["y"] + random.randint(-40, 20),
                "speed": random.uniform(80, 200),
                "alpha": 255,
                "life": 2.5,
                "text": random.choice(["🌈", "💎", "✨", "🦄", "🌟", "💰", "🍪", "⭐"]),
                "is_emoji": True,
            })


def handle_golden_click(gs, mx, my):
    if gs.golden_cookie is None:
        return
    gc = gs.golden_cookie
    dx = mx - gc["x"]
    dy = my - gc["y"]
    if dx * dx + dy * dy < 30 * 30:
        t = gc["type"]
        if t == "x2":
            gs.multiplier = 2.0
            gs.multiplier_timer = 15.0
            gs.notification = "🌟 Golden Cookie: 2x everything for 15s!"
        elif t == "x5":
            gs.multiplier = 5.0
            gs.multiplier_timer = 10.0
            gs.notification = "🌟 Golden Cookie: 5x everything for 10s!"
        elif t == "frenzy":
            gs.multiplier = 7.0
            gs.multiplier_timer = 7.0
            gs.notification = "🌟 FRENZY! 7x everything for 7s!"
        elif t == "bonus":
            bonus = max(100, gs.cps * 60)
            gs.cookies += bonus
            gs.total_cookies += bonus
            gs.notification = f"🌟 Golden Cookie: +{format_number(bonus)} cookies!"
        gs.notif_timer = 4.0
        gs.golden_cookie = None
        # Big particle burst
        for _ in range(8):
            gs.particles.append({
                "x": gc["x"] + random.randint(-40, 40),
                "y": gc["y"] + random.randint(-30, 10),
                "speed": random.uniform(50, 130),
                "alpha": 255,
                "life": 1.5,
                "text": random.choice(["🌟", "⭐", "💰", "🍪"]),
                "is_emoji": True,
            })


# ── Drawing ─────────────────────────────────────────────────────────────
def draw_game(gs):
    screen.fill(BG)

    # ── Left panel: Cookie area ─────────────────────────────────────
    # Title
    title_surf = font_lg.render("Grandma's Clicker", True, TEXT_DARK)
    screen.blit(title_surf, (225 - title_surf.get_width() // 2, 15))

    # Cookie count
    cookie_text = format_number(gs.cookies)
    count_surf = font_xl.render(f"{cookie_text}", True, COOKIE_DARK)
    screen.blit(count_surf, (225 - count_surf.get_width() // 2, 60))
    label_surf = font_sm.render("cookies", True, TEXT_LIGHT)
    screen.blit(label_surf, (225 - label_surf.get_width() // 2, 110))

    # CPS display
    cps_val = gs.cps * gs.multiplier
    cps_text = f"per second: {format_number(cps_val)}"
    cps_surf = font_sm.render(cps_text, True, TEXT_LIGHT)
    screen.blit(cps_surf, (225 - cps_surf.get_width() // 2, 132))

    # Click power
    cp_text = f"per click: {format_number(gs.click_power * gs.multiplier)}"
    cp_surf = font_xs.render(cp_text, True, TEXT_LIGHT)
    screen.blit(cp_surf, (225 - cp_surf.get_width() // 2, 155))

    # Multiplier indicator
    if gs.multiplier_timer > 0:
        mult_text = f"✨ {gs.multiplier:.0f}x MULTIPLIER ({gs.multiplier_timer:.1f}s) ✨"
        mult_surf = font_md.render(mult_text, True, GOLD)
        screen.blit(mult_surf, (225 - mult_surf.get_width() // 2, 175))

    # Main cookie button
    cookie_cx, cookie_cy = 225, 310
    cookie_radius = 90
    draw_cookie(screen, cookie_cx, cookie_cy, cookie_radius, gs.cookie_scale)

    # "Click me!" label under cookie
    click_label = font_xs.render("Click me!", True, TEXT_LIGHT)
    screen.blit(click_label, (225 - click_label.get_width() // 2, 415))

    # Particles
    for p in gs.particles:
        alpha = max(0, min(255, int(p["alpha"])))
        if alpha <= 0:
            continue
        if p["is_emoji"]:
            surf = font_emoji.render(p["text"], True, GOLD)
        else:
            surf = font_md.render(p["text"], True, GOLD)
        surf.set_alpha(alpha)
        screen.blit(surf, (int(p["x"]) - surf.get_width() // 2, int(p["y"]) - surf.get_height() // 2))

    # Rainbow cookie (ultra rare!)
    if gs.rainbow_cookie:
        rc = gs.rainbow_cookie
        t_now = time.time()
        pulse = 1.0 + 0.2 * math.sin(t_now * 6)
        rr = int(30 * pulse)
        # Rainbow color cycling
        hue_shift = (t_now * 3) % 6
        # Convert hue to RGB
        hi = int(hue_shift) % 6
        f = hue_shift - int(hue_shift)
        rainbow_colors = [
            (255, int(255 * f), 0),
            (int(255 * (1 - f)), 255, 0),
            (0, 255, int(255 * f)),
            (0, int(255 * (1 - f)), 255),
            (int(255 * f), 0, 255),
            (255, 0, int(255 * (1 - f))),
        ]
        rc_color = rainbow_colors[hi]
        # Multiple glow rings
        for ring in range(3, 0, -1):
            glow_r = rr * ring * 1.5
            glow_surf = pygame.Surface((int(glow_r * 2), int(glow_r * 2)), pygame.SRCALPHA)
            glow_alpha = max(20, 60 // ring)
            glow_c = (rc_color[0], rc_color[1], rc_color[2], glow_alpha)
            pygame.draw.circle(glow_surf, glow_c, (int(glow_r), int(glow_r)), int(glow_r))
            screen.blit(glow_surf, (rc["x"] - int(glow_r), rc["y"] - int(glow_r)))
        # Cookie body with rainbow outline
        pygame.draw.circle(screen, rc_color, (rc["x"], rc["y"]), rr)
        # Inner white shine
        pygame.draw.circle(screen, (255, 255, 255), (rc["x"] - rr // 4, rc["y"] - rr // 4), rr // 3)
        # Rotating sparkles around it
        for s in range(6):
            angle = t_now * 3 + s * (math.pi / 3)
            sx = rc["x"] + int(math.cos(angle) * (rr + 12))
            sy = rc["y"] + int(math.sin(angle) * (rr + 12))
            spark = font_xs.render("✦", True, rc_color)
            screen.blit(spark, (sx - spark.get_width() // 2, sy - spark.get_height() // 2))
        # Rainbow emoji in center
        rb_emoji = font_md.render("🌈", True, WHITE)
        screen.blit(rb_emoji, (rc["x"] - rb_emoji.get_width() // 2, rc["y"] - rb_emoji.get_height() // 2))
        # Timer countdown text
        timer_txt = font_xs.render(f"{rc['timer']:.1f}s", True, WHITE)
        screen.blit(timer_txt, (rc["x"] - timer_txt.get_width() // 2, rc["y"] + rr + 8))

    # Golden cookie
    if gs.golden_cookie:
        gc = gs.golden_cookie
        pulse = 1.0 + 0.15 * math.sin(time.time() * 5)
        gr = int(25 * pulse)
        # Glow
        glow_surf = pygame.Surface((gr * 4, gr * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 215, 0, 80), (gr * 2, gr * 2), gr * 2)
        screen.blit(glow_surf, (gc["x"] - gr * 2, gc["y"] - gr * 2))
        # Golden cookie body
        pygame.draw.circle(screen, (255, 215, 0), (gc["x"], gc["y"]), gr)
        pygame.draw.circle(screen, (200, 170, 0), (gc["x"], gc["y"]), gr, 3)
        # Sparkle
        star = font_md.render("★", True, WHITE)
        screen.blit(star, (gc["x"] - star.get_width() // 2, gc["y"] - star.get_height() // 2))

    # Grandma quote bubble
    quote_rect = pygame.Rect(30, 450, 390, 60)
    draw_rounded_rect(screen, WHITE, quote_rect, radius=15, border=2, border_color=PANEL_BORDER)
    # Grandma emoji
    g_emoji = font_emoji.render("👵", True, BLACK)
    screen.blit(g_emoji, (40, 455))
    # Quote text (wrap if needed)
    quote_words = gs.quote.split()
    line = ""
    y_off = 458
    for w in quote_words:
        test = line + w + " "
        if font_xs.size(test)[0] > 300:
            qs = font_xs.render(line, True, TEXT_DARK)
            screen.blit(qs, (90, y_off))
            y_off += 18
            line = w + " "
        else:
            line = test
    if line:
        qs = font_xs.render(line.strip(), True, TEXT_DARK)
        screen.blit(qs, (90, y_off))

    # Stats bar at bottom-left
    stats_rect = pygame.Rect(30, 520, 390, 70)
    draw_rounded_rect(screen, PANEL_BG, stats_rect, radius=10, border=1, border_color=PANEL_BORDER)
    stat1 = font_xs.render(f"Total baked: {format_number(gs.total_cookies)}", True, TEXT_DARK)
    stat2 = font_xs.render(f"Total clicks: {format_number(gs.total_clicks)}", True, TEXT_DARK)
    elapsed = int(time.time() - gs.start_time)
    mins, secs = divmod(elapsed, 60)
    hrs, mins = divmod(mins, 60)
    time_str = f"{hrs}h {mins}m {secs}s" if hrs else f"{mins}m {secs}s"
    stat3 = font_xs.render(f"Session: {time_str}", True, TEXT_DARK)
    rebirth_info = f"Rebirths: {gs.rebirths}  (x{format_number(gs.rebirth_multiplier)} perm)"
    stat4 = font_xs.render(rebirth_info, True, (180, 100, 200))
    lifetime_txt = font_xs.render(f"Lifetime: {format_number(gs.lifetime_cookies)}", True, TEXT_LIGHT)
    screen.blit(stat1, (40, 524))
    screen.blit(stat2, (200, 524))
    screen.blit(stat3, (40, 542))
    screen.blit(stat4, (200, 542))
    screen.blit(lifetime_txt, (40, 560))

    # Rebirth button
    mx, my = pygame.mouse.get_pos()
    rebirth_cost = gs.get_rebirth_cost()
    can_rebirth = gs.can_rebirth()
    rebirth_rect = pygame.Rect(30, 598, 185, 38)
    rebirth_hover = rebirth_rect.collidepoint(mx, my)
    rb_col = BTN_PURPLE_H if (can_rebirth and rebirth_hover) else BTN_PURPLE if can_rebirth else (120, 120, 120)
    draw_rounded_rect(screen, rb_col, rebirth_rect, radius=8)
    rb_label = f"🔄 Rebirth ({format_number(rebirth_cost)})"
    rb_txt = font_sm.render(rb_label, True, WHITE)
    screen.blit(rb_txt, (rebirth_rect.centerx - rb_txt.get_width() // 2, rebirth_rect.centery - rb_txt.get_height() // 2))

    # Save button
    save_rect = pygame.Rect(225, 598, 100, 38)
    save_hover = save_rect.collidepoint(mx, my)
    draw_rounded_rect(screen, BTN_GREEN_H if save_hover else BTN_GREEN, save_rect, radius=8)
    save_txt = font_sm.render("💾 Save", True, WHITE)
    screen.blit(save_txt, (save_rect.centerx - save_txt.get_width() // 2, save_rect.centery - save_txt.get_height() // 2))

    # ── Right panel: Shop ───────────────────────────────────────────
    panel_rect = pygame.Rect(460, 0, 440, HEIGHT)
    draw_rounded_rect(screen, PANEL_BG, panel_rect, radius=0, border=2, border_color=PANEL_BORDER)

    shop_title = font_lg.render("🛒 Shop", True, TEXT_DARK)
    screen.blit(shop_title, (480, 12))

    # Upgrade buttons (scrollable area)
    clip_rect = pygame.Rect(465, 55, 425, HEIGHT - 65)
    # We don't actually clip for simplicity; just offset drawing
    y = 60 + gs.scroll_offset
    upgrade_rects = []
    for i, up in enumerate(UPGRADES):
        btn_h = 65
        btn_rect = pygame.Rect(470, y, 415, btn_h)
        cost = gs.get_cost(i)
        can_afford = gs.cookies >= cost
        hover = btn_rect.collidepoint(mx, my) and clip_rect.collidepoint(mx, my)

        if y + btn_h > 45 and y < HEIGHT:  # visible check
            # Background
            if can_afford:
                col = up["color_h"] if hover else up["color"]
            else:
                col = (160, 160, 160)
            draw_rounded_rect(screen, col, btn_rect, radius=10)

            # Owned count badge
            if gs.owned[i] > 0:
                badge_text = str(gs.owned[i])
                badge_surf = font_md.render(badge_text, True, WHITE)
                badge_w = max(28, badge_surf.get_width() + 12)
                badge_rect = pygame.Rect(btn_rect.right - badge_w - 8, btn_rect.y + 5, badge_w, 26)
                draw_rounded_rect(screen, (0, 0, 0, 100), badge_rect, radius=13)
                pygame.draw.rect(screen, (255, 255, 255, 60), badge_rect, width=1, border_radius=13)
                screen.blit(badge_surf, (badge_rect.centerx - badge_surf.get_width() // 2, badge_rect.centery - badge_surf.get_height() // 2))

            # Emoji
            emoji_surf = font_emoji.render(up["emoji"], True, WHITE)
            screen.blit(emoji_surf, (480, y + 10))

            # Name
            name_surf = font_md.render(up["name"], True, WHITE)
            screen.blit(name_surf, (525, y + 6))

            # Description
            desc_surf = font_xs.render(up["desc"], True, (240, 240, 240))
            screen.blit(desc_surf, (525, y + 30))

            # Cost
            cost_str = f"Cost: {format_number(cost)}"
            cost_col = (255, 255, 200) if can_afford else (255, 180, 180)
            cost_surf = font_sm.render(cost_str, True, cost_col)
            screen.blit(cost_surf, (525, y + 46))

        upgrade_rects.append((btn_rect, i))
        y += btn_h + 6

    # Notification popup
    if gs.notif_timer > 0 and gs.notification:
        alpha = min(255, int(gs.notif_timer * 200))
        notif_surf = font_md.render(gs.notification, True, WHITE)
        nw = notif_surf.get_width() + 30
        nh = 40
        notif_bg = pygame.Surface((nw, nh), pygame.SRCALPHA)
        pygame.draw.rect(notif_bg, (60, 40, 20, min(220, alpha)), (0, 0, nw, nh), border_radius=12)
        notif_surf.set_alpha(alpha)
        nx = WIDTH // 2 - nw // 2
        ny = 10
        screen.blit(notif_bg, (nx, ny))
        screen.blit(notif_surf, (nx + 15, ny + 8))

    pygame.display.flip()
    return upgrade_rects


# ── Dev Panel Drawing ───────────────────────────────────────────────────
DEV_BUTTONS = [
    ("Give 1,000",        "give_1k"),
    ("Give 1,000,000",    "give_1m"),
    ("Give 1,000,000,000","give_1b"),
    ("Give 1 Trillion",   "give_1t"),
    ("Give 1 Quadrillion", "give_1q"),
    ("Spawn Golden",      "spawn_golden"),
    ("Spawn Rainbow",     "spawn_rainbow"),
    ("Max All Upgrades",  "max_upgrades"),
    ("+10 Rebirths",      "add_rebirths"),
    ("100x Multiplier 60s", "big_mult"),
    ("Reset Progress",    "reset"),
    ("↩ Undo Last Action",  "undo"),
]

def draw_dev_panel(gs):
    """Draw the secret dev panel overlay."""
    if not gs.dev_panel_open:
        return []
    # Darken background
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    # Panel
    pw, ph = 360, 500
    px = WIDTH // 2 - pw // 2
    py = HEIGHT // 2 - ph // 2
    panel_rect = pygame.Rect(px, py, pw, ph)
    draw_rounded_rect(screen, (30, 30, 40), panel_rect, radius=16, border=3, border_color=(255, 60, 60))

    # Title
    title = font_lg.render("🔧 DEV MODE", True, (255, 80, 80))
    screen.blit(title, (px + pw // 2 - title.get_width() // 2, py + 10))

    # Close button
    close_rect = pygame.Rect(px + pw - 40, py + 8, 30, 30)
    draw_rounded_rect(screen, (200, 50, 50), close_rect, radius=8)
    x_txt = font_md.render("X", True, WHITE)
    screen.blit(x_txt, (close_rect.centerx - x_txt.get_width() // 2, close_rect.centery - x_txt.get_height() // 2))

    # Buttons
    mx, my = pygame.mouse.get_pos()
    btn_rects = []
    by = py + 50
    for label, action in DEV_BUTTONS:
        btn_rect = pygame.Rect(px + 20, by, pw - 40, 34)
        hover = btn_rect.collidepoint(mx, my)
        if action == "reset":
            col = (180, 40, 40) if not hover else (220, 60, 60)
        elif action == "undo":
            has_undo = len(gs.dev_undo_stack) > 0
            if has_undo:
                col = (180, 160, 40) if not hover else (210, 190, 60)
            else:
                col = (80, 80, 80)  # greyed out
        else:
            col = (70, 70, 90) if not hover else (100, 100, 130)
        draw_rounded_rect(screen, col, btn_rect, radius=8)
        # Add undo count to label
        display_label = label
        if action == "undo" and len(gs.dev_undo_stack) > 0:
            display_label = f"{label} ({len(gs.dev_undo_stack)})"
        lbl = font_sm.render(display_label, True, WHITE)
        screen.blit(lbl, (btn_rect.centerx - lbl.get_width() // 2, btn_rect.centery - lbl.get_height() // 2))
        btn_rects.append((btn_rect, action))
        by += 38

    # Footer
    foot = font_xs.render("Type 'cookies12346' to toggle", True, (120, 120, 140))
    screen.blit(foot, (px + pw // 2 - foot.get_width() // 2, py + ph - 22))

    pygame.display.flip()
    return [(close_rect, "close")] + btn_rects


def handle_dev_action(gs, action):
    """Execute a dev panel action."""
    if action == "close":
        gs.dev_panel_open = False
        return
    if action == "undo":
        if gs.dev_undo_stack:
            snap = gs.dev_undo_stack.pop()
            gs._restore(snap)
            gs.notification = f"↩ DEV: Undone! ({len(gs.dev_undo_stack)} left)"
            gs.notif_timer = 2.0
        else:
            gs.notification = "↩ DEV: Nothing to undo!"
            gs.notif_timer = 2.0
        return
    # Save snapshot before any action (for undo)
    gs.dev_undo_stack.append(gs._snapshot())
    # Cap undo history at 20
    if len(gs.dev_undo_stack) > 20:
        gs.dev_undo_stack.pop(0)
    if action == "give_1k":
        gs.cookies += 1_000
        gs.total_cookies += 1_000
        gs.lifetime_cookies += 1_000
        gs.notification = "🔧 DEV: +1,000 cookies"
        gs.notif_timer = 2.0
    elif action == "give_1m":
        gs.cookies += 1_000_000
        gs.total_cookies += 1_000_000
        gs.lifetime_cookies += 1_000_000
        gs.notification = "🔧 DEV: +1,000,000 cookies"
        gs.notif_timer = 2.0
    elif action == "give_1b":
        gs.cookies += 1_000_000_000
        gs.total_cookies += 1_000_000_000
        gs.lifetime_cookies += 1_000_000_000
        gs.notification = "🔧 DEV: +1,000,000,000 cookies"
        gs.notif_timer = 2.0
    elif action == "give_1t":
        gs.cookies += 1_000_000_000_000
        gs.total_cookies += 1_000_000_000_000
        gs.lifetime_cookies += 1_000_000_000_000
        gs.notification = "🔧 DEV: +1 Trillion cookies"
        gs.notif_timer = 2.0
    elif action == "give_1q":
        gs.cookies += 1_000_000_000_000_000
        gs.total_cookies += 1_000_000_000_000_000
        gs.lifetime_cookies += 1_000_000_000_000_000
        gs.notification = "🔧 DEV: +1 Quadrillion cookies"
        gs.notif_timer = 2.0
    elif action == "spawn_golden":
        gx = random.randint(50, 400)
        gy = random.randint(100, 500)
        gs.golden_cookie = {"x": gx, "y": gy, "timer": 30.0, "type": random.choice(["x2", "x5", "frenzy", "bonus"])}
        gs.notification = "🔧 DEV: Golden cookie spawned!"
        gs.notif_timer = 2.0
    elif action == "spawn_rainbow":
        rx = random.randint(60, 390)
        ry = random.randint(120, 420)
        rtype = random.choice(["mega_click", "mega_production"])
        gs.rainbow_cookie = {"x": rx, "y": ry, "timer": 30.0, "type": rtype}
        gs.notification = "🔧 DEV: Rainbow cookie spawned!"
        gs.notif_timer = 2.0
    elif action == "max_upgrades":
        for i in range(len(UPGRADES)):
            gs.owned[i] = max(gs.owned[i], 100)
        # Recalculate click_power and cps
        gs.click_power = 1
        gs.cps = 0.0
        for i, up in enumerate(UPGRADES):
            gs.click_power += up["click_bonus"] * gs.owned[i]
            gs.cps += up["cps_bonus"] * gs.owned[i]
        gs.notification = "🔧 DEV: All upgrades set to 100!"
        gs.notif_timer = 2.0
    elif action == "add_rebirths":
        gs.rebirths += 10
        gs.rebirth_multiplier = min(2.0 ** min(gs.rebirths, 1000), 1e200)
        gs.notification = f"🔧 DEV: +10 rebirths! Now {format_number(gs.rebirth_multiplier)}x"
        gs.notif_timer = 2.0
    elif action == "big_mult":
        gs.multiplier = 100.0
        gs.multiplier_timer = 60.0
        gs.notification = "🔧 DEV: 100x multiplier for 60s!"
        gs.notif_timer = 2.0
    elif action == "reset":
        undo_stack = gs.dev_undo_stack  # preserve undo stack
        gs.__init__()
        gs.notification = "🔧 DEV: Progress reset!"
        gs.notif_timer = 2.0
        gs.dev_mode = True
        gs.dev_panel_open = True
        gs.dev_undo_stack = undo_stack


# ── Main Loop ───────────────────────────────────────────────────────────
def main():
    gs = GameState()
    gs.load()
    gs.start_time = time.time()

    auto_save_timer = 0
    running = True
    cookie_cx, cookie_cy, cookie_radius = 225, 310, 90

    while running:
        dt = clock.tick(60) / 1000.0
        auto_save_timer += dt

        # Auto-save every 30 seconds
        if auto_save_timer >= 30:
            gs.save()
            auto_save_timer = 0

        upgrade_rects = draw_game(gs)

        # Draw dev panel on top if open
        dev_btn_rects = []
        if gs.dev_panel_open:
            dev_btn_rects = draw_dev_panel(gs)

        gs.update(dt)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                gs.save()
                pygame.quit()
                sys.exit()

            # Dev panel clicks take priority
            if gs.dev_panel_open and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                clicked_dev = False
                for btn_rect, action in dev_btn_rects:
                    if btn_rect.collidepoint(mx, my):
                        handle_dev_action(gs, action)
                        clicked_dev = True
                        break
                if clicked_dev:
                    continue
                # Click outside panel closes it
                pw, ph = 360, 500
                px = WIDTH // 2 - pw // 2
                py = HEIGHT // 2 - ph // 2
                panel_rect = pygame.Rect(px, py, pw, ph)
                if not panel_rect.collidepoint(mx, my):
                    gs.dev_panel_open = False
                continue

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

                if event.button == 1:  # Left click
                    # Check cookie click
                    dx = mx - cookie_cx
                    dy = my - cookie_cy
                    if dx * dx + dy * dy < cookie_radius * cookie_radius:
                        amount = gs.click()
                        gs.cookie_scale = 0.85
                        gs.cookie_target_scale = 1.0
                        spawn_particles(gs, mx, my, amount)
                        play_click_sfx()

                    # Check rainbow cookie
                    had_rainbow = gs.rainbow_cookie is not None
                    handle_rainbow_click(gs, mx, my)
                    if had_rainbow and gs.rainbow_cookie is None:
                        play_sfx("rainbow")

                    # Check golden cookie
                    had_golden = gs.golden_cookie is not None
                    handle_golden_click(gs, mx, my)
                    if had_golden and gs.golden_cookie is None:
                        play_sfx("golden")

                    # Check upgrade buttons
                    for btn_rect, idx in upgrade_rects:
                        if btn_rect.collidepoint(mx, my):
                            if gs.buy(idx):
                                gs.notification = f"Bought {UPGRADES[idx]['name']}!"
                                gs.notif_timer = 2.0
                                play_sfx("buy")
                            else:
                                play_sfx("fail")

                    # Rebirth button
                    rebirth_rect = pygame.Rect(30, 598, 185, 38)
                    if rebirth_rect.collidepoint(mx, my):
                        if gs.rebirth():
                            gs.notification = f"🔄 REBIRTH #{gs.rebirths}! Permanent {format_number(gs.rebirth_multiplier)}x multiplier!"
                            gs.notif_timer = 5.0
                            play_sfx("rebirth")
                            # Epic particle burst
                            for _ in range(20):
                                gs.particles.append({
                                    "x": 225 + random.randint(-100, 100),
                                    "y": 310 + random.randint(-80, 40),
                                    "speed": random.uniform(60, 150),
                                    "alpha": 255,
                                    "life": 2.0,
                                    "text": random.choice(["🔄", "⭐", "✨", "🌟", "💎", "👵", "🍪"]),
                                    "is_emoji": True,
                                })
                        else:
                            gs.notification = f"Need {format_number(gs.get_rebirth_cost())} cookies to rebirth!"
                            gs.notif_timer = 2.0
                            play_sfx("fail")

                    # Save button
                    save_rect = pygame.Rect(225, 598, 100, 38)
                    if save_rect.collidepoint(mx, my):
                        gs.save()
                        gs.notification = "💾 Game saved!"
                        gs.notif_timer = 2.0
                        play_sfx("save")

                # Scroll in shop (only when mouse is over shop panel)
                elif event.button == 4 and mx >= 460:  # Scroll up
                    gs.scroll_offset = min(0, gs.scroll_offset + 40)
                elif event.button == 5 and mx >= 460:  # Scroll down
                    max_scroll = min(0, -(len(UPGRADES) * 71 - (HEIGHT - 70)))
                    gs.scroll_offset = max(max_scroll, gs.scroll_offset - 40)

            elif event.type == pygame.MOUSEWHEEL:
                if mx >= 460:  # Only scroll when mouse is over shop panel
                    if event.y > 0:
                        gs.scroll_offset = min(0, gs.scroll_offset + 40)
                    elif event.y < 0:
                        max_scroll = min(0, -(len(UPGRADES) * 71 - (HEIGHT - 70)))
                        gs.scroll_offset = max(max_scroll, gs.scroll_offset - 40)

            elif event.type == pygame.KEYDOWN:
                # Dev code input tracking
                key_name = event.unicode.lower() if event.unicode else ""
                if key_name and key_name.isalnum():
                    gs.dev_code_buffer += key_name
                    # Keep buffer trimmed to code length
                    if len(gs.dev_code_buffer) > len(gs.dev_code):
                        gs.dev_code_buffer = gs.dev_code_buffer[-len(gs.dev_code):]
                    # Check for match
                    if gs.dev_code_buffer == gs.dev_code:
                        gs.dev_mode = True
                        gs.dev_panel_open = not gs.dev_panel_open
                        gs.dev_code_buffer = ""
                        if gs.dev_panel_open:
                            gs.notification = "🔧 DEV MODE ACTIVATED!"
                        else:
                            gs.notification = "🔧 Dev panel closed"
                        gs.notif_timer = 2.0

                if event.key == pygame.K_s and not gs.dev_panel_open:
                    gs.save()
                    gs.notification = "💾 Game saved!"
                    gs.notif_timer = 2.0
                    play_sfx("save")


if __name__ == "__main__":
    main()
