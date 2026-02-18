"""
CODER TYCOON - 2.5D Edition
Walk around your house, code at the computer, buy robots,
keep rooms clean, survive inspector visits every 152 min!
"""

import pygame, sys, os, json, math, random

pygame.init()
W, H = 1280, 720
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Coder Tycoon")
clock = pygame.time.Clock()
FPS = 60

# ═══════════════════════════════════════════════════════════════════
#  FONTS
# ═══════════════════════════════════════════════════════════════════
def mkf(sz):
    for n in ["Consolas","Courier New","monospace"]:
        try: return pygame.font.SysFont(n, sz)
        except: continue
    return pygame.font.Font(None, sz)

FT  = mkf(12)
FS  = mkf(15)
FM  = mkf(19)
FL  = mkf(26)
FXL = mkf(38)
FTI = mkf(52)

def dtxt(sf, txt, font, col, x, y, anchor="topleft", shadow=False):
    if shadow:
        s = font.render(str(txt), True, (0,0,0))
        r = s.get_rect(**{anchor:(x+2,y+2)}); sf.blit(s,r)
    t = font.render(str(txt), True, col)
    r = t.get_rect(**{anchor:(x,y)}); sf.blit(t,r)
    return r

# ═══════════════════════════════════════════════════════════════════
#  COLORS
# ═══════════════════════════════════════════════════════════════════
BG       = (22, 24, 35)
C_FLOOR  = (60, 55, 50)
C_FLOOR2 = (55, 50, 45)
C_WALL   = (80, 75, 68)
C_WALL_T = (95, 88, 78)
C_WHITE  = (235, 235, 235)
C_GRAY   = (140, 140, 150)
C_DGRAY  = (70, 70, 80)
C_GOLD   = (255, 215, 60)
C_GREEN  = (80, 220, 100)
C_RED    = (220, 70, 70)
C_BLUE   = (70, 140, 255)
C_CYAN   = (60, 220, 220)
C_PURPLE = (170, 80, 255)
C_ORANGE = (255, 160, 50)
C_PINK   = (255, 120, 180)
C_TEAL   = (50, 180, 170)
C_LIME   = (160, 255, 80)
C_BROWN  = (140, 90, 50)
C_YELLOW = (255, 240, 80)
C_DIRT   = (100, 75, 40)
C_DIRT2  = (80, 60, 30)
C_SPARK  = (255, 255, 120)
C_ROBOT  = (100, 200, 220)

# ═══════════════════════════════════════════════════════════════════
#  TIME
# ═══════════════════════════════════════════════════════════════════
SECS_PER_DAY = 300.0
DAYS_PER_MONTH = 30
INSPECTOR_INTERVAL = 152.0 * 60.0  # 152 real minutes

# ═══════════════════════════════════════════════════════════════════
#  WORLD MAP - tile-based 2.5D
# ═══════════════════════════════════════════════════════════════════
TILE = 48
ISO_ANGLE = 0.5
MAP_W, MAP_H = 22, 16

ROOMS = {
    "kitchen":     {"name":"Kitchen",     "rect":(1,1,6,4),   "col":C_ORANGE, "floor":(65,58,48)},
    "living_room": {"name":"Living Room", "rect":(8,1,7,4),   "col":C_BLUE,   "floor":(58,55,52)},
    "bathroom":    {"name":"Bathroom",    "rect":(16,1,5,4),  "col":C_CYAN,   "floor":(55,65,65)},
    "bedroom":     {"name":"Bedroom",     "rect":(1,6,6,5),   "col":C_PURPLE, "floor":(62,55,65)},
    "office":      {"name":"Office",      "rect":(8,6,7,5),   "col":C_TEAL,   "floor":(50,60,58)},
    "yard":        {"name":"Yard",        "rect":(16,6,5,5),  "col":C_GREEN,  "floor":(45,65,35)},
    "garage":      {"name":"Garage",      "rect":(1,12,6,3),  "col":C_BROWN,  "floor":(55,50,45)},
    "shop":        {"name":"Shop",        "rect":(8,12,7,3),  "col":C_GOLD,   "floor":(65,60,45)},
    # Hallways connecting rooms horizontally
    "hall_h1":     {"name":"", "rect":(7,1,1,4),   "col":C_GRAY, "floor":(50,48,44)},
    "hall_h2":     {"name":"", "rect":(15,1,1,4),  "col":C_GRAY, "floor":(50,48,44)},
    "hall_h3":     {"name":"", "rect":(7,6,1,5),   "col":C_GRAY, "floor":(50,48,44)},
    "hall_h4":     {"name":"", "rect":(15,6,1,5),  "col":C_GRAY, "floor":(50,48,44)},
    "hall_h5":     {"name":"", "rect":(7,12,1,3),  "col":C_GRAY, "floor":(50,48,44)},
    # Hallways connecting rooms vertically
    "hall_v1":     {"name":"", "rect":(1,5,6,1),   "col":C_GRAY, "floor":(50,48,44)},
    "hall_v2":     {"name":"", "rect":(8,5,7,1),   "col":C_GRAY, "floor":(50,48,44)},
    "hall_v3":     {"name":"", "rect":(16,5,5,1),  "col":C_GRAY, "floor":(50,48,44)},
    "hall_v4":     {"name":"", "rect":(1,11,6,1),  "col":C_GRAY, "floor":(50,48,44)},
    "hall_v5":     {"name":"", "rect":(8,11,7,1),  "col":C_GRAY, "floor":(50,48,44)},
    # Corner connectors
    "hall_c1":     {"name":"", "rect":(7,5,1,1),   "col":C_GRAY, "floor":(50,48,44)},
    "hall_c2":     {"name":"", "rect":(15,5,1,1),  "col":C_GRAY, "floor":(50,48,44)},
    "hall_c3":     {"name":"", "rect":(7,11,1,1),  "col":C_GRAY, "floor":(50,48,44)},
    "hall_c4":     {"name":"", "rect":(15,11,1,1), "col":C_GRAY, "floor":(50,48,44)},
}
ROOM_ORDER = ["hall_h1","hall_h2","hall_h3","hall_h4","hall_h5",
              "hall_v1","hall_v2","hall_v3","hall_v4","hall_v5",
              "hall_c1","hall_c2","hall_c3","hall_c4",
              "kitchen","living_room","bathroom","bedroom","office","yard","garage","shop"]
CLEAN_ROOMS = ["kitchen","living_room","bathroom","bedroom","office","yard","garage"]

