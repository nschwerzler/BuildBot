dAAA"""
Broadcast 14 - 2.5D Survival

Core loop:
- Enter a night run in a free-roam tower map.
- Reach the active signal room (Radio 1/2/3) within 30 seconds.
- Tune AM/FM/Ghostband correctly to reveal hidden doors and progress.
- Wrong tune or missed timer triggers creature survival pressure for the rest of the night.
- Stabilize the final array on Night 7, then return to console and extract before blackout.
"""

import math
import random
from dataclasses import dataclass
from typing import List, Literal

import pygame

SCREEN_W, SCREEN_H = 1200, 720
FPS = 60
WORLD_W = 2400
FLOOR_Y = 620
TOTAL_NIGHTS = 7

PLAYER_SPEED = 255
INTERACT_RANGE = 60
SAFE_RADIUS = 88
NIGHT_BASE_TIME = 180
RADIO_WINDOW = 30.0
RADIO_START_DELAY = 10.0

C_BG = (14, 24, 18)
C_PLATFORM = (42, 72, 48)
C_TRACK = (56, 78, 44)
C_WHITE = (235, 235, 240)
C_GRAY = (165, 165, 178)
C_YELLOW = (236, 210, 95)
C_CYAN = (92, 205, 220)
C_GREEN = (85, 210, 130)
C_RED = (225, 86, 98)
C_PURPLE = (160, 105, 220)
C_ORANGE = (238, 153, 84)

Band = Literal["AM", "FM", "Ghostband"]
BANDS: List[Band] = ["AM", "FM", "Ghostband"]


@dataclass
class RadioNode:
    idx: int
    name: str
    x: float
    y: float


@dataclass
class Shop:
    x: float
    y: float


@dataclass
class Booth:
    x: float
    y: float


@dataclass
class Enemy:
    x: float
    y: float
    speed: float
    kind: str
    roam_x: float
    roam_y: float
    roam_timer: float = 0.0
    hit_cd: float = 0.0


@dataclass
class Wall:
    x: float
    y: float
    w: float
    h: float
    is_hidden_door: bool = False
    moving: bool = False
    axis: str = "x"
    amp: float = 0.0
    speed: float = 1.0


