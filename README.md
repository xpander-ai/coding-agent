# Agent Coding

A secure AI coding assistant that can clone, edit, and push changes to git repositories.

## Overview

Agent Coding is a Python-based AI agent that provides secure code manipulation capabilities. It uses Claude 3.7 Sonnet through AWS Bedrock to understand user requests and execute coding tasks in an isolated sandbox environment. The agent can clone repositories, create or modify files, and commit changes back to a repository.

## Features

- **Secure Sandboxing**: All file operations occur in isolated environments per thread
- **Git Integration**: Clone repositories and commit changes to new branches
- **File Operations**: Read, create, and edit files within the sandbox
- **Thread Isolation**: Each conversation maintains its own isolated workspace

## Architecture

The system consists of three main components:

1. **Coding Agent** (`coding_agent.py`): Handles interaction with AWS Bedrock, manages the AI conversation flow, and coordinates tool execution

2. **Sandbox** (`sandbox.py`): Provides a secure environment for file operations with basic path security to prevent sandbox escapes

3. **Local Tools** (`local_tools.py`): Defines the available operations the agent can perform

## Available Tools

- `git_clone`: Clone a git repository into the sandbox
- `describe_folders_and_files`: Show the contents of the sandbox in a tree structure
- `edit_file`: Modify an existing file
- `new_file`: Create a new file
- `read_file`: Read the contents of a file
- `commit`: Commit changes and push to a new branch

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up your AWS credentials for Bedrock access:
   - Either set AWS_PROFILE environment variable
   - Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY

## Usage

```python
from xpander_sdk import XpanderAgent
from coding_agent import CodingAgent

# Initialize the agent
agent = XpanderAgent()
coding = CodingAgent(agent)

# Start a conversation
thread_id = coding.chat("Clone the repository https://github.com/xpander-ai/docs.git and add a new tutorial")

# Continue the conversation in the same thread
coding.chat("Now commit these changes to a new branch called 'new-tutorial'", thread_id)
```

## Security

The sandbox implementation focuses on providing a secure, isolated environment for the AI to work with files:

- Each thread gets its own isolated workspace
- Path traversal attacks are blocked
- Operations are contained within the sandbox directory
- No arbitrary command execution is permitted


# Todo

- [ ] remove the xpander.py once the CLI is ready
- [ ] solve the duplicate local functions in the UI
- [ ] add thread id support in the xpander_handler
- [ ] add github and AWS auth support (Remote)
- [ ] add Agent 2 Agent support & Agent card
- [ ] test full flow with additional agents

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Xpander, Inc. All rights reserved.