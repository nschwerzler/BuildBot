"""
Shape Shifter TD Bot — External auto-player v3
Uses PostMessage to send clicks + keys DIRECTLY to the pygame window.
No focus stealing. Click = SHOOT, Space = MELEE.

Usage:
  1. Launch shape_shifter_td.py and start a game
  2. Run this bot
  3. Ctrl+C to stop
"""
import time, math
import numpy as np
import mss
import win32gui
import win32api

WINDOW_TITLE = "Shape Shifter TD"
GAME_W, GAME_H = 1280, 720

# Win32 message constants
WM_MOUSEMOVE   = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP   = 0x0202
WM_KEYDOWN     = 0x0100
WM_KEYUP       = 0x0101
MK_LBUTTON     = 0x0001

VK_SPACE = 0x20
VK_W = 0x57; VK_A = 0x41; VK_S = 0x53; VK_D = 0x44
VK_Q = 0x51; VK_E = 0x45; VK_R = 0x52; VK_F = 0x46

def MAKELPARAM(x, y):
    return (y << 16) | (x & 0xFFFF)

# ── Window ─────────────────────────────────────────────────────────
def find_window():
    hwnd = win32gui.FindWindow(None, WINDOW_TITLE)
    if hwnd == 0:
        return None, None
    rect = win32gui.GetClientRect(hwnd)
    pt = win32gui.ClientToScreen(hwnd, (rect[0], rect[1]))
    return hwnd, (pt[0], pt[1], rect[2], rect[3])

# ── PostMessage input ──────────────────────────────────────────────
def click_at(hwnd, x, y):
    lp = MAKELPARAM(x, y)
    win32gui.PostMessage(hwnd, WM_MOUSEMOVE, 0, lp)
    win32gui.PostMessage(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp)
    win32gui.PostMessage(hwnd, WM_LBUTTONUP, 0, lp)

def mouse_move(hwnd, x, y):
    win32gui.PostMessage(hwnd, WM_MOUSEMOVE, 0, MAKELPARAM(x, y))

def key_tap(hwnd, vk):
    scan = win32api.MapVirtualKey(vk, 0)
    lp_down = (scan << 16) | 1
    lp_up   = (scan << 16) | 1 | (1 << 30) | (1 << 31)
    win32gui.PostMessage(hwnd, WM_KEYDOWN, vk, lp_down)
    win32gui.PostMessage(hwnd, WM_KEYUP, vk, lp_up)

def key_down(hwnd, vk):
    scan = win32api.MapVirtualKey(vk, 0)
    win32gui.PostMessage(hwnd, WM_KEYDOWN, vk, (scan << 16) | 1)

def key_up(hwnd, vk):
    scan = win32api.MapVirtualKey(vk, 0)
    win32gui.PostMessage(hwnd, WM_KEYUP, vk, (scan << 16) | 1 | (1 << 30) | (1 << 31))

# ── Movement ───────────────────────────────────────────────────────
held = set()

def hold_key(hwnd, vk):
    if vk not in held:
        key_down(hwnd, vk)
        held.add(vk)

def release_key(hwnd, vk):
    if vk in held:
        key_up(hwnd, vk)
        held.discard(vk)

def set_movement(hwnd, dx, dy):
    if dy < -0.3: hold_key(hwnd, VK_W)
    else: release_key(hwnd, VK_W)
    if dy > 0.3: hold_key(hwnd, VK_S)
    else: release_key(hwnd, VK_S)
    if dx < -0.3: hold_key(hwnd, VK_A)
    else: release_key(hwnd, VK_A)
    if dx > 0.3: hold_key(hwnd, VK_D)
    else: release_key(hwnd, VK_D)

def release_all(hwnd):
    for vk in list(held):
        key_up(hwnd, vk)
    held.clear()

# ── Enemy detection ───────────────────────────────────────────────
BASE_GX, BASE_GY = 1160, 360

