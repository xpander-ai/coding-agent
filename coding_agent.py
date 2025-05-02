"""
Copyright (c) 2025 Xpander, Inc. All rights reserved.
"""

import inspect
from typing import Optional
from xpander_sdk import Agent, LLMProvider, XpanderClient, ToolCallResult, MemoryStrategy, LLMTokens, Tokens
from local_tools import local_tools_by_name, local_tools_list
import sandbox
import time
from bedrock import BedrockProvider

# === Coding Agent Class ===

MAXIMUM_STEPS_SOFT_LIMIT = 5
MAXIMUM_STEPS_HARD_LIMIT = 7


class CodingAgent:
    """
    Agent handling LLM interaction.

    Attributes:
        agent (Agent): The xpander.ai agent instance.
        model_provider: The model provider (e.g., BedrockProvider)
        tool_config (dict): Configuration for available tools.
    """

    def __init__(self, agent: Agent, model_id: Optional[str] = None):
        """
        Initialize the CodingAgent.

        Args:
            agent (Agent): Agent object initialized via xpander.ai SDK.
            model_id (Optional[str]): Model ID to use. If not provided, defaults to provider's default.
        """
        self.agent = agent
        self.agent.add_local_tools(local_tools_list)
        self.agent.memory_strategy = MemoryStrategy.CLEAN_TOOL_CALLS
        self.agent.select_llm_provider(LLMProvider.AMAZON_BEDROCK)
        self.model_endpoint = BedrockProvider(model_id=model_id)

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
        print("-" * 80)
        print(f"🤖 Agent response: {agent_thread.result}")
        return agent_thread.memory_thread_id

    def _call_model(self):
        """
        Call the LLM model using the configured provider.
        
        Returns:
            Dict: Model response
        """
        return self.model_endpoint.invoke_model(
            messages=self.agent.messages,
            system_message=self.agent.memory.system_message,
            temperature=0.0,
            tool_config=self.tool_config
        )
    
    def _agent_loop(self):
        """
        Run the agent interaction loop, handling LLM responses and tool executions.

        Returns:
            ExecutionResult: Final result after task execution.
        """
        step = 1
        print("🪄 Starting Agent Loop")
        execution_tokens = Tokens(worker=LLMTokens(completion_tokens=0, prompt_tokens=0, total_tokens=0))
        execution_start_time = time.perf_counter()
        
        while not self.agent.is_finished():
            sandbox.get_sandbox(self.agent.execution.memory_thread_id)

            ## AI Safety Check
            if step > MAXIMUM_STEPS_SOFT_LIMIT:
                print("🔴 Step limit reached. Sending user message to gracefully finish execution.")
                self.agent.add_messages([{"role": "user", "content": "The steps limit has been reached. Please stop the execution by calling the xpfinish-agent-execution-finished tool with the last result. All access to other tools has been blocked, please use the xpfinish-agent-execution-finished tool to finish the execution."}])

                ## Filter tools to only include the xpfinish-agent-execution-finished tool
                filtered_tools = [tool for tool in self.agent.get_tools() if tool.get('toolSpec', {}).get('name') == 'xpfinish-agent-execution-finished']
                self.tool_config = {
                    "tools": filtered_tools,
                    "toolChoice": {"any": {}}
                }
                
                ## In rare cases, the agent may not respond to the user message.
                ## We will break the loop after a certain number of steps to avoid infinite loops.
                if step > MAXIMUM_STEPS_HARD_LIMIT:
                    break

            print("-" * 80)
            print(f"🔍 Step {step}")

            response = self._call_model()
            
            # Track token usage
            execution_tokens.worker.completion_tokens += response['usage']['outputTokens']
            execution_tokens.worker.prompt_tokens += response['usage']['inputTokens']
            execution_tokens.worker.total_tokens += response['usage']['totalTokens']
            
            # Update agent state
            self.agent.add_messages(response)
            
            # Report execution metrics to Xpander
            self.agent.report_execution_metrics(
                llm_tokens=execution_tokens,
                ai_model="claude-3-7-sonnet"
            )

            # Extract tool calls
            tool_calls = self.agent.extract_tool_calls(llm_response=response)
            cloud_tool_call_results = self.agent.run_tools(tool_calls=tool_calls)

            # Handle local tool calls
            local_tool_calls = XpanderClient.retrieve_pending_local_tool_calls(tool_calls=tool_calls)
            cloud_tool_call_results[:] = [c for c in cloud_tool_call_results 
                                          if c.tool_call_id not in {t.tool_call_id for t in local_tool_calls}]
            
            # Process local tool calls sequentially
            local_tool_call_results = self._execute_local_tools(local_tool_calls)

            # Update results
            if local_tool_call_results:
                self.agent.memory.add_tool_call_results(tool_call_results=local_tool_call_results)

            # Print tool execution results
            all_tool_call_results = cloud_tool_call_results + local_tool_call_results
            for result in all_tool_call_results:
                emoji = "✅" if result.is_success else "❌"
                print(f"{emoji} {result.function_name}")

            print(f"🔢 Step {step} tokens used: {response['usage']['totalTokens']} (output: {response['usage']['outputTokens']}, input: {response['usage']['inputTokens']})")
            step += 1
            

        print(f"✨ Execution duration: {time.perf_counter() - execution_start_time:.2f} seconds")
        print(f"🔢 Total tokens used: {execution_tokens.worker.total_tokens} (output: {execution_tokens.worker.completion_tokens}, input: {execution_tokens.worker.prompt_tokens})")
        # Store sandbox state for the thread
        sandbox.sandboxes[self.agent.execution.memory_thread_id] = sandbox.current_sandbox
        return self.agent.retrieve_execution_result()

    def _execute_local_tools(self, local_tool_calls):
        """
        Execute local tools sequentially.

        Args:
            local_tool_calls (list): List of tool calls to execute.

        Returns:
            list: Results from all executed tools.
        """
        if not local_tool_calls:
            return []
            
        start_time = time.time()
        
        # Execute tools sequentially
        results = []
        for tool in local_tool_calls:
            results.append(self._execute_local_tool(tool))
            
        end_time = time.time()
        
        if len(local_tool_calls) > 1:
            print(f"⚙️ Executed {len(local_tool_calls)} local tools in {end_time - start_time:.2f} seconds")
            
        return results

    def _execute_local_tool(self, tool):
        """
        Execute a single local tool.

        Args:
            tool (ToolCall): Tool call object.

        Returns:
            ToolCallResult: Result of tool execution.
        """
        tool_start_time = time.time()
        print(f"🔦 LLM Requesting to invoke local tool: {tool.name} with generated payload: {tool.payload}")
        tool_call_result = ToolCallResult(function_name=tool.name, tool_call_id=tool.tool_call_id, payload=tool.payload)

        try:
            # Get the tool function
            original_func = local_tools_by_name.get(tool.name)
            if not original_func:
                raise ValueError(f"Tool {tool.name} not found")
            
            # Work with the payload directly
            tool_payload = tool.payload
            
            sandboxed_params = {}
            for key, value in tool_payload.items():
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

            # Execute the function directly (synchronously)
            local_tool_response = original_func(**sandboxed_params)
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
            
        tool_end_time = time.time()
        print(f"🔧 Tool {tool.name} completed in {tool_end_time - tool_start_time:.2f} seconds")
        return tool_call_result
