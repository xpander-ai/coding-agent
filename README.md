# 🚀 Coding Agent

<div align="center">

## <strong>Build, test, and deploy better AI agents — framework-agnostic, LLM-agnostic, and supercharged by <a href="https://xpander.ai" target="_blank">xpander.ai</a></strong>

<br>

<img src="https://img.shields.io/badge/version-1.0.0-blue" alt="Version">
<img src="https://img.shields.io/badge/license-MIT-green" alt="License">
<a href="https://github.com/xpander-ai/agent-coding/pulls"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
<a href="https://discord.gg/CUcp4WWh5g"><img src="https://img.shields.io/badge/Discord-Join%20our%20community-7289DA" alt="Discord"></a>
<a href="https://join.slack.com/t/xpandercommunity/shared_invite/zt-2mt2xkxkz-omM7f~_h2jcuzFudrYtZQQ" target="_blank">
  <img src="https://img.shields.io/badge/Join%20Our%20Slack%20Community-Click%20Here-4A154B" alt="Join Our Slack Community">
</a>
<br><br>

<img src="images/coding-agent.png" alt="Coding Agent diagram" width="600">

</div>

---

The **Coding Agent** is a lightweight, universal abstraction layer for any LLM or AI framework.

It empowers you to:

- Operate seamlessly across Bedrock, OpenAI, Anthropic, and more  
- Maintain persistent, threaded memory across executions  
- Orchestrate multi-agent flows via A2A (Agent-to-Agent) graph control  
- Run inside Xpander’s managed runtime or your own environment  

**Example use case:**  
Deploy a Bedrock dev agent alongside an OpenAI Codex agent, orchestrate them with a manager agent, and generate production-grade code.

> **xpander.ai makes reliable, scalable agent ecosystems effortless.**

## ⚡ Core Differentiators

| ✅ Capability | 🚀 Detail |
|---------------|-----------|
| **Framework & LLM Agnostic** | Speaks raw OpenAI, Anthropic, Gemini, Llama 3, Cohere, etc.—or plug in LangGraph/LangChain if you like. No opaque wrappers. |
| **MCP‑Ready Tooling** | Any HTTP endpoint becomes a function call via the open **Model Context Protocol**, so models can act on real systems instantly. |
| **Agent‑2‑Agent (A2A)** | Compose swarms of specialists that coordinate through xpander.ai's Agent Graph—delegation, parallelism, retries, done. |
| **Threaded Memory** | Every conversation is a state machine: persistent, inspectable, replayable. |
| **Minimal Abstractions** | We stay "thin": you keep full control of payloads, auth, and error handling. |
| **Security by Design** | Per‑thread sandboxed FS, strict path‑whitelisting, no arbitrary shell, audited commits. |

---

## 🏗️ High‑Level Architecture

```
┌───────────────┐         ┌──────────────┐         ┌────────────────────┐
│ Any other     │         │ coding_agent ├─Native─►│  Any LLM provider  │
│ Agent         ├─--A2A──►│              │         └────────────────────┘
└───────────────┘         └──────────────┘
                                 │
                                 │ function‑calls (MCP)
                                 ▼
                          ┌─────────────────────────┐
                          │  xpander.ai connectors  │───▶ Any Rest API
                          └─────────────────────────┘
                                 │
                                 ▼
                          ┌─────────────────────────┐
                          │  Secure sandbox (FS)    │
                          └─────────────────────────┘
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/xpander-ai/agent-coding.git
cd agent-coding
pip install -r requirements.txt

cp .env.example .env   # add your OpenAI/Anthropic/Gemini keys + xpander creds
xpander login
xpander agent new
python main.py         # launch the agent
```

### One‑Prompt Demo

```python
from coding_agent import CodingAgent

agent = CodingAgent()
thread = agent.chat(
    "Clone https://github.com/xpander-ai/docs.git and add a 'Getting Started' tutorial"
)
agent.chat("Push the change on a new branch called getting-started", thread)
```

---

## 🔌 Built‑in Tools

| Tool | Purpose |
|------|---------|
| `git_clone` | Shallow‑clone repo into the sandbox |
| `describe_folders_and_files` | Visual tree preview |
| `read_file`, `edit_file`, `new_file` | Safe file operations |
| `commit` | Commit & push to a new branch |
| `run_tests` | Execute project tests inside the sandbox |
| `call_endpoint` | Invoke any MCP‑described REST/gRPC endpoint |

---

## 🧠 Memory & Orchestration

* **Threads** – each session keeps its own message graph (like chat‑GPT "history" but inspectable JSON).  
* **Agent Graph** – define DAGs that gate which functions can be called and in what order. Enforces reliability and compliance.

---

## 📚 Further Reading

* [Quick‑start guide](https://docs.xpander.ai/docs/01-get-started/01-index)
* [Agent‑2‑Agent Graph](https://docs.xpander.ai/docs/02-agent-builder/06-multi-agent-teams)

---

## 📜 License

MIT © 
2025 Xpander Inc.
