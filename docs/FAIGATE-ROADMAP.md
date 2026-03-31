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

## Parity Targets

The roadmap treats three parity goals as distinct targets, not one fuzzy promise.

### Full Anthropic parity

Meaning:

- protocol-level parity for the Anthropic-compatible surface
- clients that speak Anthropic `messages` should not need special-case awareness of Gate

Includes:

- `POST /v1/messages` request and response shape
- SSE streaming parity
- content-block parity beyond basic text and tool flow
- header, version, and beta compatibility
- compatible error envelopes and stop reasons
- trustworthy token counting behavior

### Full Claude Code parity

Meaning:

- Claude Code should be comfortable to use against local Gate in real daily coding workflows

Includes:

- iterative coding sessions
- streaming and tool-oriented flows
- stable aliasing and route continuity
- fallback behavior that does not break the working session unnecessarily
- enough protocol parity that Claude Code does not feel like it is on a fragile compatibility layer

### Full Claude Desktop parity

Meaning:

- Claude Desktop should be a viable local daily-use client against Gate where endpoint override is supported

Includes:

- stable local endpoint configuration
- good session behavior for the feature set Claude Desktop actually uses
- no recurring “almost compatible but annoying in practice” gaps

Strategically, this matters beyond personal convenience. If Gate can serve Claude Desktop cleanly, it proves the local Claude-native gateway story much more strongly than API compatibility alone.

## Current release target: `v1.14.x`

`v1.13.0` shipped the Anthropic bridge as an opt-in early-adopter line.

The next release should not chase more protocol breadth first. It should make
the existing gateway meaningfully cheaper and more trustworthy for daily coding
traffic across Claude Code, opencode, openclaw, and similar clients.

### `v1.14.x`: coding auto modes plus Claude-native daily-use hardening

This is the highest-leverage next line.

Primary goals:

- make the cheapest capable route the default for coding traffic instead of
  burning Sonnet or Opus too early
- align client profiles and named routing modes around the same routing intent
- make the Anthropic bridge comfortable for real Claude Code workflows
- close the highest-value Anthropic protocol gaps
- prepare the bridge for a serious Claude Desktop parity track immediately after
- close the biggest protocol-parity gaps before expanding scope again
- keep the bridge opt-in and explicit while improving day-to-day reliability

Expected slices:

1. map Claude-native ids to routing intent instead of direct frontier providers
   - `claude-sonnet-* -> auto`
   - `claude-opus-* -> premium`
   - `claude-haiku-* -> eco`
2. add and align coding routing modes
   - `coding-auto`
   - `coding-fast`
   - `coding-premium`
3. stronger client defaults for
   - `claude`
   - `opencode`
   - `openclaw`
   - `codex`
4. SSE streaming parity for `/v1/messages`
5. fuller Anthropic block compatibility beyond the current text plus basic tool flow
6. stronger Claude-client validation fixtures and operator troubleshooting
7. sharper error and stop-reason compatibility

Non-goals:

- exact provider-side token counting for every backend
- "full parity" marketing language before live client coverage proves it
- hosted or multi-user control-plane features

### `v1.15.x`: Claude Desktop parity or adaptive orchestration trust

This should be chosen by evidence after `v1.14.x`, not by preference.

If Claude Desktop local usage proves to be the next real operator lever, take the desktop-parity line first. Otherwise, take the routing-value line first.

#### Option A: Claude Desktop parity

Primary goals:

- make Claude Desktop a genuinely usable local client against Gate
- validate supported local endpoint-override paths
- remove recurring desktop-specific compatibility friction

Expected slices:

1. endpoint-override and config-path validation for supported desktop flows
2. desktop-specific session and response compatibility hardening
3. clearer local testing and troubleshooting instructions
4. release-readiness validation for desktop workflows

The current feasibility gate for this option is tracked in [Claude Desktop feasibility](./CLAUDE-DESKTOP-FEASIBILITY.md).

#### Option B: adaptive orchestration trust

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

