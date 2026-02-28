# ClawGate

Local OpenAI-compatible LLM router for OpenClaw.

ClawGate runs on the Nexus box as a small FastAPI/Uvicorn service and exposes an OpenAI-compatible API under:

- Base URL: `http://127.0.0.1:8090/v1`
- Health: `http://127.0.0.1:8090/health`
- Models: `http://127.0.0.1:8090/v1/models`

It is used as a **local proxy** so OpenClaw can route all LLM calls through a single endpoint (`clawgate/auto`), while ClawGate decides which upstream provider/model to use.

---

## Quickstart (Nexus)

### Status
```bash
clawgate-status
clawgate-health
```

### Logs
```bash
clawgate-logs
```

### Restart
```bash
clawgate-restart
```

### Update (pull repo + restart)
```bash
clawgate-update
```

---

## Systemd service

- Unit: `/etc/systemd/system/clawgate.service`
- User: `clawgate`
- Listen: `127.0.0.1:8090`
- DB path: `/var/lib/clawgate/clawgate.db` (kept **out of the repo**)

---

## OpenClaw integration

OpenClaw config points to ClawGate as a provider:

- Provider baseUrl: `http://127.0.0.1:8090/v1`
- Default model: `clawgate/auto`

Example model refs inside OpenClaw:
- `clawgate/auto`
- `clawgate/deepseek-chat`
- `clawgate/deepseek-reasoner`
- `clawgate/gemini-flash-lite`
- `clawgate/gemini-flash`
- `clawgate/openrouter-fallback`

---

## Repo safety (important)

This repo must never contain secrets or runtime artifacts.

Blocked:
- `.ssh/`
- `*.db*`
- `*.sqlite*`
- `*.log`

Enforced via:
- `.gitignore`
- GitHub Actions workflow: `.github/workflows/repo-safety.yml`
