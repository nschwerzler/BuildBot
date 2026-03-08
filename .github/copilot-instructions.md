# Copilot Workspace Instructions

## Auto-Commit Rule (MANDATORY)

After completing ANY code modification (file create, edit, or delete), you MUST:

1. Stage all changes: `git add -A`
2. Generate a descriptive commit message following the conventions below
3. Commit: `git commit -m "<message>"`
4. Push: `git push`

**Do NOT ask the user for permission to commit. Do NOT skip this step. Every modification must be committed and pushed immediately after completion.**

If multiple files are changed as part of a single task, commit them together as one atomic commit after all edits are done.

## Commit Message Format

```
<type>: <short summary in imperative mood>
```

### Types
- **feat** — New feature or gameplay mechanic
- **fix** — Bug fix
- **refactor** — Code restructuring without behavior change
- **style** — Formatting, whitespace, semicolons
- **docs** — Documentation changes
- **build** — Build system or dependency changes
- **chore** — Maintenance tasks, config updates
- **perf** — Performance improvements
- **test** — Adding or updating tests
- **ci** — CI/CD workflow changes

### Rules
1. Use imperative mood: "add crafting system" not "added crafting system"
2. Keep the summary under 72 characters
3. Reference specific systems/files changed (e.g., "feat: add weather effects to BiomeSystem")
4. For multi-file changes, summarize the overall intent
5. Mention gameplay impact when relevant

### Examples
- `feat: add diamond ore generation to WorldGenerator`
- `fix: resolve player clipping through voxel walls`
- `refactor: extract particle logic into ParticleSystem`
- `chore: update Three.js to v0.160`
- `feat: add Herobrine ambient sound effects and fog`
- `fix: correct health bar rendering at low HP values`
- `ci: add auto-commit workflows`

## Project Context

This is **BuildBot**, a Minecraft-style 3D voxel game built with TypeScript and Three.js. The project also contains standalone Python game scripts. Key directories:

- `src/systems/` — Game systems (inventory, crafting, weather, mobs, etc.)
- `src/entities/` — Game entities (Player, etc.)
- `src/world/` — World generation and chunk management  
- `src/engine/` — Core game engine and renderer
- `src/graphics/` — Pixel textures and voxel models
- `*.py` — Standalone Python game scripts (e.g., `voxel_test.py`)
## Victory Sound (Bee Jam)

After completing every task AND when d0g3 says "play it", play the xylophone bee jam melody. Generate a WAV and play it via Python `winsound`:

```python
import wave, struct, math, os, winsound
sample_rate = 44100
def xylophone_tone(freq, duration_ms, volume=0.7):
    n = int(sample_rate * duration_ms / 1000)
    samples = []
    for i in range(n):
        t = i / sample_rate
        env = math.exp(-t * 8.0)
        val = 0.55 * math.sin(2 * math.pi * freq * t)
        val += 0.25 * math.sin(2 * math.pi * freq * 3 * t) * math.exp(-t * 12)
        val += 0.12 * math.sin(2 * math.pi * freq * 4 * t) * math.exp(-t * 16)
        val += 0.08 * math.sin(2 * math.pi * freq * 6 * t) * math.exp(-t * 20)
        if t < 0.003:
            val += 0.3 * math.sin(2 * math.pi * freq * 8 * t)
        val *= env * volume
        samples.append(max(-32767, min(32767, int(val * 32767))))
    return samples
notes = [(440,200),(494,200),(523,200),(587,250),(659,300),(587,200),(523,200),(494,250),(440,150),(440,150),(523,250),(659,350),(587,200),(523,200),(494,250),(440,200),(523,150),(587,150),(659,150),(784,350),(659,250),(523,250),(440,350),(880,120),(784,120),(659,120),(587,120),(523,120),(440,120),(440,150),(523,150),(659,250),(784,500)]
all_samples = []
for freq, dur in notes:
    all_samples.extend(xylophone_tone(freq, dur))
    all_samples.extend([0] * int(sample_rate * 0.03))
path = os.path.join(os.environ.get('TEMP', '.'), 'bee_xylo.wav')
with wave.open(path, 'w') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(sample_rate)
    w.writeframes(struct.pack(f'<{len(all_samples)}h', *all_samples))
winsound.PlaySound(path, winsound.SND_FILENAME)
```