### `v1.16.x`: remaining parity or live adaptation under pressure

Only pursue the live-adaptation line once the decision model is trustworthy and the most valuable Claude-native parity gaps are no longer the dominant operator pain.

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
| Full Anthropic parity | Not there | Streaming and deeper block coverage are missing | Treat as staged protocol parity, beginning in `v1.14.x` |
| Full Claude Code parity | Not there | Real client workflow coverage is still partial | Focus `v1.14.x` on practical daily-use parity |
| Full Claude Desktop parity | Not there | Desktop-specific override paths and real workflow validation are still thin | Make this an explicit follow-on track right after `v1.14.x` |
| SSE streaming parity | Not shipped for the bridge yet | Missing bridge streaming path | Highest-priority bridge gap for `v1.14.x` |
| Exact provider-side token counting | Not shipped | Needs backend-aware counting per route or provider API support | Useful, but not a blocker for `v1.14.x`; likely `v1.15.x` or later |

## What Should Not Drive The Next Releases

Some ideas are valid, but they are not the best next lever.

### Full parity as a release slogan

Avoid release lines built around vague parity claims.

Better framing:

- `v1.14.x`: Anthropic protocol hardening plus Claude Code daily-use parity
- `v1.15.x`: adaptive orchestration trust
- `v1.16.x`: Claude Desktop parity or live adaptation under pressure, depending on validated client demand

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

<<<<<<< HEAD
The next concrete execution line is tracked in [Implementation plan](./IMPLEMENTATION-PLAN.md).
=======
ClawRouter's transport binding model (`direct`, `wallet-router`, `aggregator`) is well-designed and faigate should adopt its vocabulary in `lane_registry.py` — this is already partly done (`route_type: direct / aggregator / wallet-router`). The area where faigate leads is the full provider-intelligence layer: ClawRouter does not model benchmark clusters, cache semantics, or per-client signal scoring.

What faigate can learn from ClawRouter: deeper agent-native transport contracts, richer `x-openclaw-*` header semantics for multi-agent delegation flows.

### Product surface priorities from LLM AIRouter and ClawRouter

ClawRouter is strongest at framing the routing promise clearly: cheapest capable
model, explicit policies, and a legible routing pipeline.

LLM AIRouter is strongest at framing the operating surface clearly: overview,
providers, analytics, stacks, routes, request log, provider limits, CLI tools,
and settings in one coherent dashboard story.

The product goal for Gate is to combine both advantages without inheriting their
hosted-first or wallet-first assumptions:

- local-first and operator-owned by default
- agent-native, not just app-dashboard-native
- one runtime that works for Claude Code, opencode, openclaw, n8n, curl, and custom apps
- explicit route intelligence, not black-box “AI chooses for you” marketing

That means the next product-surface slices should be:

1. overview dashboard that makes provider health, spend, lane families, and recent routing visible in one glance
2. providers view that exposes route type, quota domain, billing mode, lane family, and current readiness
3. analytics view that ties cost, token usage, and routing posture back to concrete clients and stacks
4. stacks view for named route bundles such as coding-default, coding-premium, local-only, or Claude-safe mirrors
5. routes and request-log views that explain why one route won and why cheaper alternatives lost
6. CLI and helper-tool surface as a first-class product feature, not a fallback for when the dashboard is missing something

That should now be read more explicitly through operator jobs:

1. `Overview`
   - "is Gate safe and request-ready right now?"
2. `Providers`
   - "which routes are usable, degraded, stale, or quota-coupled?"
3. `Clients`
   - "which tools are expensive, slow, or misprofiled?"
4. `Routes`
   - "why did Gate choose this lane and route?"
5. `Analytics`
   - "where is the spend and fallback pressure?"
6. `Request Log`
   - "what just happened?"
7. `Catalog`
   - "are my provider assumptions still fresh enough to trust?"
8. `Integrations`
   - "how do I wire Claude Code, opencode, openclaw, Codex, automation clients, and custom apps quickly?"
