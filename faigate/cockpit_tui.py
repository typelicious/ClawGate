"""Agent-native terminal cockpit for faigate — built with Textual.

Usage:
    faigate cockpit              # Interactive TUI
    faigate cockpit --agent health   # JSON output for agent consumption
    faigate cockpit --agent providers
    faigate cockpit --agent circuits
    faigate cockpit --agent stats
    faigate cockpit --agent routes
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import httpx
from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Footer, Header, Static, TabbedContent, TabPane

COCKPIT_BASE: str = "http://127.0.0.1:8092"

# ── Helper ──────────────────────────────────────────────────────────────


def _fetch(endpoint: str) -> dict[str, Any]:
    """Fetch a /api/cockpit/ endpoint; returns {} on error."""
    try:
        r = httpx.get(f"{COCKPIT_BASE}{endpoint}", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


def _circuit_color(state: str) -> str:
    if state == "OPEN":
        return "[bold red]●[/]"
    if state == "HALF_OPEN":
        return "[bold yellow]◐[/]"
    return "[bold green]●[/]"


def _healthy_color(healthy: bool) -> str:
    return "[green]✓[/]" if healthy else "[red]✗[/]"


def _latency_str(ms: float) -> str:
    if ms <= 0:
        return "—"
    if ms < 500:
        return f"[green]{ms:.0f}ms[/]"
    if ms < 2000:
        return f"[yellow]{ms:.0f}ms[/]"
    return f"[red]{ms:.0f}ms[/]"


# ── Dashboard Tab ─────────────────────────────────────────────────────


class DashboardTab(Widget):
    CIRCUIT_ORDER: list[str] = ["OPEN", "HALF_OPEN", "CLOSED"]

    def compose(self) -> ComposeResult:
        yield Static("Refreshing…", id="cockpit-summary")
        yield Static("", id="cockpit-grid")

    def on_mount(self) -> None:
        self.set_interval(5.0, self.refresh_data)
        self.refresh_data()

    def refresh_data(self) -> None:
        data = _fetch("/api/cockpit/health")
        if not data:
            return
        summary = data.get("summary", {})
        summary_widget = self.query_one("#cockpit-summary", Static)
        summary_widget.update(
            f"[bold]Providers:[/] {summary.get('total', 0)} total, "
            f"[green]{summary.get('healthy', 0)} healthy[/], "
            f"[yellow]{summary.get('degraded', 0)} degraded[/], "
            f"[red]{summary.get('unhealthy', 0)} unhealthy[/], "
            f"[red]⚡{summary.get('circuits_open', 0)} open[/]"
        )

        providers: dict[str, dict] = data.get("providers", {})
        sorted_providers = sorted(
            providers.items(),
            key=lambda kv: (
                self.CIRCUIT_ORDER.index(kv[1].get("circuit", "CLOSED"))
                if kv[1].get("circuit") in self.CIRCUIT_ORDER
                else 99,
                kv[0],
            ),
        )
        rows: list[str] = []
        for name, p in sorted_providers:
            circ = p.get("circuit", "CLOSED")
            fails = p.get("circuit_failures", 0)
            fail_str = f"[red]{fails} fails[/]" if fails > 0 else ""
            rows.append(
                f"{_circuit_color(circ)} {_healthy_color(p.get('healthy', False))} "
                f"[bold]{name}[/] {_latency_str(p.get('latency_ms', 0))} "
                f"{fail_str}"
            )
        self.query_one("#cockpit-grid", Static).update("\n".join(rows))


# ── Providers Tab ─────────────────────────────────────────────────────


class ProvidersTab(Widget):
    def compose(self) -> ComposeResult:
        yield Static("Loading providers…", id="providers-detail")

    def on_mount(self) -> None:
        self.set_interval(5.0, self.refresh_data)
        self.refresh_data()

    def refresh_data(self) -> None:
        data = _fetch("/api/cockpit/providers")
        if not data:
            return
        providers_list: list[dict] = data.get("providers", [])
        rows: list[str] = []
        for p in providers_list:
            name = p.get("name", "?")
            backend = p.get("backend", "?")
            model = p.get("model", "?")
            tier = p.get("tier", "?")
            circ = p.get("circuit", "CLOSED")
            healthy = p.get("healthy", False)
            latency = p.get("latency_ms", 0)
            context = p.get("context_window", 0) or 0
            rows.append(
                f"{_circuit_color(circ)} {_healthy_color(healthy)} "
                f"[bold]{name}[/]  {_latency_str(latency)}"
                f"\n    backend={backend}  model={model}  tier={tier}"
                f"{'  ctx=' + str(context) if context else ''}"
            )
        self.query_one("#providers-detail", Static).update("\n\n".join(rows))


# ── Circuits Tab ─────────────────────────────────────────────────────


class CircuitsTab(Widget):
    def compose(self) -> ComposeResult:
        yield Static("Loading circuits…", id="circuits-content")

    def on_mount(self) -> None:
        self.set_interval(3.0, self.refresh_data)
        self.refresh_data()

    def refresh_data(self) -> None:
        data = _fetch("/api/cockpit/circuits")
        if not data:
            return
        circuits: dict[str, dict] = data.get("circuits", {})
        if not circuits:
            self.query_one("#circuits-content", Static).update("[dim]No circuit data[/]")
            return
        rows: list[str] = []
        for name, c in sorted(circuits.items()):
            state = c.get("state", "CLOSED")
            failures = c.get("failure_count", 0)
            cooldown = c.get("cooldown_remaining_s", 0)
            last_fail = c.get("last_failure_error", "")[:80]
            rows.append(
                f"{_circuit_color(state)} [bold]{name}[/]  [{state}]  {failures} failures"
                + (f"  cooldown {cooldown:.0f}s remaining" if state == "OPEN" and cooldown > 0 else "")
                + (f"\n    last error: {last_fail}" if last_fail else "")
            )
        self.query_one("#circuits-content", Static).update("\n\n".join(rows))


# ── Routes Tab ───────────────────────────────────────────────────────


class RoutesTab(Widget):
    def compose(self) -> ComposeResult:
        yield Static("Loading routes…", id="routes-content")

    def on_mount(self) -> None:
        self.set_interval(5.0, self.refresh_data)
        self.refresh_data()

    def refresh_data(self) -> None:
        data = _fetch("/api/cockpit/routes/log?limit=20")
        if not data:
            return
        routes_list: list[dict] = data.get("routes", [])
        if not routes_list:
            self.query_one("#routes-content", Static).update("[dim]No recent routes[/]")
            return
        rows: list[str] = []
        for r in routes_list[:15]:
            provider = r.get("provider", "?")
            model = r.get("requested_model") or r.get("model", "?")
            success = r.get("success", True)
            ts = r.get("timestamp", "")
            latency = r.get("latency_ms", 0)
            status = "[green]✓[/]" if success else "[red]✗[/]"
            rows.append(f"{status} {provider}  {model}  {_latency_str(latency)}  [dim]{ts}[/]")
        self.query_one("#routes-content", Static).update("\n".join(rows))


# ── Main TUI App ─────────────────────────────────────────────────────


class CockpitApp(App):
    CSS = """
    Screen {
        background: #0a0a0f;
    }
    Header {
        background: #14141f;
        color: #7af;
    }
    Footer {
        background: #14141f;
    }
    TabPane {
        padding: 1;
    }
    #cockpit-summary {
        padding: 1;
        border: solid #222;
        margin-bottom: 1;
        background: #14141f;
    }
    #cockpit-grid, #providers-detail, #circuits-content, #routes-content {
        padding: 0 1;
        height: 1fr;
    }
    """

    TITLE = "faigate cockpit"
    SUB_TITLE = "— operator view —"

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane(" Dashboard "):
                yield DashboardTab()
            with TabPane(" Providers "):
                yield ProvidersTab()
            with TabPane(" Circuits "):
                yield CircuitsTab()
            with TabPane(" Routes "):
                yield RoutesTab()
        yield Footer()

    def key_q(self) -> None:
        self.exit()


# ── Agent mode (JSON output) ─────────────────────────────────────────


_AGENT_ENDPOINTS: dict[str, str] = {
    "health": "/api/cockpit/health",
    "providers": "/api/cockpit/providers",
    "circuits": "/api/cockpit/circuits",
    "stats": "/api/cockpit/stats",
    "routes": "/api/cockpit/routes/log",
}


def agent_json_output(endpoint: str) -> None:
    path = _AGENT_ENDPOINTS.get(endpoint, f"/api/cockpit/{endpoint}")
    data = _fetch(path)
    print(json.dumps(data, indent=2, default=str))


def run_tui() -> None:
    CockpitApp().run()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="faigate cockpit",
        description="Agent-native terminal cockpit for faigate",
    )
    parser.add_argument(
        "--agent",
        nargs="?",
        const="health",
        choices=list(_AGENT_ENDPOINTS.keys()),
        help="Agent mode: output JSON for the given endpoint",
    )
    args = parser.parse_args()

    if args.agent:
        agent_json_output(args.agent)
    else:
        run_tui()


if __name__ == "__main__":
    main()
