"""
Amazon Bedrock model provider implementation – async version using aioboto3.

Copyright (c) 2025 Xpander, Inc. All rights reserved.
"""

import aioboto3
from botocore.config import Config
from os import getenv
from typing import Dict, Optional, List, Any
from dotenv import load_dotenv
import time
from loguru import logger
from xpander_sdk import LLMTokens, Tokens

from .base import LLMProviderBase

load_dotenv()

def provider_check():
    # Ensure required secrets
    required_env_vars: List[str] = [
        "AWS_REGION",
        "MAXIMUM_STEPS_SOFT_LIMIT",
        "MAXIMUM_STEPS_HARD_LIMIT",
        "MODEL_ID",
    ]
    if not getenv("AWS_PROFILE"):
        required_env_vars += ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]

    missing = [v for v in required_env_vars if getenv(v) is None]
    if missing:
        raise KeyError(f"Environment variables are missing: {missing}")


class AsyncBedrockProvider(LLMProviderBase):
    """
    Async Provider for Amazon Bedrock model API interactions.

    Handles authentication, configuration, model invocation, and token tracking
    for the Bedrock runtime. Ensures safety instructions are enforced and supports
    retries and error logging.

    Environment Variables:
        AWS_REGION: AWS region for Bedrock.
        MODEL_ID: Identifier of the model to use.
        MAXIMUM_STEPS_SOFT_LIMIT: Step limit for AI execution safety.
        AWS_PROFILE / AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY: AWS credentials.
    """

    def __init__(self) -> None:
        provider_check()
        self.model_id = getenv("MODEL_ID")
        self.region = getenv("AWS_REGION")
        self.aws_profile = getenv("AWS_PROFILE")
        self.aws_session_token = getenv("AWS_SESSION_TOKEN")

        self.ai_safety = (
            f"If you have reached the maximum number of steps "
            f"({getenv('MAXIMUM_STEPS_SOFT_LIMIT')}), you must immediately "
            f"call xpfinish-agent-execution-finished with the final result "
            f"to complete this task, and provide useful feedback to the user "
            f"about your progress and suggestions on how to call you again "
            f"with a smaller task. Do nothing else."
        )

        self._client_cfg = Config(connect_timeout=300, read_timeout=300)

    async def invoke_model(
        self,
        messages: List[Dict[str, Any]],
        system_message: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.0,
        tools: Optional[List[Dict]] = [],
        tool_choice: Optional[str] = "required",
    ) -> Dict[str, Any]:
        """
        Asynchronously invoke the Bedrock model's /converse endpoint.

        Appends AI safety instructions to the system prompt and invokes
        the model with the specified configuration. Returns the raw Bedrock
        response or an error response on failure.

        Args:
            messages (List[Dict[str, Any]]): List of conversation messages.
            system_message (Optional[List[Dict[str, str]]]): Optional system prompt list.
            temperature (float): Temperature setting for the model generation.
            tools (Optional[List[Dict]]): Optional tool configuration for the model.
            tool_choice (Optional[str]): Tool usage policy, default is 'required'.

        Returns:
            Dict[str, Any]: Bedrock response or standardized error dictionary.
        """
        start = time.time()

        if system_message:
            system_message[0]["text"] = (
                f"{system_message[0]['text']}\n\n{self.ai_safety}"
            )

        params: Dict[str, Any] = {
            "modelId": self.model_id,
            "messages": messages,
            "inferenceConfig": {"temperature": temperature},
            "toolConfig": {
                "tools": tools,
                "toolChoice": {"any": {} if tool_choice == "required" else False},
            },
        }
        if system_message:
            params["system"] = system_message

        try:
            async with self._get_client() as client:
                resp = await client.converse(**params)

            elapsed = time.time() - start
            logger.info(f"🔄 Model response received in {elapsed:.2f} s")
            return resp

        except Exception as exc:
            logger.error(f"🔴 Error during model invocation: {exc}")
            msg = str(exc)

            if "ValidationException" in msg and "model identifier is invalid" in msg:
                err = (
                    f"The model ID '{self.model_id}' is invalid. "
                    "Please check your MODEL_ID environment variable."
                )
            else:
                err = "An error occurred while invoking the model. Please try again later."

            return self._error_response(err)

    def _get_client(self):
        """
        Create an asynchronous aioboto3 client for Bedrock Runtime.

        Returns:
            aioboto3.client: Asynchronous context-managed Bedrock client.
        """
        if self.aws_profile:
            session = aioboto3.Session(profile_name=self.aws_profile)
        else:
            session = aioboto3.Session(
                aws_access_key_id=getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=getenv("AWS_SECRET_ACCESS_KEY"),
                aws_session_token=self.aws_session_token or None,
            )

        return session.client(
            "bedrock-runtime",
            region_name=self.region,
            config=self._client_cfg,
        )

    def should_stop_running(self, response: Dict) -> bool:
        """
        Determine if the execution should stop based on the model response.

        Args:
            response (Dict): Response dictionary from the model.

        Returns:
            bool: True if response indicates an error, else False.
        """
        return response.get("status") == "error"

    def handle_token_accounting(self, execution_tokens: Tokens, response: Dict) -> LLMTokens:
        """
        Calculate and accumulate token usage based on model response.

        Args:
            execution_tokens (Tokens): Execution token tracking object.
            response (Dict): Model response containing usage metadata.

        Returns:
            LLMTokens: Structured token usage information for this execution.
        """
        usage = response["usage"]

        llm_tokens = LLMTokens(
            completion_tokens=usage["outputTokens"],
            prompt_tokens=usage["inputTokens"],
            total_tokens=usage["totalTokens"]
        )

        execution_tokens.worker.completion_tokens += llm_tokens.completion_tokens
        execution_tokens.worker.prompt_tokens += llm_tokens.prompt_tokens
        execution_tokens.worker.total_tokens += llm_tokens.total_tokens

        return llm_tokens
