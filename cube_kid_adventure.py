"""
Diary of a Mob: A Minecraft Adventure
Inspired by Cube Kid (Diary of an 8-Bit Warrior / Wimpy Villager),
Diary of a Minecraft Wolf, and Diary of a Minecraft Kitten.
"""
import pygame
import sys
import math
import random
import json
import os
import time

pygame.init()
pygame.mixer.init()

# ── CONSTANTS ──────────────────────────────────────────────────────────
WIDTH, HEIGHT = 900, 640
FPS = 60
SAVE_FILE = "mob_adventure_save.json"

# Colours (Minecraft palette inspired)
BLACK   = (0, 0, 0)
WHITE   = (255, 255, 255)
GRAY    = (180, 180, 180)
DKGRAY  = (60, 60, 60)
GREEN   = (80, 200, 80)
DKGREEN = (34, 120, 34)
BROWN   = (139, 90, 43)
DKBROWN = (90, 55, 25)
SKYBLUE = (135, 206, 235)
NIGHTBLUE = (20, 20, 60)
SAND    = (210, 180, 140)
RED     = (200, 50, 50)
ORANGE  = (220, 140, 40)
YELLOW  = (240, 220, 60)
BLUE    = (60, 100, 220)
PURPLE  = (140, 60, 200)
PINK    = (220, 120, 180)
CYAN    = (60, 200, 200)
GOLD    = (255, 215, 0)
STONE   = (128, 128, 128)
WOOD    = (160, 110, 60)
LEAF    = (50, 160, 50)
WATER   = (60, 130, 230)
LAVA    = (220, 80, 20)

# ── PIXEL ART DRAWING HELPERS ─────────────────────────────────────────
def draw_pixel_block(surf, x, y, size, colour, shade=True):
    """Draw a Minecraft-style pixel block."""
    pygame.draw.rect(surf, colour, (x, y, size, size))
    if shade:
        lighter = tuple(min(255, c + 30) for c in colour)
        darker  = tuple(max(0, c - 40) for c in colour)
        pygame.draw.line(surf, lighter, (x, y), (x + size - 1, y))
        pygame.draw.line(surf, lighter, (x, y), (x, y + size - 1))
        pygame.draw.line(surf, darker, (x + size - 1, y), (x + size - 1, y + size - 1))
        pygame.draw.line(surf, darker, (x, y + size - 1), (x + size - 1, y + size - 1))