9. `Troubleshooting`
   - "what is the shortest path from symptom to fix?"

### Licensing and product-boundary read on those surfaces

These surface expansions should follow the existing fusionAIze stack boundary:

**Tier A — Apache 2.0 core**

- local dashboard views over Gate's own runtime state
- provider inventory, lane metadata, route readiness, and request traces
- stack definitions and route explainability
- helper CLIs and exportable local reports

**Tier B — source-available operator packs**

- advanced alerts, saved routing policies, and heavier analytics overlays
- longer retention, richer usage forensics, and external callback packs
- team-aware budget controls and higher-level stack templates

**Tier C — commercial control plane**

- multi-instance shared state
- hosted or managed control-plane views
- org RBAC, audit trails, and enterprise governance overlays
- Grid/OS coordination features that should not bloat the local Gate runtime

---

## `v1.8.0` to `v1.11.x`: adaptive model orchestration (original sequence for reference)

Primary goals:

- treat providers, aggregators, and direct routes as execution paths to canonical model lanes rather than as one flat list of alternatives
- let scenarios such as `quality`, `balanced`, `eco`, and `free` choose the right lane threshold and degradation path instead of only choosing a provider tier
- preserve same-lane quality when direct quota is exhausted by trying equivalent aggregator routes before dropping to a weaker model cluster
- keep benchmark and cost assumptions visible, curated, and refreshable so "magical" routing still stays explainable

Release sequence:

1. `v1.8.0` ✅ lane registry, provider lane metadata, and route-aware catalog surfaces
2. `v1.9.0` ✅ lane-aware router scoring and "why this lane?" traces
3. `v1.9.1` ✅ routing bug fixes, signal group expansion, mode-override hook
4. `v1.9.2`: pre-failure RPM/TPM headroom, trace-id header
5. `v1.10.x`: provider intelligence layer (capability tags, benchmark ranks, cache TTL, TTFT, pricing freshness)
6. `v1.11.x`: virtual key layer, gateway-level response caching, webhook observability, guardrail hooks
7. `v2.x`: team/org budget hierarchy, multi-instance Grid coordination, semantic caching, OTEL

Non-negotiable guardrails:

- never hide a downgrade from operators
- prefer same-lane route substitution before weaker-model degradation
- keep old configs compatible while lane metadata is introduced
- treat benchmarks and cost heuristics as curated operational inputs, not as magic constants

## `v1.5.0`: guided control-center UX

Primary goals:

- make the standalone Gate shell feel like the first serious product surface instead of a loose set of helper scripts
- introduce one obvious happy path for first setup, validation, restart, and client connection
- replace raw JSON-first operator views with compact human summaries plus drill-downs where needed
- keep the Gate UX aligned with the later Grid orchestration direction so the products feel like one family

Recommended minimal slices:

1. `Quick Setup` happy path inside `faigate-menu`
2. compact summary cards for gateway, config, providers, and clients in the main operational menus
3. shorter, recommendation-first client quickstarts with per-client drilldown instead of long first-contact dumps
4. explicit next-step receipts after wizard, validation, restart, and client-setup actions

Guardrails:

- keep the shell UX scriptable and helper-driven; do not turn `faigate-menu` into a full-screen TUI yet
- prefer compact default output plus optional detail/raw views over large payload dumps
- keep wording calm and operational, especially when health, service-manager state, and bound port state disagree

Post-`1.5.0` UX items already worth bookmarking:

- readiness score and richer setup progress scoring
- port/runtime conflict auto-detection with one-step recovery suggestions
- client route previews that show where a given client would land right now
- richer action receipts and broader `what to do next` guidance
- more compact client cards before the long quickstart text

## Licensing strategy

The fusionAIze stack uses a three-tier open-core model. The tier boundaries are defined here before the features exist so there are no retroactive surprises for the community.

**Non-negotiable rule**: a feature that ships as Tier A will never be moved to Tier B or Tier C. Only newly-built features can be Tier B or Tier C from day one.

