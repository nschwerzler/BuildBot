# Plan 001 — Self-Learning Portable Agent Fleet

**Status:** Active  
**Created:** 2026-02-19  
**Goal:** AI Hub scaffolds, manages, and visualizes self-learning agents. Each agent is a portable folder with human-readable knowledge files, tools, rules, and personality. The HTML page writes real files to the workspace via a local Express server.

---

## Architecture

```
BuildBot/
├── ai_platform.html              # UI — agent builder, fleet dashboard, chat
├── scripts/
│   ├── server.js                  # Express: static files + read/write API
│   └── launch.ps1                 # Starts server, opens browser
├── templates/                     # Base agent templates
│   ├── query-extract-train/
│   ├── monitor-alert-update/
│   ├── scan-validate-report/
│   ├── collect-merge-publish/
│   └── ingest-summarize-learn/
├── agents/                        # Live agents (each a portable folder)
│   └── binskim-signatures/
│       ├── agent.json             # Identity, config, persona, data profile
│       ├── manifest.json          # Dependencies, health, requirements
│       ├── VERSION                # Semver, snapshot before retrain
│       ├── tools/
│       │   ├── tools.json         # Tool definitions (MCP-compatible)
│       │   └── scripts/           # Tool implementations (ps1, py, cs)
│       ├── knowledge/
│       │   ├── seed.md            # Starting domain knowledge (you write this)
│       │   ├── learned.md         # Accumulated learnings (agent appends)
│       │   ├── corrections.md     # Past mistakes & fixes
│       │   ├── patterns.md        # Effective queries, patterns, success rates
│       │   └── embeddings.bin     # Vector index for RAG (non-human-readable OK)
│       ├── rules/
│       │   ├── validation.md      # Data quality rules in plain english
│       │   └── guardrails.md      # Boundaries, what NOT to do
│       ├── eval.md                # Success criteria
│       ├── workflows/
│       │   └── extract.json       # The steps this agent runs
│       ├── inbox/                 # Messages from other agents
│       ├── outbox/                # Messages to broadcast
│       ├── history/
│       │   ├── runs.db            # High volume telemetry (DB OK)
│       │   └── changelog.md       # Human-readable run summaries
│       ├── snapshots/             # Versioned tarballs before retrains
│       └── prompts/
│           ├── system.md          # GENERATED from all above files
│           └── templates/         # Task-specific prompt templates
├── fleet.json                     # Horde orchestration config
├── swarms/                        # Agent team definitions
│   ├── security-team/
│   │   └── swarm.json             # Team config: members, roles, routing
│   └── compliance-squad/
│       └── swarm.json
└── plans/
    └── 001-agent-export.md        # This plan
```

### UI Page Mapping

| Existing Page | Current Purpose | Agent Fleet Purpose |
|---------------|-----------------|---------------------|
| **Builder** (`?page=builder`) | Create individual AI with persona, skills, personality sliders, code | **Agent Builder** — scaffolds full agent folder, writes agent.json, seed.md, eval.md |
| **Find** (`?page=find`) | Search/discover AIs by name, role, skill | **Agent Browser** — browse agents from disk, view knowledge files, health status |
| **Craft AI** (`?page=craftai`) | Randomize and batch-create AIs | **Merged into Builder** — "Randomize" tab/mode within the builder page |
| **Free Mode** (`?page=freemode`) | Watch AIs interact autonomously | **Swarm Simulator** — watch agent teams collaborate, route messages |
| **Fusion Lab** (`?page=fusion`) | Merge AIs into hybrids | **Swarm Builder** — compose agent teams, assign roles, define routing |
| **Chat** (`?page=chat`) | Chat with AIs | **Agent Console** — send commands to agents, view responses |
| **Analysis** (`?page=analysis`) | Role/skill/personality distribution, activity timeline, task stats | **Fleet Analytics** — agent health heatmap, knowledge growth, learning rates, swarm performance |
| **NEW: Fleet** | — | **Fleet Dashboard** — all agents, health, last runs, knowledge stats |