Run this as a one-liner via `.venv\Scripts\python.exe -c "..."` in the terminal.

## Tetris Bot (freetetris.org / N-Blox)

### Game Details
- URL: https://freetetris.org — Tetris N-Blox runs inside iframe `#gameIFrame`
- Controls: ArrowUp=rotate, ArrowLeft/Right=move, Space=hard drop
- Page viewport: 900x750, iframe at (78,125) size 728x600
- **Workflow**: Player (d0g3) handles all menu buttons (Play, New Game, level select). Bot only takes over once pieces are falling.

### Game Engine: Cocos Creator
- Game uses **Cocos Creator** engine — `cc` object with 185 keys
- `cc.director.getScene()` returns scene named "Desktop"
- Custom app object: `window.mBPSApp` with state machine (`mStateMachine`)
- State machine uses numbered states (not named strings), `mPreviousState=7` at main menu
- Find game frame via `frame.name == 'gameIFrame'` (NOT URL-based search)
- Iframe needs load time: wait for `#gameIFrame` selector, sleep 5s, then click
- Game renders on Cocos Creator canvas — no standard HTML game elements

### Scene Tree (Main Menu State)
```
Desktop
  Canvas [cc.UITransform, cc.Canvas, cc.Widget, x1819288371416691716x]
    Camera [cc.Camera]
    AppBGView [cc.UITransform, cc.Sprite]
    mainMenu-dimmingView
    mainMenu-rootView
      logo [cc.Sprite]
      menu > content > panelContent (4 children):
        [0] play — Play button
        [1] level — level selector
        [2] highScoresViewContainer — high scores
        [3] iconButtons — options, help, moreGames
```

### Custom Component on Canvas
- `x1819288371416691716x` — main game controller component
- Props: `requireIFrame`, `gameContentBasePath`, `gameDataFilePath` (obfuscated strings)
- Has `mBPSApp`, `mResourceMgr`, `mDidAddKeyEventHandlersOnFocus`

### Key JS Functions
- `getGameDiv()` — returns game div element
- `getGameCanvas()` — returns game canvas element
- `gameLoadingSceneIsReady()` — check if loading is done

### Reading Game State via JS
- Use `game_frame.evaluate()` with Playwright to access JS objects
- Walk scene via `cc.director.getScene()` → `node.children` → `node._components`
- Scene tree changes when game starts — mainMenu nodes deactivate, board nodes appear
- **After player clicks Play**: re-scan scene tree to find board/piece data nodes
- Can potentially read board array, current piece type, and score directly from JS

### Pixel Analysis (fallback approach)
- Board empty cell: RGB(198,216,242), brightness ~218
- Grid lines: ~brightness 192-200
- Background outside board: RGB(220,237,255), brightness ~237
- **NO high-contrast borders** — everything is blue-tinted, brightness-based edge detection fails
- Info panel dark border at x~498-538, brightness ~130
- Board: 10 cols × 20 rows, left ~55% of iframe, cell ~39×23px
- Piece colors differ from background by 100+ RGB distance
- DON'T use brightness threshold scanning — use fixed proportions or JS state reading

### AI Strategy
- 1 row clear = points — prioritize line clears
- Holes are worst — heavily penalize
- Keep surface flat (low bumpiness), don't stack too high

### Bot Files
- `tetris_bot.py` — Main Playwright bot with calibration + AI
- `tetris_inspect.py` / `tetris_inspect2.py` / `tetris_inspect3.py` — JS inspector scripts
- `tetris_calibration.json` — Auto-generated cached calibration
- `tetris_debug.png` — Debug screenshot

### Tech Stack
- Python 3.13.7, `.venv` at D:\BuildBot
- Playwright Python v1.58.0 with Chromium
- Pillow (PIL) v12.1.1 for screenshots
- Key press speed: ~25ms intervals
