"""
Bloxd.io Bot — h4x3r plays Minecraft in the browser!
Playwright opens the browser & navigates menus.
User32.dll handles ALL mouse + keyboard (REAL OS-level input).

d0g3 just sits back and watches. 🐢🐢🐢🐢🐢🐢 🦚
"""
import asyncio
import ctypes
import ctypes.wintypes
import sys
import os
import time
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playwright.async_api import async_playwright
import user32_control as u32c

# --- User32 mouse for REAL mouse movement ---
ctypes.windll.shcore.SetProcessDpiAwareness(1)
user32 = ctypes.windll.user32
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010


def mouse_look(dx, dy):
    """Relative mouse movement for looking around (pointer-locked camera)."""
    user32.mouse_event(MOUSEEVENTF_MOVE, int(dx), int(dy), 0, 0)


def mouse_left_down():
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)


def mouse_left_up():
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def mouse_right_click():
    user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)


def get_chrome_hwnd():
    """Find the Chromium/Chrome window playing bloxd.io."""
    results = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            results.append((hwnd, buf.value))
        return True

    user32.EnumWindows(WNDENUMPROC(callback), 0)
    for hwnd, title in results:
        if "bloxd" in title.lower():
            return hwnd, title
    for hwnd, title in results:
        if "chromium" in title.lower() or "chrome" in title.lower():
            return hwnd, title
    return None, None


def focus_game():
    """Bring the game window to the foreground and click center."""
    hwnd, title = get_chrome_hwnd()
    if hwnd:
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.3)
        # Get window center and click to give focus + trigger pointer lock
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        cx = (rect.left + rect.right) // 2
        cy = (rect.top + rect.bottom) // 2
        u32c.click(cx, cy)
        time.sleep(0.5)
        return True
    return False


# ── Game mode buttons on the bloxd.io main page ──
GAME_MODES = [
    "DoodleCube",
    "Survival",
    "BloxdHop",
    "CubeWarfare",
    "EvilTower",
    "CreativeWorld",
]


async def enter_game(page):
    """Navigate menus to get into an actual game using Playwright clicks."""
    print("[h4x3r] Looking for game mode buttons...")

    clicked = False
    for mode in GAME_MODES:
        try:
            btn = await page.query_selector(f'text="{mode}"')
            if btn and await btn.is_visible():
                print(f"[h4x3r] Found game mode: {mode} — clicking!")
                await btn.click()
                clicked = True
                await asyncio.sleep(2)
                break
        except Exception:
            continue

    if not clicked:
        print("[h4x3r] No named mode found, trying any clickable game element...")
        try:
            cards = await page.query_selector_all('[class*="game"], [class*="mode"], [class*="card"]')
            for card in cards:
                if await card.is_visible():
                    await card.click()
                    clicked = True
                    await asyncio.sleep(2)
                    break
        except Exception:
            pass

    if not clicked:
        print("[h4x3r] Clicking center of page as fallback...")
        await page.mouse.click(640, 400)
        await asyncio.sleep(2)

    # Look for Play/Start button
    print("[h4x3r] Looking for Play button...")
    for text in ["Play", "Start", "Join", "Enter", "PLAY", "START"]:
        try:
            btn = await page.query_selector(f'text="{text}"')
            if btn and await btn.is_visible():
                print(f"[h4x3r] Clicking '{text}' button!")
                await btn.click()
                await asyncio.sleep(3)
                break
        except Exception:
            continue

    # Fill name if input exists
    try:
        name_input = await page.query_selector('input[type="text"]')
        if name_input and await name_input.is_visible():
            await name_input.fill("h4x3r")
            print("[h4x3r] Set player name to 'h4x3r'")
            await asyncio.sleep(0.5)
            for text in ["Play", "Start", "Join", "PLAY"]:
                btn = await page.query_selector(f'text="{text}"')
                if btn and await btn.is_visible():
                    await btn.click()
                    await asyncio.sleep(3)
                    break
    except Exception:
        pass