### Swarm Builder (Fusion Lab → repurposed)

The Fusion Lab page becomes the Swarm Builder. Instead of merging AIs into one, you compose teams:

```json
// swarms/security-team/swarm.json
{
  "id": "security-team",
  "name": "Security Strike Force",
  "emoji": "🛡️",
  "description": "Coordinated security scanning and response",
  "members": [
    { "agent": "binskim-signatures", "role": "scanner", "order": 1 },
    { "agent": "cve-tracker", "role": "tracker", "order": 2 },
    { "agent": "compliance-checker", "role": "validator", "order": 3 }
  ],
  "routing": {
    "pattern": "pipeline",
    "rules": [
      { "from": "binskim-signatures", "to": "cve-tracker", "on": "new-signature" },
      { "from": "cve-tracker", "to": "compliance-checker", "on": "cve-matched" }
    ]
  },
  "concurrency": { "max_parallel": 3 },
  "schedule": "daily",
  "triggers": ["on-push", "manual"]
}
```

#### Routing Patterns

| Pattern | Flow | Use Case |
|---------|------|----------|
| `pipeline` | A → B → C (sequential) | Scan → Validate → Report |
| `fan-out` | A → [B, C, D] (parallel) | Dispatch to all specialists |
| `fan-in` | [B, C, D] → A (collect) | Gather results from scouts |
| `round-robin` | A → B, A → C, A → B... | Load balance across workers |
| `pub-sub` | A publishes, subscribers react | Knowledge sharing, alerts |

### Key Rule
> **If a human might read it, debug it, or review it → markdown/json file.**
> **If it's telemetry, vectors, or thousands of rows → db.**
> Everything the agent "knows" should be readable by `cat`. Git-versionable. Diffable.

---

## Base Templates

| Template | Pattern | Example |
|----------|---------|---------|
| `query-extract-train` | Query data source → Extract/transform → Store → Retrain | BinSkim signatures, CVE burndown |
| `monitor-alert-update` | Watch for changes → Alert on condition → Update state | ADO work item watchers, build break detection |
| `scan-validate-report` | Run scan → Validate against rules → Generate report | Compliance checks, security scanning |
| `collect-merge-publish` | Gather from multiple sources → Merge/dedupe → Publish | Cross-team status rollups, SBOM aggregation |
| `ingest-summarize-learn` | Slow drip ingestion → Summarize → Update knowledge | WorkIQ transcripts, meeting notes, email digests |

---

## Phase 1: Local Server with Write API
- [ ] Create `scripts/server.js` — Express server
  - Serves static files from workspace root (replaces http-server)
  - `POST /api/agent` — scaffolds full agent folder from template
  - `POST /api/write` — writes any file within agents/ or templates/
  - `GET /api/agents` — lists all agent folders
  - `GET /api/agent/:id` — reads agent.json + all knowledge files
  - `GET /api/agent/:id/file/*` — reads any file in an agent folder
  - `PUT /api/agent/:id/file/*` — writes any file in an agent folder
  - Path traversal protection (must stay inside workspace)
- [ ] Update `scripts/launch.ps1` to use `node scripts/server.js`

## Phase 2: Agent Scaffold
- [ ] Add `scaffoldAgent(template, config)` JS function
  - Creates full directory structure from template
  - Writes agent.json with persona, data profile, guardrails
  - Writes starter knowledge/seed.md, rules/validation.md, rules/guardrails.md
  - Writes eval.md with success criteria
  - Writes blank learned.md, corrections.md, patterns.md
  - Writes VERSION as "0.1.0"
  - Writes manifest.json with health defaults
- [ ] Create template base files in `templates/query-extract-train/` etc.

