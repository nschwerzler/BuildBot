"""
Broadcast Tower 13 Survival (2.5D prototype)

Core loop:
- Climb floors for supplies and signal fragments.
- Survive pressure from scary non-demonic enemies.
- Return to base level to recover and redeploy.

Controls:
- WASD / Arrow Keys: Move
- E: Interact (loot, relay stabilize, lift travel, shop)
- F: Toggle flashlight
- R: Restart (after collapse)
- ESC: Quit

Tip:
- At lift console, press E while holding S/Down to go down a floor; otherwise go up.

Carry Rules:
- You can carry 4 small items.
- At the lift console, entering the lift deposits carried items.
"""

import math
import random
from dataclasses import dataclass
from typing import List, Tuple

import pygame

SCREEN_W, SCREEN_H = 1200, 720
FPS = 60
WORLD_W = 2200
FLOOR_Y = 618
MAX_FLOOR = 12

PLAYER_SPEED = 265
INTERACT_RANGE = 58
RUN_TIME_LIMIT = 14 * 60
MAP_SEGMENTS = 20
SAFE_SHOP_RADIUS = 92

C_BG = (11, 12, 18)
C_PLATFORM = (45, 50, 61)
C_TRACK = (27, 24, 30)
C_WHITE = (235, 235, 240)
C_GRAY = (165, 165, 178)
C_YELLOW = (236, 210, 95)
C_CYAN = (92, 205, 220)
C_GREEN = (85, 210, 130)
C_RED = (225, 86, 98)
C_PURPLE = (160, 105, 220)
C_ORANGE = (238, 153, 84)


@dataclass
class Loot:
    x: float
    y: float
    kind: str  # credits, battery, calm, signal, med
    value: int


@dataclass
class SignalRelay:
    x: float
    y: float
    strength: float


@dataclass
class Wraith:
    x: float
    y: float
    speed: float
    kind: str
    hit_cd: float = 0.0


@dataclass
class CarryItem:
    kind: str
    value: int


@dataclass
class MallShop:
    x: float
    y: float
    is_abandoned: bool
    used: bool = False


@dataclass
class MazeWall:
    x: float
    y: float
    w: float
    h: float


