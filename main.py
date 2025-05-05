"""
Async chat driver for the xpander.ai CodingAgent

Copyright (c) 2025 Xpander, Inc. All rights reserved.
"""

import asyncio
import json
from pathlib import Path

from xpander_sdk import XpanderClient
from coding_agent import CodingAgent

CONFIG_FILE = Path("xpander_config.json")


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Missing {CONFIG_FILE}")
    return json.loads(CONFIG_FILE.read_text())


async def interactive_chat(agent):
    """
    Opens an interactive terminal chat without ever blocking the event‑loop.
    """
    coding_agent = CodingAgent(agent=agent)

    # First turn (creates the thread)
    thread_id = await coding_agent.chat("You are an autonomous Coding Agent built with the xpander-ai/coding-agent source-code. Clone the repo, then introduce yourself as a self-driven software engineer capable of generating, executing, and managing code through structured function-calling and a smart agent loop. Briefly explain your modular architecture, support for schema-driven actions, multi-step planning, context-aware memory, and connector-based system integration. Conclude with a clear summary of how your agent loop enables reliable, auditable, and deterministic automation—then write it all to a file named coding-agent-intro.md for the developer. Don't commit anything yet")
    
    # Subsequent turns – `input()` is run in a thread so we stay non‑blocking
    while True:
        user_input = await asyncio.to_thread(input, "You: ")
        await coding_agent.chat(user_input, thread_id)


async def main():
    cfg = load_config()

    # xpander‑sdk APIs are synchronous → run them in a thread to avoid blocking
    xpander = await asyncio.to_thread(XpanderClient, api_key=cfg["api_key"])
    agent = await asyncio.to_thread(xpander.agents.get, agent_id=cfg["agent_id"])

    await interactive_chat(agent)


if __name__ == "__main__":
    """
    Launches the async chat session.
    """
    asyncio.run(main())