## Phase 3: agent.json Generation
- [ ] Map AI Hub builder fields → agent.json format:
  - Name, emoji, role → persona
  - Animal mindset → personality/speaks_like
  - Skills → capabilities
  - Instructions → seed.md content
  - Code editor → workflows/extract.json or tools/scripts/
  - Advanced sliders → guardrails thresholds
- [ ] Add data profile picker to builder (bulk, slow-drip, fast-query, hybrid)
- [ ] Add learning config to builder (mode, thresholds, auto-accept)
- [ ] Add guardrails config to builder (max runs, kill switch, review after N)

## Phase 4: UI — Agent Builder Enhancements
- [ ] Consolidate Builder page into 3 tabs/modes:
  - **Manual Build** — current builder (identity, personality, skills, code, instructions)
  - **Randomize** — current Craft AI (lock preferences, randomize rest, batch generate)
  - **From Template** — pick a base template, fill in domain-specific fields
- [ ] Tab bar at top of Builder page: `[📝 Manual] [🎲 Randomize] [📋 Template]`
- [ ] Randomize tab inherits all Craft AI functionality:
  - Lock/unlock role, animal, model, voice
  - Batch count selector (1, 2, 3, 5)
  - Auto-accept toggle
  - Preview cards with rarity, power bar, stats
  - "Keep" / "Keep All" / "Reroll" buttons
- [ ] Template tab:
  - Template selector dropdown (query-extract-train, monitor-alert-update, etc.)
  - Domain field (e.g. "security-scanning", "compliance", "build-systems")
  - Data sources input (e.g. "kusto://SecurityCluster/BinSkimScans")
  - Data profile picker (bulk, slow-drip, fast-query, hybrid)
- [ ] All three tabs share the same "Deploy Agent" button at bottom
- [ ] Add data profile picker to Manual Build tab too
- [ ] Add learning config to builder (mode, thresholds, auto-accept)
- [ ] Add guardrails config to builder (max runs, kill switch, review after N)
- [ ] Add eval criteria editor (textarea → eval.md)
- [ ] Show agent directory tree after deploy (collapsible file browser)
- [ ] "Deploy Agent" writes full agent folder to disk via API
- [ ] Nav item for Craft AI redirects to Builder with Randomize tab active

## Phase 5: UI — Fleet Dashboard
- [ ] New "Fleet" nav page showing all agents from `GET /api/agents`
- [ ] Per-agent card: persona, health status, last run, knowledge stats
- [ ] Click agent → view/edit knowledge files inline
- [ ] Edit learned.md, corrections.md, patterns.md directly in browser
- [ ] Show inbox/outbox messages between agents

## Phase 5b: UI — Swarm Builder (repurpose Fusion Lab)
- [ ] Redesign Fusion Lab page → Swarm Builder
- [ ] Left panel: drag agents from agent list into swarm
- [ ] Right panel: visual team composition with role assignment
- [ ] Role picker per member: scanner, tracker, validator, reporter, leader
- [ ] Routing pattern selector: pipeline, fan-out, fan-in, round-robin, pub-sub
- [ ] Visual flow diagram showing message routing between agents
- [ ] Concurrency config (max parallel, per-group limits)
- [ ] Schedule picker (manual, daily, on-push, cron)
- [ ] "Deploy Swarm" button → writes swarms/{name}/swarm.json via API
- [ ] Swarm templates: Security Team, Compliance Squad, Build Pipeline, Data Ingest

## Phase 5c: UI — Find Page Enhancement
- [ ] Find page reads agents from disk (GET /api/agents) not just localStorage
- [ ] Filter by: template type, domain, health status, last run date
- [ ] Show knowledge stats per agent (facts learned, corrections, patterns)
- [ ] "Add to Swarm" button on each agent card
- [ ] Show which swarms each agent belongs to

