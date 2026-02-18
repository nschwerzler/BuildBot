import random
import tkinter as tk
from tkinter import messagebox


class TetrisLite:
    title = "Tetris Lite"
    instructions = "Left/Right or A/D: Move  Up or W: Rotate  Down or S: Soft Drop  Space: Hard Drop  R: Restart"

    SHAPES = [
        [[1, 1, 1, 1]],
        [[1, 1], [1, 1]],
        [[1, 1, 1], [0, 1, 0]],
        [[1, 1, 0], [0, 1, 1]],
        [[0, 1, 1], [1, 1, 0]],
        [[1, 0, 0], [1, 1, 1]],
        [[0, 0, 1], [1, 1, 1]],
    ]

    COLORS = ["#7dd3fc", "#fef08a", "#86efac", "#fdba74", "#fda4af", "#c4b5fd", "#67e8f9"]

    def __init__(self, app):
        self.app = app
        self.cols = 10
        self.rows = 18
        self.cell = 24
        self.reset()

    def reset(self):
        self.board = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        self.score = 0
        self.lines = 0
        self.game_over = False
        self.drop_ms = 520
        self.elapsed = 0
        self.spawn_piece()
        self.draw()

    def spawn_piece(self):
        idx = random.randrange(len(self.SHAPES))
        self.shape = [row[:] for row in self.SHAPES[idx]]
        self.color = self.COLORS[idx]
        self.px = self.cols // 2 - len(self.shape[0]) // 2
        self.py = 0
        if self.collides(self.px, self.py, self.shape):
            self.game_over = True

    def rotate(self):
        return [list(row) for row in zip(*self.shape[::-1])]

    def collides(self, nx, ny, shape):
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if not cell:
                    continue
                bx = nx + x
                by = ny + y
                if bx < 0 or bx >= self.cols or by >= self.rows:
                    return True
                if by >= 0 and self.board[by][bx] is not None:
                    return True
        return False

    def lock_piece(self):
        for y, row in enumerate(self.shape):
            for x, cell in enumerate(row):
                if cell:
                    by = self.py + y
                    bx = self.px + x
                    if 0 <= by < self.rows:
                        self.board[by][bx] = self.color
        self.clear_lines()
        self.spawn_piece()

    def clear_lines(self):
        kept = [r for r in self.board if any(c is None for c in r)]
        cleared = self.rows - len(kept)
        while len(kept) < self.rows:
            kept.insert(0, [None for _ in range(self.cols)])
        self.board = kept
        if cleared:
            self.lines += cleared
            self.score += [0, 100, 250, 450, 700][cleared]
            self.drop_ms = max(160, self.drop_ms - 8 * cleared)

    def move(self, dx, dy):
        nx = self.px + dx
        ny = self.py + dy
        if not self.collides(nx, ny, self.shape):
            self.px = nx
            self.py = ny
            return True
        if dy == 1:
            self.lock_piece()
        return False

    def hard_drop(self):
        while self.move(0, 1):
            self.score += 2

    def on_key(self, key):
        raw_key = key
        key = key.lower() if isinstance(key, str) else key
        if key == "r":
            self.reset()
            return
        if self.game_over:
            return
        if raw_key == "Left" or key == "a":
            self.move(-1, 0)
        elif raw_key == "Right" or key == "d":
            self.move(1, 0)
        elif raw_key == "Down" or key == "s":
            if self.move(0, 1):
                self.score += 1
        elif raw_key == "Up" or key == "w":
            rotated = self.rotate()
            if not self.collides(self.px, self.py, rotated):
                self.shape = rotated
        elif key == "space":
            self.hard_drop()
        self.draw()

    def update(self, dt):
        if self.game_over:
            return
        self.elapsed += dt
        if self.elapsed >= self.drop_ms:
            self.elapsed = 0
            self.move(0, 1)
            self.draw()

    def draw(self):
        c = self.app.canvas
        c.delete("all")
        w = self.cols * self.cell
        h = self.rows * self.cell
        x0 = 30
        y0 = 20
        c.create_rectangle(x0 - 2, y0 - 2, x0 + w + 2, y0 + h + 2, outline="#e5e7eb", width=2)

        for y in range(self.rows):
            for x in range(self.cols):
                color = self.board[y][x]
                if color:
                    c.create_rectangle(
                        x0 + x * self.cell,
                        y0 + y * self.cell,
                        x0 + (x + 1) * self.cell,
                        y0 + (y + 1) * self.cell,
                        fill=color,
                        outline="#0b1220",
                    )
                else:
                    c.create_rectangle(
                        x0 + x * self.cell,
                        y0 + y * self.cell,
                        x0 + (x + 1) * self.cell,
                        y0 + (y + 1) * self.cell,
                        outline="#1f2937",
                    )

        for y, row in enumerate(self.shape):
            for x, cell in enumerate(row):
                if cell:
                    c.create_rectangle(
                        x0 + (self.px + x) * self.cell,
                        y0 + (self.py + y) * self.cell,
                        x0 + (self.px + x + 1) * self.cell,
                        y0 + (self.py + y + 1) * self.cell,
                        fill=self.color,
                        outline="#0b1220",
                    )

        c.create_text(360, 60, text=f"Score: {self.score}", fill="white", font=("Segoe UI", 14, "bold"), anchor="w")
        c.create_text(360, 92, text=f"Lines: {self.lines}", fill="#d1d5db", font=("Segoe UI", 12), anchor="w")
        c.create_text(360, 130, text="Make as many lines\nas you can!", fill="#9ca3af", font=("Segoe UI", 11), anchor="nw")

        if self.game_over:
            c.create_rectangle(100, 180, 360, 290, fill="#000000", outline="#fca5a5", width=2)
            c.create_text(230, 220, text="Game Over", fill="#fca5a5", font=("Segoe UI", 20, "bold"))
            c.create_text(230, 260, text="Press R to try again", fill="white", font=("Segoe UI", 12))


