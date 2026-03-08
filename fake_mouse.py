"""
Fake Mouse / Pointer Lock Emulator for bloxd.io
Injects JS that overrides requestPointerLock so the game thinks the mouse is
captured, then sends synthetic mousemove events with movementX/Y to look around.
Used with Playwright to let the bot control first-person camera.
"""

# This is the JavaScript payload that gets injected into the page.
# It does three things:
# 1) Overrides requestPointerLock() to instantly "succeed" without a real gesture
# 2) Makes document.pointerLockElement return the canvas
# 3) Provides a global function window.__fakeMouse(dx, dy) to send look-around events

POINTER_LOCK_PATCH_JS = """
(function() {
    if (window.__fakeMouseInstalled) return 'already installed';

    let _lockedElement = null;

    // Override requestPointerLock on all elements
    const origRequestPointerLock = Element.prototype.requestPointerLock;
    Element.prototype.requestPointerLock = function() {
        _lockedElement = this;
        // Fire the pointerlockchange event so the game knows lock is active
        document.dispatchEvent(new Event('pointerlockchange'));
        console.log('[FakeMouse] Pointer lock granted on', this.tagName);
    };

    // Override exitPointerLock
    const origExitPointerLock = document.exitPointerLock;
    document.exitPointerLock = function() {
        _lockedElement = null;
        document.dispatchEvent(new Event('pointerlockchange'));
        console.log('[FakeMouse] Pointer lock released');
    };

    // Override pointerLockElement getter
    Object.defineProperty(document, 'pointerLockElement', {
        get: function() { return _lockedElement; },
        configurable: true
    });

    // Also patch mozPointerLockElement and webkitPointerLockElement
    Object.defineProperty(document, 'mozPointerLockElement', {
        get: function() { return _lockedElement; },
        configurable: true
    });
    Object.defineProperty(document, 'webkitPointerLockElement', {
        get: function() { return _lockedElement; },
        configurable: true
    });

    // Global function to send fake mouse movement (dx, dy in pixels)
    // This simulates the mouse moving by (dx, dy) while pointer-locked
    window.__fakeMouse = function(dx, dy) {
        if (!_lockedElement) return false;
        const evt = new MouseEvent('mousemove', {
            bubbles: true,
            cancelable: true,
            movementX: dx,
            movementY: dy,
            clientX: 0,
            clientY: 0,
            screenX: 0,
            screenY: 0
        });
        _lockedElement.dispatchEvent(evt);
        return true;
    };

    // Send fake mouse click (for attacking / placing blocks)
    window.__fakeClick = function(button) {
        // button: 0=left, 2=right
        if (!_lockedElement) return false;
        const downEvt = new MouseEvent('mousedown', {
            bubbles: true, cancelable: true, button: button || 0
        });
        const upEvt = new MouseEvent('mouseup', {
            bubbles: true, cancelable: true, button: button || 0
        });
        _lockedElement.dispatchEvent(downEvt);
        _lockedElement.dispatchEvent(upEvt);
        if ((button || 0) === 0) {
            _lockedElement.dispatchEvent(new MouseEvent('click', {
                bubbles: true, cancelable: true, button: 0
            }));
        }
        return true;
    };

    // Force-lock the pointer on whichever canvas exists
    window.__forcePointerLock = function() {
        const canvas = document.querySelector('canvas');
        if (canvas) {
            _lockedElement = canvas;
            document.dispatchEvent(new Event('pointerlockchange'));
            console.log('[FakeMouse] Force-locked to canvas');
            return true;
        }
        return false;
    };

    // Check lock status
    window.__isPointerLocked = function() {
        return _lockedElement !== null;
    };

    window.__fakeMouseInstalled = true;
    console.log('[FakeMouse] Pointer lock emulator installed');
    return 'installed';
})();
"""


def get_patch_js():
    """Return the JS payload string to inject via page.evaluate()."""
    return POINTER_LOCK_PATCH_JS


# ── Standalone demo: opens bloxd.io with Playwright + fake mouse ──
if __name__ == '__main__':
    import asyncio
    from playwright.async_api import async_playwright

    async def main():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                # Grant all permissions the game might need
                permissions=['notifications'],
            )
            page = await context.new_page()

            # Inject the pointer lock patch BEFORE navigation so it's ready
            await page.add_init_script(POINTER_LOCK_PATCH_JS)

            print('[FakeMouse] Navigating to bloxd.io...')
            await page.goto('https://bloxd.io/', wait_until='domcontentloaded')
            print('[FakeMouse] Page loaded. Waiting for canvas...')

            # Wait for the game canvas to appear
            await page.wait_for_selector('canvas', timeout=30000)
            print('[FakeMouse] Canvas found!')

            # Force pointer lock onto the canvas
            result = await page.evaluate('window.__forcePointerLock()')
            print(f'[FakeMouse] Force lock result: {result}')

            # Demo: look around in a circle
            print('[FakeMouse] Demo: spinning camera...')
            for i in range(100):
                await page.evaluate('window.__fakeMouse(5, 0)')  # look right
                await asyncio.sleep(0.02)

            print('[FakeMouse] Demo complete. Browser stays open.')
            print('Press Ctrl+C to exit.')
            try:
                await asyncio.sleep(999999)
            except KeyboardInterrupt:
                pass
            await browser.close()

    asyncio.run(main())