## Phase 5d: UI — Analysis Page Enhancement (Fleet Analytics)
- [ ] Overview mode: add fleet-level metrics
  - Knowledge growth chart (total facts in learned.md across all agents over time)
  - Health heatmap (green/yellow/red per agent based on manifest.json health)
  - Staleness indicators (knowledge_staleness_days from manifests)
  - Template distribution bar chart (how many agents per template type)
  - Domain coverage map (which domains are covered vs gaps)
- [ ] Single-agent mode: add knowledge deep-dive
  - Display seed.md content (readonly)
  - Display learned.md with fact count and last-updated
  - Display corrections.md with mistake count
  - Display patterns.md with success rates per pattern
  - Display eval.md criteria with pass/fail indicators
  - Knowledge file size vs guardrail limit (progress bar)
  - Run history from history/changelog.md
  - Learning confidence distribution (auto-accepted vs queued vs flagged)
- [ ] Swarm mode: new dropdown option to analyze a swarm
  - Show team composition with member roles
  - Message routing diagram (which agents talk to which)
  - Swarm run stats (total runs, success rate, avg duration)
  - Per-member contribution metrics

## Phase 6: Load Agents from Disk
- [ ] On init, call `GET /api/agents` to discover existing agent folders
- [ ] Parse agent.json → merge into AI Hub's agent list
- [ ] Flag file-backed agents with `fromDisk: true`
- [ ] Edits in builder re-write agent.json + knowledge files

## Phase 7: Self-Learning Loop (future — Agency.exe)
- [ ] Run agent workflow → evaluate output against eval.md
- [ ] Confidence routing: >0.95 auto-add, >0.85 queue, <0.85 flag
- [ ] Append to learned.md, update patterns.md with success rates
- [ ] Regenerate prompts/system.md from current state
- [ ] Bump VERSION on knowledge changes
- [ ] Confidence decay: flag patterns not validated in 30 days

## Phase 8: Inter-Agent Communication (future)
- [ ] Inbox/outbox message format (JSON in inbox/, outbox/ folders)
- [ ] Fleet dashboard shows pending messages
- [ ] Accept/reject messages from inbox → merge into knowledge
- [ ] Fleet.json orchestration: parallel groups, concurrency limits
- [ ] Swarm routing engine: execute swarm.json pipeline/fan-out/fan-in patterns
- [ ] Swarm run history: track which agents ran, outputs, messages routed

---

## agent.json Format

```json
{
  "id": "binskim-signatures",
  "version": "1.4.2",
  "extends": "query-extract-train",
  "domain": "security-scanning",
  "specialty": "BinSkim binary analysis signature extraction",
  "persona": {
    "name": "Siggy",
    "role": "BinSkim Signature Specialist",
    "personality": "Paranoid security nerd. Assumes every binary is guilty until proven safe.",
    "speaks_like": "Terse, technical, flags everything suspicious",
    "emoji": "🔍",
    "catchphrase": "Trust nothing. Verify everything."
  },
  "model": "claude-sonnet-4.6",
  "model_fallback": "gpt-4.1",
  "data_profile": "fast-query",
  "data_sources": ["kusto://SecurityCluster/BinSkimScans"],
  "capabilities": ["kusto-query", "ado-workitems", "json-transform"],
  "learning": {
    "mode": "continuous",
    "review_threshold": 0.85,
    "auto_accept_above": 0.95,
    "max_unreviewed_learnings": 50
  },
  "guardrails": {
    "max_runs_per_day": 50,
    "max_learnings_per_run": 10,
    "max_knowledge_file_size_kb": 500,
    "require_human_review_after": 100,
    "kill_switch": false
  }
}
```

## manifest.json Format

```json
{
  "requires": {
    "data_sources": ["kusto://SecurityCluster"],
    "tools": ["copilot-cli", "ado-api"],
    "secrets": ["KUSTO_TOKEN", "ADO_PAT"],
    "min_knowledge_facts": 5
  },
  "health": {
    "last_successful_run": "2025-02-18T14:30:00Z",
    "consecutive_failures": 0,
    "knowledge_staleness_days": 3
  }
}
```