class CandyMatch:
    title = "Sweet Match"
    instructions = "Click two neighboring candies to swap. Make 3+ in a row. R: Restart"

    COLORS = ["#fb7185", "#60a5fa", "#34d399", "#f59e0b", "#a78bfa", "#f472b6"]

    def __init__(self, app):
        self.app = app
        self.size = 8
        self.cell = 52
        self.reset()

    def reset(self):
        self.score = 0
        self.moves = 24
        self.target = 1600
        self.selected = None
        self.grid = [[random.randrange(len(self.COLORS)) for _ in range(self.size)] for _ in range(self.size)]
        while self.find_matches():
            self.grid = [[random.randrange(len(self.COLORS)) for _ in range(self.size)] for _ in range(self.size)]
        self.done = False
        self.draw()

    def inside(self, x, y):
        return 0 <= x < self.size and 0 <= y < self.size

    def find_matches(self):
        marks = set()
        for y in range(self.size):
            run = 1
            for x in range(1, self.size + 1):
                if x < self.size and self.grid[y][x] == self.grid[y][x - 1]:
                    run += 1
                else:
                    if run >= 3:
                        for k in range(run):
                            marks.add((x - 1 - k, y))
                    run = 1
        for x in range(self.size):
            run = 1
            for y in range(1, self.size + 1):
                if y < self.size and self.grid[y][x] == self.grid[y - 1][x]:
                    run += 1
                else:
                    if run >= 3:
                        for k in range(run):
                            marks.add((x, y - 1 - k))
                    run = 1
        return marks

    def remove_and_drop(self, marks):
        for x, y in marks:
            self.grid[y][x] = None
        for x in range(self.size):
            col = [self.grid[y][x] for y in range(self.size) if self.grid[y][x] is not None]
            missing = self.size - len(col)
            new_cells = [random.randrange(len(self.COLORS)) for _ in range(missing)]
            final = new_cells + col
            for y in range(self.size):
                self.grid[y][x] = final[y]

    def cascade(self):
        total = 0
        streak = 1
        while True:
            marks = self.find_matches()
            if not marks:
                break
            total += len(marks) * 40 * streak
            self.remove_and_drop(marks)
            streak += 1
        self.score += total

    def try_swap(self, a, b):
        ax, ay = a
        bx, by = b
        self.grid[ay][ax], self.grid[by][bx] = self.grid[by][bx], self.grid[ay][ax]
        if self.find_matches():
            self.cascade()
            self.moves -= 1
        else:
            self.grid[ay][ax], self.grid[by][bx] = self.grid[by][bx], self.grid[ay][ax]

        if self.moves <= 0:
            self.done = True
            if self.score >= self.target:
                self.app.status_var.set("You won Sweet Match! 💖")
            else:
                self.app.status_var.set("Out of moves. Press R to try again.")

    def on_click(self, x, y):
        if self.done:
            return
        gx = (x - 25) // self.cell
        gy = (y - 25) // self.cell
        if not self.inside(gx, gy):
            self.selected = None
            self.draw()
            return

        if self.selected is None:
            self.selected = (gx, gy)
        else:
            sx, sy = self.selected
            if abs(sx - gx) + abs(sy - gy) == 1:
                self.try_swap(self.selected, (gx, gy))
                self.selected = None
            else:
                self.selected = (gx, gy)
        self.draw()

    def on_key(self, key):
        if key == "r":
            self.reset()

    def update(self, dt):
        return

    def draw(self):
        c = self.app.canvas
        c.delete("all")
        x0, y0 = 25, 25
        for y in range(self.size):
            for x in range(self.size):
                color = self.COLORS[self.grid[y][x]]
                c.create_rectangle(
                    x0 + x * self.cell,
                    y0 + y * self.cell,
                    x0 + (x + 1) * self.cell,
                    y0 + (y + 1) * self.cell,
                    fill="#111827",
                    outline="#374151",
                    width=2,
                )
                c.create_oval(
                    x0 + x * self.cell + 8,
                    y0 + y * self.cell + 8,
                    x0 + (x + 1) * self.cell - 8,
                    y0 + (y + 1) * self.cell - 8,
                    fill=color,
                    outline="",
                )

        if self.selected:
            sx, sy = self.selected
            c.create_rectangle(
                x0 + sx * self.cell + 2,
                y0 + sy * self.cell + 2,
                x0 + (sx + 1) * self.cell - 2,
                y0 + (sy + 1) * self.cell - 2,
                outline="#fef08a",
                width=3,
            )

        c.create_text(455, 55, text=f"Score: {self.score}", fill="white", font=("Segoe UI", 14, "bold"), anchor="w")
        c.create_text(455, 90, text=f"Moves: {self.moves}", fill="#d1d5db", font=("Segoe UI", 12), anchor="w")
        c.create_text(455, 125, text=f"Target: {self.target}", fill="#d1d5db", font=("Segoe UI", 12), anchor="w")
        c.create_text(455, 165, text="Match candy\nfor your best score!", fill="#9ca3af", font=("Segoe UI", 11), anchor="nw")