def mine_block(duration=1.5):
    """Hold left click to mine — REAL mouse via User32."""
    mouse_left_down()
    time.sleep(duration)
    mouse_left_up()


def survival_loop(cycles=50):
    """Main game loop using REAL User32 mouse + keyboard."""
    print("\n  === h4x3r SURVIVAL MODE ===")
    print("  REAL mouse + keyboard via User32.dll")
    print("  Press Ctrl+C to stop.\n")

    for i in range(cycles):
        print(f"  Cycle {i+1}/{cycles}")

        # Look around with REAL mouse
        mouse_look(30 + random.randint(-10, 10), random.randint(-5, 5))
        time.sleep(0.2)

        # Walk forward
        u32c.key_down('w')
        time.sleep(1.0 + random.random() * 0.5)
        u32c.key_up('w')

        # Jump every few cycles
        if i % 3 == 0:
            u32c.key_down('w')
            u32c.key_press('space', hold=0.1)
            time.sleep(0.3)
            u32c.key_up('w')

        # Look around more
        mouse_look(random.randint(-40, 40), random.randint(-3, 3))
        time.sleep(0.2)

        # Mine what's in front
        if i % 4 == 0:
            print("    Mining...")
            mine_block(2.0)

        # Strafe occasionally
        if i % 5 == 0:
            key = random.choice(['a', 'd'])
            u32c.key_down(key)
            time.sleep(0.4)
            u32c.key_up(key)

        # Big look around
        if i % 7 == 0:
            mouse_look(random.randint(-60, 60), 0)

        time.sleep(0.3)


async def main():
    print("=" * 50)
    print("  Bloxd.io Bot — h4x3r edition  🐢🐢🐢🐢🐢🐢 🦚")
    print("  Playwright (browser) + User32 (mouse + keyboard)")
    print("=" * 50)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized'],
        )
        context = await browser.new_context(
            no_viewport=True,
            permissions=['notifications'],
        )
        page = await context.new_page()

        print("\n[h4x3r] Opening bloxd.io...")
        await page.goto('https://bloxd.io/', wait_until='domcontentloaded')
        print("[h4x3r] Page loaded! Waiting for it to settle...")
        await asyncio.sleep(5)

        # Screenshot to see what we're working with
        await page.screenshot(path='bloxd_debug.png')
        print("[h4x3r] Saved debug screenshot to bloxd_debug.png")

        # Navigate menus with Playwright
        await enter_game(page)

        # Wait for canvas
        print("[h4x3r] Waiting for game canvas...")
        try:
            await page.wait_for_selector('canvas', timeout=30000)
            print("[h4x3r] Canvas found!")
        except Exception:
            print("[h4x3r] No canvas yet — taking screenshot...")
            await page.screenshot(path='bloxd_debug.png')

        await asyncio.sleep(3)

        # Now switch to User32 for ALL game input!
        # Click the game window to give it focus and trigger pointer lock
        print("[h4x3r] Focusing game window with User32...")
        if focus_game():
            print("[h4x3r] Game focused! Clicking to trigger pointer lock...")
            # Click again to make sure pointer lock activates
            time.sleep(0.5)
            hwnd, _ = get_chrome_hwnd()
            if hwnd:
                rect = ctypes.wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                cx = (rect.left + rect.right) // 2
                cy = (rect.top + rect.bottom) // 2
                u32c.click(cx, cy)
                time.sleep(1)
        else:
            print("[h4x3r] Couldn't find game window!")

        print("[h4x3r] LET'S GO! 🐢🐢🐢🐢🐢🐢 🦚")

        try:
            survival_loop()
        except KeyboardInterrupt:
            print("\n\n  h4x3r stopped! You have control again, d0g3.")
            for key in ['w', 'a', 's', 'd', 'space', 'shift']:
                u32c.key_up(key)
            mouse_left_up()

        print("\n  GG! 🐢🐢🐢🐢🐢🐢 🦚")
        print("  Browser stays open — go explore!")

        try:
            await asyncio.sleep(999999)
        except KeyboardInterrupt:
            pass

        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())


if __name__ == '__main__':
    main()
