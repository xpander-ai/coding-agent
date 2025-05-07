# 🚀 Coding Agent

<div align="center">

## <strong>Build, test, and deploy better AI agents — framework-agnostic, LLM-agnostic, and supercharged by <a href="https://xpander.ai" target="_blank">xpander.ai</a></strong>

<div align="center">

![version](https://img.shields.io/badge/version-1.0.0-blue)
![license](https://img.shields.io/badge/license-MIT-green)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/xpander-ai/agent-coding/pulls)
[![Discord](https://img.shields.io/badge/Discord-Join%20our%20community-7289DA)](https://discord.gg/CUcp4WWh5g)
[![Slack](https://img.shields.io/badge/Join%20our%20Slack%20community-Click%20here-4A154B)](https://join.slack.com/t/xpandercommunity/shared_invite/zt-2mt2xkxkz-omM7f~_h2jcuzFudrYtZQQ)

<br>

<img src="images/coding-agent.png" alt="High‑level architecture diagram for Coding Agent" width="600">

</div>

---

## Why Coding Agent?

| ✅ Capability | 🚀 What it means for you |
|--------------|--------------------------|
| **Framework & LLM agnostic** | Speak directly to OpenAI, Anthropic, Gemini, Llama 3, Cohere… or wrap LangChain/LangGraph—your call. |
| **MCP‑ready tooling** | Turn any HTTP endpoint into a function call via the open **Model Context Protocol**—models can act on real systems instantly. |
| **Agent‑2‑Agent (A2A)** | Compose swarms of specialists that coordinate through xpander.ai’s Agent Graph—delegation, parallelism, retries, done. |
| **Threaded memory** | Every session is a state machine: persistent, inspectable, replayable. |
| **Minimal abstractions** | “Thin” on purpose: you keep full control of payloads, auth, and error handling. |
| **Security by design** | Per‑thread sandboxed FS, strict path‑whitelisting, no arbitrary shell, audited commits. |

---

## 🏗 Architecture (10 sec glance)

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

---

## ⚡ Quick start

> **Pre‑reqs**  
> * Python ≥ 3.10 (tested on 3.10 & 3.11)  
> * Node ≥ 18 (for `xpander-cli`)  
> * Git ≥ 2.34  
> * AWS CLI config **or** access keys _(only if you use Bedrock tools)_

```bash
git clone https://github.com/xpander-ai/agent-coding.git
cd agent-coding

# Install Python deps (virtualenv/conda recommended)
pip install -r requirements.txt

# Install CLI for agent scaffolding & deployment
npm install -g xpander-cli
```

### 1 · Authenticate once

```bash
xpander login          # opens browser‑based auth
```

### 2 · Scaffold a new agent

```bash
xpander agent new      # interactive wizard → creates ./agents/<slug>
```

### 3 · Configure `.env`

```dotenv
# AWS (optional – only for Bedrock)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...          # if using STS
AWS_REGION=us-west-2           # or your region

# xpander
XPANDER_API_KEY=...

# Coding Agent runtime
MAX_STEPS_SOFT_LIMIT=40
MAX_STEPS_HARD_LIMIT=60
MODEL_ID=us.anthropic.claude-3-7-sonnet-20250219-v1:0
```

### 4 · Chat locally

```bash
python main.py
```

---

## 🖥  One‑Prompt Demos

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

---

## 🔌 Built‑in tools

| Tool | What it does |
|------|--------------|
| `git_clone` | Shallow‑clone a repo into the sandbox |
| `describe_folders_and_files` | Visual tree preview |
| `read_file` / `edit_file` / `new_file` | Safe file ops (no path traversal) |
| `commit` | Commit & push to **new** branch |
| `run_tests` | Execute tests inside sandbox |
| `call_endpoint` | Invoke any MCP‑described REST/gRPC endpoint |

---

## 🧠 Memory & Orchestration

* **Threads** – each chat is a JSON state machine (= GPT “history” you can inspect & replay).  
* **Agent Graph** – declarative DAG that whitelists which tools run when → reliability & compliance by default.

---

## 📚 Further reading

| Guide | TL;DR |
|-------|-------|
| **[Quick‑start](https://docs.xpander.ai/docs/01-get-started/01-index)** | First 10 min with xpander.ai |
| **[Agent‑2‑Agent Graph](https://docs.xpander.ai/docs/02-agent-builder/06-multi-agent-teams)** | Compose multi‑agent workflows |

---

## 🛡 Security model (short version)

1. **Per‑thread sandbox** – each run gets its own isolated filesystem.  
2. **Path whitelists** – tools cannot touch paths outside the sandbox.  
3. **No arbitrary shell** – only curated sub‑processes with resource limits.  
4. **Audit log** – every tool call, request & response are persisted immutably.

_For deeper details, see `docs/security.md`._

---

## 📜 License

MIT © 2025 Xpander Inc.