This is the lesson from LiteLLM's BSL transition: moving the proxy from Apache 2.0 to BSL 1.1 after the community had adopted it created lasting distrust and reputational damage. faigate will not repeat that mistake.

### Tier A — Apache 2.0 (permanent)

The full local gateway runtime, as it exists and as it will continue to evolve through routine improvements:

- baseline gateway core: routing engine, heuristic rules, hook pipeline, fallback chains
- all provider adapters: direct, aggregator, wallet-router
- all built-in request hooks: locality, prefer-provider, profile-override, mode-override
- client profile system and opencode / openclaw / n8n / cli profiles
- config schema and YAML format
- SQLite metrics store and trace recording
- operator dashboard (read-only)
- `/api/route`, `/api/stats`, `/api/traces`, `/api/providers` endpoints
- all helper scripts: `faigate-menu`, `faigate-doctor`, `faigate-status`, `faigate-update`, etc.
- Homebrew formula and packaging
- everything shipped through v1.9.x and all future routine routing improvements

### Tier B — Source-available (open-core)

Features built for operators who run faigate at team or production scale. Defined as Tier B before they are built:

- virtual key layer (`max_budget`, `budget_duration`, `rpm_limit`, `allowed_models`, key lifecycle)
- per-key budget enforcement and spend ledger
- webhook / callback observability output to external sinks (Langfuse, Helicone, Datadog)
- advanced guardrail hook implementations (PII detection via Presidio, prompt injection via Lakera)
- named routing strategy weight presets as a commercial operator convenience
- gateway-level response caching with Redis backend
- team and org budget hierarchy

### Tier C — Proprietary / commercial (fusionAIze OS)

Control-plane features that belong with the broader fusionAIze stack, not with the local gateway runtime:

- managed control plane (fusionAIze Grid / OS)
- SSO / SAML / OIDC authentication for the operator UI
- RBAC and audit logs for team and org management
- multi-instance shared state and distributed rate-limit coordination (Grid)
- enterprise SLAs and priority support

### Product stack and tier mapping

| Product | Role | Tier |
|---|---|---|
| **Gate** | Local-first routing runtime | A core + selective B |
| **Lens** | Observability and spend analytics consuming Gate `/api/stats`, `/api/traces`, webhook events | B–C |
| **Grid** | Multi-instance coordination: distributed rate limits, shared virtual key registry, cross-instance cache | C |
| **OS** | SSO, RBAC, audit logs, team management — LiteLLM Enterprise's territory | C |
| **Fabric** | Content policy and guardrail enforcement via Gate's hook seam | B–C |

## `v1.3.0`: guided setup and catalog-assisted updates

Primary goals:

- make first setup and later provider updates realistic without turning `config.yaml` into hand-edited drift bait
- keep routing modes, client defaults, and provider selection understandable across many clients
- improve provider-catalog freshness and update suggestions without silently rewriting operator intent
- start the provider-discovery and recommendation-link line only in a transparency-first, metadata-first shape

Recommended minimal slices:

1. wizard candidate selection, update suggestions, dry-run summaries, and backup-aware writes
2. provider-catalog source metadata, offer-track volatility flags, and freshness alerts
3. wizard and CLI usage polish so the guided flow is self-explanatory from `--help`
4. optional provider recommendation-link metadata with explicit disclosure, but still no ranking changes based on provider-link metadata

Guardrails for any recommendation-link work in this line:

- recommendation ranking must never use provider-link metadata as an input and must stay performance-led, preferring fit, quality, health, capability, and cost behavior
- provider-link metadata should stay operator-owned and secret-backed, not embedded in user-editable client configs
- docs and CLI output should disclose clearly when a shown signup link is informational only
- the first slice should be metadata and display only; managed short links, browser control-center surfaces, and richer landing-page flows can come later

## `v1.2.0`: workstation operations baseline

Primary goals:

