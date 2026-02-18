"""
SHAPE SHIFTER TD  —  Absorb enemy abilities. Defend your base. Survive 10 minutes.
2.5D tower defense where YOU are the defense.

Controls:d
  SPACE - Melee attack
  Q/E/R - Use abilities (3 slots)
  F     - Deploy clone (costs essence)
  1/2/3 - Choose during ability selection
  ESC   - Skip ability pickup
"""
import pygame, sys, math, random, os, json

pygame.init()

# ═══════════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════════
W, H = 1280, 720
FPS = 60
DURATION = 600          # 10 minutes
BASE_POS = (W - 120, H // 2)
MELEE_RANGE = 58
MELEE_ARC = math.pi * 0.7
MELEE_DMG = 20
MELEE_CD = 0.32
SHOOT_CD = 0.18
SHOOT_DMG = 12
SHOOT_SPD = 500
ORB_PICKUP = 32
CLONE_COST = 80
MAX_CLONES = 2
P_HP = 120
P_SPEED = 230           # px / sec
BASE_HP_MAX = 600
SAVE_FILE = "shape_shifter_td_save.json"
GAME_SAVE_FILE = "shape_shifter_td_gamesave.json"

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Shape Shifter TD")
clock = pygame.time.Clock()

# ═══════════════════════════════════════════════════════════════════
#  COLORS
# ═══════════════════════════════════════════════════════════════════
BG      = (10, 10, 18)
GRID    = (20, 20, 35)
WHITE   = (255, 255, 255)
BLACK   = (0, 0, 0)
GRAY    = (100, 100, 100)
DGRAY   = (50, 50, 50)
C_SPIKE = (220, 50, 50)
C_FIRE  = (255, 140, 30)
C_FROST = (60, 220, 255)
C_VOLT  = (255, 240, 60)
C_VENOM = (80, 230, 80)
C_SHADOW= (170, 60, 255)
C_TITAN = (255, 60, 60)
C_HYDRA = (255, 160, 60)
C_VOID  = (130, 30, 200)
C_BASE  = (60, 160, 255)
C_PLAYER= (220, 220, 240)
C_CLONE = (140, 190, 220)
C_ESS   = (255, 210, 60)
C_ARMOR = (180, 180, 200)
C_HEAL  = (100, 255, 150)
C_SPLIT = (255, 180, 100)
C_TELE  = (200, 100, 255)
C_BERSERK=(255, 30, 30)
C_NECRO = (160, 80, 200)
C_GOLEM = (160, 140, 100)
C_STORM = (100, 200, 255)
C_GOLD  = (255, 215, 0)
C_SHIELD= (80, 200, 255)

# ═══════════════════════════════════════════════════════════════════
#  FONTS & HELPERS
# ═══════════════════════════════════════════════════════════════════
FS = pygame.font.SysFont("consolas", 15)
FM = pygame.font.SysFont("consolas", 20, bold=True)
FL = pygame.font.SysFont("consolas", 32, bold=True)
FX = pygame.font.SysFont("consolas", 50, bold=True)
FT = pygame.font.SysFont("consolas", 58, bold=True)

def dtxt(s, txt, f, c, x, y, anc="topleft"):
    r = f.render(txt, True, c)
    rc = r.get_rect(**{anc: (x, y)})
    s.blit(r, rc)
    return rc

def lerp(a, b, t): return a + (b - a) * max(0.0, min(1.0, t))
def lc(c1, c2, t): return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))
def dst(a, b): return math.hypot(a[0]-b[0], a[1]-b[1])
def ang(s, d): return math.atan2(d[1]-s[1], d[0]-s[0])
def nrm(dx, dy):
    l = math.hypot(dx, dy)
    return (dx/l, dy/l) if l > 0.001 else (0.0, 0.0)
def ppoly(cx, cy, r, n, rot=0):
    return [(cx + r*math.cos(2*math.pi*i/n+rot), cy + r*math.sin(2*math.pi*i/n+rot)) for i in range(n)]
