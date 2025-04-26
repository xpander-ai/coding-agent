"""
Copyright (c) 2025 Xpander, Inc. All rights reserved.
"""

from xpander import get_agent
from coding_agent import CodingAgent

if __name__ == "__main__":
    agent = get_agent() ## will come from the CLI
    coding_agent = CodingAgent(agent=agent)
    # result = run_task(AgentExecution(input="Hello, how are you?"))
    thread = coding_agent.chat("Hi, I'm a new user to Xpander. Can you help me get started?")    
    while True:
        user_input = input("You: ")
        coding_agent.chat(user_input, thread)