import json
from xpander_utils.events import XpanderEventListener, AgentExecutionResult, AgentExecution, ExecutionStatus
from xpander_sdk import XpanderClient
from coding_agent import CodingAgent

# === Load Configuration ===
# Reads API credentials and organization context from a local JSON file
with open('xpander_config.json', 'r') as config_file:
    xpander_config: dict = json.load(config_file)

# === Initialize Event Listener ===
# Create a listener to subscribe to execution requests from specified agent(s)
listener = XpanderEventListener(**xpander_config)

# initialize xpander_client
xpander = XpanderClient(api_key=xpander_config.get("api_key"))

# initialize agent instance
agent = xpander.agents.get(agent_id=xpander_config.get("agent_id"))
coding_agent = CodingAgent(agent=agent)
# === Define Execution Handler ===
def on_execution_request(execution_task: AgentExecution) -> AgentExecutionResult:
    """
    Callback triggered when an execution request is received from a registered agent.
    
    Args:
        execution_task (AgentExecution): Object containing execution metadata and input.

    Returns:
        AgentExecutionResult: Object describing the output of the execution.
    """
    # You can access the execution input via `execution_task.input`
    # Example: Extracting a specific input field
    # user_input = execution_task.input.get("user_prompt", "")
    
    agent.init_task(execution=execution_task.model_dump())    
    execution_status = coding_agent._agent_loop()
    return AgentExecutionResult(result=execution_status.result,is_success=True if execution_status.status == ExecutionStatus.COMPLETED else False)

# === Register Callback ===
# Attach your custom handler to the listener
listener.register(on_execution_request=on_execution_request)