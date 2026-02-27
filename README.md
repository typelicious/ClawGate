# 🚪 ClawGate

**Smart LLM routing proxy for OpenClaw.** Routes every request to the cheapest model that can handle it.

```
"status check"        → Gemini Flash-Lite  $0.08/M   heartbeat
"prove this theorem"  → DeepSeek Reasoner  $0.55/M   reasoning
"search for files"    → DeepSeek Chat      $0.27/M   tool use
"was ist ein Monad?"  → Gemini Flash-Lite  $0.08/M   simple query
```

## How It Works

```
OpenClaw ──► http://localhost:8090/v1/chat/completions
                         │
          Layer 1: Static Rules          (<0.01ms)
          heartbeat, explicit /model, subagent headers
                         │
          Layer 2: Heuristic Scoring     (<0.1ms)
          keyword-weighted, user messages only
                         │
          Layer 3: LLM Classifier        (optional, ~500ms)
          cheapest model classifies the task
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
   DeepSeek Chat   DeepSeek R1    Gemini Flash-Lite
    (default)      (reasoning)     (simple/heartbeat)
         │               │               │
         └───── Fallback: OpenRouter ─────┘
```

Key insight (from ClawRouter): **Only user messages are scored, never the system prompt.** OpenClaw's system prompt is large and keyword-rich — scoring it inflates every request to the reasoning tier.

## Features

- **3-layer routing engine** — static rules → heuristic scoring → optional LLM classifier
- **Prompt cache tracking** — monitors DeepSeek/Gemini cache hit rates, uses cache-aware cost calculation
- **Cost tracking** — per-request cost with cache-aware pricing ($0.014/M for cache hits vs $0.14/M)
- **Health monitoring** — auto-detects unhealthy providers, falls through to next in chain
- **Web dashboard** — live stats at `/dashboard`, auto-refresh
- **CLI stats** — `clawgate-stats` / `python -m clawgate.cli`
- **OpenClaw Skill** — native `/clawgate` slash command for stats, health, routing dry-run
- **Multilingual routing** — keywords in DE, EN, ZH, JA, RU

## Quick Start

```bash
tar xzf clawgate.tar.gz && cd clawgate
cp .env.example .env     # API keys eintragen
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn clawgate.main:app --host 127.0.0.1 --port 8090
```

## OpenClaw Integration

```jsonc
// In ~/.openclaw/openclaw.json
{
  "models": {
    "providers": {
      "clawgate": {
        "baseUrl": "http://127.0.0.1:8090/v1",
        "apiKey": "local",
        "api": "openai-completions",
        "models": [
          { "id": "auto", "name": "ClawGate Auto-Router" }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": { "primary": "clawgate/auto" }
    }
  }
}
```

## Install Skill

```bash
cp -r skills/clawgate ~/.openclaw/skills/
# Then use: /clawgate stats, /clawgate health, /clawgate daily
```

## Prompt Caching

DeepSeek and Gemini cache repeated prefixes automatically. ClawGate tracks this:

| Provider | Cache Hit Price | Normal Price | Savings |
|---|---|---|---|
| DeepSeek | $0.014/M | $0.14/M | 90% |
| Gemini Flash | 0.25x input | 1x input | 75% |

To maximize hits: keep system prompts stable, push variable content to end of messages.

## CLI

```bash
python -m clawgate.cli              # Overview
python -m clawgate.cli --daily      # Daily cost + projection
python -m clawgate.cli --recent 20  # Last 20 requests
python -m clawgate.cli --json       # Pipe to jq
```

## Dashboard

Open `http://localhost:8090/dashboard` for live stats with provider breakdown, routing rules, cache hit rates, and recent requests.

## Systemd

```bash
sudo cp clawgate.service /etc/systemd/system/
sudo systemctl enable --now clawgate
```

## License

MIT
