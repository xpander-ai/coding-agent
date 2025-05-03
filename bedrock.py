"""
Amazon Bedrock model provider implementation.

Copyright (c) 2025 Xpander, Inc. All rights reserved.
"""

import boto3
import time
from os import getenv
from botocore.config import Config
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
load_dotenv()

# Ensure required secrets
required_env_vars = ["AWS_REGION", "MAXIMUM_STEPS_SOFT_LIMIT", "MAXIMUM_STEPS_HARD_LIMIT", "MODEL_ID"]
if not getenv("AWS_PROFILE"):
    required_env_vars.extend(["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"])
missing_env_vars = [env_var_name for env_var_name in required_env_vars if getenv(env_var_name, None) is None]
if missing_env_vars:
    raise KeyError(f"Environment variables are missing: {missing_env_vars}")

class BedrockProvider:
    """
    Provider for Amazon Bedrock model API interactions.
    
    This class handles the communication with Amazon Bedrock,
    including authentication, timeouts, retries and error handling.
    """
    
    def __init__(self):
        """
        Initialize the Bedrock provider.
        
        Args:
            model_id (str, optional): The Bedrock model ID to use. Defaults to Claude 3 Sonnet.
            region (str, optional): AWS region. Defaults to value from environment variables.
        """
        # Configuration
        self.model_id = getenv("MODEL_ID")
        self.region = getenv("AWS_REGION")
        self.aws_profile = getenv("AWS_PROFILE")
        self.aws_session_token = getenv("AWS_SESSION_TOKEN")
        self.ai_safety = (f"If you have reached the maximum number of steps ({getenv('MAXIMUM_STEPS_SOFT_LIMIT')}), you must immediately call xpfinish-agent-execution-finished with the final result to complete this task, and provide useful feedback to the user about your progress and suggestions on how to call you again with a smaller task. Do nothing else.")
        
        try:
            # Setup Bedrock client with timeout configuration
            bedrock_config = Config(
                connect_timeout=300,  # 5-minute connection timeout
                read_timeout=300,     # 5-minute read timeout
            )
            
            if self.aws_profile:
                session = boto3.Session(profile_name=self.aws_profile)
                self.client = session.client("bedrock-runtime", region_name=self.region, config=bedrock_config)
            else:
                self.client = boto3.client(
                    "bedrock-runtime",
                    region_name=self.region,
                    aws_access_key_id=getenv("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=getenv("AWS_SECRET_ACCESS_KEY"),
                    aws_session_token=self.aws_session_token if self.aws_session_token else None,
                    config=bedrock_config
                )
                
            # We don't test the connection here since it could fail for various reasons
            # We'll instead let the invoke_model method handle failures
                
        except Exception as e:
            print(f"🔴 Error during Bedrock client initialization: {e}")
            print(f"🔴 Please check your AWS credentials and permissions.")
            # Set client to None so we can check for initialization failure
            self.client = None
    
    def invoke_model(self, 
                    messages: list, 
                    system_message: Optional[list[dict[str, str]]] = [],
                    temperature: float = 0.0,
                    tool_config: Optional[Dict] = None) -> Dict:
        """
        Invoke the Bedrock model with retry logic.
        
        Args:
            messages (list): The messages to send to the model.
            system_message (Any, optional): System message for the model.
            temperature (float, optional): Temperature setting. Defaults to 0.0.
            tool_config (Dict, optional): Tool configuration. Defaults to None.
            
        Returns:
            Dict: The model response.
            
        Raises:
            Exception: If all retry attempts fail.
        """
        # Check if initialization failed
        if self.client is None:
            print("🔴 Cannot invoke model - Bedrock client failed to initialize")
            return self._create_error_response("The Bedrock client failed to initialize. Please check your AWS credentials and permissions.")
            
        start_time = time.time()
        if system_message and len(system_message) > 0:
            system_message[0]['text'] = f"{system_message[0]['text']}\n\n{self.ai_safety}"
        try:
            # Build the request parameters
            params = {
                "modelId": self.model_id,
                "messages": messages,
                "inferenceConfig": {"temperature": temperature}
            }
            
            # Add optional parameters if provided
            if system_message:
                params["system"] = system_message
            
            if tool_config:
                params["toolConfig"] = tool_config
            
            # Direct synchronous call to the model
            response = self.client.converse(**params)
            
            end_time = time.time()
            print(f"🔄 Model response received in {end_time - start_time:.2f} seconds")
            return response
            
        except Exception as e:
            print(f"🔴 Error during model invocation: {e}")
            error_message = str(e)
            
            # Check for model ID validation error
            if "ValidationException" in error_message and "model identifier is invalid" in error_message:
                return self._create_error_response(f"The model ID '{self.model_id}' is invalid. Please check your MODEL_ID environment variable.")
            else:
                return self._create_error_response("An error occurred while invoking the model. Please try again later.")
    
    def _create_error_response(self, message: str) -> dict:
        return {
            "status": "error",
            "result": message,
        }