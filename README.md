# 🚀 Open-Source Framework-Agnostic Coding Agent

<div align="center">

## <strong> Build your own Coding Agent; framework-agnostic, LLM-agnostic, and supercharged by the <a href="https://xpander.ai" target="_blank">xpander.ai</a></strong> agents platform

![version](https://img.shields.io/badge/version-1.0.0-blue)
![license](https://img.shields.io/badge/license-MIT-green)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/xpander-ai/coding-agent/pulls)
[![Discord](https://img.shields.io/badge/Discord-Join%20our%20community-7289DA)](https://discord.gg/CUcp4WWh5g)
[![Slack](https://img.shields.io/badge/Join%20our%20Slack%20community-Click%20here-4A154B)](https://join.slack.com/t/xpandercommunity/shared_invite/zt-2mt2xkxkz-omM7f~_h2jcuzFudrYtZQQ)

<br>

<img src="images/coding-agent.png" alt="High‑level architecture diagram for Coding Agent" width="600">

</div>



# What is the xpander.ai Coding Agent?

The Coding Agent is an open-source, minimal implementation of an autonomous AI agent that can read, write, and commit code to a Git repository. It avoids abstractions and is vendor-agnostic, making it suitable for developers looking to understand or extend agent behavior directly.

It’s designed to operate as a standalone agent or as part of a multi-agent system, where other agents can invoke it to handle specific coding tasks.

The underlying LLM can be replaced in just two lines of code, allowing easy experimentation across different providers.

## ✨ Key Features

| ✅ Capability                       | 🔍 Description                                                                 |
|------------------------------------|--------------------------------------------------------------------------------|
| **Framework & LLM agnostic**       | Works with OpenAI, Anthropic, Gemini, Llama 3, Cohere, and LangChain/LangGraph. |
| **Unified memory**                 | Threaded state object supports persistent, structured memory across sessions.  |
| **Agent-to-Agent protocol (A2A)**  | Built-in message passing with orchestration rules for structured multi-agent workflows. |
| **Model Context Protocol (MCP)**   | Exposes tools as HTTP endpoints callable by models with full context support.  |
| **Reliable tool execution**        | Deterministic tool runner with error handling, retries, and call tracing.      |
| **Agentic RAG**                    | Optimized API call planning and caching to avoid redundant model/tool usage.   |
| **Custom agent hosting**           | Run any agent using any model on dedicated workers, no framework lock-in.      |
| **Interface layer**                | REST, Web UI, MCP, and webhook interfaces available by default.                |
| **Secrets management**             | Built-in vault for securely storing API keys and credentials.                  |
| **Low abstraction surface**        | Direct access to payloads, headers, memory, and execution logic.               |
| **Security model**                 | Sandboxed FS, path whitelisting, no shell access, and auditable write ops.     |
---

## 🏗 Architecture (10 sec glance)
At a high level, the Coding Agent acts as an intermediary between your chosen LLM and a secure coding environment, and it can be orchestrated by other agents:


```
┌───────────────┐         ┌──────────────┐         ┌────────────────────┐
│ Any other     │         │  coding_agent│─Native─►│   Any LLM backend  │
│ agent (A2A)   ├─A2A────►│              │         └────────────────────┘
└───────────────┘         └──────────────┘
                                 │  Model Context Protocol
                                 ▼
                          ┌─────────────────────────┐
                          │  xpander.ai connectors  │───▶ Any REST / gRPC API
                          └─────────────────────────┘
                                 │  sandboxed FS
                                 ▼
                          ┌─────────────────────────┐
                          │  Secure container       │
                          └─────────────────────────┘
```



## Installation

> **Prerequisites**  
> * Python ≥ 3.10 (tested on 3.10 & 3.11)  
> * Node ≥ 18 (for `xpander-cli`)  
> * Git ≥ 2.34  
> * AWS CLI config **or** access keys _(only if you use Bedrock tools)_

```bash
git clone https://github.com/xpander-ai/coding-agent.git
cd coding-agent

# Install Python dependencies (use a virtualenv/conda for isolation)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install xpander CLI for agent scaffolding & deployment
npm install -g xpander-cli
```
⚡ Quick start

Once installed, you can scaffold a new Coding Agent and start using it in just a few steps:


### 1 · Authenticate with xpander: Log in to your xpander.ai account (opens a browser for authentication):

```bash
xpander login          # opens browser‑based auth
```

### 2 · Scaffold a new agent: Create a new agent configuration using the CLI wizard (this will generate a local agent directory under ./agents/<your-agent-name>):

```bash
xpander agent new      # interactive wizard → creates ./agents/<slug>
```

### 3 · Configure your environment: Create a .env file in the project root (or update it if generated) with the required keys and settings:

```dotenv
# AWS credentials (only if using Amazon Bedrock)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...          # if using STS
AWS_REGION=us-west-2           # or your region

# xpander API key
XPANDER_API_KEY=...

# Coding Agent runtime settings
MAX_STEPS_SOFT_LIMIT=40
MAX_STEPS_HARD_LIMIT=60
MODEL_ID=us.anthropic.claude-3-7-sonnet-20250219-v1:0
```

### 4 · Run the agent locally: Start an interactive chat session with your new Coding Agent:

```bash
python main.py
```
You can now converse with the agent in your terminal. Type your requests (e.g. "Create a new Python file that prints 'Hello World'") and watch the agent autonomously write code, modify files, and commit changes based on your instructions. Use quit() or q to exit the session.




## 🖥  One‑Prompt Demos
You can also interact with the Coding Agent programmatically using the xpander SDK. Below are simple examples (in Python) using two different LLM providers. Just replace YOUR_API_KEY and YOUR_AGENT_ID with your xpander API key and an agent ID (from the agent you scaffolded or one configured in the xpander platform):

<details>
<summary>Amazon Bedrock (SDK async)</summary>

```python
import asyncio
from coding_agent import CodingAgent
from xpander_sdk import LLMProvider, XpanderClient

async def main() -> None:
    client = XpanderClient(api_key="YOUR_API_KEY")
    agent_cfg = await client.agents.get(agent_id="YOUR_AGENT_ID")

    agent = CodingAgent(agent=agent_cfg, llm_provider=LLMProvider.AMAZON_BEDROCK)
    thread = agent.chat(
        "Clone https://github.com/xpander-ai/docs.git and add a 'Getting Started' tutorial."
    )
    agent.chat("Push the change on a new branch called getting-started", thread)

asyncio.run(main())
```
</details>

<details>
<summary>OpenAI (SDK async)</summary>

```python
import asyncio
from coding_agent import CodingAgent
from xpander_sdk import LLMProvider, XpanderClient

async def main() -> None:
    client = XpanderClient(api_key="YOUR_API_KEY")
    agent_cfg = await client.agents.get(agent_id="YOUR_AGENT_ID")

    agent = CodingAgent(agent=agent_cfg, llm_provider=LLMProvider.OPEN_AI)
    thread = agent.chat(
        "Clone https://github.com/xpander-ai/docs.git and add a 'Getting Started' tutorial."
    )
    agent.chat("Push the change on a new branch called getting-started", thread)

asyncio.run(main())
```
</details>



## 🔌 Built‑in tools
Coding Agent comes with a suite of built-in tools to perform common development tasks in its sandbox:


| Tool | What it does |
|------|--------------|
| `git_clone` | Shallow‑clone a repo into the sandbox |
| `describe_folders_and_files` | Visual tree preview |
| `read_file` / `edit_file` / `new_file` | Safe file ops (no path traversal) |
| `commit` | Commit & push to **new** branch |
| `run_tests` | Execute tests inside sandbox |
| `call_endpoint` | Invoke any MCP‑described REST/gRPC endpoint |

These tools enable the agent to navigate repositories, make targeted code changes, and integrate with external services, all under controlled conditions. You can extend the agent with additional tools or endpoints as needed.




## 🧠 Memory & Orchestration


* **Threads** – Each conversation or task runs in a threaded state (essentially a JSON state machine). This is like an ongoing chat history that you can inspect or replay, ensuring the agent maintains context over multiple prompts.
* **Agent Graph** – A declarative directed acyclic graph (DAG) defines which tools or steps can run at which stage. This ensures the agent only executes allowed actions in a controlled sequence, providing reliability and compliance by default.


# Roadmap

- [ ] OpenAI Codex integration: Add OpenAI’s Codex as a coding tool for even smarter code completion.
- [ ] More LLM providers: Expand support to additional LLMs (e.g. Azure OpenAI, local models, etc.).
- [ ] Automated evals: Incorporate evaluation suites to benchmark agent performance on coding tasks.

We’re continuously improving Coding Agent. Feel free to suggest features or vote on existing ideas in the issues!

# Contributing

Contributions are welcome! If you’d like to report a bug or propose a new feature, please open an issue. Pull requests are gladly accepted – check out the code and feel free to improve it. For major changes, it’s best to discuss via an issue first to ensure alignment with the project goals. Join our growing community on Discord and Slack to ask questions, share ideas, and collaborate with other developers and researchers building with xpander.ai agents.

## 📜 License

This project is licensed under the MIT License. © 2025 Xpander Inc. Feel free to use, modify, and distribute this codebase in accordance with the license terms.