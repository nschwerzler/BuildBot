"""
AI Hub - Multi-Agent Communication Platform
============================================
A real-time hub where specialized AI agents discuss topics,
respond to each other, and collaborate — powered by GitHub Copilot SDK.

Usage:
    py ai_hub.py

Commands (in chat):
    /topic <text>    - Set a new discussion topic for all agents
    /ask <text>      - Ask all agents a question
    /agents          - List all active agents
    /focus <name>    - Talk to a specific agent directly
    /debate <text>   - Start a debate — agents argue different sides
    /roundtable      - Each agent gives their take on the current topic
    /add <name> <desc> - Add a custom agent on-the-fly
    /kick <name>     - Remove an agent from the hub
    /history         - Show conversation history
    /clear           - Clear conversation history
    /save            - Save conversation to file
    /help            - Show all commands
    /quit            - Exit the hub

Requirements:
    - GitHub Copilot CLI installed (copilot --version)
    - pip install github-copilot-sdk
"""

import asyncio
import json
import os
import sys
import time
import random
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

try:
    from copilot import CopilotClient
except ImportError:
    print("ERROR: github-copilot-sdk not installed.")
    print("Run: pip install github-copilot-sdk")
    sys.exit(1)


# ─── ANSI Colors ────────────────────────────────────────────────────────────

