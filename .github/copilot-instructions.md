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