class BroadcastTower13Survival:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Broadcast Tower 13 Survival")
        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont("Arial", 40, bold=True)
        self.font_med = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_sm = pygame.font.SysFont("Arial", 18)
        self.font_tiny = pygame.font.SysFont("Consolas", 15)

        self.running = True
        self.game_over = False

        self.player_x = 280.0
        self.player_y = FLOOR_Y - 24
        self.cam_x = 0.0

        self.max_sanity = 100.0
        self.sanity = 100.0
        self.max_health = 100.0
        self.health = 100.0
        self.max_battery = 100.0
        self.battery = 100.0
        self.flashlight_on = True

        self.credits = 28
        self.signal_noise = 0
        self.time_left = float(RUN_TIME_LIMIT)
        self.extracted_items = 0

        self.current_floor = 0
        self.floor_theme = "Broadcast Base"
        self.floor_risk = 0.0
        self.floor_reward = 0.0

        self.loot: List[Loot] = []
        self.signal_relays: List[SignalRelay] = []
        self.wraiths: List[Wraith] = []
        self.shops: List[MallShop] = []
        self.carried_small: List[CarryItem] = []
        self.walls: List[MazeWall] = []
        self.map_revealed = {floor: set() for floor in range(MAX_FLOOR + 1)}

        self.safe_light_posts = [250, 640, 980, 1320, 1730, 2060]
        self.panel_x = 1030
        self.msg = "Broadcast Tower 13 online. Climb, survive, and extract signal parts."
        self.msg_timer = 8.0

    def get_near_open_shop(self) -> MallShop | None:
        for shop in self.shops:
            if not shop.is_abandoned and math.hypot(shop.x - self.player_x, shop.y - self.player_y) < SAFE_SHOP_RADIUS:
                return shop
        return None

    def buy_shop_item(self, item_slot: int) -> bool:
        if item_slot == 1:
            name, cost = "Battery Pack", 18
            if self.credits < cost:
                self.msg = f"Need {cost} credits for {name}."
                self.msg_timer = 1.4
                return False
            self.credits -= cost
            self.battery = min(self.max_battery, self.battery + 35)
            self.msg = f"Bought {name}: +35 battery (-{cost} cr)."
        elif item_slot == 2:
            name, cost = "Calm Tonic", 16
            if self.credits < cost:
                self.msg = f"Need {cost} credits for {name}."
                self.msg_timer = 1.4
                return False
            self.credits -= cost
            self.sanity = min(self.max_sanity, self.sanity + 22)
            self.msg = f"Bought {name}: +22 sanity (-{cost} cr)."
        elif item_slot == 3:
            name, cost = "Ward Charm", 24
            if self.credits < cost:
                self.msg = f"Need {cost} credits for {name}."
                self.msg_timer = 1.4
                return False
            self.credits -= cost
            self.floor_risk = max(0.2, self.floor_risk - 1.0)
            self.msg = f"Bought {name}: floor risk reduced (-{cost} cr)."
        elif item_slot == 4:
            name, cost = "Time Snack", 20
            if self.credits < cost:
                self.msg = f"Need {cost} credits for {name}."
                self.msg_timer = 1.4
                return False
            self.credits -= cost
            self.time_left = min(RUN_TIME_LIMIT + 300, self.time_left + 45)
            self.msg = f"Bought {name}: +45s (-{cost} cr)."
        elif item_slot == 5:
            name, cost = "Med Patch", 22
            if self.credits < cost:
                self.msg = f"Need {cost} credits for {name}."
                self.msg_timer = 1.4
                return False
            self.credits -= cost
            self.health = min(self.max_health, self.health + 28)
            self.msg = f"Bought {name}: +28 health (-{cost} cr)."
        else:
            self.msg = "Shop: hold 1 Battery, 2 Calm, 3 Ward, 4 Time, 5 Med and press E."
            self.msg_timer = 1.8
            return False

        self.msg_timer = 1.8
        return True

    def reset_run(self):
        self.game_over = False
        self.player_x = 280.0
        self.player_y = FLOOR_Y - 24
        self.sanity = self.max_sanity
        self.health = self.max_health
        self.battery = self.max_battery
        self.flashlight_on = True
        self.credits = 28
        self.signal_noise = 0
        self.time_left = float(RUN_TIME_LIMIT)
        self.extracted_items = 0
        self.current_floor = 0
        self.floor_theme = "Broadcast Base"
        self.floor_risk = 0.0
        self.floor_reward = 0.0
        self.loot.clear()
        self.signal_relays.clear()
        self.wraiths.clear()
        self.shops.clear()
        self.carried_small.clear()
        self.walls.clear()
        self.map_revealed = {floor: set() for floor in range(MAX_FLOOR + 1)}
        self.msg = "New shift started. Keep the signal alive."
        self.msg_timer = 4.0

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
                elif event.key == pygame.K_r:
                    if self.game_over:
                        self.reset_run()
                elif event.key == pygame.K_f and not self.game_over:
                    self.flashlight_on = not self.flashlight_on
                    self.msg = "Flashlight ON" if self.flashlight_on else "Flashlight OFF"
                    self.msg_timer = 1.0
                elif event.key == pygame.K_e and not self.game_over:
                    self.try_interact()

    def update(self, dt: float):
        if self.game_over:
            self.msg_timer = max(0.0, self.msg_timer - dt)
            return

        self.update_player(dt)
        self.update_survival_systems(dt)
        self.update_timer(dt)
        self.reveal_nearby_map()
        self.update_camera(dt)
        self.msg_timer = max(0.0, self.msg_timer - dt)

        if self.sanity <= 0:
            self.sanity = 0
            self.game_over = True
            self.msg = "You collapsed from fear. Press R to restart."
            self.msg_timer = 999
        elif self.health <= 0:
            self.health = 0
            self.game_over = True
            self.msg = "You didn\'t survive the tower. Press R to restart."
            self.msg_timer = 999
        elif self.time_left <= 0:
            self.time_left = 0
            self.game_over = True
            self.msg = "Time is up. The tower sealed. Press R to restart."
            self.msg_timer = 999

    def update_player(self, dt: float):
        keys = pygame.key.get_pressed()
        dx, dy = 0.0, 0.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1

        if dx != 0 or dy != 0:
            mag = math.sqrt(dx * dx + dy * dy)
            dx /= mag
            dy /= mag

        old_x, old_y = self.player_x, self.player_y
        self.player_x += dx * PLAYER_SPEED * dt
        self.player_y += dy * PLAYER_SPEED * dt

        self.player_x = max(90, min(WORLD_W - 90, self.player_x))
        self.player_y = max(FLOOR_Y - 180, min(FLOOR_Y - 18, self.player_y))

        if self.current_floor > 0 and self.collides_with_walls(self.player_x, self.player_y):
            # simple resolution for maze-like movement
            self.player_x = old_x
            if self.current_floor > 0 and self.collides_with_walls(self.player_x, self.player_y):
                self.player_y = old_y

    def collides_with_walls(self, x: float, y: float) -> bool:
        player_rect = pygame.Rect(int(x - 12), int(y - 26), 24, 26)
        for wall in self.walls:
            wall_rect = pygame.Rect(int(wall.x), int(wall.y), int(wall.w), int(wall.h))
            if player_rect.colliderect(wall_rect):
                return True
        return False

    def update_timer(self, dt: float):
        self.time_left = max(0.0, self.time_left - dt)

    def reveal_nearby_map(self):
        segment_w = WORLD_W / MAP_SEGMENTS
        idx = int(self.player_x / segment_w)
        idx = max(0, min(MAP_SEGMENTS - 1, idx))
        floor_map = self.map_revealed[self.current_floor]
        for seg in range(idx - 1, idx + 2):
            if 0 <= seg < MAP_SEGMENTS:
                floor_map.add(seg)

    def update_survival_systems(self, dt: float):
        near_light = min(abs(self.player_x - lp) for lp in self.safe_light_posts) < 82
        near_open_shop = self.get_near_open_shop() is not None

        if self.current_floor == 0:
            self.sanity = min(self.max_sanity, self.sanity + 3.2 * dt)
            self.battery = min(self.max_battery, self.battery + 5.6 * dt)
            return

        floor_intensity = 1.0 + self.current_floor * 0.14 + self.signal_noise * 0.08

        # Base sanity pressure on active floors.
        drain = (0.8 + self.floor_risk * 0.18) * floor_intensity
        if near_light:
            drain *= 0.40
        if near_open_shop:
            drain = 0.0
        self.sanity = max(0.0, self.sanity - drain * dt)
        if near_open_shop:
            self.sanity = min(self.max_sanity, self.sanity + 3.8 * dt)
            self.battery = min(self.max_battery, self.battery + 2.4 * dt)
            self.health = min(self.max_health, self.health + 1.2 * dt)

        # Flashlight battery.
        if self.flashlight_on:
            self.battery = max(0.0, self.battery - (2.3 + self.floor_risk * 0.2) * dt)
            if self.battery <= 0:
                self.flashlight_on = False
                self.msg = "Battery depleted."
                self.msg_timer = 1.5

        # Survival pressure: if you stay in dark zones with low battery, health suffers.
        if not near_open_shop and self.battery < 12:
            exposure = (0.55 + self.current_floor * 0.04) * dt
            self.health = max(0.0, self.health - exposure)

        # Wraith movement / touch damage.
        for w in self.wraiths:
            direction = 1 if self.player_x > w.x else -1
            speed = w.speed
            if w.kind == "mannequin":
                if self.flashlight_on and abs(self.player_x - w.x) < 185:
                    speed *= 0.10
                else:
                    speed *= 0.95
            elif w.kind == "crawler":
                speed *= 1.25 if not self.flashlight_on else 0.90
            else:  # whisperer
                speed *= 1.12 if abs(self.player_x - w.x) > 150 else 0.86
            if near_open_shop:
                speed *= 0.34
            w.x += direction * speed * dt
            w.hit_cd = max(0.0, w.hit_cd - dt)

            if not near_open_shop and abs(w.x - self.player_x) < 26 and w.hit_cd <= 0:
                w.hit_cd = 1.0
                sanity_hit = random.uniform(3.6, 6.6) * (0.65 if self.flashlight_on else 1.0)
                if w.kind == "crawler":
                    health_hit = random.uniform(5.4, 8.2)
                    label = "Crawler"
                elif w.kind == "mannequin":
                    health_hit = random.uniform(3.8, 6.0)
                    sanity_hit *= 1.35
                    label = "Mannequin"
                else:
                    health_hit = random.uniform(4.2, 6.6)
                    sanity_hit *= 1.15
                    label = "Whisperer"
                self.health = max(0.0, self.health - health_hit)
                self.sanity = max(0.0, self.sanity - sanity_hit)
                self.msg = f"{label} strike: -{health_hit:.1f} HP, -{sanity_hit:.1f} sanity"
                self.msg_timer = 1.2

        # Keep entities in world.
        self.wraiths = [w for w in self.wraiths if -20 < w.x < WORLD_W + 20]

    def try_interact(self):
        # Shop interaction
        for shop in self.shops:
            if math.hypot(shop.x - self.player_x, shop.y - self.player_y) < INTERACT_RANGE:
                if shop.is_abandoned:
                    if shop.used:
                        self.msg = "This abandoned shop has already been scavenged."
                        self.msg_timer = 1.4
                        return
                    shop.used = True
                    self.sanity = max(0.0, self.sanity - 3.0)
                    if len(self.carried_small) < 4:
                        salvage_kind = random.choice(["credits", "battery", "calm", "signal", "med"])
                        if salvage_kind == "credits":
                            value = random.randint(12 + self.current_floor, 22 + self.current_floor * 2)
                        elif salvage_kind == "battery":
                            value = random.randint(12, 22)
                        elif salvage_kind == "calm":
                            value = random.randint(10, 18)
                        elif salvage_kind == "med":
                            value = random.randint(12, 20)
                        else:
                            value = 1
                        self.carried_small.append(CarryItem(kind=salvage_kind, value=value))
                        self.msg = f"Scavenged abandoned room: {salvage_kind} item"
                    else:
                        gain = random.randint(18, 32)
                        self.credits += gain
                        self.msg = f"Abandoned room stash sold instantly: +{gain} credits"
                    self.msg_timer = 2.0
                    return

                # Open (not abandoned) shop is a safe zone with item purchases.
                keys = pygame.key.get_pressed()
                if keys[pygame.K_1]:
                    self.buy_shop_item(1)
                elif keys[pygame.K_2]:
                    self.buy_shop_item(2)
                elif keys[pygame.K_3]:
                    self.buy_shop_item(3)
                elif keys[pygame.K_4]:
                    self.buy_shop_item(4)
                elif keys[pygame.K_5]:
                    self.buy_shop_item(5)
                else:
                    self.buy_shop_item(0)
                return

        # Loot pickup
        for i, item in enumerate(self.loot):
            if math.hypot(item.x - self.player_x, item.y - self.player_y) < INTERACT_RANGE:
                if len(self.carried_small) >= 4:
                    self.msg = "Small-item capacity full (4)."
                    self.msg_timer = 1.6
                    return
                self.carried_small.append(CarryItem(kind=item.kind, value=item.value))
                self.msg = f"Picked {item.kind} item ({item.value})"
                self.msg_timer = 1.8
                self.loot.pop(i)
                return

        # Stabilize signal relay
        for i, node in enumerate(self.signal_relays):
            if math.hypot(node.x - self.player_x, node.y - self.player_y) < INTERACT_RANGE:
                payout = int(9 + node.strength * 4 + self.current_floor * 2)
                self.credits += payout
                self.sanity = min(self.max_sanity, self.sanity + 3)
                self.msg = f"Relay stabilized +{payout} credits"
                self.msg_timer = 1.8
                self.signal_relays.pop(i)
                return

        # Lift console travel
        if abs(self.player_x - self.panel_x) < INTERACT_RANGE:
            # Entering lift deposits carried items.
            deposited = self.deposit_carried_items()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                target = self.current_floor + 1
            elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
                target = self.current_floor - 1
            else:
                target = 0  # Lift defaults to BASE return.
            target = max(0, min(MAX_FLOOR, target))
            if target == self.current_floor:
                if not deposited:
                    self.msg = "No floor change."
                self.msg_timer = 1.0
                return
            self.travel_to_floor(target)
            return

        self.msg = "Nothing to interact with."
        self.msg_timer = 1.0

    def deposit_carried_items(self) -> bool:
        if not self.carried_small:
            return False

        credits_gain = 0
        sanity_gain = 0
        battery_gain = 0
        time_gain = 0
        signal_gain = 0
        count = 0

        for item in self.carried_small:
            count += 1
            time_gain += 6
            if item.kind == "credits":
                credits_gain += item.value
            elif item.kind == "battery":
                credits_gain += item.value // 2
                battery_gain += item.value
            elif item.kind == "calm":
                credits_gain += item.value // 2
                sanity_gain += item.value
            elif item.kind == "signal":
                credits_gain += max(6, item.value * 8)
                signal_gain += 1
            elif item.kind == "med":
                credits_gain += item.value // 2
                self.health = min(self.max_health, self.health + item.value)

        self.credits += credits_gain
        self.sanity = min(self.max_sanity, self.sanity + sanity_gain)
        self.battery = min(self.max_battery, self.battery + battery_gain)
        self.time_left = min(RUN_TIME_LIMIT + 180, self.time_left + time_gain)
        self.signal_noise += signal_gain
        self.extracted_items += count

        self.carried_small.clear()

        self.msg = f"Deposited {count} items | +{credits_gain} cr, +{time_gain}s"
        self.msg_timer = 2.2
        return True

    def travel_to_floor(self, floor: int):
        self.current_floor = floor
        self.player_x = 260.0
        self.player_y = FLOOR_Y - 24
        self.reveal_nearby_map()

        if floor == 0:
            self.floor_theme = "Broadcast Base"
            self.floor_risk = 0
            self.floor_reward = 0
            self.loot.clear()
            self.signal_relays.clear()
            self.wraiths.clear()
            self.shops.clear()
            self.walls.clear()
            self.msg = "Back at base. Recover, regroup, and redeploy."
            self.msg_timer = 2.4
            return

        themes = [
            "Relay Hall East",
            "Signal Archive",
            "Maintenance Corridor",
            "Broadcast Gallery",
            "Tower Annex",
            "Control Wing",
            "Service Ducts",
        ]
        self.floor_theme = random.choice(themes)

        self.floor_risk = 1.0 + floor * 0.95 + self.signal_noise * 0.5
        self.floor_reward = 16 + floor * 10

        self.loot.clear()
        self.signal_relays.clear()
        self.wraiths.clear()
        self.shops.clear()
        self.walls.clear()

        loot_count = 5 + floor // 2
        node_count = 2 + floor // 3
        wraith_count = 1 + floor // 4
        shop_count = 3 + floor // 4

        for _ in range(loot_count):
            kind_roll = random.random()
            x = random.uniform(320, WORLD_W - 120)
            y = random.uniform(FLOOR_Y - 120, FLOOR_Y - 8)
            if kind_roll < 0.46:
                self.loot.append(Loot(x, y, "credits", random.randint(8 + floor, 16 + floor * 2)))
            elif kind_roll < 0.68:
                self.loot.append(Loot(x, y, "battery", random.randint(10, 20)))
            elif kind_roll < 0.87:
                self.loot.append(Loot(x, y, "calm", random.randint(8, 16)))
            elif kind_roll < 0.96:
                self.loot.append(Loot(x, y, "med", random.randint(12, 20)))
            else:
                self.loot.append(Loot(x, y, "signal", 1))

        for _ in range(node_count):
            x = random.uniform(420, WORLD_W - 180)
            self.signal_relays.append(SignalRelay(x, FLOOR_Y - 24, 1.0 + floor * 0.2))

        for _ in range(wraith_count):
            x = random.uniform(520, WORLD_W - 160)
            enemy_kind = random.choice(["crawler", "mannequin", "whisperer"])
            base_speed = 76 + floor * 8 + random.random() * 12
            if enemy_kind == "crawler":
                base_speed += 16
            elif enemy_kind == "mannequin":
                base_speed -= 6
            self.wraiths.append(Wraith(x=x, y=FLOOR_Y - 20, speed=base_speed, kind=enemy_kind))

        # Hallway maze: alternating divider walls with pass-through gaps.
        hall_top = FLOOR_Y - 176
        hall_bottom = FLOOR_Y - 36
        divider_w = 18
        gap_h = 56
        section_w = 165
        section_xs = list(range(420, WORLD_W - 230, section_w))

        for i, x in enumerate(section_xs):
            gap_center = FLOOR_Y - (96 if i % 2 == 0 else 136)
            gap_top = gap_center - gap_h * 0.5
            gap_bottom = gap_center + gap_h * 0.5

            upper_h = max(0.0, gap_top - hall_top)
            lower_h = max(0.0, hall_bottom - gap_bottom)
            if upper_h > 14:
                self.walls.append(MazeWall(x=x, y=hall_top, w=divider_w, h=upper_h))
            if lower_h > 14:
                self.walls.append(MazeWall(x=x, y=gap_bottom, w=divider_w, h=lower_h))

        # Shop rooms (alcoves) connected to the hallway.
        room_centers = section_xs[1::2]
        random.shuffle(room_centers)
        room_centers = sorted(room_centers[: min(shop_count, len(room_centers))])
        room_w = 130
        room_h = 72
        room_top = hall_top - 68
        door_w = 42

        for cx in room_centers:
            left = cx - room_w * 0.5
            right = cx + room_w * 0.5
            bottom = room_top + room_h
            door_left = cx - door_w * 0.5
            door_right = cx + door_w * 0.5

            # Room walls (bottom has doorway opening into hallway).
            self.walls.append(MazeWall(x=left, y=room_top, w=10, h=room_h))
            self.walls.append(MazeWall(x=right - 10, y=room_top, w=10, h=room_h))
            self.walls.append(MazeWall(x=left, y=room_top, w=room_w, h=10))
            self.walls.append(MazeWall(x=left, y=bottom - 10, w=max(0.0, door_left - left), h=10))
            self.walls.append(MazeWall(x=door_right, y=bottom - 10, w=max(0.0, right - door_right), h=10))

            is_abandoned = random.random() < 0.56
            self.shops.append(MallShop(x=cx, y=room_top + room_h * 0.55, is_abandoned=is_abandoned, used=False))

        self.msg = f"Floor {floor}: {self.floor_theme} (Risk {self.floor_risk:.1f}, Reward {self.floor_reward:.0f}+)."
        self.msg_timer = 3.0

    def update_camera(self, dt: float):
        target = self.player_x - SCREEN_W * 0.5
        target = max(0, min(WORLD_W - SCREEN_W, target))
        self.cam_x += (target - self.cam_x) * min(1.0, dt * 8)

    def draw(self):
        self.screen.fill(C_BG)
        self.draw_world()
        self.draw_hud()
        if self.game_over:
            self.draw_game_over()
        pygame.display.flip()

    def draw_world(self):
        # Sky gradient-ish strips
        for i in range(7):
            shade = 20 + i * 8
            pygame.draw.rect(self.screen, (shade, shade + 2, shade + 10), (0, i * 72, SCREEN_W, 72))

        # 2.5D platform / track base
        pygame.draw.rect(self.screen, C_PLATFORM, (0, FLOOR_Y, SCREEN_W, SCREEN_H - FLOOR_Y))
        pygame.draw.rect(self.screen, C_TRACK, (0, FLOOR_Y + 34, SCREEN_W, 76))
        pygame.draw.line(self.screen, (120, 112, 95), (0, FLOOR_Y + 48), (SCREEN_W, FLOOR_Y + 48), 3)
        pygame.draw.line(self.screen, (120, 112, 95), (0, FLOOR_Y + 88), (SCREEN_W, FLOOR_Y + 88), 3)

        # Light posts
        for lp in self.safe_light_posts:
            sx = int(lp - self.cam_x)
            if -40 <= sx <= SCREEN_W + 40:
                pygame.draw.rect(self.screen, (110, 115, 130), (sx - 3, FLOOR_Y - 82, 6, 82))
                col = (235, 222, 145) if self.flashlight_on else (170, 170, 170)
                pygame.draw.circle(self.screen, col, (sx, FLOOR_Y - 86), 8)

        # Lift console
        sx = int(self.panel_x - self.cam_x)
        pygame.draw.rect(self.screen, (76, 92, 116), (sx - 34, FLOOR_Y - 130, 68, 130), border_radius=8)
        t = self.font_tiny.render("PANEL", True, C_WHITE)
        self.screen.blit(t, (sx - t.get_width() // 2, FLOOR_Y - 118))
        k = self.font_tiny.render("E", True, C_YELLOW)
        self.screen.blit(k, (sx - 4, FLOOR_Y - 18))

        # Shops (abandoned and open)
        for shop in self.shops:
            sx = int(shop.x - self.cam_x)
            sy = int(shop.y)
            if -70 <= sx <= SCREEN_W + 70:
                if shop.is_abandoned:
                    body_col = (74, 62, 72)
                    sign_col = C_PURPLE
                    title = "ABANDONED ROOM"
                else:
                    body_col = (76, 108, 92)
                    sign_col = C_GREEN
                    title = "SAFE SHOP"
                pygame.draw.rect(self.screen, body_col, (sx - 36, sy - 36, 72, 58), border_radius=6)
                pygame.draw.rect(self.screen, (30, 30, 38), (sx - 16, sy - 16, 32, 22), border_radius=4)
                txt = self.font_tiny.render(title, True, sign_col)
                self.screen.blit(txt, (sx - txt.get_width() // 2, sy - 52))
                if shop.is_abandoned and shop.used:
                    used = self.font_tiny.render("LOOTED", True, C_GRAY)
                    self.screen.blit(used, (sx - used.get_width() // 2, sy + 10))
                else:
                    key = self.font_tiny.render("E", True, C_YELLOW)
                    self.screen.blit(key, (sx - 4, sy + 10))
                if not shop.is_abandoned:
                    hint = self.font_tiny.render("1 BAT  2 CALM  3 WARD  4 TIME  5 MED", True, C_GREEN)
                    self.screen.blit(hint, (sx - hint.get_width() // 2, sy - 66))

        # Maze walls
        for wall in self.walls:
            sx = int(wall.x - self.cam_x)
            if sx > SCREEN_W or sx + int(wall.w) < 0:
                continue
            pygame.draw.rect(
                self.screen,
                (78, 82, 98),
                (sx, int(wall.y), int(wall.w), int(wall.h)),
                border_radius=4,
            )
            pygame.draw.rect(
                self.screen,
                (116, 122, 142),
                (sx, int(wall.y), int(wall.w), int(wall.h)),
                1,
                border_radius=4,
            )

        # Loot
        for item in self.loot:
            sx = int(item.x - self.cam_x)
            sy = int(item.y)
            if -20 <= sx <= SCREEN_W + 20:
                color = C_YELLOW
                if item.kind == "battery":
                    color = C_CYAN
                elif item.kind == "calm":
                    color = C_GREEN
                elif item.kind == "signal":
                    color = C_PURPLE
                elif item.kind == "med":
                    color = (238, 108, 108)
                pygame.draw.circle(self.screen, color, (sx, sy), 8)
                pygame.draw.circle(self.screen, C_WHITE, (sx - 2, sy - 2), 2)

        # Signal relays
        for node in self.signal_relays:
            sx = int(node.x - self.cam_x)
            sy = int(node.y)
            if -30 <= sx <= SCREEN_W + 30:
                pygame.draw.ellipse(self.screen, (90, 128, 176), (sx - 14, sy - 18, 28, 18))
                pygame.draw.circle(self.screen, (160, 225, 255), (sx, sy - 12), 3)

        # Scary non-demonic enemies
        for w in self.wraiths:
            sx = int(w.x - self.cam_x)
            sy = int(w.y)
            if -40 <= sx <= SCREEN_W + 40:
                if w.kind == "crawler":
                    pygame.draw.ellipse(self.screen, (95, 112, 138), (sx - 17, sy - 14, 34, 14))
                    pygame.draw.circle(self.screen, (210, 220, 235), (sx - 7, sy - 12), 2)
                    pygame.draw.circle(self.screen, (210, 220, 235), (sx + 7, sy - 12), 2)
                elif w.kind == "mannequin":
                    pygame.draw.rect(self.screen, (188, 194, 200), (sx - 10, sy - 26, 20, 26), border_radius=2)
                    pygame.draw.circle(self.screen, (225, 230, 236), (sx, sy - 30), 8)
                    pygame.draw.circle(self.screen, (28, 28, 30), (sx - 3, sy - 31), 1)
                    pygame.draw.circle(self.screen, (28, 28, 30), (sx + 3, sy - 31), 1)
                else:
                    pygame.draw.ellipse(self.screen, (134, 146, 168), (sx - 16, sy - 22, 32, 20))
                    pygame.draw.circle(self.screen, (188, 210, 235), (sx - 5, sy - 15), 2)
                    pygame.draw.circle(self.screen, (188, 210, 235), (sx + 5, sy - 15), 2)

        # Player
        px = int(self.player_x - self.cam_x)
        py = int(self.player_y)
        pygame.draw.ellipse(self.screen, (102, 185, 245), (px - 14, py - 20, 28, 20))
        pygame.draw.circle(self.screen, (102, 185, 245), (px, py - 24), 10)
        pygame.draw.circle(self.screen, (24, 24, 24), (px - 4, py - 25), 2)
        pygame.draw.circle(self.screen, (24, 24, 24), (px + 4, py - 25), 2)

        # Flashlight cone visualization (simple radius glow)
        if self.flashlight_on and self.battery > 0:
            glow = pygame.Surface((260, 170), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (255, 245, 200, 52), (0, 0, 260, 170))
            self.screen.blit(glow, (px - 130, py - 90))

        # Fog-of-war reveal for dungeon-crawler feel.
        if self.current_floor > 0:
            segment_w = WORLD_W / MAP_SEGMENTS
            revealed = self.map_revealed[self.current_floor]
            for seg in range(MAP_SEGMENTS):
                if seg in revealed:
                    continue
                wx = seg * segment_w
                sx = int(wx - self.cam_x)
                sw = int(segment_w) + 2
                if sx > SCREEN_W or sx + sw < 0:
                    continue
                fog = pygame.Surface((sw, SCREEN_H), pygame.SRCALPHA)
                fog.fill((0, 0, 0, 165))
                self.screen.blit(fog, (sx, 0))

    def draw_meter(self, x: int, y: int, w: int, h: int, ratio: float, col: Tuple[int, int, int]):
        ratio = max(0.0, min(1.0, ratio))
        pygame.draw.rect(self.screen, (22, 22, 28), (x, y, w, h), border_radius=4)
        pygame.draw.rect(self.screen, col, (x, y, int(w * ratio), h), border_radius=4)
        pygame.draw.rect(self.screen, (120, 120, 138), (x, y, w, h), 1, border_radius=4)

    def draw_hud(self):
        pygame.draw.rect(self.screen, (8, 8, 11), (10, 10, SCREEN_W - 20, 102), border_radius=8)
        pygame.draw.rect(self.screen, (90, 96, 112), (10, 10, SCREEN_W - 20, 102), 1, border_radius=8)

        s_txt = self.font_sm.render(f"Sanity {self.sanity:0.0f}/{self.max_sanity:0.0f}", True, C_WHITE)
        h_txt = self.font_sm.render(f"Health {self.health:0.0f}/{self.max_health:0.0f}", True, C_WHITE)
        b_txt = self.font_sm.render(f"Battery {self.battery:0.0f}/{self.max_battery:0.0f}", True, C_WHITE)
        c_txt = self.font_sm.render(f"Credits {self.credits}", True, C_YELLOW)
        signal_txt = self.font_sm.render(f"Signal Fragments {self.signal_noise}", True, C_PURPLE)
        mins = int(self.time_left) // 60
        secs = int(self.time_left) % 60
        time_txt = self.font_sm.render(f"Time {mins:02d}:{secs:02d}", True, C_ORANGE)
        self.screen.blit(s_txt, (24, 20))
        self.screen.blit(h_txt, (24, 48))
        self.screen.blit(b_txt, (24, 66))
        self.screen.blit(c_txt, (24, 76))
        self.screen.blit(signal_txt, (195, 76))
        self.screen.blit(time_txt, (350, 76))

        self.draw_meter(180, 12, 240, 14, self.sanity / self.max_sanity, C_RED)
        self.draw_meter(180, 32, 240, 14, self.health / self.max_health, (226, 118, 112))
        self.draw_meter(180, 52, 240, 14, self.battery / self.max_battery, C_CYAN)

        floor_txt = self.font_med.render(f"Floor {self.current_floor}: {self.floor_theme}", True, C_WHITE)
        rr_txt = self.font_sm.render(f"Risk {self.floor_risk:.1f}   Reward {self.floor_reward:.0f}+", True, C_ORANGE)
        hint_txt = self.font_tiny.render("At PANEL: E = HOME | hold W = up | hold S = down", True, C_GRAY)
        self.screen.blit(floor_txt, (470, 22))
        self.screen.blit(rr_txt, (470, 56))
        self.screen.blit(hint_txt, (470, 84))

        # Carry inventory: 4 small
        inv_txt = self.font_tiny.render(
            f"Carry {len(self.carried_small)}/4 small | Extracted: {self.extracted_items}",
            True,
            C_CYAN,
        )
        self.screen.blit(inv_txt, (830, 22))

        if self.current_floor == 0:
            base_txt = self.font_sm.render("Base zone: faster recovery, no enemy contact.", True, C_GREEN)
            self.screen.blit(base_txt, (760, 56))

        self.draw_mini_map(1030, 88)

        if self.msg_timer > 0:
            pygame.draw.rect(self.screen, (0, 0, 0), (10, SCREEN_H - 40, SCREEN_W - 20, 30), border_radius=6)
            msg = self.font_sm.render(self.msg, True, C_WHITE)
            self.screen.blit(msg, (18, SCREEN_H - 33))

        controls = self.font_tiny.render("WASD move | E interact/deposit | 1-5 hold+E buy at safe shop | F flashlight | R restart | ESC quit", True, C_GRAY)
        self.screen.blit(controls, (12, SCREEN_H - 18))

    def draw_mini_map(self, x: int, y: int):
        map_w, map_h = 160, 52
        surface = pygame.Surface((map_w, map_h), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 150))

        seg_w = map_w / MAP_SEGMENTS
        revealed = self.map_revealed[self.current_floor]

        for seg in range(MAP_SEGMENTS):
            rect = pygame.Rect(int(seg * seg_w), 8, max(1, int(seg_w) - 1), 20)
            if seg in revealed or self.current_floor == 0:
                pygame.draw.rect(surface, (92, 106, 125), rect)
            else:
                pygame.draw.rect(surface, (35, 35, 45), rect)

        pseg = int(max(0, min(MAP_SEGMENTS - 1, (self.player_x / WORLD_W) * MAP_SEGMENTS)))
        px = int(pseg * seg_w + seg_w * 0.5)
        pygame.draw.circle(surface, C_GREEN, (px, 18), 4)

        panel_seg = int((self.panel_x / WORLD_W) * MAP_SEGMENTS)
        qx = int(panel_seg * seg_w + seg_w * 0.5)
        pygame.draw.circle(surface, C_YELLOW, (qx, 18), 3)

        title = self.font_tiny.render("MINIMAP", True, C_WHITE)
        surface.blit(title, (4, 30))
        floor = self.font_tiny.render(f"F{self.current_floor}", True, C_WHITE)
        surface.blit(floor, (112, 30))

        self.screen.blit(surface, (x, y))
        pygame.draw.rect(self.screen, (110, 118, 136), (x, y, map_w, map_h), 1, border_radius=4)

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 155))
        self.screen.blit(overlay, (0, 0))

        t1 = self.font_big.render("BROADCAST TOWER RUN FAILED", True, C_RED)
        t2 = self.font_med.render("Manage health, sanity, battery, and route planning to survive.", True, C_WHITE)
        t3 = self.font_med.render("Press R to restart", True, C_YELLOW)

        self.screen.blit(t1, (SCREEN_W // 2 - t1.get_width() // 2, 280))
        self.screen.blit(t2, (SCREEN_W // 2 - t2.get_width() // 2, 336))
        self.screen.blit(t3, (SCREEN_W // 2 - t3.get_width() // 2, 380))


def main():
    game = BroadcastTower13Survival()
    game.run()


if __name__ == "__main__":
    main()
