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

load_dotenv()

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

class AsyncBedrockProvider:
    """
    Async Provider for Amazon Bedrock model API interactions.
    
    This class handles the communication with Amazon Bedrock,
    including authentication, timeouts, retries and error handling.
    """

    def __init__(self) -> None:
        self.model_id = getenv("MODEL_ID")
        self.region   = getenv("AWS_REGION")
        self.aws_profile = getenv("AWS_PROFILE")
        self.aws_session_token = getenv("AWS_SESSION_TOKEN")

        # safetynet text appended to the first system message
        self.ai_safety = (
            f"If you have reached the maximum number of steps "
            f"({getenv('MAXIMUM_STEPS_SOFT_LIMIT')}), you must immediately "
            f"call xpfinish-agent-execution-finished with the final result "
            f"to complete this task, and provide useful feedback to the user "
            f"about your progress and suggestions on how to call you again "
            f"with a smaller task. Do nothing else."
        )

        # One Config object we’ll re‑use whenever we open a client
        self._client_cfg = Config(connect_timeout=300, read_timeout=300)

    async def invoke_model(
        self,
        messages: List[Dict[str, Any]],
        system_message: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.0,
        tool_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Call Bedrock’s /converse endpoint asynchronously.

        Returns the raw Bedrock JSON on success or an error dict on failure.
        """

        start = time.time()

        # ---- system prompt guardrail ----
        if system_message:
            # mutate copy in‑place to avoid subtle bugs; OK if caller re‑uses list
            system_message[0]["text"] = (
                f"{system_message[0]['text']}\n\n{self.ai_safety}"
            )

        # ---- Build the request once ----
        params: Dict[str, Any] = {
            "modelId": self.model_id,
            "messages": messages,
            "inferenceConfig": {"temperature": temperature},
        }
        if system_message:
            params["system"] = system_message
        if tool_config:
            params["toolConfig"] = tool_config

        # ---- Create an async client and call Bedrock ----
        # Using a context‑manager means the HTTPS connection is properly closed.
        try:
            async with self._get_client() as client:
                resp = await client.converse(**params)

            elapsed = time.time() - start
            logger.info(f"🔄 Model response received in {elapsed:.2f} s")
            return resp

        except Exception as exc:
            logger.error(f"🔴 Error during model invocation: {exc}")

            # Friendly message for wrong model ID
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
        Return an aioboto3 async‑client context manager.
        aioboto3 14.x no longer exposes the module‑level `client()` helper,
        so we always go through a `Session`.
        """
        # Build the session with or without explicit creds
        if self.aws_profile:
            session = aioboto3.Session(profile_name=self.aws_profile)
        else:
            session = aioboto3.Session(
                aws_access_key_id=getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=getenv("AWS_SECRET_ACCESS_KEY"),
                aws_session_token=self.aws_session_token or None,
            )

        # Return the async context‑manager that `async with` expects
        return session.client(
            "bedrock-runtime",
            region_name=self.region,
            config=self._client_cfg,
        )

    @staticmethod
    def _error_response(msg: str) -> Dict[str, str]:
        return {"status": "error", "result": msg}
