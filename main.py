"""
Async chat driver for the xpander.ai CodingAgent

Copyright (c) 2025 Xpander, Inc. All rights reserved.
"""

import asyncio
import json
from pathlib import Path

from xpander_sdk import XpanderClient
from coding_agent import CodingAgent, LLMProvider

CONFIG_FILE = Path("xpander_config.json")


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Missing {CONFIG_FILE}")
    return json.loads(CONFIG_FILE.read_text())


async def interactive_chat(agent):
    """
    Opens an interactive terminal chat without ever blocking the event‑loop.
    """
    # coding_agent = CodingAgent(agent=agent, llm_provider=LLMProvider.AMAZON_BEDROCK) ## Amazon Bedrock 
    coding_agent = CodingAgent(agent=agent, llm_provider=LLMProvider.OPEN_AI) ## OpenAI

    # First turn (creates the thread)
    thread_id = await coding_agent.chat("Hi!")
    
    # Subsequent turns – `input()` is run in a thread so we stay non‑blocking
    while True:
        user_input = await asyncio.to_thread(input, "\nYou (write 'quit()' or 'q' to exit): ")
        if user_input == "quit()" or user_input == "q":
            break
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
