"""
Copyright (c) 2025 Xpander, Inc. All rights reserved.
"""

import asyncio
import inspect
from typing import Optional
import boto3
from os import getenv
from dotenv import load_dotenv
from xpander_sdk import Agent, LLMProvider, XpanderClient, ToolCallResult, MemoryStrategy
from local_tools import local_tools_by_name, local_tools_list
import sandbox

# === Load Environment Variables ===

load_dotenv()

# Ensure required secrets
required_env_vars = ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
missing_env_vars = [env_var_name for env_var_name in required_env_vars if getenv(env_var_name, None) is None]
if missing_env_vars:
    raise KeyError(f"Environment variables are missing: {missing_env_vars}")

# AWS config
AWS_PROFILE = getenv("AWS_PROFILE", None)
AWS_ACCESS_KEY_ID = getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = getenv("AWS_REGION", None)
AWS_SESSION_TOKEN = getenv("AWS_SESSION_TOKEN", None)

# Model configuration
MODEL_ID = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"

# === Coding Agent Class ===

class CodingAgent:
    """
    Agent handling Bedrock interaction.

    Attributes:
        agent (Agent): The xpander.ai agent instance.
        bedrock (boto3.Client): AWS Bedrock runtime client.
        tool_config (dict): Configuration for available tools.
    """

    def __init__(self, agent: Agent):
        """
        Initialize the CodingAgent.

        Args:
            agent (Agent): Agent object initialized via xpander.ai SDK.
        """
        self.agent = agent
        self.agent.add_local_tools(local_tools_list)
        self.agent.select_llm_provider(LLMProvider.AMAZON_BEDROCK)
        self.agent.memory_strategy = MemoryStrategy.BUFFERING

        # Setup Bedrock client
        if AWS_PROFILE:
            session = boto3.Session(profile_name=AWS_PROFILE)
            self.bedrock = session.client("bedrock-runtime", region_name=AWS_REGION)
        else:
            self.bedrock = boto3.client(
                "bedrock-runtime",
                region_name=AWS_REGION,
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                aws_session_token=AWS_SESSION_TOKEN if AWS_SESSION_TOKEN else None
            )

        # Configure tools
        self.tool_config = {
            "tools": agent.get_tools(),
            "toolChoice": {"any": {} if agent.tool_choice == 'required' else False}
        }

    def chat(self, user_input: str, thread_id: Optional[str] = None):
        """
        Start a conversation with the agent.

        Args:
            user_input (str): User message.
            thread_id (Optional[str]): Existing thread identifier (for continuity).

        Returns:
            str: Memory thread ID associated with the conversation.
        """
        if thread_id:
            print(f"🧠 Adding task to existing thread: {thread_id}")
            self.agent.add_task(input=user_input, thread_id=thread_id)
        else:
            print("🧠 Adding task to a new thread")
            self.agent.add_task(input=user_input)

        agent_thread = self._agent_loop()

        print(f"📝 Last message: {self.agent.messages[-1]['content'][-1]}")
        print(f"🧠 AI Agent response: {agent_thread.result}")
        return agent_thread.memory_thread_id

    def _agent_loop(self):
        """
        Run the agent interaction loop, handling LLM responses and tool executions.

        Returns:
            ExecutionResult: Final result after task execution.
        """
        step = 1
        print("🪄 Starting Agent Loop")
        while not self.agent.is_finished():

            if self.agent.execution.memory_thread_id:
                print(f"🧠 Thread id: {self.agent.execution.memory_thread_id}")
                sandbox.get_sandbox(self.agent.execution.memory_thread_id)

            print("-" * 80)
            print(f"🔍 Step {step}")

            response = self.bedrock.converse(
                modelId=MODEL_ID,
                messages=self.agent.messages,
                inferenceConfig={"temperature": 0.0},
                toolConfig=self.tool_config,
                system=self.agent.memory.system_message
            )
            self.agent.add_messages(response)

            # Extract and execute tool calls
            tool_calls = self.agent.extract_tool_calls(llm_response=response)
            cloud_tool_call_results = self.agent.run_tools(tool_calls=tool_calls)

            # Handle local tool calls
            local_tool_calls = XpanderClient.retrieve_pending_local_tool_calls(tool_calls=tool_calls)
            cloud_tool_call_results[:] = [c for c in cloud_tool_call_results if c.tool_call_id not in {t.tool_call_id for t in local_tool_calls}]
            local_tool_call_results = asyncio.run(self._execute_local_tools_in_parallel(local_tool_calls))

            if local_tool_call_results:
                self.agent.memory.add_tool_call_results(tool_call_results=local_tool_call_results)

            # Print tool execution results
            all_tool_call_results = cloud_tool_call_results + local_tool_call_results
            for result in all_tool_call_results:
                emoji = "✅" if result.is_success else "❌"
                print(f"{emoji} {result.function_name}")

            step += 1

        sandbox.sandboxes[self.agent.execution.memory_thread_id] = sandbox.current_sandbox
        return self.agent.retrieve_execution_result()

    async def _execute_local_tools_in_parallel(self, local_tool_calls):
        """
        Execute multiple local tools in parallel.

        Args:
            local_tool_calls (list): List of tool calls to execute.

        Returns:
            list: Results from all executed tools.
        """
        tasks = [self._execute_local_tool(tool) for tool in local_tool_calls]
        return await asyncio.gather(*tasks)

    async def _execute_local_tool(self, tool):
        """
        Execute a single local tool securely.

        Args:
            tool (ToolCall): Tool call object.

        Returns:
            ToolCallResult: Result of tool execution.
        """
        print(f"🔦 Executing local tool: {tool.name} with generated payload: {tool.payload}")
        tool_call_result = ToolCallResult(function_name=tool.name, tool_call_id=tool.tool_call_id, payload=tool.payload)

        try:
            original_func = local_tools_by_name[tool.name]

            sandboxed_params = {}
            for key, value in tool.payload.items():
                if key in ['filepath', 'directory', 'target_dir', 'cwd'] and isinstance(value, str):
                    sandboxed_params[key] = sandbox.get_sandbox(filepath=value)
                else:
                    sandboxed_params[key] = value

            sig = inspect.signature(original_func)
            valid_params = sig.parameters.keys()
            invalid_params = [k for k in sandboxed_params if k not in valid_params]
            if invalid_params:
                tool_call_result.is_success = False
                tool_call_result.result = {
                    "success": False,
                    "message": f"Invalid parameters for {tool.name}: {', '.join(invalid_params)}",
                    "invalid_params": invalid_params
                }
                return tool_call_result

            if asyncio.iscoroutinefunction(original_func):
                local_tool_response = await original_func(**sandboxed_params)
            else:
                def run_func():
                    return original_func(**sandboxed_params)
                loop = asyncio.get_event_loop()
                local_tool_response = await loop.run_in_executor(None, run_func)

            tool_call_result.is_success = local_tool_response.get('success', True)
            tool_call_result.result = local_tool_response

        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"❌ Error executing tool {tool.name}: {str(e)}")
            print(f"Traceback: {error_traceback}")

            tool_call_result.is_success = False
            tool_call_result.result = {
                "success": False,
                "message": f"Error executing {tool.name}: {str(e)}",
                "error": str(e)
            }

        return tool_call_result
