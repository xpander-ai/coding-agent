"""
Copyright (c) 2025 Xpander, Inc. All rights reserved.
"""

import json
from coding_agent import CodingAgent
from xpander_sdk import XpanderClient

# === Load Configuration ===

# Reads API credentials and organization context from a local JSON file.
with open('xpander_config.json', 'r') as config_file:
    xpander_config: dict = json.load(config_file)

# Initialize xpander client
xpander = XpanderClient(api_key=xpander_config.get("api_key"))

# Initialize agent
agent = xpander.agents.get(agent_id=xpander_config.get("agent_id"))

# === Main Execution ===

if __name__ == "__main__":
    """
    Launches an interactive chat session with the CodingAgent.

    Notes:
        - Loads the agent configuration via xpander.ai SDK.
        - Initiates a conversation thread.
        - Continues a live chat loop with user input.
    """
    coding_agent = CodingAgent(agent=agent)

    # Example for initial instruction (commented out alternative example):
    # result = run_task(AgentExecution(input="Hello, how are you?"))

    thread = coding_agent.chat("You are an autonomous Coding Agent built with the xpander-ai/coding-agent source-code. Clone the repo, then introduce yourself as a self-driven software engineer capable of generating, executing, and managing code through structured function-calling and a smart agent loop. Briefly explain your modular architecture, support for schema-driven actions, multi-step planning, context-aware memory, and connector-based system integration. Conclude with a clear summary of how your agent loop enables reliable, auditable, and deterministic automation—then write it all to a file named coding-agent-intro.md for the developer. Don't commit anything yet.")    
    while True:
        user_input = input("You: ")
        coding_agent.chat(user_input, thread)
