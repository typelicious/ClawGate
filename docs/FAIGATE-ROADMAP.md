# fusionAIze Gate Roadmap

## Status

`v1.13.0` is shipped.

The current product shape is now clear:

- one local gateway
- one OpenAI-compatible surface plus an optional Anthropic-compatible bridge
- direct providers, aggregators, and local workers under one routing core
- operator-facing health, probe, catalog, and release tooling

The roadmap should now stay disciplined. The next releases should deepen routing trust and Claude-native compatibility, not sprawl into a second platform.

## Current Product Baseline

Already in place:

- canonical lane-aware routing foundations
- route-aware handling for direct, aggregator, wallet-router, and local-worker paths
- client profiles, routing modes, and request hooks
- provider-source catalog mirroring and local route visibility overlays
- quota-group-aware fallback guardrails for Anthropic-shaped traffic
- optional Anthropic bridge with `/v1/messages` and `/v1/messages/count_tokens`
- shell-native operator surfaces: doctor, provider probe, dashboard, quick setup

This means the roadmap no longer needs to ask whether Gate should become a multi-provider local gateway. It already is one.

## Release Direction

### `v1.14.x`: Claude-native daily-use hardening

This is the highest-leverage next line.

Primary goals:

- make the Anthropic bridge comfortable for real Claude Code and Claude Desktop workflows
- close the biggest protocol-parity gaps before expanding scope again
- keep the bridge opt-in and explicit while improving day-to-day reliability

Expected slices:

1. SSE streaming parity for `/v1/messages`
2. fuller Anthropic block compatibility beyond the current text plus basic tool flow
3. stronger Claude-client validation fixtures and operator troubleshooting
4. sharper error and stop-reason compatibility

Non-goals:

- exact provider-side token counting for every backend
- "full parity" marketing language before live client coverage proves it

### `v1.15.x`: adaptive orchestration trust

This is the next major routing-value line.

Primary goals:

- make canonical lanes more visible and more legible to operators
- tighten route-aware aggregator handling under real quota and latency pressure
- make benchmark and cost assumptions auditable and fresh enough to trust
- explain every meaningful routing decision in operator-facing terms

Expected slices:

1. canonical lane cards and route-family summaries in operator surfaces
2. route-aware aggregator handling with clearer quota isolation and mirror semantics
3. benchmark and cost clusters that are structured, reviewable, and freshness-aware
4. operator explainability for lane choice, same-lane fallback, and cluster downgrade

### `v1.16.x`: live adaptation under pressure

Only pursue this once `v1.15.x` makes the decision model trustworthy.

Primary goals:

- adapt route choice under quota, latency, and failure pressure
- keep same-lane substitutions ahead of weaker-cluster downgrades
- make live routing pressure visible enough that operators can trust it

Expected slices:

1. live route pressure and cooldown scoring
2. family- and lane-level adaptation signals
3. fallback pressure reporting in dashboard, route preview, and traces
4. conservative operator controls for adaptation posture

## Challenge The Backlog

This section is the reality check: what is already there, what is partially there, and what is actually worth the next release slots.

| Theme | Current reality | Biggest gap | Recommendation |
| --- | --- | --- | --- |
| Canonical model lanes | Already present in routing foundations and catalog surfaces | Too hidden in operator UX; not yet the default mental model | Double down in `v1.15.x`, not later |
| Route-aware aggregator handling | Partly present: route types, Kilo lanes, BLACKBOX handling, quota groups | Mirror semantics and quota isolation are still too implicit | Make this a first-class `v1.15.x` line |
| Benchmark and cost clusters | Present as curated metadata, but still coarse | Freshness, explainability, and structured ranking are not strong enough yet | Build reviewable cluster metadata in `v1.15.x` |
| Live adaptation under quota, latency, and failure pressure | Early adaptation exists, but still conservative | Needs stronger operator trust and clearer lane/route semantics first | Keep for `v1.16.x` after orchestration trust work |
| Operator explainability for major routing decisions | Partly present in traces and previews | Still not compact or decisive enough for day-2 operations | Make this a headline outcome of `v1.15.x` |
| Full Anthropic parity | Not there | Streaming and deeper block coverage are missing | Treat as staged parity, not one giant promise |
| Full Claude Code parity | Not there | Real client workflow coverage is still partial | Focus `v1.14.x` on practical daily-use parity |
| Full Claude Desktop parity | Not there | Client override paths and feature expectations vary | Keep as follow-on after `v1.14.x` Claude Code hardening |
| SSE streaming parity | Not shipped for the bridge yet | Missing bridge streaming path | Highest-priority bridge gap for `v1.14.x` |
| Exact provider-side token counting | Not shipped | Needs backend-aware counting per route or provider API support | Useful, but not a blocker for `v1.14.x`; likely `v1.15.x` or later |