FURNITURE = [
    {"type":"stove",   "room":"kitchen",    "tx":1,"ty":0, "w":2,"h":1, "col":(80,80,80),  "label":"Stove",   "breakable":True},
    {"type":"fridge",  "room":"kitchen",    "tx":4,"ty":0, "w":1,"h":1, "col":(200,200,210),"label":"Fridge",  "breakable":True},
    {"type":"sink_k",  "room":"kitchen",    "tx":3,"ty":0, "w":1,"h":1, "col":(150,180,200),"label":"Sink",    "breakable":True},
    {"type":"table",   "room":"kitchen",    "tx":1,"ty":2, "w":3,"h":1, "col":(140,100,60), "label":"Table",   "breakable":False},
    {"type":"couch",   "room":"living_room","tx":1,"ty":1, "w":3,"h":1, "col":(100,70,120), "label":"Couch",   "breakable":False},
    {"type":"tv",      "room":"living_room","tx":2,"ty":0, "w":2,"h":1, "col":(40,40,50),   "label":"TV",      "breakable":True},
    {"type":"shelf",   "room":"living_room","tx":5,"ty":0, "w":1,"h":2, "col":(120,90,50),  "label":"Shelf",   "breakable":False},
    {"type":"toilet",  "room":"bathroom",   "tx":1,"ty":0, "w":1,"h":1, "col":(220,220,230),"label":"Toilet",  "breakable":True},
    {"type":"shower",  "room":"bathroom",   "tx":3,"ty":0, "w":1,"h":2, "col":(170,200,220),"label":"Shower",  "breakable":True},
    {"type":"sink_b",  "room":"bathroom",   "tx":1,"ty":2, "w":1,"h":1, "col":(180,200,210),"label":"Sink",    "breakable":True},
    {"type":"bed",     "room":"bedroom",    "tx":1,"ty":1, "w":2,"h":2, "col":(100,60,80),  "label":"Bed",     "breakable":False},
    {"type":"dresser", "room":"bedroom",    "tx":4,"ty":0, "w":1,"h":1, "col":(130,95,55),  "label":"Dresser", "breakable":False},
    {"type":"lamp",    "room":"bedroom",    "tx":0,"ty":0, "w":1,"h":1, "col":(220,200,100),"label":"Lamp",    "breakable":True},
    {"type":"computer","room":"office",     "tx":2,"ty":1, "w":2,"h":1, "col":(50,50,65),   "label":"Computer","breakable":True},
    {"type":"chair",   "room":"office",     "tx":2,"ty":2, "w":1,"h":1, "col":(80,80,90),   "label":"Chair",   "breakable":False},
    {"type":"bookcase","room":"office",     "tx":5,"ty":0, "w":1,"h":2, "col":(110,80,45),  "label":"Books",   "breakable":False},
    {"type":"garden",  "room":"yard",       "tx":1,"ty":1, "w":2,"h":2, "col":(60,130,50),  "label":"Garden",  "breakable":False},
    {"type":"mailbox", "room":"yard",       "tx":3,"ty":0, "w":1,"h":1, "col":(60,60,180),  "label":"Mailbox", "breakable":False},
    {"type":"workbench","room":"garage",    "tx":1,"ty":0, "w":2,"h":1, "col":(100,85,60),  "label":"Workbench","breakable":True},
    {"type":"tools",   "room":"garage",     "tx":4,"ty":0, "w":1,"h":1, "col":(160,160,170),"label":"Tools",   "breakable":False},
    {"type":"register","room":"shop",       "tx":3,"ty":1, "w":1,"h":1, "col":(200,180,50), "label":"Shop",    "breakable":False},
    {"type":"shelf_s1","room":"shop",       "tx":0,"ty":0, "w":1,"h":2, "col":(130,100,60), "label":"Shelf",   "breakable":False},
    {"type":"shelf_s2","room":"shop",       "tx":6,"ty":0, "w":1,"h":2, "col":(130,100,60), "label":"Shelf",   "breakable":False},
]

# ═══════════════════════════════════════════════════════════════════
#  ROBOTS
# ═══════════════════════════════════════════════════════════════════
ROBOT_DB = {
    "cleaner_bot":   {"name":"Cleaner Bot",   "desc":"Kitchen, Living, Bath",   "rooms":["kitchen","living_room","bathroom"],
                      "power":1.0, "cost":500,  "col":C_CYAN,   "icon":"C"},
    "yard_bot":      {"name":"Yard Bot",      "desc":"Yard specialist",          "rooms":["yard"],
                      "power":1.5, "cost":400,  "col":C_GREEN,  "icon":"Y"},
    "office_bot":    {"name":"Office Bot",    "desc":"Keeps office clean",       "rooms":["office"],
                      "power":1.3, "cost":350,  "col":C_TEAL,   "icon":"O"},
    "handy_bot":     {"name":"Handy Bot",     "desc":"Garage + repairs",         "rooms":["garage"],
                      "power":1.3, "cost":300,  "col":C_BROWN,  "icon":"H"},
    "bedroom_bot":   {"name":"Bedroom Bot",   "desc":"Bedroom tidy",             "rooms":["bedroom"],
                      "power":1.2, "cost":350,  "col":C_PURPLE, "icon":"B"},
    "super_cleaner": {"name":"Super Cleaner", "desc":"ALL rooms, 2x",            "rooms":["kitchen","living_room","bathroom","bedroom","office","yard","garage"],
                      "power":2.0, "cost":2000, "col":C_GOLD,   "icon":"S"},
    "repair_bot":    {"name":"Repair Bot",    "desc":"Fixes broken items!",      "rooms":[],
                      "power":0.0, "cost":1500, "col":C_SPARK,  "icon":"R"},
    "mega_bot":      {"name":"Mega Bot",      "desc":"ALL rooms 4x + repair",    "rooms":["kitchen","living_room","bathroom","bedroom","office","yard","garage"],
                      "power":4.0, "cost":5000, "col":C_YELLOW, "icon":"M"},
}
ROBOT_ORDER = ["cleaner_bot","yard_bot","office_bot","handy_bot","bedroom_bot","super_cleaner","repair_bot","mega_bot"]

# ═══════════════════════════════════════════════════════════════════
#  GAME PROJECTS
# ═══════════════════════════════════════════════════════════════════
GAME_PROJECTS = [
    {"name":"Pixel Pong",       "work":100,  "pay":200,  "col":C_GREEN},
    {"name":"Snake Remix",      "work":180,  "pay":350,  "col":C_LIME},
    {"name":"Space Blaster",    "work":300,  "pay":600,  "col":C_BLUE},
    {"name":"Dungeon Crawler",  "work":500,  "pay":1000, "col":C_PURPLE},
    {"name":"RPG Quest",        "work":800,  "pay":1800, "col":C_ORANGE},
    {"name":"City Builder",     "work":1200, "pay":2800, "col":C_TEAL},
    {"name":"MMO Lite",         "work":2000, "pay":5000, "col":C_PINK},
    {"name":"Open World Epic",  "work":3500, "pay":9000, "col":C_GOLD},
    {"name":"VR Masterpiece",   "work":5000, "pay":14000,"col":C_CYAN},
    {"name":"AAA Blockbuster",  "work":8000, "pay":25000,"col":C_YELLOW},
]

# ═══════════════════════════════════════════════════════════════════
#  UPGRADES
# ═══════════════════════════════════════════════════════════════════
UPGRADES = {
    "coffee_machine":  {"name":"Coffee Machine",  "desc":"+15% code speed",  "cost":400,  "stat":"code_speed","val":0.15},
    "better_keyboard": {"name":"Better Keyboard", "desc":"+25% code speed",  "cost":600,  "stat":"code_speed","val":0.25},
    "ergonomic_chair": {"name":"Ergonomic Chair", "desc":"+20% code speed",  "cost":800,  "stat":"code_speed","val":0.20},
    "dual_monitors":   {"name":"Dual Monitors",   "desc":"+30% code speed",  "cost":1500, "stat":"code_speed","val":0.30},
    "robot_oil":       {"name":"Robot Oil",        "desc":"+30% robot speed", "cost":700,  "stat":"robot_eff", "val":0.30},
    "smart_home":      {"name":"Smart Home Hub",   "desc":"+40% robot speed", "cost":2000, "stat":"robot_eff", "val":0.40},
    "ai_assistant":    {"name":"AI Assistant",     "desc":"+50% code speed",  "cost":3000, "stat":"code_speed","val":0.50},
    "auto_coder":      {"name":"Auto-Coder",       "desc":"Passive code 1/s", "cost":5000, "stat":"auto_code", "val":1.0},
}
UPGRADE_ORDER = ["coffee_machine","better_keyboard","ergonomic_chair","dual_monitors",
                 "robot_oil","smart_home","ai_assistant","auto_coder"]

