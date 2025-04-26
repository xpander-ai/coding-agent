"""
Copyright (c) 2025 Xpander, Inc. All rights reserved.
"""

import json
from xpander_utils.events import XpanderEventListener, AgentExecutionResult, AgentExecution, ExecutionStatus
from xpander import get_agent, run_task

# === Load Configuration ===
# Reads API credentials and organization context from a local JSON file
with open('xpander_config.json', 'r') as config_file:
    xpander_config: dict = json.load(config_file)

# Create a listener to subscribe to execution requests from specified agent(s)
listener = XpanderEventListener(**xpander_config)
xpander_agent = get_agent() ## Todo- move outside the function and deal with thread id
# === Define Execution Handler ===
def on_execution_request(execution_task: AgentExecution) -> AgentExecutionResult:
    """
    Callback triggered when an execution request is received from a registered agent.
    
    Args:
        execution_task (AgentExecution): Object containing execution metadata and input.

    Returns:
        AgentExecutionResult: Object describing the output of the execution.
    """
    
    ## Work around
    
    execution_status = run_task(xpander_agent, execution_task)
    return AgentExecutionResult(result=execution_status.result,is_success=True if execution_status.status == ExecutionStatus.COMPLETED else False)

# === Register Callback ===
# Attach your custom handler to the listener
print("📥 Waiting for execution requests...")
listener.register(on_execution_request=on_execution_request)
