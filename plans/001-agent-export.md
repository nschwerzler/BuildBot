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
| **Craft AI** (`?page=craftai`) | Randomize and batch-create AIs | **Template Stamper** — stamp out agents from templates with randomized personas |
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
- [ ] Add "Deploy Agent" button → scaffolds folder via API, shows toast
- [ ] Add template selector dropdown in builder (the 5 templates)
- [ ] Add data sources input field
- [ ] Add eval criteria editor (textarea → eval.md)
- [ ] Add guardrails editor (sliders for max_runs, review thresholds)
- [ ] Show agent directory tree after deploy (collapsible file browser)

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
  "model": "claude-sonnet-4-5-20250929",
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
- [ ] LLM routing: Claude API vs local Phi-3.5 vs Copilot CLI per agent? Or configurable per agent.json?
- [ ] Where do agents live long-term? Git repo per agent? Monorepo? Shared network drive?
- [ ] Secret management: env vars, Azure Key Vault, or per-agent encrypted config?
- [ ] Bulk data agents (20GB+) — stream from ADO API or export to local files first?
- [ ] Human review workflow: CLI prompt, web UI, or Teams notifications?
- [ ] Agency.exe: .NET 10 AOT CLI for execution/learning/orchestration (separate repo?)

---

## Current State
- Phase: Not started
- Active task: None
- Blockers: None