# ═══════════════════════════════════════════════════════════════════
#  GAME STATE
# ═══════════════════════════════════════════════════════════════════
SAVE_FILE = "coder_tycoon_save.json"
state = "title"

money = 1000
game_time = 0.0
total_games = 0
total_inspections = 0
total_earned = 0
inspect_timer = INSPECTOR_INTERVAL

player = {"x": 10.0 * TILE, "y": 8.0 * TILE, "spd": 160.0, "facing": "down"}
cam = {"x": 0.0, "y": 0.0}

rooms_clean = {r: 100.0 for r in CLEAN_ROOMS}
dirt_spots = {r: [] for r in CLEAN_ROOMS}
broken_set = set()
break_timers = {}

owned_robots = []
robot_entities = []

owned_upgrades = set()
code_speed_bonus = 0.0
robot_eff_bonus = 0.0
auto_code_rate = 0.0

current_project = None
project_progress = 0.0
code_combo = 0
code_combo_timer = 0.0

shop_open = False
shop_tab = 0
shop_scroll = 0
project_menu = False
notifications = []
particles = []
inspector_active = False
inspector_result = {}
inspector_show_timer = 0.0
auto_save_timer = 60.0

# ═══════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════
def add_notif(text, col=C_WHITE, dur=3.0):
    notifications.append({"text":text,"col":col,"life":dur,"max":dur})

def tile_to_screen(tx, ty):
    sx = tx * TILE - cam["x"]
    sy = ty * TILE * ISO_ANGLE - cam["y"]
    return sx, sy

def screen_to_tile(sx, sy):
    tx = (sx + cam["x"]) / TILE
    ty = (sy + cam["y"]) / (TILE * ISO_ANGLE)
    return tx, ty

def get_room_at_tile(tx, ty):
    for rid, rd in ROOMS.items():
        rx, ry, rw, rh = rd["rect"]
        if rx <= tx < rx + rw and ry <= ty < ry + rh:
            return rid
    return None

def get_room_at_player():
    tx = player["x"] / TILE
    ty = player["y"] / TILE
    return get_room_at_tile(tx, ty)

def player_near_furniture(ftype, dist=2.0):
    px, py = player["x"] / TILE, player["y"] / TILE
    for i, f in enumerate(FURNITURE):
        if f["type"] == ftype:
            rd = ROOMS[f["room"]]["rect"]
            fx = rd[0] + f["tx"] + f["w"] / 2
            fy = rd[1] + f["ty"] + f["h"] / 2
            d = math.hypot(px - fx, py - fy)
            if d < dist:
                return True
    return False

def get_furn_world_pos(f):
    rd = ROOMS[f["room"]]["rect"]
    return rd[0] + f["tx"], rd[1] + f["ty"]