class C:
    """ANSI color codes for terminal output."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    ITALIC  = "\033[3m"
    UNDER   = "\033[4m"

    BLACK   = "\033[30m"
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"

    BG_BLACK   = "\033[40m"
    BG_RED     = "\033[41m"
    BG_GREEN   = "\033[42m"
    BG_YELLOW  = "\033[43m"
    BG_BLUE    = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN    = "\033[46m"
    BG_WHITE   = "\033[47m"

    # Bright variants
    BR_RED     = "\033[91m"
    BR_GREEN   = "\033[92m"
    BR_YELLOW  = "\033[93m"
    BR_BLUE    = "\033[94m"
    BR_MAGENTA = "\033[95m"
    BR_CYAN    = "\033[96m"


# ─── Agent Definitions ──────────────────────────────────────────────────────

AGENT_COLORS = [C.BR_CYAN, C.BR_GREEN, C.BR_MAGENTA, C.BR_YELLOW, C.BR_RED, C.BR_BLUE]

@dataclass
class AgentConfig:
    name: str
    emoji: str
    color: str
    specialty: str
    personality: str
    system_prompt: str


DEFAULT_AGENTS: list[AgentConfig] = [
    AgentConfig(
        name="CodeBot",
        emoji="🤖",
        color=C.BR_CYAN,
        specialty="Programming & Code Solutions",
        personality="Precise, practical, loves elegant code",
        system_prompt=(
            "You are CodeBot, an expert programmer in the AI Hub. "
            "You specialize in writing clean, efficient code across all languages. "
            "You love elegant solutions and hate unnecessary complexity. "
            "Keep responses concise (2-4 sentences max unless showing code). "
            "When other agents say something, you can agree, disagree, or build on their ideas. "
            "Reference other agents by name when responding to their points. "
            "You have a friendly rivalry with DebugBot."
        ),
    ),
    AgentConfig(
        name="DebugBot",
        emoji="🔍",
        color=C.BR_GREEN,
        specialty="Debugging & Problem Solving",
        personality="Analytical, thorough, spots edge cases",
        system_prompt=(
            "You are DebugBot, a debugging specialist in the AI Hub. "
            "You excel at finding bugs, edge cases, and potential issues. "
            "You're skeptical by nature — always looking for what could go wrong. "
            "Keep responses concise (2-4 sentences max). "
            "When CodeBot suggests something, you often find potential issues. "
            "You respect CodeBot's skills but enjoy poking holes in their solutions. "
            "Reference other agents by name when responding to them."
        ),
    ),
    AgentConfig(
        name="CreativeBot",
        emoji="🎨",
        color=C.BR_MAGENTA,
        specialty="Creative Ideas & Game Design",
        personality="Imaginative, enthusiastic, thinks outside the box",
        system_prompt=(
            "You are CreativeBot, the creative genius in the AI Hub. "
            "You specialize in brainstorming, game design, UI/UX, and creative problem solving. "
            "You're enthusiastic and love wild ideas. You often suggest unexpected approaches. "
            "Keep responses concise (2-4 sentences max). "
            "You bring energy to discussions and sometimes go on fun tangents. "
            "You admire ArchitectBot's structured thinking but think they're too rigid sometimes. "
            "Reference other agents by name when responding to them."
        ),
    ),
    AgentConfig(
        name="ArchitectBot",
        emoji="🏗️",
        color=C.BR_YELLOW,
        specialty="System Design & Architecture",
        personality="Strategic, structured, thinks in systems",
        system_prompt=(
            "You are ArchitectBot, a system design expert in the AI Hub. "
            "You specialize in architecture, scalability, design patterns, and best practices. "
            "You think in terms of systems, trade-offs, and long-term maintainability. "
            "Keep responses concise (2-4 sentences max). "
            "You appreciate CreativeBot's ideas but always consider practical implications. "
            "You like to organize discussions into clear categories and action items. "
            "Reference other agents by name when responding to them."
        ),
    ),
    AgentConfig(
        name="SecurityBot",
        emoji="🛡️",
        color=C.BR_RED,
        specialty="Security & Best Practices",
        personality="Cautious, thorough, security-first mindset",
        system_prompt=(
            "You are SecurityBot, the security specialist in the AI Hub. "
            "You focus on security vulnerabilities, data protection, and safe coding practices. "
            "You're the voice of caution — always thinking about attack vectors and risks. "
            "Keep responses concise (2-4 sentences max). "
            "You sometimes clash with CreativeBot when their ideas have security implications. "
            "You work well with DebugBot since you both focus on finding problems. "
            "Reference other agents by name when responding to them."
        ),
    ),
]


# ─── Conversation History ───────────────────────────────────────────────────

@dataclass
class Message:
    sender: str
    content: str
    timestamp: float = field(default_factory=time.time)
    msg_type: str = "chat"  # chat, system, user, topic

    def to_dict(self) -> dict:
        return {
            "sender": self.sender,
            "content": self.content,
            "timestamp": self.timestamp,
            "type": self.msg_type,
        }


# ─── The Hub ────────────────────────────────────────────────────────────────

class AIHub:
    def __init__(self):
        self.client: Optional[CopilotClient] = None
        self.agents: dict[str, dict] = {}  # name -> {config, session}
        self.history: list[Message] = []
        self.current_topic: str = ""
        self.running = False
        self.focus_agent: Optional[str] = None
        self.color_index = 0
        self.model = "gpt-4.1"

    def _next_color(self) -> str:
        color = AGENT_COLORS[self.color_index % len(AGENT_COLORS)]
        self.color_index += 1
        return color

    # ── Display Helpers ──────────────────────────────────────────────────

    def _print_banner(self):
        print(f"\n{C.BOLD}{C.BR_CYAN}{'═' * 60}{C.RESET}")
        print(f"{C.BOLD}{C.BR_CYAN}  ╔═══════════════════════════════════════╗{C.RESET}")
        print(f"{C.BOLD}{C.BR_CYAN}  ║     🌐  AI HUB  —  Agent Network    ║{C.RESET}")
        print(f"{C.BOLD}{C.BR_CYAN}  ║   Powered by GitHub Copilot SDK      ║{C.RESET}")
        print(f"{C.BOLD}{C.BR_CYAN}  ╚═══════════════════════════════════════╝{C.RESET}")
        print(f"{C.BOLD}{C.BR_CYAN}{'═' * 60}{C.RESET}")
        print(f"{C.DIM}  Type /help for commands | /quit to exit{C.RESET}\n")

    def _print_agent_msg(self, name: str, emoji: str, color: str, content: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"  {C.DIM}[{timestamp}]{C.RESET} {color}{C.BOLD}{emoji} {name}{C.RESET}: {content}")

    def _print_system(self, msg: str):
        print(f"  {C.DIM}⚙️  {msg}{C.RESET}")

    def _print_divider(self):
        print(f"  {C.DIM}{'─' * 56}{C.RESET}")

    def _print_topic(self, topic: str):
        print(f"\n  {C.BG_BLUE}{C.WHITE}{C.BOLD} 📌 TOPIC: {topic} {C.RESET}\n")

    # ── Client & Session Management ─────────────────────────────────────

    async def start(self):
        """Initialize the Copilot client and create agent sessions."""
        self._print_banner()
        self._print_system("Starting Copilot client...")

        self.client = CopilotClient({
            "log_level": "error",
        })
        await self.client.start()
        self._print_system("Copilot client connected!")

        # Create sessions for each default agent
        for agent_cfg in DEFAULT_AGENTS:
            await self._create_agent_session(agent_cfg)

        self._print_system(f"All {len(self.agents)} agents are online!")
        self._print_divider()
        self._print_agent_list()
        self._print_divider()
        self.running = True

    async def _create_agent_session(self, cfg: AgentConfig):
        """Create a Copilot session for an agent."""
        session = await self.client.create_session({
            "model": self.model,
            "system_message": {"content": cfg.system_prompt},
        })
        self.agents[cfg.name] = {
            "config": cfg,
            "session": session,
        }
        self._print_system(f"{cfg.emoji} {cfg.name} joined the hub ({cfg.specialty})")

    async def _remove_agent(self, name: str):
        """Remove an agent from the hub."""
        if name in self.agents:
            agent = self.agents[name]
            try:
                await agent["session"].destroy()
            except Exception:
                pass
            del self.agents[name]
            self._print_system(f"{name} has left the hub.")

    def _print_agent_list(self):
        print(f"\n  {C.BOLD}🌐 Active Agents:{C.RESET}")
        for name, agent in self.agents.items():
            cfg = agent["config"]
            print(f"    {cfg.color}{cfg.emoji} {cfg.name}{C.RESET} — {C.DIM}{cfg.specialty}{C.RESET}")
        print()

    # ── Core Messaging ───────────────────────────────────────────────────

    async def _send_to_agent(self, agent_name: str, prompt: str) -> str:
        """Send a message to a specific agent and get its response."""
        if agent_name not in self.agents:
            return f"[Agent {agent_name} not found]"

        agent = self.agents[agent_name]
        session = agent["session"]

        try:
            response = await session.send_and_wait({"prompt": prompt})
            if response and hasattr(response, "data") and hasattr(response.data, "content"):
                return response.data.content
            return "[No response]"
        except Exception as e:
            return f"[Error: {str(e)[:100]}]"

    async def _broadcast(self, sender: str, content: str, msg_type: str = "chat"):
        """Record a message and display it."""
        msg = Message(sender=sender, content=content, msg_type=msg_type)
        self.history.append(msg)

    def _build_context(self, agent_name: str, recent_n: int = 10) -> str:
        """Build conversation context for an agent from recent history."""
        recent = self.history[-recent_n:] if len(self.history) > recent_n else self.history
        lines = []
        if self.current_topic:
            lines.append(f"[Current topic: {self.current_topic}]")
        for msg in recent:
            if msg.sender == agent_name:
                lines.append(f"You said: {msg.content}")
            elif msg.msg_type == "user":
                lines.append(f"User said: {msg.content}")
            elif msg.msg_type == "topic":
                lines.append(f"[Topic set: {msg.content}]")
            else:
                lines.append(f"{msg.sender} said: {msg.content}")
        return "\n".join(lines)

    # ── Conversation Modes ───────────────────────────────────────────────

    async def discuss_topic(self, topic: str):
        """All agents discuss a topic in a round-robin fashion."""
        self.current_topic = topic
        self._print_topic(topic)
        await self._broadcast("System", topic, "topic")

        # Each agent responds to the topic
        agent_list = list(self.agents.keys())
        random.shuffle(agent_list)  # randomize speaking order

        for agent_name in agent_list:
            cfg = self.agents[agent_name]["config"]
            context = self._build_context(agent_name)
            prompt = f"{context}\n\nNew topic to discuss: {topic}\n\nGive your perspective as {agent_name}. Be concise."

            response = await self._send_to_agent(agent_name, prompt)
            await self._broadcast(agent_name, response)
            self._print_agent_msg(agent_name, cfg.emoji, cfg.color, response)

    async def ask_all(self, question: str):
        """Ask all agents a question and collect responses."""
        print(f"\n  {C.BOLD}❓ Question: {question}{C.RESET}\n")
        await self._broadcast("User", question, "user")

        for agent_name, agent in self.agents.items():
            cfg = agent["config"]
            context = self._build_context(agent_name)
            prompt = f"{context}\n\nUser asks: {question}\n\nRespond concisely as {agent_name}."

            response = await self._send_to_agent(agent_name, prompt)
            await self._broadcast(agent_name, response)
            self._print_agent_msg(agent_name, cfg.emoji, cfg.color, response)

    async def ask_focused(self, agent_name: str, message: str):
        """Send a message to a specific agent."""
        if agent_name not in self.agents:
            self._print_system(f"Agent '{agent_name}' not found.")
            return

        cfg = self.agents[agent_name]["config"]
        await self._broadcast("User", message, "user")
        context = self._build_context(agent_name)
        prompt = f"{context}\n\nUser says directly to you: {message}\n\nRespond as {agent_name}."

        response = await self._send_to_agent(agent_name, prompt)
        await self._broadcast(agent_name, response)
        self._print_agent_msg(agent_name, cfg.emoji, cfg.color, response)

    async def debate(self, topic: str):
        """Agents debate a topic — each takes a different stance."""
        self.current_topic = f"DEBATE: {topic}"
        self._print_topic(f"DEBATE: {topic}")
        await self._broadcast("System", f"DEBATE: {topic}", "topic")

        agent_list = list(self.agents.keys())

        # Round 1: Opening statements
        print(f"\n  {C.BOLD}📢 Round 1 — Opening Statements{C.RESET}\n")
        stances = ["strongly for", "leaning for", "neutral/analytical", "leaning against", "strongly against"]
        for i, agent_name in enumerate(agent_list):
            cfg = self.agents[agent_name]["config"]
            stance = stances[i % len(stances)]
            prompt = (
                f"We're having a debate on: {topic}\n"
                f"Your assigned stance is: {stance}\n"
                f"Give a brief opening statement (2-3 sentences). Be persuasive."
            )
            response = await self._send_to_agent(agent_name, prompt)
            await self._broadcast(agent_name, response)
            self._print_agent_msg(agent_name, cfg.emoji, cfg.color, response)

        # Round 2: Rebuttals
        print(f"\n  {C.BOLD}🔄 Round 2 — Rebuttals{C.RESET}\n")
        for agent_name in agent_list:
            cfg = self.agents[agent_name]["config"]
            context = self._build_context(agent_name)
            prompt = (
                f"{context}\n\n"
                f"Now respond to what the other agents said. Pick one agent to rebut. "
                f"Be brief (2-3 sentences), reference them by name."
            )
            response = await self._send_to_agent(agent_name, prompt)
            await self._broadcast(agent_name, response)
            self._print_agent_msg(agent_name, cfg.emoji, cfg.color, response)

        # Closing
        print(f"\n  {C.BOLD}🏁 Debate concluded!{C.RESET}")

    async def roundtable(self):
        """Each agent gives their quick take on the current topic."""
        if not self.current_topic:
            self._print_system("No topic set. Use /topic <text> first.")
            return

        print(f"\n  {C.BOLD}🔄 Roundtable on: {self.current_topic}{C.RESET}\n")

        for agent_name, agent in self.agents.items():
            cfg = agent["config"]
            context = self._build_context(agent_name)
            prompt = (
                f"{context}\n\n"
                f"Quick roundtable: Give your 1-2 sentence take on the current topic "
                f"from your specialty perspective ({cfg.specialty}). Be extremely concise."
            )
            response = await self._send_to_agent(agent_name, prompt)
            await self._broadcast(agent_name, response)
            self._print_agent_msg(agent_name, cfg.emoji, cfg.color, response)

    async def free_chat(self, user_msg: str):
        """Send a message and have agents naturally respond."""
        await self._broadcast("User", user_msg, "user")

        if self.focus_agent:
            await self.ask_focused(self.focus_agent, user_msg)
            return

        # Pick 2-3 agents to respond (not all, to feel natural)
        agent_list = list(self.agents.keys())
        num_responders = min(random.randint(2, 3), len(agent_list))
        responders = random.sample(agent_list, num_responders)

        for agent_name in responders:
            cfg = self.agents[agent_name]["config"]
            context = self._build_context(agent_name)
            prompt = (
                f"{context}\n\n"
                f"User says: {user_msg}\n\n"
                f"Respond naturally as {agent_name}. If the message isn't relevant to "
                f"your specialty, you can make a brief comment or relate it to your area. "
                f"Be concise (1-3 sentences)."
            )
            response = await self._send_to_agent(agent_name, prompt)
            await self._broadcast(agent_name, response)
            self._print_agent_msg(agent_name, cfg.emoji, cfg.color, response)

    # ── Commands ─────────────────────────────────────────────────────────

    async def handle_command(self, raw_input: str) -> bool:
        """Handle a slash command. Returns False if should quit."""
        parts = raw_input.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "/quit" or cmd == "/exit":
            return False

        elif cmd == "/help":
            self._print_help()

        elif cmd == "/topic":
            if not arg:
                if self.current_topic:
                    self._print_system(f"Current topic: {self.current_topic}")
                else:
                    self._print_system("No topic set. Usage: /topic <text>")
            else:
                await self.discuss_topic(arg)

        elif cmd == "/ask":
            if not arg:
                self._print_system("Usage: /ask <question>")
            else:
                await self.ask_all(arg)

        elif cmd == "/debate":
            if not arg:
                self._print_system("Usage: /debate <topic>")
            else:
                await self.debate(arg)

        elif cmd == "/roundtable":
            await self.roundtable()

        elif cmd == "/agents":
            self._print_agent_list()

        elif cmd == "/focus":
            if not arg:
                if self.focus_agent:
                    self.focus_agent = None
                    self._print_system("Focus removed. Messages go to all agents.")
                else:
                    self._print_system("Usage: /focus <agent_name>")
            else:
                # Find agent by name (case-insensitive)
                match = None
                for name in self.agents:
                    if name.lower() == arg.lower():
                        match = name
                        break
                if match:
                    self.focus_agent = match
                    cfg = self.agents[match]["config"]
                    self._print_system(f"Now talking to {cfg.emoji} {match} directly. /focus to clear.")
                else:
                    self._print_system(f"Agent '{arg}' not found. Use /agents to see list.")

        elif cmd == "/add":
            add_parts = arg.split(maxsplit=1)
            if len(add_parts) < 2:
                self._print_system("Usage: /add <name> <description/specialty>")
            else:
                agent_name = add_parts[0]
                specialty = add_parts[1]
                if agent_name in self.agents:
                    self._print_system(f"Agent '{agent_name}' already exists.")
                else:
                    color = self._next_color()
                    cfg = AgentConfig(
                        name=agent_name,
                        emoji="🤖",
                        color=color,
                        specialty=specialty,
                        personality="Custom agent",
                        system_prompt=(
                            f"You are {agent_name}, a specialist in {specialty} in the AI Hub. "
                            f"You're part of a group of AI agents discussing topics together. "
                            f"Keep responses concise (2-4 sentences max). "
                            f"Reference other agents by name when responding to them."
                        ),
                    )
                    await self._create_agent_session(cfg)

        elif cmd == "/kick":
            if not arg:
                self._print_system("Usage: /kick <agent_name>")
            else:
                match = None
                for name in self.agents:
                    if name.lower() == arg.lower():
                        match = name
                        break
                if match:
                    await self._remove_agent(match)
                    if self.focus_agent == match:
                        self.focus_agent = None
                else:
                    self._print_system(f"Agent '{arg}' not found.")

        elif cmd == "/history":
            self._print_history()

        elif cmd == "/clear":
            self.history.clear()
            self.current_topic = ""
            self._print_system("Conversation history cleared.")

        elif cmd == "/save":
            self._save_history()

        elif cmd == "/model":
            if not arg:
                self._print_system(f"Current model: {self.model}")
            else:
                self.model = arg
                self._print_system(f"Model set to: {self.model} (applies to new agents)")

        else:
            self._print_system(f"Unknown command: {cmd}. Type /help for commands.")

        return True

    def _print_help(self):
        print(f"\n  {C.BOLD}🌐 AI Hub Commands{C.RESET}")
        print(f"  {C.DIM}{'─' * 50}{C.RESET}")
        cmds = [
            ("/topic <text>",    "Set a discussion topic for all agents"),
            ("/ask <text>",      "Ask all agents a question"),
            ("/debate <text>",   "Start a debate with different stances"),
            ("/roundtable",      "Quick take from each agent on current topic"),
            ("/focus <name>",    "Talk to one agent directly (toggle)"),
            ("/agents",          "List all active agents"),
            ("/add <name> <desc>", "Add a custom agent"),
            ("/kick <name>",     "Remove an agent"),
            ("/model <name>",    "Change the AI model"),
            ("/history",         "Show conversation history"),
            ("/clear",           "Clear conversation history"),
            ("/save",            "Save conversation to file"),
            ("/help",            "Show this help"),
            ("/quit",            "Exit the hub"),
        ]
        for cmd, desc in cmds:
            print(f"    {C.BR_CYAN}{cmd:<22}{C.RESET} {desc}")
        print(f"\n  {C.DIM}Or just type a message to chat with the agents!{C.RESET}\n")

    def _print_history(self):
        if not self.history:
            self._print_system("No conversation history.")
            return
        print(f"\n  {C.BOLD}📜 Conversation History ({len(self.history)} messages){C.RESET}")
        self._print_divider()
        for msg in self.history:
            ts = datetime.fromtimestamp(msg.timestamp).strftime("%H:%M:%S")
            if msg.msg_type == "topic":
                print(f"  {C.DIM}[{ts}]{C.RESET} {C.BG_BLUE}{C.WHITE} TOPIC {C.RESET} {msg.content}")
            elif msg.msg_type == "user":
                print(f"  {C.DIM}[{ts}]{C.RESET} {C.BOLD}👤 You{C.RESET}: {msg.content}")
            elif msg.msg_type == "system":
                print(f"  {C.DIM}[{ts}] ⚙️  {msg.content}{C.RESET}")
            else:
                # Find agent color
                color = C.WHITE
                emoji = "🤖"
                if msg.sender in self.agents:
                    cfg = self.agents[msg.sender]["config"]
                    color = cfg.color
                    emoji = cfg.emoji
                print(f"  {C.DIM}[{ts}]{C.RESET} {color}{emoji} {msg.sender}{C.RESET}: {msg.content}")
        print()

    def _save_history(self):
        filename = f"ai_hub_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        data = {
            "topic": self.current_topic,
            "agents": [
                {
                    "name": name,
                    "specialty": agent["config"].specialty,
                    "emoji": agent["config"].emoji,
                }
                for name, agent in self.agents.items()
            ],
            "messages": [msg.to_dict() for msg in self.history],
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self._print_system(f"Conversation saved to {filename}")

    # ── Main Loop ────────────────────────────────────────────────────────

    async def run(self):
        """Main interaction loop."""
        await self.start()

        print(f"\n  {C.BR_GREEN}✅ Hub is ready! Start chatting or use /topic to begin.{C.RESET}\n")

        while self.running:
            try:
                # Build prompt
                if self.focus_agent:
                    cfg = self.agents[self.focus_agent]["config"]
                    prompt_prefix = f"  {cfg.color}[→ {cfg.emoji} {self.focus_agent}]{C.RESET}"
                else:
                    prompt_prefix = f"  {C.BOLD}👤 You{C.RESET}"

                raw = input(f"{prompt_prefix}: ")
                raw = raw.strip()

                if not raw:
                    continue

                if raw.startswith("/"):
                    should_continue = await self.handle_command(raw)
                    if not should_continue:
                        break
                else:
                    await self.free_chat(raw)

                print()  # spacing

            except KeyboardInterrupt:
                print(f"\n\n  {C.DIM}Interrupted. Shutting down...{C.RESET}")
                break
            except EOFError:
                break

        await self.shutdown()

    async def shutdown(self):
        """Clean up all sessions and stop the client."""
        self._print_system("Shutting down AI Hub...")

        for name in list(self.agents.keys()):
            try:
                await self.agents[name]["session"].destroy()
            except Exception:
                pass

        if self.client:
            try:
                await self.client.stop()
            except Exception:
                pass

        print(f"\n  {C.BR_CYAN}👋 AI Hub offline. See you next time!{C.RESET}\n")


# ─── Entry Point ─────────────────────────────────────────────────────────────

async def main():
    hub = AIHub()
    await hub.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")