- add a dedicated workstation operations guide
- document macOS `launchd` as a first-class local-runtime path
- document Windows Task Scheduler / PowerShell as the baseline Windows path
- keep development checkouts and runtime installs clearly separated
- add a project-owned Homebrew packaging path for macOS workstations

Recommended minimal slices:

1. workstation baseline docs and path layout
2. macOS `launchd` example and instructions
3. Windows startup examples and documentation
4. optional lightweight install helpers only if the docs prove insufficient
5. Homebrew formula and `brew services` guidance for the packaged macOS path

## Post-1.0 direction

The first post-`1.0` block should stay narrow enough to ship as `v1.1.0`.

Primary goals:

- double-check and extend AI-native client support beyond the current OpenClaw, n8n, and CLI baseline
- ship the next wave of integration starters for requested and high-signal agent frameworks
- expose more useful per-client token and usage metrics in the operator surface
- audit the routing-stage stack so the responsibility of each layer stays clear
- keep a structured watch on ClawRouter-style product evolution without copying features blindly

The current framework prioritization lives in [AI-NATIVE-MATRIX.md](./AI-NATIVE-MATRIX.md).

## Big Picture

The opportunity is not to build another thin router.

The opportunity is to build a reusable AI gateway plane that works across:

- local model workers
- direct provider APIs
- proxy providers
- OpenClaw
- workflow systems such as n8n
- CLI-native development environments
- agent tools
- future AI-native SaaS products

If the core stays disciplined, fusionAIze Gate can become the common routing and policy layer shared by several products without collapsing into a bloated platform.

That is the target shape:

- one gateway core
- many providers
- many clients
- optional context and optimization layers
- clear operational boundaries

## Design principles

### 1. Gateway first

fusionAIze Gate should stay a gateway and control plane, not a monolithic platform.

### 2. Standard protocols first

If a client can use the OpenAI-compatible API cleanly, keep it on that path before building a custom adapter.

### 3. Multi-dimensional routing

The design target is to exceed simpler router behavior by making routing explicitly multi-dimensional.

That means fusionAIze Gate should increasingly consider:

- capability support
- health and latency
- cost tier
- local vs cloud locality
- context window size
- cache behavior and cache pricing
- tool usage
- client identity
- modality requirements
- compliance or tenancy constraints

The intent is not to claim that this is fully implemented today. The intent is to make this the guiding routing architecture.

### 4. Optional extension layers

Context, memory, optimization, and sidecar adapters should plug into the gateway cleanly, not become mandatory core behavior.

## Current runtime baseline

Today the runtime already supports:

- one OpenAI-compatible endpoint
- multiple providers behind a single local base URL
- policy, static, heuristic, client-profile, and optional LLM-assisted routing stages
- direct model pinning and fallback chains
- local worker contracts and health probes
- route introspection and traces
- client-aware routing defaults for OpenClaw, n8n, and CLI callers

The next runtime gap to close is not “more core abstraction”. It is “more real clients with less glue”.

## `v1.1.0`: AI-native client expansion and operator visibility

Primary goals:

- add the first post-`1.0` starter wave for requested and high-signal AI-native clients
- add a curated framework matrix so external users can quickly see where fusionAIze Gate fits
- deepen client and token reporting in API and dashboard surfaces
- review policy, static, heuristic, hook, client-profile, and classifier boundaries with clearer ownership and tests

Recommended minimal slices:

1. AI-native client matrix plus roadmap update
2. first-wave starter templates for `SWE-AF`, `paperclip`, `ship-faster`, and the highest-fit external frameworks
3. per-client token and usage reporting in stats and dashboard views
4. routing-layer review plus targeted rule/test cleanup

The plugin question should stay explicitly out of scope for `v1.1.0` and be revisited only after this release line lands.

## OpenClaw direction

OpenClaw remains a first-class integration surface.

Current coverage:

- one-agent traffic through the normal OpenAI-compatible path
- many-agent or delegated traffic through the same path with `x-openclaw-source`
- OpenClaw-side model aliases and profile defaults