def draw_cat(surf, x, y, scale=1):
    """Draw a pixel-art Minecraft cat."""
    s = int(4 * scale)
    # Body
    body_col = (230, 160, 60)
    for bx in range(5):
        for by in range(3):
            draw_pixel_block(surf, x + bx * s, y + 2 * s + by * s, s, body_col)
    # Head
    head_col = (240, 180, 80)
    for hx in range(4):
        for hy in range(3):
            draw_pixel_block(surf, x + hx * s, y + hy * s, s, head_col)
    # Ears
    draw_pixel_block(surf, x, y - s, s, (200, 140, 50))
    draw_pixel_block(surf, x + 3 * s, y - s, s, (200, 140, 50))
    # Eyes
    pygame.draw.rect(surf, (50, 200, 50), (x + s, y + s, s // 2, s // 2))
    pygame.draw.rect(surf, (50, 200, 50), (x + 2 * s + s // 2, y + s, s // 2, s // 2))
    # Nose
    pygame.draw.rect(surf, PINK, (x + int(1.5 * s), y + int(1.5 * s), s // 2, s // 2))
    # Tail
    for t in range(3):
        draw_pixel_block(surf, x + 5 * s, y + (2 + t) * s, s, (200, 130, 40))
    # Legs
    for lx in [0, 1, 3, 4]:
        draw_pixel_block(surf, x + lx * s, y + 5 * s, s, body_col)

def draw_wolf(surf, x, y, scale=1):
    """Draw a pixel-art Minecraft wolf."""
    s = int(4 * scale)
    body_col = (200, 200, 200)
    dark = (160, 160, 160)
    # Body
    for bx in range(6):
        for by in range(3):
            draw_pixel_block(surf, x + bx * s, y + 2 * s + by * s, s, body_col)
    # Head
    for hx in range(4):
        for hy in range(3):
            draw_pixel_block(surf, x + hx * s, y + hy * s, s, body_col)
    # Ears
    draw_pixel_block(surf, x, y - s, s, dark)
    draw_pixel_block(surf, x + 3 * s, y - s, s, dark)
    # Snout
    draw_pixel_block(surf, x + s, y + 2 * s, s * 2, s, shade=False)
    pygame.draw.rect(surf, (220, 220, 220), (x + s, y + 2 * s, s * 2, s))
    # Eyes
    pygame.draw.rect(surf, RED, (x + s, y + s, s // 2, s // 2))
    pygame.draw.rect(surf, RED, (x + 2 * s + s // 2, y + s, s // 2, s // 2))
    # Nose
    pygame.draw.rect(surf, BLACK, (x + int(1.5 * s), y + 2 * s, s // 2, s // 2))
    # Tail
    for t in range(4):
        draw_pixel_block(surf, x + 6 * s, y + (1 + t) * s, s, dark)
    # Legs
    for lx in [0, 1, 4, 5]:
        draw_pixel_block(surf, x + lx * s, y + 5 * s, s, body_col)

def draw_bunny(surf, x, y, scale=1):
    """Draw a pixel-art Minecraft bunny."""
    s = int(4 * scale)
    body_col = (230, 220, 200)
    ear_col  = (210, 190, 170)
    # Body
    for bx in range(4):
        for by in range(3):
            draw_pixel_block(surf, x + bx * s, y + 3 * s + by * s, s, body_col)
    # Head
    for hx in range(3):
        for hy in range(2):
            draw_pixel_block(surf, x + hx * s, y + s + hy * s, s, body_col)
    # Long ears
    for ey in range(3):
        draw_pixel_block(surf, x, y - ey * s, s, ear_col)
        draw_pixel_block(surf, x + 2 * s, y - ey * s, s, ear_col)
    # Inner ear pink
    pygame.draw.rect(surf, PINK, (x + 1, y - s + 1, s - 2, s * 2 - 2))
    pygame.draw.rect(surf, PINK, (x + 2 * s + 1, y - s + 1, s - 2, s * 2 - 2))
    # Eyes
    pygame.draw.rect(surf, RED, (x + s // 2, y + int(1.5 * s), s // 2, s // 2))
    pygame.draw.rect(surf, RED, (x + 2 * s, y + int(1.5 * s), s // 2, s // 2))
    # Nose
    pygame.draw.rect(surf, PINK, (x + s, y + 2 * s, s // 2, s // 2))
    # Tail poof
    draw_pixel_block(surf, x + 4 * s, y + 4 * s, s, WHITE)
    # Legs
    for lx in [0, 1, 2, 3]:
        draw_pixel_block(surf, x + lx * s, y + 6 * s, s, body_col)

def draw_human(surf, x, y, scale=1, mob_type="cat"):
    """Draw a pixel-art Minecraft villager/human — skin tint from original mob."""
    s = int(4 * scale)
    if mob_type == "cat":
        skin = (230, 180, 120)
        hair = (160, 100, 40)
        shirt = (230, 160, 60)
    elif mob_type == "wolf":
        skin = (210, 180, 150)
        hair = (180, 180, 180)
        shirt = (100, 100, 200)
    else:
        skin = (240, 210, 180)
        hair = (200, 170, 130)
        shirt = (80, 180, 80)
    # Hair
    for hx in range(3):
        draw_pixel_block(surf, x + hx * s, y, s, hair)
    draw_pixel_block(surf, x, y + s, s, hair)
    draw_pixel_block(surf, x + 2 * s, y + s, s, hair)
    # Face
    for fx in range(3):
        for fy in range(3):
            draw_pixel_block(surf, x + fx * s, y + s + fy * s, s, skin)
    # Eyes
    pygame.draw.rect(surf, (60, 140, 60), (x + s // 2, y + 2 * s, s // 2, s // 2))
    pygame.draw.rect(surf, (60, 140, 60), (x + 2 * s, y + 2 * s, s // 2, s // 2))
    # Mouth
    pygame.draw.rect(surf, (180, 120, 80), (x + s, y + 3 * s, s, s // 3))
    # Body / shirt
    for bx in range(3):
        for by in range(4):
            draw_pixel_block(surf, x + bx * s, y + 4 * s + by * s, s, shirt)
    # Arms
    for ay in range(3):
        draw_pixel_block(surf, x - s, y + 4 * s + ay * s, s, skin)
        draw_pixel_block(surf, x + 3 * s, y + 4 * s + ay * s, s, skin)
    # Legs
    pants = (80, 60, 40)
    for ly in range(2):
        draw_pixel_block(surf, x + s // 2, y + 8 * s + ly * s, s, pants)
        draw_pixel_block(surf, x + int(1.5 * s), y + 8 * s + ly * s, s, pants)

def draw_chest(surf, x, y, w, h, opened=False):
    """Draw a Minecraft chest."""
    # Base
    pygame.draw.rect(surf, DKBROWN, (x, y + h // 3, w, h * 2 // 3))
    pygame.draw.rect(surf, BROWN, (x + 2, y + h // 3 + 2, w - 4, h * 2 // 3 - 4))
    # Lid
    if opened:
        pygame.draw.rect(surf, DKBROWN, (x, y - h // 3, w, h // 3))
        pygame.draw.rect(surf, BROWN, (x + 2, y - h // 3 + 2, w - 4, h // 3 - 4))
    else:
        pygame.draw.rect(surf, DKBROWN, (x, y, w, h // 3))
        pygame.draw.rect(surf, BROWN, (x + 2, y + 2, w - 4, h // 3 - 4))
    # Lock
    lock_x = x + w // 2 - 4
    lock_y = y + h // 3 - 4 if not opened else y + h // 3 - 4
    pygame.draw.rect(surf, GOLD, (lock_x, lock_y, 8, 8))

def draw_potion(surf, x, y, h=40):
    """Draw a glowing potion bottle."""
    # Bottle neck
    pygame.draw.rect(surf, (200, 200, 220), (x + 8, y, 8, h // 4))
    # Cork
    pygame.draw.rect(surf, BROWN, (x + 7, y - 3, 10, 5))
    # Bottle body
    pygame.draw.ellipse(surf, (100, 60, 200), (x, y + h // 4, 24, h * 3 // 4))
    # Glow
    pygame.draw.ellipse(surf, (180, 120, 255), (x + 4, y + h // 4 + 4, 16, h * 3 // 4 - 8))
    # Sparkles
    for _ in range(3):
        sx = x + random.randint(4, 20)
        sy = y + h // 4 + random.randint(4, h * 3 // 4 - 8)
        pygame.draw.circle(surf, WHITE, (sx, sy), 1)

def draw_house_exterior(surf, x, y, w, h):
    """Draw the abandoned house from outside."""
    # Walls
    for bx in range(0, w, 12):
        for by in range(h // 3, h, 12):
            col = random.choice([(STONE[0] + random.randint(-10, 10),
                                   STONE[1] + random.randint(-10, 10),
                                   STONE[2] + random.randint(-10, 10))])
            col = tuple(max(0, min(255, c)) for c in col)
            pygame.draw.rect(surf, col, (x + bx, y + by, 11, 11))
    # Roof
    for i in range(w // 2):
        pygame.draw.rect(surf, DKBROWN, (x + w // 2 - i, y + h // 3 - i // 2, i * 2, 4))
    # Door
    dw, dh = 30, 50
    dx = x + w // 2 - dw // 2
    dy = y + h - dh
    pygame.draw.rect(surf, (60, 40, 20), (dx, dy, dw, dh))
    pygame.draw.circle(surf, GOLD, (dx + dw - 6, dy + dh // 2), 3)
    # Windows (dark / broken)
    pygame.draw.rect(surf, (20, 20, 40), (x + 15, y + h // 3 + 15, 25, 20))
    pygame.draw.rect(surf, (20, 20, 40), (x + w - 40, y + h // 3 + 15, 25, 20))
    # Cracks
    pygame.draw.line(surf, DKGRAY, (x + 10, y + h // 2), (x + 30, y + h // 2 + 20), 2)
    pygame.draw.line(surf, DKGRAY, (x + w - 20, y + h * 2 // 3), (x + w - 5, y + h - 10), 2)

# ── STORY / QUEST DATA ────────────────────────────────────────────────
CHAPTERS = [
    {
        "id": "thirsty",
        "title": "Chapter 1: A Thirsty Beginning",
        "scenes": [
            {
                "id": "start",
                "text": [
                    "The sun beats down on the dry plains.",
                    "You haven't had water in hours.",
                    "Your throat is parched and your paws ache.",
                    "",
                    "In the distance, you spot an old, abandoned house.",
                    "Maybe... there's water inside?",
                ],
                "choices": [
                    ("Approach the abandoned house", "approach_house"),
                    ("Look around the plains first", "look_plains"),
                ],
                "bg": "plains",
            },
            {
                "id": "look_plains",
                "text": [
                    "You scan the horizon. Nothing but dry grass",
                    "and a few dead trees. No water anywhere.",
                    "",
                    "A zombie groans somewhere far away...",
                    "The abandoned house is your only hope.",
                ],
                "choices": [
                    ("Head to the house", "approach_house"),
                ],
                "bg": "plains",
            },
            {
                "id": "approach_house",
                "text": [
                    "You creep towards the crumbling building.",
                    "Cobwebs cover the doorway. The wooden door",
                    "hangs off one hinge, creaking in the wind.",
                    "",
                    "Through the dark doorway, you can see",
                    "dusty furniture and... is that a chest?",
                ],
                "choices": [
                    ("Enter the house", "enter_house"),
                    ("Peek through the window first", "peek_window"),
                ],
                "bg": "house_exterior",
            },
            {
                "id": "peek_window",
                "text": [
                    "You peer through the cracked window.",
                    "Inside you see: a broken table, old bookshelves,",
                    "and in the corner... a wooden chest!",
                    "",
                    "The house seems empty. No mobs inside.",
                    "It should be safe to enter.",
                ],
                "choices": [
                    ("Enter through the door", "enter_house"),
                ],
                "bg": "house_exterior",
            },
            {
                "id": "enter_house",
                "text": [
                    "You step inside. Dust swirls around your paws.",
                    "Old bookshelves line the walls — titles include:",
                    "  'Diary of a Minecraft Wolf'",
                    "  'Diary of a Minecraft Kitten'",
                    "  'An 8-Bit Warrior's Journal'",
                    "",
                    "But your eyes are drawn to the CHEST",
                    "sitting in the corner, slightly glowing...",
                ],
                "choices": [
                    ("Open the chest", "open_chest"),
                    ("Read one of the books first", "read_books"),
                    ("Search for water elsewhere", "search_water"),
                ],
                "bg": "house_interior",
            },
            {
                "id": "read_books",
                "text": [
                    "You flip open 'Diary of a Minecraft Wolf'.",
                    "It tells of a wolf who befriended a player",
                    "and went on incredible adventures together.",
                    "",
                    "'Diary of a Minecraft Kitten' describes a",
                    "tiny kitten who survived the Overworld alone.",
                    "",
                    "The last book speaks of a villager named Runt",
                    "who dreamed of becoming a warrior...",
                    "",
                    "These stories fill you with DETERMINATION.",
                    "Maybe you can have adventures like them!",
                ],
                "choices": [
                    ("Now open the chest", "open_chest"),
                ],
                "bg": "house_interior",
                "gain_item": "Ancient Knowledge",
            },
            {
                "id": "search_water",
                "text": [
                    "You rummage through the old cabinets.",
                    "Empty bottles, cobwebs, a rusty bucket...",
                    "",
                    "Wait — there IS an old water bucket here!",
                    "You lap up the stale water gratefully.",
                    "It's not great, but it stops the thirst.",
                    "",
                    "Now about that glowing chest...",
                ],
                "choices": [
                    ("Open the chest", "open_chest"),
                ],
                "bg": "house_interior",
                "gain_item": "Stale Water",
                "heal": 20,
            },
            {
                "id": "open_chest",
                "text": [
                    "You push open the heavy lid. CREAK!",
                    "",
                    "Inside, resting on purple velvet, is a",
                    "shimmering potion that glows with magic.",
                    "",
                    "The label reads:",
                    "  'POTION OF HUMAN FORM'",
                    "  'Transforms any mob into a human.'",
                    "  'Warning: effects are permanent.'",
                    "",
                    "Your heart races. With this potion,",
                    "you could walk among villagers,",
                    "learn to fight, become a WARRIOR...",
                    "Just like in those books!",
                ],
                "choices": [
                    ("Drink the potion!", "drink_potion"),
                    ("Think about it first...", "hesitate"),
                ],
                "bg": "chest_room",
                "gain_item": "Potion of Human Form",
            },
            {
                "id": "hesitate",
                "text": [
                    "You stare at the glowing purple liquid.",
                    "'Permanent' is a scary word...",
                    "",
                    "But then you think about your life as a mob.",
                    "Running from players, hiding from wolves",
                    "(if you're the cat or bunny), scrounging for food.",
                    "",
                    "This potion could change EVERYTHING.",
                    "You could have a real adventure.",
                    "You could be like Runt from the books...",
                ],
                "choices": [
                    ("Drink it. No turning back.", "drink_potion"),
                ],
                "bg": "chest_room",
            },
            {
                "id": "drink_potion",
                "text": [
                    "You tip the bottle and drink deep.",
                    "",
                    "The world SPINS. Colours blur together.",
                    "Your paws tingle... stretch... change...",
                    "",
                    "When the dizziness fades, you look down.",
                    "HANDS. You have HANDS!",
                    "You're standing on two legs!",
                    "",
                    "You catch your reflection in a broken mirror:",
                    "A young human stares back at you.",
                    "But your eyes still have that mob spark.",
                    "",
                    "You are HUMAN now. The adventure begins!",
                ],
                "choices": [
                    ("Step outside into the world", "chapter2_start"),
                ],
                "bg": "transformation",
                "transform": True,
            },
        ],
    },
    {
        "id": "village",
        "title": "Chapter 2: The Village",
        "scenes": [
            {
                "id": "chapter2_start",
                "text": [
                    "You step out of the house on wobbly human legs.",
                    "The world looks different at this height!",
                    "",
                    "To the EAST, smoke rises from chimneys —",
                    "a village! Maybe they'll take you in.",
                    "",
                    "To the WEST, a dark forest looms.",
                    "Strange sounds echo from within...",
                    "",
                    "To the NORTH, mountains scrape the sky.",
                ],
                "choices": [
                    ("Head to the village (East)", "village_gate"),
                    ("Explore the dark forest (West)", "dark_forest"),
                    ("Climb towards the mountains (North)", "mountain_path"),
                ],
                "bg": "overworld",
            },
            {
                "id": "village_gate",
                "text": [
                    "You approach the village. An iron golem",
                    "guards the entrance, watching you carefully.",
                    "",
                    "A villager in brown robes approaches.",
                    "'Hmm? A stranger? You don't look like',",
                    "'you're from around here...'",
                    "",
                    "'I'm the Village Elder. What brings you",
                    " to Oakvale?'",
                ],
                "choices": [
                    ("'I need shelter and food'", "ask_shelter"),
                    ("'I want to become a warrior!'", "ask_warrior"),
                    ("'I'm just passing through'", "passing_through"),
                ],
                "bg": "village",
            },
            {
                "id": "ask_shelter",
                "text": [
                    "The Elder strokes his chin thoughtfully.",
                    "'We always need more hands around here.',",
                    "'Tell you what — help us with some tasks',",
                    "'and you can stay in the empty cottage.'",
                    "",
                    "'First, we need someone to gather wood.',",
                    "'The lumberjack hurt his back yesterday.'",
                    "",
                    "Quest Unlocked: Gather 10 Wood!",
                ],
                "choices": [
                    ("Accept the quest", "gather_wood"),
                    ("Ask about warrior training instead", "ask_warrior"),
                ],
                "bg": "village",
                "unlock_quest": "gather_wood",
            },
            {
                "id": "ask_warrior",
                "text": [
                    "The Elder's eyes widen.",
                    "'A warrior? Ha! We haven't had a warrior',",
                    "'in this village since... well, since Runt.'",
                    "",
                    "'But he proved that even the most unlikely',",
                    "'person can become a great fighter.'",
                    "",
                    "'If you want training, talk to Brio.',",
                    "'He's the combat instructor. But first...',",
                    "'you'll need to prove yourself.',",
                    "'Go gather some wood for the village.'",
                    "",
                    "Quest Unlocked: Gather 10 Wood!",
                ],
                "choices": [
                    ("Accept the quest", "gather_wood"),
                ],
                "bg": "village",
                "unlock_quest": "gather_wood",
            },
            {
                "id": "passing_through",
                "text": [
                    "'Just passing through, eh?' The Elder nods.",
                    "'Well, you're welcome to rest here.',",
                    "'But be warned — hostile mobs have been',",
                    "'more aggressive lately. Something is',",
                    "'stirring in the Nether...'",
                    "",
                    "'If you want to help, we could always',",
                    "'use an extra hand gathering resources.'",
                ],
                "choices": [
                    ("Offer to help", "ask_shelter"),
                    ("Ask about the Nether threat", "nether_rumor"),
                ],
                "bg": "village",
            },
            {
                "id": "nether_rumor",
                "text": [
                    "The Elder lowers his voice.",
                    "'Lately, zombie pigmen have been spotted',",
                    "'near the old portal in the mountain.',",
                    "'And at night... blazes. BLAZES, on the',",
                    "'surface! Something isn't right.'",
                    "",
                    "'A young warrior named Breeze went to',",
                    "'investigate. She hasn't returned...'",
                    "",
                    "'We think the portal has been activated.',",
                    "'But who — or what — opened it?'",
                ],
                "choices": [
                    ("Volunteer to investigate", "volunteer_nether"),
                    ("Ask to gather wood first", "gather_wood"),
                ],
                "bg": "village",
            },
            {
                "id": "volunteer_nether",
                "text": [
                    "'Brave! But foolish,' the Elder says.",
                    "'You can barely walk straight on those legs.',",
                    "'Train first. Gather resources. Get strong.'",
                    "",
                    "'Come back when you have iron armor',",
                    "'and a diamond sword. Then we'll talk',",
                    "'about the Nether.'",
                    "",
                    "Quest Unlocked: Gather 10 Wood!",
                    "Quest Unlocked: Craft Iron Armor!",
                    "Quest Unlocked: Find a Diamond Sword!",
                ],
                "choices": [
                    ("Time to start gathering", "gather_wood"),
                ],
                "bg": "village",
                "unlock_quest": "gather_wood",
            },
            {
                "id": "gather_wood",
                "text": [
                    "You head to the forest edge near the village.",
                    "Trees tower above you — oak, birch, spruce.",
                    "",
                    "You punch a tree. OW! That hurts!",
                    "Right... humans use TOOLS.",
                    "",
                    "You find a stone axe leaning against a stump.",
                    "Much better! CHOP CHOP CHOP!",
                ],
                "choices": [
                    ("Keep chopping (Mini-game!)", "wood_minigame"),
                ],
                "bg": "forest",
                "gain_item": "Stone Axe",
            },
            {
                "id": "wood_minigame",
                "text": [
                    "--- WOOD CHOPPING MINI-GAME ---",
                    "",
                    "Press SPACE as the bar reaches the GREEN zone!",
                    "Get 10 logs to complete the quest!",
                ],
                "choices": [],
                "bg": "forest",
                "minigame": "chop_wood",
            },
            {
                "id": "wood_complete",
                "text": [
                    "You carry a big stack of oak logs back",
                    "to the village. The Elder beams at you.",
                    "",
                    "'Excellent work! You've earned your place.'",
                    "'Here — take this as a reward.'",
                    "",
                    "Received: Wooden Sword!",
                    "Received: Bread x5!",
                    "",
                    "'Now, if you want warrior training,',",
                    "'go see Brio at the training grounds.'",
                ],
                "choices": [
                    ("Visit Brio for combat training", "meet_brio"),
                    ("Explore the village first", "explore_village"),
                ],
                "bg": "village",
                "gain_item": "Wooden Sword",
                "complete_quest": "gather_wood",
            },
            {
                "id": "explore_village",
                "text": [
                    "You wander through the village.",
                    "",
                    "There's a BLACKSMITH hammering away,",
                    "a LIBRARY full of enchanting books,",
                    "a FARM with wheat and carrots,",
                    "and a MARKET with trading villagers.",
                    "",
                    "The training grounds are to the north.",
                ],
                "choices": [
                    ("Visit the Blacksmith", "blacksmith"),
                    ("Visit the Library", "library"),
                    ("Go to the Training Grounds", "meet_brio"),
                    ("Visit the Market", "market"),
                ],
                "bg": "village",
            },
            {
                "id": "blacksmith",
                "text": [
                    "The Blacksmith, a burly man named Torx,",
                    "looks up from his anvil.",
                    "",
                    "'Need something forged? Bring me materials',",
                    "'and I can make weapons and armor.'",
                    "",
                    "'Right now I can offer:'",
                    "  Stone Sword — 5 Cobblestone",
                    "  Iron Sword — 3 Iron Ingots",
                    "  Iron Chestplate — 8 Iron Ingots",
                ],
                "choices": [
                    ("'I'll come back with materials'", "explore_village"),
                    ("Go to training grounds", "meet_brio"),
                ],
                "bg": "village",
            },
            {
                "id": "library",
                "text": [
                    "The librarian adjusts her glasses.",
                    "'Ah, a new face! I'm Lira.'",
                    "'I study enchantments and brewing.'",
                    "",
                    "'Did you know that the potion you drank',",
                    "'is one of the rarest in existence?'",
                    "",
                    "'Only a master alchemist could have',",
                    "'brewed it. Someone left it in that',",
                    "'house on PURPOSE. For you.'",
                    "",
                    "She smiles mysteriously.",
                    "'Perhaps your adventure was meant to be.'",
                ],
                "choices": [
                    ("'Who left it there?'", "library_mystery"),
                    ("Go train with Brio", "meet_brio"),
                ],
                "bg": "village",
                "gain_item": "Enchanting Knowledge",
            },
            {
                "id": "library_mystery",
                "text": [
                    "Lira glances around nervously.",
                    "'There's an old legend about the Alchemist',",
                    "'of the End. A being who creates potions',",
                    "'that can reshape reality itself.'",
                    "",
                    "'Some say the Alchemist foresaw a great',",
                    "'threat to the Overworld and chose a hero',",
                    "'from among the mobs to fight it.'",
                    "",
                    "'That hero... might be you.'",
                    "",
                    "Main Quest Updated: Discover the Alchemist's Plan!",
                ],
                "choices": [
                    ("This is a lot to take in...", "explore_village"),
                ],
                "bg": "village",
                "unlock_quest": "alchemist_mystery",
            },
            {
                "id": "market",
                "text": [
                    "The market is bustling with villagers.",
                    "A trader offers you some deals:",
                    "",
                    "  5 Emeralds → Iron Pickaxe",
                    "  10 Emeralds → Ender Pearl",
                    "  3 Emeralds → Golden Apple",
                    "",
                    "'Emeralds? Kill mobs, complete quests,',",
                    "'or mine for them!' the trader says.",
                ],
                "choices": [
                    ("'Thanks, I'll earn some emeralds'", "explore_village"),
                    ("Go to training grounds", "meet_brio"),
                ],
                "bg": "village",
            },
            {
                "id": "meet_brio",
                "text": [
                    "A muscular villager in leather armor",
                    "swings a iron sword at a training dummy.",
                    "",
                    "'You must be the new one. I'm Brio.',",
                    "'The Elder says you want to be a warrior?'",
                    "",
                    "He looks you up and down skeptically.",
                    "'You don't look like much. But Runt',",
                    "'didn't either, and he became a legend.'",
                    "",
                    "'Let's see what you've got. FIGHT ME!'",
                ],
                "choices": [
                    ("Accept the training duel!", "combat_tutorial"),
                ],
                "bg": "training",
            },
            {
                "id": "combat_tutorial",
                "text": [
                    "--- COMBAT TUTORIAL ---",
                    "",
                    "Brio readies his training sword.",
                    "",
                    "Controls:",
                    "  [A] - Attack",
                    "  [D] - Defend / Block",
                    "  [SPACE] - Dodge",
                    "",
                    "Time your blocks to parry!",
                    "Dodge heavy attacks!",
                    "Strike when Brio is recovering!",
                ],
                "choices": [],
                "bg": "training",
                "minigame": "combat",
                "enemy": {"name": "Brio (Training)", "hp": 50, "atk": 5, "def": 3},
            },
            {
                "id": "combat_win",
                "text": [
                    "Brio staggers back, grinning.",
                    "'Not bad! Not bad at all!'",
                    "",
                    "'You've got raw talent. Keep training',",
                    "'and you might just survive out there.'",
                    "",
                    "Received: Leather Armor!",
                    "Received: Combat Training Lv1!",
                    "",
                    "'Come back anytime to spar. And when',",
                    "'you're ready... there's a cave nearby',",
                    "'full of monsters that need clearing.'",
                    "",
                    "Quest Unlocked: Clear the Cave!",
                ],
                "choices": [
                    ("Explore the cave", "cave_entrance"),
                    ("Keep exploring the village", "explore_village"),
                ],
                "bg": "training",
                "gain_item": "Leather Armor",
                "unlock_quest": "clear_cave",
            },
        ],
    },
    {
        "id": "cave",
        "title": "Chapter 3: The Cave",
        "scenes": [
            {
                "id": "cave_entrance",
                "text": [
                    "You stand at the mouth of a dark cave.",
                    "Cool air flows from inside. You can hear",
                    "the drip... drip... of water.",
                    "",
                    "And something else. Growling.",
                    "",
                    "Your hand tightens around your sword.",
                    "This is it. Your first real challenge.",
                ],
                "choices": [
                    ("Enter the cave bravely", "cave_dark"),
                    ("Craft some torches first", "craft_torches"),
                ],
                "bg": "cave",
            },
            {
                "id": "craft_torches",
                "text": [
                    "Smart thinking! You combine some sticks",
                    "and coal from the ground.",
                    "",
                    "Crafted: Torches x8!",
                    "",
                    "The warm glow makes you feel braver.",
                    "Time to face whatever's in there.",
                ],
                "choices": [
                    ("Enter the cave with torches", "cave_lit"),
                ],
                "bg": "cave",
                "gain_item": "Torches x8",
            },
            {
                "id": "cave_dark",
                "text": [
                    "You stumble into the darkness.",
                    "Can barely see your hand in front of—",
                    "",
                    "HISSSS!",
                    "",
                    "A CREEPER! Right next to you!",
                    "It's already flashing white—",
                    "",
                    "You dive to the side just in time!",
                    "BOOM! The explosion echoes through the cave.",
                    "That was WAY too close.",
                    "",
                    "Note to self: BRING TORCHES next time.",
                ],
                "choices": [
                    ("Press deeper into the cave", "cave_zombies"),
                ],
                "bg": "cave",
                "damage": 15,
            },
            {
                "id": "cave_lit",
                "text": [
                    "Your torches illuminate the stone walls.",
                    "You can see coal and iron ore glinting!",
                    "",
                    "Ahead, the tunnel splits in two:",
                    "  LEFT — wider, sounds of zombies",
                    "  RIGHT — narrow, strange purple glow",
                ],
                "choices": [
                    ("Go LEFT (fight zombies)", "cave_zombies"),
                    ("Go RIGHT (investigate glow)", "cave_portal"),
                ],
                "bg": "cave",
                "gain_item": "Iron Ore x3",
            },
            {
                "id": "cave_zombies",
                "text": [
                    "Three zombies lumber towards you!",
                    "Their groans echo off the cave walls.",
                    "",
                    "Time to put Brio's training to use!",
                ],
                "choices": [],
                "bg": "cave",
                "minigame": "combat",
                "enemy": {"name": "Cave Zombies (x3)", "hp": 80, "atk": 8, "def": 2},
            },
            {
                "id": "zombie_victory",
                "text": [
                    "The last zombie falls with a groan.",
                    "You catch your breath, sword dripping.",
                    "",
                    "Loot dropped:",
                    "  Rotten Flesh x3",
                    "  Iron Ingot x2",
                    "  5 Emeralds",
                    "",
                    "You also find a sign on the wall:",
                    "'BREEZE WAS HERE — GONE DEEPER'",
                    "",
                    "That's the warrior the Elder mentioned!",
                ],
                "choices": [
                    ("Follow Breeze's trail deeper", "cave_deep"),
                    ("Head back to the village", "village_return"),
                ],
                "bg": "cave",
                "gain_item": "Iron Ingot x2",
            },
            {
                "id": "cave_portal",
                "text": [
                    "The narrow passage opens into a cavern.",
                    "And there, embedded in the wall...",
                    "",
                    "A NETHER PORTAL. Active. Swirling purple.",
                    "",
                    "This must be what the Elder warned about.",
                    "The heat coming from it is intense.",
                    "",
                    "You're not ready for the Nether yet.",
                    "But now you know where the portal is.",
                    "",
                    "Quest Updated: Report the portal to the Elder!",
                ],
                "choices": [
                    ("Head back to report", "village_return"),
                    ("Step through the portal (DANGER!)", "nether_early"),
                ],
                "bg": "nether_portal",
                "unlock_quest": "report_portal",
            },
            {
                "id": "nether_early",
                "text": [
                    "You step through the portal and—",
                    "",
                    "HEAT. FIRE. LAKES OF LAVA.",
                    "",
                    "A ghast spots you IMMEDIATELY.",
                    "FWOOOOSH! A fireball hurtles towards you!",
                    "",
                    "You barely dodge and leap back through",
                    "the portal, singed and terrified.",
                    "",
                    "Yeah... definitely not ready for that yet.",
                ],
                "choices": [
                    ("Run back to the village", "village_return"),
                ],
                "bg": "nether",
                "damage": 30,
            },
            {
                "id": "cave_deep",
                "text": [
                    "You follow scratched arrows on the walls.",
                    "Breeze left a trail! The cave goes deeper...",
                    "",
                    "You find her camp — abandoned bedroll,",
                    "empty food wrappers, a half-finished map.",
                    "",
                    "Her journal reads:",
                    "'Day 5 — Found something amazing deeper in.",
                    " A spawner room. Beyond it, DIAMONDS.',",
                    "'Day 7 — The spawner room is too dangerous.',",
                    " Need backup. Going to find another way.'",
                    "",
                    "She must have gone towards the Nether portal.",
                ],
                "choices": [
                    ("Take Breeze's map and head back", "village_return"),
                    ("Try the spawner room", "spawner_room"),
                ],
                "bg": "cave",
                "gain_item": "Breeze's Map",
            },
            {
                "id": "spawner_room",
                "text": [
                    "You enter a room with a spinning mob spawner!",
                    "Skeletons materialize from dark smoke!",
                    "",
                    "CLACK CLACK CLACK — arrows fly!",
                    "This is a serious fight!",
                ],
                "choices": [],
                "bg": "cave",
                "minigame": "combat",
                "enemy": {"name": "Skeleton Spawner", "hp": 120, "atk": 12, "def": 5},
            },
            {
                "id": "spawner_victory",
                "text": [
                    "You smash the spawner! It crumbles to dust.",
                    "",
                    "Behind it, in the wall... DIAMONDS!",
                    "Three beautiful blue gems glitter!",
                    "",
                    "Received: Diamond x3!",
                    "Received: Enchanted Book (Sharpness I)!",
                    "",
                    "With these, the Blacksmith can forge",
                    "a DIAMOND SWORD!",
                    "",
                    "Time to head back to the village.",
                ],
                "choices": [
                    ("Return to the village", "village_return"),
                ],
                "bg": "cave",
                "gain_item": "Diamond x3",
            },
            {
                "id": "village_return",
                "text": [
                    "You emerge from the cave, blinking in the",
                    "sunlight. The village is a welcome sight.",
                    "",
                    "The Elder rushes over.",
                    "'You're alive! What did you find?'",
                    "",
                    "You tell him about the cave, the zombies,",
                    "the Nether portal, and Breeze's trail.",
                    "",
                    "'This is worse than I feared...',",
                    "'We need to prepare. But tonight — REST.',",
                    "'Tomorrow, your real training begins.'",
                    "",
                    "       TO BE CONTINUED...",
                    "    (More chapters coming soon!)",
                ],
                "choices": [
                    ("Save & Return to Menu", "save_menu"),
                ],
                "bg": "village_night",
                "complete_quest": "clear_cave",
            },
        ],
    },
    {
        "id": "dark_forest_ch",
        "title": "Chapter 2B: The Dark Forest",
        "scenes": [
            {
                "id": "dark_forest",
                "text": [
                    "You venture into the dark oak forest.",
                    "The canopy is so thick, barely any light",
                    "filters through. Mushrooms glow faintly.",
                    "",
                    "Your mob instincts scream: DANGER!",
                    "Spiders skitter in the treetops above.",
                    "",
                    "But something glints on the ground...",
                ],
                "choices": [
                    ("Investigate the glint", "forest_treasure"),
                    ("Head back to the village path", "village_gate"),
                ],
                "bg": "dark_forest",
            },
            {
                "id": "forest_treasure",
                "text": [
                    "It's an old compass! The needle spins",
                    "wildly before pointing... DOWN.",
                    "",
                    "A compass that points underground?",
                    "It must be enchanted — pointing to",
                    "something buried deep below.",
                    "",
                    "You pocket it. Might be useful later.",
                    "",
                    "A spider drops from above! FIGHT!",
                ],
                "choices": [],
                "bg": "dark_forest",
                "minigame": "combat",
                "enemy": {"name": "Giant Spider", "hp": 60, "atk": 10, "def": 3},
                "gain_item": "Enchanted Compass",
            },
            {
                "id": "spider_victory",
                "text": [
                    "The spider curls up, defeated.",
                    "It drops some string and spider eyes.",
                    "",
                    "The forest is getting darker.",
                    "Better head to the village before night.",
                ],
                "choices": [
                    ("Head to the village", "village_gate"),
                ],
                "bg": "dark_forest",
                "gain_item": "String x3",
            },
            {
                "id": "mountain_path",
                "text": [
                    "You climb the rocky path upward.",
                    "The air gets cooler. Snow dusts the peaks.",
                    "",
                    "You find a small alcove with a campfire",
                    "— recently used. Someone was here.",
                    "",
                    "Carved into the rock: 'BREEZE'",
                    "with an arrow pointing to a cave entrance.",
                    "",
                    "The cave leads deep into the mountain...",
                ],
                "choices": [
                    ("Enter the mountain cave", "cave_entrance"),
                    ("Head to the village instead", "village_gate"),
                ],
                "bg": "mountain",
            },
        ],
    },
]

# Build a flat scene lookup
ALL_SCENES = {}
for chapter in CHAPTERS:
    for scene in chapter["scenes"]:
        ALL_SCENES[scene["id"]] = scene

# ── GAME STATE ─────────────────────────────────────────────────────────
class GameState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.mob_type = None       # "cat", "wolf", "bunny"
        self.name = ""
        self.hp = 100
        self.max_hp = 100
        self.atk = 10
        self.defense = 5
        self.level = 1
        self.xp = 0
        self.xp_next = 50
        self.inventory = []
        self.quests_active = []
        self.quests_done = []
        self.current_scene = "start"
        self.is_human = False
        self.emeralds = 0
        self.combat_skill = 0
        self.scenes_visited = []
        self.wood_count = 0
        self.chapter = 0

    def save(self):
        data = {
            "mob_type": self.mob_type,
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "atk": self.atk,
            "defense": self.defense,
            "level": self.level,
            "xp": self.xp,
            "xp_next": self.xp_next,
            "inventory": self.inventory,
            "quests_active": self.quests_active,
            "quests_done": self.quests_done,
            "current_scene": self.current_scene,
            "is_human": self.is_human,
            "emeralds": self.emeralds,
            "combat_skill": self.combat_skill,
            "scenes_visited": self.scenes_visited,
            "wood_count": self.wood_count,
            "chapter": self.chapter,
        }
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load(self):
        if not os.path.exists(SAVE_FILE):
            return False
        try:
            with open(SAVE_FILE) as f:
                data = json.load(f)
            for k, v in data.items():
                if hasattr(self, k):
                    setattr(self, k, v)
            return True
        except Exception:
            return False

    def gain_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_next:
            self.xp -= self.xp_next
            self.level += 1
            self.max_hp += 10
            self.hp = self.max_hp
            self.atk += 2
            self.defense += 1
            self.xp_next = int(self.xp_next * 1.4)

# ── MAIN GAME CLASS ───────────────────────────────────────────────────
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Diary of a Mob — A Minecraft Adventure")
        self.clock = pygame.time.Clock()
        self.state = GameState()
        self.phase = "title"  # title, select_mob, name_input, story, minigame_chop, minigame_combat, game_over
        self.font_lg = pygame.font.SysFont("consolas", 32, bold=True)
        self.font_md = pygame.font.SysFont("consolas", 20)
        self.font_sm = pygame.font.SysFont("consolas", 16)
        self.font_xs = pygame.font.SysFont("consolas", 13)
        self.selected_choice = 0
        self.text_progress = 0
        self.text_timer = 0
        self.particles = []
        self.shake = 0
        self.notification = ""
        self.notif_timer = 0
        self.transition_alpha = 0
        self.transitioning = False
        self.next_scene_id = None
        # Minigame state
        self.chop_bar = 0
        self.chop_dir = 1
        self.chop_count = 0
        self.chop_hits = 0
        # Combat state
        self.combat_enemy = None
        self.combat_enemy_hp = 0
        self.combat_enemy_max_hp = 0
        self.combat_player_cd = 0
        self.combat_enemy_cd = 0
        self.combat_block = False
        self.combat_dodge = False
        self.combat_dodge_timer = 0
        self.combat_log = []
        self.combat_anim = ""
        self.combat_anim_timer = 0
        self.combat_result = None
        # Title animation
        self.title_bob = 0
        self.stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT // 2),
                       random.random() * 2 + 0.5) for _ in range(60)]
        # Name input
        self.name_input = ""
        # BG cache
        self.bg_cache = {}

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    running = False
            if self.phase == "title":
                self.update_title(dt, events)
                self.draw_title()
            elif self.phase == "select_mob":
                self.update_select_mob(dt, events)
                self.draw_select_mob()
            elif self.phase == "name_input":
                self.update_name_input(dt, events)
                self.draw_name_input()
            elif self.phase == "story":
                self.update_story(dt, events)
                self.draw_story()
            elif self.phase == "minigame_chop":
                self.update_chop(dt, events)
                self.draw_chop()
            elif self.phase == "minigame_combat":
                self.update_combat(dt, events)
                self.draw_combat()
            elif self.phase == "game_over":
                self.update_game_over(dt, events)
                self.draw_game_over()
            # Notification overlay
            if self.notif_timer > 0:
                self.notif_timer -= dt
                alpha = min(255, int(self.notif_timer * 200))
                ns = self.font_md.render(self.notification, True, GOLD)
                ns.set_alpha(alpha)
                self.screen.blit(ns, (WIDTH // 2 - ns.get_width() // 2, 50))
            pygame.display.flip()
        self.state.save()
        pygame.quit()
        sys.exit()

    # ── HELPER: activate selected title choice ─────────────────────
    def _title_activate(self):
        if self.selected_choice == 0:
            self.state.reset()
            self.phase = "select_mob"
        elif self.selected_choice == 1:
            if self.state.load():
                self.phase = "story"
                self.text_progress = 999
            else:
                self.notification = "No save file found!"
                self.notif_timer = 2

    # ── TITLE ─────────────────────────────────────────────────────────
    def update_title(self, dt, events):
        self.title_bob += dt * 2
        # Store button rects for click detection
        self._title_btn_rects = []
        opts = ["New Game", "Continue"]
        for i, opt in enumerate(opts):
            t = self.font_md.render("  " + opt, True, WHITE)
            tw = t.get_width()
            bx = WIDTH // 2 - tw // 2 - 10
            by = 380 + i * 40 - 4
            self._title_btn_rects.append(pygame.Rect(bx, by, tw + 20, 34))
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                for i, rect in enumerate(self._title_btn_rects):
                    if rect.collidepoint(mx, my):
                        self.selected_choice = i
                        self._title_activate()
                        break
            elif e.type == pygame.MOUSEMOTION:
                mx, my = e.pos
                for i, rect in enumerate(self._title_btn_rects):
                    if rect.collidepoint(mx, my):
                        self.selected_choice = i
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._title_activate()
                elif e.key in (pygame.K_UP, pygame.K_w):
                    self.selected_choice = max(0, self.selected_choice - 1)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.selected_choice = min(1, self.selected_choice + 1)

    def draw_title(self):
        self.screen.fill(BLACK)
        # Stars
        for sx, sy, ss in self.stars:
            bright = int(128 + 127 * math.sin(time.time() * ss))
            pygame.draw.circle(self.screen, (bright, bright, bright), (int(sx), int(sy)), 1)
        # Ground
        pygame.draw.rect(self.screen, DKGREEN, (0, HEIGHT - 100, WIDTH, 100))
        for gx in range(0, WIDTH, 16):
            h = random.randint(2, 8)
            pygame.draw.rect(self.screen, GREEN, (gx, HEIGHT - 100 - h, 4, h))
        # Title
        bob = int(math.sin(self.title_bob) * 5)
        title1 = self.font_lg.render("DIARY OF A MOB", True, GOLD)
        title2 = self.font_md.render("A Minecraft Adventure", True, WHITE)
        title3 = self.font_xs.render("Inspired by Cube Kid, Diary of a Minecraft Wolf & Kitten", True, GRAY)
        self.screen.blit(title1, (WIDTH // 2 - title1.get_width() // 2, 120 + bob))
        self.screen.blit(title2, (WIDTH // 2 - title2.get_width() // 2, 165 + bob))
        self.screen.blit(title3, (WIDTH // 2 - title3.get_width() // 2, 195))
        # Draw small mob icons
        draw_cat(self.screen, WIDTH // 2 - 120, 240, 2)
        draw_wolf(self.screen, WIDTH // 2 - 30, 235, 2)
        draw_bunny(self.screen, WIDTH // 2 + 70, 235, 2)
        # Menu
        opts = ["New Game", "Continue"]
        for i, opt in enumerate(opts):
            col = GOLD if i == self.selected_choice else WHITE
            prefix = "> " if i == self.selected_choice else "  "
            t = self.font_md.render(prefix + opt, True, col)
            self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 380 + i * 40))
        # Footer
        ft = self.font_xs.render("Click or WASD + Enter", True, GRAY)
        self.screen.blit(ft, (WIDTH // 2 - ft.get_width() // 2, HEIGHT - 30))

    # ── MOB SELECT ────────────────────────────────────────────────────
    def _mob_card_rects(self):
        rects = []
        for i in range(3):
            bx = 100 + i * 260
            by = 140
            bw, bh = 220, 350
            rects.append(pygame.Rect(bx, by, bw, bh))
        return rects

    def update_select_mob(self, dt, events):
        card_rects = self._mob_card_rects()
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                for i, rect in enumerate(card_rects):
                    if rect.collidepoint(mx, my):
                        self.selected_choice = i
                        self.state.mob_type = ["cat", "wolf", "bunny"][i]
                        self.phase = "name_input"
                        self.selected_choice = 0
                        break
            elif e.type == pygame.MOUSEMOTION:
                mx, my = e.pos
                for i, rect in enumerate(card_rects):
                    if rect.collidepoint(mx, my):
                        self.selected_choice = i
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_LEFT, pygame.K_a):
                    self.selected_choice = max(0, self.selected_choice - 1)
                elif e.key in (pygame.K_RIGHT, pygame.K_d):
                    self.selected_choice = min(2, self.selected_choice + 1)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.state.mob_type = ["cat", "wolf", "bunny"][self.selected_choice]
                    self.phase = "name_input"
                    self.selected_choice = 0

    def draw_select_mob(self):
        self.screen.fill((20, 20, 30))
        # Title
        t = self.font_lg.render("Choose Your Mob", True, WHITE)
        self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 40))
        sub = self.font_sm.render("Who will you begin your adventure as?", True, GRAY)
        self.screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 80))
        mobs = [
            ("Cat", "Diary of a Minecraft Kitten", "Agile & sneaky. +2 Speed", (230, 160, 60)),
            ("Wolf", "Diary of a Minecraft Wolf", "Strong & loyal. +2 Attack", (200, 200, 200)),
            ("Bunny", "The unlikely hero", "Quick & lucky. +2 Dodge", (230, 220, 200)),
        ]
        for i, (name, book, desc, col) in enumerate(mobs):
            bx = 100 + i * 260
            by = 140
            bw, bh = 220, 350
            # Card
            border = GOLD if i == self.selected_choice else DKGRAY
            pygame.draw.rect(self.screen, border, (bx - 3, by - 3, bw + 6, bh + 6), border_radius=8)
            pygame.draw.rect(self.screen, (30, 30, 45), (bx, by, bw, bh), border_radius=8)
            # Draw mob
            cx = bx + bw // 2 - 20
            cy = by + 40
            if i == 0:
                draw_cat(self.screen, cx, cy, 3)
            elif i == 1:
                draw_wolf(self.screen, cx - 10, cy, 3)
            else:
                draw_bunny(self.screen, cx, cy - 10, 3)
            # Labels
            nt = self.font_md.render(name, True, col)
            self.screen.blit(nt, (bx + bw // 2 - nt.get_width() // 2, by + 150))
            bt = self.font_xs.render(book, True, CYAN)
            self.screen.blit(bt, (bx + bw // 2 - bt.get_width() // 2, by + 180))
            # Description
            dt_text = self.font_sm.render(desc, True, GREEN)
            self.screen.blit(dt_text, (bx + bw // 2 - dt_text.get_width() // 2, by + 210))
            if i == self.selected_choice:
                sel = self.font_sm.render("[ SELECTED ]", True, GOLD)
                self.screen.blit(sel, (bx + bw // 2 - sel.get_width() // 2, by + bh - 40))
        ft = self.font_xs.render("Click a mob or A/D + Enter", True, GRAY)
        self.screen.blit(ft, (WIDTH // 2 - ft.get_width() // 2, HEIGHT - 30))

    # ── NAME INPUT ────────────────────────────────────────────────────
    def update_name_input(self, dt, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN and len(self.name_input) > 0:
                    self.state.name = self.name_input
                    # Apply mob bonuses
                    if self.state.mob_type == "cat":
                        self.state.defense += 2
                    elif self.state.mob_type == "wolf":
                        self.state.atk += 2
                    else:
                        self.state.max_hp += 10
                        self.state.hp = self.state.max_hp
                    self.phase = "story"
                    self.state.current_scene = "start"
                    self.text_progress = 0
                    self.text_timer = 0
                    self.selected_choice = 0
                elif e.key == pygame.K_BACKSPACE:
                    self.name_input = self.name_input[:-1]
                elif len(self.name_input) < 16 and e.unicode.isprintable() and e.unicode != '':
                    self.name_input += e.unicode

    def draw_name_input(self):
        self.screen.fill((20, 20, 30))
        mob_names = {"cat": "Kitten", "wolf": "Wolf", "bunny": "Bunny"}
        t = self.font_lg.render(f"Name Your {mob_names[self.state.mob_type]}", True, WHITE)
        self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 150))
        # Draw mob
        cx = WIDTH // 2 - 20
        if self.state.mob_type == "cat":
            draw_cat(self.screen, cx, 230, 4)
        elif self.state.mob_type == "wolf":
            draw_wolf(self.screen, cx - 15, 225, 4)
        else:
            draw_bunny(self.screen, cx, 220, 4)
        # Input box
        box_w = 300
        box_x = WIDTH // 2 - box_w // 2
        box_y = 370
        pygame.draw.rect(self.screen, DKGRAY, (box_x, box_y, box_w, 40), border_radius=5)
        pygame.draw.rect(self.screen, WHITE, (box_x, box_y, box_w, 40), 2, border_radius=5)
        cursor = "|" if int(time.time() * 2) % 2 == 0 else ""
        nt = self.font_md.render(self.name_input + cursor, True, WHITE)
        self.screen.blit(nt, (box_x + 10, box_y + 8))
        hint = self.font_xs.render("Type a name and press Enter", True, GRAY)
        self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 420))

    # ── STORY SCENE ───────────────────────────────────────────────────
    def get_scene(self):
        return ALL_SCENES.get(self.state.current_scene)

    def goto_scene(self, scene_id):
        if scene_id == "save_menu":
            self.state.save()
            self.notification = "Game Saved!"
            self.notif_timer = 2
            self.phase = "title"
            self.selected_choice = 0
            return
        self.state.current_scene = scene_id
        if scene_id not in self.state.scenes_visited:
            self.state.scenes_visited.append(scene_id)
        scene = self.get_scene()
        if not scene:
            return
        # Process scene effects
        if scene.get("gain_item"):
            item = scene["gain_item"]
            if item not in self.state.inventory:
                self.state.inventory.append(item)
                self.notification = f"Obtained: {item}"
                self.notif_timer = 2.5
        if scene.get("heal"):
            self.state.hp = min(self.state.max_hp, self.state.hp + scene["heal"])
        if scene.get("damage"):
            self.state.hp = max(1, self.state.hp - scene["damage"])
            self.shake = 0.5
        if scene.get("transform"):
            self.state.is_human = True
            self.state.gain_xp(100)
            self.notification = "TRANSFORMED INTO HUMAN! +100 XP"
            self.notif_timer = 3
        if scene.get("unlock_quest"):
            q = scene["unlock_quest"]
            if q not in self.state.quests_active and q not in self.state.quests_done:
                self.state.quests_active.append(q)
        if scene.get("complete_quest"):
            q = scene["complete_quest"]
            if q in self.state.quests_active:
                self.state.quests_active.remove(q)
            if q not in self.state.quests_done:
                self.state.quests_done.append(q)
                self.state.gain_xp(50)
        if scene.get("minigame") == "chop_wood":
            self.phase = "minigame_chop"
            self.chop_bar = 0
            self.chop_dir = 1
            self.chop_count = 0
            self.chop_hits = 0
            return
        if scene.get("minigame") == "combat":
            enemy = scene.get("enemy", {"name": "Enemy", "hp": 50, "atk": 8, "def": 2})
            self.start_combat(enemy)
            return
        self.text_progress = 0
        self.text_timer = 0
        self.selected_choice = 0

    def _story_choice_rects(self, scene):
        """Return clickable rects for current story choices."""
        rects = []
        if not scene["choices"]:
            return rects
        box_y = HEIGHT - 250
        box_h = 230
        cy = box_y + box_h - 10 - len(scene["choices"]) * 24
        for i, (text, _) in enumerate(scene["choices"]):
            rects.append(pygame.Rect(40, cy + i * 24 - 2, WIDTH - 100, 22))
        return rects

    def update_story(self, dt, events):
        scene = self.get_scene()
        if not scene:
            return
        self.text_timer += dt * 30
        max_chars = sum(len(line) for line in scene["text"])
        if self.text_timer > self.text_progress:
            self.text_progress = min(int(self.text_timer), max_chars)
        if self.shake > 0:
            self.shake -= dt
        choice_rects = self._story_choice_rects(scene) if self.text_progress >= max_chars else []
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                if self.text_progress < max_chars:
                    # Click to skip typewriter
                    self.text_progress = max_chars
                    self.text_timer = max_chars
                elif scene["choices"]:
                    for i, rect in enumerate(choice_rects):
                        if rect.collidepoint(mx, my):
                            self.selected_choice = i
                            target = scene["choices"][i][1]
                            self.goto_scene(target)
                            break
            elif e.type == pygame.MOUSEMOTION and choice_rects:
                mx, my = e.pos
                for i, rect in enumerate(choice_rects):
                    if rect.collidepoint(mx, my):
                        self.selected_choice = i
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.text_progress < max_chars:
                        self.text_progress = max_chars
                        self.text_timer = max_chars
                    elif scene["choices"]:
                        target = scene["choices"][self.selected_choice][1]
                        self.goto_scene(target)
                elif e.key in (pygame.K_UP, pygame.K_w) and scene["choices"]:
                    self.selected_choice = max(0, self.selected_choice - 1)
                elif e.key in (pygame.K_DOWN, pygame.K_s) and scene["choices"]:
                    self.selected_choice = min(len(scene["choices"]) - 1, self.selected_choice + 1)

    def draw_bg(self, bg_name):
        """Draw background based on scene type."""
        if bg_name == "plains":
            self.screen.fill(SKYBLUE)
            pygame.draw.rect(self.screen, GREEN, (0, HEIGHT - 200, WIDTH, 200))
            pygame.draw.rect(self.screen, DKGREEN, (0, HEIGHT - 200, WIDTH, 4))
            # Sun
            pygame.draw.circle(self.screen, YELLOW, (WIDTH - 100, 80), 40)
            # Clouds
            for cx in [100, 350, 600]:
                pygame.draw.ellipse(self.screen, WHITE, (cx, 50, 80, 30))
                pygame.draw.ellipse(self.screen, WHITE, (cx + 20, 35, 80, 30))
            # Dead trees
            for tx in [150, 650]:
                pygame.draw.rect(self.screen, DKBROWN, (tx, HEIGHT - 280, 10, 80))
                pygame.draw.line(self.screen, DKBROWN, (tx + 5, HEIGHT - 270), (tx - 15, HEIGHT - 300), 3)
                pygame.draw.line(self.screen, DKBROWN, (tx + 5, HEIGHT - 260), (tx + 25, HEIGHT - 290), 3)
        elif bg_name == "house_exterior":
            self.screen.fill(SKYBLUE)
            pygame.draw.rect(self.screen, GREEN, (0, HEIGHT - 150, WIDTH, 150))
            draw_house_exterior(self.screen, WIDTH // 2 - 80, HEIGHT - 310, 160, 160)
        elif bg_name in ("house_interior", "chest_room"):
            self.screen.fill((40, 30, 25))
            # Stone walls
            for bx in range(0, WIDTH, 20):
                for by in range(0, HEIGHT - 250, 20):
                    v = random.randint(-8, 8)
                    c = (STONE[0] + v, STONE[1] + v, STONE[2] + v)
                    c = tuple(max(0, min(255, x)) for x in c)
                    pygame.draw.rect(self.screen, c, (bx, by, 19, 19))
            # Floor
            for bx in range(0, WIDTH, 20):
                for by in range(HEIGHT - 250, HEIGHT - 200, 20):
                    pygame.draw.rect(self.screen, WOOD, (bx, by, 19, 19))
            # Bookshelves
            for bx in [30, 60, 90]:
                pygame.draw.rect(self.screen, DKBROWN, (bx, 60, 25, 80))
                for row in range(3):
                    col = random.choice([RED, BLUE, GREEN, BROWN])
                    pygame.draw.rect(self.screen, col, (bx + 2, 62 + row * 25, 21, 20))
            if bg_name == "chest_room":
                draw_chest(self.screen, WIDTH // 2 - 30, HEIGHT - 310, 60, 50, opened=True)
                draw_potion(self.screen, WIDTH // 2 - 12, HEIGHT - 350)
        elif bg_name == "transformation":
            # Magic purple swirl
            self.screen.fill((30, 10, 50))
            for i in range(40):
                angle = time.time() * 2 + i * 0.3
                r = 50 + i * 4
                px = int(WIDTH // 2 + math.cos(angle) * r)
                py = int(HEIGHT // 2 - 60 + math.sin(angle) * r)
                bright = max(50, 255 - i * 5)
                pygame.draw.circle(self.screen, (bright, 50, bright), (px, py), 3)
            # Draw human form
            draw_human(self.screen, WIDTH // 2 - 10, HEIGHT // 2 - 40, 3, self.state.mob_type)
        elif bg_name == "overworld":
            self.screen.fill(SKYBLUE)
            pygame.draw.rect(self.screen, GREEN, (0, HEIGHT - 180, WIDTH, 180))
            # Village smoke east
            for i in range(5):
                a = int(100 + math.sin(time.time() + i) * 20)
                pygame.draw.circle(self.screen, (a, a, a), (WIDTH - 100 + i * 8, 100 - i * 15), 8 - i)
            # Dark forest west
            for tx in range(5):
                pygame.draw.rect(self.screen, (20, 60, 20), (20 + tx * 30, HEIGHT - 280, 20, 100))
                pygame.draw.circle(self.screen, (30, 80, 30), (30 + tx * 30, HEIGHT - 280), 25)
            # Mountain north
            pts = [(WIDTH // 2 - 100, HEIGHT - 250), (WIDTH // 2, 60), (WIDTH // 2 + 100, HEIGHT - 250)]
            pygame.draw.polygon(self.screen, STONE, pts)
            pygame.draw.polygon(self.screen, WHITE, [(WIDTH // 2 - 20, 100), (WIDTH // 2, 60), (WIDTH // 2 + 20, 100)])
        elif bg_name == "village":
            self.screen.fill(SKYBLUE)
            pygame.draw.rect(self.screen, (190, 170, 120), (0, HEIGHT - 160, WIDTH, 160))  # Path
            # Houses
            for hx in [80, 300, 550, 720]:
                hw = random.randint(50, 70)
                hh = random.randint(60, 80)
                pygame.draw.rect(self.screen, WOOD, (hx, HEIGHT - 160 - hh, hw, hh))
                pygame.draw.polygon(self.screen, DKBROWN,
                                    [(hx - 5, HEIGHT - 160 - hh), (hx + hw // 2, HEIGHT - 160 - hh - 30),
                                     (hx + hw + 5, HEIGHT - 160 - hh)])
                pygame.draw.rect(self.screen, (60, 40, 20), (hx + hw // 2 - 8, HEIGHT - 160 - 35, 16, 35))
            # Iron Golem
            pygame.draw.rect(self.screen, (180, 180, 180), (50, HEIGHT - 220, 20, 40))
            pygame.draw.rect(self.screen, (180, 180, 180), (45, HEIGHT - 230, 30, 15))
        elif bg_name == "village_night":
            self.screen.fill(NIGHTBLUE)
            pygame.draw.rect(self.screen, (30, 50, 30), (0, HEIGHT - 160, WIDTH, 160))
            # Moon
            pygame.draw.circle(self.screen, (220, 220, 200), (WIDTH - 100, 60), 30)
            # Stars
            for sx, sy, ss in self.stars[:20]:
                pygame.draw.circle(self.screen, WHITE, (int(sx), int(sy)), 1)
            # Houses with lit windows
            for hx in [80, 300, 550]:
                pygame.draw.rect(self.screen, (50, 35, 20), (hx, HEIGHT - 220, 60, 60))
                pygame.draw.rect(self.screen, YELLOW, (hx + 10, HEIGHT - 210, 15, 15))
        elif bg_name == "forest" or bg_name == "dark_forest":
            if bg_name == "dark_forest":
                self.screen.fill((10, 20, 10))
            else:
                self.screen.fill((40, 80, 40))
            pygame.draw.rect(self.screen, DKGREEN, (0, HEIGHT - 150, WIDTH, 150))
            for tx in range(8):
                x = 30 + tx * 110
                trunk_h = random.randint(100, 180)
                pygame.draw.rect(self.screen, DKBROWN, (x, HEIGHT - 150 - trunk_h, 16, trunk_h))
                pygame.draw.circle(self.screen, LEAF if bg_name != "dark_forest" else (20, 60, 20),
                                   (x + 8, HEIGHT - 150 - trunk_h), 35)
        elif bg_name == "training":
            self.screen.fill(SKYBLUE)
            pygame.draw.rect(self.screen, SAND, (0, HEIGHT - 150, WIDTH, 150))
            # Training dummy
            pygame.draw.rect(self.screen, WOOD, (WIDTH - 150, HEIGHT - 250, 8, 80))
            pygame.draw.circle(self.screen, (200, 180, 140), (WIDTH - 146, HEIGHT - 260), 15)
            # Fence
            for fx in range(0, WIDTH, 40):
                pygame.draw.rect(self.screen, WOOD, (fx, HEIGHT - 170, 6, 30))
            pygame.draw.rect(self.screen, WOOD, (0, HEIGHT - 160, WIDTH, 4))
        elif bg_name == "cave":
            self.screen.fill((20, 18, 15))
            for i in range(30):
                bx = random.randint(0, WIDTH)
                by = random.randint(0, HEIGHT - 200)
                bs = random.randint(15, 30)
                v = random.randint(30, 60)
                pygame.draw.rect(self.screen, (v, v, v), (bx, by, bs, bs))
            pygame.draw.rect(self.screen, (40, 35, 30), (0, HEIGHT - 120, WIDTH, 120))
        elif bg_name == "nether_portal":
            self.screen.fill((20, 18, 15))
            # Portal frame
            px, py = WIDTH // 2 - 30, HEIGHT // 2 - 80
            for i in range(5):
                pygame.draw.rect(self.screen, (50, 10, 50), (px - 10, py + i * 30, 15, 28))
                pygame.draw.rect(self.screen, (50, 10, 50), (px + 55, py + i * 30, 15, 28))
            for i in range(3):
                pygame.draw.rect(self.screen, (50, 10, 50), (px + i * 20, py - 10, 18, 15))
                pygame.draw.rect(self.screen, (50, 10, 50), (px + i * 20, py + 145, 18, 15))
            # Purple swirl
            for i in range(20):
                sx = px + 5 + random.randint(0, 50)
                sy = py + random.randint(0, 140)
                c = random.randint(100, 200)
                pygame.draw.rect(self.screen, (c, 50, c), (sx, sy, 4, 4))
        elif bg_name == "nether":
            self.screen.fill((60, 10, 10))
            # Lava
            pygame.draw.rect(self.screen, LAVA, (0, HEIGHT - 100, WIDTH, 100))
            for i in range(10):
                bx = random.randint(0, WIDTH)
                pygame.draw.circle(self.screen, ORANGE, (bx, HEIGHT - random.randint(20, 80)), random.randint(3, 8))
            # Netherrack
            for i in range(20):
                bx = random.randint(0, WIDTH)
                by = random.randint(0, HEIGHT - 120)
                pygame.draw.rect(self.screen, (100, 30, 30), (bx, by, 20, 20))
        elif bg_name == "mountain":
            self.screen.fill(SKYBLUE)
            pts = [(0, HEIGHT - 100), (WIDTH // 3, 50), (WIDTH * 2 // 3, 80), (WIDTH, HEIGHT - 100)]
            pygame.draw.polygon(self.screen, STONE, pts)
            pygame.draw.polygon(self.screen, WHITE, [(WIDTH // 3 - 15, 70), (WIDTH // 3, 50), (WIDTH // 3 + 15, 70)])
            pygame.draw.rect(self.screen, DKGREEN, (0, HEIGHT - 100, WIDTH, 100))
        else:
            self.screen.fill(BLACK)

    def draw_story(self):
        scene = self.get_scene()
        if not scene:
            return
        # Background
        ox = int(math.sin(time.time() * 20) * self.shake * 8) if self.shake > 0 else 0
        oy = int(math.cos(time.time() * 20) * self.shake * 8) if self.shake > 0 else 0
        self.screen.fill(BLACK)
        bg_surf = pygame.Surface((WIDTH, HEIGHT))
        self.draw_bg(scene.get("bg", "plains"))
        self.screen.blit(self.screen.copy(), (ox, oy))
        # Text box
        box_y = HEIGHT - 250
        box_h = 230
        box_surf = pygame.Surface((WIDTH - 40, box_h))
        box_surf.set_alpha(220)
        box_surf.fill((20, 20, 30))
        self.screen.blit(box_surf, (20, box_y))
        pygame.draw.rect(self.screen, GOLD, (20, box_y, WIDTH - 40, box_h), 2, border_radius=4)
        # Chapter title
        for ch in CHAPTERS:
            for s in ch["scenes"]:
                if s["id"] == self.state.current_scene:
                    ct = self.font_xs.render(ch["title"], True, GOLD)
                    self.screen.blit(ct, (30, box_y + 5))
                    break
        # Text with typewriter effect
        chars_shown = 0
        ty = box_y + 22
        for line in scene["text"]:
            if chars_shown + len(line) <= self.text_progress:
                t = self.font_sm.render(line, True, WHITE)
                self.screen.blit(t, (35, ty))
                chars_shown += len(line)
            else:
                remaining = self.text_progress - chars_shown
                if remaining > 0:
                    partial = line[:remaining]
                    t = self.font_sm.render(partial, True, WHITE)
                    self.screen.blit(t, (35, ty))
                break
            ty += 18
        # Choices
        max_chars = sum(len(line) for line in scene["text"])
        if self.text_progress >= max_chars and scene["choices"]:
            cy = box_y + box_h - 10 - len(scene["choices"]) * 24
            for i, (text, _) in enumerate(scene["choices"]):
                col = GOLD if i == self.selected_choice else GRAY
                prefix = ">" if i == self.selected_choice else " "
                ct = self.font_sm.render(f" {prefix} {text}", True, col)
                self.screen.blit(ct, (40, cy + i * 24))
        elif self.text_progress >= max_chars and not scene["choices"]:
            pt = self.font_xs.render("Click or press ENTER to continue...", True, GRAY)
            self.screen.blit(pt, (WIDTH // 2 - pt.get_width() // 2, box_y + box_h - 20))
        # HUD
        self.draw_hud()

    def draw_hud(self):
        """Draw player stats HUD at top."""
        # Background bar
        pygame.draw.rect(self.screen, (0, 0, 0, 180), (0, 0, WIDTH, 32))
        pygame.draw.rect(self.screen, DKGRAY, (0, 0, WIDTH, 32))
        # Name + mob
        mob_label = self.state.mob_type.title() if not self.state.is_human else "Human"
        name_t = self.font_xs.render(f"{self.state.name} the {mob_label}", True, WHITE)
        self.screen.blit(name_t, (10, 8))
        # HP bar
        hp_x = 200
        hp_w = 120
        pygame.draw.rect(self.screen, (60, 0, 0), (hp_x, 8, hp_w, 16))
        hp_fill = max(0, self.state.hp / self.state.max_hp)
        col = GREEN if hp_fill > 0.5 else YELLOW if hp_fill > 0.25 else RED
        pygame.draw.rect(self.screen, col, (hp_x, 8, int(hp_w * hp_fill), 16))
        hp_t = self.font_xs.render(f"HP {self.state.hp}/{self.state.max_hp}", True, WHITE)
        self.screen.blit(hp_t, (hp_x + 5, 9))
        # Level
        lv_t = self.font_xs.render(f"Lv{self.state.level}", True, GOLD)
        self.screen.blit(lv_t, (340, 8))
        # XP bar
        xp_x = 380
        xp_w = 80
        pygame.draw.rect(self.screen, (0, 0, 60), (xp_x, 8, xp_w, 16))
        xp_fill = self.state.xp / self.state.xp_next if self.state.xp_next > 0 else 0
        pygame.draw.rect(self.screen, CYAN, (xp_x, 8, int(xp_w * xp_fill), 16))
        xp_t = self.font_xs.render(f"XP {self.state.xp}/{self.state.xp_next}", True, WHITE)
        self.screen.blit(xp_t, (xp_x + 5, 9))
        # ATK / DEF
        stat_t = self.font_xs.render(f"ATK:{self.state.atk} DEF:{self.state.defense}", True, ORANGE)
        self.screen.blit(stat_t, (480, 8))
        # Emeralds
        em_t = self.font_xs.render(f"Em:{self.state.emeralds}", True, GREEN)
        self.screen.blit(em_t, (620, 8))
        # Items count
        it_t = self.font_xs.render(f"Items:{len(self.state.inventory)}", True, GRAY)
        self.screen.blit(it_t, (700, 8))
        # Quests
        qt = self.font_xs.render(f"Q:{len(self.state.quests_active)}", True, YELLOW)
        self.screen.blit(qt, (800, 8))

    # ── CHOP WOOD MINIGAME ────────────────────────────────────────────
    def update_chop(self, dt, events):
        speed = 2 + self.chop_count * 0.3  # Gets faster
        self.chop_bar += self.chop_dir * speed * dt * 60
        if self.chop_bar >= 100:
            self.chop_bar = 100
            self.chop_dir = -1
        elif self.chop_bar <= 0:
            self.chop_bar = 0
            self.chop_dir = 1
        for e in events:
            if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) or \
               (e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE):
                # Green zone is 35-65
                if 35 <= self.chop_bar <= 65:
                    self.chop_hits += 1
                    self.chop_count += 1
                    self.notification = f"CHOP! {self.chop_hits}/10 Logs"
                    self.notif_timer = 0.8
                    if self.chop_hits >= 10:
                        self.state.wood_count = 10
                        self.state.gain_xp(30)
                        self.phase = "story"
                        self.goto_scene("wood_complete")
                else:
                    self.chop_count += 1
                    self.notification = "MISS! Try again!"
                    self.notif_timer = 0.8

    def draw_chop(self):
        self.screen.fill((40, 80, 40))
        # Trees
        for tx in range(5):
            x = 50 + tx * 180
            pygame.draw.rect(self.screen, DKBROWN, (x, 100, 20, 200))
            pygame.draw.circle(self.screen, LEAF, (x + 10, 100), 50)
        # UI
        t = self.font_lg.render("CHOP WOOD!", True, WHITE)
        self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 20))
        count_t = self.font_md.render(f"Logs: {self.chop_hits} / 10", True, GOLD)
        self.screen.blit(count_t, (WIDTH // 2 - count_t.get_width() // 2, 60))
        # Timing bar
        bar_x = WIDTH // 2 - 200
        bar_y = HEIGHT - 120
        bar_w = 400
        bar_h = 30
        pygame.draw.rect(self.screen, DKGRAY, (bar_x, bar_y, bar_w, bar_h))
        # Green zone
        gz_start = int(bar_w * 0.35)
        gz_end = int(bar_w * 0.65)
        pygame.draw.rect(self.screen, GREEN, (bar_x + gz_start, bar_y, gz_end - gz_start, bar_h))
        # Marker
        mx = bar_x + int(bar_w * self.chop_bar / 100)
        pygame.draw.rect(self.screen, WHITE, (mx - 3, bar_y - 5, 6, bar_h + 10))
        hint = self.font_sm.render("Click or SPACE in the GREEN zone!", True, WHITE)
        self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 70))

    # ── COMBAT MINIGAME ───────────────────────────────────────────────
    def _combat_do_attack(self):
        dmg = max(1, self.state.atk - self.combat_enemy.get("def", 0) + random.randint(-2, 3))
        if self.state.mob_type == "wolf":
            dmg += 1
        self.combat_enemy_hp -= dmg
        self.combat_log.append(f"You attack for {dmg}!")
        self.combat_anim = "player_hit"
        self.combat_anim_timer = 0.3
        self.combat_player_cd = 0.6
        if self.combat_enemy_hp <= 0:
            self.combat_enemy_hp = 0
            self.combat_result = "win"
            self.combat_log.append(f"{self.combat_enemy['name']} defeated!")

    def _combat_do_block(self):
        self.combat_block = True
        self.combat_log.append("Blocking...")

    def _combat_do_dodge(self):
        self.combat_dodge = True
        self.combat_dodge_timer = 0.4
        self.combat_log.append("Dodging!")

    def start_combat(self, enemy):
        self.phase = "minigame_combat"
        self.combat_enemy = enemy
        self.combat_enemy_hp = enemy["hp"]
        self.combat_enemy_max_hp = enemy["hp"]
        self.combat_player_cd = 0
        self.combat_enemy_cd = 1.5
        self.combat_block = False
        self.combat_dodge = False
        self.combat_dodge_timer = 0
        self.combat_log = [f"{enemy['name']} appears!"]
        self.combat_anim = ""
        self.combat_anim_timer = 0
        self.combat_result = None

    def update_combat(self, dt, events):
        if self.combat_result:
            for e in events:
                if (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE)) or \
                   (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1):
                    if self.combat_result == "win":
                        self.state.gain_xp(40 + self.combat_enemy_max_hp // 2)
                        self.state.combat_skill += 1
                        self.phase = "story"
                        # Figure out victory scene
                        scene = self.get_scene()
                        enemy_name = self.combat_enemy["name"].lower()
                        if "brio" in enemy_name:
                            self.goto_scene("combat_win")
                        elif "zombie" in enemy_name:
                            self.goto_scene("zombie_victory")
                        elif "spider" in enemy_name:
                            self.goto_scene("spider_victory")
                        elif "skeleton" in enemy_name or "spawner" in enemy_name:
                            self.goto_scene("spawner_victory")
                        else:
                            self.goto_scene("village_return")
                    else:
                        self.state.hp = self.state.max_hp // 2
                        self.phase = "story"
                        self.notification = "You were defeated... but survived."
                        self.notif_timer = 2
            return
        # Cooldowns
        if self.combat_player_cd > 0:
            self.combat_player_cd -= dt
        if self.combat_dodge_timer > 0:
            self.combat_dodge_timer -= dt
            if self.combat_dodge_timer <= 0:
                self.combat_dodge = False
        self.combat_enemy_cd -= dt
        if self.combat_anim_timer > 0:
            self.combat_anim_timer -= dt
        # Enemy attack
        if self.combat_enemy_cd <= 0 and not self.combat_result:
            enemy_dmg = max(1, self.combat_enemy["atk"] - self.state.defense // 2)
            if self.combat_block:
                enemy_dmg = max(1, enemy_dmg // 3)
                self.combat_log.append(f"BLOCKED! {self.combat_enemy['name']} deals {enemy_dmg}")
                self.combat_anim = "block"
            elif self.combat_dodge:
                enemy_dmg = 0
                self.combat_log.append("DODGED!")
                self.combat_anim = "dodge"
            else:
                self.combat_log.append(f"{self.combat_enemy['name']} hits you for {enemy_dmg}!")
                self.combat_anim = "enemy_hit"
            self.state.hp -= enemy_dmg
            self.combat_anim_timer = 0.4
            self.combat_enemy_cd = 1.5 + random.random()
            self.combat_block = False
            if self.state.hp <= 0:
                self.state.hp = 0
                self.combat_result = "lose"
                self.combat_log.append("You were defeated!")
        # Combat button rects for mouse
        ctrl_y = HEIGHT - 100
        atk_rect = pygame.Rect(50, ctrl_y - 5, 200, 35)
        blk_rect = pygame.Rect(330, ctrl_y - 5, 200, 35)
        dge_rect = pygame.Rect(610, ctrl_y - 5, 230, 35)
        for e in events:
            # Left-click = Attack (like Minecraft!), Right-click = Block
            if e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = e.pos
                if e.button == 1:  # Left click
                    if atk_rect.collidepoint(mx, my) and self.combat_player_cd <= 0:
                        self._combat_do_attack()
                    elif blk_rect.collidepoint(mx, my):
                        self._combat_do_block()
                    elif dge_rect.collidepoint(mx, my) and self.combat_dodge_timer <= 0:
                        self._combat_do_dodge()
                    elif self.combat_player_cd <= 0:
                        # Click anywhere else = attack (Minecraft left-click)
                        self._combat_do_attack()
                elif e.button == 3:  # Right click = block (Minecraft shield)
                    self._combat_do_block()
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_a and self.combat_player_cd <= 0:
                    self._combat_do_attack()
                elif e.key == pygame.K_d:
                    self._combat_do_block()
                elif e.key == pygame.K_SPACE and self.combat_dodge_timer <= 0:
                    self._combat_do_dodge()
        # Trim log
        if len(self.combat_log) > 8:
            self.combat_log = self.combat_log[-8:]

    def draw_combat(self):
        self.screen.fill((30, 25, 20))
        # Enemy
        et = self.font_md.render(self.combat_enemy["name"], True, RED)
        self.screen.blit(et, (WIDTH // 2 - et.get_width() // 2, 20))
        # Enemy HP bar
        ehp_x = WIDTH // 2 - 100
        ehp_w = 200
        pygame.draw.rect(self.screen, (60, 0, 0), (ehp_x, 50, ehp_w, 20))
        ehp_fill = max(0, self.combat_enemy_hp / self.combat_enemy_max_hp)
        pygame.draw.rect(self.screen, RED, (ehp_x, 50, int(ehp_w * ehp_fill), 20))
        ehp_t = self.font_xs.render(f"{self.combat_enemy_hp}/{self.combat_enemy_max_hp}", True, WHITE)
        self.screen.blit(ehp_t, (ehp_x + ehp_w // 2 - ehp_t.get_width() // 2, 52))
        # Enemy sprite (simple)
        ex = WIDTH // 2 - 20
        ey = 100
        shake_x = int(math.sin(time.time() * 30) * 5) if self.combat_anim == "player_hit" and self.combat_anim_timer > 0 else 0
        enemy_name = self.combat_enemy["name"].lower()
        if "zombie" in enemy_name:
            # Green zombie
            for bx in range(3):
                for by in range(4):
                    draw_pixel_block(self.screen, ex + shake_x + bx * 12, ey + by * 12, 12, (50, 120, 50))
            pygame.draw.rect(self.screen, BLACK, (ex + shake_x + 4, ey + 8, 6, 4))
            pygame.draw.rect(self.screen, BLACK, (ex + shake_x + 26, ey + 8, 6, 4))
        elif "spider" in enemy_name:
            pygame.draw.ellipse(self.screen, (50, 40, 40), (ex + shake_x - 10, ey + 10, 60, 30))
            for i in range(4):
                pygame.draw.line(self.screen, (40, 30, 30),
                                 (ex + shake_x + 10 + i * 10, ey + 25),
                                 (ex + shake_x - 15 + i * 15, ey + 50), 2)
            pygame.draw.rect(self.screen, RED, (ex + shake_x + 5, ey + 15, 5, 5))
            pygame.draw.rect(self.screen, RED, (ex + shake_x + 30, ey + 15, 5, 5))
        elif "skeleton" in enemy_name or "spawner" in enemy_name:
            for by in range(5):
                draw_pixel_block(self.screen, ex + shake_x + 8, ey + by * 10, 10, WHITE)
            pygame.draw.rect(self.screen, BLACK, (ex + shake_x + 10, ey + 4, 3, 3))
            pygame.draw.rect(self.screen, BLACK, (ex + shake_x + 18, ey + 4, 3, 3))
            # Bow
            pygame.draw.line(self.screen, BROWN, (ex + shake_x + 30, ey), (ex + shake_x + 30, ey + 40), 2)
        else:
            # Generic humanoid (Brio)
            draw_pixel_block(self.screen, ex + shake_x + 4, ey, 20, (180, 140, 100))
            for by in range(3):
                draw_pixel_block(self.screen, ex + shake_x, ey + 28 + by * 12, 28, (120, 80, 40))
            # Sword
            pygame.draw.rect(self.screen, GRAY, (ex + shake_x + 32, ey + 20, 4, 30))
            pygame.draw.rect(self.screen, BROWN, (ex + shake_x + 30, ey + 18, 8, 4))
        # Player sprite
        py_y = HEIGHT - 300
        px = 100
        p_shake = int(math.sin(time.time() * 30) * 5) if self.combat_anim == "enemy_hit" and self.combat_anim_timer > 0 else 0
        if self.state.is_human:
            draw_human(self.screen, px + p_shake, py_y, 2, self.state.mob_type)
        else:
            if self.state.mob_type == "cat":
                draw_cat(self.screen, px + p_shake, py_y, 3)
            elif self.state.mob_type == "wolf":
                draw_wolf(self.screen, px + p_shake, py_y, 3)
            else:
                draw_bunny(self.screen, px + p_shake, py_y, 3)
        # Player HP bar
        php_x = 60
        php_w = 150
        pygame.draw.rect(self.screen, (60, 0, 0), (php_x, HEIGHT - 320, php_w, 16))
        php_fill = max(0, self.state.hp / self.state.max_hp)
        hcol = GREEN if php_fill > 0.5 else YELLOW if php_fill > 0.25 else RED
        pygame.draw.rect(self.screen, hcol, (php_x, HEIGHT - 320, int(php_w * php_fill), 16))
        php_t = self.font_xs.render(f"{self.state.hp}/{self.state.max_hp}", True, WHITE)
        self.screen.blit(php_t, (php_x + 5, HEIGHT - 319))
        name_t = self.font_sm.render(self.state.name, True, WHITE)
        self.screen.blit(name_t, (php_x, HEIGHT - 340))
        # Combat controls
        ctrl_y = HEIGHT - 100
        controls = [
            ("[LClick/A] Attack", ORANGE if self.combat_player_cd <= 0 else DKGRAY),
            ("[RClick/D] Block", BLUE if not self.combat_block else CYAN),
            ("[SPACE] Dodge", GREEN if self.combat_dodge_timer <= 0 else DKGRAY),
        ]
        for i, (txt, col) in enumerate(controls):
            ct = self.font_md.render(txt, True, col)
            self.screen.blit(ct, (50 + i * 280, ctrl_y))
        # Combat log
        log_x = WIDTH - 320
        log_y = 100
        pygame.draw.rect(self.screen, (15, 15, 20), (log_x - 5, log_y - 5, 310, 200))
        lt = self.font_xs.render("— Combat Log —", True, GRAY)
        self.screen.blit(lt, (log_x, log_y))
        for i, msg in enumerate(self.combat_log[-7:]):
            col = WHITE
            if "BLOCKED" in msg or "DODGED" in msg:
                col = CYAN
            elif "defeated" in msg.lower():
                col = GOLD
            elif "hit you" in msg:
                col = RED
            elif "attack for" in msg:
                col = ORANGE
            mt = self.font_xs.render(msg, True, col)
            self.screen.blit(mt, (log_x, log_y + 20 + i * 18))
        # Result overlay
        if self.combat_result:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(160)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            if self.combat_result == "win":
                rt = self.font_lg.render("VICTORY!", True, GOLD)
                xp_gain = 40 + self.combat_enemy_max_hp // 2
                xp_t = self.font_md.render(f"+{xp_gain} XP", True, CYAN)
            else:
                rt = self.font_lg.render("DEFEATED...", True, RED)
                xp_t = self.font_md.render("You barely escaped...", True, GRAY)
            self.screen.blit(rt, (WIDTH // 2 - rt.get_width() // 2, HEIGHT // 2 - 40))
            self.screen.blit(xp_t, (WIDTH // 2 - xp_t.get_width() // 2, HEIGHT // 2 + 10))
            cont = self.font_sm.render("Click or press ENTER to continue", True, WHITE)
            self.screen.blit(cont, (WIDTH // 2 - cont.get_width() // 2, HEIGHT // 2 + 50))

    # ── GAME OVER ─────────────────────────────────────────────────────
    def update_game_over(self, dt, events):
        for e in events:
            if (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE)) or \
               (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1):
                self.phase = "title"
                self.selected_choice = 0

    def draw_game_over(self):
        self.screen.fill(BLACK)
        t = self.font_lg.render("GAME OVER", True, RED)
        self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 - 40))
        st = self.font_md.render("Your adventure has ended... for now.", True, GRAY)
        self.screen.blit(st, (WIDTH // 2 - st.get_width() // 2, HEIGHT // 2 + 10))
        ct = self.font_sm.render("Click or press ENTER for title screen", True, WHITE)
        self.screen.blit(ct, (WIDTH // 2 - ct.get_width() // 2, HEIGHT // 2 + 50))


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