def get_time_display():
    total_days = int(game_time / SECS_PER_DAY)
    dim = (total_days % DAYS_PER_MONTH) + 1
    month = (total_days // DAYS_PER_MONTH) + 1
    year = ((month - 1) // 12) + 1
    miy = ((month - 1) % 12) + 1
    frac = (game_time % SECS_PER_DAY) / SECS_PER_DAY
    hour = int(frac * 24)
    minute = int((frac * 24 - hour) * 60)
    per = "AM" if hour < 12 else "PM"
    dh = hour % 12
    if dh == 0: dh = 12
    mnames = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    return dim, mnames[miy-1], year, f"{dh}:{minute:02d} {per}"

def get_house_score():
    if not CLEAN_ROOMS: return 100.0
    total = sum(rooms_clean[r] for r in CLEAN_ROOMS) / len(CLEAN_ROOMS)
    broken_penalty = len(broken_set) * 3
    return max(0, min(100, total - broken_penalty))

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

# ═══════════════════════════════════════════════════════════════════
#  SAVE / LOAD
# ═══════════════════════════════════════════════════════════════════
def save_data():
    try:
        d = {
            "money":money, "game_time":game_time, "total_games":total_games,
            "total_inspections":total_inspections, "total_earned":total_earned,
            "inspect_timer":inspect_timer,
            "player_x":player["x"], "player_y":player["y"],
            "rooms_clean":rooms_clean,
            "broken_set":list(broken_set),
            "owned_robots":owned_robots,
            "owned_upgrades":list(owned_upgrades),
            "current_project":current_project, "project_progress":project_progress,
            "code_speed_bonus":code_speed_bonus, "robot_eff_bonus":robot_eff_bonus,
            "auto_code_rate":auto_code_rate,
        }
        with open(SAVE_FILE,"w") as f: json.dump(d,f)
        return True
    except: return False

def load_data():
    global money, game_time, total_games, total_inspections, total_earned
    global inspect_timer, rooms_clean, broken_set, owned_robots, owned_upgrades
    global current_project, project_progress, code_speed_bonus, robot_eff_bonus, auto_code_rate
    if not os.path.exists(SAVE_FILE): return False
    try:
        with open(SAVE_FILE) as f: d = json.load(f)
        money = d.get("money",1000)
        game_time = d.get("game_time",0)
        total_games = d.get("total_games",0)
        total_inspections = d.get("total_inspections",0)
        total_earned = d.get("total_earned",0)
        inspect_timer = d.get("inspect_timer", INSPECTOR_INTERVAL)
        player["x"] = d.get("player_x", 10*TILE)
        player["y"] = d.get("player_y", 8*TILE)
        for r in CLEAN_ROOMS:
            rooms_clean[r] = d.get("rooms_clean",{}).get(r, 100.0)
        broken_set.clear()
        broken_set.update(d.get("broken_set",[]))
        owned_robots.clear(); owned_robots.extend(d.get("owned_robots",[]))
        owned_upgrades.clear(); owned_upgrades.update(d.get("owned_upgrades",[]))
        current_project = d.get("current_project")
        project_progress = d.get("project_progress",0)
        code_speed_bonus = d.get("code_speed_bonus",0)
        robot_eff_bonus = d.get("robot_eff_bonus",0)
        auto_code_rate = d.get("auto_code_rate",0)
        rebuild_robots()
        return True
    except: return False

def has_save():
    return os.path.exists(SAVE_FILE)

def new_game():
    global money, game_time, total_games, total_inspections, total_earned
    global inspect_timer, current_project, project_progress
    global code_speed_bonus, robot_eff_bonus, auto_code_rate
    global shop_open, shop_tab, project_menu, inspector_active, inspector_show_timer
    global code_combo, code_combo_timer, auto_save_timer
    money = 1000; game_time = 0; total_games = 0; total_inspections = 0; total_earned = 0
    inspect_timer = INSPECTOR_INTERVAL
    player["x"] = 10*TILE; player["y"] = 8*TILE
    for r in CLEAN_ROOMS: rooms_clean[r] = 100.0
    for r in CLEAN_ROOMS: dirt_spots[r] = []
    broken_set.clear(); break_timers.clear()
    owned_robots.clear(); robot_entities.clear()
    owned_upgrades.clear()
    code_speed_bonus = 0; robot_eff_bonus = 0; auto_code_rate = 0
    current_project = None; project_progress = 0
    shop_open = False; shop_tab = 0; project_menu = False
    inspector_active = False; inspector_show_timer = 0
    code_combo = 0; code_combo_timer = 0
    auto_save_timer = 60.0
    notifications.clear(); particles.clear()

# ═══════════════════════════════════════════════════════════════════
#  ROBOT VISUAL ENTITIES
# ═══════════════════════════════════════════════════════════════════
def rebuild_robots():
    robot_entities.clear()
    for rid in owned_robots:
        rb = ROBOT_DB[rid]
        if rb["rooms"]:
            room = random.choice(rb["rooms"])
        else:
            room = random.choice(CLEAN_ROOMS)
        rd = ROOMS[room]["rect"]
        rx = (rd[0] + random.uniform(0.5, rd[2]-0.5)) * TILE
        ry = (rd[1] + random.uniform(0.5, rd[3]-0.5)) * TILE
        robot_entities.append({
            "type": rid, "x": rx, "y": ry,
            "target_x": rx, "target_y": ry,
            "room": room, "move_timer": random.uniform(1,4),
            "col": rb["col"],
        })

def spawn_robot_entity(rid):
    rb = ROBOT_DB[rid]
    if rb["rooms"]:
        room = random.choice(rb["rooms"])
    else:
        room = random.choice(CLEAN_ROOMS)
    rd = ROOMS[room]["rect"]
    rx = (rd[0] + random.uniform(0.5, rd[2]-0.5)) * TILE
    ry = (rd[1] + random.uniform(0.5, rd[3]-0.5)) * TILE
    robot_entities.append({
        "type":rid, "x":rx, "y":ry,
        "target_x":rx, "target_y":ry,
        "room":room, "move_timer":random.uniform(1,4),
        "col":rb["col"],
    })

# ═══════════════════════════════════════════════════════════════════
#  UPDATE
# ═══════════════════════════════════════════════════════════════════
def update_game(dt):
    global game_time, inspect_timer, money, project_progress, current_project
    global total_games, total_earned, inspector_active, inspector_result
    global inspector_show_timer, total_inspections, auto_save_timer
    global code_combo, code_combo_timer

    game_time += dt

    # Player movement
    keys = pygame.key.get_pressed()
    dx, dy = 0, 0
    if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:   dy += 1
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:   dx -= 1
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:  dx += 1
    if dx or dy:
        ln = math.hypot(dx, dy)
        dx /= ln; dy /= ln
        spd = player["spd"] * dt
        nx = player["x"] + dx * spd
        ny = player["y"] + dy * spd
        nx = clamp(nx, TILE * 0.5, (MAP_W - 0.5) * TILE)
        ny = clamp(ny, TILE * 0.5, (MAP_H - 0.5) * TILE)
        ntx, nty = nx / TILE, ny / TILE
        room = get_room_at_tile(ntx, nty)
        if room is not None:
            player["x"] = nx
            player["y"] = ny
        else:
            room_x = get_room_at_tile(nx/TILE, player["y"]/TILE)
            room_y = get_room_at_tile(player["x"]/TILE, ny/TILE)
            if room_x:
                player["x"] = nx
            elif room_y:
                player["y"] = ny
        if abs(dx) > abs(dy):
            player["facing"] = "right" if dx > 0 else "left"
        else:
            player["facing"] = "down" if dy > 0 else "up"

    # Camera follow
    cam["x"] = player["x"] - W / 2
    cam["y"] = player["y"] * ISO_ANGLE - H / 2

    # Room decay
    for rid in CLEAN_ROOMS:
        decay_rate = 0.015
        if rid == "kitchen": decay_rate = 0.020
        elif rid == "yard": decay_rate = 0.022
        elif rid == "bathroom": decay_rate = 0.018
        rooms_clean[rid] = max(0, rooms_clean[rid] - decay_rate * dt)
        if rooms_clean[rid] < 85 and random.random() < 0.02 * dt:
            rd = ROOMS[rid]["rect"]
            sx = rd[0] + random.uniform(0.3, rd[2]-0.3)
            sy = rd[1] + random.uniform(0.3, rd[3]-0.3)
            dirt_spots[rid].append({"x":sx, "y":sy, "sz":random.uniform(0.2,0.5),
                                    "type":random.choice(["dirt","stain","mess"])})

    # Furniture breaking
    for i, f in enumerate(FURNITURE):
        if not f["breakable"] or i in broken_set:
            continue
        if i not in break_timers:
            break_timers[i] = random.uniform(180, 600)
        break_timers[i] -= dt
        if break_timers[i] <= 0:
            broken_set.add(i)
            add_notif(f"{f['label']} broke!", C_RED, 3.0)
            break_timers[i] = 0

    # Robot AI
    for re in robot_entities:
        rb = ROBOT_DB[re["type"]]
        re["move_timer"] -= dt
        if re["move_timer"] <= 0:
            re["move_timer"] = random.uniform(2, 5)
            if rb["rooms"]:
                room = random.choice(rb["rooms"])
            else:
                room = random.choice(CLEAN_ROOMS)
            re["room"] = room
            rd = ROOMS[room]["rect"]
            re["target_x"] = (rd[0] + random.uniform(0.5, rd[2]-0.5)) * TILE
            re["target_y"] = (rd[1] + random.uniform(0.5, rd[3]-0.5)) * TILE

        tdx = re["target_x"] - re["x"]
        tdy = re["target_y"] - re["y"]
        tdist = math.hypot(tdx, tdy)
        if tdist > 2:
            speed = 60.0
            re["x"] += (tdx / tdist) * speed * dt
            re["y"] += (tdy / tdist) * speed * dt

        cur_room = get_room_at_tile(re["x"]/TILE, re["y"]/TILE)
        if cur_room and cur_room in CLEAN_ROOMS and rb["power"] > 0:
            clean_rate = 0.06 * rb["power"] * (1 + robot_eff_bonus)
            rooms_clean[cur_room] = min(100, rooms_clean[cur_room] + clean_rate * dt)
            if dirt_spots.get(cur_room):
                rtx, rty = re["x"]/TILE, re["y"]/TILE
                dirt_spots[cur_room] = [d for d in dirt_spots[cur_room]
                                        if math.hypot(d["x"]-rtx, d["y"]-rty) > 1.5]

        if re["type"] in ("repair_bot","mega_bot") and broken_set:
            best = None; best_dist = 999
            for bi in broken_set:
                f = FURNITURE[bi]
                fx, fy = get_furn_world_pos(f)
                fx = (fx + f["w"]/2) * TILE
                fy = (fy + f["h"]/2) * TILE
                d = math.hypot(re["x"]-fx, re["y"]-fy)
                if d < best_dist:
                    best_dist = d; best = bi
            if best is not None:
                f = FURNITURE[best]
                fx, fy = get_furn_world_pos(f)
                fx = (fx + f["w"]/2) * TILE
                fy = (fy + f["h"]/2) * TILE
                re["target_x"] = fx; re["target_y"] = fy
                if best_dist < TILE * 1.5:
                    broken_set.discard(best)
                    break_timers[best] = random.uniform(180, 600)
                    add_notif(f"{f['label']} repaired!", C_GREEN, 2.0)

    # Auto-coder
    if auto_code_rate > 0 and current_project is not None:
        proj = GAME_PROJECTS[current_project]
        work = auto_code_rate * dt * (1 + code_speed_bonus)
        project_progress += work
        if project_progress >= proj["work"]:
            finish_project()

    # Code combo decay
    if code_combo_timer > 0:
        code_combo_timer -= dt
        if code_combo_timer <= 0:
            code_combo = 0

    # Inspector
    inspect_timer -= dt
    if inspect_timer <= 0:
        inspect_timer = INSPECTOR_INTERVAL
        run_inspection()

    if inspector_show_timer > 0:
        inspector_show_timer -= dt
        if inspector_show_timer <= 0:
            inspector_active = False

    # Notifications
    for n in notifications[:]:
        n["life"] -= dt
        if n["life"] <= 0: notifications.remove(n)

    # Particles
    for p in particles[:]:
        p["life"] -= dt
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
        if p["life"] <= 0: particles.remove(p)

    # Auto save
    auto_save_timer -= dt
    if auto_save_timer <= 0:
        auto_save_timer = 60.0
        save_data()

def finish_project():
    global money, total_games, total_earned, current_project, project_progress
    if current_project is None: return
    proj = GAME_PROJECTS[current_project]
    money += proj["pay"]
    total_earned += proj["pay"]
    total_games += 1
    add_notif(f"Finished '{proj['name']}'! +${proj['pay']}", C_GOLD, 4.0)
    for _ in range(20):
        particles.append({"x":player["x"]/TILE,"y":player["y"]/TILE,
            "vx":random.uniform(-3,3),"vy":random.uniform(-4,-1),
            "col":proj["col"],"life":random.uniform(0.5,1.5),"sz":random.randint(3,6)})
    current_project = None; project_progress = 0

def do_code_click():
    global project_progress, code_combo, code_combo_timer
    if current_project is None:
        add_notif("Pick a project first! (Q)", C_ORANGE, 1.5)
        return
    if not player_near_furniture("computer", 2.5):
        add_notif("Get to the computer first!", C_ORANGE, 1.5)
        return
    proj = GAME_PROJECTS[current_project]
    spd = 5.0 * (1 + code_speed_bonus) * (1 + min(code_combo, 50) * 0.02)
    project_progress += spd
    code_combo += 1
    code_combo_timer = 2.0
    for _ in range(3):
        particles.append({"x":player["x"]/TILE+random.uniform(-0.3,0.3),
            "y":player["y"]/TILE+random.uniform(-0.5,0),
            "vx":random.uniform(-1,1),"vy":random.uniform(-2,-0.5),
            "col":proj["col"],"life":0.5,"sz":2})
    if project_progress >= proj["work"]:
        finish_project()

def manual_clean_room():
    rid = get_room_at_player()
    if rid and rid in CLEAN_ROOMS:
        rooms_clean[rid] = min(100, rooms_clean[rid] + 2.5)
        if dirt_spots.get(rid) and len(dirt_spots[rid]) > 0:
            dirt_spots[rid].pop(0)
        add_notif(f"Cleaned {ROOMS[rid]['name']}!", C_GREEN, 1.0)
    else:
        add_notif("Nothing to clean here.", C_GRAY, 1.0)

def repair_nearest():
    px, py = player["x"]/TILE, player["y"]/TILE
    best = None; best_d = 999
    for bi in broken_set:
        f = FURNITURE[bi]
        fx, fy = get_furn_world_pos(f)
        fx += f["w"]/2; fy += f["h"]/2
        d = math.hypot(px-fx, py-fy)
        if d < best_d:
            best_d = d; best = bi
    if best is not None and best_d < 2.5:
        broken_set.discard(best)
        break_timers[best] = random.uniform(180, 600)
        add_notif(f"Repaired {FURNITURE[best]['label']}!", C_GREEN, 2.0)
    else:
        add_notif("No broken items nearby.", C_GRAY, 1.0)

def run_inspection():
    global inspector_active, inspector_result, inspector_show_timer
    global money, total_inspections
    total_inspections += 1
    score = get_house_score()
    broken_count = len(broken_set)
    room_scores = {r: rooms_clean[r] for r in CLEAN_ROOMS}
    if score >= 90:   grade,reward,msg,gc = "A+",2000,"Spotless!",C_GOLD
    elif score >= 75: grade,reward,msg,gc = "A",1200,"Very clean!",C_GREEN
    elif score >= 60: grade,reward,msg,gc = "B",600,"Pretty good.",C_LIME
    elif score >= 45: grade,reward,msg,gc = "C",0,"Average...",C_YELLOW
    elif score >= 30: grade,reward,msg,gc = "D",-500,"Below standard!",C_ORANGE
    else:             grade,reward,msg,gc = "F",-1500,"Terrible!",C_RED
    money += reward
    inspector_result = {"score":score,"grade":grade,"reward":reward,"msg":msg,
                        "gc":gc,"room_scores":room_scores,"broken":broken_count}
    inspector_active = True
    inspector_show_timer = 8.0
    pfx = "+" if reward >= 0 else ""
    add_notif(f"Inspector: {grade}! {pfx}${reward}", C_GREEN if reward>=0 else C_RED, 5.0)
    save_data()

def buy_robot(rid):
    global money
    cost = ROBOT_DB[rid]["cost"]
    if money < cost:
        add_notif("Not enough money!", C_RED, 2.0); return False
    money -= cost
    owned_robots.append(rid)
    spawn_robot_entity(rid)
    add_notif(f"Bought {ROBOT_DB[rid]['name']}!", C_GREEN, 2.5)
    save_data(); return True

def buy_upgrade(uid):
    global money, code_speed_bonus, robot_eff_bonus, auto_code_rate
    if uid in owned_upgrades:
        add_notif("Already owned!", C_ORANGE, 2.0); return False
    cost = UPGRADES[uid]["cost"]
    if money < cost:
        add_notif("Not enough money!", C_RED, 2.0); return False
    money -= cost
    owned_upgrades.add(uid)
    u = UPGRADES[uid]
    if u["stat"]=="code_speed": code_speed_bonus += u["val"]
    elif u["stat"]=="robot_eff": robot_eff_bonus += u["val"]
    elif u["stat"]=="auto_code": auto_code_rate += u["val"]
    add_notif(f"Bought {u['name']}!", C_GREEN, 2.5)
    save_data(); return True

def start_project(idx):
    global current_project, project_progress
    if current_project is not None: return
    if 0 <= idx < len(GAME_PROJECTS):
        current_project = idx; project_progress = 0
        add_notif(f"Started '{GAME_PROJECTS[idx]['name']}'!", C_BLUE, 2.5)

# ═══════════════════════════════════════════════════════════════════
#  DRAWING - 2.5D
# ═══════════════════════════════════════════════════════════════════
def draw_tile_rect(surf, tx, ty, tw, th, col, filled=True):
    x1, y1 = tile_to_screen(tx, ty)
    x2, y2 = tile_to_screen(tx+tw, ty)
    x3, y3 = tile_to_screen(tx+tw, ty+th)
    x4, y4 = tile_to_screen(tx, ty+th)
    pts = [(x1,y1),(x2,y2),(x3,y3),(x4,y4)]
    if filled:
        pygame.draw.polygon(surf, col, pts)
    pygame.draw.polygon(surf, tuple(min(255,c+30) for c in col), pts, 1)

def draw_tile_box(surf, tx, ty, tw, th, height, col):
    h_off = height * TILE * ISO_ANGLE * 0.3
    x1, y1 = tile_to_screen(tx, ty)
    x2, y2 = tile_to_screen(tx+tw, ty)
    x3, y3 = tile_to_screen(tx+tw, ty+th)
    x4, y4 = tile_to_screen(tx, ty+th)
    dark = tuple(max(0,c-40) for c in col)
    front = [(x4,y4-h_off),(x3,y3-h_off),(x3,y3),(x4,y4)]
    pygame.draw.polygon(surf, dark, front)
    pygame.draw.polygon(surf, tuple(min(255,c+15) for c in dark), front, 1)
    side = tuple(max(0,c-25) for c in col)
    right = [(x3,y3-h_off),(x2,y2-h_off),(x2,y2),(x3,y3)]
    pygame.draw.polygon(surf, side, right)
    pygame.draw.polygon(surf, tuple(min(255,c+15) for c in side), right, 1)
    top_pts = [(x1,y1-h_off),(x2,y2-h_off),(x3,y3-h_off),(x4,y4-h_off)]
    pygame.draw.polygon(surf, col, top_pts)
    pygame.draw.polygon(surf, tuple(min(255,c+30) for c in col), top_pts, 1)

def draw_world(surf):
    surf.fill(BG)

    # Outdoor tiles
    for ty in range(MAP_H):
        for tx in range(MAP_W):
            sx, sy = tile_to_screen(tx, ty)
            if -TILE < sx < W + TILE and -TILE < sy < H + TILE:
                room = get_room_at_tile(tx + 0.5, ty + 0.5)
                if room is None:
                    c = (35, 50, 30) if (tx + ty) % 2 == 0 else (32, 47, 28)
                    draw_tile_rect(surf, tx, ty, 1, 1, c)

    # Rooms
    for rid in ROOM_ORDER:
        rd = ROOMS[rid]
        rx, ry, rw, rh = rd["rect"]
        fc = rd["floor"]

        for dy in range(rh):
            for dx in range(rw):
                shade = 8 if (dx+dy) % 2 == 0 else 0
                c = tuple(min(255,v+shade) for v in fc)
                draw_tile_rect(surf, rx+dx, ry+dy, 1, 1, c)

        # Dirty overlay
        if rid in CLEAN_ROOMS:
            dirt_level = 100 - rooms_clean.get(rid, 100)
            if dirt_level > 15:
                alpha = min(120, int(dirt_level * 1.2))
                dirt_surf = pygame.Surface((W, H), pygame.SRCALPHA)
                for dy in range(rh):
                    for dx in range(rw):
                        sx2, sy2 = tile_to_screen(rx+dx, ry+dy)
                        sw2, _ = tile_to_screen(rx+dx+1, ry+dy)
                        _, sh2 = tile_to_screen(rx+dx, ry+dy+1)
                        w = max(1, int(sw2 - sx2))
                        h = max(1, int(sh2 - sy2))
                        pygame.draw.rect(dirt_surf, (80,60,30,alpha), (int(sx2),int(sy2),w,h))
                surf.blit(dirt_surf, (0,0))

        # Dirt spots
        if rid in dirt_spots:
            for ds in dirt_spots[rid]:
                sx3, sy3 = tile_to_screen(ds["x"], ds["y"])
                sz = int(ds["sz"] * TILE * 0.4)
                c = C_DIRT if ds["type"] == "dirt" else (C_DIRT2 if ds["type"] == "stain" else (90,80,50))
                pygame.draw.ellipse(surf, c, (int(sx3)-sz, int(sy3)-sz//2, sz*2, sz))

        # Walls
        wall_h = 0.15
        draw_tile_box(surf, rx, ry - wall_h, rw, wall_h, 1.5, C_WALL)
        draw_tile_box(surf, rx - wall_h, ry, wall_h, rh, 1.5, C_WALL_T)

        # Room label
        lx, ly = tile_to_screen(rx + rw/2, ry + 0.3)
        dtxt(surf, rd["name"], FT, rd["col"], int(lx), int(ly), "midtop")

    # Furniture
    for i, f in enumerate(FURNITURE):
        fx, fy = get_furn_world_pos(f)
        is_broken = i in broken_set
        col = f["col"] if not is_broken else (180, 50, 50)
        height = 0.6 if f["w"] < 2 else 0.8
        draw_tile_box(surf, fx, fy, f["w"], f["h"], height, col)
        if is_broken:
            sx4, sy4 = tile_to_screen(fx + f["w"]/2, fy + f["h"]/2)
            dtxt(surf, "X", FM, C_RED, int(sx4), int(sy4) - 12, "center")
            if random.random() < 0.05:
                particles.append({"x":fx+f["w"]/2+random.uniform(-0.3,0.3),
                    "y":fy+f["h"]/2+random.uniform(-0.3,0),
                    "vx":random.uniform(-1,1),"vy":random.uniform(-2,-0.5),
                    "col":C_SPARK,"life":0.3,"sz":2})
        if f["type"] in ("computer","register"):
            sx5, sy5 = tile_to_screen(fx + f["w"]/2, fy - 0.2)
            near = player_near_furniture(f["type"], 2.5)
            lc = C_YELLOW if near else C_DGRAY
            dtxt(surf, f["label"], FT, lc, int(sx5), int(sy5), "midbottom")

    # Robot entities
    for re in robot_entities:
        rx2, ry2 = tile_to_screen(re["x"]/TILE, re["y"]/TILE)
        sz = 10
        pygame.draw.rect(surf, re["col"], (int(rx2)-sz//2, int(ry2)-sz, sz, sz), border_radius=3)
        pygame.draw.circle(surf, tuple(min(255,c+40) for c in re["col"]), (int(rx2), int(ry2)-sz-4), 5)
        pygame.draw.line(surf, C_WHITE, (int(rx2), int(ry2)-sz-9), (int(rx2), int(ry2)-sz-15), 1)
        pygame.draw.circle(surf, C_SPARK, (int(rx2), int(ry2)-sz-16), 2)

    # Particles
    for p in particles:
        sx6, sy6 = tile_to_screen(p["x"], p["y"])
        sz = p.get("sz", 3)
        pygame.draw.circle(surf, p["col"], (int(sx6), int(sy6)), sz)

    # Player
    px, py = tile_to_screen(player["x"]/TILE, player["y"]/TILE)
    pygame.draw.ellipse(surf, (0,0,0,80), (int(px)-10, int(py)-2, 20, 8))
    body_col = (80, 160, 255)
    pygame.draw.rect(surf, body_col, (int(px)-8, int(py)-22, 16, 16), border_radius=4)
    head_col = (220, 180, 140)
    pygame.draw.circle(surf, head_col, (int(px), int(py)-28), 7)
    ex_off = 0; ey_off = 0
    if player["facing"] == "left": ex_off = -2
    elif player["facing"] == "right": ex_off = 2
    elif player["facing"] == "up": ey_off = -2
    else: ey_off = 1
    pygame.draw.circle(surf, (40,40,40), (int(px)-2+ex_off, int(py)-29+ey_off), 1)
    pygame.draw.circle(surf, (40,40,40), (int(px)+2+ex_off, int(py)-29+ey_off), 1)
    pygame.draw.rect(surf, (50,50,70), (int(px)-6, int(py)-6, 5, 6))
    pygame.draw.rect(surf, (50,50,70), (int(px)+1, int(py)-6, 5, 6))

def draw_hud(surf):
    pygame.draw.rect(surf, (20,22,32,200), (0,0,W,50))
    dtxt(surf, f"${money:,}", FL, C_GOLD, 15, 10)
    day, mon, yr, tod = get_time_display()
    dtxt(surf, f"{mon} {day}, Year {yr}  {tod}", FM, C_WHITE, W//2, 5, "midtop")
    frac = (game_time % SECS_PER_DAY) / SECS_PER_DAY
    hour = frac * 24
    dtxt(surf, "DAY" if 6<=hour<18 else "NIGHT", FT, C_YELLOW if 6<=hour<18 else C_BLUE, W//2, 28, "midtop")
    mins_left = inspect_timer / 60.0
    ic = C_RED if mins_left<10 else (C_ORANGE if mins_left<30 else C_GREEN)
    dtxt(surf, f"Inspector: {mins_left:.1f}m", FS, ic, W-15, 8, "topright")
    dtxt(surf, f"Robots: {len(owned_robots)}", FS, C_CYAN, W-15, 28, "topright")
    dtxt(surf, f"Games: {total_games}", FS, C_PURPLE, 250, 12)
    rid = get_room_at_player()
    if rid:
        rn = ROOMS[rid]["name"]
        rc = ROOMS[rid]["col"]
        dtxt(surf, f"[{rn}]", FM, rc, W//2, 38, "midtop")
    dtxt(surf, "WASD Move  SPACE Code  E Clean  R Repair  TAB Shop  Q Projects  F1 Save", FT, C_DGRAY, W//2, 52, "midtop")

    # Project HUD
    if current_project is not None:
        proj = GAME_PROJECTS[current_project]
        pct = min(1.0, project_progress / proj["work"])
        pw, ph = 250, 55
        px2, py2 = 10, H - ph - 10
        pygame.draw.rect(surf, (30,32,45,220), (px2,py2,pw,ph), border_radius=6)
        pygame.draw.rect(surf, proj["col"], (px2,py2,pw,ph), 2, border_radius=6)
        dtxt(surf, proj["name"], FS, proj["col"], px2+8, py2+4)
        bx, by, bw, bh = px2+8, py2+24, pw-16, 12
        pygame.draw.rect(surf, C_DGRAY, (bx,by,bw,bh), border_radius=4)
        fw = int(bw * pct)
        if fw > 0: pygame.draw.rect(surf, proj["col"], (bx,by,fw,bh), border_radius=4)
        dtxt(surf, f"{pct*100:.1f}% | ${proj['pay']}", FT, C_WHITE, bx+bw//2, by-1, "midtop")
        near = player_near_furniture("computer", 2.5)
        if near:
            dtxt(surf, "SPACE to code!", FT, C_GREEN, px2+8, py2+40)
        else:
            dtxt(surf, "Go to computer!", FT, C_ORANGE, px2+8, py2+40)
        if code_combo > 0:
            cc = C_GOLD if code_combo>=20 else (C_ORANGE if code_combo>=10 else C_WHITE)
            dtxt(surf, f"x{code_combo}", FM, cc, px2+pw-10, py2+4, "topright")

    # House score
    score = get_house_score()
    sc = C_GREEN if score>=75 else (C_YELLOW if score>=50 else (C_ORANGE if score>=30 else C_RED))
    dtxt(surf, f"House: {score:.0f}%", FM, sc, W-15, H-30, "bottomright")
    bk = len(broken_set)
    if bk > 0:
        dtxt(surf, f"Broken: {bk}", FS, C_RED, W-15, H-50, "bottomright")

    # Notifications
    for i, n in enumerate(notifications[-5:]):
        y = 70 + i * 22
        dtxt(surf, n["text"], FS, n["col"], W-15, y, "topright")

def draw_shop_overlay(surf):
    overlay = pygame.Surface((W,H), pygame.SRCALPHA)
    overlay.fill((0,0,0,170))
    surf.blit(overlay, (0,0))
    dtxt(surf, "SHOP", FXL, C_GOLD, W//2, 20, "midtop", shadow=True)
    dtxt(surf, f"${money:,}", FM, C_GOLD, W//2, 65, "midtop")
    tabs = ["Robots","Upgrades"]
    tab_rects = []
    for i, name in enumerate(tabs):
        tx = W//2 - 120 + i * 240
        c = C_GOLD if shop_tab == i else C_GRAY
        r = dtxt(surf, f"[ {name} ]", FM, c, tx, 95, "midtop")
        tab_rects.append(r)
    item_rects = []
    if shop_tab == 0:
        for i, rid in enumerate(ROBOT_ORDER):
            rb = ROBOT_DB[rid]
            y = 135 + i * 55
            if y > H - 60: break
            owned_n = owned_robots.count(rid)
            rect = pygame.Rect(120, y, W-240, 48)
            pygame.draw.rect(surf, (40,42,55,220), rect, border_radius=6)
            pygame.draw.rect(surf, rb["col"], rect, 2, border_radius=6)
            dtxt(surf, f"[{rb['icon']}] {rb['name']}", FM, rb["col"], 135, y+4)
            dtxt(surf, rb["desc"], FT, C_GRAY, 135, y+26)
            dtxt(surf, f"x{owned_n}", FS, C_WHITE, W-370, y+10)
            can = money >= rb["cost"]
            bc = C_GREEN if can else C_RED
            dtxt(surf, f"${rb['cost']}", FS, bc, W-270, y+10)
            dtxt(surf, "[BUY]", FS, bc, W-190, y+10)
            item_rects.append(("robot", rid, pygame.Rect(W-230, y, 100, 48)))
    else:
        for i, uid in enumerate(UPGRADE_ORDER):
            u = UPGRADES[uid]
            y = 135 + i * 55
            if y > H - 60: break
            owned = uid in owned_upgrades
            rect = pygame.Rect(120, y, W-240, 48)
            bg = (35,50,35,220) if owned else (40,42,55,220)
            pygame.draw.rect(surf, bg, rect, border_radius=6)
            bc2 = C_GREEN if owned else C_GRAY
            pygame.draw.rect(surf, bc2, rect, 2, border_radius=6)
            dtxt(surf, u["name"], FM, C_GREEN if owned else C_WHITE, 135, y+4)
            dtxt(surf, u["desc"], FT, C_GRAY, 135, y+26)
            if owned:
                dtxt(surf, "OWNED", FS, C_GREEN, W-210, y+14, "midtop")
            else:
                can = money >= u["cost"]
                pc = C_GREEN if can else C_RED
                dtxt(surf, f"${u['cost']}", FS, pc, W-270, y+10)
                dtxt(surf, "[BUY]", FS, pc, W-190, y+10)
                item_rects.append(("upgrade", uid, pygame.Rect(W-230, y, 100, 48)))
    dtxt(surf, "[TAB] Switch  [ESC] Close", FS, C_GRAY, W//2, H-25, "midtop")
    return tab_rects, item_rects

def draw_project_menu(surf):
    overlay = pygame.Surface((W,H), pygame.SRCALPHA)
    overlay.fill((0,0,0,170))
    surf.blit(overlay, (0,0))
    dtxt(surf, "GAME PROJECTS", FXL, C_BLUE, W//2, 20, "midtop", shadow=True)
    if current_project is not None:
        proj = GAME_PROJECTS[current_project]
        pct = project_progress / proj["work"] * 100
        dtxt(surf, f"Current: {proj['name']} ({pct:.1f}%)", FM, proj["col"], W//2, 65, "midtop")
    else:
        dtxt(surf, "Pick a project to start coding!", FM, C_GRAY, W//2, 65, "midtop")
    rects = []
    for i, proj in enumerate(GAME_PROJECTS):
        y = 100 + i * 52
        if y > H - 60: break
        rect = pygame.Rect(150, y, W-300, 45)
        is_cur = current_project == i
        bg = (40,40,60,220) if is_cur else (40,42,55,220)
        pygame.draw.rect(surf, bg, rect, border_radius=6)
        pygame.draw.rect(surf, proj["col"], rect, 2, border_radius=6)
        dtxt(surf, proj["name"], FM, proj["col"], 165, y+4)
        dtxt(surf, f"Work: {proj['work']}  Pay: ${proj['pay']}", FT, C_GRAY, 165, y+26)
        if is_cur:
            dtxt(surf, "IN PROGRESS", FS, C_YELLOW, W-190, y+12)
        elif current_project is None:
            dtxt(surf, "[START]", FS, C_GREEN, W-200, y+12)
            rects.append((i, pygame.Rect(W-240, y, 100, 45)))
    dtxt(surf, "[ESC/Q] Close", FS, C_GRAY, W//2, H-25, "midtop")
    return rects

def draw_inspector_overlay(surf):
    if not inspector_active: return
    overlay = pygame.Surface((W,H), pygame.SRCALPHA)
    overlay.fill((0,0,0,170))
    surf.blit(overlay, (0,0))
    r = inspector_result
    pw, ph = 480, 420
    px2, py2 = W//2 - pw//2, H//2 - ph//2
    pygame.draw.rect(surf, (35,37,50), (px2,py2,pw,ph), border_radius=12)
    pygame.draw.rect(surf, C_GOLD, (px2,py2,pw,ph), 3, border_radius=12)
    dtxt(surf, "INSPECTION", FL, C_GOLD, W//2, py2+12, "midtop")
    dtxt(surf, f"Grade: {r['grade']}", FXL, r["gc"], W//2, py2+45, "midtop")
    dtxt(surf, r["msg"], FM, C_WHITE, W//2, py2+92, "midtop")
    dtxt(surf, f"Score: {r['score']:.0f}%", FM,
         C_GREEN if r['score']>=60 else C_RED, W//2, py2+120, "midtop")
    i = 0
    for rid2 in CLEAN_ROOMS:
        sc2 = r["room_scores"].get(rid2,0)
        cc = C_GREEN if sc2>=75 else (C_YELLOW if sc2>=50 else C_RED)
        dtxt(surf, f"{ROOMS[rid2]['name']}: {sc2:.0f}%", FS, cc, px2+30, py2+155+i*22)
        bx = px2 + 250; bw = 160
        pygame.draw.rect(surf, C_DGRAY, (bx, py2+158+i*22, bw, 10), border_radius=3)
        fw = int(bw * sc2 / 100)
        if fw > 0: pygame.draw.rect(surf, cc, (bx, py2+158+i*22, fw, 10), border_radius=3)
        i += 1
    if r["broken"] > 0:
        dtxt(surf, f"Broken items: {r['broken']} (-{r['broken']*3}%)", FS, C_RED, W//2, py2+ph-80, "midtop")
    if r["reward"] >= 0:
        dtxt(surf, f"Bonus: +${r['reward']}", FM, C_GREEN, W//2, py2+ph-50, "midtop")
    else:
        dtxt(surf, f"Fine: -${abs(r['reward'])}", FM, C_RED, W//2, py2+ph-50, "midtop")
    dtxt(surf, "Click to dismiss", FT, C_GRAY, W//2, py2+ph-20, "midtop")

def draw_title(surf):
    surf.fill(BG)
    dtxt(surf, "CODER TYCOON", FTI, C_GOLD, W//2, 100, "midtop", shadow=True)
    dtxt(surf, "2.5D Edition", FL, C_CYAN, W//2, 170, "midtop")
    lines = [
        "       /\\         ",
        "      /  \\   [=O=]",
        "     / __ \\  /|X|\\",
        "    |_|  |_|  / \\ ",
    ]
    for i, l in enumerate(lines):
        dtxt(surf, l, FM, C_WHITE, W//2, 220+i*24, "midtop")
    dtxt(surf, "Walk around your house, code at the computer,", FS, C_GRAY, W//2, 340, "midtop")
    dtxt(surf, "buy robots to clean, survive inspections!", FS, C_GRAY, W//2, 360, "midtop")
    dtxt(surf, "[N] New Game", FL, C_GREEN, W//2, 420, "midtop")
    if has_save():
        dtxt(surf, "[C] Continue", FL, C_BLUE, W//2, 460, "midtop")
    dtxt(surf, "WASD to move | SPACE to code at computer", FS, C_ORANGE, W//2, 520, "midtop")
    dtxt(surf, "E to clean | R to repair | TAB for shop", FS, C_ORANGE, W//2, 545, "midtop")
    dtxt(surf, "Inspector visits every 152 minutes!", FS, C_YELLOW, W//2, 590, "midtop")

def draw_gameover(surf):
    surf.fill((20,10,10))
    dtxt(surf, "BANKRUPT!", FXL, C_RED, W//2, 200, "midtop", shadow=True)
    dtxt(surf, f"Survived {total_inspections} inspections", FM, C_WHITE, W//2, 270, "midtop")
    dtxt(surf, f"Games: {total_games} | Earned: ${total_earned:,}", FM, C_GOLD, W//2, 310, "midtop")
    dtxt(surf, "[R] Restart  [ESC] Quit", FM, C_GRAY, W//2, 400, "midtop")

# ═══════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════════════════════════
running = True
shop_tab_rects = []
shop_item_rects = []
proj_rects = []

while running:
    dt = clock.tick(FPS) / 1000.0
    dt = min(dt, 0.05)
    mx, my = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if state == "play": save_data()
            running = False
        if event.type == pygame.KEYDOWN:
            key = event.key
            if state == "title":
                if key == pygame.K_n:
                    new_game(); state = "play"
                    add_notif("Welcome! Go to the OFFICE to code!", C_GOLD, 5.0)
                    add_notif("Press Q to pick a project first!", C_CYAN, 5.0)
                elif key == pygame.K_c and has_save():
                    if load_data():
                        state = "play"; add_notif("Game loaded!", C_GREEN, 2.0)
            elif state == "play":
                if inspector_active:
                    inspector_active = False; inspector_show_timer = 0
                    continue
                if shop_open:
                    if key == pygame.K_TAB:
                        shop_tab = (shop_tab + 1) % 2
                    elif key == pygame.K_ESCAPE:
                        shop_open = False
                    continue
                if project_menu:
                    if key in (pygame.K_ESCAPE, pygame.K_q):
                        project_menu = False
                    continue
                if key == pygame.K_SPACE:
                    do_code_click()
                elif key == pygame.K_e:
                    manual_clean_room()
                elif key == pygame.K_r:
                    repair_nearest()
                elif key == pygame.K_TAB:
                    if player_near_furniture("register", 3.0):
                        shop_open = True; shop_tab = 0
                    else:
                        add_notif("Go to the Shop room first!", C_ORANGE, 2.0)
                elif key == pygame.K_q:
                    project_menu = True
                elif key == pygame.K_F1:
                    if save_data(): add_notif("Saved!", C_GREEN, 2.0)
                elif key == pygame.K_ESCAPE:
                    save_data(); state = "title"
            elif state == "gameover":
                if key == pygame.K_r:
                    new_game(); state = "play"
                elif key == pygame.K_ESCAPE:
                    running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if state == "play":
                if inspector_active:
                    inspector_active = False; inspector_show_timer = 0
                    continue
                if shop_open:
                    for i, tr in enumerate(shop_tab_rects):
                        if tr.collidepoint(mx, my):
                            shop_tab = i; break
                    for t, iid, r in shop_item_rects:
                        if r.collidepoint(mx, my):
                            if t == "robot": buy_robot(iid)
                            elif t == "upgrade": buy_upgrade(iid)
                            break
                    continue
                if project_menu:
                    for idx, r in proj_rects:
                        if r.collidepoint(mx, my):
                            start_project(idx); project_menu = False
                            break
                    continue

    if state == "play" and not shop_open and not project_menu and not inspector_active:
        update_game(dt)
        if money < -5000:
            state = "gameover"

    if state == "title":
        draw_title(screen)
    elif state == "play":
        draw_world(screen)
        draw_hud(screen)
        if shop_open:
            shop_tab_rects, shop_item_rects = draw_shop_overlay(screen)
        if project_menu:
            proj_rects = draw_project_menu(screen)
        draw_inspector_overlay(screen)
    elif state == "gameover":
        draw_gameover(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()