class GoldSquarePush:
    title = "Golden Block"
    instructions = "Arrow keys/WASD move. Push block into gold. Ice slides, sand costs extra, thorn resets. R: Restart  N: Next"

    def __init__(self, app):
        self.app = app
        self.level_num = 1
        self.cell = 56
        self.generate_level(self.level_num)

    def generate_level(self, level_num):
        rng = random.Random()
        w = min(8 + level_num // 4, 12)
        h = min(6 + level_num // 6, 10)
        self.cell = min(56, 650 // w, 380 // h)
        grid = [["." for _ in range(w)] for _ in range(h)]

        for x in range(w):
            grid[0][x] = "#"
            grid[h - 1][x] = "#"
        for y in range(h):
            grid[y][0] = "#"
            grid[y][w - 1] = "#"

        reserved = set()
        if rng.random() < 0.5:
            y = rng.randint(2, h - 3)
            self.player_start = (2, y)
            self.block_start = (3, y)
            self.goal = (w - 3, y)
            for x in range(2, w - 2):
                reserved.add((x, y))
        else:
            x = rng.randint(2, w - 3)
            self.player_start = (x, 2)
            self.block_start = (x, 3)
            self.goal = (x, h - 3)
            for y in range(2, h - 2):
                reserved.add((x, y))

        reserved.add(self.player_start)
        reserved.add(self.block_start)
        reserved.add(self.goal)

        def random_empty():
            for _ in range(200):
                x = rng.randint(1, w - 2)
                y = rng.randint(1, h - 2)
                if (x, y) in reserved:
                    continue
                if grid[y][x] == ".":
                    return x, y
            return None

        wall_count = min(2 + level_num // 3, (w - 2) * (h - 2) // 4)
        for _ in range(wall_count):
            pos = random_empty()
            if not pos:
                break
            x, y = pos
            grid[y][x] = "#"

        rock_count = min(1 + level_num // 5, (w - 2) * (h - 2) // 6)
        for _ in range(rock_count):
            pos = random_empty()
            if not pos:
                break
            x, y = pos
            grid[y][x] = "R"

        ice_count = min(1 + level_num // 2, 10)
        for _ in range(ice_count):
            pos = random_empty()
            if not pos:
                break
            x, y = pos
            grid[y][x] = "I"

        sand_count = min(1 + level_num // 2, 10)
        for _ in range(sand_count):
            pos = random_empty()
            if not pos:
                break
            x, y = pos
            grid[y][x] = "S"

        thorn_count = min(level_num // 4, 8)
        for _ in range(thorn_count):
            pos = random_empty()
            if not pos:
                break
            x, y = pos
            grid[y][x] = "T"

        self.grid = grid
        self.h = h
        self.w = w
        self.reset_state()

    def reset_state(self):
        self.player = self.player_start
        self.block = self.block_start
        self.moves = 0
        self.won = False
        self.draw()

    def reset(self):
        self.reset_state()

    def next_level(self):
        self.level_num += 1
        self.generate_level(self.level_num)
        self.app.status_var.set(f"Welcome to level {self.level_num}! 🌟")

    def walkable(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h and self.grid[y][x] not in ("#", "R")

    def tile_at(self, x, y):
        return self.grid[y][x]

    def apply_tile_effects(self, dx, dy):
        extra_moves = 0
        while True:
            px, py = self.player
            tile = self.tile_at(px, py)
            if tile == "S":
                extra_moves += 1
            if tile == "T":
                self.player = self.player_start
                extra_moves += 2
                break
            if tile != "I":
                break
            nx, ny = px + dx, py + dy
            if not self.walkable(nx, ny) or (nx, ny) == self.block:
                break
            self.player = (nx, ny)

        return extra_moves

    def move(self, dx, dy):
        if self.won:
            return
        px, py = self.player
        nx, ny = px + dx, py + dy
        if not self.walkable(nx, ny):
            return
        if (nx, ny) == self.block:
            bx, by = nx + dx, ny + dy
            if not self.walkable(bx, by) or (bx, by) == self.block:
                return
            self.block = (bx, by)
        self.player = (nx, ny)
        self.moves += 1 + self.apply_tile_effects(dx, dy)
        if self.block == self.goal:
            self.won = True
            self.app.status_var.set(f"Level {self.level_num} solved! Press N for next level.")
        self.draw()

    def on_key(self, key):
        key = key.lower()
        if key in ("left", "a"):
            self.move(-1, 0)
        elif key in ("right", "d"):
            self.move(1, 0)
        elif key in ("up", "w"):
            self.move(0, -1)
        elif key in ("down", "s"):
            self.move(0, 1)
        elif key == "r":
            self.reset()
        elif key == "n":
            if self.won:
                self.next_level()
            else:
                self.app.status_var.set("Solve this level first, then press N.")

    def update(self, dt):
        return

    def draw(self):
        c = self.app.canvas
        c.delete("all")
        board_w = self.w * self.cell
        board_h = self.h * self.cell
        x0 = max(20, (730 - board_w) // 2)
        y0 = max(55, (470 - board_h) // 2 + 30)
        for y in range(self.h):
            for x in range(self.w):
                tile = self.grid[y][x]
                if tile == "#":
                    fill = "#111827"
                elif tile == "R":
                    fill = "#4b5563"
                elif tile == "I":
                    fill = "#60a5fa"
                elif tile == "S":
                    fill = "#b45309"
                elif tile == "T":
                    fill = "#be185d"
                else:
                    fill = "#1f2937"
                c.create_rectangle(
                    x0 + x * self.cell,
                    y0 + y * self.cell,
                    x0 + (x + 1) * self.cell,
                    y0 + (y + 1) * self.cell,
                    fill=fill,
                    outline="#334155",
                )

        gx, gy = self.goal
        c.create_rectangle(
            x0 + gx * self.cell + 8,
            y0 + gy * self.cell + 8,
            x0 + (gx + 1) * self.cell - 8,
            y0 + (gy + 1) * self.cell - 8,
            fill="#fbbf24",
            outline="#fef3c7",
            width=2,
        )

        bx, by = self.block
        c.create_rectangle(
            x0 + bx * self.cell + 8,
            y0 + by * self.cell + 8,
            x0 + (bx + 1) * self.cell - 8,
            y0 + (by + 1) * self.cell - 8,
            fill="#f97316",
            outline="#fed7aa",
            width=2,
        )

        px, py = self.player
        c.create_oval(
            x0 + px * self.cell + 10,
            y0 + py * self.cell + 10,
            x0 + (px + 1) * self.cell - 10,
            y0 + (py + 1) * self.cell - 10,
            fill="#22d3ee",
            outline="#bae6fd",
            width=2,
        )

        c.create_text(35, 20, text=f"Level {self.level_num}/∞", fill="white", font=("Segoe UI", 14, "bold"), anchor="w")
        c.create_text(250, 20, text=f"Moves: {self.moves}", fill="#d1d5db", font=("Segoe UI", 12), anchor="w")
        c.create_text(350, 20, text="I=Ice  S=Sand  T=Thorn  R=Rock", fill="#93c5fd", font=("Segoe UI", 10), anchor="w")
        if self.won:
            c.create_text(620, 20, text="Solved!", fill="#86efac", font=("Segoe UI", 14, "bold"), anchor="w")


class MemoryPairs:
    title = "Memory Pairs"
    instructions = "Click cards to reveal matching pairs. R: Restart"

    def __init__(self, app):
        self.app = app
        self.rows = 4
        self.cols = 4
        self.cell = 90
        self.reset()

    def reset(self):
        symbols = list("AABBCCDDEEFFGGHH")
        random.shuffle(symbols)
        self.grid = [symbols[i * self.cols:(i + 1) * self.cols] for i in range(self.rows)]
        self.revealed = [[False] * self.cols for _ in range(self.rows)]
        self.first = None
        self.locked = False
        self.hide_time = 0
        self.pending = None
        self.moves = 0
        self.matches = 0
        self.draw()

    def on_click(self, x, y):
        if self.locked:
            return
        gx = (x - 120) // self.cell
        gy = (y - 40) // self.cell
        if not (0 <= gx < self.cols and 0 <= gy < self.rows):
            return
        if self.revealed[gy][gx]:
            return

        self.revealed[gy][gx] = True
        if self.first is None:
            self.first = (gx, gy)
        else:
            self.moves += 1
            fx, fy = self.first
            if self.grid[fy][fx] == self.grid[gy][gx]:
                self.matches += 1
                self.first = None
                if self.matches == (self.rows * self.cols) // 2:
                    self.app.status_var.set("Perfect memory! You solved all pairs 💝")
            else:
                self.locked = True
                self.hide_time = 700
                self.pending = ((fx, fy), (gx, gy))
                self.first = None
        self.draw()

    def on_key(self, key):
        if key == "r":
            self.reset()

    def update(self, dt):
        if self.locked:
            self.hide_time -= dt
            if self.hide_time <= 0:
                (a, b) = self.pending
                self.revealed[a[1]][a[0]] = False
                self.revealed[b[1]][b[0]] = False
                self.pending = None
                self.locked = False
                self.draw()

    def draw(self):
        c = self.app.canvas
        c.delete("all")
        x0, y0 = 120, 40
        for y in range(self.rows):
            for x in range(self.cols):
                rx0 = x0 + x * self.cell
                ry0 = y0 + y * self.cell
                rx1 = rx0 + self.cell - 10
                ry1 = ry0 + self.cell - 10
                if self.revealed[y][x]:
                    c.create_rectangle(rx0, ry0, rx1, ry1, fill="#1d4ed8", outline="#bfdbfe", width=2)
                    c.create_text((rx0 + rx1) // 2, (ry0 + ry1) // 2, text=self.grid[y][x], fill="white", font=("Segoe UI", 28, "bold"))
                else:
                    c.create_rectangle(rx0, ry0, rx1, ry1, fill="#334155", outline="#94a3b8", width=2)
                    c.create_text((rx0 + rx1) // 2, (ry0 + ry1) // 2, text="?", fill="#e2e8f0", font=("Segoe UI", 24, "bold"))

        c.create_text(25, 25, text=f"Moves: {self.moves}", fill="white", font=("Segoe UI", 14, "bold"), anchor="w")
        c.create_text(25, 52, text=f"Pairs Found: {self.matches}/8", fill="#d1d5db", font=("Segoe UI", 12), anchor="w")


class SlidingPuzzle:
    title = "Number Slide"
    instructions = "Click a tile next to the blank to slide it. Arrange 1-8 in order. R: Restart level  N: Next level"

    def __init__(self, app):
        self.app = app
        self.size = 3
        self.cell = 120
        self.total_levels = 100
        self.current_level = 1
        self.reset()

    def solved_state(self):
        return [1, 2, 3, 4, 5, 6, 7, 8, 0]

    def neighbors(self, idx):
        x = idx % self.size
        y = idx // self.size
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                yield ny * self.size + nx

    def reset(self):
        self.board = self.solved_state()
        blank = self.board.index(0)
        shuffle_moves = min(90 + self.current_level * 6, 900)
        for _ in range(shuffle_moves):
            n = random.choice(list(self.neighbors(blank)))
            self.board[blank], self.board[n] = self.board[n], self.board[blank]
            blank = n
        self.moves = 0
        self.won = False
        self.draw()

    def next_level(self):
        if self.current_level < self.total_levels:
            self.current_level += 1
            self.app.status_var.set(f"Level {self.current_level}: You got this! 🌟")
            self.reset()
        else:
            self.app.status_var.set("Amazing! You cleared all 100 Number Slide levels! 👑")

    def on_click(self, x, y):
        gx = (x - 170) // self.cell
        gy = (y - 30) // self.cell
        if not (0 <= gx < self.size and 0 <= gy < self.size):
            return
        idx = gy * self.size + gx
        blank = self.board.index(0)
        if idx in self.neighbors(blank):
            self.board[blank], self.board[idx] = self.board[idx], self.board[blank]
            self.moves += 1
            if self.board == self.solved_state():
                self.won = True
                if self.current_level < self.total_levels:
                    self.app.status_var.set(f"Level {self.current_level} cleared! Press N for level {self.current_level + 1}.")
                else:
                    self.app.status_var.set("You solved Number Slide level 100! 🎉")
            self.draw()

    def on_key(self, key):
        key = key.lower() if isinstance(key, str) else key
        if key == "r":
            self.reset()
        elif key == "n" and self.won:
            self.next_level()

    def update(self, dt):
        return

    def draw(self):
        c = self.app.canvas
        c.delete("all")
        x0, y0 = 170, 30
        for i, val in enumerate(self.board):
            x = i % self.size
            y = i // self.size
            rx0 = x0 + x * self.cell
            ry0 = y0 + y * self.cell
            rx1 = rx0 + self.cell - 8
            ry1 = ry0 + self.cell - 8
            if val == 0:
                c.create_rectangle(rx0, ry0, rx1, ry1, fill="#0f172a", outline="#1e293b", width=2)
            else:
                c.create_rectangle(rx0, ry0, rx1, ry1, fill="#14b8a6", outline="#99f6e4", width=2)
                c.create_text((rx0 + rx1) // 2, (ry0 + ry1) // 2, text=str(val), fill="#042f2e", font=("Segoe UI", 34, "bold"))

        c.create_text(20, 30, text=f"Moves: {self.moves}", fill="white", font=("Segoe UI", 14, "bold"), anchor="w")
        c.create_text(20, 58, text=f"Level: {self.current_level}/{self.total_levels}", fill="#d1d5db", font=("Segoe UI", 12), anchor="w")
        if self.won:
            c.create_text(20, 88, text="Solved! Press N for next level", fill="#86efac", font=("Segoe UI", 14, "bold"), anchor="w")


class MomPuzzleCollection:
    def __init__(self, root):
        self.root = root
        self.root.title("Puzzle Gift for Mom 💐")
        self.root.geometry("760x620")
        self.root.configure(bg="#0b1220")

        self.header = tk.Label(
            root,
            text="Puzzle Gift for Mom 💖",
            bg="#0b1220",
            fg="#f9fafb",
            font=("Segoe UI", 20, "bold"),
        )
        self.header.pack(pady=(12, 6))

        self.info_var = tk.StringVar(value="Pick a puzzle mode below")
        self.info_label = tk.Label(root, textvariable=self.info_var, bg="#0b1220", fg="#d1d5db", font=("Segoe UI", 11))
        self.info_label.pack()

        button_frame = tk.Frame(root, bg="#0b1220")
        button_frame.pack(pady=8)

        self.canvas = tk.Canvas(root, width=730, height=470, bg="#0f172a", highlightthickness=0)
        self.canvas.pack(pady=8)

        self.status_var = tk.StringVar(value="Have fun! 🌸")
        self.status_label = tk.Label(root, textvariable=self.status_var, bg="#0b1220", fg="#86efac", font=("Segoe UI", 10, "bold"))
        self.status_label.pack(pady=(0, 8))

        self.games = {
            "Tetris Lite": TetrisLite(self),
            "Sweet Match": CandyMatch(self),
            "Golden Block": GoldSquarePush(self),
            "Memory Pairs": MemoryPairs(self),
            "Number Slide": SlidingPuzzle(self),
        }

        for name in self.games.keys():
            tk.Button(
                button_frame,
                text=name,
                command=lambda n=name: self.start_game(n),
                bg="#1e293b",
                fg="#f8fafc",
                activebackground="#334155",
                activeforeground="white",
                padx=10,
                pady=5,
                relief="flat",
                font=("Segoe UI", 10, "bold"),
            ).pack(side="left", padx=5)

        self.active = None
        self.start_game("Tetris Lite")

        self.root.bind("<Key>", self.on_key)
        self.canvas.bind("<Button-1>", self.on_click)

        self.loop()

    def start_game(self, name):
        self.active = self.games[name]
        self.info_var.set(f"{self.active.title}: {self.active.instructions}")
        self.status_var.set("Have fun! 🌸")
        if hasattr(self.active, "reset"):
            self.active.reset()

    def on_key(self, event):
        if self.active and hasattr(self.active, "on_key"):
            self.active.on_key(event.keysym if len(event.keysym) > 1 else event.char)

    def on_click(self, event):
        if self.active and hasattr(self.active, "on_click"):
            self.active.on_click(event.x, event.y)

    def loop(self):
        dt = 50

        if self.active and hasattr(self.active, "update"):
            self.active.update(dt)
        self.root.after(50, self.loop)


def main():
    root = tk.Tk()
    app = MomPuzzleCollection(root)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        messagebox.showerror("Error", f"Something went wrong:\n{exc}")