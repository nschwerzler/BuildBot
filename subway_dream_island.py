"""
Subway: Dream Island Run

Goal:
- Survive the subway.
- Earn currency called CHICKENS.
- Buy the first train to unlock full subway navigation (no longer stuck).
- Save enough CHICKENS to buy the Dream Island train.

Controls:
- WASD / Arrow Keys: Move
- E: Interact (sell, buy train)
- F: Use selected item
- 1-5: Select inventory slot
- ESC: Quit

Rules:
- Loot appears only at NIGHT.
- You must survive and keep SANITY up.
"""

import math
import random
import sys
from dataclasses import dataclass
from typing import List, Tuple

import pygame

# ---------- Config ----------
SCREEN_W, SCREEN_H = 1100, 700
FPS = 60

WORLD_W, WORLD_H = 2400, 680
FLOOR_Y = 620

DAY_LENGTH = 55.0
NIGHT_LENGTH = 55.0

FIRST_TRAIN_COST = 25
DREAM_TRAIN_COST = 10000

PLAYER_SPEED = 260
PLAYER_MAX_HP = 100
PLAYER_MAX_SANITY = 100

LOOT_SPAWN_EVERY = (1.6, 3.2)
ENEMY_SPAWN_EVERY = (3.8, 6.5)
SURFACE_WORK_COOLDOWN = 3.0

# ---------- Colors ----------
C_BG_DAY = (26, 30, 38)
C_BG_NIGHT = (10, 10, 16)
C_PLATFORM = (48, 52, 64)
C_TRACK = (30, 24, 24)
C_RAIL = (120, 110, 96)
C_WHITE = (240, 240, 240)
C_GRAY = (160, 165, 178)
C_RED = (220, 80, 90)
C_GREEN = (80, 220, 120)
C_YELLOW = (240, 215, 100)
C_CYAN = (100, 200, 220)
C_PURPLE = (170, 110, 220)
C_ORANGE = (235, 150, 70)


@dataclass
class Item:
    name: str
    kind: str  # sell, sanity, heal
    value: int


@dataclass
class LootDrop:
    x: float
    y: float
    item: Item


@dataclass
class NightEnemy:
    x: float
    y: float
    hp: int = 24
    speed: float = 95
    hit_cd: float = 0.0