Near-term direction:

- document one-agent and many-agent behavior explicitly
- keep the integration header-based and OpenAI-compatible
- avoid forking the core gateway logic just for OpenClaw

## Modality expansion

Inspired by the value of image-router patterns in other gateways, fusionAIze Gate should eventually support modality-aware routing beyond chat.

Planned direction:

- add a provider contract for image-generation-capable backends
- add modality-aware request classification
- route image tasks to the right backend without polluting the chat path

This is a roadmap item, not a current runtime claim.

## Architecture direction

### Gateway core

Responsibilities:

- request normalization
- route selection
- fallback handling
- timeout boundaries
- usage and trace recording
- operational endpoints

### Provider layer

Responsibilities:

- cloud providers
- OpenAI-compatible proxies
- local workers
- future modality-specific providers

### Client layer

Responsibilities:

- OpenClaw
- n8n and workflow clients
- CLI wrappers and proxy clients
- future AI-native app integrations

### Optional extension layer

Responsibilities:

- request hooks
- context or memory enrichment
- optimization hooks
- policy overlays

## Release path to v1.0.0

`v0.3.0` is the first public fusionAIze Gate release. The path to `v1.0.0` should stay incremental and reviewable.

### `v0.4.x`: deeper routing and extension hardening

Primary goals:

- deepen multi-dimensional scoring beyond simple fit checks for cache behavior, context windows, provider limits, locality, latency, and recent failures
- keep refining the simple dashboard around traces, provider/client breakdowns, route visibility, and safe operator ergonomics
- keep OpenClaw one-agent and many-agent flows on the same OpenAI-compatible path with clearer defaults
- harden the request hook seam for context, memory, and optimization layers, including fail-closed behavior and input sanitization

This release line should deepen the gateway core without turning it into a monolith.

### `v0.5.0`: operator distribution baseline

Primary goals:

- add the first modality-aware provider contract, starting with image generation
- publish an official Docker release path
- publish fusionAIze Gate to PyPI
- add provider and client onboarding helpers for many-provider and many-client deployments
- add a publish dry-run path for Python package and GHCR validation before real release tags
- add validation workflows so operators can catch config mistakes before rollout
- complete the public community-health baseline and security-overview baseline for the repo

This is the first release line where installation and upgrade paths should feel productized for external users.

### `v0.6.x`: modality expansion

Primary goals:

- add modality-aware provider contracts, starting with image generation
- extend that contract toward image editing where the provider surface supports it
- keep chat and image paths explicit instead of mixing modality-specific behavior into one opaque route
- expose modality-aware health, provider inventory, and routing visibility in the dashboard and operational endpoints

This should borrow the useful parts of image-router patterns without copying another gateway's product shape.

### `v0.7.x`: operations polish

Primary goals:

- expand the release-check baseline into stronger update alerts so operators can see when a newer release is available
- add an optional automatic update enabler for controlled deployments
- improve route traces, metrics, and dashboard filters for providers, clients, and profiles
- keep the dashboard simple, read-heavy, and operationally safe

This release line is about day-2 operations rather than new routing concepts.

The first small slice in this line is to turn `GET /api/update` from a plain boolean check into an operator-facing alert surface with update type, alert level, and recommended action.

The next small slice is to keep auto-update conservative:

- disabled by default
- no checkout mutation over HTTP
- helper-driven and operator-triggered only
- major upgrades still manual unless explicitly allowed

### `v0.8.x`: many-provider and many-client onboarding

Primary goals:

- make onboarding repeatable for many providers and many clients on one gateway
- ship clearer presets and validation for OpenClaw, n8n, CLI wrappers, and future AI-native applications
- reduce manual config editing for common deployment shapes
- tighten integration coverage for delegated or many-agent traffic where headers identify sub-clients

The target is faster adoption without custom glue for every client.

Current `v0.8.x` baseline already includes:

- onboarding report plus validation helpers
- staged provider rollout reporting
- client matrix reporting
- starter templates for OpenClaw, n8n, CLI, cloud providers, local workers, and image providers
- matching provider `.env` starter files
- delegated OpenClaw request examples
- starter custom-profile examples for future AI-native applications
- doctor checks for missing provider env placeholders
- JSON and Markdown onboarding exports

### `v0.9.x`: pre-1.0 hardening

Primary goals:

- stabilize request hook boundaries and extension contracts
- expand integration and functional test coverage across real client flows
- complete documentation review across README, onboarding, integrations, troubleshooting, and release docs
- close obvious operational gaps discovered during earlier releases

This release line should leave `v1.0.0` focused on stability and security gates, not backlog cleanup.

Current `v0.9.x` baseline is aimed at:

- conservative response headers and dashboard CSP defaults
- explicit JSON and multipart size guardrails
- bounded routing and operator header handling
- broader functional API tests around dashboard, routing, and upload surfaces
- documentation updates that make the hardened defaults visible to operators

### `v1.0.0`: stable gateway baseline

Primary goals:

- declare a stable fusionAIze Gate gateway baseline for local-first, multi-provider routing
- publish the first separate npm CLI package for fusionAIze Gate-adjacent CLI usage
- complete a comprehensive security review before release

The `v1.0.0` security review should explicitly cover:

- cross-site scripting and HTML or CSS injection risks in the dashboard
- request, header, and parameter injection risks in proxy and routing paths
- dependency vulnerabilities and unsafe defaults
- local-worker and upstream proxy trust boundaries
- auth, secret-handling, and writable-path assumptions

`v1.0.0` should only ship after those review results are addressed or documented with a clear mitigation plan.

Current `v1.0.0` baseline is aimed at:

- dashboard CSP hardening without turning the no-build UI into a separate frontend app
- reduced leakage of upstream provider failure details in client responses
- clearer trust-boundary validation for provider base URLs
- a documented release-gate security review with explicit residual risks
- a separate npm CLI package that complements the Python gateway instead of replacing it

## Updated near-term PR sequence

The next sequence should ladder directly into the release path above:

1. `feat(provider): add modality-aware provider contracts, starting with image generation`
2. `feat(provider): extend modality contracts toward image editing where supported`
3. `feat(onboarding): add provider/client onboarding helpers and validation workflows`
4. `feat(dist): add Docker release path and PyPI publishing baseline`
5. `feat(ops): add update alerts and an optional auto-update enabler for controlled deployments`
6. `feat(cli): define the separate npm or TypeScript CLI package path for the v1.0.0 line`

## Check on the earlier sequence

The earlier near-term sequence is now effectively complete up through the routing and observability foundation:

1. `docs: add fusionAIze Gate roadmap and rename note` -> done
2. `feat(config): add provider capability schema` -> done
3. `feat(router): add policy-based provider selection` -> done
4. `feat(provider): add local worker provider contract` -> done
5. `feat(api): add client profile support` -> done
6. `feat(obs): add route introspection and policy metrics` -> done, and now extended with traces and local worker probing
7. `feat(ext): add optional request hook interfaces` -> done
8. `feat(router): add first multi-dimensional route-fit inputs for cache, context windows, provider limits, and locality` -> done
9. `feat(obs): harden the simple dashboard around traces, provider/client filters, and route visibility` -> done

## Detailed near-term backlog

### 1. Optional request hook interfaces

Why:

- this creates the seam for context, memory, and optimization layers without hard-coupling them

Examples:

- optional memory or context enrichment before routing
- request-shaping hooks for RTK-like CLI optimization
- operator-controlled extension points that can stay disabled by default

### 2. Multi-dimensional routing inputs

Why:

- routing should understand more than keywords and simple tier preferences

Examples:

- cache-read vs cache-miss economics
- context window fit
- locality and policy constraints
- latency/health tradeoffs
- provider-specific max context and cache behavior

### 3. Simple dashboard hardening

