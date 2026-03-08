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
- `*.py` — Standalone Python game scripts

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
