"""
Async event‑driven executor for xpander.ai CodingAgent

Copyright (c) 2025 Xpander, Inc. All rights reserved.
"""

import asyncio
import json
from pathlib import Path
from loguru import logger

from xpander_utils.events import (
    XpanderEventListener,
    AgentExecutionResult,
    AgentExecution,
    ExecutionStatus,
)
from xpander_sdk import XpanderClient
from coding_agent import CodingAgent

# Configuration & SDK setup (sync → thread‑offloaded where needed)

CFG_PATH = Path("xpander_config.json")
if not CFG_PATH.exists():
    raise FileNotFoundError("Missing xpander_config.json")

xpander_cfg: dict = json.loads(CFG_PATH.read_text())

# xpander‑sdk is blocking; create the client in a worker thread
xpander: XpanderClient = asyncio.run(
    asyncio.to_thread(XpanderClient, api_key=xpander_cfg["api_key"])
)

# Async execution handler
async def on_execution_request(execution_task: AgentExecution) -> AgentExecutionResult:
    """
    Handles an execution request arriving via XpanderEventListener.
    Must be async‑def so the listener can await it without blocking.
    """

    try:
        # --- fetch agent object (blocking → thread) -------------------
        agent = await asyncio.to_thread(
            xpander.agents.get, agent_id=xpander_cfg["agent_id"]
        )

        # initialise task metadata (also blocking)
        await asyncio.to_thread(agent.init_task, execution=execution_task.model_dump())

        # --- run the CodingAgent -------------------------------------
        coding_agent = CodingAgent(agent=agent)
        exec_status = await coding_agent._agent_loop()   # returns ExecutionResult

    except Exception as exc:
        # --------------------------------------------------------------
        logger.error(f"❌ Error in agent loop: {exc}")

        # Ensure xpander agent reflects failure state
        agent = await asyncio.to_thread(
            xpander.agents.get, agent_id=xpander_cfg["agent_id"]
        )
        await asyncio.to_thread(agent.init_task, execution=execution_task.model_dump())
        agent.execution.status = ExecutionStatus.ERROR
        agent.execution.result = (
            "The agent is not available at this time. Please try again later."
        )

        return AgentExecutionResult(result=agent.execution.result, is_success=False)

    # ---------------- normal completion ------------------------------
    return AgentExecutionResult(
        result=exec_status.result,
        is_success=exec_status.status == ExecutionStatus.COMPLETED,
    )


# Event listener registration

listener = XpanderEventListener(**xpander_cfg)
listener.register(on_execution_request=on_execution_request)

# The listener’s internal loop is usually started automatically after
# registration; if not, you might need to call `listener.start()` here.
