import json
from xpander_utils.events import (
    XpanderEventListener,
    AgentExecutionResult,
    AgentExecution,
    ExecutionStatus,
)
from xpander_sdk import XpanderClient
from coding_agent import CodingAgent

# === Load Configuration ===
# Reads API credentials and organization context from a local JSON file.
with open('xpander_config.json', 'r') as config_file:
    xpander_config: dict = json.load(config_file)

# === Initialize Event Listener ===
# Creates a listener to subscribe to execution requests from specified agent(s).
listener = XpanderEventListener(**xpander_config, base_url="https://inbound.stg.xpander.ai")

# Initialize xpander client
xpander = XpanderClient(api_key=xpander_config.get("api_key"), base_url="https://inbound.stg.xpander.ai")

# === Define Execution Handler ===
def on_execution_request(execution_task: AgentExecution) -> AgentExecutionResult:
    """
    Callback triggered when an execution request is received from a registered agent.
    
    This function initializes a task for the agent and executes the agent loop to obtain results.

    Args:
        execution_task (AgentExecution): 
            Object containing metadata and input details for the execution task.

    Returns:
        AgentExecutionResult: 
            Object containing the execution result and a success flag based on execution status.

    Notes:
        - Integration built for xpander.ai agent execution flow.
        - The function calls the internal `_agent_loop` to process tasks.
    """
    
    # Initialize agent instance
    agent = xpander.agents.get(agent_id=xpander_config.get("agent_id"))
    coding_agent = CodingAgent(agent=agent)
    
    agent.init_task(execution=execution_task.model_dump())
    execution_status = coding_agent._agent_loop()
    
    return AgentExecutionResult(
        result=execution_status.result,
        is_success=True if execution_status.status == ExecutionStatus.COMPLETED else False,
    )

# === Register Callback ===
# Attach the custom handler to the event listener.
listener.register(on_execution_request=on_execution_request)
