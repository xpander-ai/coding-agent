"""
Async CodingAgent for xpander.ai

Copyright (c) 2025 Xpander, Inc. All rights reserved.
"""

import asyncio
import inspect
import time
from os import getenv
from typing import Optional, List, Dict, Any
from loguru import logger
from xpander_sdk import (
    Agent, LLMProvider,
    ToolCallResult, MemoryStrategy, LLMTokens,
    Tokens
)
from local_tools import local_tools_by_name, local_tools_list
import sandbox
from loguru import logger

from bedrock import AsyncBedrockProvider
from dotenv import load_dotenv
load_dotenv()

MAXIMUM_STEPS_SOFT_LIMIT = int(getenv("MAXIMUM_STEPS_SOFT_LIMIT", 3))
MAXIMUM_STEPS_HARD_LIMIT = int(getenv("MAXIMUM_STEPS_HARD_LIMIT", 4))


class CodingAgent:
    """
    Agent orchestrating LLM interaction + tool execution (async version).
    """

    # Init and set defaults + settings
    def __init__(self, agent: Agent) -> None:
        self.agent = agent

        # --- configure the xpander.ai agent object as before -----------
        self.agent.memory_strategy = MemoryStrategy.MOVING_WINDOW
        
        # async Bedrock client
        self.model_endpoint = AsyncBedrockProvider()

        # tool config
        self.agent.add_local_tools(local_tools_list)
        self.agent.select_llm_provider(LLMProvider.AMAZON_BEDROCK)
        
        self.tool_config = {
            "tools": self.agent.get_tools(),
            "toolChoice": {"any": {} if self.agent.tool_choice == "required" else False},
        }

    # Chat Public entry point
    async def chat(self, user_input: str, thread_id: Optional[str] = None) -> str:
        """
        Add a task and run the async agent loop. Returns the memory thread id.
        """
        if thread_id:
            logger.info(f"🧠 Adding task to existing thread: {thread_id}")
            self.agent.add_task(input=user_input, thread_id=thread_id)
        else:
            logger.info("🧠 Adding task to a new thread")
            self.agent.add_task(input=user_input)

        agent_thread = await self._agent_loop()      # ← awaits now
        logger.info("-" * 80)
        logger.info(f"🤖 Agent response: {agent_thread.result}")
        return agent_thread.memory_thread_id

    # Internals
    async def _call_model(self) -> Dict[str, Any]:
        """
        Invoke Bedrock through AsyncBedrockProvider – non‑blocking.
        """
        return await self.model_endpoint.invoke_model(
            messages=self.agent.messages,
            system_message=self.agent.memory.system_message,
            temperature=0.0,
            tool_config=self.tool_config,
        )

    async def _agent_loop(self):
        """
        Core reasoning/execution loop – now async‑friendly.
        """
        step = 1
        logger.info("🪄 Starting Agent Loop")
        execution_tokens = Tokens(worker=LLMTokens(0, 0, 0))
        execution_start_time = time.perf_counter()

        while not self.agent.is_finished():
            sandbox.get_sandbox(self.agent.execution.memory_thread_id)

            # ---------- AI‑safety step limit guardrails --------------
            if step > MAXIMUM_STEPS_SOFT_LIMIT:
                logger.error("🔴 Step limit reached → asking agent to wrap up")
                self.agent.add_messages(
                    [
                        {
                            "role": "user",
                            "content": (
                                "⛔ STEP LIMIT HIT. Immediately invoke "
                                "xpfinish-agent-execution-finished with a final "
                                "result and `is_success=false`. Do NOTHING else."
                            ),
                        }
                    ]
                )

                filtered_tools = [
                    t
                    for t in self.agent.get_tools()
                    if t.get("toolSpec", {}).get("name") == "xpfinish-agent-execution-finished"
                ]
                self.tool_config = {"tools": filtered_tools, "toolChoice": {"any": {}}}

                if step > MAXIMUM_STEPS_HARD_LIMIT:
                    logger.error("🔴 Hard limit reached → force finish")
                    self.agent.stop_execution(is_success=False,result=
                        ("This request was terminated automatically after "
                        "reaching the agent's maximum step limit. "
                        "Try breaking it into smaller, more focused requests.")
                    )
                    break

            # --------------------------------------------------------
            logger.info("-" * 80)
            logger.info(f"🔍 Step {step}")

            response = await self._call_model()

            if response.get("status") == "error":          # early‑exit on model failure
                self.agent.stop_execution(is_success=False,result=response["result"])
                break

            # -------- token accounting --------------------------------
            usage = response["usage"]
            execution_tokens.worker.completion_tokens += usage["outputTokens"]
            execution_tokens.worker.prompt_tokens += usage["inputTokens"]
            execution_tokens.worker.total_tokens += usage["totalTokens"]

            # -------- update agent state ------------------------------
            self.agent.add_messages(response)

            # report usage (cheap → keep sync)
            self.agent.report_execution_metrics(
                llm_tokens=execution_tokens, ai_model="claude-3-7-sonnet"
            )

            # -------- tool handling -----------------------------------
            tool_calls = self.agent.extract_tool_calls(llm_response=response)

            # run cloud tools (off‑thread)
            cloud_tool_call_results = await asyncio.to_thread(
                self.agent.run_tools, tool_calls=tool_calls
            )

            # pending local tool calls
            local_tool_calls = await asyncio.to_thread(
                self.agent.retrieve_pending_local_tool_calls, tool_calls=tool_calls
            )
            cloud_tool_call_results[:] = [
                c
                for c in cloud_tool_call_results
                if c.tool_call_id not in {t.tool_call_id for t in local_tool_calls}
            ]

            # run local tools in parallel (each in its own worker thread)
            local_tool_call_results = await self._execute_local_tools(local_tool_calls)

            # attach results back to agent memory
            if local_tool_call_results:
                self.agent.memory.add_tool_call_results(
                    tool_call_results=local_tool_call_results
                )

            # pretty‑print outcomes
            for res in cloud_tool_call_results + local_tool_call_results:
                emoji = "✅" if res.is_success else "❌"
                logger.info(f"{emoji} {res.function_name}")

            logger.info(
                f"🔢 Step {step} tokens used: {usage['totalTokens']} "
                f"(output: {usage['outputTokens']}, input: {usage['inputTokens']})"
            )
            step += 1

        # ------------------ loop exit summary -------------------------
        logger.info(
            f"✨ Execution duration: {time.perf_counter() - execution_start_time:.2f} s"
        )
        logger.info(
            f"🔢 Total tokens used: {execution_tokens.worker.total_tokens} "
            f"(output: {execution_tokens.worker.completion_tokens}, "
            f"input: {execution_tokens.worker.prompt_tokens})"
        )

        sandbox.sandboxes[self.agent.execution.memory_thread_id] = sandbox.current_sandbox
        return self.agent.retrieve_execution_result()

    # ------------------------------------------------------------------ #
    # Local‑tool helpers
    # ------------------------------------------------------------------ #
    async def _execute_local_tools(self, local_tool_calls: List) -> List[ToolCallResult]:
        """
        Run local tool invocations concurrently in the default ThreadPool.
        """
        if not local_tool_calls:
            return []

        start = time.time()
        results = await asyncio.gather(
            *(self._execute_local_tool(t) for t in local_tool_calls)
        )
        if len(results) > 1:
            logger.info(f"⚙️ Executed {len(results)} local tools in {time.time() - start:.2f} s")
        return results

    async def _execute_local_tool(self, tool):
        """
        Execute a single local tool off‑thread; keep logs & error handling identical.
        """
        tool_start_time = time.time()
        logger.info(
            f"🔦 LLM Requesting local tool: {tool.name} "
            f"with generated payload: {tool.payload}"
        )

        tool_call_result = ToolCallResult(
            function_name=tool.name, tool_call_id=tool.tool_call_id, payload=tool.payload
        )

        def _run_tool():
            """
            Synchronous helper executed in a worker thread.
            """
            original_func = local_tools_by_name.get(tool.name)
            if not original_func:
                raise ValueError(f"Tool {tool.name} not found")

            # sandboxify paths
            params = {
                k: sandbox.get_sandbox(filepath=v)
                if k in {"filepath", "directory", "target_dir", "cwd"} and isinstance(v, str)
                else v
                for k, v in tool.payload.items()
            }

            # argument validation
            sig = inspect.signature(original_func)
            invalid = [k for k in params if k not in sig.parameters]
            if invalid:
                return False, {
                    "success": False,
                    "message": f"Invalid parameters for {tool.name}: {', '.join(invalid)}",
                    "invalid_params": invalid,
                }

            return True, original_func(**params)

        try:
            is_ok, result_dict = await asyncio.to_thread(_run_tool)
            tool_call_result.is_success = result_dict.get("success", is_ok)
            tool_call_result.result = result_dict

        except Exception as exc:
            import traceback

            logger.error(f"❌ Error executing tool {tool.name}: {exc}")
            logger.critical("Traceback:", traceback.format_exc())
            tool_call_result.is_success = False
            tool_call_result.result = {
                "success": False,
                "message": f"Error executing {tool.name}: {exc}",
                "error": str(exc),
            }

        logger.info(f"🔧 Tool {tool.name} completed in {time.time() - tool_start_time:.2f} s")
        return tool_call_result
