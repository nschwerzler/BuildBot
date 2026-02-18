# Copilot Commit Message Instructions

When generating commit messages for this project, follow these conventions:

## Format
```
<type>: <short summary in imperative mood>

<optional body explaining what and why>
```

## Types
- **feat**: New feature or gameplay mechanic
- **fix**: Bug fix
- **refactor**: Code restructuring without behavior change
- **style**: Formatting, missing semicolons, whitespace
- **docs**: Documentation changes
- **build**: Build system or dependency changes
- **chore**: Maintenance tasks, config updates
- **perf**: Performance improvements
- **test**: Adding or updating tests

## Rules
1. Use imperative mood: "add crafting system" not "added crafting system"
2. Keep the summary under 72 characters
3. Reference specific systems/files changed (e.g., "feat: add weather effects to BiomeSystem")
4. For multi-file changes, summarize the overall intent
5. Mention gameplay impact when relevant (e.g., "feat: add hunger decay over time for survival challenge")

## Examples
- `feat: add diamond ore generation to WorldGenerator`
- `fix: resolve player clipping through voxel walls`
- `refactor: extract particle logic into ParticleSystem`
- `chore: update Three.js to v0.160`
- `feat: add Herobrine ambient sound effects and fog`
- `fix: correct health bar rendering at low HP values`
