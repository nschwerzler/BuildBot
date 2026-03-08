import ctypes
import time

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
VK_F6 = 0x75
VK_F8 = 0x77


def key_pressed(vk: int) -> bool:
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)


def click_once() -> None:
    user32 = ctypes.windll.user32
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def main() -> None:
    clicking = False
    interval = 0.005
    print("F6 = toggle clicker, F8 = quit")

    f6_prev = False
    while True:
        f6_now = key_pressed(VK_F6)
        f8_now = key_pressed(VK_F8)

        if f8_now:
            print("Exiting.")
            return

        if f6_now and not f6_prev:
            clicking = not clicking
            print("Clicking:", "ON" if clicking else "OFF")

        if clicking:
            click_once()
            time.sleep(interval)
        else:
            time.sleep(0.01)

        f6_prev = f6_now


if __name__ == "__main__":
    main()
