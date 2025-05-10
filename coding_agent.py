"""
Async CodingAgent for xpander.ai

Copyright (c) 2025 Xpander, Inc. All rights reserved.
"""

import asyncio
import inspect
import time
from os import getenv
from typing import Literal, Optional, List, Dict, Any
from loguru import logger
from xpander_sdk import (
    Agent, LLMProvider,
    ToolCallResult, MemoryStrategy, LLMTokens,
    Tokens
)
from local_tools import local_tools_by_name, local_tools_list
import sandbox
from llm_providers import AsyncOpenAIProvider ## OpenAI
# from llm_providers import AsyncBedrockProvider ## Amazon Bedrock    
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig()
logging.getLogger().setLevel(logging.WARN)

MAXIMUM_STEPS_SOFT_LIMIT = int(getenv("MAXIMUM_STEPS_SOFT_LIMIT", 3))
MAXIMUM_STEPS_HARD_LIMIT = int(getenv("MAXIMUM_STEPS_HARD_LIMIT", 4))


class CodingAgent:
    """
    Async CodingAgent implementation for xpander.ai.

    Coordinates LLM interaction, manages reasoning steps, and executes both
    local and cloud tools asynchronously. Enforces safety constraints and
    token usage tracking.

    Args:
        agent (Agent): The xpander.ai Agent instance to operate.
        llm_provider (Literal): The provider to use (OPEN_AI or AMAZON_BEDROCK).
    """

    def __init__(
        self,
        agent: Agent,
        # llm_provider: Literal[LLMProvider.AMAZON_BEDROCK]
        llm_provider: Literal[LLMProvider.OPEN_AI]
    ) -> None:
        self.agent = agent
        self.llm_provider = llm_provider

        self.agent.memory_strategy = MemoryStrategy.MOVING_WINDOW
        self.agent.add_local_tools(local_tools_list)
        self.agent.select_llm_provider(llm_provider)

        # if llm_provider == LLMProvider.AMAZON_BEDROCK:
        #     self.model_endpoint = AsyncBedrockProvider()
        if llm_provider == LLMProvider.OPEN_AI:
            self.model_endpoint = AsyncOpenAIProvider()

    async def chat(self, user_input: str, thread_id: Optional[str] = None) -> str:
        """
        Public entry point for chat interaction.

        Adds a user task to the agent memory and initiates the async reasoning loop.

        Args:
            user_input (str): User's input or instruction.
            thread_id (Optional[str]): Memory thread to append to (if continuing a thread).

        Returns:
            str: The memory thread ID of the resulting agent run.
        """
        if thread_id:
            logger.info(f"🧠 Adding task to existing thread: {thread_id}")
            self.agent.add_task(input=user_input, thread_id=thread_id)
        else:
            logger.info("🧠 Adding task to a new thread")
            self.agent.add_task(input=user_input)

        agent_thread = await self._agent_loop()
        logger.info("-" * 80)
        logger.info(f"🤖 Agent response: {agent_thread.result}")
        return agent_thread.memory_thread_id

    async def _call_model(self, tools: Optional[List[Dict]] = []) -> Dict[str, Any]:
        """
        Internal helper to call the model endpoint.

        Args:
            tools (Optional[List[Dict]]): Tool specification for the model.

        Returns:
            Dict[str, Any]: Model response or error.
        """
        return await self.model_endpoint.invoke_model(
            messages=self.agent.messages,
            system_message=self.agent.memory.system_message,
            temperature=0.0,
            tools=tools,
            tool_choice=self.agent.tool_choice,
        )

    async def _agent_loop(self):
        """
        Core async loop coordinating reasoning steps and tool execution.

        Returns:
            Any: The final agent thread result after loop completion.
        """
        step = 1
        logger.info("🪄 Starting Agent Loop")
        execution_tokens = Tokens(worker=LLMTokens(0, 0, 0))
        execution_start_time = time.perf_counter()

        while not self.agent.is_finished():
            sandbox.get_sandbox(self.agent.execution.memory_thread_id)

            tools, reached_limit = self.has_step_limit_been_hit(step=step)
            if reached_limit:
                break

            logger.info("-" * 80)
            logger.info(f"🔍 Step {step}")

            response = await self._call_model(tools=tools)

            if (
                self.llm_provider == LLMProvider.AMAZON_BEDROCK
                and self.model_endpoint.should_stop_running(response=response)
            ):
                self.agent.stop_execution(is_success=False, result=response["result"])
                break

            step_usage = self.model_endpoint.handle_token_accounting(
                execution_tokens=execution_tokens,
                response=response,
            )

            llm_response = response.model_dump() if not isinstance(response, dict) else response
            self.agent.add_messages(llm_response)

            self.agent.report_execution_metrics(
                llm_tokens=execution_tokens,
                ai_model=self.model_endpoint.model_id,
            )

            tool_calls = self.agent.extract_tool_calls(llm_response=llm_response)

            cloud_tool_call_results = await asyncio.to_thread(
                self.agent.run_tools,
                tool_calls=tool_calls,
            )

            local_tool_calls = await asyncio.to_thread(
                self.agent.retrieve_pending_local_tool_calls,
                tool_calls=tool_calls,
            )
            cloud_tool_call_results[:] = [
                c for c in cloud_tool_call_results
                if c.tool_call_id not in {t.tool_call_id for t in local_tool_calls}
            ]

            local_tool_call_results = await self._execute_local_tools(local_tool_calls)

            if local_tool_call_results:
                self.agent.memory.add_tool_call_results(
                    tool_call_results=local_tool_call_results,
                )

            for res in cloud_tool_call_results + local_tool_call_results:
                emoji = "✅" if res.is_success else "❌"
                logger.info(f"{emoji} {res.function_name}")

            logger.info(
                f"🔢 Step {step} tokens used: {step_usage.total_tokens} "
                f"(output: {step_usage.completion_tokens}, input: {step_usage.prompt_tokens})"
            )
            step += 1

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

    async def _execute_local_tools(self, local_tool_calls: List) -> List[ToolCallResult]:
        """
        Execute multiple local tools concurrently in thread pool.

        Args:
            local_tool_calls (List): List of local tool calls to run.

        Returns:
            List[ToolCallResult]: Results of executed local tools.
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

    async def _execute_local_tool(self, tool) -> ToolCallResult:
        """
        Execute a single local tool in a background thread.

        Args:
            tool: Tool object to be executed.

        Returns:
            ToolCallResult: Result object with success flag and output payload.
        """
        tool_start_time = time.time()
        logger.info(
            f"🔦 LLM Requesting local tool: {tool.name} "
            f"with generated payload: {tool.payload}"
        )

        tool_call_result = ToolCallResult(
            function_name=tool.name,
            tool_call_id=tool.tool_call_id,
            payload=tool.payload,
        )

        def _run_tool():
            original_func = local_tools_by_name.get(tool.name)
            if not original_func:
                raise ValueError(f"Tool {tool.name} not found")

            params = {
                k: sandbox.get_sandbox(filepath=v)
                if k in {"filepath", "directory", "target_dir", "cwd"} and isinstance(v, str)
                else v
                for k, v in tool.payload.items()
            }

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
    
    
    def has_step_limit_been_hit(self, step: int) -> tuple[List[Dict], bool]:
        tools = self.agent.get_tools()
        
        reached_limit = False

        if step > MAXIMUM_STEPS_SOFT_LIMIT:
            logger.error("🔴 Step limit reached → asking agent to wrap up")
            self.agent.add_messages([
                {
                    "role": "user",
                    "content": (
                        "⛔ STEP LIMIT HIT. Immediately invoke "
                        "xpfinish-agent-execution-finished with a final "
                        "result and `is_success=false`. Do NOTHING else."
                    ),
                }
            ])
            tools = [
                t for t in tools
                if t.get("name", t.get("toolSpec", {}).get("name")) == "xpfinish-agent-execution-finished"
            ]

            if step > MAXIMUM_STEPS_HARD_LIMIT:
                logger.error("🔴 Hard limit reached → force finish")
                self.agent.stop_execution(
                    is_success=False,
                    result=(
                        "This request was terminated automatically after "
                        "reaching the agent's maximum step limit. "
                        "Try breaking it into smaller, more focused requests."
                    )
                )
                reached_limit = True
        
        return tools, reached_limit

