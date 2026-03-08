import ctypes
import time

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
VK_F7 = 0x76
VK_F8 = 0x77


def key_pressed(vk: int) -> bool:
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)


def click_once() -> None:
    user32 = ctypes.windll.user32
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def main() -> None:
    interval = 0.004
    print("Hold F7 to click fast. Press F8 to quit.")

    while True:
        if key_pressed(VK_F8):
            print("Exiting.")
            return

        if key_pressed(VK_F7):
            click_once()
            time.sleep(interval)
        else:
            time.sleep(0.01)


if __name__ == "__main__":
    main()
