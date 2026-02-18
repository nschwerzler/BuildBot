"""
AI SURVIVAL 2.5D
- Survive as long as possible.
- The AI does NOT chat. It only triggers random good and bad world events.
- If you close the game during a run, your run save is wiped.

Controls:
  WASD / Arrow Keys - Move
    LEFT CLICK - Sword slash
  SPACE - Dash (short cooldown)
    TAB - Toggle inventory panel
    1 / 2 - Select inventory slot
    E - Use selected inventory item
  ESC - Quit run (counts as close, save is lost)
"""

import json
import math
import os
import random
from dataclasses import dataclass
from typing import List, Tuple

import pygame

SCREEN_W, SCREEN_H = 1000, 720
FPS = 60

WORLD_W, WORLD_H = 70, 50
TILE = 32
WALL_H = 12  # fake 2.5D wall extrusion

RUN_SAVE = "ai_survival_run.json"
META_SAVE = "ai_survival_meta.json"

C_BG = (15, 17, 24)
C_FLOOR = (42, 45, 58)
C_FLOOR2 = (38, 41, 52)
C_WALL_TOP = (90, 102, 140)
C_WALL_FRONT = (62, 72, 100)
C_WALL_SHADOW = (42, 48, 68)
C_PLAYER = (90, 220, 140)
C_ENEMY = (220, 90, 90)
C_PICKUP = (240, 210, 90)
C_TEXT = (235, 235, 245)
C_GOOD = (120, 230, 140)
C_BAD = (250, 110, 110)


@dataclass
class Enemy:
    x: float
    y: float
    hp: int
    speed: float
    damage: int


@dataclass
class Pickup:
    x: float
    y: float
    kind: str  # food, heal


class EventDirector:
    def __init__(self):
        self.timer = 8.0
        self.interval = 11.0

    def update_and_maybe_trigger(self, dt: float, game: "AISurvivalGame"):
        self.timer -= dt
        if self.timer > 0:
            return
        self.interval = max(5.0, self.interval - 0.2)
        self.timer = random.uniform(self.interval * 0.7, self.interval * 1.25)
        self.trigger_random_event(game)

    def trigger_random_event(self, game: "AISurvivalGame"):
        if random.random() < 0.48:
            self.good_event(game)
        else:
            self.bad_event(game)

    def good_event(self, game: "AISurvivalGame"):
        roll = random.randint(1, 6)
        if roll == 1:
            bonus = random.randint(6, 10)
            game.max_hp += bonus
            game.hp = min(game.max_hp, game.hp + bonus)
            game.post_event(f"AI Event: Permanent Vitality (+{bonus} Max HP)", True)
        elif roll == 2:
            game.sword_damage += 2
            game.post_event("AI Event: Sharpened Edge (+2 Sword ATK permanently)", True)
        elif roll == 3:
            game.perm_speed_bonus += 0.12
            game.post_event("AI Event: Lightfoot (+speed permanently)", True)
        elif roll == 4:
            game.perm_food_drain_mult = max(0.55, game.perm_food_drain_mult - 0.08)
            game.post_event("AI Event: Better Metabolism (slower hunger permanently)", True)
        elif roll == 5:
            game.inventory["food_pack"] += 1
            game.inventory["medkit"] += 1
            game.post_event("AI Event: Emergency Supplies (+1 Food Pack, +1 Medkit)", True)
        else:
            game.speed_boost_timer = 8.0
            game.post_event("AI Event: Adrenaline Wind (+speed temp)", True)

    def bad_event(self, game: "AISurvivalGame"):
        roll = random.randint(1, 6)
        if roll == 1:
            penalty = random.randint(4, 8)
            game.max_hp = max(40, game.max_hp - penalty)
            game.hp = min(game.hp, game.max_hp)
            game.post_event(f"AI Event: Permanent Frailty (-{penalty} Max HP)", False)
        elif roll == 2:
            game.sword_damage = max(4, game.sword_damage - 1)
            game.post_event("AI Event: Blunted Blade (-1 Sword ATK permanently)", False)
        elif roll == 3:
            game.perm_speed_bonus = max(-1.2, game.perm_speed_bonus - 0.10)
            game.post_event("AI Event: Heavy Air (speed permanently reduced)", False)
        elif roll == 4:
            game.perm_food_drain_mult = min(2.2, game.perm_food_drain_mult + 0.12)
            game.post_event("AI Event: Starvation Curse (hunger drains faster permanently)", False)
        elif roll == 5:
            game.perm_enemy_hp_mult = min(3.0, game.perm_enemy_hp_mult + 0.14)
            game.post_event("AI Event: Hardened Foes (enemy HP permanently up)", False)
        else:
            game.perm_enemy_damage_mult = min(2.8, game.perm_enemy_damage_mult + 0.10)
            game.post_event("AI Event: Deadlier Foes (enemy damage permanently up)", False)


class AISurvivalGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("AI Survival 2.5D")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)
        self.font_big = pygame.font.SysFont("Arial", 34, bold=True)

        self.grid = [[0 for _ in range(WORLD_W)] for _ in range(WORLD_H)]
        self._build_world()

        self.cam_x = WORLD_W / 2
        self.cam_y = WORLD_H / 2
        self.px = WORLD_W / 2 + 0.5
        self.py = WORLD_H / 2 + 0.5

        self.max_hp = 100
        self.hp = 100
        self.food = 100.0
        self.base_speed = 4.2
        self.dash_cd = 0.0
        self.sword_cd = 0.0
        self.sword_damage = 11
        self.sword_range = 1.35
        self.sword_swing_timer = 0.0
        self.sword_swing_total = 0.22
        self.last_sword_angle = -math.pi / 2

        self.enemies: List[Enemy] = []
        self.pickups: List[Pickup] = []
        self.wave = 1
        self.wave_timer = 0.0
        self.survival_time = 0.0
        self.food_spawn_timer = 4.5

        self.director = EventDirector()
        self.event_text = "AI Director Active: random events incoming"
        self.event_timer = 4.0
        self.event_good = True

        self.speed_boost_timer = 0.0
        self.darkness_timer = 0.0
        self.reverse_controls_timer = 0.0
        self.enemy_speed_mult = 1.0
        self.enemy_speed_timer = 0.0

        self.perm_speed_bonus = 0.0
        self.perm_food_drain_mult = 1.0
        self.perm_enemy_hp_mult = 1.0
        self.perm_enemy_damage_mult = 1.0

        self.inventory = {
            "food_pack": 1,
            "medkit": 1,
        }
        self.inventory_order = ["food_pack", "medkit"]
        self.inventory_names = {
            "food_pack": "Food Pack (+30 Food)",
            "medkit": "Medkit (+24 HP)",
        }
        self.selected_slot = 0
        self.show_inventory = False

        self.run_save_timer = 0.0
        self.running = True
        self.dead = False
        self.high_score = self._load_highscore()

        self._invalidate_old_run_save()
        self._save_run_state()

        for _ in range(4):
            self.spawn_enemy()
        for _ in range(4):
            self.spawn_pickup(random.choice(["food", "heal"]))

    def _build_world(self):
        for y in range(WORLD_H):
            for x in range(WORLD_W):
                if x == 0 or y == 0 or x == WORLD_W - 1 or y == WORLD_H - 1:
                    self.grid[y][x] = 1
        for _ in range(120):
            x = random.randint(2, WORLD_W - 3)
            y = random.randint(2, WORLD_H - 3)
            if abs(x - WORLD_W // 2) > 5 or abs(y - WORLD_H // 2) > 5:
                self.grid[y][x] = 1

    def _invalidate_old_run_save(self):
        if os.path.exists(RUN_SAVE):
            try:
                os.remove(RUN_SAVE)
                self.event_text = "Previous run save deleted (closing loses progress)"
                self.event_timer = 5.0
                self.event_good = False
            except OSError:
                pass

    def _load_highscore(self) -> float:
        if not os.path.exists(META_SAVE):
            return 0.0
        try:
            with open(META_SAVE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return float(data.get("best_time", 0.0))
        except Exception:
            return 0.0

    def _save_highscore(self):
        if self.survival_time <= self.high_score:
            return
        self.high_score = self.survival_time
        try:
            with open(META_SAVE, "w", encoding="utf-8") as f:
                json.dump({"best_time": round(self.high_score, 2)}, f, indent=2)
        except Exception:
            pass

    def _save_run_state(self):
        data = {
            "survival_time": round(self.survival_time, 2),
            "hp": self.hp,
            "food": round(self.food, 2),
            "wave": self.wave,
        }
        try:
            with open(RUN_SAVE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _wipe_run_save(self):
        if os.path.exists(RUN_SAVE):
            try:
                os.remove(RUN_SAVE)
            except OSError:
                pass

    def is_solid(self, x: float, y: float) -> bool:
        tx, ty = int(x), int(y)
        if tx < 0 or ty < 0 or tx >= WORLD_W or ty >= WORLD_H:
            return True
        return self.grid[ty][tx] == 1

    def spawn_enemy(self, near_player: bool = False):
        for _ in range(50):
            if near_player:
                x = self.px + random.uniform(-5, 5)
                y = self.py + random.uniform(-5, 5)
            else:
                x = random.uniform(2, WORLD_W - 2)
                y = random.uniform(2, WORLD_H - 2)
            if not self.is_solid(x, y):
                if abs(x - self.px) + abs(y - self.py) > 4:
                    hp = 20 + self.wave * 2
                    hp = int(hp * self.perm_enemy_hp_mult)
                    dmg = max(1, int((8 + self.wave // 3) * self.perm_enemy_damage_mult))
                    self.enemies.append(Enemy(x, y, hp=hp, speed=1.8 + self.wave * 0.03, damage=dmg))
                    return

    def spawn_pickup(self, kind: str):
        for _ in range(40):
            x = random.uniform(2, WORLD_W - 2)
            y = random.uniform(2, WORLD_H - 2)
            if not self.is_solid(x, y):
                self.pickups.append(Pickup(x, y, kind))
                return

    def post_event(self, text: str, good: bool):
        self.event_text = text
        self.event_good = good
        self.event_timer = 3.8

    def update(self, dt: float):
        if self.dead:
            return

        self.survival_time += dt
        self.food = max(0.0, self.food - dt * 1.7 * self.perm_food_drain_mult)
        if self.food <= 0:
            self.hp -= dt * 8

        if self.dash_cd > 0:
            self.dash_cd -= dt
        if self.sword_cd > 0:
            self.sword_cd -= dt
        if self.sword_swing_timer > 0:
            self.sword_swing_timer -= dt
        if self.speed_boost_timer > 0:
            self.speed_boost_timer -= dt
        if self.darkness_timer > 0:
            self.darkness_timer -= dt
        if self.reverse_controls_timer > 0:
            self.reverse_controls_timer -= dt
        if self.enemy_speed_timer > 0:
            self.enemy_speed_timer -= dt
        else:
            self.enemy_speed_mult = 1.0
        if self.event_timer > 0:
            self.event_timer -= dt

        keys = pygame.key.get_pressed()
        dx = (1 if keys[pygame.K_d] or keys[pygame.K_RIGHT] else 0) - (1 if keys[pygame.K_a] or keys[pygame.K_LEFT] else 0)
        dy = (1 if keys[pygame.K_s] or keys[pygame.K_DOWN] else 0) - (1 if keys[pygame.K_w] or keys[pygame.K_UP] else 0)

        if self.reverse_controls_timer > 0:
            dx, dy = -dx, -dy

        speed = self.base_speed + self.perm_speed_bonus + (1.2 if self.speed_boost_timer > 0 else 0.0)
        speed = max(2.2, speed)
        if dx != 0 or dy != 0:
            mag = math.sqrt(dx * dx + dy * dy)
            nx, ny = dx / mag, dy / mag
            nxp = self.px + nx * speed * dt
            nyp = self.py + ny * speed * dt
            if not self.is_solid(nxp, self.py):
                self.px = nxp
            if not self.is_solid(self.px, nyp):
                self.py = nyp

        for e in self.enemies:
            vx = self.px - e.x
            vy = self.py - e.y
            dist = math.hypot(vx, vy)
            if dist > 0.01:
                vx /= dist
                vy /= dist
            move = e.speed * self.enemy_speed_mult * dt
            ex = e.x + vx * move
            ey = e.y + vy * move
            if not self.is_solid(ex, e.y):
                e.x = ex
            if not self.is_solid(e.x, ey):
                e.y = ey

            if dist < 0.75:
                self.hp -= e.damage * dt

        self.enemies = [e for e in self.enemies if e.hp > 0]

        kept: List[Pickup] = []
        for p in self.pickups:
            if math.hypot(self.px - p.x, self.py - p.y) < 0.7:
                if p.kind == "food":
                    self.inventory["food_pack"] += 1
                else:
                    self.inventory["medkit"] += 1
            else:
                kept.append(p)
        self.pickups = kept

        self.wave_timer += dt
        self.food_spawn_timer -= dt

        if self.food_spawn_timer <= 0:
            self.spawn_pickup("food")
            self.food_spawn_timer = random.uniform(4.0, 7.0)

        if self.wave_timer > 14:
            self.wave_timer = 0
            self.wave += 1
            for _ in range(1 + self.wave // 3):
                self.spawn_enemy()
            if random.random() < 0.95:
                self.spawn_pickup("food" if random.random() < 0.8 else "heal")

        self.director.update_and_maybe_trigger(dt, self)

        self.cam_x += (self.px - self.cam_x) * 7 * dt
        self.cam_y += (self.py - self.cam_y) * 7 * dt

        self.run_save_timer += dt
        if self.run_save_timer >= 1.0:
            self.run_save_timer = 0.0
            self._save_run_state()

        if self.hp <= 0:
            self.dead = True
            self._save_highscore()
            self._wipe_run_save()

    def _norm_angle_diff(self, a: float, b: float) -> float:
        return (a - b + math.pi) % (math.pi * 2) - math.pi

    def do_sword_attack(self, mouse_pos: Tuple[int, int]):
        if self.dead or self.sword_cd > 0:
            return
        self.sword_cd = 0.24

        world_mx = (mouse_pos[0] - SCREEN_W / 2) / TILE + self.cam_x
        world_my = (mouse_pos[1] - SCREEN_H / 2) / TILE + self.cam_y
        attack_angle = math.atan2(world_my - self.py, world_mx - self.px)
        self.last_sword_angle = attack_angle
        self.sword_swing_timer = self.sword_swing_total

        base_damage = self.sword_damage + self.wave // 7
        for e in self.enemies:
            dx = e.x - self.px
            dy = e.y - self.py
            dist = math.hypot(dx, dy)
            if dist > self.sword_range:
                continue
            angle_to_enemy = math.atan2(dy, dx)
            if abs(self._norm_angle_diff(angle_to_enemy, attack_angle)) > 1.1:
                continue
            e.hp -= base_damage

    def use_selected_inventory_item(self):
        key = self.inventory_order[self.selected_slot]
        if self.inventory.get(key, 0) <= 0:
            return
        if key == "food_pack":
            self.food = min(100.0, self.food + 30)
        elif key == "medkit":
            self.hp = min(self.max_hp, self.hp + 24)
        self.inventory[key] -= 1

    def _draw_sword_swing(self, psx: int, psy: int):
        if self.sword_swing_timer <= 0:
            return

        progress = 1.0 - (self.sword_swing_timer / self.sword_swing_total)
        progress = max(0.0, min(1.0, progress))
        sweep = -0.85 + (1.7 * progress)
        angle = self.last_sword_angle + sweep

        dir_x = math.cos(angle)
        dir_y = math.sin(angle)
        perp_x = -dir_y
        perp_y = dir_x

        base_x = psx + dir_x * 15
        base_y = psy + dir_y * 15
        tip_x = psx + dir_x * 54
        tip_y = psy + dir_y * 54

        blade_half = 4
        blade_poly = [
            (base_x + perp_x * blade_half, base_y + perp_y * blade_half),
            (base_x - perp_x * blade_half, base_y - perp_y * blade_half),
            (tip_x - perp_x * 2, tip_y - perp_y * 2),
            (tip_x + perp_x * 2, tip_y + perp_y * 2),
        ]
        pygame.draw.polygon(self.screen, (200, 210, 230), blade_poly)
        pygame.draw.polygon(self.screen, (105, 120, 155), blade_poly, 1)

        for i in range(1, 4):
            t = i / 4
            sx = base_x + (tip_x - base_x) * t
            sy = base_y + (tip_y - base_y) * t
            pygame.draw.line(
                self.screen,
                (160, 175, 205),
                (sx - perp_x * 3, sy - perp_y * 3),
                (sx + perp_x * 3, sy + perp_y * 3),
                1,
            )

        guard_x = psx + dir_x * 12
        guard_y = psy + dir_y * 12
        pygame.draw.line(
            self.screen,
            (170, 140, 80),
            (guard_x - perp_x * 7, guard_y - perp_y * 7),
            (guard_x + perp_x * 7, guard_y + perp_y * 7),
            3,
        )
        handle_end_x = psx + dir_x * 6
        handle_end_y = psy + dir_y * 6
        pygame.draw.line(self.screen, (95, 65, 40), (psx, psy), (handle_end_x, handle_end_y), 4)

        trail_alpha = int(120 * (1.0 - progress))
        if trail_alpha > 0:
            trail = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            arc_rect = pygame.Rect(psx - 58, psy - 58, 116, 116)
            pygame.draw.arc(trail, (220, 230, 255, trail_alpha), arc_rect, angle - 0.35, angle + 0.35, 3)
            self.screen.blit(trail, (0, 0))

    def draw_world_tile(self, tx: int, ty: int):
        sx = int((tx - self.cam_x) * TILE + SCREEN_W / 2)
        sy = int((ty - self.cam_y) * TILE + SCREEN_H / 2)
        if sx < -TILE or sy < -TILE or sx > SCREEN_W + TILE or sy > SCREEN_H + TILE:
            return

        t = self.grid[ty][tx]
        if t == 0:
            c = C_FLOOR if (tx + ty) % 2 == 0 else C_FLOOR2
            pygame.draw.rect(self.screen, c, (sx, sy, TILE + 1, TILE + 1))
        else:
            pygame.draw.rect(self.screen, C_WALL_SHADOW, (sx, sy, TILE + 1, TILE + WALL_H + 1))
            pygame.draw.rect(self.screen, C_WALL_TOP, (sx, sy - WALL_H, TILE + 1, WALL_H + 1))
            pygame.draw.rect(self.screen, C_WALL_FRONT, (sx + 1, sy + 1, TILE - 1, TILE - 1))

    def draw(self):
        self.screen.fill(C_BG)

        for y in range(WORLD_H):
            for x in range(WORLD_W):
                self.draw_world_tile(x, y)

        for p in self.pickups:
            sx = int((p.x - self.cam_x) * TILE + SCREEN_W / 2)
            sy = int((p.y - self.cam_y) * TILE + SCREEN_H / 2)
            color = C_PICKUP if p.kind == "food" else (130, 230, 255)
            pygame.draw.circle(self.screen, color, (sx, sy), 6)

        for e in sorted(self.enemies, key=lambda item: item.y):
            sx = int((e.x - self.cam_x) * TILE + SCREEN_W / 2)
            sy = int((e.y - self.cam_y) * TILE + SCREEN_H / 2)
            pygame.draw.circle(self.screen, C_ENEMY, (sx, sy), 10)

        psx = int((self.px - self.cam_x) * TILE + SCREEN_W / 2)
        psy = int((self.py - self.cam_y) * TILE + SCREEN_H / 2)
        pygame.draw.circle(self.screen, C_PLAYER, (psx, psy), 11)
        self._draw_sword_swing(psx, psy)

        hp_txt = self.font.render(f"HP: {int(self.hp)}/{self.max_hp}", True, C_TEXT)
        food_txt = self.font.render(f"Food: {int(self.food)}", True, C_TEXT)
        time_txt = self.font.render(f"Survival: {self.survival_time:.1f}s", True, C_TEXT)
        wave_txt = self.font.render(f"Wave: {self.wave}", True, C_TEXT)
        best_txt = self.font.render(f"Best: {self.high_score:.1f}s", True, C_TEXT)
        next_event_txt = self.font.render(f"Next Event: {max(0.0, self.director.timer):.1f}s", True, C_TEXT)
        self.screen.blit(hp_txt, (12, 10))
        self.screen.blit(food_txt, (12, 32))
        self.screen.blit(time_txt, (12, 54))
        self.screen.blit(wave_txt, (12, 76))
        self.screen.blit(best_txt, (12, 98))
        self.screen.blit(next_event_txt, (12, 120))

        slot_key = self.inventory_order[self.selected_slot]
        selected_name = self.inventory_names[slot_key]
        selected_count = self.inventory.get(slot_key, 0)
        inv_txt = self.font.render(f"Selected Item [{self.selected_slot + 1}]: {selected_name} x{selected_count}", True, C_TEXT)
        self.screen.blit(inv_txt, (12, 142))

        event_col = C_GOOD if self.event_good else C_BAD
        ev = self.font.render(self.event_text, True, event_col)
        self.screen.blit(ev, (12, SCREEN_H - 32))

        if self.show_inventory:
            panel = pygame.Surface((460, 160), pygame.SRCALPHA)
            panel.fill((0, 0, 0, 170))
            self.screen.blit(panel, (12, SCREEN_H - 210))
            title = self.font.render("Inventory", True, C_TEXT)
            self.screen.blit(title, (22, SCREEN_H - 200))
            for i, key in enumerate(self.inventory_order):
                marker = ">" if i == self.selected_slot else " "
                line = f"{marker} [{i + 1}] {self.inventory_names[key]} x{self.inventory.get(key, 0)}"
                txt = self.font.render(line, True, C_TEXT)
                self.screen.blit(txt, (26, SCREEN_H - 172 + i * 28))
            hint = self.font.render("TAB toggle | 1/2 select | E use", True, C_TEXT)
            self.screen.blit(hint, (26, SCREEN_H - 112))

        if self.darkness_timer > 0:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            pygame.draw.circle(overlay, (0, 0, 0, 0), (psx, psy), 120)
            self.screen.blit(overlay, (0, 0))

        if self.dead:
            ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 170))
            self.screen.blit(ov, (0, 0))
            t1 = self.font_big.render("You Did Not Survive", True, C_BAD)
            t2 = self.font.render("Press ENTER to restart | ESC to quit", True, C_TEXT)
            self.screen.blit(t1, (SCREEN_W // 2 - t1.get_width() // 2, 290))
            self.screen.blit(t2, (SCREEN_W // 2 - t2.get_width() // 2, 340))

        pygame.display.flip()

    def restart(self):
        self.__init__()

    def handle_keydown(self, key: int):
        if self.dead:
            if key == pygame.K_RETURN:
                self.restart()
            elif key == pygame.K_ESCAPE:
                self._wipe_run_save()
                self.running = False
            return

        if key == pygame.K_SPACE and self.dash_cd <= 0:
            self.dash_cd = 1.1
            keys = pygame.key.get_pressed()
            dx = (1 if keys[pygame.K_d] or keys[pygame.K_RIGHT] else 0) - (1 if keys[pygame.K_a] or keys[pygame.K_LEFT] else 0)
            dy = (1 if keys[pygame.K_s] or keys[pygame.K_DOWN] else 0) - (1 if keys[pygame.K_w] or keys[pygame.K_UP] else 0)
            if dx == 0 and dy == 0:
                dy = -1
            mag = math.sqrt(dx * dx + dy * dy)
            dx /= mag
            dy /= mag
            dash_dist = 2.4
            tx = self.px + dx * dash_dist
            ty = self.py + dy * dash_dist
            if not self.is_solid(tx, self.py):
                self.px = tx
            if not self.is_solid(self.px, ty):
                self.py = ty

        elif key == pygame.K_ESCAPE:
            self._wipe_run_save()
            self.running = False
        elif key == pygame.K_TAB:
            self.show_inventory = not self.show_inventory
        elif key == pygame.K_1:
            self.selected_slot = 0
        elif key == pygame.K_2:
            self.selected_slot = 1
        elif key == pygame.K_e:
            self.use_selected_inventory_item()

    def run(self):
        while self.running:
            dt = min(0.05, self.clock.tick(FPS) / 1000.0)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._wipe_run_save()  # close = lose run save
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.do_sword_attack(event.pos)

            self.update(dt)
            self.draw()

        pygame.quit()


def main():
    AISurvivalGame().run()


if __name__ == "__main__":
    main()
