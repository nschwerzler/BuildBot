"""
PET QUEST: FIND YOUR OWNER
A 2.5D Dungeon Crawler where you play as a lost pet searching through
dangerous dungeons to find your beloved owner.

Controls:
  WASD / Arrow Keys - Move
  SPACE - Attack
  LEFT CLICK - Spit Attack (ranged)
  E - Use Item
  TAB - Inventory
  1-3 - Switch items
  ESC - Pause
"""
import pygame
import random
import math
import sys
import json
import os
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict

SCREEN_W, SCREEN_H = 960, 720
TILE_SIZE = 48
FPS = 60
DUNGEON_W, DUNGEON_H = 40, 30
WALL_HEIGHT = 18  # 2.5D wall extrusion height

# Colors
C_BLACK = (0, 0, 0)
C_WHITE = (255, 255, 255)
C_GRAY = (80, 80, 80)
C_DARK_GRAY = (40, 40, 40)
C_FLOOR = (55, 45, 40)
C_FLOOR2 = (50, 40, 35)
C_WALL_TOP = (90, 75, 65)
C_WALL_FRONT = (60, 50, 42)
C_WALL_SHADOW = (35, 28, 22)
C_DOOR = (120, 85, 50)
C_STAIRS = (180, 160, 50)
C_RED = (220, 50, 50)
C_GREEN = (50, 200, 80)
C_BLUE = (60, 120, 220)
C_YELLOW = (240, 220, 60)
C_ORANGE = (240, 150, 40)
C_PURPLE = (160, 60, 200)
C_PINK = (240, 120, 160)
C_CYAN = (60, 200, 220)
C_BROWN = (140, 90, 50)

# === ENUMS ===
class TileType(Enum):
    VOID = 0
    FLOOR = 1
    WALL = 2
    DOOR = 3
    STAIRS_DOWN = 4
    STAIRS_UP = 5
    CLUE = 6
    TRAP = 7

class PetType(Enum):
    DOG = "Dog"
    CAT = "Cat"
    HAMSTER = "Hamster"

class ItemType(Enum):
    TREAT = "Treat"
    BANDAGE = "Bandage"
    BONE = "Bone"
    CATNIP = "Catnip"
    SEED = "Seed"
    COLLAR = "Collar"
    TOY = "Squeaky Toy"
    JERKY = "Jerky"
    FISH_FEAST = "Fish Feast"
    POWER_KIBBLE = "Power Kibble"
    IRON_COLLAR = "Iron Collar"
    SWIFT_HARNESS = "Swift Harness"
    SPIKED_VEST = "Spiked Vest"
    KEY = "Key"

class EnemyType(Enum):
    RAT = "Rat"
    SPIDER = "Spider"
    BAT = "Bat"
    SNAKE = "Snake"
    GHOST_CAT = "Ghost Cat"
    SHADOW_HOUND = "Shadow Hound"
    SLIME = "Slime"
    FIRE_IMP = "Fire Imp"
    SCORPION = "Scorpion"
    MUSHROOM_BRUTE = "Mushroom Brute"
    MINI_WARDEN = "Mini Warden"
    BOSS_CAGE_KEEPER = "Cage Keeper"
    BOSS_ABYSS_WARDEN = "Abyss Warden"

# === DATA CLASSES ===
@dataclass
class Item:
    item_type: ItemType
    name: str
    description: str
    heal: int = 0
    damage_boost: int = 0
    max_hp_boost: int = 0
    speed_boost: float = 0.0
    spit_cd_boost: float = 0.0
    special_cd_boost: float = 0.0
    count: int = 1

@dataclass
class Enemy:
    enemy_type: EnemyType
    x: float
    y: float
    hp: int
    max_hp: int
    damage: int
    speed: float
    color: Tuple[int, int, int]
    size: int = 12
    attack_cooldown: float = 0
    stun_timer: float = 0
    anim_timer: float = 0
    is_boss: bool = False
    alert: bool = False
    patrol_angle: float = 0
    spawn_x: float = 0
    spawn_y: float = 0
    drops: List[ItemType] = field(default_factory=list)

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    color: Tuple[int, int, int]
    life: float
    max_life: float
    size: float = 3

@dataclass
class Projectile:
    x: float
    y: float
    vx: float
    vy: float
    damage: int
    color: Tuple[int, int, int]
    life: float = 2.0
    size: float = 5
    trail_timer: float = 0.0

@dataclass 
class FloatingText:
    x: float
    y: float
    text: str
    color: Tuple[int, int, int]
    life: float = 1.0

@dataclass
class Clue:
    text: str
    found: bool = False

# === PET STATS ===
PET_STATS = {
    PetType.DOG: {"hp": 12, "attack": 3, "speed": 2.8, "special": "Bark (stun enemies)", "color": (180, 130, 70)},
    PetType.CAT: {"hp": 9, "attack": 4, "speed": 3.5, "special": "Pounce (dash attack)", "color": (200, 160, 80)},
    PetType.HAMSTER: {"hp": 8, "attack": 2, "speed": 3.0, "special": "Burrow (dodge + heal)", "color": (220, 190, 140)},
}

# === CLUE DATABASE ===
CLUE_TEXTS = [
    "A torn photo... it shows a human hand petting something soft.",
    "You smell something familiar... your owner's scent! They were HERE.",
    "A note: 'I will find you, my little friend. Wait for me.'",
    "Scratch marks on the wall... someone was dragged deeper.",
    "Your owner's favorite sweater! The scent is still warm...",
    "A trail of treats... your owner left these for you to follow!",
    "Pawprints AND footprints lead deeper into the dungeon.",
    "You hear a distant voice calling your name...",
    "A broken leash on the ground. Your owner fought to stay.",
    "A locket with your picture inside. They never forgot you.",
]