class Broadcast14:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Broadcast 14")
        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont("Arial", 40, bold=True)
        self.font_med = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_sm = pygame.font.SysFont("Arial", 18)
        self.font_tiny = pygame.font.SysFont("Consolas", 15)

        self.running = True
        self.game_over = False
        self.victory = False

        self.player_x = 280.0
        self.player_y = FLOOR_Y - 24
        self.cam_x = 0.0

        self.max_health = 100.0
        self.health = 100.0
        self.max_sanity = 100.0
        self.sanity = 100.0
        self.max_battery = 100.0
        self.battery = 100.0
        self.flashlight_on = True
        self.ward_chips = 0

        self.credits = 35

        self.current_night = 1
        self.night_time_left = float(NIGHT_BASE_TIME)
        self.required_radios = 3
        self.radios_completed = 0
        self.night_failed = False
        self.failure_spawn_timer = 14.0

        self.selected_band: Band = "AM"
        self.active_radio_idx = 0
        self.active_target_band: Band = "AM"
        self.radio_time_left = RADIO_WINDOW
        self.radio_start_delay_left = 0.0
        self.radio_presses_needed = 1
        self.radio_presses_done = 0
        self.radio_timer_failed = False

        self.doors_reveal_timer = 0.0
        self.silent_zone_active = False
        self.lockdown_extract_ready = False

        self.map_revealed = {night: set() for night in range(1, TOTAL_NIGHTS + 1)}
        self.panel_x = 2140

        self.radios: List[RadioNode] = [
            RadioNode(0, "Radio 1", 620, FLOOR_Y - 130),
            RadioNode(1, "Radio 2", 1260, FLOOR_Y - 125),
            RadioNode(2, "Radio 3", 1820, FLOOR_Y - 132),
        ]
        self.shops: List[Shop] = [Shop(930, FLOOR_Y - 118), Shop(1670, FLOOR_Y - 116)]
        self.booths: List[Booth] = [Booth(370, FLOOR_Y - 118), Booth(2030, FLOOR_Y - 118)]

        self.walls: List[Wall] = []
        self.enemies: List[Enemy] = []

        self.msg = "Night 1 started. Reach the active radio in 30s."
        self.msg_timer = 5.0

        self.build_shared_map()
        self.start_night(1, fresh=True)

    def build_shared_map(self):
        self.walls.clear()

        hall_top = FLOOR_Y - 178
        hall_bottom = FLOOR_Y - 34
        divider_w = 18
        section_w = 175

        for i, x in enumerate(range(420, WORLD_W - 300, section_w)):
            gap_center = FLOOR_Y - (98 if i % 2 == 0 else 138)
            gap_h = 56
            gap_top = gap_center - gap_h * 0.5
            gap_bottom = gap_center + gap_h * 0.5

            upper_h = max(0.0, gap_top - hall_top)
            lower_h = max(0.0, hall_bottom - gap_bottom)
            if upper_h > 14:
                self.walls.append(Wall(x=x, y=hall_top, w=divider_w, h=upper_h))
            if lower_h > 14:
                self.walls.append(Wall(x=x, y=gap_bottom, w=divider_w, h=lower_h))

        # Hidden doors revealed by correct tuning.
        self.walls.append(Wall(x=1110, y=hall_top + 58, w=18, h=56, is_hidden_door=True))
        self.walls.append(Wall(x=1540, y=hall_top + 42, w=18, h=56, is_hidden_door=True))

        # Moving walls (same layout every night, stronger movement with night).
        self.walls.append(Wall(x=760, y=FLOOR_Y - 168, w=110, h=18, moving=True, axis="y", amp=22, speed=0.9))
        self.walls.append(Wall(x=1380, y=FLOOR_Y - 92, w=120, h=18, moving=True, axis="x", amp=30, speed=1.1))

    def start_night(self, night: int, fresh: bool = False):
        self.current_night = night
        self.night_time_left = float(NIGHT_BASE_TIME)
        self.required_radios = min(5, 3 + (night - 1) // 2)
        self.radios_completed = 0
        self.night_failed = False
        self.failure_spawn_timer = max(8.0, 14.0 - night * 0.8)
        self.doors_reveal_timer = 0.0
        self.lockdown_extract_ready = False

        self.active_radio_idx = -1
        self.active_target_band = random.choice(BANDS)
        self.radio_time_left = 0.0
        self.radio_start_delay_left = RADIO_START_DELAY + random.uniform(0.0, 4.0)
        self.radio_presses_needed = 1
        self.radio_presses_done = 0
        self.radio_timer_failed = False

        # No creatures at spawn; creatures activate after radio failure.
        self.enemies.clear()

        self.player_x = 260.0
        self.player_y = FLOOR_Y - 24

        if not fresh:
            self.health = min(self.max_health, self.health + 20)
            self.sanity = min(self.max_sanity, self.sanity + 26)
            self.battery = min(self.max_battery, self.battery + 35)

        self.msg = f"Night {night}: survive for 3:00. Radios are optional bonus objectives."
        self.msg_timer = 3.2

    def spawn_enemy(self, x: float | None = None, kind: str | None = None):
        if x is None:
            x = random.uniform(480, WORLD_W - 180)
        if kind is None:
            kind = random.choice(["stalker", "feral", "wisp"])
        speed = 80 + self.current_night * 8 + random.uniform(-8, 12)
        if kind == "feral":
            speed += 10
        elif kind == "wisp":
            speed += 4
        y = random.uniform(FLOOR_Y - 150, FLOOR_Y - 28)
        roam_x = random.uniform(240, WORLD_W - 180)
        roam_y = random.uniform(FLOOR_Y - 168, FLOOR_Y - 28)
        self.enemies.append(Enemy(x=x, y=y, speed=speed, kind=kind, roam_x=roam_x, roam_y=roam_y, roam_timer=2.0))

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
                elif event.key == pygame.K_r and (self.game_over or self.victory):
                    self.reset_run()
                elif event.key == pygame.K_f and not (self.game_over or self.victory):
                    self.flashlight_on = not self.flashlight_on
                    self.msg = "Flashlight ON" if self.flashlight_on else "Flashlight OFF"
                    self.msg_timer = 0.9
                elif event.key == pygame.K_1:
                    self.selected_band = "AM"
                elif event.key == pygame.K_2:
                    self.selected_band = "FM"
                elif event.key == pygame.K_3:
                    self.selected_band = "Ghostband"
                elif event.key == pygame.K_e and not (self.game_over or self.victory):
                    self.try_interact()

    def reset_run(self):
        self.game_over = False
        self.victory = False
        self.health = self.max_health
        self.sanity = self.max_sanity
        self.battery = self.max_battery
        self.ward_chips = 0
        self.credits = 35
        self.flashlight_on = True
        self.map_revealed = {night: set() for night in range(1, TOTAL_NIGHTS + 1)}
        self.start_night(1, fresh=True)

    def update(self, dt: float):
        if self.game_over or self.victory:
            self.msg_timer = max(0.0, self.msg_timer - dt)
            return

        self.update_player(dt)
        self.update_walls(dt)
        self.update_survival(dt)
        self.update_entities(dt)
        self.update_radio_objective(dt)
        self.update_camera(dt)
        self.reveal_map()
        self.msg_timer = max(0.0, self.msg_timer - dt)

        if self.health <= 0 or self.sanity <= 0:
            self.game_over = True
            self.msg = "You did not survive the night. Press R to restart."
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
        self.player_y = max(FLOOR_Y - 182, min(FLOOR_Y - 16, self.player_y))

        if self.collides_walls(self.player_x, self.player_y):
            self.player_x = old_x
            if self.collides_walls(self.player_x, self.player_y):
                self.player_y = old_y

    def wall_rect(self, wall: Wall) -> pygame.Rect:
        move_scale = 1.0 + (self.current_night - 1) * 0.16
        x = wall.x
        y = wall.y
        if wall.moving:
            wave = math.sin(pygame.time.get_ticks() * 0.001 * wall.speed * move_scale) * wall.amp
            if wall.axis == "x":
                x += wave
            else:
                y += wave
        return pygame.Rect(int(x), int(y), int(wall.w), int(wall.h))

    def collides_walls(self, px: float, py: float) -> bool:
        player_rect = pygame.Rect(int(px - 12), int(py - 26), 24, 26)
        for wall in self.walls:
            if wall.is_hidden_door and self.doors_reveal_timer > 0:
                continue
            if player_rect.colliderect(self.wall_rect(wall)):
                return True
        return False

    def is_in_safe_zone(self) -> bool:
        for booth in self.booths:
            if math.hypot(booth.x - self.player_x, booth.y - self.player_y) < SAFE_RADIUS:
                return True
        for shop in self.shops:
            if math.hypot(shop.x - self.player_x, shop.y - self.player_y) < SAFE_RADIUS:
                return True
        return False

    def update_walls(self, dt: float):
        self.doors_reveal_timer = max(0.0, self.doors_reveal_timer - dt)

    def update_survival(self, dt: float):
        in_safe = self.is_in_safe_zone()

        if self.flashlight_on:
            self.battery = max(0.0, self.battery - (2.0 + self.current_night * 0.25) * dt)
            if self.battery <= 0:
                self.flashlight_on = False
                self.msg = "Scanner battery drained."
                self.msg_timer = 1.2

        # Silent zones begin on higher nights.
        self.silent_zone_active = self.current_night >= 5 and 930 < self.player_x < 1330

        sanity_drain = (0.58 + self.current_night * 0.14)
        if in_safe:
            sanity_drain *= 0.0
            self.sanity = min(self.max_sanity, self.sanity + 3.3 * dt)
            self.health = min(self.max_health, self.health + 1.2 * dt)
            self.battery = min(self.max_battery, self.battery + 2.2 * dt)
        elif self.silent_zone_active:
            sanity_drain *= 1.4

        self.sanity = max(0.0, self.sanity - sanity_drain * dt)

        if not in_safe and self.battery < 14:
            self.health = max(0.0, self.health - (0.48 + self.current_night * 0.06) * dt)

    def update_entities(self, dt: float):
        in_safe = self.is_in_safe_zone()

        if self.night_failed:
            self.failure_spawn_timer -= dt
            if self.failure_spawn_timer <= 0:
                self.spawn_enemy()
                self.failure_spawn_timer = max(5.5, 12.0 - self.current_night)

        for enemy in self.enemies:
            dx = self.player_x - enemy.x
            dy = self.player_y - enemy.y
            dist_player = math.hypot(dx, dy)

            detect_range = 220 if enemy.kind == "stalker" else (260 if enemy.kind == "feral" else 300)
            chase = dist_player < detect_range and not in_safe

            speed = enemy.speed * (0.78 if self.flashlight_on else 1.07)
            if enemy.kind == "stalker" and self.flashlight_on:
                speed *= 0.72
            if enemy.kind == "feral":
                speed *= 1.12
            if enemy.kind == "wisp":
                speed *= 0.92

            if in_safe:
                speed *= 0.25

            if chase and dist_player > 0.001:
                ux = dx / dist_player
                uy = dy / dist_player
                if enemy.kind == "wisp":
                    uy += math.sin(pygame.time.get_ticks() * 0.01 + enemy.x * 0.01) * 0.08
                elif enemy.kind == "feral":
                    ux += random.uniform(-0.03, 0.03)
                enemy.x += ux * speed * dt
                enemy.y += uy * speed * dt
            else:
                enemy.roam_timer -= dt
                roam_dx = enemy.roam_x - enemy.x
                roam_dy = enemy.roam_y - enemy.y
                roam_dist = math.hypot(roam_dx, roam_dy)
                if roam_dist > 1.0:
                    enemy.x += (roam_dx / roam_dist) * speed * 0.56 * dt
                    enemy.y += (roam_dy / roam_dist) * speed * 0.56 * dt
                if enemy.roam_timer <= 0 or roam_dist < 16:
                    enemy.roam_timer = random.uniform(1.4, 3.2)
                    enemy.roam_x = random.uniform(240, WORLD_W - 180)
                    enemy.roam_y = random.uniform(FLOOR_Y - 168, FLOOR_Y - 28)

            enemy.y = max(FLOOR_Y - 170, min(FLOOR_Y - 22, enemy.y))
            enemy.hit_cd = max(0.0, enemy.hit_cd - dt)

            # Tight hitbox: must be close in both X and Y.
            if (
                not in_safe
                and abs(enemy.x - self.player_x) < 14
                and abs(enemy.y - self.player_y) < 24
                and enemy.hit_cd <= 0
            ):
                enemy.hit_cd = 1.0
                hp_hit = random.uniform(4.0, 7.2)
                sanity_hit = random.uniform(4.5, 8.5)
                if self.ward_chips > 0:
                    self.ward_chips -= 1
                    hp_hit *= 0.35
                    sanity_hit *= 0.35
                self.health = max(0.0, self.health - hp_hit)
                self.sanity = max(0.0, self.sanity - sanity_hit)
                name = "Stalker" if enemy.kind == "stalker" else ("Feral" if enemy.kind == "feral" else "Wisp")
                self.msg = f"{name} hit: -{hp_hit:.1f} HP, -{sanity_hit:.1f} sanity"
                self.msg_timer = 1.1

        self.enemies = [enemy for enemy in self.enemies if -40 < enemy.x < WORLD_W + 40]

    def update_radio_objective(self, dt: float):
        self.night_time_left = max(0.0, self.night_time_left - dt)

        if self.night_time_left <= 0:
            if self.current_night >= TOTAL_NIGHTS:
                self.victory = True
                self.msg = "You survived all 7 nights. Extraction successful."
                self.msg_timer = 999
            else:
                self.start_night(self.current_night + 1)
            return

        if not self.night_failed:
            if self.active_radio_idx < 0:
                self.radio_start_delay_left = max(0.0, self.radio_start_delay_left - dt)
                if self.radio_start_delay_left <= 0:
                    self.choose_next_radio_task()
                    active = self.radios[self.active_radio_idx].name
                    self.msg = f"{active} is live. Tune with {self.selected_band} and press E x{self.radio_presses_needed}."
                    self.msg_timer = 2.2
            else:
                self.radio_time_left = max(0.0, self.radio_time_left - dt)
                if self.radio_time_left <= 0:
                    self.fail_radio_event("Radio window missed. Survive hostile creatures for the rest of the night.")

    def fail_radio_event(self, message: str):
        self.night_failed = True
        self.radio_timer_failed = True
        self.active_radio_idx = -1
        self.radio_time_left = 0.0
        self.spawn_enemy(kind="stalker")
        self.spawn_enemy(kind="feral")
        self.spawn_enemy(kind="wisp")
        self.msg = message
        self.msg_timer = 2.5

    def choose_next_radio_task(self):
        self.active_radio_idx = random.randint(0, 2)
        self.active_target_band = random.choice(BANDS)
        self.radio_time_left = RADIO_WINDOW
        self.radio_presses_needed = random.randint(1, 3)
        self.radio_presses_done = 0

    def try_interact(self):
        # Shop purchases: select with 1/2/3 and press E near shop.
        for shop in self.shops:
            if math.hypot(shop.x - self.player_x, shop.y - self.player_y) < INTERACT_RANGE:
                if self.selected_band == "AM":
                    cost = 16
                    if self.credits < cost:
                        self.msg = "Need 16 credits for Fuse."
                    else:
                        self.credits -= cost
                        self.night_time_left = min(NIGHT_BASE_TIME + 40, self.night_time_left + 18)
                        self.msg = "Bought Fuse: +18s lockdown time."
                elif self.selected_band == "FM":
                    cost = 18
                    if self.credits < cost:
                        self.msg = "Need 18 credits for Battery Cell."
                    else:
                        self.credits -= cost
                        self.battery = min(self.max_battery, self.battery + 38)
                        self.msg = "Bought Battery Cell: +38 battery."
                else:
                    cost = 20
                    if self.credits < cost:
                        self.msg = "Need 20 credits for Ward Chip."
                    else:
                        self.credits -= cost
                        self.ward_chips += 1
                        self.msg = "Bought Ward Chip: next creature hit reduced."
                self.msg_timer = 1.7
                return

        # Radio interaction.
        if self.active_radio_idx < 0 and not self.night_failed:
            for radio in self.radios:
                if math.hypot(radio.x - self.player_x, radio.y - self.player_y) < INTERACT_RANGE:
                    self.msg = "Radio network warming up. Stand by."
                    self.msg_timer = 1.0
                    return

        for radio in self.radios:
            if math.hypot(radio.x - self.player_x, radio.y - self.player_y) < INTERACT_RANGE:
                if self.night_failed:
                    self.msg = "Radio objective unavailable right now."
                    self.msg_timer = 1.0
                    return
                if radio.idx != self.active_radio_idx:
                    self.msg = f"{radio.name} is idle. Go to active radio target."
                    self.msg_timer = 1.0
                    return

                if self.selected_band == self.active_target_band:
                    self.radio_presses_done += 1
                    if self.radio_presses_done >= self.radio_presses_needed:
                        self.radios_completed += 1
                        self.credits += 8 + self.current_night * 2
                        self.sanity = min(self.max_sanity, self.sanity + 6)
                        self.doors_reveal_timer = 18.0
                        self.choose_next_radio_task()
                        self.msg = "Radio stabilized! Hidden doors opened briefly and you gained rewards."
                        self.msg_timer = 2.0
                    else:
                        left = self.radio_presses_needed - self.radio_presses_done
                        self.msg = f"Signal locking... press E {left} more time(s)."
                        self.msg_timer = 1.2
                else:
                    # Wrong band no longer instantly spawns enemies.
                    # Player must still complete exact E-count on correct band before timer expires.
                    self.radio_presses_done = 0
                    self.msg = f"Wrong band. Set {self.active_target_band} and press E x{self.radio_presses_needed}."
                    self.msg_timer = 1.5
                return

        # Lift console (status)
        if abs(self.player_x - self.panel_x) < INTERACT_RANGE:
            self.msg = "Console: survive until timer reaches 0 to progress to next night."
            self.msg_timer = 1.4
            return

        self.msg = "Nothing to interact with."
        self.msg_timer = 1.0

    def reveal_map(self):
        seg_count = 22
        seg_w = WORLD_W / seg_count
        idx = int(self.player_x / seg_w)
        idx = max(0, min(seg_count - 1, idx))
        current = self.map_revealed[self.current_night]
        for seg in range(idx - 1, idx + 2):
            if 0 <= seg < seg_count:
                current.add(seg)

    def update_camera(self, dt: float):
        target = self.player_x - SCREEN_W * 0.5
        target = max(0, min(WORLD_W - SCREEN_W, target))
        self.cam_x += (target - self.cam_x) * min(1.0, dt * 8)

    def draw(self):
        self.screen.fill(C_BG)
        self.draw_world()
        self.draw_hud()
        if self.game_over:
            self.draw_end("RUN FAILED", C_RED)
        elif self.victory:
            self.draw_end("YOU EXTRACTED", C_GREEN)
        pygame.display.flip()

    def draw_world(self):
        for i in range(7):
            shade = 22 + i * 6
            pygame.draw.rect(self.screen, (shade - 4, shade + 20, shade - 2), (0, i * 72, SCREEN_W, 72))

        pygame.draw.rect(self.screen, C_PLATFORM, (0, FLOOR_Y, SCREEN_W, SCREEN_H - FLOOR_Y))
        pygame.draw.rect(self.screen, C_TRACK, (0, FLOOR_Y + 34, SCREEN_W, 76))
        pygame.draw.line(self.screen, (94, 80, 56), (0, FLOOR_Y + 48), (SCREEN_W, FLOOR_Y + 48), 3)

        # forest trunks and canopy silhouette
        for tx in range(140, WORLD_W, 220):
            sx = int(tx - self.cam_x)
            if -40 <= sx <= SCREEN_W + 40:
                pygame.draw.rect(self.screen, (78, 58, 40), (sx - 6, FLOOR_Y - 140, 12, 140))
                pygame.draw.circle(self.screen, (34, 72, 40), (sx, FLOOR_Y - 150), 32)
                pygame.draw.circle(self.screen, (22, 54, 30), (sx - 20, FLOOR_Y - 132), 24)

        # ranger control cabins
        for booth in self.booths:
            sx = int(booth.x - self.cam_x)
            sy = int(booth.y)
            pygame.draw.rect(self.screen, (78, 98, 66), (sx - 38, sy - 34, 76, 56), border_radius=6)
            label = self.font_tiny.render("RANGER POST", True, C_CYAN)
            self.screen.blit(label, (sx - label.get_width() // 2, sy - 48))

        # supply huts
        for shop in self.shops:
            sx = int(shop.x - self.cam_x)
            sy = int(shop.y)
            pygame.draw.rect(self.screen, (92, 112, 68), (sx - 38, sy - 34, 76, 56), border_radius=6)
            label = self.font_tiny.render("SUPPLY HUT", True, C_GREEN)
            self.screen.blit(label, (sx - label.get_width() // 2, sy - 48))
            hint = self.font_tiny.render("AM=Fuse FM=Battery GB=Ward", True, C_GREEN)
            self.screen.blit(hint, (sx - hint.get_width() // 2, sy - 64))

        # lift console
        px = int(self.panel_x - self.cam_x)
        pygame.draw.rect(self.screen, (76, 92, 116), (px - 34, FLOOR_Y - 130, 68, 130), border_radius=8)
        ptxt = self.font_tiny.render("CONSOLE", True, C_WHITE)
        self.screen.blit(ptxt, (px - ptxt.get_width() // 2, FLOOR_Y - 116))

        # radios
        for radio in self.radios:
            sx = int(radio.x - self.cam_x)
            sy = int(radio.y)
            is_active = radio.idx == self.active_radio_idx and not self.night_failed
            color = C_ORANGE if is_active else C_CYAN
            pygame.draw.rect(self.screen, (66, 74, 95), (sx - 24, sy - 24, 48, 30), border_radius=5)
            pygame.draw.circle(self.screen, color, (sx, sy - 30), 7)
            txt = self.font_tiny.render(radio.name, True, color)
            self.screen.blit(txt, (sx - txt.get_width() // 2, sy - 48))
            if is_active:
                left = max(0, self.radio_presses_needed - self.radio_presses_done)
                need_txt = self.font_tiny.render(f"E x{left} left", True, C_YELLOW)
                self.screen.blit(need_txt, (sx - need_txt.get_width() // 2, sy - 64))

        # walls
        for wall in self.walls:
            if wall.is_hidden_door and self.doors_reveal_timer > 0:
                continue
            rect = self.wall_rect(wall)
            sx = int(rect.x - self.cam_x)
            if sx > SCREEN_W or sx + rect.w < 0:
                continue
            body = (78, 82, 98) if not wall.is_hidden_door else (58, 58, 66)
            pygame.draw.rect(self.screen, body, (sx, rect.y, rect.w, rect.h), border_radius=4)
            pygame.draw.rect(self.screen, (116, 122, 142), (sx, rect.y, rect.w, rect.h), 1, border_radius=4)

        # forest creatures
        for enemy in self.enemies:
            sx = int(enemy.x - self.cam_x)
            sy = int(enemy.y)
            if -40 <= sx <= SCREEN_W + 40:
                if enemy.kind == "stalker":
                    pygame.draw.rect(self.screen, (168, 174, 180), (sx - 8, sy - 22, 16, 22), border_radius=2)
                    pygame.draw.circle(self.screen, (212, 218, 224), (sx, sy - 25), 7)
                    pygame.draw.circle(self.screen, (28, 28, 30), (sx - 2, sy - 26), 1)
                    pygame.draw.circle(self.screen, (28, 28, 30), (sx + 2, sy - 26), 1)
                elif enemy.kind == "feral":
                    pygame.draw.ellipse(self.screen, (98, 90, 76), (sx - 12, sy - 14, 24, 14))
                    pygame.draw.circle(self.screen, (134, 122, 106), (sx + 10, sy - 13), 5)
                    pygame.draw.circle(self.screen, (30, 30, 30), (sx + 12, sy - 14), 1)
                else:
                    pygame.draw.ellipse(self.screen, (92, 112, 136), (sx - 11, sy - 16, 22, 16))
                    pygame.draw.circle(self.screen, (150, 182, 216), (sx, sy - 16), 3)

        # dark-night overlay (forest mood)
        darkness = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        darkness_alpha = min(200, 118 + self.current_night * 10)
        darkness.fill((4, 8, 6, darkness_alpha))
        self.screen.blit(darkness, (0, 0))

        # player
        player_sx = int(self.player_x - self.cam_x)
        player_sy = int(self.player_y)
        pygame.draw.ellipse(self.screen, (102, 185, 245), (player_sx - 14, player_sy - 20, 28, 20))
        pygame.draw.circle(self.screen, (102, 185, 245), (player_sx, player_sy - 24), 10)

        if self.flashlight_on and self.battery > 0:
            glow = pygame.Surface((300, 200), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (255, 245, 210, 64), (0, 0, 300, 200))
            self.screen.blit(glow, (player_sx - 150, player_sy - 104))

    def draw_meter(self, x: int, y: int, w: int, h: int, ratio: float, col):
        ratio = max(0.0, min(1.0, ratio))
        pygame.draw.rect(self.screen, (22, 22, 28), (x, y, w, h), border_radius=4)
        pygame.draw.rect(self.screen, col, (x, y, int(w * ratio), h), border_radius=4)
        pygame.draw.rect(self.screen, (120, 120, 138), (x, y, w, h), 1, border_radius=4)

    def draw_hud(self):
        pygame.draw.rect(self.screen, (8, 8, 11), (10, 10, SCREEN_W - 20, 108), border_radius=8)
        pygame.draw.rect(self.screen, (90, 96, 112), (10, 10, SCREEN_W - 20, 108), 1, border_radius=8)

        self.screen.blit(self.font_sm.render(f"Night {self.current_night}/7", True, C_WHITE), (22, 18))
        self.screen.blit(self.font_sm.render(f"Health {self.health:0.0f}", True, C_WHITE), (22, 42))
        self.screen.blit(self.font_sm.render(f"Sanity {self.sanity:0.0f}", True, C_WHITE), (22, 66))
        self.screen.blit(self.font_sm.render(f"Battery {self.battery:0.0f}", True, C_WHITE), (22, 90))

        self.draw_meter(118, 46, 210, 10, self.health / self.max_health, (226, 118, 112))
        self.draw_meter(118, 70, 210, 10, self.sanity / self.max_sanity, C_RED)
        self.draw_meter(118, 94, 210, 10, self.battery / self.max_battery, C_CYAN)

        mins = int(self.night_time_left) // 60
        secs = int(self.night_time_left) % 60
        radio_secs = max(0, int(self.radio_time_left))

        self.screen.blit(self.font_sm.render(f"Survive Timer {mins:02d}:{secs:02d}", True, C_ORANGE), (350, 20))
        self.screen.blit(self.font_sm.render(f"Credits {self.credits}", True, C_YELLOW), (350, 45))
        self.screen.blit(self.font_sm.render(f"Ward Chips {self.ward_chips}", True, C_GREEN), (350, 70))

        if not self.night_failed:
            if self.active_radio_idx < 0:
                hint = f"Survive the night | Next radio in {int(self.radio_start_delay_left)}s"
            else:
                radio_name = self.radios[self.active_radio_idx].name
                left_presses = max(0, self.radio_presses_needed - self.radio_presses_done)
                hint = f"Survive | Active: {radio_name} | Band {self.selected_band} | Press E {left_presses} more time(s) | Timer {radio_secs}s"
        elif self.night_failed:
            hint = "Night failed: survive creatures until dawn."

        if self.current_night >= 5 and self.silent_zone_active:
            hint = "SILENT ZONE: audio cues cut out. Follow minimap and visuals."

        self.screen.blit(self.font_tiny.render(hint, True, C_GRAY), (470, 22))
        self.draw_minimap(980, 62)

        controls = "1/2/3 select band (AM/FM/Ghostband) | E interact | F scanner | R restart"
        self.screen.blit(self.font_tiny.render(controls, True, C_GRAY), (14, SCREEN_H - 20))

        if self.msg_timer > 0:
            pygame.draw.rect(self.screen, (0, 0, 0), (10, SCREEN_H - 44, SCREEN_W - 20, 26), border_radius=6)
            self.screen.blit(self.font_sm.render(self.msg, True, C_WHITE), (16, SCREEN_H - 39))

    def draw_minimap(self, x: int, y: int):
        map_w, map_h = 205, 54
        surface = pygame.Surface((map_w, map_h), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 145))

        # player
        px = int((self.player_x / WORLD_W) * map_w)
        pygame.draw.circle(surface, C_GREEN, (px, 16), 4)

        # radios
        for radio in self.radios:
            rx = int((radio.x / WORLD_W) * map_w)
            col = C_CYAN
            if radio.idx == self.active_radio_idx and not self.night_failed:
                col = C_RED
            pygame.draw.circle(surface, col, (rx, 16), 3)
            tag = self.font_tiny.render(str(radio.idx + 1), True, col)
            surface.blit(tag, (rx - 4, 22))

        # console
        cx = int((self.panel_x / WORLD_W) * map_w)
        pygame.draw.circle(surface, C_YELLOW, (cx, 16), 3)

        surface.blit(self.font_tiny.render("MINIMAP", True, C_WHITE), (4, 36))
        self.screen.blit(surface, (x, y))
        pygame.draw.rect(self.screen, (110, 118, 136), (x, y, map_w, map_h), 1, border_radius=4)

    def draw_end(self, title: str, col):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        self.screen.blit(overlay, (0, 0))

        t1 = self.font_big.render(title, True, col)
        t2 = self.font_med.render("Press R to restart", True, C_WHITE)
        self.screen.blit(t1, (SCREEN_W // 2 - t1.get_width() // 2, 292))
        self.screen.blit(t2, (SCREEN_W // 2 - t2.get_width() // 2, 348))


def main():
    game = Broadcast14()
    game.run()


if __name__ == "__main__":
    main()