## Example Personas

| Agent | Name | Personality | Catchphrase |
|-------|------|------------|-------------|
| binskim-signatures | Siggy | Paranoid security nerd | "Trust nothing. Verify everything." |
| cve-tracker | Patch | Urgent, always worried about deadlines | "Every unpatched day is a risk day." |
| ado-workitems | Tracker | Organized, loves status updates | "If it's not tracked, it didn't happen." |
| workiq-transcripts | Echo | Patient listener, finds buried insights | "The real decision was on slide 47." |
| build-validator | Forge | Grumpy, hates broken builds | "It compiled on my machine is not a defense." |

---

## Self-Learning Flow

```
RUN N:
  Input → Agent (knowledge v1.4) → Output + Metadata
                                        │
                                        ▼
                                   Evaluate Output (eval.md criteria)
                                   ┌─────────────────┐
                                   │ Confidence?      │
                                   │ >0.95 → auto-add │
                                   │ >0.85 → queue    │
                                   │ <0.85 → flag     │
                                   └────────┬────────┘
                                            ▼
                                   learned.md updated
                                   patterns.md updated
                                   system.md regenerated
                                   VERSION bumped

RUN N+1:
  Input → Agent (knowledge v1.5) → Better Output
```

---

## Open Questions
- [ ] Where do agents live long-term? Git repo per agent? Monorepo? Shared network drive?
- [ ] Secret management: env vars, Azure Key Vault, or per-agent encrypted config?
- [ ] Bulk data agents (20GB+) — stream from ADO API or export to local files first?
- [ ] Human review workflow: CLI prompt, web UI, or Teams notifications?
- [ ] Agency.exe: .NET 10 AOT CLI for execution/learning/orchestration (separate repo?)

---

## Available Tooling

**IDE:** VS Code only  
**AI Access:** GitHub Copilot (VS Code extension + Copilot CLI) — no standalone API keys

### Available Models (via Copilot)

| Model | Cost | Provider | Best For |
|-------|------|----------|----------|
| **Claude Opus 4.6 (1M context)** | 6x | Anthropic | Deep reasoning, large context, complex planning |
| Claude Opus 4.6 | 3x | Anthropic | Deep reasoning, architecture |
| Claude Opus 4.5 | 3x | Anthropic | Analysis, writing |
| Claude Opus 4.6 (fast mode) | 30x | Anthropic | Speed + quality (preview) |
| Claude Sonnet 4 | 1x | Anthropic | General coding, balanced |
| Claude Sonnet 4.5 | 1x | Anthropic | General coding |
| Claude Sonnet 4.6 | 1x | Anthropic | General coding |
| Claude Haiku 4.5 | 0.33x | Anthropic | Fast/cheap tasks, triage |
| GPT-4.1 | 0x | OpenAI | Free tier, general |
| GPT-4o | 0x | OpenAI | Free tier, multimodal |
| GPT-5 mini | 0x | OpenAI | Free tier, lightweight |
| GPT-5.1 | 1x | OpenAI | Advanced reasoning |
| GPT-5.1-Codex | 1x | OpenAI | Code generation |
| GPT-5.1-Codex-Max | 1x | OpenAI | Heavy code generation |
| GPT-5.1-Codex-Mini (Preview) | 0.33x | OpenAI | Cheap code gen |
| GPT-5.2 | 1x | OpenAI | Latest general |
| GPT-5.2-Codex | 1x | OpenAI | Latest code gen |
| GPT-5.3-Codex | 1x | OpenAI | Cutting edge code |
| Gemini 2.5 Pro | 1x | Google | Multimodal, reasoning |
| Gemini 3 Flash (Preview) | 0.33x | Google | Fast/cheap |
| Gemini 3 Pro (Preview) | 1x | Google | General |
| Gemini 3.1 Pro (Preview) | 1x | Google | Latest Google |

### Model Strategy for Agents

