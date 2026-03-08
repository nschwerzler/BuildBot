"""Find desktop icon positions using Windows Shell ListView API."""
import ctypes
from ctypes import wintypes
import struct
import json

ctypes.windll.shcore.SetProcessDpiAwareness(1)
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def find_desktop_listview():
    progman = user32.FindWindowW('Progman', None)
    defview = user32.FindWindowExW(progman, 0, 'SHELLDLL_DefView', None)
    if defview:
        lv = user32.FindWindowExW(defview, 0, 'SysListView32', None)
        if lv:
            return lv
    worker = 0
    while True:
        worker = user32.FindWindowExW(0, worker, 'WorkerW', None)
        if not worker:
            break
        defview = user32.FindWindowExW(worker, 0, 'SHELLDLL_DefView', None)
        if defview:
            lv = user32.FindWindowExW(defview, 0, 'SysListView32', None)
            if lv:
                return lv
    return None

lv = find_desktop_listview()
print(f"ListView HWND: {lv}")

if not lv:
    print("Could not find desktop ListView!")
    exit(1)

LVM_GETITEMCOUNT = 0x1004
LVM_GETITEMPOSITION = 0x1010
LVM_GETITEMTEXTW = 0x1073

count = user32.SendMessageW(lv, LVM_GETITEMCOUNT, 0, 0)
print(f"Icon count: {count}")

pid = wintypes.DWORD()
user32.GetWindowThreadProcessId(lv, ctypes.byref(pid))

PROCESS_ALL_ACCESS = 0x1F0FFF
hProcess = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid.value)
if not hProcess:
    print(f"Failed to open explorer process: {ctypes.GetLastError()}")
    exit(1)

MEM_COMMIT = 0x1000
MEM_RELEASE = 0x8000
PAGE_READWRITE = 0x04

pPoint = kernel32.VirtualAllocEx(hProcess, 0, 8, MEM_COMMIT, PAGE_READWRITE)
pItem = kernel32.VirtualAllocEx(hProcess, 0, 580, MEM_COMMIT, PAGE_READWRITE)

icons = []
for i in range(count):
    # Get position
    user32.SendMessageW(lv, LVM_GETITEMPOSITION, i, pPoint)
    point_buf = (ctypes.c_byte * 8)()
    bytesRead = ctypes.c_size_t()
    kernel32.ReadProcessMemory(hProcess, pPoint, point_buf, 8, ctypes.byref(bytesRead))
    x, y = struct.unpack('ii', bytes(point_buf))

    # Get text
    text_ptr = pItem + 60
    lvitem_data = bytearray(60)
    struct.pack_into('I', lvitem_data, 0, 0x0001)  # LVIF_TEXT
    struct.pack_into('i', lvitem_data, 4, i)
    struct.pack_into('i', lvitem_data, 8, 0)
    struct.pack_into('Q', lvitem_data, 24, text_ptr)  # pszText (64-bit)
    struct.pack_into('i', lvitem_data, 32, 260)

    written = ctypes.c_size_t()
    kernel32.WriteProcessMemory(hProcess, pItem, bytes(lvitem_data), 60, ctypes.byref(written))
    user32.SendMessageW(lv, LVM_GETITEMTEXTW, i, pItem)

    text_buf = (ctypes.c_byte * 520)()
    kernel32.ReadProcessMemory(hProcess, text_ptr, text_buf, 520, ctypes.byref(bytesRead))
    text = bytes(text_buf).decode('utf-16-le').rstrip('\x00')

    print(f'  [{i}] "{text}" at ({x}, {y})')
    icons.append({"name": text, "x": x, "y": y})

kernel32.VirtualFreeEx(hProcess, pPoint, 0, MEM_RELEASE)
kernel32.VirtualFreeEx(hProcess, pItem, 0, MEM_RELEASE)
kernel32.CloseHandle(hProcess)

# Save for later use
with open(r"D:\BuildBot\desktop_icons.json", "w") as f:
    json.dump(icons, f, indent=2)
print(f"\nSaved {len(icons)} icon positions to desktop_icons.json")