# === DUNGEON GENERATOR ===
class DungeonGenerator:
    def __init__(self, width: int, height: int, floor_num: int):
        self.w = width
        self.h = height
        self.floor_num = floor_num
        self.tiles = [[TileType.VOID for _ in range(width)] for _ in range(height)]
        self.rooms: List[pygame.Rect] = []
        self.enemy_spawns: List[Tuple[int, int]] = []
        self.item_spawns: List[Tuple[int, int, ItemType]] = []
        self.clue_positions: List[Tuple[int, int]] = []
        self.stairs_down: Optional[Tuple[int, int]] = None
        self.stairs_up: Optional[Tuple[int, int]] = None
        self.start_pos: Tuple[int, int] = (5, 5)

    def generate(self) -> None:
        num_rooms = 6 + self.floor_num * 2
        min_size, max_size = 4, 8

        for _ in range(num_rooms * 5):
            w = random.randint(min_size, max_size)
            h = random.randint(min_size, max_size)
            x = random.randint(1, self.w - w - 1)
            y = random.randint(1, self.h - h - 1)
            room = pygame.Rect(x, y, w, h)

            if not any(room.inflate(2, 2).colliderect(r) for r in self.rooms):
                self.rooms.append(room)
                self._carve_room(room)
                if len(self.rooms) >= num_rooms:
                    break

        # Connect rooms with corridors
        for i in range(len(self.rooms) - 1):
            self._connect_rooms(self.rooms[i], self.rooms[i + 1])

        # Place stairs
        if self.rooms:
            first_room = self.rooms[0]
            self.start_pos = (first_room.centerx, first_room.centery)
            self.stairs_up = (first_room.centerx, first_room.centery)
            self.tiles[first_room.centery][first_room.centerx] = TileType.STAIRS_UP

            last_room = self.rooms[-1]
            self.stairs_down = (last_room.centerx, last_room.centery)
            self.tiles[last_room.centery][last_room.centerx] = TileType.STAIRS_DOWN

        # Place enemies
        for room in self.rooms[1:]:
            num_enemies = random.randint(1, 2 + self.floor_num // 2)
            for _ in range(num_enemies):
                ex = random.randint(room.left + 1, room.right - 1)
                ey = random.randint(room.top + 1, room.bottom - 1)
                self.enemy_spawns.append((ex, ey))

        # Place items
        for room in self.rooms[1:-1]:
            if random.random() < 0.5:
                ix = random.randint(room.left + 1, room.right - 1)
                iy = random.randint(room.top + 1, room.bottom - 1)
                item = random.choice([
                    ItemType.TREAT,
                    ItemType.BANDAGE,
                    ItemType.BONE,
                    ItemType.TOY,
                    ItemType.JERKY,
                    ItemType.FISH_FEAST,
                    ItemType.POWER_KIBBLE,
                ])
                self.item_spawns.append((ix, iy, item))

        # Place clue in a random middle room
        if len(self.rooms) > 2:
            clue_room = random.choice(self.rooms[1:-1])
            cx = clue_room.centerx
            cy = clue_room.centery
            if self.tiles[cy][cx] == TileType.FLOOR:
                self.tiles[cy][cx] = TileType.CLUE
                self.clue_positions.append((cx, cy))

        # Place traps on higher floors
        if self.floor_num >= 2:
            for room in self.rooms[1:]:
                if random.random() < 0.3:
                    tx = random.randint(room.left + 1, room.right - 1)
                    ty = random.randint(room.top + 1, room.bottom - 1)
                    if self.tiles[ty][tx] == TileType.FLOOR:
                        self.tiles[ty][tx] = TileType.TRAP

        # Add walls around floors
        self._add_walls()

    def _carve_room(self, room: pygame.Rect) -> None:
        for y in range(room.top, room.bottom):
            for x in range(room.left, room.right):
                if 0 <= x < self.w and 0 <= y < self.h:
                    self.tiles[y][x] = TileType.FLOOR

    def _connect_rooms(self, room1: pygame.Rect, room2: pygame.Rect) -> None:
        x1, y1 = room1.centerx, room1.centery
        x2, y2 = room2.centerx, room2.centery

        if random.random() < 0.5:
            self._carve_h_corridor(x1, x2, y1)
            self._carve_v_corridor(y1, y2, x2)
        else:
            self._carve_v_corridor(y1, y2, x1)
            self._carve_h_corridor(x1, x2, y2)

    def _carve_h_corridor(self, x1: int, x2: int, y: int) -> None:
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < self.w and 0 <= y < self.h:
                if self.tiles[y][x] == TileType.VOID:
                    self.tiles[y][x] = TileType.FLOOR
                # Widen corridor
                if 0 <= y - 1 < self.h and self.tiles[y-1][x] == TileType.VOID:
                    self.tiles[y-1][x] = TileType.FLOOR

    def _carve_v_corridor(self, y1: int, y2: int, x: int) -> None:
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x < self.w and 0 <= y < self.h:
                if self.tiles[y][x] == TileType.VOID:
                    self.tiles[y][x] = TileType.FLOOR
                if 0 <= x + 1 < self.w and self.tiles[y][x+1] == TileType.VOID:
                    self.tiles[y][x+1] = TileType.FLOOR

    def _add_walls(self) -> None:
        for y in range(self.h):
            for x in range(self.w):
                if self.tiles[y][x] == TileType.VOID:
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.w and 0 <= ny < self.h:
                                if self.tiles[ny][nx] in (TileType.FLOOR, TileType.DOOR, 
                                                           TileType.STAIRS_DOWN, TileType.STAIRS_UP,
                                                           TileType.CLUE, TileType.TRAP):
                                    self.tiles[y][x] = TileType.WALL
                                    break
                        else:
                            continue
                        break

# === MAIN GAME CLASS ===
class PetDungeonCrawler:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Pet Quest: Find Your Owner")
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("Arial", 36, bold=True)
        self.font_med = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_sm = pygame.font.SysFont("Arial", 16)
        self.font_tiny = pygame.font.SysFont("Arial", 13)

        # Game state
        self.state = "title"  # title, select, difficulty, prep, infinite_prompt, floor_reward, playing, inventory, paused, clue, dead, victory
        self.pet_type: Optional[PetType] = None
        self.pending_pet: Optional[PetType] = None
        self.selection_index = 0
        self.difficulty_options = ["Easy", "Normal", "Hard", "Infinite"]
        self.difficulty_index = 1
        self.difficulty = "Normal"
        self.prep_item_index = 0
        self.prep_gear_index = 0
        self.prep_item_options = [ItemType.TREAT, ItemType.BANDAGE, ItemType.BONE, ItemType.TOY]
        self.prep_gear_options = [
            {
                "name": "Comfy Harness",
                "description": "+2 HP and slightly faster",
                "hp_bonus": 2,
                "atk_bonus": 0,
                "spd_bonus": 0.2,
                "spit_cd_bonus": 0.0,
                "special_cd_bonus": 0.0,
            },
            {
                "name": "Battle Bell",
                "description": "+1 attack and faster specials",
                "hp_bonus": 0,
                "atk_bonus": 1,
                "spd_bonus": 0.0,
                "spit_cd_bonus": 0.0,
                "special_cd_bonus": -0.4,
            },
            {
                "name": "Swift Boots",
                "description": "Higher speed and faster spit",
                "hp_bonus": 0,
                "atk_bonus": 0,
                "spd_bonus": 0.35,
                "spit_cd_bonus": -0.1,
                "special_cd_bonus": 0.0,
            },
        ]
        self.equipped_gear = self.prep_gear_options[0]
        self.floor_reward_choices: List[Dict[str, float]] = []
        self.floor_reward_index = 0
        self.floor_reward_completed_floor = 0
        self.floor_reward_bonus_loot: Optional[ItemType] = None

        self.enemy_hp_mult = 1.0
        self.enemy_dmg_mult = 1.0
        self.enemy_speed_mult = 1.0
        self.start_item_count = 1
        self.is_infinite_mode = False
        self.infinite_save_path = "pet_dungeon_infinite_save.json"
        self.infinite_save_timer = 0.0

        # Player
        self.px = 0.0
        self.py = 0.0
        self.hp = 10
        self.max_hp = 10
        self.attack_power = 3
        self.speed = 2.5
        self.facing = 0.0  # radians
        self.attack_timer = 0.0
        self.attack_cooldown = 0.3
        self.invulnerable = 0.0
        self.special_cooldown = 0.0
        self.special_max_cd = 3.0
        self.spit_cooldown = 0.0
        self.spit_max_cd = 0.5
        self.xp = 0
        self.level = 1
        self.xp_to_next = 10

        # Dungeon
        self.floor_num = 1
        self.max_floors = 5
        self.dungeon: Optional[DungeonGenerator] = None
        self.enemies: List[Enemy] = []
        self.items_on_ground: List[Tuple[float, float, Item]] = []
        self.particles: List[Particle] = []
        self.projectiles: List[Projectile] = []
        self.floating_texts: List[FloatingText] = []
        self.inventory: List[Item] = []
        self.selected_item = 0
        self.clues_found: List[Clue] = []
        self.current_clue_text = ""
        self.keys_held = 0

        # Camera
        self.cam_x = 0.0
        self.cam_y = 0.0

        # Animation
        self.walk_anim = 0.0
        self.time = 0.0
        self.screen_shake = 0.0
        self.transition_alpha = 0
        self.transitioning = False
        self.transition_target = ""

        # Minimap
        self.explored = set()
        self.dungeon_w = DUNGEON_W
        self.dungeon_h = DUNGEON_H

        # Sounds
        self._init_sounds()

    def _add_item_to_inventory(self, item: Item) -> bool:
        for inv_item in self.inventory:
            if inv_item.item_type == item.item_type:
                inv_item.count += item.count
                return True
        if len(self.inventory) < 6:
            self.inventory.append(item)
            return True
        return False

    def _roll_floor_reward_choices(self) -> List[Dict[str, float]]:
        pool = [
            {"name": "Savage Fang", "description": "+2 ATK permanently", "atk_bonus": 2, "hp_bonus": 0, "spd_bonus": 0.0, "spit_cd_bonus": 0.0, "special_cd_bonus": 0.0},
            {"name": "Guardian Plate", "description": "+6 max HP permanently", "atk_bonus": 0, "hp_bonus": 6, "spd_bonus": 0.0, "spit_cd_bonus": 0.0, "special_cd_bonus": 0.0},
            {"name": "Wind Anklet", "description": "+0.15 speed permanently", "atk_bonus": 0, "hp_bonus": 0, "spd_bonus": 0.15, "spit_cd_bonus": 0.0, "special_cd_bonus": 0.0},
            {"name": "Spit Gland", "description": "Spit cooldown -0.05s permanently", "atk_bonus": 0, "hp_bonus": 0, "spd_bonus": 0.0, "spit_cd_bonus": -0.05, "special_cd_bonus": 0.0},
            {"name": "Focus Totem", "description": "Special cooldown -0.20s permanently", "atk_bonus": 0, "hp_bonus": 0, "spd_bonus": 0.0, "spit_cd_bonus": 0.0, "special_cd_bonus": -0.2},
            {"name": "Battle Chow", "description": "+1 ATK and +2 max HP permanently", "atk_bonus": 1, "hp_bonus": 2, "spd_bonus": 0.0, "spit_cd_bonus": 0.0, "special_cd_bonus": 0.0},
        ]
        return random.sample(pool, 3)

    def _open_floor_reward(self):
        self.floor_reward_choices = self._roll_floor_reward_choices()
        self.floor_reward_index = 0
        self.floor_reward_completed_floor = self.floor_num
        self.floor_reward_bonus_loot = None
        if self.floor_num % 5 == 0:
            self.floor_reward_bonus_loot = random.choice([
                ItemType.IRON_COLLAR,
                ItemType.SWIFT_HARNESS,
                ItemType.SPIKED_VEST,
                ItemType.POWER_KIBBLE,
                ItemType.FISH_FEAST,
            ])
        self.state = "floor_reward"

    def _apply_floor_reward_choice(self):
        if not self.floor_reward_choices:
            return
        choice = self.floor_reward_choices[self.floor_reward_index]
        self.attack_power += int(choice["atk_bonus"])
        hp_bonus = int(choice["hp_bonus"])
        if hp_bonus > 0:
            self.max_hp += hp_bonus
            self.hp = min(self.max_hp, self.hp + hp_bonus)
        self.speed = max(1.0, self.speed + float(choice["spd_bonus"]))
        self.spit_max_cd = max(0.2, self.spit_max_cd + float(choice["spit_cd_bonus"]))
        self.special_max_cd = max(1.0, self.special_max_cd + float(choice["special_cd_bonus"]))
        self.equipped_gear = {
            "name": choice["name"],
            "description": choice["description"],
            "hp_bonus": hp_bonus,
            "atk_bonus": int(choice["atk_bonus"]),
            "spd_bonus": float(choice["spd_bonus"]),
            "spit_cd_bonus": float(choice["spit_cd_bonus"]),
            "special_cd_bonus": float(choice["special_cd_bonus"]),
        }

        if self.floor_reward_bonus_loot:
            bonus_item = self._create_item(self.floor_reward_bonus_loot)
            bonus_item.count = 1
            if not self._add_item_to_inventory(bonus_item):
                if bonus_item.damage_boost:
                    self.attack_power += bonus_item.damage_boost
                if bonus_item.max_hp_boost:
                    self.max_hp += bonus_item.max_hp_boost
                    self.hp = min(self.max_hp, self.hp + bonus_item.max_hp_boost)
                if bonus_item.speed_boost:
                    self.speed = max(1.0, self.speed + bonus_item.speed_boost)
                if bonus_item.spit_cd_boost:
                    self.spit_max_cd = max(0.2, self.spit_max_cd + bonus_item.spit_cd_boost)
                if bonus_item.special_cd_boost:
                    self.special_max_cd = max(1.0, self.special_max_cd + bonus_item.special_cd_boost)

        self.state = "playing"
        self.transitioning = True
        self.transition_target = "next_floor"

    def _init_sounds(self):
        """Generate simple sound effects"""
        self.sounds = {}
        try:
            # Attack sound
            samples = []
            for i in range(2000):
                t = i / 22050
                val = int(math.sin(t * 800 * (1 - t * 3)) * 3000 * max(0, 1 - t * 5))
                samples.append(max(-32768, min(32767, val)))
            buf = bytes()
            for s in samples:
                buf += s.to_bytes(2, 'little', signed=True)
            snd = pygame.mixer.Sound(buffer=buf)
            snd.set_volume(0.3)
            self.sounds['attack'] = snd

            # Hit sound
            samples = []
            for i in range(1500):
                t = i / 22050
                val = int((random.random() * 2 - 1) * 4000 * max(0, 1 - t * 8))
                samples.append(max(-32768, min(32767, val)))
            buf = bytes()
            for s in samples:
                buf += s.to_bytes(2, 'little', signed=True)
            snd = pygame.mixer.Sound(buffer=buf)
            snd.set_volume(0.25)
            self.sounds['hit'] = snd

            # Pickup sound
            samples = []
            for i in range(3000):
                t = i / 22050
                freq = 400 + t * 1200
                val = int(math.sin(t * freq * 2 * math.pi) * 2000 * max(0, 1 - t * 5))
                samples.append(max(-32768, min(32767, val)))
            buf = bytes()
            for s in samples:
                buf += s.to_bytes(2, 'little', signed=True)
            snd = pygame.mixer.Sound(buffer=buf)
            snd.set_volume(0.3)
            self.sounds['pickup'] = snd

            # Stairs sound
            samples = []
            for i in range(5000):
                t = i / 22050
                freq = 200 + t * 400
                val = int(math.sin(t * freq * 2 * math.pi) * 2500 * max(0, 1 - t * 3))
                samples.append(max(-32768, min(32767, val)))
            buf = bytes()
            for s in samples:
                buf += s.to_bytes(2, 'little', signed=True)
            snd = pygame.mixer.Sound(buffer=buf)
            snd.set_volume(0.3)
            self.sounds['stairs'] = snd

            # Spit sound - wet pop
            samples = []
            for i in range(2500):
                t = i / 22050
                freq = 600 - t * 400
                val = int(math.sin(t * freq * 2 * math.pi) * 2500 * max(0, 1 - t * 4)
                          + (random.random() * 2 - 1) * 1000 * max(0, 0.3 - t))
                samples.append(max(-32768, min(32767, val)))
            buf = bytes()
            for s in samples:
                buf += s.to_bytes(2, 'little', signed=True)
            snd = pygame.mixer.Sound(buffer=buf)
            snd.set_volume(0.3)
            self.sounds['spit'] = snd
        except:
            pass

    def play_sound(self, name: str):
        if name in self.sounds:
            self.sounds[name].play()

    def _apply_difficulty_settings(self):
        if self.difficulty == "Easy":
            self.enemy_hp_mult = 0.85
            self.enemy_dmg_mult = 0.8
            self.enemy_speed_mult = 0.95
            self.start_item_count = 2
            self.max_floors = 4
            self.is_infinite_mode = False
        elif self.difficulty == "Hard":
            self.enemy_hp_mult = 1.25
            self.enemy_dmg_mult = 1.25
            self.enemy_speed_mult = 1.1
            self.start_item_count = 1
            self.max_floors = 8
            self.is_infinite_mode = False
        elif self.difficulty == "Infinite":
            self.enemy_hp_mult = 1.15
            self.enemy_dmg_mult = 1.2
            self.enemy_speed_mult = 1.08
            self.start_item_count = 1
            self.max_floors = 999999
            self.is_infinite_mode = True
        else:
            self.enemy_hp_mult = 1.0
            self.enemy_dmg_mult = 1.0
            self.enemy_speed_mult = 1.0
            self.start_item_count = 1
            self.max_floors = 5
            self.is_infinite_mode = False

    def _infinite_save_exists(self) -> bool:
        return os.path.exists(self.infinite_save_path)

    def _serialize_inventory(self) -> List[Dict[str, int]]:
        serialized = []
        for item in self.inventory:
            serialized.append({"item_type": item.item_type.name, "count": item.count})
        return serialized

    def _deserialize_inventory(self, raw: List[Dict[str, int]]) -> List[Item]:
        inv: List[Item] = []
        for entry in raw:
            try:
                item_type = ItemType[entry["item_type"]]
            except Exception:
                continue
            item = self._create_item(item_type)
            item.count = max(1, int(entry.get("count", 1)))
            inv.append(item)
        return inv

    def _save_infinite_progress(self):
        if not self.is_infinite_mode or not self.pet_type or self.state in ("dead", "victory"):
            return
        data = {
            "pet_type": self.pet_type.name,
            "difficulty": self.difficulty,
            "floor_num": self.floor_num,
            "level": self.level,
            "xp": self.xp,
            "xp_to_next": self.xp_to_next,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack_power": self.attack_power,
            "speed": self.speed,
            "keys_held": self.keys_held,
            "selected_item": self.selected_item,
            "inventory": self._serialize_inventory(),
            "clues": [c.text for c in self.clues_found],
            "equipped_gear": self.equipped_gear,
            "spit_max_cd": self.spit_max_cd,
            "special_max_cd": self.special_max_cd,
        }
        try:
            with open(self.infinite_save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _load_infinite_progress(self) -> bool:
        if not self._infinite_save_exists():
            return False
        try:
            with open(self.infinite_save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return False

        try:
            self.pet_type = PetType[data["pet_type"]]
        except Exception:
            return False

        self.difficulty = "Infinite"
        self._apply_difficulty_settings()
        self.floor_num = max(1, int(data.get("floor_num", 1)))
        self.level = max(1, int(data.get("level", 1)))
        self.xp = max(0, int(data.get("xp", 0)))
        self.xp_to_next = max(10, int(data.get("xp_to_next", 10)))
        self.max_hp = max(1, int(data.get("max_hp", PET_STATS[self.pet_type]["hp"])))
        self.hp = max(1, min(self.max_hp, int(data.get("hp", self.max_hp))))
        self.attack_power = max(1, int(data.get("attack_power", PET_STATS[self.pet_type]["attack"])))
        self.speed = max(1.0, float(data.get("speed", PET_STATS[self.pet_type]["speed"])))
        self.keys_held = max(0, int(data.get("keys_held", 0)))
        self.selected_item = max(0, int(data.get("selected_item", 0)))
        self.inventory = self._deserialize_inventory(data.get("inventory", []))
        if not self.inventory:
            self.inventory = [self._create_item(ItemType.TREAT)]
        self.selected_item = min(self.selected_item, len(self.inventory) - 1)
        self.clues_found = [Clue(str(text), True) for text in data.get("clues", [])]
        self.equipped_gear = data.get("equipped_gear", self.prep_gear_options[0])
        self.spit_max_cd = max(0.2, float(data.get("spit_max_cd", 0.5)))
        self.special_max_cd = max(1.5, float(data.get("special_max_cd", 3.0)))
        self.generate_floor()
        self.state = "playing"
        return True

    def _clear_infinite_save(self):
        if self._infinite_save_exists():
            try:
                os.remove(self.infinite_save_path)
            except Exception:
                pass

    def start_game(self, pet: PetType, difficulty: str = "Normal"):
        self.pet_type = pet
        self.difficulty = difficulty
        self._apply_difficulty_settings()
        stats = PET_STATS[pet]
        self.max_hp = stats["hp"]
        self.hp = self.max_hp
        self.attack_power = stats["attack"]
        self.speed = stats["speed"]
        self.spit_max_cd = 0.5
        self.special_max_cd = 3.0
        self.special_cooldown = 0.0
        self.floor_num = 1
        self.level = 1
        self.xp = 0
        self.xp_to_next = 10
        self.inventory = []
        self.clues_found = []
        self.keys_held = 0
        self.prep_item_index = 0
        self.prep_gear_index = 0
        self.equipped_gear = self.prep_gear_options[self.prep_gear_index]
        self.state = "prep"

    def _apply_prep_loadout(self):
        if not self.pet_type:
            return
        stats = PET_STATS[self.pet_type]
        gear = self.prep_gear_options[self.prep_gear_index]
        self.equipped_gear = gear
        self.max_hp = max(1, stats["hp"] + gear["hp_bonus"])
        self.hp = self.max_hp
        self.attack_power = max(1, stats["attack"] + gear["atk_bonus"])
        self.speed = max(1.0, stats["speed"] + gear["spd_bonus"])
        self.spit_max_cd = max(0.2, 0.5 + gear["spit_cd_bonus"])
        self.special_max_cd = max(1.5, 3.0 + gear["special_cd_bonus"])
        self.special_cooldown = 0.0
        self.inventory = []
        starter_item = self._create_item(self.prep_item_options[self.prep_item_index])
        starter_item.count = self.start_item_count
        self.inventory.append(starter_item)
        self.generate_floor()
        self.state = "playing"
        if self.is_infinite_mode:
            self._save_infinite_progress()

    # === DUNGEON SETUP ===
    def _is_boss_floor(self) -> bool:
        if self.is_infinite_mode:
            return self.floor_num % 5 == 0
        return self.floor_num == self.max_floors

    def generate_floor(self):
        if self.is_infinite_mode:
            self.dungeon_w = min(40 + self.floor_num * 2, 72)
            self.dungeon_h = min(30 + self.floor_num, 54)
        else:
            self.dungeon_w = DUNGEON_W
            self.dungeon_h = DUNGEON_H

        self.dungeon = DungeonGenerator(self.dungeon_w, self.dungeon_h, self.floor_num)
        self.dungeon.generate()
        self.px = float(self.dungeon.start_pos[0]) + 0.5
        self.py = float(self.dungeon.start_pos[1]) + 0.5
        self.enemies = []
        self.items_on_ground = []
        self.particles = []
        self.projectiles = []
        self.floating_texts = []
        self.explored = set()

        # Spawn enemies
        for ex, ey in self.dungeon.enemy_spawns:
            enemy = self._create_enemy(ex + 0.5, ey + 0.5)
            self.enemies.append(enemy)

        # Mini-bosses in random areas
        if self.dungeon.rooms and len(self.dungeon.rooms) > 3 and not self._is_boss_floor():
            mini_count = 1 + self.floor_num // 6
            candidate_rooms = self.dungeon.rooms[1:-1]
            random.shuffle(candidate_rooms)
            for room in candidate_rooms[:mini_count]:
                mini = self._create_miniboss(room.centerx + 0.5, room.centery + 0.5)
                self.enemies.append(mini)

        # Boss room every 5 floors in infinite (and final floor in non-infinite)
        if self._is_boss_floor() and self.dungeon.rooms:
            self.enemies = []
            boss_room = self.dungeon.rooms[-1]
            boss = self._create_boss(boss_room.centerx + 0.5, boss_room.centery + 0.5)
            self.enemies.append(boss)
            if self.floor_num >= 10:
                guard_a = self._create_miniboss(boss_room.centerx - 1.5, boss_room.centery + 0.5)
                guard_b = self._create_miniboss(boss_room.centerx + 1.5, boss_room.centery + 0.5)
                self.enemies.extend([guard_a, guard_b])

        # Spawn items
        for ix, iy, item_type in self.dungeon.item_spawns:
            item = self._create_item(item_type)
            self.items_on_ground.append((ix + 0.5, iy + 0.5, item))

        # Extra random gear in deeper infinite runs
        if self.is_infinite_mode and self.floor_num >= 6 and self.dungeon.rooms:
            extra_room = random.choice(self.dungeon.rooms[1:])
            gx = random.randint(extra_room.left + 1, extra_room.right - 1) + 0.5
            gy = random.randint(extra_room.top + 1, extra_room.bottom - 1) + 0.5
            gear_drop = random.choice([ItemType.IRON_COLLAR, ItemType.SWIFT_HARNESS, ItemType.SPIKED_VEST])
            self.items_on_ground.append((gx, gy, self._create_item(gear_drop)))

        # Key on every floor
        if self.dungeon.rooms and len(self.dungeon.rooms) > 2:
            key_room = self.dungeon.rooms[len(self.dungeon.rooms) // 2]
            kx = random.randint(key_room.left + 1, key_room.right - 1) + 0.5
            ky = random.randint(key_room.top + 1, key_room.bottom - 1) + 0.5
            self.items_on_ground.append((kx, ky, Item(ItemType.KEY, "Dungeon Key", "Opens locked doors", count=1)))

        if self._is_boss_floor() and self.dungeon.rooms:
            reward_room = self.dungeon.rooms[-1]
            rx = reward_room.centerx + 0.5
            ry = reward_room.centery - 1.5
            reward_item = random.choice([ItemType.IRON_COLLAR, ItemType.SWIFT_HARNESS, ItemType.SPIKED_VEST, ItemType.POWER_KIBBLE])
            self.items_on_ground.append((rx, ry, self._create_item(reward_item)))

        self.play_sound('stairs')

    def _create_enemy(self, x: float, y: float) -> Enemy:
        floor_scale = 1 + (self.floor_num - 1) * 0.3
        roll = random.random()
        if self.floor_num >= 8 and roll < 0.12:
            enemy = Enemy(EnemyType.FIRE_IMP, x, y, int(7 * floor_scale), int(7 * floor_scale),
                        int(3 * floor_scale), 2.4, (210, 90, 40), 10, spawn_x=x, spawn_y=y,
                        drops=[ItemType.POWER_KIBBLE])
        elif self.floor_num >= 7 and roll < 0.22:
            enemy = Enemy(EnemyType.MUSHROOM_BRUTE, x, y, int(12 * floor_scale), int(12 * floor_scale),
                        int(3 * floor_scale), 1.0, (120, 60, 40), 15, spawn_x=x, spawn_y=y,
                        drops=[ItemType.FISH_FEAST])
        elif self.floor_num >= 6 and roll < 0.32:
            enemy = Enemy(EnemyType.SCORPION, x, y, int(9 * floor_scale), int(9 * floor_scale),
                        int(3 * floor_scale), 1.9, (130, 90, 40), 12, spawn_x=x, spawn_y=y,
                        drops=[ItemType.JERKY])
        elif self.floor_num >= 4 and roll < 0.42:
            enemy = Enemy(EnemyType.SHADOW_HOUND, x, y, int(8 * floor_scale), int(8 * floor_scale),
                        int(3 * floor_scale), 1.8, (60, 20, 80), 14, spawn_x=x, spawn_y=y,
                        drops=[ItemType.JERKY])
        elif self.floor_num >= 3 and roll < 0.53:
            enemy = Enemy(EnemyType.GHOST_CAT, x, y, int(6 * floor_scale), int(6 * floor_scale),
                        int(2 * floor_scale), 2.2, (150, 200, 180), 10, spawn_x=x, spawn_y=y,
                        drops=[ItemType.CATNIP])
        elif roll < 0.65:
            enemy = Enemy(EnemyType.SPIDER, x, y, int(5 * floor_scale), int(5 * floor_scale),
                        int(2 * floor_scale), 1.5, (80, 60, 40), 10, spawn_x=x, spawn_y=y,
                        drops=[ItemType.BANDAGE])
        elif roll < 0.75:
            enemy = Enemy(EnemyType.BAT, x, y, int(3 * floor_scale), int(3 * floor_scale),
                        int(1 * floor_scale), 2.5, (100, 80, 120), 8, spawn_x=x, spawn_y=y)
        elif roll < 0.83:
            enemy = Enemy(EnemyType.SNAKE, x, y, int(6 * floor_scale), int(6 * floor_scale),
                        int(2 * floor_scale), 1.2, (60, 120, 50), 11, spawn_x=x, spawn_y=y,
                        drops=[ItemType.SEED])
        elif roll < 0.91:
            enemy = Enemy(EnemyType.SLIME, x, y, int(8 * floor_scale), int(8 * floor_scale),
                        int(2 * floor_scale), 1.3, (70, 180, 90), 13, spawn_x=x, spawn_y=y,
                        drops=[ItemType.TREAT])
        else:
            enemy = Enemy(EnemyType.RAT, x, y, int(4 * floor_scale), int(4 * floor_scale),
                        int(1 * floor_scale), 1.0, (130, 110, 90), 9, spawn_x=x, spawn_y=y)
        return self._apply_enemy_scaling(enemy)

    def _create_miniboss(self, x: float, y: float) -> Enemy:
        floor_scale = 1 + (self.floor_num - 1) * 0.35
        mini = Enemy(
            EnemyType.MINI_WARDEN,
            x,
            y,
            int(20 * floor_scale),
            int(20 * floor_scale),
            int(4 * floor_scale),
            1.5,
            (170, 60, 120),
            18,
            is_boss=True,
            spawn_x=x,
            spawn_y=y,
            drops=[random.choice([ItemType.JERKY, ItemType.FISH_FEAST, ItemType.POWER_KIBBLE])],
        )
        return self._apply_enemy_scaling(mini)

    def _create_boss(self, x: float, y: float) -> Enemy:
        if self.is_infinite_mode and self.floor_num % 10 == 0:
            boss_type = EnemyType.BOSS_ABYSS_WARDEN
            base_hp = 120 + self.floor_num * 14
            base_damage = 8 + self.floor_num // 4
            color = (120, 20, 20)
            size = 28
            speed = 1.25
        else:
            boss_type = EnemyType.BOSS_CAGE_KEEPER
            base_hp = 90 + self.floor_num * 12
            base_damage = 6 + self.floor_num // 5
            color = (180, 40, 40)
            size = 24
            speed = 1.1

        boss = Enemy(boss_type, x, y, base_hp, base_hp,
                    base_damage, speed, color, size,
                    is_boss=True, spawn_x=x, spawn_y=y,
                    drops=[
                        random.choice([ItemType.IRON_COLLAR, ItemType.SWIFT_HARNESS, ItemType.SPIKED_VEST]),
                        random.choice([ItemType.POWER_KIBBLE, ItemType.JERKY, ItemType.FISH_FEAST]),
                    ])
        return self._apply_enemy_scaling(boss)

    def _apply_enemy_scaling(self, enemy: Enemy) -> Enemy:
        enemy.max_hp = max(1, int(enemy.max_hp * self.enemy_hp_mult))
        enemy.hp = min(enemy.hp, enemy.max_hp)
        enemy.damage = max(1, int(enemy.damage * self.enemy_dmg_mult))
        enemy.speed = enemy.speed * self.enemy_speed_mult
        return enemy

    def _create_item(self, item_type: ItemType) -> Item:
        items = {
            ItemType.TREAT: Item(ItemType.TREAT, "Treat", "Heals 4 HP", heal=4),
            ItemType.BANDAGE: Item(ItemType.BANDAGE, "Bandage", "Heals 6 HP", heal=6),
            ItemType.BONE: Item(ItemType.BONE, "Bone", "+2 ATK permanently", damage_boost=2),
            ItemType.CATNIP: Item(ItemType.CATNIP, "Catnip", "Heals 3 and +0.10 speed permanently", heal=3, speed_boost=0.10),
            ItemType.SEED: Item(ItemType.SEED, "Seed", "Heals 2 HP", heal=2),
            ItemType.COLLAR: Item(ItemType.COLLAR, "Power Collar", "+3 Attack permanently", damage_boost=3),
            ItemType.TOY: Item(ItemType.TOY, "Squeaky Toy", "Distracts enemies", heal=0),
            ItemType.JERKY: Item(ItemType.JERKY, "Protein Jerky", "+2 ATK permanently", damage_boost=2),
            ItemType.FISH_FEAST: Item(ItemType.FISH_FEAST, "Fish Feast", "Heals 4 and +4 max HP permanently", heal=4, max_hp_boost=4),
            ItemType.POWER_KIBBLE: Item(ItemType.POWER_KIBBLE, "Power Kibble", "+1 ATK and +0.10 speed permanently", damage_boost=1, speed_boost=0.10),
            ItemType.IRON_COLLAR: Item(ItemType.IRON_COLLAR, "Iron Collar", "+4 ATK permanently", damage_boost=4),
            ItemType.SWIFT_HARNESS: Item(ItemType.SWIFT_HARNESS, "Swift Harness", "+0.35 speed and faster spit permanently", speed_boost=0.35, spit_cd_boost=-0.08),
            ItemType.SPIKED_VEST: Item(ItemType.SPIKED_VEST, "Spiked Vest", "+8 max HP permanently", max_hp_boost=8),
            ItemType.KEY: Item(ItemType.KEY, "Dungeon Key", "Opens locked doors"),
        }
        return items.get(item_type, items[ItemType.TREAT])

    # === GAME LOGIC ===

    def update(self, dt: float):
        if self.state == "playing":
            self._update_playing(dt)
        self.time += dt

        # Transition
        if self.transitioning:
            self.transition_alpha = min(255, self.transition_alpha + int(600 * dt))
            if self.transition_alpha >= 255:
                self.transitioning = False
                if self.transition_target == "next_floor":
                    self.floor_num += 1
                    if (not self.is_infinite_mode) and self.floor_num > self.max_floors:
                        self.state = "victory"
                    else:
                        self.generate_floor()
                        if self.is_infinite_mode:
                            self._save_infinite_progress()
                self.transition_alpha = 255
        elif self.transition_alpha > 0:
            self.transition_alpha = max(0, self.transition_alpha - int(400 * dt))

    def _update_playing(self, dt: float):
        keys = pygame.key.get_pressed()

        if self.invulnerable > 0:
            self.invulnerable -= dt
        if self.attack_timer > 0:
            self.attack_timer -= dt
        if self.spit_cooldown > 0:
            self.spit_cooldown -= dt
        if self.special_cooldown > 0:
            self.special_cooldown -= dt
        if self.screen_shake > 0:
            self.screen_shake -= dt

        # Movement
        dx, dy = 0.0, 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1

        if dx != 0 or dy != 0:
            length = math.sqrt(dx * dx + dy * dy)
            dx /= length
            dy /= length
            self.facing = math.atan2(dy, dx)
            self.walk_anim += dt * 8

            new_x = self.px + dx * self.speed * dt
            new_y = self.py + dy * self.speed * dt

            # Collision
            if not self._is_solid(new_x, self.py):
                self.px = new_x
            if not self._is_solid(self.px, new_y):
                self.py = new_y

        # Explore minimap
        tx, ty = int(self.px), int(self.py)
        for oy in range(-3, 4):
            for ox in range(-3, 4):
                self.explored.add((tx + ox, ty + oy))

        # Pick up items
        items_to_remove = []
        for i, (ix, iy, item) in enumerate(self.items_on_ground):
            dist = math.sqrt((self.px - ix) ** 2 + (self.py - iy) ** 2)
            if dist < 0.7:
                if item.item_type == ItemType.KEY:
                    self.keys_held += 1
                    self.add_floating_text(ix, iy, "+1 Key!", C_YELLOW)
                elif len(self.inventory) < 6:
                    self.inventory.append(item)
                    self.add_floating_text(ix, iy, f"+{item.name}", C_GREEN)
                else:
                    continue  # Inventory full
                items_to_remove.append(i)
                self.play_sound('pickup')
        for i in reversed(items_to_remove):
            self.items_on_ground.pop(i)

        # Check clue tile
        if self.dungeon:
            tile = self.dungeon.tiles[int(self.py)][int(self.px)]
            if tile == TileType.CLUE:
                self.dungeon.tiles[int(self.py)][int(self.px)] = TileType.FLOOR
                clue_idx = len(self.clues_found) % len(CLUE_TEXTS)
                clue = Clue(CLUE_TEXTS[clue_idx])
                self.clues_found.append(clue)
                self.current_clue_text = clue.text
                self.state = "clue"
                self.play_sound('pickup')

            # Check stairs
            if tile == TileType.STAIRS_DOWN:
                stair_dist = math.sqrt(
                    (self.px - self.dungeon.stairs_down[0] - 0.5) ** 2 +
                    (self.py - self.dungeon.stairs_down[1] - 0.5) ** 2
                ) if self.dungeon.stairs_down else 999
                if stair_dist < 0.5 and not self.transitioning:
                    # Check if enemies dead on boss floor
                    bosses = [e for e in self.enemies if e.is_boss]
                    if bosses:
                        self.add_floating_text(self.px, self.py - 0.5, "Defeat the boss first!", C_RED)
                    else:
                        self._open_floor_reward()

            # Check trap
            if tile == TileType.TRAP and self.invulnerable <= 0:
                self.hp -= 2
                self.invulnerable = 0.5
                self.screen_shake = 0.15
                self.add_floating_text(self.px, self.py - 0.5, "-2 TRAP!", C_RED)
                self.dungeon.tiles[int(self.py)][int(self.px)] = TileType.FLOOR  # One-time trap
                self.spawn_particles(self.px, self.py, C_ORANGE, 6)
                if self.hp <= 0:
                    self._on_player_death()

        # Update enemies
        for enemy in self.enemies:
            self._update_enemy(enemy, dt)

        # Remove dead enemies
        dead_enemies = [e for e in self.enemies if e.hp <= 0]
        for e in dead_enemies:
            self.xp += 5 + (3 if e.is_boss else 0)
            if self.xp >= self.xp_to_next:
                self._level_up()
            self.spawn_particles(e.x, e.y, e.color, 12)
            # Drop items
            for drop in e.drops:
                item = self._create_item(drop)
                self.items_on_ground.append((e.x, e.y, item))
        self.enemies = [e for e in self.enemies if e.hp > 0]

        # Update projectiles
        projs_to_remove = []
        for i, proj in enumerate(self.projectiles):
            proj.x += proj.vx * dt
            proj.y += proj.vy * dt
            proj.life -= dt
            proj.trail_timer += dt
            # Spawn trail particles
            if proj.trail_timer > 0.03:
                proj.trail_timer = 0
                self.particles.append(Particle(
                    proj.x, proj.y, random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5),
                    proj.color, 0.3, 0.3, 3))
            # Hit wall
            if self._is_solid(proj.x, proj.y, 0.1):
                projs_to_remove.append(i)
                self.spawn_particles(proj.x, proj.y, proj.color, 5)
                continue
            # Hit enemies
            for enemy in self.enemies:
                dist = math.sqrt((proj.x - enemy.x) ** 2 + (proj.y - enemy.y) ** 2)
                if dist < 0.6:
                    enemy.hp -= proj.damage
                    enemy.stun_timer = 0.1
                    angle = math.atan2(enemy.y - proj.y, enemy.x - proj.x)
                    enemy.x += math.cos(angle) * 0.2
                    enemy.y += math.sin(angle) * 0.2
                    self.add_floating_text(enemy.x, enemy.y - 0.5, f"-{proj.damage}", C_GREEN)
                    self.spawn_particles(proj.x, proj.y, proj.color, 6)
                    self.play_sound('hit')
                    projs_to_remove.append(i)
                    break
        for i in reversed(projs_to_remove):
            if i < len(self.projectiles):
                self.projectiles.pop(i)
        self.projectiles = [p for p in self.projectiles if p.life > 0]

        # Update particles
        for p in self.particles:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.life -= dt
            p.size = max(0, p.size * (p.life / p.max_life))
        self.particles = [p for p in self.particles if p.life > 0]

        # Update floating texts
        for ft in self.floating_texts:
            ft.y -= dt * 1.5
            ft.life -= dt
        self.floating_texts = [ft for ft in self.floating_texts if ft.life > 0]

        # Camera
        self.cam_x += (self.px - self.cam_x) * 6 * dt
        self.cam_y += (self.py - self.cam_y) * 6 * dt

    def _update_enemy(self, e: Enemy, dt: float):
        if e.stun_timer > 0:
            e.stun_timer -= dt
            return

        e.anim_timer += dt
        e.attack_cooldown = max(0, e.attack_cooldown - dt)

        dist = math.sqrt((self.px - e.x) ** 2 + (self.py - e.y) ** 2)
        alert_range = 5 if not e.is_boss else 8

        if dist < alert_range:
            e.alert = True
        elif dist > alert_range + 3:
            e.alert = False

        if e.alert:
            # Move toward player
            angle = math.atan2(self.py - e.y, self.px - e.x)
            move_x = math.cos(angle) * e.speed * dt
            move_y = math.sin(angle) * e.speed * dt

            new_x = e.x + move_x
            new_y = e.y + move_y
            if not self._is_solid(new_x, e.y):
                e.x = new_x
            if not self._is_solid(e.x, new_y):
                e.y = new_y

            # Attack player
            if dist < 0.8 and e.attack_cooldown <= 0 and self.invulnerable <= 0:
                self.hp -= e.damage
                self.invulnerable = 0.4
                self.screen_shake = 0.1
                e.attack_cooldown = 1.0
                self.add_floating_text(self.px, self.py - 0.5, f"-{e.damage}", C_RED)
                self.spawn_particles(self.px, self.py, C_RED, 5)
                self.play_sound('hit')
                if self.hp <= 0:
                    self._on_player_death()

        if self.is_infinite_mode and self.state == "playing":
            self.infinite_save_timer += dt
            if self.infinite_save_timer >= 1.0:
                self.infinite_save_timer = 0.0
                self._save_infinite_progress()

    def _on_player_death(self):
        self.state = "dead"
        if self.is_infinite_mode:
            self._clear_infinite_save()
        else:
            # Patrol
            e.patrol_angle += dt * 0.5
            patrol_x = e.spawn_x + math.cos(e.patrol_angle) * 1.5
            patrol_y = e.spawn_y + math.sin(e.patrol_angle) * 1.5
            angle = math.atan2(patrol_y - e.y, patrol_x - e.x)
            move_x = math.cos(angle) * e.speed * 0.3 * dt
            move_y = math.sin(angle) * e.speed * 0.3 * dt
            new_x = e.x + move_x
            new_y = e.y + move_y
            if not self._is_solid(new_x, e.y):
                e.x = new_x
            if not self._is_solid(e.x, new_y):
                e.y = new_y

    def _is_solid(self, x: float, y: float, radius: float = 0.3) -> bool:
        if not self.dungeon:
            return True
        for ox in [-radius, radius]:
            for oy in [-radius, radius]:
                tx = int(x + ox)
                ty = int(y + oy)
                if tx < 0 or tx >= self.dungeon.w or ty < 0 or ty >= self.dungeon.h:
                    return True
                if self.dungeon.tiles[ty][tx] in (TileType.WALL, TileType.VOID):
                    return True
        return False

    def do_attack(self):
        if self.attack_timer > 0:
            return
        self.attack_timer = self.attack_cooldown
        self.play_sound('attack')

        # Attack in facing direction
        atk_x = self.px + math.cos(self.facing) * 0.8
        atk_y = self.py + math.sin(self.facing) * 0.8
        self.spawn_particles(atk_x, atk_y, C_WHITE, 4)

        for enemy in self.enemies:
            dist = math.sqrt((atk_x - enemy.x) ** 2 + (atk_y - enemy.y) ** 2)
            if dist < 1.0:
                dmg = self.attack_power + random.randint(0, 1)
                enemy.hp -= dmg
                enemy.stun_timer = 0.15
                # Knockback
                angle = math.atan2(enemy.y - self.py, enemy.x - self.px)
                enemy.x += math.cos(angle) * 0.3
                enemy.y += math.sin(angle) * 0.3
                self.add_floating_text(enemy.x, enemy.y - 0.5, f"-{dmg}", C_YELLOW)
                self.play_sound('hit')
                self.screen_shake = 0.05

    def do_spit(self, mouse_x: int, mouse_y: int):
        if self.spit_cooldown > 0:
            return
        self.spit_cooldown = self.spit_max_cd
        self.play_sound('spit')

        # Calculate direction toward mouse in world coords
        world_mx = (mouse_x - SCREEN_W // 2) / TILE_SIZE + self.cam_x
        world_my = (mouse_y - SCREEN_H // 2) / TILE_SIZE + self.cam_y
        angle = math.atan2(world_my - self.py, world_mx - self.px)
        self.facing = angle

        speed = 8.0
        spit_color = {
            PetType.DOG: (140, 200, 100),   # green slobber
            PetType.CAT: (180, 100, 200),   # purple hairball
            PetType.HAMSTER: (200, 180, 80), # seed spit
        }.get(self.pet_type, (140, 200, 100))

        dmg = max(1, self.attack_power - 1)
        proj = Projectile(
            self.px + math.cos(angle) * 0.4,
            self.py + math.sin(angle) * 0.4,
            math.cos(angle) * speed,
            math.sin(angle) * speed,
            dmg, spit_color
        )
        self.projectiles.append(proj)
        self.spawn_particles(self.px + math.cos(angle) * 0.4,
                            self.py + math.sin(angle) * 0.4,
                            spit_color, 3)

    def do_special(self):
        if self.special_cooldown > 0 or not self.pet_type:
            return
        self.special_cooldown = self.special_max_cd

        if self.pet_type == PetType.DOG:
            # Bark - stun all nearby enemies
            for enemy in self.enemies:
                dist = math.sqrt((self.px - enemy.x) ** 2 + (self.py - enemy.y) ** 2)
                if dist < 4:
                    enemy.stun_timer = 2.0
                    self.add_floating_text(enemy.x, enemy.y - 0.3, "STUNNED!", C_CYAN)
            self.spawn_particles(self.px, self.py, C_CYAN, 15)
            self.add_floating_text(self.px, self.py - 0.7, "WOOF!", C_CYAN)

        elif self.pet_type == PetType.CAT:
            # Pounce - dash forward and deal damage
            dash_x = self.px + math.cos(self.facing) * 3
            dash_y = self.py + math.sin(self.facing) * 3
            if not self._is_solid(dash_x, dash_y):
                self.px = dash_x
                self.py = dash_y
            for enemy in self.enemies:
                dist = math.sqrt((self.px - enemy.x) ** 2 + (self.py - enemy.y) ** 2)
                if dist < 1.5:
                    dmg = self.attack_power * 2
                    enemy.hp -= dmg
                    self.add_floating_text(enemy.x, enemy.y - 0.3, f"-{dmg} POUNCE!", C_ORANGE)
            self.spawn_particles(self.px, self.py, C_ORANGE, 10)

        elif self.pet_type == PetType.HAMSTER:
            # Burrow - become invulnerable briefly + heal
            self.invulnerable = 2.0
            heal = 3
            self.hp = min(self.max_hp, self.hp + heal)
            self.add_floating_text(self.px, self.py - 0.5, f"+{heal} BURROW!", C_GREEN)
            self.spawn_particles(self.px, self.py, C_BROWN, 10)

    def use_item(self):
        if self.selected_item < len(self.inventory):
            item = self.inventory[self.selected_item]
            if item.heal > 0:
                old_hp = self.hp
                self.hp = min(self.max_hp, self.hp + item.heal)
                healed = self.hp - old_hp
                self.add_floating_text(self.px, self.py - 0.5, f"+{healed} HP", C_GREEN)
                self.spawn_particles(self.px, self.py, C_GREEN, 6)
            if item.damage_boost > 0:
                self.attack_power += item.damage_boost
                self.add_floating_text(self.px, self.py - 0.5, f"+{item.damage_boost} ATK!", C_YELLOW)
            if item.max_hp_boost > 0:
                self.max_hp += item.max_hp_boost
                self.hp = min(self.max_hp, self.hp + item.max_hp_boost)
                self.add_floating_text(self.px, self.py - 0.8, f"+{item.max_hp_boost} MAX HP!", C_CYAN)
            if item.speed_boost != 0:
                self.speed = max(1.0, self.speed + item.speed_boost)
                self.add_floating_text(self.px, self.py - 0.9, f"{item.speed_boost:+.2f} SPD", C_CYAN)
            if item.spit_cd_boost != 0:
                self.spit_max_cd = max(0.2, self.spit_max_cd + item.spit_cd_boost)
                self.add_floating_text(self.px, self.py - 1.0, "Spit Faster!", C_CYAN)
            if item.special_cd_boost != 0:
                self.special_max_cd = max(1.0, self.special_max_cd + item.special_cd_boost)
                self.add_floating_text(self.px, self.py - 1.1, "Special Faster!", C_PURPLE)
            if item.item_type == ItemType.TOY:
                # Distract enemies
                for enemy in self.enemies:
                    dist = math.sqrt((self.px - enemy.x) ** 2 + (self.py - enemy.y) ** 2)
                    if dist < 5:
                        enemy.alert = False
                        enemy.stun_timer = 3.0
                self.add_floating_text(self.px, self.py - 0.5, "SQUEAK!", C_PINK)
            self.play_sound('pickup')
            item.count -= 1
            if item.count <= 0:
                self.inventory.pop(self.selected_item)
                if self.selected_item >= len(self.inventory):
                    self.selected_item = max(0, len(self.inventory) - 1)
            if self.is_infinite_mode:
                self._save_infinite_progress()

    def _level_up(self):
        self.level += 1
        self.xp -= self.xp_to_next
        self.xp_to_next = int(self.xp_to_next * 1.5)
        self.max_hp += 2
        self.hp = self.max_hp
        self.attack_power += 1
        self.add_floating_text(self.px, self.py - 1, f"LEVEL {self.level}!", C_YELLOW)
        self.spawn_particles(self.px, self.py, C_YELLOW, 20)

    def add_floating_text(self, x: float, y: float, text: str, color):
        self.floating_texts.append(FloatingText(x, y, text, color))

    def spawn_particles(self, x: float, y: float, color, count: int):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 4)
            self.particles.append(Particle(
                x, y,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                color, random.uniform(0.3, 0.8), 0.8,
                random.uniform(2, 5)
            ))

    # === RENDERING ===
    def world_to_screen(self, wx: float, wy: float) -> Tuple[int, int]:
        shake_x = random.uniform(-2, 2) * self.screen_shake * 10 if self.screen_shake > 0 else 0
        shake_y = random.uniform(-2, 2) * self.screen_shake * 10 if self.screen_shake > 0 else 0
        sx = int((wx - self.cam_x) * TILE_SIZE + SCREEN_W // 2 + shake_x)
        sy = int((wy - self.cam_y) * TILE_SIZE + SCREEN_H // 2 + shake_y)
        return sx, sy

    def _item_color(self, item_type: ItemType):
        return {
            ItemType.TREAT: C_PINK,
            ItemType.BANDAGE: C_WHITE,
            ItemType.BONE: (230, 220, 200),
            ItemType.CATNIP: C_GREEN,
            ItemType.SEED: C_YELLOW,
            ItemType.COLLAR: C_PURPLE,
            ItemType.TOY: C_ORANGE,
            ItemType.JERKY: (190, 80, 60),
            ItemType.FISH_FEAST: (100, 170, 230),
            ItemType.POWER_KIBBLE: (255, 180, 70),
            ItemType.IRON_COLLAR: (150, 160, 180),
            ItemType.SWIFT_HARNESS: (90, 220, 220),
            ItemType.SPIKED_VEST: (170, 120, 210),
            ItemType.KEY: C_YELLOW,
        }.get(item_type, C_WHITE)

    def draw(self):
        if self.state == "title":
            self._draw_title()
        elif self.state == "select":
            self._draw_select()
        elif self.state == "difficulty":
            self._draw_difficulty_select()
        elif self.state == "infinite_prompt":
            self._draw_infinite_prompt()
        elif self.state == "prep":
            self._draw_prep_loadout()
        elif self.state == "floor_reward":
            self._draw_floor_reward()
        elif self.state in ("playing", "inventory", "paused", "clue"):
            self._draw_game()
            if self.state == "inventory":
                self._draw_inventory_overlay()
            elif self.state == "paused":
                self._draw_pause()
            elif self.state == "clue":
                self._draw_clue()
        elif self.state == "dead":
            self._draw_game()
            self._draw_death()
        elif self.state == "victory":
            self._draw_victory()

        # Transition overlay
        if self.transition_alpha > 0:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H))
            overlay.set_alpha(self.transition_alpha)
            overlay.fill(C_BLACK)
            self.screen.blit(overlay, (0, 0))
            if self.transition_alpha > 200:
                txt = self.font_med.render(f"Floor {self.floor_num}...", True, C_WHITE)
                self.screen.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, SCREEN_H // 2))

        pygame.display.flip()

    def _draw_title(self):
        self.screen.fill((15, 10, 20))

        # Animated background
        for i in range(30):
            x = (self.time * 20 + i * 80) % SCREEN_W
            y = (math.sin(self.time + i) * 50 + i * 25) % SCREEN_H
            alpha = int(100 + math.sin(self.time * 2 + i) * 50)
            s = pygame.Surface((4, 4))
            s.set_alpha(alpha)
            s.fill(C_PURPLE)
            self.screen.blit(s, (x, y))

        # Title
        title = self.font_big.render("PET QUEST", True, C_YELLOW)
        subtitle = self.font_med.render("Find Your Owner", True, C_ORANGE)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 180))
        self.screen.blit(subtitle, (SCREEN_W // 2 - subtitle.get_width() // 2, 230))

        # Pet silhouettes
        pets = [("Dog", C_BROWN, 280), ("Cat", C_ORANGE, 400), ("Hamster", C_YELLOW, 520)]
        for name, color, cx in pets:
            bob = math.sin(self.time * 2 + cx) * 5
            pygame.draw.circle(self.screen, color, (cx, int(350 + bob)), 25)
            pygame.draw.circle(self.screen, tuple(max(0, c - 40) for c in color), (cx, int(350 + bob)), 25, 2)
            txt = self.font_sm.render(name, True, color)
            self.screen.blit(txt, (cx - txt.get_width() // 2, 385))

        # Prompt
        blink = math.sin(self.time * 3) > 0
        if blink:
            prompt = self.font_med.render("Press ENTER to start", True, C_WHITE)
            self.screen.blit(prompt, (SCREEN_W // 2 - prompt.get_width() // 2, 500))

        # Credits
        cred = self.font_tiny.render("WASD to move | SPACE melee | CLICK to spit | Q for special | E to use item", True, C_GRAY)
        self.screen.blit(cred, (SCREEN_W // 2 - cred.get_width() // 2, SCREEN_H - 40))

    def _draw_select(self):
        self.screen.fill((15, 10, 20))
        title = self.font_big.render("Choose Your Pet", True, C_WHITE)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 60))

        pets = list(PetType)
        for i, pet in enumerate(pets):
            stats = PET_STATS[pet]
            x = 130 + i * 260
            y = 180
            w, h = 220, 380

            # Card
            selected = i == self.selection_index
            border_color = C_YELLOW if selected else C_GRAY
            pygame.draw.rect(self.screen, (30, 25, 35), (x, y, w, h), border_radius=10)
            pygame.draw.rect(self.screen, border_color, (x, y, w, h), 3, border_radius=10)

            if selected:
                glow = pygame.Surface((w + 10, h + 10), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*C_YELLOW, 30), (0, 0, w + 10, h + 10), border_radius=12)
                self.screen.blit(glow, (x - 5, y - 5))

            # Pet sprite
            color = stats["color"]
            cx = x + w // 2
            cy = y + 80
            bob = math.sin(self.time * 3 + i) * 4 if selected else 0
            # Body
            pygame.draw.ellipse(self.screen, color, (cx - 20, int(cy - 15 + bob), 40, 30))
            # Head
            pygame.draw.circle(self.screen, color, (cx, int(cy - 22 + bob)), 16)
            # Eyes
            pygame.draw.circle(self.screen, C_BLACK, (cx - 5, int(cy - 24 + bob)), 3)
            pygame.draw.circle(self.screen, C_BLACK, (cx + 5, int(cy - 24 + bob)), 3)
            pygame.draw.circle(self.screen, C_WHITE, (cx - 4, int(cy - 25 + bob)), 1)
            pygame.draw.circle(self.screen, C_WHITE, (cx + 6, int(cy - 25 + bob)), 1)

            if pet == PetType.DOG:
                # Ears
                pygame.draw.ellipse(self.screen, tuple(max(0, c - 30) for c in color),
                                   (cx - 18, int(cy - 38 + bob), 12, 16))
                pygame.draw.ellipse(self.screen, tuple(max(0, c - 30) for c in color),
                                   (cx + 6, int(cy - 38 + bob), 12, 16))
                # Tail
                pygame.draw.arc(self.screen, color, (cx + 15, int(cy - 5 + bob), 15, 20),
                              0, math.pi, 3)
            elif pet == PetType.CAT:
                # Pointy ears
                pygame.draw.polygon(self.screen, color, [
                    (cx - 14, int(cy - 34 + bob)), (cx - 8, int(cy - 22 + bob)), (cx - 20, int(cy - 22 + bob))])
                pygame.draw.polygon(self.screen, color, [
                    (cx + 14, int(cy - 34 + bob)), (cx + 8, int(cy - 22 + bob)), (cx + 20, int(cy - 22 + bob))])
                # Whiskers
                pygame.draw.line(self.screen, C_WHITE, (cx - 8, int(cy - 20 + bob)), (cx - 25, int(cy - 22 + bob)))
                pygame.draw.line(self.screen, C_WHITE, (cx + 8, int(cy - 20 + bob)), (cx + 25, int(cy - 22 + bob)))
            elif pet == PetType.HAMSTER:
                # Chubby cheeks
                pygame.draw.circle(self.screen, tuple(min(255, c + 30) for c in color),
                                  (cx - 12, int(cy - 18 + bob)), 8)
                pygame.draw.circle(self.screen, tuple(min(255, c + 30) for c in color),
                                  (cx + 12, int(cy - 18 + bob)), 8)
                # Small ears
                pygame.draw.circle(self.screen, tuple(max(0, c - 20) for c in color),
                                  (cx - 12, int(cy - 34 + bob)), 6)
                pygame.draw.circle(self.screen, tuple(max(0, c - 20) for c in color),
                                  (cx + 12, int(cy - 34 + bob)), 6)

            # Name
            name_txt = self.font_med.render(pet.value, True, C_WHITE)
            self.screen.blit(name_txt, (cx - name_txt.get_width() // 2, y + 120))

            # Stats
            stat_y = y + 160
            for label, val, max_val, col in [
                ("HP", stats["hp"], 15, C_RED),
                ("ATK", stats["attack"], 6, C_ORANGE),
                ("SPD", stats["speed"], 4, C_CYAN),
            ]:
                txt = self.font_sm.render(f"{label}:", True, C_WHITE)
                self.screen.blit(txt, (x + 15, stat_y))
                bar_x = x + 60
                bar_w = w - 80
                pygame.draw.rect(self.screen, C_DARK_GRAY, (bar_x, stat_y + 3, bar_w, 12))
                fill_w = int(bar_w * (val if isinstance(val, int) else val) / max_val)
                pygame.draw.rect(self.screen, col, (bar_x, stat_y + 3, fill_w, 12))
                stat_y += 28

            # Special
            spec_txt = self.font_tiny.render(f"Special: {stats['special']}", True, C_PURPLE)
            self.screen.blit(spec_txt, (x + 10, y + 280))

            # Flavor text
            flavors = {
                PetType.DOG: "Loyal and brave. Will\nnever stop searching.",
                PetType.CAT: "Quick and fierce. No\ndungeon can hold them.",
                PetType.HAMSTER: "Small but determined.\nSurvives against all odds.",
            }
            for j, line in enumerate(flavors[pet].split('\n')):
                ft = self.font_tiny.render(line, True, (160, 160, 160))
                self.screen.blit(ft, (x + 10, y + 310 + j * 18))

        # Controls
        ctrl = self.font_sm.render("← → to select, ENTER to confirm", True, C_GRAY)
        self.screen.blit(ctrl, (SCREEN_W // 2 - ctrl.get_width() // 2, SCREEN_H - 50))

    def _draw_difficulty_select(self):
        self.screen.fill((12, 9, 18))
        title = self.font_big.render("Choose Difficulty", True, C_WHITE)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 90))

        hint_pet = self.pending_pet.value if self.pending_pet else "Pet"
        pet_txt = self.font_sm.render(f"Selected pet: {hint_pet}", True, C_CYAN)
        self.screen.blit(pet_txt, (SCREEN_W // 2 - pet_txt.get_width() // 2, 140))

        for i, diff in enumerate(self.difficulty_options):
            y = 210 + i * 85
            selected = i == self.difficulty_index
            box_color = (45, 38, 55) if selected else (28, 22, 35)
            border = C_YELLOW if selected else C_GRAY
            pygame.draw.rect(self.screen, box_color, (210, y, 540, 64), border_radius=10)
            pygame.draw.rect(self.screen, border, (210, y, 540, 64), 2, border_radius=10)

            label = diff
            if diff == "Infinite" and self._infinite_save_exists():
                label = "Infinite (save found)"
            txt = self.font_med.render(label, True, C_WHITE)
            self.screen.blit(txt, (240, y + 10))

            desc_map = {
                "Easy": "Softer enemies, extra starter item, 4 floors.",
                "Normal": "Default adventure balance, 5 floors.",
                "Hard": "Stronger enemies and longer dungeon, 8 floors.",
                "Infinite": "Endless floors. Progress is saved until you die.",
            }
            desc = self.font_tiny.render(desc_map[diff], True, C_GRAY)
            self.screen.blit(desc, (242, y + 38))

        ctrl = self.font_sm.render("↑ ↓ to choose, ENTER confirm, ESC back", True, C_GRAY)
        self.screen.blit(ctrl, (SCREEN_W // 2 - ctrl.get_width() // 2, SCREEN_H - 40))

    def _draw_infinite_prompt(self):
        self.screen.fill((10, 8, 16))
        title = self.font_big.render("Infinite Run Save Found", True, C_YELLOW)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 180))
        sub = self.font_med.render("Continue saved run or start a new one?", True, C_WHITE)
        self.screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, 250))
        c_txt = self.font_sm.render("Press C to continue saved run", True, C_GREEN)
        n_txt = self.font_sm.render("Press N for a new run", True, C_ORANGE)
        b_txt = self.font_tiny.render("Press ESC to go back", True, C_GRAY)
        self.screen.blit(c_txt, (SCREEN_W // 2 - c_txt.get_width() // 2, 330))
        self.screen.blit(n_txt, (SCREEN_W // 2 - n_txt.get_width() // 2, 365))
        self.screen.blit(b_txt, (SCREEN_W // 2 - b_txt.get_width() // 2, 405))

    def _draw_prep_loadout(self):
        self.screen.fill((14, 10, 20))
        title = self.font_big.render("Pack Inventory & Equip Gear", True, C_WHITE)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 40))

        mode_txt = self.font_sm.render(f"Mode: {self.difficulty}", True, C_CYAN)
        self.screen.blit(mode_txt, (SCREEN_W // 2 - mode_txt.get_width() // 2, 86))

        # Starter item section
        pygame.draw.rect(self.screen, (28, 24, 35), (100, 140, 760, 180), border_radius=10)
        pygame.draw.rect(self.screen, C_GRAY, (100, 140, 760, 180), 2, border_radius=10)
        item_title = self.font_med.render("Starter Inventory Item", True, C_WHITE)
        self.screen.blit(item_title, (130, 160))

        item = self._create_item(self.prep_item_options[self.prep_item_index])
        item.count = self.start_item_count
        item_name = self.font_med.render(f"{item.name} x{item.count}", True, C_YELLOW)
        item_desc = self.font_sm.render(item.description, True, C_GRAY)
        self.screen.blit(item_name, (130, 205))
        self.screen.blit(item_desc, (130, 238))
        item_ctrl = self.font_tiny.render("Use UP/DOWN to change starter item", True, C_GRAY)
        self.screen.blit(item_ctrl, (130, 282))

        # Gear section
        pygame.draw.rect(self.screen, (28, 24, 35), (100, 350, 760, 230), border_radius=10)
        pygame.draw.rect(self.screen, C_GRAY, (100, 350, 760, 230), 2, border_radius=10)
        gear_title = self.font_med.render("Equip Slot", True, C_WHITE)
        self.screen.blit(gear_title, (130, 370))

        gear = self.prep_gear_options[self.prep_gear_index]
        gear_name = self.font_med.render(gear["name"], True, C_GREEN)
        gear_desc = self.font_sm.render(gear["description"], True, C_GRAY)
        self.screen.blit(gear_name, (130, 415))
        self.screen.blit(gear_desc, (130, 447))

        stats_line = (
            f"HP {gear['hp_bonus']:+d}  |  ATK {gear['atk_bonus']:+d}  |  "
            f"SPD {gear['spd_bonus']:+.2f}  |  SPIT CD {gear['spit_cd_bonus']:+.2f}s"
        )
        stats_txt = self.font_tiny.render(stats_line, True, C_CYAN)
        self.screen.blit(stats_txt, (130, 485))

        gear_ctrl = self.font_tiny.render("Use LEFT/RIGHT to change gear", True, C_GRAY)
        self.screen.blit(gear_ctrl, (130, 525))

        go_txt = self.font_sm.render("Press ENTER to begin run", True, C_YELLOW)
        self.screen.blit(go_txt, (SCREEN_W // 2 - go_txt.get_width() // 2, SCREEN_H - 30))

    def _draw_floor_reward(self):
        self.screen.fill((10, 8, 16))
        title = self.font_big.render(f"Floor {self.floor_reward_completed_floor} Cleared!", True, C_YELLOW)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 60))

        subtitle = self.font_med.render("Choose one permanent gear upgrade", True, C_WHITE)
        self.screen.blit(subtitle, (SCREEN_W // 2 - subtitle.get_width() // 2, 110))

        for i, choice in enumerate(self.floor_reward_choices):
            y = 180 + i * 130
            selected = i == self.floor_reward_index
            bg = (45, 35, 60) if selected else (28, 23, 38)
            border = C_YELLOW if selected else C_GRAY
            pygame.draw.rect(self.screen, bg, (150, y, 660, 110), border_radius=10)
            pygame.draw.rect(self.screen, border, (150, y, 660, 110), 2, border_radius=10)

            name = self.font_med.render(choice["name"], True, C_GREEN if selected else C_WHITE)
            desc = self.font_sm.render(choice["description"], True, C_GRAY)
            self.screen.blit(name, (180, y + 14))
            self.screen.blit(desc, (180, y + 48))

            detail = (
                f"ATK {int(choice['atk_bonus']):+d} | HP {int(choice['hp_bonus']):+d} | "
                f"SPD {float(choice['spd_bonus']):+.2f} | SPIT CD {float(choice['spit_cd_bonus']):+.2f}s | "
                f"SPECIAL CD {float(choice['special_cd_bonus']):+.2f}s"
            )
            detail_txt = self.font_tiny.render(detail, True, C_CYAN)
            self.screen.blit(detail_txt, (180, y + 78))

        if self.floor_reward_bonus_loot:
            bonus_item = self._create_item(self.floor_reward_bonus_loot)
            bonus = self.font_med.render(f"5-Floor Bonus Loot: {bonus_item.name}", True, C_ORANGE)
            bonus_desc = self.font_tiny.render(bonus_item.description, True, C_GRAY)
            self.screen.blit(bonus, (SCREEN_W // 2 - bonus.get_width() // 2, SCREEN_H - 95))
            self.screen.blit(bonus_desc, (SCREEN_W // 2 - bonus_desc.get_width() // 2, SCREEN_H - 70))

        ctrl = self.font_sm.render("UP/DOWN to choose, ENTER to continue", True, C_GRAY)
        self.screen.blit(ctrl, (SCREEN_W // 2 - ctrl.get_width() // 2, SCREEN_H - 35))

    def _draw_game(self):
        self.screen.fill((8, 6, 12))

        if not self.dungeon:
            return

        # Calculate visible range
        tiles_x = SCREEN_W // TILE_SIZE + 4
        tiles_y = SCREEN_H // TILE_SIZE + 4
        start_tx = int(self.cam_x) - tiles_x // 2
        start_ty = int(self.cam_y) - tiles_y // 2

        # Draw floor tiles first
        for ty in range(start_ty, start_ty + tiles_y):
            for tx in range(start_tx, start_tx + tiles_x):
                if 0 <= tx < self.dungeon.w and 0 <= ty < self.dungeon.h:
                    if (tx, ty) not in self.explored:
                        continue
                    tile = self.dungeon.tiles[ty][tx]
                    sx, sy = self.world_to_screen(tx, ty)

                    if tile == TileType.FLOOR:
                        color = C_FLOOR if (tx + ty) % 2 == 0 else C_FLOOR2
                        pygame.draw.rect(self.screen, color, (sx, sy, TILE_SIZE + 1, TILE_SIZE + 1))
                        # Floor detail
                        if (tx * 7 + ty * 13) % 11 == 0:
                            pygame.draw.circle(self.screen, tuple(c + 8 for c in color), (sx + 24, sy + 24), 2)

                    elif tile == TileType.STAIRS_DOWN:
                        pygame.draw.rect(self.screen, C_FLOOR, (sx, sy, TILE_SIZE, TILE_SIZE))
                        # Stairs icon
                        for i in range(4):
                            step_y = sy + 8 + i * 8
                            step_w = TILE_SIZE - 8 - i * 6
                            pygame.draw.rect(self.screen, C_STAIRS, (sx + 4 + i * 3, step_y, step_w, 6))
                        txt = self.font_tiny.render("▼", True, C_YELLOW)
                        self.screen.blit(txt, (sx + 18, sy + 2))

                    elif tile == TileType.STAIRS_UP:
                        pygame.draw.rect(self.screen, C_FLOOR, (sx, sy, TILE_SIZE, TILE_SIZE))
                        for i in range(4):
                            step_y = sy + 32 - i * 8
                            step_w = TILE_SIZE - 8 - i * 6
                            pygame.draw.rect(self.screen, (120, 140, 100), (sx + 4 + i * 3, step_y, step_w, 6))

                    elif tile == TileType.CLUE:
                        pygame.draw.rect(self.screen, C_FLOOR, (sx, sy, TILE_SIZE, TILE_SIZE))
                        glow = int(abs(math.sin(self.time * 3)) * 80)
                        pygame.draw.circle(self.screen, (200 + glow // 3, 180 + glow // 2, 50 + glow),
                                         (sx + TILE_SIZE // 2, sy + TILE_SIZE // 2), 10)
                        txt = self.font_sm.render("?", True, C_WHITE)
                        self.screen.blit(txt, (sx + 18, sy + 12))

                    elif tile == TileType.TRAP:
                        pygame.draw.rect(self.screen, C_FLOOR, (sx, sy, TILE_SIZE, TILE_SIZE))
                        # Subtle spikes
                        for i in range(3):
                            for j in range(3):
                                px = sx + 10 + i * 12
                                py2 = sy + 10 + j * 12
                                pygame.draw.polygon(self.screen, (90, 70, 60),
                                                  [(px, py2 + 6), (px + 3, py2), (px + 6, py2 + 6)])

        # Draw walls with 2.5D extrusion (sorted by Y for depth)
        for ty in range(start_ty, start_ty + tiles_y):
            for tx in range(start_tx, start_tx + tiles_x):
                if 0 <= tx < self.dungeon.w and 0 <= ty < self.dungeon.h:
                    if (tx, ty) not in self.explored:
                        continue
                    tile = self.dungeon.tiles[ty][tx]
                    if tile == TileType.WALL:
                        sx, sy = self.world_to_screen(tx, ty)

                        # Wall front face (2.5D extrusion)
                        pygame.draw.rect(self.screen, C_WALL_SHADOW,
                                        (sx, sy, TILE_SIZE + 1, TILE_SIZE + WALL_HEIGHT + 1))
                        # Wall top face 
                        pygame.draw.rect(self.screen, C_WALL_TOP,
                                        (sx, sy - WALL_HEIGHT, TILE_SIZE + 1, WALL_HEIGHT + 1))
                        # Front face with shading
                        pygame.draw.rect(self.screen, C_WALL_FRONT,
                                        (sx + 1, sy + 1, TILE_SIZE - 1, TILE_SIZE - 1))
                        # Top edge highlight
                        pygame.draw.line(self.screen, (110, 95, 80), (sx, sy - WALL_HEIGHT), 
                                        (sx + TILE_SIZE, sy - WALL_HEIGHT))
                        # Brick lines
                        if (tx + ty) % 3 == 0:
                            pygame.draw.line(self.screen, C_WALL_SHADOW, 
                                           (sx + 4, sy + TILE_SIZE // 2), 
                                           (sx + TILE_SIZE - 4, sy + TILE_SIZE // 2))

        # Draw items on ground
        for ix, iy, item in self.items_on_ground:
            sx, sy = self.world_to_screen(ix, iy)
            bob = math.sin(self.time * 4 + ix * 3) * 3
            color = self._item_color(item.item_type)
            # Glow
            glow_s = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(glow_s, (*color, 40), (10, 10), 10)
            self.screen.blit(glow_s, (sx - 10, int(sy - 10 + bob)))
            pygame.draw.circle(self.screen, color, (sx, int(sy + bob)), 5)
            pygame.draw.circle(self.screen, C_WHITE, (sx - 1, int(sy - 2 + bob)), 2)

        # Draw enemies
        for enemy in sorted(self.enemies, key=lambda e: e.y):
            self._draw_enemy(enemy)

        # Draw player
        self._draw_player()

        # Draw projectiles (spit)
        for proj in self.projectiles:
            sx, sy = self.world_to_screen(proj.x, proj.y)
            # Glow
            glow_s = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(glow_s, (*proj.color, 60), (12, 12), 12)
            self.screen.blit(glow_s, (sx - 12, sy - 12))
            # Core
            pygame.draw.circle(self.screen, proj.color, (sx, sy), int(proj.size))
            pygame.draw.circle(self.screen, C_WHITE, (sx - 1, sy - 1), max(1, int(proj.size) - 2))

        # Draw particles
        for p in self.particles:
            sx, sy = self.world_to_screen(p.x, p.y)
            alpha = int(255 * (p.life / p.max_life))
            s = pygame.Surface((int(p.size * 2), int(p.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p.color, alpha), (int(p.size), int(p.size)), int(p.size))
            self.screen.blit(s, (sx - int(p.size), sy - int(p.size)))

        # Draw floating texts
        for ft in self.floating_texts:
            sx, sy = self.world_to_screen(ft.x, ft.y)
            alpha = int(255 * ft.life)
            txt = self.font_sm.render(ft.text, True, ft.color)
            txt.set_alpha(alpha)
            self.screen.blit(txt, (sx - txt.get_width() // 2, sy))

        # === HUD ===
        self._draw_hud()

    def _draw_player(self):
        sx, sy = self.world_to_screen(self.px, self.py)

        # Invulnerability flash
        if self.invulnerable > 0 and int(self.time * 10) % 2 == 0:
            return

        color = PET_STATS[self.pet_type]["color"] if self.pet_type else C_WHITE
        dark_color = tuple(max(0, c - 40) for c in color)

        # Shadow
        shadow = pygame.Surface((28, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 60), (0, 0, 28, 10))
        self.screen.blit(shadow, (sx - 14, sy + 4))

        bob = math.sin(self.walk_anim) * 2

        # Body
        pygame.draw.ellipse(self.screen, color, (sx - 12, int(sy - 10 + bob), 24, 18))
        # Head
        pygame.draw.circle(self.screen, color, (sx, int(sy - 16 + bob)), 10)

        # Eyes (direction-based)
        eye_ox = math.cos(self.facing) * 3
        eye_oy = math.sin(self.facing) * 2
        pygame.draw.circle(self.screen, C_BLACK, (int(sx - 3 + eye_ox), int(sy - 18 + bob + eye_oy)), 2)
        pygame.draw.circle(self.screen, C_BLACK, (int(sx + 3 + eye_ox), int(sy - 18 + bob + eye_oy)), 2)
        # Eye shine
        pygame.draw.circle(self.screen, C_WHITE, (int(sx - 2 + eye_ox), int(sy - 19 + bob + eye_oy)), 1)
        pygame.draw.circle(self.screen, C_WHITE, (int(sx + 4 + eye_ox), int(sy - 19 + bob + eye_oy)), 1)

        # Pet-specific features
        if self.pet_type == PetType.DOG:
            pygame.draw.ellipse(self.screen, dark_color, (sx - 12, int(sy - 28 + bob), 8, 10))
            pygame.draw.ellipse(self.screen, dark_color, (sx + 4, int(sy - 28 + bob), 8, 10))
            # Nose
            pygame.draw.circle(self.screen, C_BLACK, (sx, int(sy - 14 + bob)), 2)
        elif self.pet_type == PetType.CAT:
            pygame.draw.polygon(self.screen, color, [
                (sx - 8, int(sy - 28 + bob)), (sx - 4, int(sy - 18 + bob)), (sx - 12, int(sy - 18 + bob))])
            pygame.draw.polygon(self.screen, color, [
                (sx + 8, int(sy - 28 + bob)), (sx + 4, int(sy - 18 + bob)), (sx + 12, int(sy - 18 + bob))])
            # Whiskers
            pygame.draw.line(self.screen, C_WHITE, (sx - 5, int(sy - 14 + bob)), (sx - 15, int(sy - 16 + bob)))
            pygame.draw.line(self.screen, C_WHITE, (sx + 5, int(sy - 14 + bob)), (sx + 15, int(sy - 16 + bob)))
        elif self.pet_type == PetType.HAMSTER:
            pygame.draw.circle(self.screen, tuple(min(255, c + 30) for c in color),
                              (sx - 8, int(sy - 14 + bob)), 5)
            pygame.draw.circle(self.screen, tuple(min(255, c + 30) for c in color),
                              (sx + 8, int(sy - 14 + bob)), 5)
            pygame.draw.circle(self.screen, dark_color, (sx - 7, int(sy - 24 + bob)), 4)
            pygame.draw.circle(self.screen, dark_color, (sx + 7, int(sy - 24 + bob)), 4)

        # Attack swing visual
        if self.attack_timer > self.attack_cooldown * 0.5:
            atk_x = sx + math.cos(self.facing) * 20
            atk_y = sy + math.sin(self.facing) * 20
            alpha = int(200 * (self.attack_timer / self.attack_cooldown))
            atk_s = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.arc(atk_s, (*C_WHITE, alpha), (0, 0, 30, 30),
                          self.facing - 0.8, self.facing + 0.8, 3)
            self.screen.blit(atk_s, (int(atk_x) - 15, int(atk_y) - 15))

    def _draw_enemy(self, e: Enemy):
        sx, sy = self.world_to_screen(e.x, e.y)

        if e.stun_timer > 0 and int(self.time * 10) % 2 == 0:
            return

        # Shadow
        shadow = pygame.Surface((e.size * 2, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 60), (0, 0, e.size * 2, 8))
        self.screen.blit(shadow, (sx - e.size, sy + 3))

        bob = math.sin(e.anim_timer * 5) * 2

        # Body
        body_color = e.color
        if e.stun_timer > 0:
            body_color = C_CYAN
        pygame.draw.ellipse(self.screen, body_color,
                           (sx - e.size, int(sy - e.size + bob), e.size * 2, int(e.size * 1.5)))
        # Head
        head_size = e.size - 3
        pygame.draw.circle(self.screen, body_color, (sx, int(sy - e.size - 2 + bob)), head_size)

        # Eyes (red when alert)
        eye_col = C_RED if e.alert else C_WHITE
        pygame.draw.circle(self.screen, eye_col, (sx - 3, int(sy - e.size - 3 + bob)), 2)
        pygame.draw.circle(self.screen, eye_col, (sx + 3, int(sy - e.size - 3 + bob)), 2)

        # Boss crown
        if e.is_boss:
            crown_y = int(sy - e.size - head_size - 5 + bob)
            pygame.draw.polygon(self.screen, C_YELLOW, [
                (sx - 8, crown_y + 6), (sx - 8, crown_y),
                (sx - 4, crown_y + 3), (sx, crown_y - 2),
                (sx + 4, crown_y + 3), (sx + 8, crown_y),
                (sx + 8, crown_y + 6)
            ])

        # HP bar
        if e.hp < e.max_hp:
            bar_w = e.size * 2
            bar_h = 4
            bar_x = sx - bar_w // 2
            bar_y = int(sy - e.size - head_size - 8 + bob)
            if e.is_boss:
                bar_y -= 10
            pygame.draw.rect(self.screen, C_DARK_GRAY, (bar_x, bar_y, bar_w, bar_h))
            fill = int(bar_w * e.hp / e.max_hp)
            pygame.draw.rect(self.screen, C_RED, (bar_x, bar_y, fill, bar_h))

        # Name for bosses
        if e.is_boss:
            name = self.font_tiny.render(e.enemy_type.value, True, C_RED)
            self.screen.blit(name, (sx - name.get_width() // 2, int(sy - e.size - 30 + bob)))

        # Stunned stars
        if e.stun_timer > 0:
            for i in range(3):
                star_angle = self.time * 5 + i * 2.1
                star_x = sx + math.cos(star_angle) * 12
                star_y = sy - e.size - 10 + math.sin(star_angle) * 5
                txt = self.font_tiny.render("★", True, C_YELLOW)
                self.screen.blit(txt, (int(star_x), int(star_y)))

    def _draw_hud(self):
        # HP bar
        pygame.draw.rect(self.screen, (20, 15, 25), (10, 10, 220, 70), border_radius=8)
        pygame.draw.rect(self.screen, C_GRAY, (10, 10, 220, 70), 2, border_radius=8)

        # Pet icon
        if self.pet_type:
            color = PET_STATS[self.pet_type]["color"]
            pygame.draw.circle(self.screen, color, (40, 35), 12)
            pygame.draw.circle(self.screen, C_BLACK, (37, 33), 2)
            pygame.draw.circle(self.screen, C_BLACK, (43, 33), 2)

        # HP
        hp_text = self.font_sm.render(f"HP: {self.hp}/{self.max_hp}", True, C_WHITE)
        self.screen.blit(hp_text, (60, 18))
        bar_w = 148
        pygame.draw.rect(self.screen, C_DARK_GRAY, (60, 38, bar_w, 10))
        hp_fill = int(bar_w * max(0, self.hp) / self.max_hp)
        hp_color = C_GREEN if self.hp > self.max_hp * 0.5 else C_YELLOW if self.hp > self.max_hp * 0.25 else C_RED
        pygame.draw.rect(self.screen, hp_color, (60, 38, hp_fill, 10))

        # XP
        xp_text = self.font_tiny.render(f"Lv.{self.level} XP:{self.xp}/{self.xp_to_next}", True, C_CYAN)
        self.screen.blit(xp_text, (60, 52))
        pygame.draw.rect(self.screen, C_DARK_GRAY, (130, 55, 76, 5))
        xp_fill = int(76 * self.xp / self.xp_to_next)
        pygame.draw.rect(self.screen, C_CYAN, (130, 55, xp_fill, 5))

        # Floor info
        floor_cap = "∞" if self.is_infinite_mode else str(self.max_floors)
        floor_text = self.font_sm.render(f"Floor {self.floor_num}/{floor_cap}", True, C_YELLOW)
        self.screen.blit(floor_text, (SCREEN_W - 120, 15))
        mode_text = self.font_tiny.render(self.difficulty, True, C_CYAN)
        self.screen.blit(mode_text, (SCREEN_W - 120, 30))

        # Attack power
        atk_text = self.font_tiny.render(f"ATK: {self.attack_power}", True, C_ORANGE)
        self.screen.blit(atk_text, (SCREEN_W - 120, 45))

        gear_name = self.equipped_gear.get("name", "No Gear") if isinstance(self.equipped_gear, dict) else "No Gear"
        gear_txt = self.font_tiny.render(f"Gear: {gear_name}", True, C_GREEN)
        self.screen.blit(gear_txt, (SCREEN_W - 220, 60))

        # Keys
        if self.keys_held > 0:
            key_text = self.font_tiny.render(f"Keys: {self.keys_held}", True, C_YELLOW)
            self.screen.blit(key_text, (SCREEN_W - 120, 55))

        # Clues found
        clue_text = self.font_tiny.render(f"Clues: {len(self.clues_found)}", True, C_PURPLE)
        self.screen.blit(clue_text, (SCREEN_W - 120, 70))

        # Special cooldown
        if self.pet_type:
            spec_name = PET_STATS[self.pet_type]["special"].split("(")[0].strip()
            if self.special_cooldown > 0:
                cd_text = self.font_sm.render(f"Q: {spec_name} ({self.special_cooldown:.1f}s)", True, C_GRAY)
            else:
                cd_text = self.font_sm.render(f"Q: {spec_name} READY", True, C_PURPLE)
            self.screen.blit(cd_text, (10, SCREEN_H - 70))

        # Inventory quick bar
        bar_y = SCREEN_H - 45
        for i in range(min(6, max(len(self.inventory), 1))):
            ix = 10 + i * 50
            selected = i == self.selected_item
            border = C_YELLOW if selected else C_GRAY
            pygame.draw.rect(self.screen, (25, 20, 30), (ix, bar_y, 44, 38), border_radius=4)
            pygame.draw.rect(self.screen, border, (ix, bar_y, 44, 38), 2, border_radius=4)
            if i < len(self.inventory):
                item = self.inventory[i]
                color = self._item_color(item.item_type)
                pygame.draw.circle(self.screen, color, (ix + 22, bar_y + 16), 8)
                num = self.font_tiny.render(str(item.count), True, C_WHITE)
                self.screen.blit(num, (ix + 30, bar_y + 22))
            key_txt = self.font_tiny.render(str(i + 1), True, C_GRAY)
            self.screen.blit(key_txt, (ix + 2, bar_y + 2))

        # E to use
        use_txt = self.font_tiny.render("CLICK: Spit | SPACE: Melee | E: Use Item | TAB: Inventory | Q: Special", True, C_GRAY)
        self.screen.blit(use_txt, (10, SCREEN_H - 90))

        # Minimap
        self._draw_minimap()

    def _draw_minimap(self):
        map_size = 100
        map_x = SCREEN_W - map_size - 10
        map_y = SCREEN_H - map_size - 50
        map_surface = pygame.Surface((map_size, map_size), pygame.SRCALPHA)
        map_surface.fill((0, 0, 0, 150))

        scale = map_size / max(self.dungeon.w, self.dungeon.h)
        for (tx, ty) in self.explored:
            if 0 <= tx < self.dungeon.w and 0 <= ty < self.dungeon.h:
                tile = self.dungeon.tiles[ty][tx]
                if tile == TileType.FLOOR:
                    color = (60, 50, 45, 200)
                elif tile == TileType.WALL:
                    color = (100, 85, 75, 200)
                elif tile == TileType.STAIRS_DOWN:
                    color = (*C_YELLOW, 255)
                elif tile == TileType.STAIRS_UP:
                    color = (*C_CYAN, 255)
                elif tile == TileType.CLUE:
                    color = (*C_PURPLE, 255)
                else:
                    color = (50, 40, 35, 200)
                mx = int(tx * scale)
                my = int(ty * scale)
                pygame.draw.rect(map_surface, color, (mx, my, max(2, int(scale)), max(2, int(scale))))

        # Player dot
        px = int(self.px * scale)
        py = int(self.py * scale)
        pygame.draw.circle(map_surface, C_GREEN, (px, py), 3)

        # Enemy dots
        for e in self.enemies:
            ex = int(e.x * scale)
            ey = int(e.y * scale)
            col = C_RED if e.alert else C_ORANGE
            pygame.draw.circle(map_surface, col, (ex, ey), 2)

        self.screen.blit(map_surface, (map_x, map_y))
        pygame.draw.rect(self.screen, C_GRAY, (map_x, map_y, map_size, map_size), 1)

    def _draw_inventory_overlay(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title = self.font_big.render("Inventory", True, C_WHITE)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 80))

        if not self.inventory:
            empty = self.font_med.render("Empty... find some items!", True, C_GRAY)
            self.screen.blit(empty, (SCREEN_W // 2 - empty.get_width() // 2, 200))
        else:
            for i, item in enumerate(self.inventory):
                y = 150 + i * 60
                selected = i == self.selected_item
                bg_color = (50, 45, 55) if selected else (30, 25, 35)
                pygame.draw.rect(self.screen, bg_color, (250, y, 460, 50), border_radius=6)
                if selected:
                    pygame.draw.rect(self.screen, C_YELLOW, (250, y, 460, 50), 2, border_radius=6)

                color = self._item_color(item.item_type)
                pygame.draw.circle(self.screen, color, (280, y + 25), 12)

                name = self.font_med.render(f"{item.name} x{item.count}", True, C_WHITE)
                desc = self.font_tiny.render(item.description, True, C_GRAY)
                self.screen.blit(name, (305, y + 5))
                self.screen.blit(desc, (305, y + 30))

        # Clues section
        clue_title = self.font_med.render(f"Clues Found: {len(self.clues_found)}", True, C_PURPLE)
        self.screen.blit(clue_title, (SCREEN_W // 2 - clue_title.get_width() // 2, SCREEN_H - 180))
        gear_name = self.equipped_gear.get("name", "No Gear") if isinstance(self.equipped_gear, dict) else "No Gear"
        gear_info = self.font_tiny.render(f"Equipped: {gear_name}", True, C_GREEN)
        self.screen.blit(gear_info, (SCREEN_W // 2 - gear_info.get_width() // 2, SCREEN_H - 205))
        for i, clue in enumerate(self.clues_found[-3:]):
            ct = self.font_tiny.render(f"• {clue.text[:60]}...", True, (160, 140, 180))
            self.screen.blit(ct, (200, SCREEN_H - 150 + i * 20))

        close = self.font_sm.render("Press TAB to close", True, C_GRAY)
        self.screen.blit(close, (SCREEN_W // 2 - close.get_width() // 2, SCREEN_H - 40))

    def _draw_pause(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        txt = self.font_big.render("PAUSED", True, C_WHITE)
        self.screen.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, SCREEN_H // 2 - 40))
        sub = self.font_sm.render("Press ESC to resume", True, C_GRAY)
        self.screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, SCREEN_H // 2 + 10))

    def _draw_clue(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Clue card
        card_w, card_h = 500, 200
        card_x = SCREEN_W // 2 - card_w // 2
        card_y = SCREEN_H // 2 - card_h // 2
        pygame.draw.rect(self.screen, (40, 30, 50), (card_x, card_y, card_w, card_h), border_radius=12)
        pygame.draw.rect(self.screen, C_PURPLE, (card_x, card_y, card_w, card_h), 3, border_radius=12)

        title = self.font_med.render(f"Clue #{len(self.clues_found)} Found!", True, C_PURPLE)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, card_y + 20))

        # Word wrap clue text
        words = self.current_clue_text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if self.font_sm.size(test_line)[0] < card_w - 40:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        for i, line in enumerate(lines):
            txt = self.font_sm.render(line, True, C_WHITE)
            self.screen.blit(txt, (card_x + 20, card_y + 60 + i * 24))

        prompt = self.font_sm.render("Press ENTER to continue", True, C_GRAY)
        self.screen.blit(prompt, (SCREEN_W // 2 - prompt.get_width() // 2, card_y + card_h - 35))

    def _draw_death(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((60, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title = self.font_big.render("You collapsed...", True, C_RED)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 200))

        sub = self.font_med.render("But your owner is still out there...", True, C_WHITE)
        self.screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, 260))

        stats = [
            f"Floor reached: {self.floor_num}",
            f"Level: {self.level}",
            f"Clues found: {len(self.clues_found)}",
        ]
        for i, s in enumerate(stats):
            txt = self.font_sm.render(s, True, C_GRAY)
            self.screen.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, 320 + i * 30))

        blink = math.sin(self.time * 3) > 0
        if blink:
            prompt = self.font_med.render("Press ENTER to try again", True, C_YELLOW)
            self.screen.blit(prompt, (SCREEN_W // 2 - prompt.get_width() // 2, 450))

    def _draw_victory(self):
        self.screen.fill((10, 15, 25))

        # Starfield
        for i in range(50):
            sx = (self.time * 10 + i * 73) % SCREEN_W
            sy = (i * 37 + math.sin(self.time + i) * 20) % SCREEN_H
            brightness = int(150 + math.sin(self.time * 2 + i) * 100)
            pygame.draw.circle(self.screen, (brightness, brightness, brightness), (int(sx), int(sy)), 1)

        title = self.font_big.render("YOU FOUND YOUR OWNER!", True, C_YELLOW)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 120))

        # Reunion scene
        pet_color = PET_STATS[self.pet_type]["color"] if self.pet_type else C_BROWN
        # Owner
        pygame.draw.circle(self.screen, (200, 160, 130), (SCREEN_W // 2 + 30, 300), 20)  # Head
        pygame.draw.rect(self.screen, C_BLUE, (SCREEN_W // 2 + 10, 320, 40, 50))  # Body
        # Pet
        bob = math.sin(self.time * 4) * 5
        pygame.draw.ellipse(self.screen, pet_color, 
                           (SCREEN_W // 2 - 40, int(330 + bob), 30, 20))
        pygame.draw.circle(self.screen, pet_color, (SCREEN_W // 2 - 25, int(320 + bob)), 10)

        # Hearts
        for i in range(5):
            hx = SCREEN_W // 2 - 20 + math.cos(self.time * 2 + i * 1.3) * 40
            hy = 280 + math.sin(self.time * 3 + i * 0.7) * 15
            txt = self.font_med.render("♥", True, C_RED)
            self.screen.blit(txt, (int(hx), int(hy)))

        # Story text
        lines = [
            f"After {self.max_floors} harrowing dungeon floors,",
            f"the brave little {self.pet_type.value if self.pet_type else 'pet'} finally found their owner.",
            "",
            f"Level {self.level} | Clues found: {len(self.clues_found)}",
            "",
            '"I knew you\'d find me," they whispered,',
            "holding their beloved pet close.",
            "",
            "You are home at last."
        ]
        for i, line in enumerate(lines):
            color = C_WHITE if i < 2 else C_GRAY if i > 2 else C_YELLOW
            txt = self.font_sm.render(line, True, color)
            self.screen.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, 400 + i * 25))

        blink = math.sin(self.time * 3) > 0
        if blink:
            prompt = self.font_med.render("Press ENTER to play again", True, C_GREEN)
            self.screen.blit(prompt, (SCREEN_W // 2 - prompt.get_width() // 2, SCREEN_H - 60))

    # === MAIN LOOP ===
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)  # Cap delta time

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.is_infinite_mode and self.state in ("playing", "paused", "inventory", "clue"):
                        self._save_infinite_progress()
                    running = False

                if event.type == pygame.KEYDOWN:
                    if self.state == "title":
                        if event.key == pygame.K_RETURN:
                            self.state = "select"

                    elif self.state == "select":
                        pets = list(PetType)
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            self.selection_index = (self.selection_index - 1) % len(pets)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            self.selection_index = (self.selection_index + 1) % len(pets)
                        elif event.key == pygame.K_RETURN:
                            self.pending_pet = pets[self.selection_index]
                            self.difficulty_index = 1
                            self.state = "difficulty"

                    elif self.state == "difficulty":
                        if event.key in (pygame.K_UP, pygame.K_w):
                            self.difficulty_index = (self.difficulty_index - 1) % len(self.difficulty_options)
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.difficulty_index = (self.difficulty_index + 1) % len(self.difficulty_options)
                        elif event.key == pygame.K_ESCAPE:
                            self.state = "select"
                        elif event.key == pygame.K_RETURN and self.pending_pet:
                            selected_difficulty = self.difficulty_options[self.difficulty_index]
                            if selected_difficulty == "Infinite" and self._infinite_save_exists():
                                self.state = "infinite_prompt"
                            else:
                                self.start_game(self.pending_pet, selected_difficulty)

                    elif self.state == "infinite_prompt":
                        if event.key == pygame.K_c:
                            loaded = self._load_infinite_progress()
                            if not loaded and self.pending_pet:
                                self.start_game(self.pending_pet, "Infinite")
                        elif event.key == pygame.K_n and self.pending_pet:
                            self._clear_infinite_save()
                            self.start_game(self.pending_pet, "Infinite")
                        elif event.key == pygame.K_ESCAPE:
                            self.state = "difficulty"

                    elif self.state == "prep":
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            self.prep_gear_index = (self.prep_gear_index - 1) % len(self.prep_gear_options)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            self.prep_gear_index = (self.prep_gear_index + 1) % len(self.prep_gear_options)
                        elif event.key in (pygame.K_UP, pygame.K_w):
                            self.prep_item_index = (self.prep_item_index - 1) % len(self.prep_item_options)
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.prep_item_index = (self.prep_item_index + 1) % len(self.prep_item_options)
                        elif event.key == pygame.K_ESCAPE:
                            self.state = "difficulty"
                        elif event.key == pygame.K_RETURN:
                            self._apply_prep_loadout()

                    elif self.state == "floor_reward":
                        if event.key in (pygame.K_UP, pygame.K_w):
                            if self.floor_reward_choices:
                                self.floor_reward_index = (self.floor_reward_index - 1) % len(self.floor_reward_choices)
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            if self.floor_reward_choices:
                                self.floor_reward_index = (self.floor_reward_index + 1) % len(self.floor_reward_choices)
                        elif event.key == pygame.K_RETURN:
                            self._apply_floor_reward_choice()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and self.state == "playing":
                        self.do_spit(*event.pos)

                if event.type == pygame.KEYDOWN:
                    if self.state == "playing":
                        if event.key == pygame.K_SPACE:
                            self.do_attack()
                        elif event.key == pygame.K_q:
                            self.do_special()
                        elif event.key == pygame.K_e:
                            self.use_item()
                        elif event.key == pygame.K_TAB:
                            self.state = "inventory"
                        elif event.key == pygame.K_ESCAPE:
                            self.state = "paused"
                        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6):
                            idx = event.key - pygame.K_1
                            if idx < len(self.inventory):
                                self.selected_item = idx

                    elif self.state == "inventory":
                        if event.key == pygame.K_TAB or event.key == pygame.K_ESCAPE:
                            self.state = "playing"
                        elif event.key in (pygame.K_UP, pygame.K_w):
                            self.selected_item = max(0, self.selected_item - 1)
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.selected_item = min(len(self.inventory) - 1, self.selected_item + 1)
                        elif event.key == pygame.K_e:
                            self.use_item()

                    elif self.state == "paused":
                        if event.key == pygame.K_ESCAPE:
                            self.state = "playing"

                    elif self.state == "clue":
                        if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                            self.state = "playing"

                    elif self.state == "dead":
                        if event.key == pygame.K_RETURN:
                            self.state = "select"

                    elif self.state == "victory":
                        if event.key == pygame.K_RETURN:
                            self.state = "title"

            self.update(dt)
            self.draw()

        pygame.quit()

# === ENTRY POINT ===
def main():
    game = PetDungeonCrawler()
    game.run()

if __name__ == "__main__":
    main()