def bcol(cols):
    if not cols: return C_PLAYER
    return tuple(sum(c[i] for c in cols)//len(cols) for i in range(3))
def clamp(v, lo, hi): return max(lo, min(hi, v))

# ═══════════════════════════════════════════════════════════════════
#  ABILITY / ENEMY / BOSS TABLES
# ═══════════════════════════════════════════════════════════════════
ABILS = {
    "spike_burst":  {"name":"Spike Burst",  "color":C_SPIKE, "cd":3.0,  "desc":"8 spikes radiate out",       "boss":False},
    "fire_wave":    {"name":"Fire Wave",    "color":C_FIRE,  "cd":3.5,  "desc":"Piercing fire forward",      "boss":False},
    "freeze_pulse": {"name":"Freeze Pulse", "color":C_FROST, "cd":5.5,  "desc":"Freeze nearby enemies 2s",   "boss":False},
    "chain_bolt":   {"name":"Chain Bolt",   "color":C_VOLT,  "cd":4.5,  "desc":"Lightning bounces x3",       "boss":False},
    "poison_cloud": {"name":"Poison Cloud", "color":C_VENOM, "cd":6.0,  "desc":"Toxic zone 4s",              "boss":False},
    "shadow_dash":  {"name":"Shadow Dash",  "color":C_SHADOW,"cd":4.0,  "desc":"Teleport + damage in path",  "boss":False},
    "armor_bash":   {"name":"Armor Bash",   "color":C_ARMOR, "cd":4.0,  "desc":"Heavy shield slam",          "boss":False},
    "heal_pulse":   {"name":"Heal Pulse",   "color":C_HEAL,  "cd":8.0,  "desc":"Heal player 30 HP",          "boss":False},
    "split_shot":   {"name":"Split Shot",   "color":C_SPLIT, "cd":3.5,  "desc":"Bullet splits into 3",       "boss":False},
    "phase_blink":  {"name":"Phase Blink",  "color":C_TELE,  "cd":5.0,  "desc":"Teleport + invuln 1s",       "boss":False},
    "berserk_rage": {"name":"Berserk Rage", "color":C_BERSERK,"cd":12.0,"desc":"2x speed+dmg for 5s",       "boss":False},
    "raise_dead":   {"name":"Raise Dead",   "color":C_NECRO, "cd":14.0,"desc":"Summon 3 allied minions",    "boss":False},
    "titan_slam":   {"name":"Titan Slam",   "color":C_TITAN, "cd":7.0,  "desc":"Massive AoE shockwave",      "boss":True},
    "hydra_volley": {"name":"Hydra Volley", "color":C_HYDRA, "cd":5.0,  "desc":"5 homing fireballs",         "boss":True},
    "void_rift":    {"name":"Void Rift",    "color":C_VOID,  "cd":9.0,  "desc":"Black hole pulls+damages",   "boss":True},
    "golem_wall":   {"name":"Golem Wall",   "color":C_GOLEM, "cd":8.0,  "desc":"Stone barrier blocks foes",  "boss":True},
    "storm_call":   {"name":"Storm Call",   "color":C_STORM, "cd":7.0,  "desc":"Lightning strikes random foes","boss":True},
}

E_STATS = {
    "spike":    {"hp":60,  "spd":85,  "dmg":8,  "col":C_SPIKE,  "sides":3, "sz":14, "ess":5},
    "blaze":    {"hp":70,  "spd":105, "dmg":10, "col":C_FIRE,   "sides":0, "sz":13, "ess":6},
    "frost":    {"hp":80,  "spd":70,  "dmg":7,  "col":C_FROST,  "sides":6, "sz":15, "ess":7},
    "volt":     {"hp":45,  "spd":155, "dmg":12, "col":C_VOLT,   "sides":4, "sz":12, "ess":8},
    "venom":    {"hp":90,  "spd":62,  "dmg":6,  "col":C_VENOM,  "sides":5, "sz":15, "ess":8},
    "shadow":   {"hp":40,  "spd":165, "dmg":15, "col":C_SHADOW, "sides":7, "sz":13, "ess":10},
    "armored":  {"hp":160, "spd":50,  "dmg":6,  "col":C_ARMOR,  "sides":4, "sz":17, "ess":10},
    "healer":   {"hp":50,  "spd":65,  "dmg":5,  "col":C_HEAL,   "sides":0, "sz":12, "ess":12},
    "splitter": {"hp":80,  "spd":90,  "dmg":8,  "col":C_SPLIT,  "sides":3, "sz":14, "ess":8},
    "teleporter":{"hp":55, "spd":80,  "dmg":11, "col":C_TELE,   "sides":5, "sz":12, "ess":10},
    "berserker":{"hp":110, "spd":75,  "dmg":18, "col":C_BERSERK,"sides":3, "sz":16, "ess":12},
    "necro":    {"hp":70,  "spd":48,  "dmg":5,  "col":C_NECRO,  "sides":6, "sz":14, "ess":15},
}

B_STATS = {
    "titan":      {"hp":600,  "spd":45, "dmg":20, "col":C_TITAN, "sz":36, "ess":60,  "abil":"titan_slam"},
    "hydra":      {"hp":800,  "spd":55, "dmg":18, "col":C_HYDRA, "sz":38, "ess":70,  "abil":"hydra_volley"},
    "void_lord":  {"hp":1000, "spd":40, "dmg":25, "col":C_VOID,  "sz":40, "ess":80,  "abil":"void_rift"},
    "golem_king": {"hp":1200, "spd":35, "dmg":22, "col":C_GOLEM, "sz":42, "ess":100, "abil":"golem_wall"},
    "storm_wyrm": {"hp":1500, "spd":60, "dmg":20, "col":C_STORM, "sz":44, "ess":120, "abil":"storm_call"},
}

E_ABIL = {
    "spike":"spike_burst", "blaze":"fire_wave", "frost":"freeze_pulse",
    "volt":"chain_bolt", "venom":"poison_cloud", "shadow":"shadow_dash",
    "armored":"armor_bash", "healer":"heal_pulse", "splitter":"split_shot",
    "teleporter":"phase_blink", "berserker":"berserk_rage", "necro":"raise_dead",
}

# ═══════════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════
notifications = []

def add_notification(text, color=WHITE, duration=2.5):
    notifications.append({"text": text, "color": color, "life": duration, "ml": duration})

def update_notifications(dt):
    for n in notifications[:]:
        n["life"] -= dt
        if n["life"] <= 0:
            notifications.remove(n)

def draw_notifications(surf):
    y = 100
    for n in notifications:
        a = min(1.0, n["life"] / 0.5)  # fade out in last 0.5s
        col = tuple(int(n["color"][i] * a) for i in range(3))
        r = FM.render(n["text"], True, col)
        rc = r.get_rect(midtop=(W // 2, y))
        # Dark bg behind text
        bg = pygame.Surface((rc.width + 20, rc.height + 8), pygame.SRCALPHA)
        bg.fill((0, 0, 0, int(140 * a)))
        surf.blit(bg, (rc.x - 10, rc.y - 4))
        surf.blit(r, rc)
        y += rc.height + 12

# ═══════════════════════════════════════════════════════════════════
#  PARTICLES
# ═══════════════════════════════════════════════════════════════════
particles = []

def spawn_parts(x, y, col, n=8, spd=90, life=0.5, sz=3):
    for _ in range(n):
        a = random.uniform(0, math.tau)
        s = random.uniform(spd*0.3, spd)
        particles.append({"x":x,"y":y,"vx":math.cos(a)*s,"vy":math.sin(a)*s,
                          "life":random.uniform(life*0.5,life),"ml":life,"col":col,"sz":sz})

def update_parts(dt):
    for p in particles[:]:
        p["life"] -= dt
        if p["life"] <= 0:
            particles.remove(p); continue
        p["x"] += p["vx"]*dt; p["y"] += p["vy"]*dt
        p["vx"] *= 0.96; p["vy"] *= 0.96

def draw_parts(surf):
    for p in particles:
        a = max(0, p["life"]/p["ml"])
        sz = max(1, int(p["sz"]*a))
        c = tuple(int(p["col"][i]*a) for i in range(3))
        pygame.draw.circle(surf, c, (int(p["x"]), int(p["y"])), sz)

# ═══════════════════════════════════════════════════════════════════
#  GLOBAL GAME STATE
# ═══════════════════════════════════════════════════════════════════
state = "title"
game_time = 0.0
shake = 0.0
player = {}
base = {}
enemies = []
clones = []
projectiles = []
zones = []
orbs = []
rings = []
chain_vis = []
essence = 0
kills = 0
spawn_timer = 0.0
boss_spawned = set()
dbl_active = False       # permanent double-attack (unlocked on first boss kill)
atk_multi = 1            # stacking attack multiplier (doubles per boss kill)
pending_ab = None
pending_boss = False
best = {"time":0,"kills":0,"wins":0}
_auto_save_timer = 60.0

# --- Damage Numbers ---
dmg_numbers = []

# --- Combo System ---
combo_count = 0
combo_timer = 0.0
combo_best = 0

# --- Power-ups ---
powerups = []

# --- Wave Announcements ---
wave_announce = {"text": "", "life": 0.0, "color": WHITE}

# --- Stats Tracking ---
stats = {"total_dmg": 0, "melee_kills": 0, "ability_kills": 0, "shots_fired": 0,
         "bosses_killed": 0, "powerups_collected": 0, "max_combo": 0, "deaths": 0}

# --- Shop / Gear UI ---
shop_open = False
shop_tab = 0   # 0=perks, 1=gear
shop_scroll = 0

# --- Player Respawn ---
respawn_timer = 0.0   # >0 means player is dead/respawning
respawn_boss = None   # boss type to re-fight

# --- Berserk Buff ---
berserk_timer = 0.0

# --- Elite modifier names ---
ELITE_MODS = ["shielded", "enraged", "vampiric", "splitting"]

# --- Friendly minions (from raise_dead) ---
minions = []

# --- Chaos gem timer ---
chaos_timer = 0.0

# --- Difficulty ---
#  0=Easy, 1=Normal, 2=Hard
difficulty = 1
DIFF_NAMES = ["Easy", "Normal", "Hard"]
DIFF_COLORS = [(80,220,80), (255,220,60), (255,60,60)]
DIFF_HP_MULT = [0.6, 1.0, 1.6]       # enemy/boss HP multiplier
DIFF_SPD_MULT = [0.85, 1.0, 1.2]     # enemy speed multiplier
DIFF_SPAWN_MULT = [1.3, 1.0, 0.7]    # spawn interval mult (higher=slower spawns)
DIFF_DMG_MULT = [0.7, 1.0, 1.4]      # enemy damage multiplier
DIFF_ESS_MULT = [1.3, 1.0, 0.8]      # essence reward multiplier

# --- XP / Perk Progress ---
# Earn 1 perk point every XP_PER_PERK kills (in addition to boss kill rewards)
XP_PER_PERK = 50
run_xp = 0  # kills-based XP accumulated this run

def load_best():
    global best
    if os.path.exists(SAVE_FILE):
        try:
            best = json.load(open(SAVE_FILE))
        except Exception:
            pass

def save_best():
    try:
        json.dump(best, open(SAVE_FILE,"w"))
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════════
#  PERSISTENT PROFILE — Perks & Gear (saved across runs)
# ═══════════════════════════════════════════════════════════════════
PROFILE_FILE = "shape_shifter_td_profile.json"

PERKS = {
    "vitality":     {"name":"Vitality",      "desc":"+20 Max HP",          "max_lvl":10,"costs":[1,1,1,2,2,2,3,3,4,4]},
    "swiftness":    {"name":"Swiftness",     "desc":"+12 Move Speed",      "max_lvl":5, "costs":[1,2,2,3,4]},
    "might":        {"name":"Might",         "desc":"+3 Melee+Shoot DMG",  "max_lvl":8, "costs":[1,1,2,2,3,3,4,4]},
    "regeneration": {"name":"Regeneration",  "desc":"+0.5 HP/s regen",     "max_lvl":6, "costs":[1,2,2,3,3,4]},
    "essence_boost":{"name":"Essence Boost", "desc":"+15% essence gain",   "max_lvl":5, "costs":[2,2,3,3,4]},
    "fortify":      {"name":"Fortify Base",  "desc":"+50 Base HP",         "max_lvl":6, "costs":[1,2,2,3,4,5]},
    "quick_cast":   {"name":"Quick Cast",    "desc":"-5% ability CDs",     "max_lvl":5, "costs":[2,3,3,4,5]},
    "clone_tough":  {"name":"Clone Tough",   "desc":"+15 Clone HP",        "max_lvl":5, "costs":[1,2,3,3,4]},
}
PERK_ORDER = ["vitality","swiftness","might","regeneration","essence_boost","fortify","quick_cast","clone_tough"]

GEAR_DB = {
    "rusty_blade":   {"name":"Rusty Blade",   "slot":"weapon",   "rarity":"common",   "desc":"+10% melee dmg",        "stats":{"melee_pct":0.10}},
    "fire_staff":    {"name":"Fire Staff",    "slot":"weapon",   "rarity":"rare",     "desc":"+20% ability dmg",      "stats":{"abil_pct":0.20}},
    "crystal_bow":   {"name":"Crystal Bow",   "slot":"weapon",   "rarity":"rare",     "desc":"+30% shoot dmg",        "stats":{"shoot_pct":0.30}},
    "void_scythe":   {"name":"Void Scythe",   "slot":"weapon",   "rarity":"epic",     "desc":"+25% all damage",       "stats":{"all_pct":0.25}},
    "titan_hammer":  {"name":"Titan Hammer",  "slot":"weapon",   "rarity":"legendary","desc":"+35% melee+knockback",  "stats":{"melee_pct":0.35}},
    "leather_vest":  {"name":"Leather Vest",  "slot":"armor",    "rarity":"common",   "desc":"+30 Max HP",            "stats":{"hp_bonus":30}},
    "frost_plate":   {"name":"Frost Plate",   "slot":"armor",    "rarity":"rare",     "desc":"+50 HP, frost aura",    "stats":{"hp_bonus":50}},
    "shadow_cloak":  {"name":"Shadow Cloak",  "slot":"armor",    "rarity":"epic",     "desc":"+20% dodge chance",     "stats":{"dodge_pct":0.20}},
    "titan_armor":   {"name":"Titan Armor",   "slot":"armor",    "rarity":"legendary","desc":"+80 HP, +10% dmg",      "stats":{"hp_bonus":80,"all_pct":0.10}},
    "speed_ring":    {"name":"Speed Ring",    "slot":"accessory","rarity":"common",   "desc":"+25 Speed",             "stats":{"spd_bonus":25}},
    "essence_amulet":{"name":"Essence Amulet","slot":"accessory","rarity":"rare",     "desc":"+25% essence",          "stats":{"ess_pct":0.25}},
    "revival_charm": {"name":"Revival Charm", "slot":"accessory","rarity":"epic",     "desc":"Auto-revive once 50HP", "stats":{"revive":True}},
    "chaos_gem":     {"name":"Chaos Gem",     "slot":"accessory","rarity":"legendary","desc":"Random ability /30s",   "stats":{"chaos":True}},
}

RARITY_COLORS = {"common":(180,180,180),"rare":(60,160,255),"epic":(180,60,255),"legendary":(255,200,50)}
RARITY_WEIGHT = {"common":50,"rare":30,"epic":15,"legendary":5}

# Boss → possible gear drops
BOSS_GEAR_DROPS = {
    "titan":      ["rusty_blade","leather_vest","speed_ring"],
    "hydra":      ["fire_staff","frost_plate","essence_amulet"],
    "void_lord":  ["void_scythe","shadow_cloak","revival_charm"],
    "golem_king": ["titan_hammer","titan_armor","chaos_gem"],
    "storm_wyrm": ["crystal_bow","frost_plate","essence_amulet","chaos_gem"],
}

profile = {
    "perk_points": 0,
    "perks": {},
    "equipped": {"weapon": None, "armor": None, "accessory": None},
    "inventory": [],
    "total_kills": 0,
    "total_wins": 0,
    "total_bosses": 0,
    "total_runs": 0,
    "saved_xp": 0,
}

def load_profile():
    global profile
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE) as f:
                loaded = json.load(f)
            for k in profile:
                if k in loaded:
                    profile[k] = loaded[k]
        except Exception:
            pass

def save_profile():
    try:
        with open(PROFILE_FILE, "w") as f:
            json.dump(profile, f)
    except Exception:
        pass

def get_perk_level(pid):
    return profile["perks"].get(pid, 0)

def buy_perk(pid):
    pk = PERKS[pid]
    lvl = get_perk_level(pid)
    if lvl >= pk["max_lvl"]:
        return False
    cost = pk["costs"][lvl]
    if profile["perk_points"] < cost:
        return False
    profile["perk_points"] -= cost
    profile["perks"][pid] = lvl + 1
    save_profile()
    return True

def get_gear_stats():
    """Combined stats from equipped gear."""
    stats = {}
    for slot, gid in profile["equipped"].items():
        if gid and gid in GEAR_DB:
            for k, v in GEAR_DB[gid]["stats"].items():
                if isinstance(v, bool):
                    stats[k] = v
                else:
                    stats[k] = stats.get(k, 0) + v
    return stats

def equip_gear(gid):
    """Equip a gear piece from inventory."""
    if gid not in profile["inventory"] or gid not in GEAR_DB:
        return False
    slot = GEAR_DB[gid]["slot"]
    old = profile["equipped"][slot]
    if old:
        profile["inventory"].append(old)
    profile["inventory"].remove(gid)
    profile["equipped"][slot] = gid
    save_profile()
    return True

def unequip_gear(slot):
    gid = profile["equipped"].get(slot)
    if gid:
        profile["inventory"].append(gid)
        profile["equipped"][slot] = None
        save_profile()

def grant_gear(gid):
    """Give player a gear piece."""
    if gid in GEAR_DB:
        profile["inventory"].append(gid)
        save_profile()
        g = GEAR_DB[gid]
        rc = RARITY_COLORS.get(g["rarity"], WHITE)
        add_notification(f"Got gear: {g['name']}!", rc, 3.5)

def roll_boss_gear(btype):
    """Roll for gear drop from boss kill."""
    pool = BOSS_GEAR_DROPS.get(btype, [])
    if not pool:
        return
    if random.random() < 0.5:  # 50% chance per boss kill
        gid = random.choice(pool)
        grant_gear(gid)

def apply_perks_and_gear():
    """Apply persistent bonuses at game start."""
    gs = get_gear_stats()
    player["max_hp"] = P_HP + get_perk_level("vitality") * 20 + gs.get("hp_bonus", 0)
    player["hp"] = player["max_hp"]
    player["spd"] = P_SPEED + get_perk_level("swiftness") * 12 + gs.get("spd_bonus", 0)
    base["max_hp"] = BASE_HP_MAX + get_perk_level("fortify") * 50
    base["hp"] = base["max_hp"]

# ═══════════════════════════════════════════════════════════════════
#  MID-GAME SAVE / LOAD
# ═══════════════════════════════════════════════════════════════════
def save_game():
    """Save full game state to disk so player can resume later."""
    try:
        data = {
            "game_time": game_time,
            "essence": essence,
            "kills": kills,
            "spawn_timer": spawn_timer,
            "boss_spawned": list(boss_spawned),
            "dbl_active": dbl_active,
            "atk_multi": atk_multi,
            "shake": shake,
            "combo_count": combo_count,
            "combo_timer": combo_timer,
            "combo_best": combo_best,
            "berserk_timer": berserk_timer,
            "respawn_timer": respawn_timer,
            "respawn_boss": respawn_boss,
            "chaos_timer": chaos_timer,
            "difficulty": difficulty,
            "run_xp": run_xp,
            "stats": stats,
            "player": {
                "x": player["x"], "y": player["y"],
                "hp": player["hp"], "max_hp": player["max_hp"],
                "spd": player["spd"], "facing": player["facing"],
                "ab": player["ab"], "cd": player["cd"],
                "mcd": player["mcd"], "scd": player["scd"],
                "manim": player["manim"], "invuln": player["invuln"],
            },
            "base": {
                "x": base["x"], "y": base["y"],
                "hp": base["hp"], "max_hp": base["max_hp"],
                "flash": base["flash"],
            },
            "enemies": [{
                "x": e["x"], "y": e["y"], "hp": e["hp"], "max_hp": e["max_hp"],
                "spd": e["spd"], "dmg": e["dmg"], "type": e["type"],
                "col": list(e["col"]), "sides": e["sides"], "sz": e["sz"],
                "ess": e["ess"], "boss": e["boss"], "btype": e["btype"],
                "frozen": e["frozen"], "hflash": e["hflash"],
                "acd": e["acd"], "wander_t": e["wander_t"],
                "wx": e["wx"], "wy": e["wy"],
                "elite": e.get("elite", ""), "phase": e.get("phase", 0),
                "shield_hp": e.get("shield_hp", 0),
            } for e in enemies],
            "clones": [{
                "x": c["x"], "y": c["y"], "hp": c["hp"], "max_hp": c["max_hp"],
                "spd": c["spd"], "facing": c["facing"],
                "ab": c["ab"], "cd": c["cd"],
                "mcd": c["mcd"], "scd": c["scd"], "manim": c["manim"],
            } for c in clones],
            "orbs": [{
                "x": o["x"], "y": o["y"], "ab": o["ab"],
                "boss": o["boss"], "life": o["life"], "t": o["t"],
            } for o in orbs],
        }
        with open(GAME_SAVE_FILE, "w") as f:
            json.dump(data, f)
        add_notification("Game Saved!", (80, 255, 80), 2.0)
    except Exception as ex:
        add_notification(f"Save failed: {ex}", (255, 80, 80), 3.0)

def load_game():
    """Load a saved game and restore full state. Returns True on success."""
    global state, game_time, shake, player, base, essence, kills
    global spawn_timer, boss_spawned, dbl_active, atk_multi
    global combo_count, combo_timer, combo_best, berserk_timer
    global respawn_timer, respawn_boss, chaos_timer, stats
    global difficulty, run_xp
    if not os.path.exists(GAME_SAVE_FILE):
        return False
    try:
        with open(GAME_SAVE_FILE) as f:
            data = json.load(f)
        # Clear lists
        enemies.clear(); clones.clear(); projectiles.clear()
        zones.clear(); orbs.clear(); rings.clear(); chain_vis.clear()
        particles.clear(); notifications.clear()
        dmg_numbers.clear(); powerups.clear(); minions.clear()
        # Scalars
        game_time = data["game_time"]
        essence = data["essence"]
        kills = data["kills"]
        spawn_timer = data["spawn_timer"]
        boss_spawned = set(data["boss_spawned"])
        dbl_active = data["dbl_active"]
        atk_multi = data["atk_multi"]
        shake = data.get("shake", 0)
        combo_count = data.get("combo_count", 0)
        combo_timer = data.get("combo_timer", 0)
        combo_best = data.get("combo_best", 0)
        berserk_timer = data.get("berserk_timer", 0)
        respawn_timer = data.get("respawn_timer", 0)
        respawn_boss = data.get("respawn_boss", None)
        chaos_timer = data.get("chaos_timer", 0)
        difficulty = data.get("difficulty", 1)
        run_xp = data.get("run_xp", 0)
        stats = data.get("stats", {"total_dmg":0,"melee_kills":0,"ability_kills":0,"shots_fired":0,"bosses_killed":0,"powerups_collected":0,"max_combo":0,"deaths":0})
        # Player
        pd = data["player"]
        player.update({
            "x": pd["x"], "y": pd["y"],
            "hp": pd["hp"], "max_hp": pd["max_hp"],
            "spd": pd["spd"], "facing": pd["facing"],
            "ab": pd["ab"], "cd": pd["cd"],
            "mcd": pd["mcd"], "scd": pd["scd"],
            "manim": pd["manim"], "invuln": pd["invuln"],
        })
        # Base
        bd = data["base"]
        base.update({
            "x": bd["x"], "y": bd["y"],
            "hp": bd["hp"], "max_hp": bd["max_hp"],
            "flash": bd.get("flash", 0),
        })
        # Enemies
        for ed in data["enemies"]:
            enemies.append({
                "x": ed["x"], "y": ed["y"], "hp": ed["hp"], "max_hp": ed["max_hp"],
                "spd": ed["spd"], "dmg": ed["dmg"], "type": ed["type"],
                "col": tuple(ed["col"]), "sides": ed["sides"], "sz": ed["sz"],
                "ess": ed["ess"], "boss": ed["boss"], "btype": ed["btype"],
                "frozen": ed["frozen"], "hflash": ed["hflash"],
                "acd": ed["acd"], "wander_t": ed["wander_t"],
                "wx": ed["wx"], "wy": ed["wy"],
                "elite": ed.get("elite", ""), "phase": ed.get("phase", 0),
                "shield_hp": ed.get("shield_hp", 0),
            })
        # Clones
        for cd_data in data["clones"]:
            clones.append({
                "x": cd_data["x"], "y": cd_data["y"],
                "hp": cd_data["hp"], "max_hp": cd_data["max_hp"],
                "spd": cd_data["spd"], "facing": cd_data["facing"],
                "ab": cd_data["ab"], "cd": cd_data["cd"],
                "mcd": cd_data["mcd"], "scd": cd_data["scd"],
                "manim": cd_data["manim"],
            })
        # Orbs
        for od in data["orbs"]:
            orbs.append({
                "x": od["x"], "y": od["y"], "ab": od["ab"],
                "boss": od["boss"], "life": od["life"], "t": od["t"],
            })
        state = "play"
        add_notification("Game Loaded!", (80, 200, 255), 2.0)
        return True
    except Exception as ex:
        add_notification(f"Load failed: {ex}", (255, 80, 80), 3.0)
        return False

def has_game_save():
    return os.path.exists(GAME_SAVE_FILE)

def delete_game_save():
    if os.path.exists(GAME_SAVE_FILE):
        try:
            os.remove(GAME_SAVE_FILE)
        except Exception:
            pass

def init_game():
    global state, game_time, shake, player, base, enemies, clones
    global projectiles, zones, orbs, rings, chain_vis
    global essence, kills, spawn_timer, boss_spawned, pending_ab, pending_boss, dbl_active, atk_multi, _auto_save_timer
    global combo_count, combo_timer, combo_best, shop_open, shop_tab, shop_scroll
    global respawn_timer, respawn_boss, berserk_timer, chaos_timer
    state = "play"
    game_time = 0.0
    shake = 0.0
    player = {
        "x": W - 260, "y": H//2,
        "hp": P_HP, "max_hp": P_HP, "spd": P_SPEED,
        "facing": math.pi,
        "ab": [None, None, None],
        "cd": [0.0, 0.0, 0.0],
        "mcd": 0.0, "scd": 0.0, "manim": 0.0,
        "invuln": 0.0,
    }
    base = {"x": BASE_POS[0], "y": BASE_POS[1], "hp": BASE_HP_MAX, "max_hp": BASE_HP_MAX, "flash":0.0}
    enemies.clear(); clones.clear(); projectiles.clear()
    zones.clear(); orbs.clear(); rings.clear(); chain_vis.clear()
    particles.clear(); dmg_numbers.clear(); powerups.clear(); minions.clear()
    essence = 0; kills = 0; spawn_timer = 1.5
    boss_spawned = set()
    pending_ab = None; pending_boss = False
    dbl_active = False
    atk_multi = 1
    _auto_save_timer = 60.0
    combo_count = 0; combo_timer = 0.0; combo_best = 0
    shop_open = False; shop_tab = 0; shop_scroll = 0
    respawn_timer = 0.0; respawn_boss = None
    berserk_timer = 0.0; chaos_timer = 0.0
    stats["total_dmg"] = 0; stats["melee_kills"] = 0; stats["ability_kills"] = 0
    stats["shots_fired"] = 0; stats["bosses_killed"] = 0; stats["powerups_collected"] = 0
    stats["max_combo"] = 0; stats["deaths"] = 0
    notifications.clear()
    wave_announce["text"] = ""; wave_announce["life"] = 0.0
    global run_xp
    run_xp = profile.get("saved_xp", 0)
    # Apply persistent perks & gear
    apply_perks_and_gear()
    profile["total_runs"] += 1
    save_profile()

# ═══════════════════════════════════════════════════════════════════
#  ENTITY CREATION
# ═══════════════════════════════════════════════════════════════════
def create_enemy(etype, x=None, y=None):
    s = E_STATS[etype]
    if x is None:
        x = random.uniform(-40, -10)
    if y is None:
        y = random.uniform(90, H - 30)
    # scale HP with time + difficulty
    t_scale = 1.0 + game_time / 300.0
    hp_val = s["hp"] * t_scale * DIFF_HP_MULT[difficulty]
    spd_val = s["spd"] * DIFF_SPD_MULT[difficulty]
    dmg_val = int(s["dmg"] * DIFF_DMG_MULT[difficulty])
    e = {
        "x":x, "y":y, "hp":hp_val, "max_hp":hp_val,
        "spd":spd_val, "dmg":dmg_val, "type":etype,
        "col":s["col"], "sides":s["sides"], "sz":s["sz"], "ess":s["ess"],
        "boss":False, "btype":"", "frozen":0.0,
        "hflash":0.0, "acd":0.0, "wander_t":0.0, "wx":0.0, "wy":0.0,
        "elite":"", "shield_hp":0, "phase":0, "tele_cd":0.0, "heal_cd":0.0,
    }
    # Elite modifier chance (increases with time)
    if game_time > 60 and random.random() < min(0.25, game_time / 1200):
        mod = random.choice(ELITE_MODS)
        e["elite"] = mod
        if mod == "shielded":
            e["shield_hp"] = e["max_hp"] * 0.3
        elif mod == "enraged":
            e["spd"] *= 1.4; e["dmg"] = int(e["dmg"] * 1.3)
        elif mod == "vampiric":
            pass  # heals on hit, handled in update
        elif mod == "splitting":
            pass  # splits on death, handled in update
        e["ess"] = int(e["ess"] * 1.5)
    enemies.append(e)

def create_boss(btype):
    s = B_STATS[btype]
    t_scale = 1.0 + game_time / 400.0
    hp_val = s["hp"] * t_scale * DIFF_HP_MULT[difficulty]
    spd_val = s["spd"] * DIFF_SPD_MULT[difficulty]
    dmg_val = int(s["dmg"] * DIFF_DMG_MULT[difficulty])
    enemies.append({
        "x":-50, "y":H//2 + random.uniform(-100,100),
        "hp":hp_val, "max_hp":hp_val,
        "spd":spd_val, "dmg":dmg_val, "type":"boss",
        "col":s["col"], "sides":8, "sz":s["sz"], "ess":s["ess"],
        "boss":True, "btype":btype, "frozen":0.0,
        "hflash":0.0, "acd":0.0, "wander_t":0.0, "wx":0.0, "wy":0.0,
        "elite":"", "shield_hp":0, "phase":0, "tele_cd":0.0, "heal_cd":0.0,
    })
    # Wave announcement
    bname = btype.replace("_", " ").title()
    wave_announce["text"] = f"BOSS: {bname}!"
    wave_announce["life"] = 3.5
    wave_announce["color"] = s["col"]

def create_clone():
    global essence
    if essence < CLONE_COST or sum(1 for c in clones if c["hp"]>0) >= MAX_CLONES:
        return False
    essence -= CLONE_COST
    clone_hp = 60 + get_perk_level("clone_tough") * 15
    clones.append({
        "x":player["x"], "y":player["y"],
        "hp":clone_hp, "max_hp":clone_hp, "spd":P_SPEED*0.7,
        "facing":player["facing"],
        "ab": list(player["ab"]),
        "cd": [0.0, 0.0, 0.0],
        "mcd":0.0, "scd":0.0, "manim":0.0,
    })
    spawn_parts(player["x"], player["y"], C_CLONE, 15, 120, 0.6)
    return True

def create_orb(x, y, etype, is_boss=False, btype=""):
    ab_id = None
    if is_boss and btype in B_STATS:
        ab_id = B_STATS[btype]["abil"]
    elif etype in E_ABIL:
        ab_id = E_ABIL[etype]
    if ab_id:
        orbs.append({"x":x, "y":y, "ab":ab_id, "boss": is_boss, "life":12.0, "t":0.0})

# ═══════════════════════════════════════════════════════════════════
#  ABILITY USE
# ═══════════════════════════════════════════════════════════════════
def use_ability(ab_id, ux, uy, facing, source="player"):
    """Fire an ability effect from position (ux,uy) in direction facing."""
    global shake
    info = ABILS[ab_id]

    if ab_id == "spike_burst":
        for i in range(8):
            a = i * math.pi / 4
            projectiles.append({"x":ux,"y":uy,"vx":math.cos(a)*320,"vy":math.sin(a)*320,
                                "dmg":35,"r":6,"col":info["color"],"life":0.55,
                                "pierce":False,"hit":set(),"src":source})
        spawn_parts(ux, uy, info["color"], 12, 100, 0.3)
        shake = max(shake, 3)

    elif ab_id == "fire_wave":
        projectiles.append({"x":ux,"y":uy,
                            "vx":math.cos(facing)*380,"vy":math.sin(facing)*380,
                            "dmg":55,"r":20,"col":info["color"],"life":0.75,
                            "pierce":True,"hit":set(),"src":source})
        spawn_parts(ux, uy, info["color"], 8, 80, 0.3)
        shake = max(shake, 2)

    elif ab_id == "freeze_pulse":
        rad = 160
        for e in enemies:
            if dst((ux,uy),(e["x"],e["y"])) < rad:
                e["frozen"] = 2.5
        rings.append({"x":ux,"y":uy,"r":0,"mr":rad,"life":0.4,"ml":0.4,"col":info["color"],"w":3})
        spawn_parts(ux, uy, info["color"], 16, 130, 0.4)
        shake = max(shake, 2)

    elif ab_id == "chain_bolt":
        rng = 260
        nearby = [e for e in enemies if dst((ux,uy),(e["x"],e["y"])) < rng]
        pts = [(ux, uy)]
        hit = []
        for _ in range(3):
            if not nearby: break
            tgt = min(nearby, key=lambda e: dst(pts[-1], (e["x"],e["y"])))
            hit.append(tgt)
            pts.append((tgt["x"], tgt["y"]))
            nearby.remove(tgt)
        for e in hit:
            e["hp"] -= 40
            e["hflash"] = 0.15
            spawn_parts(e["x"], e["y"], info["color"], 6, 70, 0.25)
        if len(pts) > 1:
            chain_vis.append({"pts":pts, "life":0.25, "col":info["color"]})
        shake = max(shake, 2)

    elif ab_id == "poison_cloud":
        zones.append({"x":ux,"y":uy,"r":85,"dps":28,"life":4.0,"ml":4.0,"col":info["color"]})
        spawn_parts(ux, uy, info["color"], 10, 60, 0.5, 4)

    elif ab_id == "shadow_dash":
        dash = 190
        ox, oy = ux, uy
        nx = clamp(ux + math.cos(facing)*dash, 30, W-30)
        ny = clamp(uy + math.sin(facing)*dash, 85, H-30)
        mx, my = (ox+nx)/2, (oy+ny)/2
        for e in enemies:
            if dst((e["x"],e["y"]),(mx,my)) < dash/2 + 35:
                e["hp"] -= 50
                e["hflash"] = 0.15
                spawn_parts(e["x"],e["y"], info["color"], 5, 80, 0.3)
        if source == "player":
            player["x"], player["y"] = nx, ny
            player["invuln"] = 0.3
        # trail particles
        steps = 8
        for i in range(steps):
            t = i / steps
            px = lerp(ox, nx, t); py = lerp(oy, ny, t)
            spawn_parts(px, py, info["color"], 3, 50, 0.4, 2)
        shake = max(shake, 4)

    elif ab_id == "titan_slam":
        rad = 220
        for e in enemies:
            d = dst((ux,uy),(e["x"],e["y"]))
            if d < rad:
                e["hp"] -= 90
                e["hflash"] = 0.2
                # knockback
                if d > 1:
                    ndx, ndy = nrm(e["x"]-ux, e["y"]-uy)
                    e["x"] += ndx * 60; e["y"] += ndy * 60
        rings.append({"x":ux,"y":uy,"r":0,"mr":rad,"life":0.5,"ml":0.5,"col":info["color"],"w":5})
        spawn_parts(ux, uy, info["color"], 25, 160, 0.5, 4)
        shake = max(shake, 8)

    elif ab_id == "hydra_volley":
        for i in range(5):
            a = facing + (i - 2) * 0.25
            projectiles.append({"x":ux,"y":uy,"vx":math.cos(a)*300,"vy":math.sin(a)*300,
                                "dmg":55,"r":10,"col":info["color"],"life":1.0,
                                "pierce":False,"hit":set(),"src":source})
        spawn_parts(ux, uy, info["color"], 10, 100, 0.3)
        shake = max(shake, 4)

    elif ab_id == "void_rift":
        zones.append({"x":ux,"y":uy,"r":130,"dps":20,"life":5.0,"ml":5.0,
                       "col":info["color"],"pull":True})
        rings.append({"x":ux,"y":uy,"r":130,"mr":0,"life":5.0,"ml":5.0,"col":info["color"],"w":2})
        spawn_parts(ux, uy, info["color"], 20, 80, 0.6, 3)
        shake = max(shake, 5)

    # --- NEW ABILITIES ---
    elif ab_id == "armor_bash":
        # Heavy forward cone slam with knockback
        rad = 90
        for e in enemies:
            d = dst((ux,uy),(e["x"],e["y"]))
            if d < rad:
                a2e = ang((ux,uy),(e["x"],e["y"]))
                adiff = abs((a2e - facing + math.pi) % (2*math.pi) - math.pi)
                if adiff < math.pi * 0.4:
                    e["hp"] -= 45
                    e["hflash"] = 0.2
                    if d > 1:
                        nd_x, nd_y = nrm(e["x"]-ux, e["y"]-uy)
                        e["x"] += nd_x * 50; e["y"] += nd_y * 50
                    spawn_parts(e["x"], e["y"], info["color"], 4, 60, 0.2)
        rings.append({"x":ux,"y":uy,"r":0,"mr":rad,"life":0.3,"ml":0.3,"col":info["color"],"w":4})
        spawn_parts(ux, uy, info["color"], 10, 80, 0.3)
        shake = max(shake, 4)

    elif ab_id == "heal_pulse":
        # Heal player
        heal = 30 + get_perk_level("regeneration") * 5
        player["hp"] = min(player["max_hp"], player["hp"] + heal)
        # Also heal base slightly
        base["hp"] = min(base["max_hp"], base["hp"] + 15)
        rings.append({"x":ux,"y":uy,"r":0,"mr":120,"life":0.5,"ml":0.5,"col":info["color"],"w":3})
        spawn_parts(ux, uy, info["color"], 15, 100, 0.4, 3)
        # Also heal nearby clones
        for c in clones:
            if dst((ux,uy),(c["x"],c["y"])) < 150:
                c["hp"] = min(c["max_hp"], c["hp"] + 20)

    elif ab_id == "split_shot":
        # Fire 1 bullet that splits into 3 after 0.3s
        for i in range(3):
            a = facing + (i - 1) * 0.3
            projectiles.append({"x":ux,"y":uy,"vx":math.cos(a)*350,"vy":math.sin(a)*350,
                                "dmg":30,"r":7,"col":info["color"],"life":0.7,
                                "pierce":False,"hit":set(),"src":source})
        spawn_parts(ux, uy, info["color"], 6, 70, 0.2)
        shake = max(shake, 2)

    elif ab_id == "phase_blink":
        # Teleport to mouse + invulnerability
        mx, my = pygame.mouse.get_pos()
        old_x, old_y = ux, uy
        nx = clamp(mx, 30, W-30)
        ny = clamp(my, 85, H-30)
        if source == "player":
            player["x"], player["y"] = nx, ny
            player["invuln"] = 1.0
        # Trail
        steps = 10
        for i in range(steps):
            t = i / steps
            px = lerp(old_x, nx, t); py = lerp(old_y, ny, t)
            spawn_parts(px, py, info["color"], 2, 40, 0.5, 2)
        spawn_parts(nx, ny, info["color"], 12, 100, 0.4)

    elif ab_id == "berserk_rage":
        global berserk_timer
        berserk_timer = 5.0
        spawn_parts(ux, uy, info["color"], 20, 120, 0.5)
        rings.append({"x":ux,"y":uy,"r":0,"mr":80,"life":0.3,"ml":0.3,"col":info["color"],"w":3})
        add_notification("BERSERK MODE!", (255, 60, 30), 2.0)
        shake = max(shake, 4)

    elif ab_id == "raise_dead":
        # Summon 3 friendly minions
        for i in range(3):
            a = facing + (i - 1) * 0.8
            mx = ux + math.cos(a) * 50
            my = uy + math.sin(a) * 50
            minions.append({
                "x": mx, "y": my, "hp": 40, "max_hp": 40,
                "spd": 120, "dmg": 10, "life": 10.0,
                "col": info["color"], "facing": facing,
            })
        spawn_parts(ux, uy, info["color"], 15, 80, 0.4)
        shake = max(shake, 2)

    elif ab_id == "golem_wall":
        # Create a line of blocking zones perpendicular to facing
        perp = facing + math.pi / 2
        for i in range(-2, 3):
            wx = ux + math.cos(perp) * i * 35
            wy = uy + math.sin(perp) * i * 35
            zones.append({"x":wx,"y":wy,"r":30,"dps":15,"life":6.0,"ml":6.0,
                          "col":info["color"],"pull":False})
        spawn_parts(ux, uy, info["color"], 15, 80, 0.4)
        shake = max(shake, 5)

    elif ab_id == "storm_call":
        # Lightning strikes on 5 random enemies
        targets = random.sample(enemies, min(5, len(enemies))) if enemies else []
        for e in targets:
            e["hp"] -= 70
            e["hflash"] = 0.2
            e["frozen"] = 0.5
            spawn_parts(e["x"], e["y"], info["color"], 10, 100, 0.3)
            chain_vis.append({"pts":[(e["x"],e["y"]-200),(e["x"],e["y"])],"life":0.3,"col":info["color"]})
        shake = max(shake, 6)

# ═══════════════════════════════════════════════════════════════════
#  UPDATE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════
def get_avail_types():
    """Each difficulty has its own enemy pool that unlocks over time."""
    t = game_time
    types = ["spike"]

    if difficulty == 0:  # Easy — original/normal enemy types
        if t >= 25:  types.append("blaze")
        if t >= 55:  types.append("frost")
        if t >= 90:  types.append("venom")
        if t >= 130: types.append("armored")
        if t >= 180: types.append("shadow")
        if t >= 240: types.append("healer")

    elif difficulty == 1:  # Normal — new/expansion enemy types
        if t >= 25:  types.append("volt")
        if t >= 60:  types.append("splitter")
        if t >= 100: types.append("teleporter")
        if t >= 150: types.append("berserker")
        if t >= 220: types.append("necro")

    else:  # Hard — ALL enemy types, unlocks faster
        if t >= 15:  types.append("blaze")
        if t >= 30:  types.append("volt")
        if t >= 45:  types.append("frost")
        if t >= 60:  types.append("armored")
        if t >= 80:  types.append("venom")
        if t >= 100: types.append("healer")
        if t >= 120: types.append("splitter")
        if t >= 145: types.append("shadow")
        if t >= 170: types.append("teleporter")
        if t >= 200: types.append("berserker")
        if t >= 250: types.append("necro")

    return types

def get_spawn_interval():
    return max(0.35, 1.8 - game_time / 380) * DIFF_SPAWN_MULT[difficulty]

def update_waves(dt):
    global spawn_timer
    spawn_timer -= dt
    # Boss spawns (5 bosses, times scaled by difficulty)
    boss_scale = [1.1, 1.0, 0.8][difficulty]
    boss_times = [(100,"titan"),(200,"hydra"),(300,"void_lord"),(400,"golem_king"),(500,"storm_wyrm")]
    for bt, btype in boss_times:
        if game_time >= bt * boss_scale and btype not in boss_spawned:
            boss_spawned.add(btype)
            create_boss(btype)
            spawn_timer = 3.0
    # Wave announcements for new enemy types (per-difficulty)
    if difficulty == 0:
        type_announce = [(25,"Blazes"),(55,"Frost"),(90,"Venom"),(130,"Armored"),(180,"Shadow"),(240,"Healers")]
    elif difficulty == 1:
        type_announce = [(25,"Volts"),(60,"Splitters"),(100,"Teleporters"),(150,"Berserkers"),(220,"Necromancers")]
    else:
        type_announce = [(15,"Blazes"),(30,"Volts"),(45,"Frost"),(60,"Armored"),
                         (80,"Venom"),(100,"Healers"),(120,"Splitters"),
                         (145,"Shadow"),(170,"Teleporters"),(200,"Berserkers"),(250,"Necromancers")]
    for at, name in type_announce:
        if abs(game_time - at) < dt * 1.1 and wave_announce["life"] <= 0:
            wave_announce["text"] = f"New Threat: {name}!"
            wave_announce["life"] = 2.5
            wave_announce["color"] = (255, 200, 80)
    # Regular spawns
    if spawn_timer <= 0:
        spawn_timer = get_spawn_interval()
        types = get_avail_types()
        count = 1 if game_time < 200 else (random.choice([1,2]) if game_time < 400 else random.choice([1,2,2,3]))
        for _ in range(count):
            create_enemy(random.choice(types))

def update_player(dt):
    p = player
    # Movement
    keys = pygame.key.get_pressed()
    dx, dy = 0, 0
    if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
    if dx != 0 or dy != 0:
        ndx, ndy = nrm(dx, dy)
        spd = p["spd"] * (1.5 if berserk_timer > 0 else 1.0)
        p["x"] += ndx * spd * dt
        p["y"] += ndy * spd * dt
    p["x"] = clamp(p["x"], 30, W - 30)
    # Always face mouse cursor
    mx, my = pygame.mouse.get_pos()
    p["facing"] = math.atan2(my - p["y"], mx - p["x"])
    p["y"] = clamp(p["y"], 85, H - 30)
    # Cooldowns
    p["mcd"] = max(0, p["mcd"] - dt)
    p["scd"] = max(0, p["scd"] - dt)
    p["manim"] = max(0, p["manim"] - dt)
    p["invuln"] = max(0, p["invuln"] - dt)
    for i in range(3):
        p["cd"][i] = max(0, p["cd"][i] - dt)
    # Contact damage from enemies
    dodge_pct = get_gear_stats().get("dodge_pct", 0)
    if p["invuln"] <= 0:
        for e in enemies:
            if dst((p["x"],p["y"]),(e["x"],e["y"])) < 28:
                if dodge_pct > 0 and random.random() < dodge_pct:
                    spawn_dmg_number(p["x"], p["y"] - 16, 0, WHITE)  # miss
                    continue
                # Shielded elite: player can't easily damage them, but they also hit harder? No - just contact damage
                p["hp"] -= e["dmg"] * dt
                if e["boss"]:
                    p["hp"] -= e["dmg"] * 0.5 * dt  # bosses hit harder
    # Regen (base + perk)
    regen_rate = 1.5 + get_perk_level("regeneration") * 0.5
    if p["hp"] < p["max_hp"] and p["hp"] > 0:
        p["hp"] = min(p["max_hp"], p["hp"] + regen_rate * dt)

def do_shoot():
    """Fire projectiles toward mouse cursor. Count = atk_multi."""
    global shake
    p = player
    if p["scd"] > 0: return
    p["scd"] = SHOOT_CD
    mx, my = pygame.mouse.get_pos()
    a = math.atan2(my - p["y"], mx - p["x"])
    p["facing"] = a
    # Damage bonus from perks, gear, berserk
    might_bonus = get_perk_level("might") * 3
    gs = get_gear_stats()
    shoot_mult = 1.0 + gs.get("shoot_pct", 0) + gs.get("all_pct", 0)
    berserk_mult = 2.0 if berserk_timer > 0 else 1.0
    bullet_dmg = int((SHOOT_DMG + might_bonus) * shoot_mult * berserk_mult)
    stats["shots_fired"] += atk_multi
    # Fire atk_multi bullets in a spread
    count = atk_multi
    spread = 0.12  # angle offset between shots
    for bi in range(count):
        offset = (bi - (count - 1) / 2) * spread
        ba = a + offset
        projectiles.append({
            "x": p["x"] + math.cos(ba) * 18,
            "y": p["y"] + math.sin(ba) * 18,
            "vx": math.cos(ba) * SHOOT_SPD, "vy": math.sin(ba) * SHOOT_SPD,
            "dmg": bullet_dmg, "r": 5, "col": C_PLAYER, "life": 0.8,
            "pierce": False, "hit": set(), "src": "player",
        })
        spawn_parts(p["x"] + math.cos(ba)*18, p["y"] + math.sin(ba)*18, C_PLAYER, 3, 40, 0.15, 2)
    shake = max(shake, 0.5)

def do_melee():
    global shake
    p = player
    if p["mcd"] > 0: return
    p["mcd"] = MELEE_CD
    p["manim"] = 0.2
    # Damage bonus from perks, gear, berserk
    might_bonus = get_perk_level("might") * 3
    gs = get_gear_stats()
    melee_mult = 1.0 + gs.get("melee_pct", 0) + gs.get("all_pct", 0)
    berserk_mult = 2.0 if berserk_timer > 0 else 1.0
    melee_dmg = int((MELEE_DMG + might_bonus) * melee_mult * berserk_mult)
    hit = 0
    for e in enemies:
        d = dst((p["x"],p["y"]),(e["x"],e["y"]))
        if d > MELEE_RANGE: continue
        a2e = ang((p["x"],p["y"]),(e["x"],e["y"]))
        adiff = abs((a2e - p["facing"] + math.pi) % (2*math.pi) - math.pi)
        if adiff < MELEE_ARC / 2:
            # Shielded elite takes reduced damage
            actual_dmg = melee_dmg
            if e.get("elite") == "shielded" and e.get("shield_hp", 0) > 0:
                e["shield_hp"] -= actual_dmg
                if e["shield_hp"] <= 0:
                    actual_dmg = -e["shield_hp"]
                    e["shield_hp"] = 0
                else:
                    actual_dmg = 0
            e["hp"] -= actual_dmg
            e["hflash"] = 0.12
            hit += 1
            spawn_dmg_number(e["x"], e["y"] - 14, actual_dmg, WHITE)
            spawn_parts(e["x"], e["y"], WHITE, 4, 60, 0.2)
            # Knockback from titan hammer gear
            if gs.get("knockback"):
                ka = ang((p["x"],p["y"]),(e["x"],e["y"]))
                e["x"] += math.cos(ka) * 40
                e["y"] += math.sin(ka) * 40
    if hit > 0:
        shake = max(shake, 2)
        stats["total_dmg"] += melee_dmg * hit

def try_use_ability(slot):
    p = player
    ab = p["ab"][slot]
    if ab is None or p["cd"][slot] > 0: return
    # Apply quick cast perk
    cd_reduction = 1.0 - get_perk_level("quick_cast") * 0.05
    p["cd"][slot] = ABILS[ab]["cd"] * cd_reduction
    # Fire ability atk_multi times with slight angle offsets
    for i in range(atk_multi):
        off = (i - (atk_multi - 1) / 2) * 0.15
        use_ability(ab, p["x"], p["y"], p["facing"] + off)

def update_enemies(dt):
    global essence, kills, shake, dbl_active, atk_multi, combo_count, combo_timer, run_xp
    gs = get_gear_stats()
    ess_mult = 1.0 + get_perk_level("essence_boost") * 0.15 + gs.get("ess_pct", 0)
    for e in enemies[:]:
        # Frozen
        if e["frozen"] > 0:
            e["frozen"] -= dt
            continue
        e["hflash"] = max(0, e["hflash"] - dt)
        e["acd"] = max(0, e["acd"] - dt)

        # --- Special enemy behaviors ---
        # Teleporter: blink toward base occasionally
        if e["type"] == "teleporter":
            e["tele_cd"] = max(0, e.get("tele_cd", 0) - dt)
            if e["tele_cd"] <= 0 and random.random() < 0.005:
                e["tele_cd"] = 4.0
                e["x"] += random.uniform(80, 160)
                e["y"] += random.uniform(-60, 60)
                e["y"] = clamp(e["y"], 60, H - 20)
                spawn_parts(e["x"], e["y"], e["col"], 8, 80, 0.3)

        # Healer: heal nearby enemies
        if e["type"] == "healer":
            e["heal_cd"] = max(0, e.get("heal_cd", 0) - dt)
            if e["heal_cd"] <= 0:
                e["heal_cd"] = 3.0
                for other in enemies:
                    if other is not e and dst((e["x"],e["y"]),(other["x"],other["y"])) < 120:
                        heal_amt = other["max_hp"] * 0.05
                        other["hp"] = min(other["max_hp"], other["hp"] + heal_amt)
                spawn_parts(e["x"], e["y"], C_HEAL, 6, 50, 0.3, 2)

        # Boss phases: at 50% HP, bosses get faster and stronger
        if e["boss"] and e["phase"] == 0 and e["hp"] < e["max_hp"] * 0.5:
            e["phase"] = 1
            e["spd"] *= 1.4
            e["dmg"] = int(e["dmg"] * 1.3)
            spawn_parts(e["x"], e["y"], e["col"], 20, 120, 0.5)
            add_notification(f"Boss Enraged! (Phase 2)", e["col"], 2.5)
            shake = max(shake, 6)

        # Move toward base (with slight seeking of player if close)
        tx, ty = base["x"], base["y"]
        dp = dst((e["x"],e["y"]),(player["x"],player["y"]))
        if dp < 180 and not e["boss"]:
            tx, ty = player["x"], player["y"]
        elif e["boss"]:
            px_weight = 0.3
            tx = base["x"] * (1 - px_weight) + player["x"] * px_weight
            ty = base["y"] * (1 - px_weight) + player["y"] * px_weight
        ndx, ndy = nrm(tx - e["x"], ty - e["y"])
        spd = e["spd"]
        e["x"] += ndx * spd * dt
        e["y"] += ndy * spd * dt
        e["y"] = clamp(e["y"], 60, H - 20)

        # Damage base on contact
        if dst((e["x"],e["y"]),(base["x"],base["y"])) < 45:
            base["hp"] -= e["dmg"] * dt
            base["flash"] = 0.15
            # Vampiric elite heals on dealing damage
            if e["elite"] == "vampiric":
                e["hp"] = min(e["max_hp"], e["hp"] + e["dmg"] * dt * 0.3)

        # Check death
        if e["hp"] <= 0:
            ex, ey = e["x"], e["y"]
            etype = e["type"]
            is_boss = e["boss"]
            btype = e.get("btype", "")
            elite = e.get("elite", "")
            ess_reward = int(e["ess"] * ess_mult * DIFF_ESS_MULT[difficulty])

            enemies.remove(e)
            essence += ess_reward
            kills += 1
            spawn_parts(ex, ey, e["col"], 15, 100, 0.4)
            shake = max(shake, 3 if is_boss else 1)
            spawn_dmg_number(ex, ey - 10, ess_reward, C_ESS)

            # XP toward perk points
            run_xp += 1
            if run_xp >= XP_PER_PERK:
                run_xp -= XP_PER_PERK
                profile["perk_points"] += 1
                add_notification("+1 Perk Point! (kills)", C_GOLD, 2.5)
                save_profile()

            # Combo
            combo_count += 1
            combo_timer = 2.0
            if combo_count >= 5 and combo_count % 5 == 0:
                bonus = combo_count * 2
                essence += bonus
                add_notification(f"COMBO x{combo_count}! +{bonus} essence", C_ESS, 1.5)

            # Elite: splitting spawns 2 smaller enemies
            if elite == "splitting" and not is_boss:
                for _ in range(2):
                    create_enemy(etype, ex + random.uniform(-20,20), ey + random.uniform(-20,20))

            # Boss kill reward
            if is_boss:
                dbl_active = True
                atk_multi *= 2
                spawn_parts(ex, ey, (255,255,100), 25, 150, 0.6)
                stats["bosses_killed"] += 1
                profile["total_bosses"] += 1
                # Reward perk point
                profile["perk_points"] += 1
                save_profile()
                add_notification("+1 Perk Point!", C_GOLD, 3.0)
                # Roll gear drop
                roll_boss_gear(btype)

            # Drop ability orb
            drop_chance = 1.0 if is_boss else 0.15
            if random.random() < drop_chance:
                create_orb(ex, ey, etype, is_boss, btype)

            # Power-up drop chance
            if random.random() < 0.08:
                spawn_powerup(ex, ey)

def update_clones(dt):
    for c in clones[:]:
        if c["hp"] <= 0:
            spawn_parts(c["x"], c["y"], C_CLONE, 10, 80, 0.4)
            clones.remove(c); continue
        c["mcd"] = max(0, c["mcd"] - dt)
        c["scd"] = max(0, c["scd"] - dt)
        c["manim"] = max(0, c["manim"] - dt)
        for i in range(3):
            c["cd"][i] = max(0, c["cd"][i] - dt)
        # Find nearest enemy
        nearest = None; nd = 999999
        for e in enemies:
            d = dst((c["x"],c["y"]),(e["x"],e["y"]))
            if d < nd:
                nd = d; nearest = e
        if nearest and nd < 250:
            # Move toward
            ndx, ndy = nrm(nearest["x"]-c["x"], nearest["y"]-c["y"])
            c["x"] += ndx * c["spd"] * dt
            c["y"] += ndy * c["spd"] * dt
            c["facing"] = math.atan2(ndy, ndx)
            # Melee
            if nd < MELEE_RANGE and c["mcd"] <= 0:
                c["mcd"] = MELEE_CD * 1.5
                c["manim"] = 0.2
                nearest["hp"] -= MELEE_DMG * 0.7
                nearest["hflash"] = 0.1
                spawn_parts(nearest["x"], nearest["y"], C_CLONE, 3, 50, 0.2)
            # Shoot at enemy
            elif nd < 220 and c["scd"] <= 0:
                c["scd"] = SHOOT_CD * 1.5
                a = math.atan2(nearest["y"]-c["y"], nearest["x"]-c["x"])
                projectiles.append({
                    "x": c["x"]+math.cos(a)*18, "y": c["y"]+math.sin(a)*18,
                    "vx": math.cos(a)*SHOOT_SPD*0.85, "vy": math.sin(a)*SHOOT_SPD*0.85,
                    "dmg": SHOOT_DMG*0.6, "r": 4, "col": C_CLONE, "life": 0.7,
                    "pierce": False, "hit": set(), "src": "clone",
                })
            # Use abilities
            for i in range(3):
                if c["ab"][i] and c["cd"][i] <= 0 and nd < 200:
                    c["cd"][i] = ABILS[c["ab"][i]]["cd"] * 1.3
                    use_ability(c["ab"][i], c["x"], c["y"], c["facing"], "clone")
                    break
        # Contact damage
        for e in enemies:
            if dst((c["x"],c["y"]),(e["x"],e["y"])) < 22:
                c["hp"] -= e["dmg"] * dt

def update_projectiles(dt):
    for p in projectiles[:]:
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
        p["life"] -= dt
        if p["life"] <= 0 or p["x"]<-50 or p["x"]>W+50 or p["y"]<-50 or p["y"]>H+50:
            projectiles.remove(p); continue
        # Hit enemies
        for e in enemies:
            if id(e) in p["hit"]: continue
            if dst((p["x"],p["y"]),(e["x"],e["y"])) < p["r"] + e["sz"]:
                actual_dmg = p["dmg"]
                if e.get("elite") == "shielded" and e.get("shield_hp", 0) > 0:
                    e["shield_hp"] -= actual_dmg
                    if e["shield_hp"] <= 0:
                        actual_dmg = -e["shield_hp"]
                        e["shield_hp"] = 0
                    else:
                        actual_dmg = 0
                e["hp"] -= actual_dmg
                e["hflash"] = 0.12
                p["hit"].add(id(e))
                spawn_dmg_number(e["x"], e["y"] - 14, actual_dmg, p["col"])
                spawn_parts(e["x"], e["y"], p["col"], 5, 70, 0.2)
                stats["total_dmg"] += actual_dmg
                if not p["pierce"]:
                    if p in projectiles:
                        projectiles.remove(p)
                    break

def update_zones(dt):
    for z in zones[:]:
        z["life"] -= dt
        if z["life"] <= 0:
            zones.remove(z); continue
        # Damage enemies in zone
        for e in enemies:
            if dst((z["x"],z["y"]),(e["x"],e["y"])) < z["r"]:
                e["hp"] -= z["dps"] * dt
                if random.random() < 0.1:
                    spawn_parts(e["x"], e["y"], z["col"], 2, 30, 0.2, 2)
        # Pull effect for void rift
        if z.get("pull"):
            for e in enemies:
                d = dst((z["x"],z["y"]),(e["x"],e["y"]))
                if d < z["r"] * 1.5 and d > 10:
                    pull_str = 80
                    ndx, ndy = nrm(z["x"]-e["x"], z["y"]-e["y"])
                    e["x"] += ndx * pull_str * dt
                    e["y"] += ndy * pull_str * dt

def update_orbs(dt):
    global pending_ab, pending_boss, state
    for o in orbs[:]:
        o["life"] -= dt
        o["t"] += dt
        if o["life"] <= 0:
            orbs.remove(o); continue
        # Check pickup
        if dst((player["x"],player["y"]),(o["x"],o["y"])) < ORB_PICKUP:
            ab_id = o["ab"]
            is_boss = o["boss"]
            orbs.remove(o)
            # Check if we need selection
            filled = sum(1 for a in player["ab"] if a is not None)
            if filled >= 3:
                # Full slots: choose which to replace
                pending_ab = ab_id
                pending_boss = is_boss
                state = "select_replace"
            else:
                # Auto-absorb into first empty slot
                for i in range(3):
                    if player["ab"][i] is None:
                        player["ab"][i] = ab_id
                        player["cd"][i] = 0
                        spawn_parts(player["x"], player["y"], ABILS[ab_id]["color"], 15, 100, 0.5)
                        break
            break  # only pick up one per frame

def update_rings(dt):
    for r in rings[:]:
        r["life"] -= dt
        if r["life"] <= 0:
            rings.remove(r); continue
        t = 1 - r["life"] / r["ml"]
        if r["mr"] > r["r"]:
            r["r"] = lerp(0, r["mr"], t)  # expanding
        else:
            r["r"] = lerp(r["mr"], 0, t)  # contracting (void rift)

def update_chains(dt):
    for c in chain_vis[:]:
        c["life"] -= dt
        if c["life"] <= 0:
            chain_vis.remove(c)

# ═══════════════════════════════════════════════════════════════════
#  DAMAGE NUMBERS
# ═══════════════════════════════════════════════════════════════════
def spawn_dmg_number(x, y, amount, col=WHITE):
    dmg_numbers.append({
        "x": x + random.uniform(-10, 10), "y": y - 10,
        "text": str(int(amount)), "col": col,
        "life": 0.8, "ml": 0.8, "vy": -60,
    })

def update_dmg_numbers(dt):
    for d in dmg_numbers[:]:
        d["life"] -= dt
        d["y"] += d["vy"] * dt
        d["vy"] *= 0.95
        if d["life"] <= 0:
            dmg_numbers.remove(d)

def draw_dmg_numbers(surf, sx, sy):
    for d in dmg_numbers:
        a = max(0, d["life"] / d["ml"])
        col = tuple(int(d["col"][i] * a) for i in range(3))
        sz = max(12, int(16 * a))
        fnt = pygame.font.SysFont("consolas", sz, bold=True)
        txt = fnt.render(d["text"], True, col)
        surf.blit(txt, (int(d["x"] + sx - txt.get_width()//2), int(d["y"] + sy)))

# ═══════════════════════════════════════════════════════════════════
#  POWER-UPS
# ═══════════════════════════════════════════════════════════════════
POWERUP_TYPES = {
    "health":  {"col":(80,255,80),  "name":"Health",  "desc":"+30 HP"},
    "speed":   {"col":(80,200,255), "name":"Speed",   "desc":"Speed boost 5s"},
    "shield":  {"col":(200,200,255),"name":"Shield",  "desc":"Invuln 3s"},
    "essence": {"col":C_ESS,        "name":"Essence", "desc":"+20 essence"},
    "damage":  {"col":(255,80,80),  "name":"Power",   "desc":"2x damage 5s"},
}

def spawn_powerup(x, y):
    ptype = random.choice(list(POWERUP_TYPES.keys()))
    powerups.append({"x": x, "y": y, "type": ptype, "life": 8.0, "t": 0.0})

def update_powerups(dt):
    global essence
    for p in powerups[:]:
        p["life"] -= dt
        p["t"] += dt
        if p["life"] <= 0:
            powerups.remove(p); continue
        # Pickup
        if dst((player["x"],player["y"]),(p["x"],p["y"])) < 35:
            ptype = p["type"]
            stats["powerups_collected"] += 1
            if ptype == "health":
                player["hp"] = min(player["max_hp"], player["hp"] + 30)
                add_notification("+30 HP!", (80,255,80), 1.5)
            elif ptype == "speed":
                player["spd"] += 60
                # Temporary - will revert (simplified: just a burst)
                add_notification("Speed Boost!", (80,200,255), 1.5)
            elif ptype == "shield":
                player["invuln"] = max(player["invuln"], 3.0)
                add_notification("Shield Active!", (200,200,255), 1.5)
            elif ptype == "essence":
                bonus = 20 + int(20 * get_gear_stats().get("ess_pct", 0))
                essence += bonus
                add_notification(f"+{bonus} Essence!", C_ESS, 1.5)
            elif ptype == "damage":
                global berserk_timer
                berserk_timer = max(berserk_timer, 5.0)
                add_notification("Power Surge!", (255,80,80), 1.5)
            spawn_parts(p["x"], p["y"], POWERUP_TYPES[ptype]["col"], 10, 80, 0.3)
            powerups.remove(p)
            break

def draw_powerups(surf, sx, sy):
    t = pygame.time.get_ticks() / 1000
    for p in powerups:
        info = POWERUP_TYPES[p["type"]]
        bob = math.sin(p["t"] * 4) * 4
        px, py = int(p["x"]+sx), int(p["y"]+sy+bob)
        # Glow
        gc = tuple(int(info["col"][i]*0.3) for i in range(3))
        pygame.draw.circle(surf, gc, (px, py), 14)
        pygame.draw.circle(surf, info["col"], (px, py), 8)
        # Label
        if p["life"] > 2 or int(p["life"]*5)%2==0:
            dtxt(surf, info["name"], FS, info["col"], px, py-18, "midbottom")

# ═══════════════════════════════════════════════════════════════════
#  FRIENDLY MINIONS (from raise_dead)
# ═══════════════════════════════════════════════════════════════════
def update_minions(dt):
    for m in minions[:]:
        m["life"] -= dt
        if m["life"] <= 0 or m["hp"] <= 0:
            spawn_parts(m["x"], m["y"], m["col"], 5, 50, 0.3)
            minions.remove(m); continue
        # Find nearest enemy and attack
        nearest = None; nd = 999999
        for e in enemies:
            d = dst((m["x"],m["y"]),(e["x"],e["y"]))
            if d < nd:
                nd = d; nearest = e
        if nearest and nd < 200:
            ndx, ndy = nrm(nearest["x"]-m["x"], nearest["y"]-m["y"])
            m["x"] += ndx * m["spd"] * dt
            m["y"] += ndy * m["spd"] * dt
            m["facing"] = math.atan2(ndy, ndx)
            if nd < 30:
                nearest["hp"] -= m["dmg"] * dt
                nearest["hflash"] = 0.1
        # Contact damage from enemies
        for e in enemies:
            if dst((m["x"],m["y"]),(e["x"],e["y"])) < 20:
                m["hp"] -= e["dmg"] * dt

def draw_minions(surf, sx, sy):
    for m in minions:
        mx_draw = int(m["x"]+sx)
        my_draw = int(m["y"]+sy) - 4
        a = min(1.0, m["life"] / 2.0)
        col = tuple(int(m["col"][i]*a) for i in range(3))
        draw_shadow(surf, m["x"]+sx, m["y"]+sy, 8)
        draw_entity_shape(surf, mx_draw, my_draw, 8, 5, col, pygame.time.get_ticks()/1000, 1)

def update_game(dt):
    global game_time, shake, state, combo_count, combo_timer, combo_best
    global respawn_timer, respawn_boss, berserk_timer, chaos_timer
    game_time += dt
    shake = max(0, shake - 12 * dt)
    base["flash"] = max(0, base["flash"] - dt)

    # --- Respawn logic (player is dead, waiting to respawn) ---
    if respawn_timer > 0:
        respawn_timer -= dt
        if respawn_timer <= 0:
            # Respawn player
            player["hp"] = player["max_hp"]
            player["x"] = base["x"] - 80
            player["y"] = base["y"]
            player["invuln"] = 3.0
            spawn_parts(player["x"], player["y"], C_PLAYER, 20, 120, 0.6)
            add_notification("Respawned!", (80, 255, 80), 2.0)
            # Clear non-boss enemies
            for e in enemies[:]:
                if not e["boss"]:
                    enemies.remove(e)
            # Re-fight most recent boss
            if respawn_boss and respawn_boss in B_STATS:
                # Check if that boss is already alive
                alive = any(e["boss"] and e["btype"] == respawn_boss for e in enemies)
                if not alive:
                    create_boss(respawn_boss)
                    add_notification(f"Boss re-fight: {respawn_boss.replace('_',' ').title()}!", (255, 80, 80), 3.0)
            respawn_boss = None
        else:
            # Still dead — only update minimal things
            update_parts(dt)
            update_notifications(dt)
            update_zones(dt)
            update_rings(dt)
            update_chains(dt)
            return

    # --- Berserk buff ---
    if berserk_timer > 0:
        berserk_timer -= dt
        if berserk_timer <= 0:
            add_notification("Berserk ended", GRAY, 1.5)

    # --- Chaos gem: random ability every 30s ---
    gs = get_gear_stats()
    if gs.get("chaos"):
        chaos_timer -= dt
        if chaos_timer <= 0:
            chaos_timer = 30.0
            all_abs = [k for k in ABILS if not ABILS[k]["boss"]]
            rand_ab = random.choice(all_abs)
            use_ability(rand_ab, player["x"], player["y"], player["facing"])
            add_notification(f"Chaos: {ABILS[rand_ab]['name']}!", (255, 200, 50), 1.5)

    # --- Combo timer decay ---
    if combo_timer > 0:
        combo_timer -= dt
        if combo_timer <= 0:
            if combo_count > combo_best:
                combo_best = combo_count
            if combo_count > stats["max_combo"]:
                stats["max_combo"] = combo_count
            combo_count = 0

    update_waves(dt)
    update_player(dt)
    update_enemies(dt)
    update_clones(dt)
    update_minions(dt)
    update_projectiles(dt)
    update_zones(dt)
    update_orbs(dt)
    update_rings(dt)
    update_chains(dt)
    update_parts(dt)
    update_notifications(dt)
    update_dmg_numbers(dt)
    update_powerups(dt)

    # --- Wave announcement decay ---
    if wave_announce["life"] > 0:
        wave_announce["life"] -= dt

    # Auto-save every 60 seconds
    global _auto_save_timer
    _auto_save_timer -= dt
    if _auto_save_timer <= 0:
        _auto_save_timer = 60.0
        save_game()

    # --- Win/lose ---
    if base["hp"] <= 0:
        base["hp"] = 0
        state = "lose"
        if game_time > best["time"]:
            best["time"] = game_time
        if kills > best["kills"]:
            best["kills"] = kills
        # Award perk points based on progress
        pts = stats["bosses_killed"] + (1 if game_time > 180 else 0)
        if pts > 0:
            profile["perk_points"] += pts
            profile["total_kills"] += kills
        profile["saved_xp"] = run_xp
        save_profile()
        save_best()
        delete_game_save()

    # --- Player death → respawn + refight boss (no game over!) ---
    if player["hp"] <= 0 and respawn_timer <= 0:
        player["hp"] = 0
        stats["deaths"] += 1
        spawn_parts(player["x"], player["y"], (255, 80, 80), 25, 120, 0.5)
        shake = max(shake, 8)
        add_notification("You died! Respawning...", (255, 80, 80), 2.5)
        respawn_timer = 2.0
        # Find most recent boss type
        boss_list = [(120,"titan"),(240,"hydra"),(360,"void_lord"),(450,"golem_king"),(540,"storm_wyrm")]
        respawn_boss = None
        for bt, btype in boss_list:
            if btype in boss_spawned:
                respawn_boss = btype
        # Lose some essence as penalty
        essence_loss = max(0, essence // 4)
        essence = max(0, essence - essence_loss)
        if essence_loss > 0:
            add_notification(f"Lost {essence_loss} essence!", (255, 180, 80), 2.0)

    if game_time >= DURATION:
        state = "win"
        best["wins"] = best.get("wins",0) + 1
        if kills > best["kills"]:
            best["kills"] = kills
        best["time"] = DURATION
        # Award perk points on win (bonus!)
        pts = stats["bosses_killed"] + 3
        profile["perk_points"] += pts
        profile["total_wins"] += 1
        profile["total_kills"] += kills
        profile["saved_xp"] = run_xp
        save_profile()
        save_best()
        delete_game_save()

# ═══════════════════════════════════════════════════════════════════
#  DRAWING
# ═══════════════════════════════════════════════════════════════════

def draw_wave_announce(surf):
    if wave_announce["life"] > 0:
        alpha = min(1.0, wave_announce["life"] * 2) * 255
        tc = wave_announce["color"]
        dtxt(surf, wave_announce["text"], FL, tc, W // 2, 100, "midtop")

def draw_combo(surf):
    if combo_count >= 3:
        pulse = 1.0 + 0.15 * math.sin(game_time * 8)
        cc = (255, 200, 50)
        dtxt(surf, f"COMBO x{combo_count}", FM, cc, W - 20, 80, "topright")
        if combo_best > 10:
            dtxt(surf, f"Best: x{combo_best}", FS, GRAY, W - 20, 102, "topright")

def draw_minimap(surf):
    mm_w, mm_h = 140, 90
    mm_x, mm_y = W - mm_w - 10, H - mm_h - 70
    mm_surf = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
    mm_surf.fill((10, 10, 20, 180))
    sx_scale, sy_scale = mm_w / W, mm_h / H
    # Base
    bx, by = int(base["x"] * sx_scale), int(base["y"] * sy_scale)
    pygame.draw.rect(mm_surf, C_BASE, (bx - 3, by - 3, 6, 6))
    # Player
    px, py_ = int(player["x"] * sx_scale), int(player["y"] * sy_scale)
    pygame.draw.rect(mm_surf, C_PLAYER, (px - 2, py_ - 2, 4, 4))
    # Enemies
    for e in enemies:
        ex, ey = int(e["x"] * sx_scale), int(e["y"] * sy_scale)
        col = (255, 100, 100) if e["boss"] else (255, 60, 60)
        sz = 3 if e["boss"] else 1
        pygame.draw.rect(mm_surf, col, (ex - sz, ey - sz, sz * 2, sz * 2))
    # Clones
    for c in clones:
        cx, cy = int(c["x"] * sx_scale), int(c["y"] * sy_scale)
        pygame.draw.rect(mm_surf, C_CLONE, (cx - 1, cy - 1, 3, 3))
    # Powerups
    for pu in powerups:
        ppx, ppy = int(pu["x"] * sx_scale), int(pu["y"] * sy_scale)
        pygame.draw.rect(mm_surf, C_GOLD, (ppx, ppy, 2, 2))
    pygame.draw.rect(mm_surf, GRAY, (0, 0, mm_w, mm_h), 1)
    surf.blit(mm_surf, (mm_x, mm_y))

def draw_shop(surf):
    if not shop_open: return
    # Full overlay
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surf.blit(overlay, (0, 0))
    panel_x, panel_y = 100, 60
    panel_w, panel_h = W - 200, H - 120
    pygame.draw.rect(surf, (20, 20, 30), (panel_x, panel_y, panel_w, panel_h), border_radius=8)
    pygame.draw.rect(surf, C_ESS, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=8)

    dtxt(surf, "PERK SHOP", FL, C_GOLD, W // 2, panel_y + 12, "midtop")
    dtxt(surf, f"Perk Points: {profile['perk_points']}", FM, C_ESS, W // 2, panel_y + 48, "midtop")
    dtxt(surf, "[TAB] Close   |   [1-8] Buy Perk   |   [G] Gear", FS, GRAY, W // 2, panel_y + 72, "midtop")

    if shop_tab == 0:
        # PERKS tab
        dtxt(surf, "═══ PERKS ═══", FM, WHITE, W // 2, panel_y + 95, "midtop")
        for idx, pk in enumerate(PERK_ORDER):
            pdata = PERKS[pk]
            lvl = get_perk_level(pk)
            py = panel_y + 120 + idx * 36
            # Number key
            num = idx + 1
            # Level bar
            max_lvl = pdata["max_lvl"]
            col = C_GOLD if lvl < max_lvl else (100, 255, 100)
            cost = pdata["costs"][lvl] if lvl < max_lvl else 0
            cost_str = f"Cost: {cost}" if lvl < max_lvl else "MAXED"
            can_buy = lvl < max_lvl and profile["perk_points"] >= cost
            tc = WHITE if can_buy else GRAY
            dtxt(surf, f"[{num}]", FS, tc, panel_x + 20, py)
            dtxt(surf, f"{pdata['name']}", FM, col, panel_x + 55, py)
            dtxt(surf, f"Lv {lvl}/{max_lvl}", FS, WHITE, panel_x + 220, py)
            dtxt(surf, pdata["desc"], FS, GRAY, panel_x + 310, py)
            dtxt(surf, cost_str, FS, tc, panel_x + 520, py)
    else:
        # GEAR tab
        dtxt(surf, "═══ GEAR ═══", FM, WHITE, W // 2, panel_y + 95, "midtop")
        # Equipped slots
        slot_labels = ["Weapon", "Armor", "Accessory"]
        slot_keys = ["weapon", "armor", "accessory"]
        for si, (slbl, skey) in enumerate(zip(slot_labels, slot_keys)):
            py = panel_y + 122 + si * 30
            gid = profile["equipped"][skey]
            dtxt(surf, f"{slbl}:", FM, GRAY, panel_x + 20, py)
            if gid and gid in GEAR_DB:
                g = GEAR_DB[gid]
                rcol = RARITY_COLORS.get(g["rarity"], WHITE)
                dtxt(surf, g["name"], FM, rcol, panel_x + 140, py)
                dtxt(surf, g["desc"], FS, GRAY, panel_x + 320, py)
                dtxt(surf, f"[U] Unequip", FS, (255,180,180), panel_x + 560, py)
            else:
                dtxt(surf, "(none)", FS, DGRAY, panel_x + 140, py)
        # Inventory
        dtxt(surf, "─── Inventory ───", FS, GRAY, W // 2, panel_y + 220, "midtop")
        inv = profile.get("inventory", [])
        for ii, gid in enumerate(inv):
            if gid not in GEAR_DB: continue
            py = panel_y + 245 + ii * 26
            if py > panel_y + panel_h - 30: break
            g = GEAR_DB[gid]
            rcol = RARITY_COLORS.get(g["rarity"], WHITE)
            equipped = any(v == gid for v in profile["equipped"].values())
            tag = " [E]" if equipped else ""
            dtxt(surf, f"[{ii+1}]", FS, WHITE, panel_x + 20, py)
            dtxt(surf, f"{g['name']}{tag}", FM, rcol, panel_x + 55, py)
            dtxt(surf, f"({g['slot']})", FS, GRAY, panel_x + 250, py)
            dtxt(surf, g["desc"], FS, GRAY, panel_x + 330, py)

def draw_respawn_overlay(surf):
    if respawn_timer > 0:
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surf.blit(overlay, (0, 0))
        dtxt(surf, "RESPAWNING...", FL, (255, 80, 80), W // 2, H // 2 - 30, "center")
        dtxt(surf, f"{respawn_timer:.1f}s", FM, WHITE, W // 2, H // 2 + 10, "center")
        dtxt(surf, f"Re-fight: {respawn_boss.upper() if respawn_boss else '???'}", FM, (255, 200, 100), W // 2, H // 2 + 40, "center")

def draw_berserk_indicator(surf):
    if berserk_timer > 0:
        pulse = int(100 + 100 * abs(math.sin(game_time * 6)))
        col = (255, pulse // 2, pulse // 4)
        dtxt(surf, f"BERSERK! {berserk_timer:.1f}s", FM, col, W // 2, 130, "midtop")

def draw_ground(surf, sx, sy):
    surf.fill(BG)
    # Grid with slight fade
    for x in range(0, W+1, 64):
        a = 0.3 + 0.2 * (x / W)
        c = tuple(int(GRID[i] * a + BG[i] * (1-a)) for i in range(3))
        pygame.draw.line(surf, c, (x + int(sx), 0), (x + int(sx), H))
    for y in range(0, H+1, 64):
        a = 0.4 + 0.3 * (y / H)
        c = tuple(int(GRID[i] * a + BG[i] * (1-a)) for i in range(3))
        pygame.draw.line(surf, c, (0, y + int(sy)), (W, y + int(sy)))
    # Spawn zone indicator
    pygame.draw.rect(surf, (15, 12, 25), (0, 0, 60, H))

def draw_entity_shape(surf, x, y, sz, sides, col, rot=0, outline=0):
    """Draw a geometric shape. sides=0 means circle."""
    ix, iy = int(x), int(y)
    if sides == 0:
        pygame.draw.circle(surf, col, (ix, iy), sz)
        if outline:
            pygame.draw.circle(surf, WHITE, (ix, iy), sz, outline)
    else:
        pts = ppoly(ix, iy, sz, sides, rot)
        pygame.draw.polygon(surf, col, pts)
        if outline:
            pygame.draw.polygon(surf, WHITE, pts, outline)

def draw_shadow(surf, x, y, sz):
    """Draw shadow ellipse."""
    pygame.draw.ellipse(surf, (5, 5, 10), (int(x - sz*0.7), int(y + sz*0.3), int(sz*1.4), int(sz*0.5)))

def draw_hp_bar(surf, x, y, w, h, ratio, col):
    pygame.draw.rect(surf, (30,30,30), (int(x-w/2), int(y), w, h))
    pygame.draw.rect(surf, col, (int(x-w/2), int(y), int(w * max(0,ratio)), h))

def draw_base(surf, sx, sy):
    bx, by = base["x"]+sx, base["y"]+sy
    # Glow
    t = pygame.time.get_ticks() / 1000
    glow_r = 50 + math.sin(t * 2) * 8
    for i in range(3):
        a = 0.15 - i * 0.04
        c = tuple(int(C_BASE[j] * a) for j in range(3))
        pygame.draw.circle(surf, c, (int(bx), int(by)), int(glow_r + i * 12))
    # Main shape
    pts = ppoly(bx, by, 35, 8, t * 0.3)
    col = C_BASE if base["flash"] <= 0 else (255, 80, 80)
    pygame.draw.polygon(surf, col, pts)
    pygame.draw.polygon(surf, WHITE, pts, 2)
    # HP bar
    draw_hp_bar(surf, bx, by - 50, 70, 6, base["hp"]/base["max_hp"], C_BASE)
    dtxt(surf, "BASE", FS, GRAY, int(bx), int(by - 60), "midbottom")

def draw_player_entity(surf, px, py, p, col_tint=None):
    """Draw player or clone."""
    # Determine shape based on abilities
    n_ab = sum(1 for a in p["ab"] if a is not None)
    sides = 4 + n_ab  # 4-7 sides
    ab_cols = [ABILS[a]["color"] for a in p["ab"] if a is not None]
    col = bcol(ab_cols) if ab_cols else C_PLAYER
    if col_tint:
        col = lc(col, col_tint, 0.4)
    sz = 16
    t = pygame.time.get_ticks() / 1000
    # Shadow
    draw_shadow(surf, px, py, sz)
    # Body (lifted slightly for 2.5D)
    by = py - 6
    rot = t * 0.5
    draw_entity_shape(surf, px, by, sz, sides, col, rot, 2)
    # Invuln flash
    if p.get("invuln", 0) > 0 and int(t * 20) % 2 == 0:
        draw_entity_shape(surf, px, by, sz + 3, sides, WHITE, rot, 1)
    # Melee swing visual
    if p["manim"] > 0:
        swing_a = p["facing"]
        arc_r = MELEE_RANGE
        for i in range(-3, 4):
            a = swing_a + i * 0.12
            ex = px + math.cos(a) * arc_r * (1 - p["manim"]*3)
            ey = by + math.sin(a) * arc_r * (1 - p["manim"]*3)
            pygame.draw.circle(surf, WHITE, (int(ex), int(ey)), 2)

def draw_enemy_entity(surf, e, sx, sy):
    ex, ey = e["x"]+sx, e["y"]+sy
    sz = e["sz"]
    # Shadow
    draw_shadow(surf, ex, ey, sz)
    # Body
    height = 8 if not e["boss"] else 12
    by = ey - height
    col = e["col"]
    if e["hflash"] > 0:
        col = lc(col, WHITE, e["hflash"] * 5)
    if e["frozen"] > 0:
        col = lc(col, C_FROST, 0.6)
    rot = pygame.time.get_ticks() / 1000 * (2 if not e["boss"] else 0.8)
    sides = e["sides"] if e["sides"] > 0 else 0
    draw_entity_shape(surf, ex, by, sz, sides, col, rot, 1 if not e["boss"] else 2)
    # Boss aura
    if e["boss"]:
        for i in range(2):
            r = sz + 8 + i * 6 + math.sin(rot * 3 + i) * 3
            ac = tuple(int(e["col"][j] * 0.3) for j in range(3))
            pygame.draw.circle(surf, ac, (int(ex), int(by)), int(r), 1)
    # HP bar
    if e["hp"] < e["max_hp"]:
        bw = 30 if not e["boss"] else 60
        draw_hp_bar(surf, ex, by - sz - 8, bw, 4, e["hp"]/e["max_hp"], e["col"])
    # Frozen indicator
    if e["frozen"] > 0:
        pygame.draw.circle(surf, C_FROST, (int(ex), int(by)), sz + 4, 2)
    # Elite indicator
    elite = e.get("elite", "")
    if elite:
        t = pygame.time.get_ticks() / 1000
        elite_cols = {"shielded": C_SHIELD, "enraged": C_BERSERK, "vampiric": (180, 0, 60), "splitting": C_SPLIT}
        ec = elite_cols.get(elite, WHITE)
        # Pulsing ring
        pulse = sz + 6 + math.sin(t * 5) * 3
        pygame.draw.circle(surf, ec, (int(ex), int(by)), int(pulse), 1)
        # Shield bar for shielded elites
        if elite == "shielded" and e.get("shield_hp", 0) > 0:
            shp_ratio = e["shield_hp"] / (e["max_hp"] * 0.3)
            bw = 30 if not e["boss"] else 60
            draw_hp_bar(surf, ex, by - sz - 14, bw, 3, shp_ratio, C_SHIELD)
    # Boss phase 2 visual
    if e["boss"] and e.get("phase", 0) >= 1:
        t = pygame.time.get_ticks() / 1000
        for i in range(3):
            a = t * 4 + i * 2.09
            rx, ry = ex + math.cos(a) * (sz + 15), by + math.sin(a) * (sz + 15)
            pygame.draw.circle(surf, (255, 60, 60), (int(rx), int(ry)), 3)

def draw_zones(surf, sx, sy):
    for z in zones:
        a = max(0.1, z["life"] / z["ml"])
        col = tuple(int(z["col"][i] * a * 0.4) for i in range(3))
        pygame.draw.circle(surf, col, (int(z["x"]+sx), int(z["y"]+sy)), int(z["r"]))
        # Edge
        ecol = tuple(int(z["col"][i] * a) for i in range(3))
        pygame.draw.circle(surf, ecol, (int(z["x"]+sx), int(z["y"]+sy)), int(z["r"]), 2)

def draw_projectiles(surf, sx, sy):
    for p in projectiles:
        c = p["col"]
        pygame.draw.circle(surf, c, (int(p["x"]+sx), int(p["y"]+sy)), max(3, p["r"]))
        # Trail
        tx = p["x"] - p["vx"]*0.03
        ty = p["y"] - p["vy"]*0.03
        pygame.draw.line(surf, c, (int(p["x"]+sx),int(p["y"]+sy)), (int(tx+sx),int(ty+sy)), 2)

def draw_rings(surf, sx, sy):
    for r in rings:
        a = max(0, r["life"] / r["ml"])
        col = tuple(int(r["col"][i] * a) for i in range(3))
        if r["r"] > 2:
            pygame.draw.circle(surf, col, (int(r["x"]+sx), int(r["y"]+sy)), int(r["r"]), max(1,r["w"]))

def draw_chains(surf, sx, sy):
    for c in chain_vis:
        a = max(0, c["life"] / 0.25)
        col = tuple(int(c["col"][i] * a) for i in range(3))
        pts = c["pts"]
        for i in range(len(pts)-1):
            p1 = (int(pts[i][0]+sx), int(pts[i][1]+sy))
            p2 = (int(pts[i+1][0]+sx), int(pts[i+1][1]+sy))
            # Zigzag lightning
            mid_pts = [p1]
            segs = 4
            for s in range(1, segs):
                t = s / segs
                mx = lerp(p1[0], p2[0], t) + random.uniform(-8, 8)
                my = lerp(p1[1], p2[1], t) + random.uniform(-8, 8)
                mid_pts.append((int(mx), int(my)))
            mid_pts.append(p2)
            pygame.draw.lines(surf, col, False, mid_pts, 2)

def draw_orbs(surf, sx, sy):
    t = pygame.time.get_ticks() / 1000
    for o in orbs:
        ox, oy = o["x"]+sx, o["y"]+sy
        bob = math.sin(o["t"] * 3) * 5
        col = ABILS[o["ab"]]["color"]
        sz = 10 + math.sin(o["t"] * 4) * 2
        pygame.draw.circle(surf, col, (int(ox), int(oy - 10 + bob)), int(sz))
        # Glow
        gc = tuple(int(col[i]*0.3) for i in range(3))
        pygame.draw.circle(surf, gc, (int(ox), int(oy - 10 + bob)), int(sz + 6))
        # Label
        dtxt(surf, ABILS[o["ab"]]["name"], FS, col, int(ox), int(oy - 25 + bob), "midbottom")
        if o["boss"]:
            dtxt(surf, "BOSS", FS, (255,80,80), int(ox), int(oy - 38 + bob), "midbottom")

def draw_hud(surf):
    # Top bar background
    pygame.draw.rect(surf, (8, 8, 14), (0, 0, W, 72))
    pygame.draw.line(surf, GRID, (0, 72), (W, 72), 2)

    # Timer
    remaining = max(0, DURATION - game_time)
    mins = int(remaining) // 60
    secs = int(remaining) % 60
    timer_col = WHITE if remaining > 60 else ((255,80,80) if int(remaining*3)%2==0 else WHITE)
    dtxt(surf, f"{mins:02d}:{secs:02d}", FL, timer_col, W//2, 8, "midtop")
    dtxt(surf, "SURVIVE", FS, GRAY, W//2, 45, "midtop")

    # Player HP
    dtxt(surf, "HP", FS, GRAY, 15, 8)
    draw_hp_bar(surf, 80, 8, 150, 14, player["hp"]/player["max_hp"], (80,220,80))
    dtxt(surf, f"{int(player['hp'])}/{player['max_hp']}", FS, WHITE, 155, 8, "midtop")

    # Base HP
    dtxt(surf, "BASE", FS, GRAY, 15, 30)
    draw_hp_bar(surf, 80, 30, 150, 14, base["hp"]/base["max_hp"], C_BASE)
    dtxt(surf, f"{int(base['hp'])}/{base['max_hp']}", FS, WHITE, 155, 30, "midtop")

    # Essence + Kills
    dtxt(surf, f"Essence: {essence}", FM, C_ESS, 15, 52)
    dtxt(surf, f"Kills: {kills}", FS, GRAY, 180, 55)

    # Clone info
    nc = sum(1 for c in clones if c["hp"] > 0)
    clone_col = WHITE if essence >= CLONE_COST else GRAY
    dtxt(surf, f"[F] Clone: {nc}/{MAX_CLONES}  ({CLONE_COST} ess)", FS, clone_col, W - 250, 8)

    # Double-attack status
    if dbl_active:
        dbl_col = (255, 255, 100) if int(game_time * 4) % 2 == 0 else (255, 220, 60)
        dtxt(surf, f"x{atk_multi} ATTACKS", FM, dbl_col, W - 250, 28)
        # Also show a small icon near crosshair area
        dtxt(surf, f"x{atk_multi}", FM, dbl_col, W//2 + 60, 48, "midtop")

    # Ability slots - bottom of screen
    slot_y = H - 60
    slot_w = 170
    slot_h = 48
    keys_label = ["Q", "E", "R"]
    for i in range(3):
        sx = W//2 - (3 * slot_w + 20) // 2 + i * (slot_w + 10)
        ab = player["ab"][i]
        # Background
        bg_col = (20, 20, 30) if ab else (15, 15, 20)
        pygame.draw.rect(surf, bg_col, (sx, slot_y, slot_w, slot_h), border_radius=6)
        pygame.draw.rect(surf, GRAY, (sx, slot_y, slot_w, slot_h), 1, border_radius=6)
        # Key label
        dtxt(surf, f"[{keys_label[i]}]", FM, WHITE, sx + 5, slot_y + 3)
        if ab:
            info = ABILS[ab]
            dtxt(surf, info["name"], FS, info["color"], sx + 38, slot_y + 5)
            # Cooldown bar
            cd_ratio = player["cd"][i] / info["cd"] if info["cd"] > 0 else 0
            bar_w = slot_w - 8
            pygame.draw.rect(surf, (30,30,40), (sx+4, slot_y+28, bar_w, 12))
            if cd_ratio > 0:
                pygame.draw.rect(surf, (60,40,40), (sx+4, slot_y+28, int(bar_w*cd_ratio), 12))
            else:
                pygame.draw.rect(surf, info["color"], (sx+4, slot_y+28, bar_w, 12))
                dtxt(surf, "READY", FS, BLACK, sx + slot_w//2, slot_y + 28, "midtop")
            if cd_ratio > 0:
                dtxt(surf, f"{player['cd'][i]:.1f}s", FS, GRAY, sx + slot_w//2, slot_y + 28, "midtop")
        else:
            dtxt(surf, "(empty)", FS, DGRAY, sx + 38, slot_y + 15)

    # Wave info
    if any(e["boss"] for e in enemies):
        bname = next((e["btype"].upper() for e in enemies if e["boss"]), "BOSS")
        if int(game_time * 4) % 2 == 0:
            dtxt(surf, f"!! BOSS: {bname} !!", FM, (255,60,60), W//2, 76, "midtop")

    # Deaths counter
    if stats["deaths"] > 0:
        dtxt(surf, f"Deaths: {stats['deaths']}", FS, (255, 120, 120), 280, 55)

    # TAB hint
    dtxt(surf, "[TAB] Perks", FS, C_GOLD, W - 100, 55)

    # Difficulty indicator
    dtxt(surf, DIFF_NAMES[difficulty], FS, DIFF_COLORS[difficulty], W // 2, 58, "midtop")

    # XP bar toward next perk point
    xp_bar_x = 260
    xp_bar_y = 55
    xp_bar_w = 120
    xp_bar_h = 10
    xp_ratio = run_xp / XP_PER_PERK if XP_PER_PERK > 0 else 0
    pygame.draw.rect(surf, (25, 25, 35), (xp_bar_x, xp_bar_y, xp_bar_w, xp_bar_h), border_radius=3)
    if xp_ratio > 0:
        pygame.draw.rect(surf, C_GOLD, (xp_bar_x, xp_bar_y, int(xp_bar_w * xp_ratio), xp_bar_h), border_radius=3)
    pygame.draw.rect(surf, GRAY, (xp_bar_x, xp_bar_y, xp_bar_w, xp_bar_h), 1, border_radius=3)
    dtxt(surf, f"XP {run_xp}/{XP_PER_PERK}", FS, C_GOLD, xp_bar_x + xp_bar_w + 5, xp_bar_y - 1)

def draw_selection_ui(surf):
    """Draw ability selection overlay."""
    # Dim overlay
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surf.blit(overlay, (0, 0))

    ab_info = ABILS[pending_ab]

    if state == "select_replace":
        if pending_boss:
            dtxt(surf, "BOSS POWER!", FX, ab_info["color"], W//2, 100, "midtop")
        else:
            dtxt(surf, "NEW ABILITY FOUND!", FX, ab_info["color"], W//2, 100, "midtop")
        dtxt(surf, ab_info["name"], FL, ab_info["color"], W//2, 160, "midtop")
        dtxt(surf, ab_info["desc"], FM, WHITE, W//2, 200, "midtop")
        dtxt(surf, "Click ability to REPLACE (or press 1, 2, 3):", FM, GRAY, W//2, 260, "midtop")
        dtxt(surf, "Right-click or ESC to skip", FS, DGRAY, W//2, 290, "midtop")

    # Draw current ability cards
    keys_label = ["1 (Q)", "2 (E)", "3 (R)"]
    card_w, card_h = 220, 130
    total_w = 3 * card_w + 40
    start_x = W//2 - total_w//2
    for i in range(3):
        cx = start_x + i * (card_w + 20)
        cy = 330
        ab = player["ab"][i]
        # Card bg
        col = ABILS[ab]["color"] if ab else DGRAY
        bg = tuple(int(col[j] * 0.2) for j in range(3))
        pygame.draw.rect(surf, bg, (cx, cy, card_w, card_h), border_radius=8)
        pygame.draw.rect(surf, col if ab else GRAY, (cx, cy, card_w, card_h), 2, border_radius=8)
        # Key
        dtxt(surf, keys_label[i], FM, WHITE, cx + card_w//2, cy + 10, "midtop")
        if ab:
            info = ABILS[ab]
            dtxt(surf, info["name"], FM, info["color"], cx + card_w//2, cy + 40, "midtop")
            dtxt(surf, info["desc"], FS, GRAY, cx + card_w//2, cy + 70, "midtop")
            label = "REPLACE"
            dtxt(surf, f"[{label}]", FS, WHITE, cx + card_w//2, cy + 100, "midtop")
        else:
            dtxt(surf, "(empty)", FS, DGRAY, cx + card_w//2, cy + 55, "midtop")

    # Show new ability preview
    if state == "select_replace":
        py = 500
        dtxt(surf, "Will gain:", FS, GRAY, W//2, py, "midtop")
        pygame.draw.rect(surf, tuple(int(ab_info["color"][j]*0.25) for j in range(3)),
                         (W//2-110, py+25, 220, 60), border_radius=8)
        pygame.draw.rect(surf, ab_info["color"], (W//2-110, py+25, 220, 60), 2, border_radius=8)
        dtxt(surf, ab_info["name"], FM, ab_info["color"], W//2, py+35, "midtop")
        dtxt(surf, ab_info["desc"], FS, WHITE, W//2, py+60, "midtop")

def draw_title(surf):
    surf.fill(BG)
    # Grid
    for x in range(0, W+1, 64):
        pygame.draw.line(surf, GRID, (x, 0), (x, H))
    for y in range(0, H+1, 64):
        pygame.draw.line(surf, GRID, (0, y), (W, y))

    t = pygame.time.get_ticks() / 1000

    # Title
    dtxt(surf, "SHAPE SHIFTER", FT, WHITE, W//2, 120, "midtop")
    dtxt(surf, "T D", FT, C_BASE, W//2, 185, "midtop")

    # Floating shapes
    for i in range(6):
        cols = [C_SPIKE, C_FIRE, C_FROST, C_VOLT, C_VENOM, C_SHADOW]
        sides = [3, 0, 6, 4, 5, 7]
        x = 180 + i * 170
        y = 310 + math.sin(t * 1.5 + i * 1.2) * 15
        draw_entity_shape(surf, x, y, 20, sides[i], cols[i], t + i, 2)

    dtxt(surf, "Absorb enemy abilities. Defend your base.", FM, GRAY, W//2, 380, "midtop")
    dtxt(surf, "Survive 10 minutes!", FM, C_ESS, W//2, 410, "midtop")

    # Difficulty selector
    dtxt(surf, f"Difficulty: ", FM, GRAY, W//2 - 80, 440, "midtop")
    dcol = DIFF_COLORS[difficulty]
    pulse = 0.7 + 0.3 * math.sin(t * 3)
    dc_pulse = tuple(int(c * pulse) for c in dcol)
    dtxt(surf, f"< {DIFF_NAMES[difficulty]} >", FM, dc_pulse, W//2 + 40, 440, "midtop")
    dtxt(surf, "[D] Change", FS, DGRAY, W//2 + 150, 443, "midtop")

    y = 470
    dtxt(surf, "WASD - Move    CLICK - Shoot    SPACE - Melee    Q/E/R - Abilities", FS, DGRAY, W//2, y, "midtop")
    dtxt(surf, "F - Deploy Clone    1/2/3 - Choose ability    Ctrl+S - Save", FS, DGRAY, W//2, y+22, "midtop")

    if int(t * 2) % 2 == 0:
        dtxt(surf, "Press ENTER to start", FL, WHITE, W//2, 540, "midtop")

    if has_game_save():
        glow = 0.6 + 0.4 * math.sin(t * 3)
        cont_col = tuple(int(c * glow) for c in (80, 200, 255))
        dtxt(surf, "Press C to CONTINUE saved game", FM, cont_col, W//2, 580, "midtop")

    # Profile info
    pp = profile.get("perk_points", 0)
    runs = profile.get("total_runs", 0)
    wins = profile.get("total_wins", 0)
    if pp > 0 or runs > 0:
        dtxt(surf, f"Perk Points: {pp}   Runs: {runs}   Wins: {wins}", FS, C_GOLD, W//2, 620, "midtop")
        dtxt(surf, "[TAB] Open Perk Shop", FS, C_GOLD, W//2, 640, "midtop")
    # Equipped gear
    gear_strs = []
    for slot in ["weapon", "armor", "accessory"]:
        gid = profile["equipped"].get(slot)
        if gid and gid in GEAR_DB:
            gear_strs.append(GEAR_DB[gid]["name"])
    if gear_strs:
        dtxt(surf, f"Gear: {', '.join(gear_strs)}", FS, (180,180,255), W//2, 660, "midtop")

    # Best stats
    if best["time"] > 0 or best.get("wins",0) > 0:
        bm = int(best["time"]) // 60
        bs = int(best["time"]) % 60
        dtxt(surf, f"Best: {bm:02d}:{bs:02d}  Kills: {best['kills']}  Wins: {best.get('wins',0)}",
             FS, DGRAY, W//2, H - 30, "midtop")

def draw_endscreen(surf, won):
    # Dim
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surf.blit(overlay, (0, 0))

    if won:
        dtxt(surf, "SURVIVED!", FT, C_ESS, W//2, 150, "midtop")
        dtxt(surf, "10 minutes defended!", FL, WHITE, W//2, 230, "midtop")
    else:
        dtxt(surf, "DEFEATED", FT, (255, 60, 60), W//2, 150, "midtop")
        mins = int(game_time) // 60
        secs = int(game_time) % 60
        dtxt(surf, f"Survived {mins:02d}:{secs:02d}", FL, WHITE, W//2, 230, "midtop")

    dtxt(surf, f"Enemies slain: {kills}", FM, GRAY, W//2, 310, "midtop")
    n_ab = sum(1 for a in player["ab"] if a is not None)
    dtxt(surf, f"Abilities held: {n_ab}", FM, GRAY, W//2, 345, "midtop")
    dtxt(surf, f"Bosses killed: {stats['bosses_killed']}  Deaths: {stats['deaths']}  Best combo: {combo_best}", FS, GRAY, W//2, 375, "midtop")
    # Perk point reward display
    pts_earned = stats["bosses_killed"] + (3 if (state == "win") else (1 if game_time > 180 else 0))
    if pts_earned > 0:
        dtxt(surf, f"+{pts_earned} Perk Points earned!", FM, C_GOLD, W//2, 405, "midtop")
    dtxt(surf, f"Total Perk Points: {profile.get('perk_points', 0)}", FS, C_GOLD, W//2, 430, "midtop")

    t = pygame.time.get_ticks() / 1000
    if int(t * 2) % 2 == 0:
        dtxt(surf, "Press ENTER to play again", FM, WHITE, W//2, 480, "midtop")
    dtxt(surf, "Press ESC for title", FS, DGRAY, W//2, 520, "midtop")

def draw_frame():
    # Screen shake offset
    sx = random.uniform(-shake, shake) if shake > 0.5 else 0
    sy = random.uniform(-shake, shake) if shake > 0.5 else 0

    draw_ground(screen, sx, sy)

    # Collect all drawable entities for y-sorting
    drawables = []

    # Base
    drawables.append(("base", base["y"], None))

    # Enemies
    for e in enemies:
        drawables.append(("enemy", e["y"], e))

    # Clones
    for c in clones:
        drawables.append(("clone", c["y"], c))

    # Player
    drawables.append(("player", player["y"], player))

    # Sort by y
    drawables.sort(key=lambda d: d[1])

    # Draw zones first (on ground)
    draw_zones(screen, sx, sy)

    # Draw orbs
    draw_orbs(screen, sx, sy)

    # Draw sorted entities
    for dtype, _, data in drawables:
        if dtype == "base":
            draw_base(screen, sx, sy)
        elif dtype == "enemy":
            draw_enemy_entity(screen, data, sx, sy)
        elif dtype == "clone":
            draw_player_entity(screen, data["x"]+sx, data["y"]+sy, data, C_CLONE)
        elif dtype == "player":
            draw_player_entity(screen, data["x"]+sx, data["y"]+sy, data)

    # Projectiles
    draw_projectiles(screen, sx, sy)
    # Rings
    draw_rings(screen, sx, sy)
    # Chains
    draw_chains(screen, sx, sy)
    # Minions
    draw_minions(screen, sx, sy)
    # Powerups
    draw_powerups(screen, sx, sy)
    # Damage numbers
    draw_dmg_numbers(screen, sx, sy)
    # Particles
    draw_parts(screen)
    # HUD (no shake)
    draw_hud(screen)
    # Combo display
    draw_combo(screen)
    # Berserk indicator
    draw_berserk_indicator(screen)
    # Wave announcement
    draw_wave_announce(screen)
    # Minimap
    draw_minimap(screen)
    # Respawn overlay
    draw_respawn_overlay(screen)
    # Notifications (no shake)
    draw_notifications(screen)
    # Shop overlay (on top of everything)
    draw_shop(screen)

# ═══════════════════════════════════════════════════════════════════
#  INPUT HANDLING
# ═══════════════════════════════════════════════════════════════════
def get_card_rects():
    """Return list of (x, y, w, h) for the 3 ability cards on selection screen."""
    card_w, card_h = 220, 130
    total_w = 3 * card_w + 40
    start_x = W//2 - total_w//2
    rects = []
    for i in range(3):
        cx = start_x + i * (card_w + 20)
        cy = 330
        rects.append(pygame.Rect(cx, cy, card_w, card_h))
    return rects

def handle_selection_click(mx, my):
    """Handle mouse click on ability selection cards."""
    rects = get_card_rects()
    for i, r in enumerate(rects):
        if r.collidepoint(mx, my):
            # Simulate pressing 1/2/3
            handle_selection(pygame.K_1 + i)
            return

def handle_selection(key):
    global state, pending_ab, pending_boss
    if state == "select_replace":
        if key in (pygame.K_1, pygame.K_2, pygame.K_3):
            slot = key - pygame.K_1
            if player["ab"][slot] is not None:
                old_name = ABILS[player["ab"][slot]]["name"]
                player["ab"][slot] = pending_ab
                player["cd"][slot] = 0
                spawn_parts(player["x"], player["y"], ABILS[pending_ab]["color"], 20, 120, 0.6)
                state = "play"
                pending_ab = None
        elif key == pygame.K_ESCAPE:
            state = "play"
            pending_ab = None
    elif state == "select_keep":
        if key in (pygame.K_1, pygame.K_2, pygame.K_3):
            slot = key - pygame.K_1
            if player["ab"][slot] is not None:
                kept = player["ab"][slot]
                player["ab"] = [None, None, None]
                player["cd"] = [0.0, 0.0, 0.0]
                player["ab"][0] = kept
                # Boss ability in next slot
                player["ab"][1] = pending_ab
                player["cd"][1] = 0
                spawn_parts(player["x"], player["y"], ABILS[pending_ab]["color"], 25, 140, 0.7)
                spawn_parts(player["x"], player["y"], ABILS[kept]["color"], 15, 100, 0.5)
                state = "play"
                pending_ab = None

def handle_key(key):
    global state, shop_open, shop_tab, difficulty
    if state == "title":
        if key == pygame.K_RETURN:
            delete_game_save()
            init_game()
        elif key == pygame.K_c and has_game_save():
            load_game()
        elif key == pygame.K_TAB:
            shop_open = not shop_open
        elif key == pygame.K_d:
            difficulty = (difficulty + 1) % 3
    elif state == "play":
        if shop_open:
            # Shop controls
            if key == pygame.K_TAB or key == pygame.K_ESCAPE:
                shop_open = False
            elif key == pygame.K_g:
                shop_tab = 1 - shop_tab  # toggle between perks and gear tab
            elif shop_tab == 0:
                # Perk buying: keys 1-8
                num = None
                if key == pygame.K_1: num = 0
                elif key == pygame.K_2: num = 1
                elif key == pygame.K_3: num = 2
                elif key == pygame.K_4: num = 3
                elif key == pygame.K_5: num = 4
                elif key == pygame.K_6: num = 5
                elif key == pygame.K_7: num = 6
                elif key == pygame.K_8: num = 7
                if num is not None and num < len(PERK_ORDER):
                    pk = PERK_ORDER[num]
                    if buy_perk(pk):
                        add_notification(f"Upgraded {PERKS[pk]['name']}!", C_GOLD, 2.0)
                        apply_perks_and_gear()
                    else:
                        add_notification("Not enough perk points or maxed!", (255,100,100), 1.5)
            else:
                # Gear tab: number keys equip from inventory
                num = None
                if key == pygame.K_1: num = 0
                elif key == pygame.K_2: num = 1
                elif key == pygame.K_3: num = 2
                elif key == pygame.K_4: num = 3
                elif key == pygame.K_5: num = 4
                elif key == pygame.K_6: num = 5
                elif key == pygame.K_7: num = 6
                elif key == pygame.K_8: num = 7
                elif key == pygame.K_9: num = 8
                if num is not None:
                    inv = profile.get("inventory", [])
                    if num < len(inv):
                        equip_gear(inv[num])
                        apply_perks_and_gear()
                elif key == pygame.K_u:
                    # Unequip all
                    for slot in profile["equipped"]:
                        unequip_gear(slot)
                    apply_perks_and_gear()
            return
        if key == pygame.K_SPACE:
            do_melee()
        elif key == pygame.K_q:
            try_use_ability(0)
        elif key == pygame.K_e:
            try_use_ability(1)
        elif key == pygame.K_r:
            try_use_ability(2)
        elif key == pygame.K_f:
            create_clone()
        elif key == pygame.K_TAB:
            shop_open = True
        elif key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
            save_game()
    elif state in ("select_replace", "select_keep"):
        handle_selection(key)
    elif state in ("win", "lose"):
        if key == pygame.K_RETURN:
            init_game()
        elif key == pygame.K_ESCAPE:
            state = "title"

# ═══════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════════════════════════
load_best()
load_profile()
running = True

while running:
    dt = clock.tick(FPS) / 1000.0
    dt = min(dt, 0.05)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            handle_key(event.key)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if state == "play" and not shop_open:
                do_shoot()
            elif state == "title":
                init_game()
            elif state in ("win", "lose"):
                init_game()
            elif state in ("select_replace", "select_keep"):
                handle_selection_click(*event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            if state == "select_replace":
                handle_selection(pygame.K_ESCAPE)

    if state == "title":
        update_notifications(dt)
        draw_title(screen)
        draw_notifications(screen)
    elif state == "play":
        if not shop_open:
            update_game(dt)
        else:
            update_notifications(dt)
        draw_frame()
    elif state in ("select_replace", "select_keep"):
        # Game is paused during selection, just draw
        update_notifications(dt)
        draw_frame()
        draw_selection_ui(screen)
        draw_notifications(screen)
    elif state == "win":
        update_notifications(dt)
        draw_frame()
        draw_endscreen(screen, True)
        draw_notifications(screen)
    elif state == "lose":
        update_notifications(dt)
        draw_frame()
        draw_endscreen(screen, False)
        draw_notifications(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()
