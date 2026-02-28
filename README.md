# ClawGate

[![repo-safety](https://github.com/typelicious/ClawGate/actions/workflows/repo-safety.yml/badge.svg)](https://github.com/typelicious/ClawGate/actions/workflows/repo-safety.yml)
[![CI](https://github.com/typelicious/ClawGate/actions/workflows/ci.yml/badge.svg)](https://github.com/typelicious/ClawGate/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](./pyproject.toml)

ClawGate is an openai-compatible router and local proxy for OpenClaw: OpenClaw sends every request to one local endpoint, and ClawGate chooses the upstream provider and model.

This repo is intentionally optimized for search and clarity around these keywords: openai-compatible, router, proxy, openclaw, llm gateway, multi-provider.

## Why It Matters

- One local endpoint for OpenClaw: `http://127.0.0.1:8090/v1`
- Cost control through rule-based routing across multiple providers
- Local failover chain when a chosen provider fails
- OpenAI-compatible interface for easy OpenClaw integration
- Operational visibility via health, stats, recent requests, and a small dashboard

## Common Use Cases

- OpenClaw multi-model routing without teaching OpenClaw every upstream model detail
- Local proxy on a Nexus box that keeps upstream API keys on the server
- Cost control by sending simple prompts to cheaper models and heavier tasks to reasoning models
- Failover from one provider to the next configured provider in the fallback chain

## Quickstart (Nexus)

This assumes a Linux host such as `nexus-core`, a checkout at `/opt/clawgate`, and systemd.

```bash
cd /opt/clawgate
cp .env.example .env
$EDITOR .env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./scripts/clawgate-install
clawgate-health
```

If you do not want the helper symlinks yet, the direct equivalents are:

```bash
cd /opt/clawgate
sudo install -m 644 clawgate.service /etc/systemd/system/clawgate.service
sudo systemctl daemon-reload
sudo systemctl enable --now clawgate.service
curl -fsS http://127.0.0.1:8090/health
```

## Architecture

```text
OpenClaw
  |
  v
http://127.0.0.1:8090/v1/chat/completions
  |
  +--> Layer 1: static rules
  +--> Layer 2: heuristic rules
  +--> Layer 3: optional LLM classifier (disabled by default)
  |
  +--> selected provider
         |- deepseek-chat
         |- deepseek-reasoner
         |- gemini-flash-lite
         |- gemini-flash
         `- openrouter-fallback
```

## Implemented HTTP Endpoints

These are the routes implemented today in [clawgate/main.py](./clawgate/main.py):

### OpenAI-Compatible Endpoints

- `GET /v1/models`
- `POST /v1/chat/completions`

There are no other `v1/*` endpoints in the current codebase.

### Operational Endpoints

- `GET /health`
- `GET /api/stats`
- `GET /api/recent?limit=50`
- `GET /dashboard`

### Copy/Paste Examples

```bash
curl -fsS http://127.0.0.1:8090/health
curl -fsS http://127.0.0.1:8090/v1/models
curl -fsS http://127.0.0.1:8090/api/stats
curl -fsS 'http://127.0.0.1:8090/api/recent?limit=10'
curl -fsS http://127.0.0.1:8090/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Was ist ein Monad?"}],
    "max_tokens": 64
  }'
```

## How Routing Works

ClawGate routes requests in three layers:

1. Static rules
2. Heuristic rules
3. Optional LLM classifier

Important implementation detail: keyword scoring only inspects user messages, not the system prompt. This avoids misrouting because OpenClaw system prompts are usually large and keyword-heavy.

The default `config.yaml` routes to these configured providers:

- `deepseek-chat`
- `deepseek-reasoner`
- `gemini-flash-lite`
- `gemini-flash`
- `openrouter-fallback`

The default fallback chain is:

```yaml
fallback_chain:
  - deepseek-chat
  - deepseek-reasoner
  - gemini-flash
  - openrouter-fallback
```

## Systemd Service

The unit file in this repo is [clawgate.service](./clawgate.service). The deployed unit path is:

```text
/etc/systemd/system/clawgate.service
```

### Key Environment Variables

These are the environment variables currently supported by the app and config:

- `DEEPSEEK_API_KEY`
- `GEMINI_API_KEY`
- `OPENROUTER_API_KEY`
- `DEEPSEEK_BASE_URL` (optional override)
- `GEMINI_BASE_URL` (optional override)
- `CLAWGATE_DB_PATH` (optional; defaults to `./clawgate.db`, the service sets `/var/lib/clawgate/clawgate.db`)

The unit also loads:

```text
/opt/clawgate/.env
```

### Hardening Highlights

These protections are present in the current unit file:

- `NoNewPrivileges=true`
- `ProtectSystem=strict`
- `ProtectHome=true`
- `ReadWritePaths=/var/lib/clawgate`
- `PrivateTmp=true`

That means the service is read-only across most of the filesystem and only needs write access to `/var/lib/clawgate` for the metrics database.

## Helper Scripts

All helper scripts live in [scripts](./scripts). Running `./scripts/clawgate-install` also creates symlinks in:

```text
/usr/local/bin
```

Installed commands:

- `clawgate-install`
- `clawgate-start`
- `clawgate-stop`
- `clawgate-restart`
- `clawgate-status`
- `clawgate-logs`
- `clawgate-health`
- `clawgate-update`
- `clawgate-uninstall`

### Real Command Examples

From the repo checkout:

```bash
./scripts/clawgate-install
./scripts/clawgate-status
./scripts/clawgate-health
./scripts/clawgate-update
```

After install creates symlinks:

```bash
clawgate-status
clawgate-logs
clawgate-restart
clawgate-health
```

What the helpers do today:

- `clawgate-install`: installs `/etc/systemd/system/clawgate.service`, creates `/var/lib/clawgate`, creates `/usr/local/bin/clawgate-*` symlinks, reloads systemd, enables and starts the service
- `clawgate-start|stop|restart|status|logs|health`: thin systemd or curl wrappers
- `clawgate-update`: runs `git fetch --all --prune`, `git reset --hard origin/main`, `git clean -fd`, refreshes the service unit, restarts, then health-checks with retries
- `clawgate-uninstall`: disables the service, removes the systemd unit, removes `/usr/local/bin/clawgate-*` symlinks

## Deploy Workflow (Nexus)

The repo already ships the intended Nexus update path in [scripts/clawgate-update](./scripts/clawgate-update):

```bash
cd /opt/clawgate
clawgate-update
```

Equivalent explicit steps:

```bash
cd /opt/clawgate
git fetch --all --prune
git reset --hard origin/main
git clean -fd
sudo install -m 644 clawgate.service /etc/systemd/system/clawgate.service
sudo systemctl daemon-reload
sudo systemctl restart clawgate.service
for attempt in 1 2 3 4 5; do
  curl -fsS -m 2 http://127.0.0.1:8090/health && break
  sleep 2
done
```

`git reset --hard` and `git clean -fd` are intentional here: this update flow is meant for a deployment checkout on Nexus, not for a development checkout with local edits.

## OpenClaw Integration

Point OpenClaw at ClawGate as a provider and make `clawgate/auto` the default model. The full example lives in [openclaw-integration.jsonc](./openclaw-integration.jsonc).

Minimal provider block:

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "clawgate": {
        "baseUrl": "http://127.0.0.1:8090/v1",
        "apiKey": "local",
        "auth": "api-key",
        "api": "openai-completions",
        "models": [
          { "id": "auto", "name": "ClawGate Auto-Router" }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "clawgate/auto",
        "fallbacks": []
      }
    }
  }
}
```

## Repo Safety

This repo includes the GitHub Action [repo-safety.yml](./.github/workflows/repo-safety.yml).

It blocks two classes of mistakes:

- forbidden artifacts currently tracked in the working tree
- forbidden artifacts anywhere in Git history

Blocked patterns:

- `.ssh/`
- `*.db*`
- `*.sqlite*`
- `*.log`

Why this exists: secrets and runtime artifacts are easy to commit by accident, hard to remove from history, noisy in code review, and risky in public or shared repos.

## FAQ / Troubleshooting

### `curl /health` fails

Check whether the service is up and listening:

```bash
clawgate-status
sudo ss -ltnp | grep -E '127\.0\.0\.1:8090\b' || true
```

### Port `8090` is already in use

Find the conflicting process:

```bash
sudo ss -ltnp | grep ':8090'
```

The service unit expects to own `127.0.0.1:8090`.

### The service starts but OpenClaw cannot use it

Verify OpenClaw points to:

```text
http://127.0.0.1:8090/v1
```

Also confirm the default model is `clawgate/auto`.

### `clawgate-update` discarded local changes

That is by design. The deploy helper uses `git reset --hard` and `git clean -fd` to keep `/opt/clawgate` identical to `origin/main`.

### The metrics database is missing

The service writes to:

```text
/var/lib/clawgate/clawgate.db
```

If needed, confirm the directory exists and the service user can write there:

```bash
sudo install -d -o clawgate -g clawgate -m 755 /var/lib/clawgate
```

### A provider is marked unhealthy after failures

Health state is tracked from request outcomes. Check recent service logs:

```bash
clawgate-logs
```

Then verify the relevant API key and upstream endpoint in `/opt/clawgate/.env`.

## Roadmap

- Add more tests around provider adapters and API responses
- Expand OpenClaw integration examples for more deployment variants
- Add more operational docs if the repo grows beyond a single README
- Consider more provider backends and more routing rules over time

## Assumptions

- The primary deployment target is a Linux host with systemd, such as a Nexus or mini-PC setup
- The deployment checkout lives at `/opt/clawgate`
- OpenClaw runs on the same host and reaches ClawGate via `127.0.0.1`
- This README documents what is implemented now; it intentionally avoids describing unimplemented endpoints or background jobs

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## Security

- Do not commit `.env`, keys, databases, sqlite files, or logs
- Use the `repo-safety` workflow and `.gitignore` as guardrails, not excuses
- If you need to rotate leaked credentials, rotate them upstream first and then remove them from local deploy files

## License

MIT. See [LICENSE](./LICENSE).