Why:

- fusionAIze Gate already exposes a dashboard endpoint, but operators need a clearer read-only control surface

Examples:

- route trace table with provider and client filters
- provider health panel with capabilities and contract type
- quick links to dry-run routing and recent failure context

### 4. Image generation and editing routing

Why:

- multi-modal routing is a natural next expansion for a gateway plane

Examples:

- image-generation-capable provider contracts
- image-editing-capable provider contracts
- explicit modality routing so chat, image generation, and image editing stay understandable

### 5. Provider and client onboarding helpers

Why:

- many-provider, many-client deployments need a clearer adoption path than manual config editing alone

Examples:

- bootstrap helpers for provider credentials and base URLs
- starter profiles for OpenClaw, n8n, CLI, and future AI-native applications
- preflight config validation before a rollout or restart

### 6. Update alerts and optional automatic update enablers

Why:

- operators need a safer path than only ad hoc manual updates

Current baseline:

- cached release checks via `GET /api/update`
- dashboard visibility for current vs latest known release
- local helper access via `faigate-update-check`
- opt-in eligibility reporting and helper-driven apply flow via `faigate-auto-update`

This should remain opt-in and operationally conservative as it expands toward scheduled helper use, stronger rollout controls, clearer operator approval boundaries, and small rollout-ring/channel distinctions.

### 7. Distribution channels

Why:

- the project should become easier to adopt without coupling packaging strategy to one runtime

Examples:

- GitHub Releases as the default channel now
- Docker images and PyPI packages by `v0.5.0`
- a separate npm or TypeScript CLI package by `v1.0.0`, not a Node rewrite of the core gateway

### 8. Security review as a release gate

Why:

- `v1.0.0` needs a credible stability and security bar, not just a larger feature list

Examples:

- dashboard rendering review for XSS and HTML or CSS injection paths
- request routing review for injection, header abuse, and unsafe forwarding behavior
- dependency and configuration review for known vulnerabilities and insecure defaults
- documentation review so security expectations and deployment assumptions are explicit

## Documentation direction

fusionAIze Gate should be understandable from the outside in under a few minutes.

That means keeping these docs current:

- README for the landing page
- architecture for technical orientation
- integrations for OpenClaw, n8n, CLI, and future clients
- onboarding for many-provider and many-client adoption
- troubleshooting for operators
- process docs for contributors

## Review cadence

Every 4 or 5 merged PRs, run a broader review pass:

- review unit tests
- review integration tests
- review functional coverage against real workflows
- update every relevant doc
- refresh the roadmap and process docs if the direction changed

This is necessary because fusionAIze Gate is evolving quickly and the docs can drift even when individual PRs are clean.

## Provider discovery and recommendation links

fusionAIze Gate should be able to help operators and end users discover suitable providers, but it should not turn recommendation output into a monetized marketplace.

That means the future recommendation-link line should stay deliberately staged:

### First slices that make sense soon

- add optional provider-catalog fields for signup URLs, disclosure labels, and source ownership
- surface those links in CLI or later browser-based control-center output only when they are available and disclosed
- allow operator-managed secret or env-backed provider-link overrides rather than baking them into normal client-visible config

### Later slices that make sense after that

- optional managed short-link or landing-page wrappers
- richer provider discovery views in a small browser control center
- trust/performance signals derived from historical provider behavior, so recommendations can explain quality and reliability more concretely

The non-negotiable rule is simple: recommendation quality must stay fully independent from provider-link metadata, and signup links may only follow from a recommendation rather than shaping it.

## Assumptions

- OpenAI-compatible HTTP remains the default interoperability surface in the near term
- OpenClaw, n8n, and CLI tools should keep sharing one gateway unless a client truly requires a dedicated adapter
- modality expansion should stay contract-driven instead of adding ad hoc special cases
- context, memory, and optimization remain optional layers around the gateway core
>>>>>>> b0b5a2e (feat: refine routing defaults and operator dashboard)
