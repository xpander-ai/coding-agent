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
xpander = XpanderClient(
    api_key=xpander_config.get("api_key"),
    base_url="https://inbound.stg.xpander.ai"  # TODO: REMOVE BASE_URL
)

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
    # thread = coding_agent.chat("Reorder the apps in the apps folder of the xpander-ai/docs repo and commit it to a new branch once you figure it out")

    thread = coding_agent.chat("Hi")
    
    while True:
        user_input = input("You: ")
        coding_agent.chat(user_input, thread)
