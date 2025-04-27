"""
Copyright (c) 2025 Xpander, Inc. All rights reserved.
"""

from xpander import get_agent
from coding_agent import CodingAgent

if __name__ == "__main__":
    agent = get_agent() ## will come from the CLI
    coding_agent = CodingAgent(agent=agent)
    # result = run_task(AgentExecution(input="Hello, how are you?"))
    thread = coding_agent.chat("Reorder the apps in the apps folder of the xpander-ai/docs repo and commit it to a new branch once you figure it out")    
    while True:
        user_input = input("You: ")
        coding_agent.chat(user_input, thread)