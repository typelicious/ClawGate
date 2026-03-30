# Claude Desktop Feasibility

## Purpose

This note answers one narrow product question:

Should `fusionAIze Gate` prioritize a dedicated Claude Desktop parity line immediately after the current bridge hardening work?

The answer depends less on Gate's internal bridge quality and more on what Claude Desktop itself currently exposes for local gateway integration.

## Current evidence

### What is clearly supported today

Claude Code has explicit official gateway documentation.

Anthropic's Claude Code docs currently describe:

- gateway support via the Anthropic Messages format
- `ANTHROPIC_BASE_URL` for a unified gateway endpoint
- required forwarding of `anthropic-version` and `anthropic-beta`
- `POST /v1/messages` and `POST /v1/messages/count_tokens` as the required Anthropic-format paths

Source:

- [Claude Code LLM gateway configuration](https://code.claude.com/docs/en/llm-gateway)

This makes Claude Code parity a straightforward engineering problem for Gate.

### What is not equally clear today

For Claude Desktop, the currently visible official documentation strongly emphasizes:

- the desktop app itself
- desktop extensions
- MCP/local MCP
- enterprise deployment and policy controls
- Cowork / Claude Code inside Desktop

But it does not currently provide equally explicit public documentation for a general-purpose local Anthropic gateway override path comparable to Claude Code's `ANTHROPIC_BASE_URL` flow.

Relevant sources reviewed:

- [Installing Claude Desktop](https://support.claude.com/en/articles/10065433-installing-claude-for-desktop)
- [Deploy Claude Desktop for macOS](https://support.claude.com/en/articles/12611117-deploy-claude-desktop-for-macos)
- [Enterprise Configuration](https://support.claude.com/ru/articles/12622667)
- [Getting started with MCP on Claude Desktop](https://support.claude.com/en/articles/10949351-getting-started-with-model-context-protocol-mcp-on-claude-for-desktop)

That means Desktop parity is not blocked by Gate alone. It is partly blocked by whether Claude Desktop currently exposes a stable, supported route to point its model traffic at a local Anthropic-compatible gateway.

## Practical interpretation

There are three distinct desktop outcomes:

### 1. Strong feasibility

Claude Desktop exposes a stable, supported endpoint-override path for model traffic.

If this is confirmed, Desktop parity becomes a normal Gate engineering line:

- bridge compatibility
- session behavior
- validation and release-readiness

### 2. Partial feasibility

Claude Desktop exposes only a limited or version-sensitive override path.

In that case, Desktop parity is still worth pursuing, but it should be framed as:

- supported for validated versions and flows
- not universal across all Desktop builds yet

### 3. Weak feasibility

Claude Desktop does not expose a reliable override path for its core model traffic, and only supports MCP or desktop-extension integration.

In that case, "Claude Desktop parity" in the same sense as Claude Code parity is not a normal bridge problem. It becomes either:

- an MCP/extension strategy, or
- a wait-for-client-capability strategy

## What this means for Gate

### Good news

Gate's current architecture is still the right one.

If Desktop endpoint override is available, Gate is well positioned:

- Anthropic-compatible bridge already exists
- routing, fallback, and quota-group handling already stay in the Gate core
- Claude-oriented aliases already exist
- operator validation scripts already exist

### Current risk

The risk is not "can Gate map requests?".

The risk is:

- can Claude Desktop actually be pointed at Gate in a stable, supported way?

If the answer is not yet clearly yes, then a full Desktop parity release line would be premature.

## Recommendation

### Product decision

Treat Claude Desktop parity as strategically important, but evidence-gated.

That means:

- keep it explicitly in the roadmap
- do not promise it on the same confidence level as Claude Code parity yet
- run a short feasibility validation round before giving it the next release slot

### Recommended next step

Run a focused Claude Desktop validation round before choosing between:

- `v1.15.x`: Claude Desktop parity
- `v1.15.x`: adaptive orchestration trust

## Validation checklist

This is the minimum evidence needed to promote Desktop parity into the next release line.

### A. Endpoint override reality

Confirm whether the current Claude Desktop build supports directing model traffic to a local Anthropic-compatible gateway in a stable way.

Need answers to:

- is there an officially documented endpoint override path?
- is it environment-based, settings-based, policy-based, or unsupported?
- is it stable across current macOS and Windows builds?

### B. Minimal local happy path

If override exists, validate:

1. Claude Desktop reaches local Gate
2. Gate receives Anthropic-shaped traffic
3. non-streaming bridge flow succeeds
4. headers and model aliasing behave as expected

### C. Real workflow viability

Validate whether the desktop workflow actually uses features that matter for parity:

- streaming
- tool-style blocks
- long-lived sessions
- any desktop-specific request/response behavior that differs from Claude Code

### D. Operator viability

Confirm that the setup is something an operator could realistically maintain:

- configuration path is understandable
- local validation is repeatable
- failures are diagnosable
- the setup is not dependent on one undocumented trick

## Go / no-go rule

Promote Claude Desktop parity into the next release line only if:

1. a stable endpoint-override path is confirmed, and
2. at least one real desktop workflow succeeds reproducibly against local Gate

Otherwise:

- keep Desktop parity in the roadmap
- keep it strategically important
- but take adaptive orchestration trust first and revisit Desktop when client support is clearer