def find_enemies(frame):
    h, w = frame.shape[:2]
    y0, y1 = 80, h - 60
    x0, x1 = 20, w - 20
    play = frame[y0:y1, x0:x1].astype(np.int16)
    r, g, b = play[:,:,0], play[:,:,1], play[:,:,2]
    sat = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)
    bright = (r + g + b) // 3
    mask = (sat > 40) & (bright > 50)
    base_lx, base_ly = BASE_GX - x0, BASE_GY - y0
    yy, xx = np.ogrid[:play.shape[0], :play.shape[1]]
    mask &= ((xx - base_lx)**2 + (yy - base_ly)**2) > 80**2
    eys, exs = np.where(mask)
    if len(exs) == 0:
        return []
    step = max(1, len(exs) // 400)
    exs, eys = exs[::step], eys[::step]
    pts = list(zip((exs + x0).tolist(), (eys + y0).tolist()))
    clusters = []
    used = set()
    for i, (px, py) in enumerate(pts):
        if i in used: continue
        sx, sy, cnt = px, py, 1
        used.add(i)
        for j in range(i + 1, len(pts)):
            if j in used: continue
            x2, y2 = pts[j]
            if abs(x2 - sx/cnt) < 40 and abs(y2 - sy/cnt) < 40:
                sx += x2; sy += y2; cnt += 1; used.add(j)
        if cnt >= 3:
            clusters.append((sx / cnt, sy / cnt, cnt))
    # Prioritize enemies nearest to base for defense
    clusters.sort(key=lambda c: (c[0] - BASE_GX)**2 + (c[1] - BASE_GY)**2)
    return clusters

# ── Main ───────────────────────────────────────────────────────────
def main():
    print("=" * 50)
    print("  SHAPE SHIFTER TD — BOT v3 (PostMessage)")
    print("  Click=SHOOT  Space=MELEE  Q/E/R=abilities")
    print("=" * 50)

    # Wait for game window
    hwnd, client = None, None
    for _ in range(30):
        hwnd, client = find_window()
        if hwnd:
            break
        time.sleep(1)
    if hwnd is None:
        print(f"ERROR: '{WINDOW_TITLE}' not found! Launch game first.")
        return
    cx, cy, cw, ch = client
    print(f"Window hwnd={hwnd} at ({cx},{cy}) {cw}x{ch}")
    print("BOT ACTIVE — no prompt, attacking NOW!")

    sct = mss.mss()
    fn = 0
    last_shoot = last_melee = 0
    last_ab = [0, 0, 0]
    clicks = melees = 0

    try:
        while True:
            t = time.time()
            fn += 1
            hwnd, client = find_window()
            if client is None:
                print("Window lost!"); break
            cx, cy, cw, ch = client

            monitor = {"left": cx, "top": cy, "width": min(cw, GAME_W), "height": min(ch, GAME_H)}
            raw = sct.grab(monitor)
            frame = np.frombuffer(raw.rgb, dtype=np.uint8).reshape(raw.height, raw.width, 3)
            enemies = find_enemies(frame)
            now = time.time()

            if enemies:
                aim_x, aim_y = int(enemies[0][0]), int(enemies[0][1])
            else:
                aim_x, aim_y = 200, GAME_H // 2
            aim_x = max(10, min(GAME_W - 10, aim_x))
            aim_y = max(10, min(GAME_H - 10, aim_y))

            # AIM
            mouse_move(hwnd, aim_x, aim_y)

            # SHOOT (click)
            if now - last_shoot >= 0.01:
                click_at(hwnd, aim_x, aim_y)
                last_shoot = now; clicks += 1

            # MELEE (space)
            if now - last_melee >= 0.01:
                key_tap(hwnd, VK_SPACE)
                last_melee = now; melees += 1

            # ABILITIES
            for i, vk in enumerate([VK_Q, VK_E, VK_R]):
                if now - last_ab[i] >= 3.0:
                    key_tap(hwnd, vk); last_ab[i] = now

            # CLONE
            if fn % 300 == 0:
                key_tap(hwnd, VK_F)

            # MOVE toward enemies
            if enemies:
                px_est, py_est = GAME_W * 0.6, GAME_H // 2
                dx = aim_x - px_est; dy = aim_y - py_est
                dist = math.hypot(dx, dy)
                if dist > 1:
                    ndx, ndy = dx / dist, dy / dist
                else:
                    ndx, ndy = 0, 0
                if dist > 200: set_movement(hwnd, ndx, ndy)
                elif dist < 50: set_movement(hwnd, -ndx, -ndy)
                else:
                    sd = 1 if int(now) % 3 < 2 else -1
                    set_movement(hwnd, -ndy * sd, ndx * sd)
            else:
                set_movement(hwnd, -0.5, 0)

            if fn % 30 == 0:
                print(f"  [f{fn:>5}] clicks={clicks} melees={melees} enemies={len(enemies)} aim=({aim_x},{aim_y})")

            elapsed = time.time() - t
            if elapsed < 0.05:
                time.sleep(0.05 - elapsed)

    except KeyboardInterrupt:
        pass
    finally:
        release_all(hwnd)
        print(f"\nStopped. frames={fn} clicks={clicks} melees={melees}")

if __name__ == "__main__":
    main()
