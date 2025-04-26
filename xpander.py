"""
Copyright (c) 2025 Xpander, Inc. All rights reserved.
"""

import json
import os
from dotenv import load_dotenv
from xpander_sdk import XpanderClient, Agent, Execution
from xpander_utils.events import AgentExecution
from coder_agent import CoderAgent
# Setup
load_dotenv()
XPANDER_API_KEY = os.environ.get("XPANDER_API_KEY")
xpander_client = XpanderClient(api_key=XPANDER_API_KEY)

def get_agent():
    """Get or create an agent with proper configuration and handle synchronization"""
    # Step 1: Load xpander_config.json if exists or create default
    config = {}
    try:
        with open('xpander_config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {'agent_id': None, 'api_key': '', 'organization_id': ''}
    
    # Step 2: Check if we have an existing agent ID
    if config.get('agent_id'):
        # 2a: Load existing agent from cloud
        print(f"Loading existing agent: {config['agent_id']}")
        agent = xpander_client.agents.get(config['agent_id'])
        
        # 2b: Check if local instructions exist
        local_instructions = None
        try:
            with open('agent_instructions.json', 'r') as f:
                local_instructions = json.load(f)
                print("Found local agent_instructions.json")
                
                # 2c: Update cloud agent with local instructions if they exist
                if local_instructions:
                    print("Updating cloud agent with local instructions")
                    agent.instructions.general = local_instructions.get('general', agent.instructions.general)
                    agent.instructions.goal = local_instructions.get('goal', agent.instructions.goal)
                    agent.instructions.role = local_instructions.get('role', agent.instructions.role)
        except FileNotFoundError:
            # 2d: No local instructions, download from cloud agent
            print("No local agent_instructions.json found. Creating from cloud agent settings.")
            cloud_instructions = {
                'general': agent.instructions.general,
                'goal': agent.instructions.goal,
                'role': agent.instructions.role
            }
            with open('agent_instructions.json', 'w') as f:
                json.dump(cloud_instructions, f, indent=2)
    else:
        # Step 3: Create new agent
        print("Creating new agent")
        agent = xpander_client.agents.create(name="Coder Agent")
        
        # 3a: Update config with new agent info
        config.update({
            'organization_id': agent.organization_id,
            'api_key': XPANDER_API_KEY,
            'agent_id': agent.id
        })
        with open('xpander_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        # 3b: Load and apply instructions
        try:
            with open('agent_instructions.json', 'r') as f:
                instructions = json.load(f)
                print("Applying local instructions to new agent")
                agent.instructions.general = instructions.get('general', '')
                agent.instructions.goal = instructions.get('goal', '')
                agent.instructions.role = instructions.get('role', '')
        except FileNotFoundError:
            print("No agent_instructions.json found. Using defaults.")
            default_instructions = {
                'general': "You are a helpful assistant.",
                'goal': "Your goal is to help the user with their questions.",
                'role': "Your role is not specific to any domain."
            }
            # Create default instructions file
            with open('agent_instructions.json', 'w') as f:
                json.dump(default_instructions, f, indent=2)
            
            # Apply default instructions to agent
            agent.instructions.general = default_instructions['general']
            agent.instructions.goal = default_instructions['goal']
            agent.instructions.role = default_instructions['role']
    # Step 4: Ensure config is up to date
    config.update({
        'organization_id': agent.organization_id,
        'api_key': XPANDER_API_KEY,
        'agent_id': agent.id
    })
    with open('xpander_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    print("🤖 Agent is ready")
    print(f"Check the agent in the xpander dashboard: https://app.xpander.ai/agents/{agent.id}")
    return agent

def run_task(agent: Agent, execution_task: AgentExecution) -> Execution:
    agent.init_task(execution=execution_task.model_dump())    
    return CoderAgent(agent=agent)._agent_loop()