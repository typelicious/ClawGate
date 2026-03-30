# Implementation Plan

## Scope

This document turns the current roadmap into the next concrete release lines.

It is intentionally biased toward the biggest product levers:

- Claude-native daily usability
- routing trust and operator explainability
- adaptive behavior under real pressure

It is not a parking lot for every possible feature.

## Principles

- keep `fusionAIze Gate` as the gateway, not a second platform
- prefer one coherent release theme over many mini-features
- do protocol hardening before bigger marketing claims
- do routing explainability before stronger live adaptation
- keep `v2.x` work behind clean product boundaries

## Release Sequence

### `v1.14.x` - Claude-native daily-use hardening

Goal:

- move the Anthropic bridge from early-adopter-safe to comfortable for everyday Claude-native use

Why this matters first:

- it is the biggest remaining daily workflow gap
- it unlocks real Claude Code testing without client reshaping
- it sharpens the product story around one local endpoint for both OpenAI-native and Claude-native clients

Target slices:

1. SSE streaming parity for `/v1/messages`
2. stronger Anthropic block compatibility
   - richer `tool_use`
   - richer `tool_result`
   - clearer unsupported block handling
3. stronger client-facing parity behaviors
   - stop reasons
   - version/beta handling
   - error mapping consistency
4. expanded client-near validation
   - Claude Code workflow validation
   - Claude Desktop workflow notes and smoke steps

Success bar:

- Claude Code can be pointed at local Gate and used for normal iterative coding flows with acceptable behavior
- streaming and tool-oriented workflows do not immediately fall off the happy path

Deliberately not required:

- exact provider-side token counting
- full parity claims across every Anthropic client feature

### `v1.15.x` - Adaptive orchestration trust

Goal:

- make route selection understandable and trustworthy enough that operators rely on it instead of overriding it by hand

Why it is second:

- the routing engine already does more than the docs and surfaces make obvious
- the biggest leverage now is visibility, structured lane semantics, and safer aggregator handling

Target slices:

1. canonical lane visibility
   - route preview speaks in lanes first, transports second
   - dashboard and provider views summarize lane families clearly
2. route-aware aggregator handling
   - clearer mirror/same-lane semantics
   - quota-isolated vs quota-coupled route handling
   - stronger aggregator readiness language
3. benchmark and cost clusters
   - structured cluster metadata
   - freshness/review age
   - operator-visible inputs
4. operator explainability
   - why lane won
   - why route won
   - why same-lane mirror was skipped
   - why downgrade happened

Success bar:

- operators can look at a route decision and understand it without reading source code
- aggregator handling feels intentional instead of “maybe a fallback”

### `v1.16.x` - Live adaptation under pressure

Goal:

- adapt routing under quota, latency, and failure pressure without becoming opaque

Why it is third:

- dynamic adaptation is only worth shipping once lane and route semantics are already trusted

Target slices:

1. live pressure scoring
   - quota pressure
   - latency inflation
   - failure pressure
   - fallback pressure
2. same-lane-first reactions
   - mirror route before weaker cluster
3. operator controls
   - conservative defaults
   - visible adaptation state
   - clear cooldown and recovery behavior
4. richer traces
   - actual attempted route order
   - same-lane fallback vs cluster degrade

Success bar:

- route switching under pressure is visible, understandable, and mostly unsurprising to operators

## Deferred Lines

### Exact provider-side token counting

Recommendation:

- defer until after `v1.14.x`
- implement first for the providers that expose reliable count endpoints or deterministic usage feedback
- keep the current bridge estimate until a route-specific exact path exists

### Virtual keys and per-key budgets

Recommendation:

- likely next after the `v1.16.x` trust line if operator-scale controls become the top demand
- this is the prerequisite for later team/org budget hierarchy

### OTEL trace-context forwarding

Recommendation:

- can move earlier than other `v2.x` items
- good candidate for a narrower cross-cutting observability release if demand is high

### Team and org budget hierarchy

Recommendation:

- defer until virtual keys and spend ledger are genuinely stable

### Grid shared-state coordination

Recommendation:

- design the contract early
- implement later
- keep Gate itself free of hard Redis/Postgres coupling

### Semantic caching

Recommendation:

- do not start before exact caching plus usage evidence

## Concrete Next Actions

### Immediate

1. merge docs cleanup and roadmap reset
2. open a focused `v1.14.x` feature branch for bridge streaming and Claude-native parity hardening
3. define the `v1.14.x` validation matrix before the implementation expands

### `v1.14.x` validation matrix

Minimum:

- `POST /v1/messages` non-streaming
- `POST /v1/messages` streaming
- `tool_use` / `tool_result`
- `count_tokens`
- version/beta header handling
- one real Claude Code local workflow

Stretch:

- Claude Desktop local override flow
- route fallback under Anthropic quota pressure

## Open Questions

- which Claude Code workflows are still meaningfully blocked after streaming lands?
- which bridge gaps are protocol gaps versus route-selection gaps?
- which exact providers should support exact token counting first?
- do operators want OTEL before virtual keys, or vice versa?

## Anti-Goals

- no second gateway runtime for Anthropic traffic
- no opaque routing magic that cannot be explained later
- no multi-instance infrastructure inside Gate just to claim clustering
- no semantic-cache detour before the simpler operator wins land
