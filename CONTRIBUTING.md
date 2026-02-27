# Contributing to ClawGate

Danke für dein Interesse! Beiträge sind willkommen.

## Development Setup

```bash
git clone https://github.com/langenetwork/clawgate.git
cd clawgate
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v
```

Tests mocken `httpx` und brauchen keine API-Keys.

## Linting

```bash
ruff check .
ruff format .
```

## Adding a New Provider

1. Add provider config to `config.yaml` with `pricing` block
2. If the API isn't OpenAI-compatible, add a backend method in `providers.py`
3. Add routing rules in `config.yaml` (static or heuristic)
4. Add tests in `tests/test_routing.py`

## Adding Routing Rules

Heuristic rules in `config.yaml` support:
- `message_keywords` — keyword matching (user messages only!)
- `has_tools` — tool call detection
- `estimated_tokens` — token count thresholds
- `fallthrough` — catch-all default

Important: Never score the system prompt for keywords. See ClawRouter's insight on this.

## Submitting Changes

1. Fork the repo
2. Create a feature branch
3. Add tests for new functionality
4. Ensure `pytest` and `ruff check` pass
5. Open a PR with a clear description

## ClawHub Skill Updates

The skill lives in `skills/clawgate/SKILL.md`. If you update slash commands or add new endpoints, update the skill too.