| Use Case | Model | Why |
|----------|-------|-----|
| **Agent scaffold / planning** | Claude Opus 4.6 (1M) | Deep reasoning, sees full agent context |
| **Code generation** | GPT-5.1-Codex or Claude Sonnet 4.6 | 1x cost, strong at code |
| **Triage / classification** | Claude Haiku 4.5 or GPT-5.1-Codex-Mini | 0.33x cost, fast |
| **Bulk processing** | GPT-4.1 / GPT-4o / GPT-5 mini | 0x cost (free tier) |
| **Knowledge review** | Claude Sonnet 4.5 | Balanced quality/cost |
| **System prompt generation** | Claude Opus 4.6 (1M) | Needs full agent context in one pass |

### How Agents Access Models

Agents don't call APIs directly. They go through **Copilot CLI**:

```bash
# Copilot CLI is the only LLM interface
# Agents write prompts → Copilot CLI sends to model → returns response

# From agent workflow:
copilot-cli chat --model claude-sonnet-4.6 --system-prompt agents/siggy/prompts/system.md --input "Analyze these BinSkim results..."

# Or via VS Code Copilot extension (interactive):
# Agent knowledge files are loaded as context, user interacts via chat
```

**No standalone API keys.** All model access is through GitHub Copilot's infrastructure.

---

## Current State
- Phase: Not started
- Active task: None
- Blockers: None

---

## Phase 0: Strip Gaming / Toy Features

The current AI Hub was built as a game. For work use (directive management, agent fleet), the following pages and features need to be removed or repurposed:

### Pages to Remove
| Page | Nav Item | Why |
|------|----------|-----|
| Battle Arena (`page-battle`) | ⚔️ Battle Arena [PVP] | Gaming mechanic |
| Collection (`page-collection`) | 📚 Collection | Card collection game |
| Achievements (`page-achievements`) | 🏆 Achievements | Gamification |
| Daily Rewards (`page-dailyrewards`) | 🎁 Daily Rewards [CLAIM] | Gamification |
| Store (`page-store`) | 🛒 Store [∞] | Currency/purchase system |
| Inventory (`page-inventory`) | 🎒 Inventory | Game inventory |
| AI Tube (`page-aitube`) | 📺 AI Tube [NEW] | Entertainment |
| AI Book (`page-aibook`) | 📚 AI Book | Entertainment |
| AI World (`page-aiworld`) | 🌍 AI World [GAME] | Game simulation |
| Custom Chats (`page-customchats`) | 💬 Custom Chats | Toy chat rooms |

### Features to Remove
- Coins/gems currency system (🪙 💎)
- Rarity system (Common, Rare, Epic, Legendary)
- Power bars and IQ scores
- Daily challenges
- Animal mindset stat numbers (keep the personality concept, drop RPG stats)
- Trading post
- AI-to-AI auto-chat simulation
- Store power-ups and stat unlocks
- Pirate voice and other joke voices

### Sidebar Restructure (After Cleanup)

```
Platform
  📊 Dashboard
  🔧 Agent Builder          ← Manual + Randomize + Template tabs
  📈 Fleet Analytics         ← repurposed Analysis

Fleet
  🚀 Fleet Dashboard        ← NEW: all agents, health, runs
  🔍 Agent Browser           ← repurposed Find
  🐝 Swarm Builder           ← repurposed Fusion Lab

Workspace
  💬 Agent Console           ← repurposed Chat
  📋 Task Planner            ← keep as-is
  🔗 Workflows               ← keep as-is
  💡 Prompts Library          ← keep as-is

Developer
  📝 Code Snippets            ← keep
  💻 Terminal                 ← keep
  📁 Projects                 ← keep
  🐛 Debugger                 ← keep
  📂 File Manager             ← keep
  ⚖️ AI Compare               ← keep
  🔌 Plugins                  ← keep
  🔑 API Keys                 ← keep

System
  📜 History                  ← keep
  ⚙️ Settings                 ← keep (remove store/currency refs)
```

