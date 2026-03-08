"""Quick probe: take one page screenshot, find board, dump pixel colors at each cell center."""
import time, io, math, sys
from playwright.sync_api import sync_playwright
from PIL import Image

EMPTY_CELL_COLOR = (198, 216, 242)
BOARD_COLS, BOARD_ROWS = 10, 20

def color_distance(c1, c2):
    return math.sqrt(sum((a-b)**2 for a,b in zip(c1,c2)))

def is_empty_cell(r,g,b):
    return color_distance((r,g,b), EMPTY_CELL_COLOR) < 30

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_context(viewport={"width":900,"height":750}).new_page()
    page.goto("https://www.freetetris.org/", wait_until="domcontentloaded")
    time.sleep(5)
    iframe_el = page.query_selector("#gameIFrame")
    iframe_el.click()
    time.sleep(2)
    
    print(">>> Click PLAY, wait for pieces to appear, then press Enter here <<<")
    input()
    
    box = iframe_el.bounding_box()
    data = page.screenshot(type="png")
    full = Image.open(io.BytesIO(data))
    x,y,w,h = int(box['x']),int(box['y']),int(box['width']),int(box['height'])
    img = full.crop((x,y,x+w,y+h))
    img.save("D:\\BuildBot\\tetris_probe.png")
    print(f"Saved tetris_probe.png ({img.size})")
    
    # Find board
    max_x = int(img.width * 0.65)
    exs, eys = [], []
    for yy in range(0, img.height, 4):
        for xx in range(0, max_x, 4):
            r,g,b = img.getpixel((xx,yy))[:3]
            if is_empty_cell(r,g,b):
                exs.append(xx); eys.append(yy)
    exs.sort(); eys.sort()
    trim = max(1, len(exs)//20)
    left,right = exs[trim], exs[-trim]
    top,bottom = eys[trim], eys[-trim]
    cw = (right-left)/BOARD_COLS
    ch = (bottom-top)/BOARD_ROWS
    print(f"Board: ({left},{top})-({right},{bottom}) cell:{cw:.1f}x{ch:.1f}")
    
    # Dump colors at each cell center
    print(f"\n{'':>4}", end="")
    for col in range(BOARD_COLS):
        print(f"  col{col:>2}  ", end="")
    print()
    
    for row in range(BOARD_ROWS):
        cx_list = []
        for col in range(BOARD_COLS):
            cx = int(left + col*cw + cw*0.5)
            cy = int(top + row*ch + ch*0.5)
            r,g,b = img.getpixel((cx,cy))[:3]
            dist = color_distance((r,g,b), EMPTY_CELL_COLOR)
            marker = "." if dist < 30 else f"{r:3d},{g:3d},{b:3d}"
            cx_list.append(marker)
        print(f"r{row:2d} ", end="")
        for m in cx_list:
            print(f"{m:>9} ", end="")
        print()
    
    browser.close()