## What Should Not Drive The Next Releases

Some ideas are valid, but they are not the best next lever.

### Full parity as a release slogan

Avoid release lines built around vague parity claims.

Better framing:

- `v1.14.x`: Claude-native daily-use hardening
- `v1.15.x`: adaptive orchestration trust
- `v1.16.x`: live adaptation under pressure

### Exact token counting before streaming parity

Exact provider-side token counting is valuable, but it is not the next operational blocker. Streaming parity and workflow continuity matter more first.

### Semantic caching before exact caching or usage evidence

Semantic caching is expensive, operationally heavier, and easy to romanticize. It should remain explicitly later than:

- exact request/response caching
- virtual keys and budgets
- a stable multi-instance contract
- observed workload evidence that semantic similarity would actually pay off

## `v2.x`: budgets, coordination, and higher-cost intelligence

These are valid directions, but they should be sequenced honestly.

### Team and org budget hierarchy

Worth doing only after a solid virtual-key layer exists.

Recommendation:

- first ship per-key budget controls and spend ledgers
- then extend to `user -> team -> org`

This is not the next highest-leverage line for the current product. It is a later operator-scale feature.

### Multi-instance shared state via Grid

Still the right product boundary.

Recommendation:

- keep Gate single-instance-friendly
- define a clean shared-state contract that Grid can consume later
- do not pull Redis/Postgres complexity into Gate just to fake clustering

This should remain a `v2.x` line and should follow virtual keys, not precede them.

### Semantic caching

Still a late bet.

Recommendation:

- do exact caching first
- measure hit patterns
- only build semantic caching when prompt homogeneity is proven and the vector-store cost is justified

### OTEL-compatible trace context

This one is different: it is lower risk and more operator-useful than semantic caching.

Recommendation:

- move OTEL trace-context forwarding forward in priority
- it can plausibly land before other `v2.x` ideas

If one item from the old `v2.x` bucket should move earlier, it is OTEL glue, not semantic caching.

## Competitive Positioning: Where To Double Down

The strongest differentiators to compound are:

1. canonical lane abstraction
2. route-aware transport handling across direct, aggregator, and local paths
3. local-first operator control
4. explainable routing and fallback decisions
5. hybrid cloud-plus-local execution

That means:

- do not copy hosted-router black-box behavior
- do not turn Gate into a distributed platform runtime
- do not bury routing logic in one-off client adapters

The right move is to make Gate more legible, more adaptive, and more trustworthy as a gateway.

## Historical Baseline

Recent shipped lines, newest first:

- `v1.13.0`: optional Anthropic bridge and Claude-oriented routing hints
- `v1.12.0`: live provider-source catalog surfaces, Kilo lane clarity, release automation hardening
- `v1.8.0` to `v1.11.x`: canonical lane foundations, route-aware scoring, signal-group expansion, and operator explainability groundwork

Detailed design notes for the orchestration track still live in [Adaptive model orchestration](./ADAPTIVE-ORCHESTRATION.md).

The next concrete execution line is tracked in [Implementation plan](./IMPLEMENTATION-PLAN.md).