class SubwayDreamIsland:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Subway: Dream Island Run")
        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont("Arial", 40, bold=True)
        self.font_med = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_sm = pygame.font.SysFont("Arial", 18)
        self.font_tiny = pygame.font.SysFont("Consolas", 15)

        self.running = True

        self.player_x = 220.0
        self.player_y = FLOOR_Y - 26
        self.player_hp = PLAYER_MAX_HP
        self.player_sanity = PLAYER_MAX_SANITY

        self.inventory: List[Item] = []
        self.selected_slot = 0
        self.chickens = 100

        self.nav_unlocked = False
        self.has_bought_first_train = False
        self.won = False
        self.subway_level = 1
        self.on_surface = False
        self.surface_work_cd = 0.0

        self.phase = "day"  # day, night
        self.phase_timer = DAY_LENGTH

        self.loot: List[LootDrop] = []
        self.enemies: List[NightEnemy] = []
        self.loot_spawn_timer = random.uniform(*LOOT_SPAWN_EVERY)
        self.enemy_spawn_timer = random.uniform(*ENEMY_SPAWN_EVERY)

        self.message = "You are stuck in the subway. Survive, earn CHICKENS, find the trains."
        self.msg_timer = 6.0

        self.cam_x = 0.0

        self.safe_light_posts = [320, 610, 980, 1390, 1810, 2200]

        # Interaction points
        self.trade_booths = [360, 1480]  # day-only sell + work
        self.first_train_x = 630
        self.dream_train_x = 2260
        self.surface_exit_x = 1080
        self.surface_work_spots = [780, 1450]
        self.surface_return_x = 210
        self.dream_train_available = False

        # Place some guaranteed loot in the currently reachable area.
        self._drop_loot_cache(150, 640, 7)

    def get_transfer_train_cost(self) -> int:
        if not self.has_bought_first_train:
            return FIRST_TRAIN_COST
        return max(18, 40 - (self.subway_level - 1) * 3)

    def get_dream_train_cost(self) -> int:
        return max(4200, DREAM_TRAIN_COST - (self.subway_level - 1) * 650)

    def reroll_subway_map(self, from_train: bool = False):
        self.subway_level += 1
        self.loot.clear()
        self.enemies.clear()

        # Better subway tiers get broader, richer station layouts.
        booth_mid = random.randint(1160, 1720)
        self.trade_booths = [random.randint(250, 520), booth_mid]
        self.safe_light_posts = sorted([
            random.randint(260, 420),
            random.randint(540, 760),
            random.randint(860, 1120),
            random.randint(1220, 1500),
            random.randint(1620, 1900),
            random.randint(1980, 2260),
        ])
        self.first_train_x = random.randint(560, 840)
        self.surface_exit_x = random.randint(980, 1320)
        self.dream_train_x = random.randint(1980, 2320)

        left_spot = random.randint(700, 980)
        right_spot = random.randint(1280, 1680)
        self.surface_work_spots = [left_spot, right_spot]

        chance = min(0.2 + (self.subway_level - 1) * 0.12, 0.9)
        self.dream_train_available = random.random() < chance

        # Fresh nearby loot when arriving in a new station.
        self._drop_loot_cache(140, 760 if not self.nav_unlocked else 960, 8)

        self.player_x = max(170, self.first_train_x - 130) if from_train else 220
        self.player_y = FLOOR_Y - 26
        self.on_surface = False
        self.surface_work_cd = 0.0
        self.message = f"Arrived at Subway {self.subway_level}. Trains are better here."
        self.msg_timer = 3.8

    # ---------- Core ----------
    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_e:
                    self.try_interact()
                elif event.key == pygame.K_f:
                    self.use_selected_item()
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
                    idx = event.key - pygame.K_1
                    self.selected_slot = max(0, min(idx, 4))

    def update(self, dt: float):
        if self.won:
            return

        self.update_phase(dt)
        if self.surface_work_cd > 0:
            self.surface_work_cd = max(0.0, self.surface_work_cd - dt)
        self.update_player(dt)
        self.update_loot(dt)
        self.update_enemies(dt)
        self.update_message(dt)
        self.update_camera(dt)

        if self.player_hp <= 0 or self.player_sanity <= 0:
            self.message = "You didn\'t survive the subway night... Press ESC to quit."
            self.msg_timer = 999

    # ---------- Systems ----------
    def update_phase(self, dt: float):
        self.phase_timer -= dt
        if self.phase_timer <= 0:
            if self.phase == "day":
                self.phase = "night"
                self.phase_timer = NIGHT_LENGTH
                self.message = "NIGHT: Subway survival begins. Loot starts appearing."
                self.msg_timer = 4.5
            else:
                self.phase = "day"
                self.phase_timer = DAY_LENGTH
                self.enemies.clear()
                # Better subway tiers improve dream-train appearance odds.
                chance = min(0.2 + (self.subway_level - 1) * 0.12, 0.9)
                self.dream_train_available = random.random() < chance
                self.message = "DAY: Less danger. Sell loot and prepare."
                self.msg_timer = 4.0

        if self.phase == "night":
            # Constant sanity pressure at night.
            drain = 1.3
            near_light = min(abs(self.player_x - lp) for lp in self.safe_light_posts) < 85
            if near_light:
                drain *= 0.2
            self.player_sanity = max(0, self.player_sanity - drain * dt)
        else:
            self.player_sanity = min(PLAYER_MAX_SANITY, self.player_sanity + 3.2 * dt)

    def update_player(self, dt: float):
        if self.player_hp <= 0 or self.player_sanity <= 0:
            return

        keys = pygame.key.get_pressed()
        dx = 0.0
        dy = 0.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1

        speed = PLAYER_SPEED
        if self.phase == "night":
            speed *= 0.93

        if dx != 0 or dy != 0:
            mag = math.sqrt(dx * dx + dy * dy)
            if mag > 0:
                dx /= mag
                dy /= mag

        self.player_x += dx * speed * dt
        self.player_y += dy * speed * dt

        min_x = 80
        max_x = WORLD_W - 80

        # "Stuck" until first train is entered.
        if not self.nav_unlocked:
            max_x = 690

        self.player_x = max(min_x, min(max_x, self.player_x))
        self.player_y = max(FLOOR_Y - 220, min(FLOOR_Y - 18, self.player_y))

    def update_loot(self, dt: float):
        if self.phase != "night" or self.on_surface:
            return

        self.loot_spawn_timer -= dt
        if self.loot_spawn_timer <= 0:
            self.loot_spawn_timer = random.uniform(*LOOT_SPAWN_EVERY)
            spawn_max = WORLD_W - 120 if self.nav_unlocked else 660
            x = random.uniform(120, spawn_max)
            y = FLOOR_Y - 10
            self.loot.append(LootDrop(x, y, self.roll_loot()))

    def update_enemies(self, dt: float):
        if self.phase != "night" or self.player_hp <= 0 or self.on_surface:
            return

        self.enemy_spawn_timer -= dt
        if self.enemy_spawn_timer <= 0:
            self.enemy_spawn_timer = random.uniform(*ENEMY_SPAWN_EVERY)
            spawn_max = WORLD_W - 120 if self.nav_unlocked else 670
            side = random.choice([-1, 1])
            x = self.player_x + side * random.uniform(260, 380)
            x = max(110, min(spawn_max, x))
            self.enemies.append(NightEnemy(x=x, y=FLOOR_Y - 22, hp=24 + random.randint(0, 8), speed=95 + random.random() * 35))

        for enemy in self.enemies:
            dir_sign = 1 if self.player_x > enemy.x else -1
            enemy.x += dir_sign * enemy.speed * dt
            enemy.hit_cd = max(0.0, enemy.hit_cd - dt)

            if abs(enemy.x - self.player_x) < 24 and enemy.hit_cd <= 0:
                enemy.hit_cd = 1.0
                hp_hit = random.randint(5, 10)
                sanity_hit = random.randint(2, 5)
                self.player_hp = max(0, self.player_hp - hp_hit)
                self.player_sanity = max(0, self.player_sanity - sanity_hit)
                self.message = f"Night creature hit! -{hp_hit} HP, -{sanity_hit} SANITY"
                self.msg_timer = 1.3

        # Optional self-defense: if player uses sanity/heal items they can outlast; simple despawn drift
        self.enemies = [e for e in self.enemies if -50 < e.x < WORLD_W + 50 and e.hp > 0]

    def _drop_loot_cache(self, x_min: float, x_max: float, count: int):
        for _ in range(count):
            x = random.uniform(x_min, x_max)
            y = random.uniform(FLOOR_Y - 95, FLOOR_Y - 8)
            self.loot.append(LootDrop(x, y, self.roll_loot()))

    def update_message(self, dt: float):
        self.msg_timer = max(0.0, self.msg_timer - dt)

    def update_camera(self, dt: float):
        target = self.player_x - SCREEN_W * 0.5
        target = max(0, min(WORLD_W - SCREEN_W, target))
        self.cam_x += (target - self.cam_x) * min(1.0, dt * 8.0)

    # ---------- Interactions ----------
    def try_interact(self):
        if self.player_hp <= 0 or self.player_sanity <= 0 or self.won:
            return

        if self.on_surface:
            if abs(self.player_x - self.surface_return_x) < 55:
                self.on_surface = False
                self.player_x = self.surface_exit_x + 40
                self.message = "Returned to the subway platform."
                self.msg_timer = 2.0
                return

            for spot in self.surface_work_spots:
                if abs(self.player_x - spot) < 55:
                    if self.phase != "day":
                        self.message = "Surface jobs run during daytime only."
                        self.msg_timer = 2.0
                        return
                    if self.surface_work_cd > 0:
                        self.message = f"Work shift cooling down: {self.surface_work_cd:0.1f}s"
                        self.msg_timer = 1.4
                        return
                    earn = random.randint(16, 28) + (self.subway_level - 1) * 4
                    self.chickens += earn
                    self.surface_work_cd = SURFACE_WORK_COOLDOWN
                    self.message = f"Surface work shift complete: +{earn} CHICKENS"
                    self.msg_timer = 2.0
                    return

            self.message = "Surface: E at a job stall to work, or at EXIT to return."
            self.msg_timer = 1.8
            return

        # Manual pickup: press E near loot.
        if self._try_pickup_nearby_loot():
            return

        # Trade booth
        for bx in self.trade_booths:
            if abs(self.player_x - bx) < 50:
                if self.phase != "day":
                    self.message = "Trade booths are closed at night."
                    self.msg_timer = 2.0
                    return
                sold = self.sell_selected_item()
                if sold:
                    return
                # Day work option even without sell loot.
                earn = random.randint(8, 15) + (self.subway_level - 1) * 2
                self.chickens += earn
                self.message = f"Day shift at trade booth: +{earn} CHICKENS"
                self.msg_timer = 2.3
                return

        # Surface exit
        if abs(self.player_x - self.surface_exit_x) < 60:
            if self.phase != "day":
                self.message = "Surface gate opens during the day only."
                self.msg_timer = 2.0
                return
            self.on_surface = True
            self.enemies.clear()
            self.player_x = self.surface_return_x + 70
            self.player_y = FLOOR_Y - 26
            self.message = "Reached the surface. Work stalls can earn CHICKENS."
            self.msg_timer = 2.8
            return

        # Transfer train: first boarding unlocks navigation, and each boarding rerolls to a better subway map.
        if abs(self.player_x - self.first_train_x) < 55:
            cost = self.get_transfer_train_cost()
            if self.chickens >= cost:
                self.chickens -= cost
                if not self.has_bought_first_train:
                    self.has_bought_first_train = True
                    self.nav_unlocked = True
                self.reroll_subway_map(from_train=True)
            else:
                need = cost - self.chickens
                self.message = f"Transfer train costs {cost} CHICKENS. Need {need} more."
                self.msg_timer = 2.8
            return

        # Dream Island train
        if self.has_bought_first_train and self.dream_train_available and abs(self.player_x - self.dream_train_x) < 60:
            dream_cost = self.get_dream_train_cost()
            if self.chickens >= dream_cost:
                self.chickens -= dream_cost
                self.won = True
                self.message = "You bought the Dream Island train ticket and escaped the subway!"
                self.msg_timer = 999
            else:
                need = dream_cost - self.chickens
                self.message = f"Dream Island train costs {dream_cost} CHICKENS. Need {need} more."
                self.msg_timer = 3.0
            return

        self.message = "Nothing to interact with here."
        self.msg_timer = 1.2

    def _try_pickup_nearby_loot(self) -> bool:
        nearest_idx = -1
        nearest_dist = 999999.0
        for i, drop in enumerate(self.loot):
            dx = drop.x - self.player_x
            dy = drop.y - self.player_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 55 and dist < nearest_dist:
                nearest_idx = i
                nearest_dist = dist

        if nearest_idx == -1:
            return False

        if len(self.inventory) >= 5:
            self.message = "Inventory full (5). Use or sell items first."
            self.msg_timer = 1.8
            return True

        drop = self.loot.pop(nearest_idx)
        self.add_item(drop.item)
        return True

    def use_selected_item(self):
        if self.selected_slot >= len(self.inventory):
            self.message = "Selected slot is empty."
            self.msg_timer = 1.2
            return

        item = self.inventory[self.selected_slot]
        used = False

        if item.kind == "sanity":
            old = self.player_sanity
            self.player_sanity = min(PLAYER_MAX_SANITY, self.player_sanity + item.value)
            gain = int(self.player_sanity - old)
            self.message = f"Used {item.name}: +{gain} sanity"
            used = True
        elif item.kind == "heal":
            old = self.player_hp
            self.player_hp = min(PLAYER_MAX_HP, self.player_hp + item.value)
            gain = int(self.player_hp - old)
            self.message = f"Used {item.name}: +{gain} HP"
            used = True
        elif item.kind == "sell":
            self.message = "This item earns CHICKENS at a trade booth (press E there)."
            self.msg_timer = 2.0
            return

        if used:
            self.inventory.pop(self.selected_slot)
            if self.selected_slot >= len(self.inventory):
                self.selected_slot = max(0, len(self.inventory) - 1)
            self.msg_timer = 1.8

    def sell_selected_item(self) -> bool:
        if self.selected_slot >= len(self.inventory):
            return False
        item = self.inventory[self.selected_slot]
        if item.kind != "sell":
            return False

        payout = item.value + (self.subway_level - 1) * 2
        self.chickens += payout
        self.inventory.pop(self.selected_slot)
        if self.selected_slot >= len(self.inventory):
            self.selected_slot = max(0, len(self.inventory) - 1)
        self.message = f"Sold {item.name} for {payout} CHICKENS."
        self.msg_timer = 1.9
        return True

    # ---------- Loot ----------
    def roll_loot(self) -> Item:
        r = random.random()
        if r < 0.35:
            return Item("Scrap Bolt", "sell", random.randint(7, 12))
        if r < 0.55:
            return Item("Battery Core", "sell", random.randint(14, 24))
        if r < 0.74:
            return Item("Snack Pack", "sanity", random.randint(14, 24))
        if r < 0.90:
            return Item("First Aid Kit", "heal", random.randint(16, 28))
        return Item("Golden Token", "sell", random.randint(35, 60))

    def add_item(self, item: Item):
        if len(self.inventory) >= 5:
            self.message = "Inventory full (5). Use items or sell at a booth."
            self.msg_timer = 1.8
            return
        self.inventory.append(item)
        self.message = f"Picked up {item.name}."
        self.msg_timer = 1.0

    # ---------- Draw ----------
    def draw(self):
        bg = C_BG_DAY if self.phase == "day" else C_BG_NIGHT
        self.screen.fill(bg)

        self.draw_world()
        self.draw_hud()

        if self.player_hp <= 0 or self.player_sanity <= 0:
            self.draw_game_over_overlay()
        elif self.won:
            self.draw_win_overlay()

        pygame.display.flip()

    def draw_world(self):
        if self.on_surface:
            self.draw_surface_world()
            return

        # Ambient
        if self.phase == "night":
            for _ in range(18):
                x = random.randint(0, SCREEN_W)
                y = random.randint(0, 160)
                self.screen.set_at((x, y), (200, 200, 255))

        # Platform and tracks
        platform_rect = pygame.Rect(0, FLOOR_Y, SCREEN_W, SCREEN_H - FLOOR_Y)
        pygame.draw.rect(self.screen, C_PLATFORM, platform_rect)

        track_y = FLOOR_Y + 30
        pygame.draw.rect(self.screen, C_TRACK, (0, track_y, SCREEN_W, 80))
        pygame.draw.line(self.screen, C_RAIL, (0, track_y + 14), (SCREEN_W, track_y + 14), 3)
        pygame.draw.line(self.screen, C_RAIL, (0, track_y + 60), (SCREEN_W, track_y + 60), 3)

        # Lamp posts
        for lp in self.safe_light_posts:
            sx = int(lp - self.cam_x)
            if -60 <= sx <= SCREEN_W + 60:
                pygame.draw.rect(self.screen, (110, 110, 125), (sx - 3, FLOOR_Y - 80, 6, 80))
                lamp_col = (230, 220, 140) if self.phase == "night" else (180, 180, 180)
                pygame.draw.circle(self.screen, lamp_col, (sx, FLOOR_Y - 84), 8)
                if self.phase == "night":
                    glow = pygame.Surface((170, 70), pygame.SRCALPHA)
                    pygame.draw.ellipse(glow, (255, 225, 120, 46), (0, 0, 170, 70))
                    self.screen.blit(glow, (sx - 85, FLOOR_Y - 58))

        # Trade booths
        for bx in self.trade_booths:
            sx = int(bx - self.cam_x)
            if -120 <= sx <= SCREEN_W + 120:
                pygame.draw.rect(self.screen, (65, 86, 98), (sx - 34, FLOOR_Y - 54, 68, 54), border_radius=6)
                txt = self.font_tiny.render("DAY TRADE", True, C_WHITE)
                self.screen.blit(txt, (sx - txt.get_width() // 2, FLOOR_Y - 42))
                tip = self.font_tiny.render("E", True, C_YELLOW)
                self.screen.blit(tip, (sx - 4, FLOOR_Y - 22))

        # Surface exit gate
        sx = int(self.surface_exit_x - self.cam_x)
        if -140 <= sx <= SCREEN_W + 140:
            pygame.draw.rect(self.screen, (90, 140, 165), (sx - 30, FLOOR_Y - 110, 60, 110), border_radius=8)
            ex = self.font_tiny.render("SURFACE EXIT", True, C_WHITE)
            self.screen.blit(ex, (sx - ex.get_width() // 2, FLOOR_Y - 124))
            key = self.font_tiny.render("E", True, C_YELLOW)
            self.screen.blit(key, (sx - 4, FLOOR_Y - 22))

        # Trains / stations
        transfer_cost = self.get_transfer_train_cost()
        self.draw_train(self.first_train_x, "Transfer Train", transfer_cost, locked=not self.has_bought_first_train)
        if self.dream_train_available or self.won:
            self.draw_train(self.dream_train_x, "Dream Island", self.get_dream_train_cost(), locked=not self.won)

        # Stuck gate before first train unlock
        if not self.nav_unlocked:
            gate_x = int(720 - self.cam_x)
            pygame.draw.rect(self.screen, (140, 60, 70), (gate_x - 8, FLOOR_Y - 180, 16, 180))
            lock_txt = self.font_tiny.render("STUCK AREA END", True, C_RED)
            self.screen.blit(lock_txt, (gate_x - lock_txt.get_width() // 2, FLOOR_Y - 200))

        # Loot
        for drop in self.loot:
            sx = int(drop.x - self.cam_x)
            sy = int(drop.y)
            if -30 <= sx <= SCREEN_W + 30:
                color = C_CYAN if drop.item.kind == "sanity" else C_GREEN if drop.item.kind == "heal" else C_ORANGE
                pygame.draw.circle(self.screen, color, (sx, sy), 8)
                pygame.draw.circle(self.screen, C_WHITE, (sx - 2, sy - 2), 2)

        # Enemies
        for enemy in self.enemies:
            sx = int(enemy.x - self.cam_x)
            sy = int(enemy.y)
            if -40 <= sx <= SCREEN_W + 40:
                pygame.draw.ellipse(self.screen, (120, 55, 150), (sx - 16, sy - 20, 32, 22))
                pygame.draw.circle(self.screen, (230, 70, 90), (sx - 5, sy - 14), 3)
                pygame.draw.circle(self.screen, (230, 70, 90), (sx + 5, sy - 14), 3)

        # Player
        px = int(self.player_x - self.cam_x)
        py = int(self.player_y)
        pygame.draw.ellipse(self.screen, (95, 180, 240), (px - 14, py - 20, 28, 20))
        pygame.draw.circle(self.screen, (95, 180, 240), (px, py - 24), 10)
        pygame.draw.circle(self.screen, (20, 20, 20), (px - 4, py - 25), 2)
        pygame.draw.circle(self.screen, (20, 20, 20), (px + 4, py - 25), 2)

    def draw_train(self, world_x: float, label: str, cost: int, locked: bool):
        sx = int(world_x - self.cam_x)
        if sx < -260 or sx > SCREEN_W + 260:
            return

        body = pygame.Rect(sx - 115, FLOOR_Y - 110, 230, 90)
        col = (52, 88, 125) if "Dream" not in label else (80, 65, 130)
        pygame.draw.rect(self.screen, col, body, border_radius=10)
        pygame.draw.rect(self.screen, (210, 220, 235), body, 2, border_radius=10)

        for i in range(3):
            wx = sx - 78 + i * 56
            pygame.draw.rect(self.screen, (30, 45, 65), (wx, FLOOR_Y - 94, 38, 26), border_radius=4)

        name = self.font_tiny.render(label, True, C_WHITE)
        self.screen.blit(name, (sx - name.get_width() // 2, FLOOR_Y - 122))

        price_col = C_GREEN if self.chickens >= cost and locked else C_YELLOW
        if label == "Transfer Train" and self.has_bought_first_train:
            cost_text = self.font_tiny.render(f"Ride: {cost} CHICKENS", True, C_GREEN if self.chickens >= cost else C_YELLOW)
        elif label == "Dream Island" and self.won:
            cost_text = self.font_tiny.render("BOARDED", True, C_GREEN)
        else:
            cost_text = self.font_tiny.render(f"Cost: {cost} CHICKENS", True, price_col)
        self.screen.blit(cost_text, (sx - cost_text.get_width() // 2, FLOOR_Y - 10))

        key = self.font_tiny.render("Press E", True, C_WHITE)
        self.screen.blit(key, (sx - key.get_width() // 2, FLOOR_Y + 8))

    def draw_surface_world(self):
        self.screen.fill((44, 70, 102))

        # Simple skyline
        for i in range(8):
            bx = i * 160 - int(self.cam_x * 0.15) % 180
            bh = 90 + (i % 4) * 25
            pygame.draw.rect(self.screen, (58, 78, 96), (bx, FLOOR_Y - bh - 70, 120, bh))

        pygame.draw.rect(self.screen, (84, 88, 76), (0, FLOOR_Y, SCREEN_W, SCREEN_H - FLOOR_Y))

        # Return gate
        rx = int(self.surface_return_x - self.cam_x)
        pygame.draw.rect(self.screen, (72, 112, 140), (rx - 28, FLOOR_Y - 102, 56, 102), border_radius=7)
        rtxt = self.font_tiny.render("EXIT TO SUBWAY", True, C_WHITE)
        self.screen.blit(rtxt, (rx - rtxt.get_width() // 2, FLOOR_Y - 118))

        # Work stalls
        for spot in self.surface_work_spots:
            sx = int(spot - self.cam_x)
            pygame.draw.rect(self.screen, (112, 84, 62), (sx - 32, FLOOR_Y - 54, 64, 54), border_radius=5)
            txt = self.font_tiny.render("WORK", True, C_WHITE)
            self.screen.blit(txt, (sx - txt.get_width() // 2, FLOOR_Y - 40))
            tip = self.font_tiny.render("E", True, C_YELLOW)
            self.screen.blit(tip, (sx - 4, FLOOR_Y - 21))

        # Player
        px = int(self.player_x - self.cam_x)
        py = int(self.player_y)
        pygame.draw.ellipse(self.screen, (95, 180, 240), (px - 14, py - 20, 28, 20))
        pygame.draw.circle(self.screen, (95, 180, 240), (px, py - 24), 10)
        pygame.draw.circle(self.screen, (20, 20, 20), (px - 4, py - 25), 2)
        pygame.draw.circle(self.screen, (20, 20, 20), (px + 4, py - 25), 2)

    def draw_hud(self):
        # Top panel
        pygame.draw.rect(self.screen, (8, 8, 12), (8, 8, SCREEN_W - 16, 92), border_radius=8)
        pygame.draw.rect(self.screen, (90, 95, 110), (8, 8, SCREEN_W - 16, 92), 1, border_radius=8)

        hp_txt = self.font_sm.render(f"HP {int(self.player_hp)}/{PLAYER_MAX_HP}", True, C_WHITE)
        sanity_txt = self.font_sm.render(f"SANITY {int(self.player_sanity)}/{PLAYER_MAX_SANITY}", True, C_WHITE)
        money_txt = self.font_sm.render(f"CHICKENS: {self.chickens}", True, C_YELLOW)
        self.screen.blit(hp_txt, (18, 14))
        self.screen.blit(sanity_txt, (18, 40))
        self.screen.blit(money_txt, (18, 66))

        self.draw_meter(150, 18, 220, 16, self.player_hp / PLAYER_MAX_HP, C_RED)
        self.draw_meter(150, 44, 220, 16, self.player_sanity / PLAYER_MAX_SANITY, C_PURPLE)

        phase_col = C_CYAN if self.phase == "day" else C_ORANGE
        phase_txt = self.font_med.render(f"{self.phase.upper()} - {self.phase_timer:04.1f}s", True, phase_col)
        self.screen.blit(phase_txt, (420, 20))

        stuck_txt = "ON SURFACE" if self.on_surface else ("NO LONGER STUCK" if self.nav_unlocked else "STUCK IN SUBWAY")
        stuck_col = C_GREEN if self.nav_unlocked else C_RED
        if self.on_surface:
            stuck_col = C_CYAN
        nav_txt = self.font_sm.render(stuck_txt, True, stuck_col)
        self.screen.blit(nav_txt, (426, 62))

        dream_state = "AVAILABLE" if self.dream_train_available else "RARE (not here now)"
        goal_txt = self.font_sm.render(
            f"Subway {self.subway_level} | Transfer: {self.get_transfer_train_cost()} | Dream: {self.get_dream_train_cost()} ({dream_state})",
            True,
            C_WHITE,
        )
        self.screen.blit(goal_txt, (690, 20))

        # Inventory bar
        inv_x = 690
        inv_y = 50
        for i in range(5):
            x = inv_x + i * 78
            rect = pygame.Rect(x, inv_y, 72, 42)
            selected = i == self.selected_slot
            pygame.draw.rect(self.screen, (28, 28, 38), rect, border_radius=6)
            pygame.draw.rect(self.screen, C_YELLOW if selected else C_GRAY, rect, 2, border_radius=6)

            slot_key = self.font_tiny.render(str(i + 1), True, C_GRAY)
            self.screen.blit(slot_key, (x + 3, inv_y + 2))
            if i < len(self.inventory):
                item = self.inventory[i]
                label = item.name[:11]
                t = self.font_tiny.render(label, True, C_WHITE)
                self.screen.blit(t, (x + 8, inv_y + 14))

        if self.msg_timer > 0:
            msg = self.font_sm.render(self.message, True, C_WHITE)
            pygame.draw.rect(self.screen, (0, 0, 0), (10, SCREEN_H - 40, SCREEN_W - 20, 30), border_radius=6)
            self.screen.blit(msg, (18, SCREEN_H - 33))

        controls = self.font_tiny.render("WASD move | E interact/work | F use item | 1-5 slots | Day trade/work, night loot", True, C_GRAY)
        self.screen.blit(controls, (14, SCREEN_H - 18))

    def draw_meter(self, x: int, y: int, w: int, h: int, ratio: float, color: Tuple[int, int, int]):
        ratio = max(0.0, min(1.0, ratio))
        pygame.draw.rect(self.screen, (24, 24, 28), (x, y, w, h), border_radius=4)
        pygame.draw.rect(self.screen, color, (x, y, int(w * ratio), h), border_radius=4)
        pygame.draw.rect(self.screen, (120, 120, 140), (x, y, w, h), 1, border_radius=4)

    def draw_game_over_overlay(self):
        s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        self.screen.blit(s, (0, 0))
        t1 = self.font_big.render("YOU WERE LOST IN THE SUBWAY", True, C_RED)
        t2 = self.font_med.render("Survive longer nights, keep sanity up, and gather CHICKENS.", True, C_WHITE)
        self.screen.blit(t1, (SCREEN_W // 2 - t1.get_width() // 2, 280))
        self.screen.blit(t2, (SCREEN_W // 2 - t2.get_width() // 2, 336))

    def draw_win_overlay(self):
        s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        s.fill((15, 10, 30, 155))
        self.screen.blit(s, (0, 0))
        t1 = self.font_big.render("DREAM ISLAND TRAIN BOARDED", True, C_YELLOW)
        t2 = self.font_med.render("You escaped the subway. You made it.", True, C_WHITE)
        self.screen.blit(t1, (SCREEN_W // 2 - t1.get_width() // 2, 276))
        self.screen.blit(t2, (SCREEN_W // 2 - t2.get_width() // 2, 332))


def main():
    game = SubwayDreamIsland()
    game.run()


if __name__ == "__main__":
    main()