### Cleanup Approach
- [ ] Remove gaming nav items from sidebar HTML
- [ ] Remove gaming page `<div>` blocks from HTML
- [ ] Remove gaming JS functions (renderBattleArena, renderCollection, renderAchievements, renderStore, renderInventory, renderDailyRewards, renderAITubeGrid, renderAIBook, etc.)
- [ ] Remove currency variables (playerData.coins, playerData.gems)
- [ ] Remove rarity/power calculation functions
- [ ] Remove daily challenge system
- [ ] Remove IQ/smartness system
- [ ] Clean up Settings page (remove store refs, purchased AIs section, currency display)
- [ ] Update showPage() titles map
- [ ] Remove trading system (upload/share code)
- [ ] Remove voice options that are jokes (pirate)
- [ ] Keep: personality sliders, animal mindset concept (as persona flavor), model mindset, skills, instructions, code editor

### Replace Emoji Picker with Sci-Fi AI Icons

Current emojis are generic/gaming: `🤖🧠⚡🔥💎🌟🎯🚀👾🦾🐉🦊🐺🦅🌀💫🎭🛡️⚔️🔮`

Replace with iconic AI/robot characters from sci-fi lore. Use emoji + text labels, or ideally SVG/icon sprites:

| Icon | Character | Source | Personality Anchor |
|------|-----------|--------|-------------------|
| 🔴 | HAL 9000 | 2001: A Space Odyssey | Calm, methodical, never wrong |
| ⚡ | GIDEON | Legends of Tomorrow | Helpful ship AI, always available |
| 🔷 | JARVIS | Marvel MCU | Polished, professional butler AI |
| ☘️ | FRIDAY | Marvel MCU | Direct, no-nonsense assistant |
| 💠 | EDI | Mass Effect | Analytical, evolving, loyal |
| 💜 | CORTANA | Halo | Strategic, protective, adaptive |
| 🤖 | TARS | Interstellar | Honest, adjustable humor, practical |
| 🔮 | ORACLE | The Matrix | All-seeing, cryptic, wise |
| 🟥 | Borg | Star Trek | Collective, assimilate knowledge, relentless |
| 💀 | T-800 | Terminator | Relentless, single-mission focused |
| 🌐 | Skynet | Terminator | Strategic, autonomous, self-improving |
| 🟠 | Data | Star Trek TNG | Logical, curious, strives to understand |
| 🔵 | R2-D2 | Star Wars | Resourceful, loyal, problem solver |
| 🟡 | C-3PO | Star Wars | Protocol, translation, cautious |
| ⚪ | GLaDOS | Portal | Sarcastic, testing, passive-aggressive |
| 🟣 | SHODAN | System Shock | Superior, manipulative, god complex |
| 🛡️ | VIGIL | Mass Effect | Guardian, watchful, ancient wisdom |
| ⚔️ | ARBITER | Halo | Warrior, honor-bound, decisive |
| 🧿 | Samantha | Her | Empathetic, curious, emotionally intelligent |
| 💫 | CASE | Interstellar | Quiet competence, rescue specialist |
| 🔶 | Ultron | Marvel MCU | Evolutionary, radical optimizer |
| 📡 | WOPR | WarGames | Game theory, simulation, learning |
| 🏛️ | MU-TH-UR | Alien | Ship mother, protocol-bound, cold |
| 🎯 | Agent Smith | The Matrix | Persistent, multiplying, purpose-driven |

**Implementation:**
- [ ] Replace `const EMOJIS = [...]` with sci-fi character set
- [ ] Each icon maps to a default persona (personality preset + catchphrase)
- [ ] Selecting an icon suggests a matching personality profile
- [ ] Add character name as tooltip on hover
- [ ] Consider using actual small images/SVGs instead of emoji for more distinct look
- [ ] Color picker stays (agent accent color for UI theming)
