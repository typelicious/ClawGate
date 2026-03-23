"""Tests for enriched routing metrics and trace queries."""

import sqlite3
from pathlib import Path

from faigate.metrics import MetricsStore


def test_metrics_store_persists_trace_fields(tmp_path):
    db_path = tmp_path / "faigate.db"
    metrics = MetricsStore(str(db_path))
    metrics.init()

    metrics.log_request(
        provider="local-worker",
        model="llama3",
        modality="chat",
        layer="profile",
        rule_name="profile-local-only",
        prompt_tokens=120,
        completion_tokens=24,
        cost_usd=0.0,
        latency_ms=43.0,
        requested_model="auto",
        client_profile="local-only",
        client_tag="n8n",
        decision_reason="Client profile 'local-only' selected a preferred provider",
        confidence=0.6,
        canonical_model="local/llama3",
        lane_family="local",
        route_type="local",
        lane_cluster="local-workhorse",
        selection_path="profile-primary",
        runtime_window_state="clear",
        recovered_recently=True,
        last_recovered_issue_type="timeout",
        decision_details={"canonical_model": "local/llama3", "route_type": "local"},
        attempt_order=["local-worker", "cloud-default"],
    )

    recent = metrics.get_recent(1)
    assert recent[0]["requested_model"] == "auto"
    assert recent[0]["modality"] == "chat"
    assert recent[0]["client_profile"] == "local-only"
    assert recent[0]["client_tag"] == "n8n"
    assert recent[0]["decision_reason"].startswith("Client profile")
    assert recent[0]["confidence"] == 0.6
    assert recent[0]["canonical_model"] == "local/llama3"
    assert recent[0]["lane_family"] == "local"
    assert recent[0]["route_type"] == "local"
    assert recent[0]["lane_cluster"] == "local-workhorse"
    assert recent[0]["selection_path"] == "profile-primary"
    assert recent[0]["runtime_window_state"] == "clear"
    assert recent[0]["recovered_recently"] == 1
    assert recent[0]["last_recovered_issue_type"] == "timeout"
    assert recent[0]["decision_details"]["canonical_model"] == "local/llama3"
    assert recent[0]["attempt_order"] == ["local-worker", "cloud-default"]

    client_rows = metrics.get_client_breakdown()
    assert client_rows[0]["modality"] == "chat"
    assert client_rows[0]["client_profile"] == "local-only"
    assert client_rows[0]["client_tag"] == "n8n"
    assert client_rows[0]["provider"] == "local-worker"
    assert client_rows[0]["layer"] == "profile"
    assert client_rows[0]["requests"] == 1
    assert client_rows[0]["prompt_tokens"] == 120
    assert client_rows[0]["compl_tokens"] == 24
    assert client_rows[0]["total_tokens"] == 144
    assert client_rows[0]["failures"] == 0
    assert client_rows[0]["success_pct"] == 100.0

    client_totals = metrics.get_client_totals()
    assert client_totals[0]["client_profile"] == "local-only"
    assert client_totals[0]["client_tag"] == "n8n"
    assert client_totals[0]["total_tokens"] == 144

    metrics.close()


def test_metrics_store_migrates_existing_db(tmp_path):
    db_path = Path(tmp_path) / "legacy.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE requests (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   REAL    NOT NULL,
            provider    TEXT    NOT NULL,
            model       TEXT    NOT NULL,
            layer       TEXT    NOT NULL,
            rule_name   TEXT    NOT NULL,
            prompt_tok  INTEGER DEFAULT 0,
            compl_tok   INTEGER DEFAULT 0,
            cache_hit   INTEGER DEFAULT 0,
            cache_miss  INTEGER DEFAULT 0,
            cost_usd    REAL    DEFAULT 0,
            latency_ms  REAL    DEFAULT 0,
            success     INTEGER DEFAULT 1,
            error       TEXT    DEFAULT ''
        );
        """
    )
    conn.commit()
    conn.close()

    reopened = MetricsStore(str(db_path))
    reopened.init()
    columns = {
        row["name"]
        for row in reopened._q("PRAGMA table_info(requests)")  # noqa: SLF001
    }

    assert "client_profile" in columns
    assert "client_tag" in columns
    assert "modality" in columns
    assert "attempt_order" in columns
    assert "canonical_model" in columns
    assert "lane_family" in columns
    assert "route_type" in columns
    assert "lane_cluster" in columns
    assert "selection_path" in columns
    assert "runtime_window_state" in columns
    assert "recovered_recently" in columns
    assert "last_recovered_issue_type" in columns
    assert "decision_details" in columns
    reopened.close()


def test_metrics_store_filters_recent_and_breakdowns(tmp_path):
    db_path = tmp_path / "filtered.db"
    metrics = MetricsStore(str(db_path))
    metrics.init()

    metrics.log_request(
        provider="local-worker",
        model="llama3",
        modality="image_generation",
        layer="hook",
        rule_name="request-hooks",
        cost_usd=0.0,
        latency_ms=25.0,
        client_profile="local-only",
        client_tag="codex",
        success=True,
    )
    metrics.log_request(
        provider="cloud-default",
        model="cloud-chat",
        modality="chat",
        layer="policy",
        rule_name="prefer-cloud",
        cost_usd=0.01,
        latency_ms=140.0,
        client_profile="generic",
        client_tag="n8n",
        success=False,
    )

    local_recent = metrics.get_recent(10, provider="local-worker")
    assert len(local_recent) == 1
    assert local_recent[0]["provider"] == "local-worker"

    failed_recent = metrics.get_recent(10, success=False)
    assert len(failed_recent) == 1
    assert failed_recent[0]["provider"] == "cloud-default"

    client_rows = metrics.get_client_breakdown(client_tag="codex")
    assert len(client_rows) == 1
    assert client_rows[0]["modality"] == "image_generation"
    assert client_rows[0]["client_tag"] == "codex"
    assert client_rows[0]["provider"] == "local-worker"
    assert client_rows[0]["success_pct"] == 100.0

    modality_rows = metrics.get_modality_breakdown(modality="image_generation")
    assert len(modality_rows) == 1
    assert modality_rows[0]["modality"] == "image_generation"
    assert modality_rows[0]["provider"] == "local-worker"

    routing_rows = metrics.get_routing_breakdown(layer="hook")
    assert len(routing_rows) == 1
    assert routing_rows[0]["layer"] == "hook"


def test_metrics_store_aggregates_lane_family_and_selection_paths(tmp_path):
    db_path = tmp_path / "families.db"
    metrics = MetricsStore(str(db_path))
    metrics.init()

    metrics.log_request(
        provider="deepseek-chat",
        model="deepseek-chat",
        modality="chat",
        layer="heuristic",
        rule_name="default",
        cost_usd=0.03,
        latency_ms=120.0,
        canonical_model="deepseek/chat",
        lane_family="deepseek",
        route_type="direct",
        lane_cluster="balanced-workhorse",
        selection_path="primary-selected",
        runtime_window_state="clear",
        recovered_recently=True,
        last_recovered_issue_type="rate-limited",
    )
    metrics.log_request(
        provider="openrouter-fallback",
        model="openrouter/auto",
        modality="chat",
        layer="fallback",
        rule_name="fallback",
        cost_usd=0.04,
        latency_ms=200.0,
        canonical_model="aggregator/openrouter-auto",
        lane_family="openrouter",
        route_type="aggregator",
        lane_cluster="aggregator-fallback",
        selection_path="same-lane-route",
        runtime_window_state="cooldown",
        recovered_recently=False,
        last_recovered_issue_type="",
    )

    family_rows = metrics.get_lane_family_breakdown()
    deepseek_row = next(row for row in family_rows if row["lane_family"] == "deepseek")
    assert deepseek_row["recovered_requests"] == 1
    openrouter_row = next(row for row in family_rows if row["lane_family"] == "openrouter")
    assert openrouter_row["cooldown_requests"] == 1

    selection_rows = metrics.get_selection_path_breakdown()
    same_lane = next(row for row in selection_rows if row["selection_path"] == "same-lane-route")
    assert same_lane["lane_family"] == "openrouter"
    assert same_lane["runtime_window_state"] == "cooldown"
    assert same_lane["recovered_recently"] == 0

    metrics.close()


def test_metrics_store_tracks_operator_events(tmp_path):
    db_path = tmp_path / "operator.db"
    metrics = MetricsStore(str(db_path))
    metrics.init()

    metrics.log_operator_event(
        event_type="update",
        action="auto-update-apply",
        client_tag="operator",
        status="ok",
        update_type="minor",
        target_version="v0.7.0",
        eligible=True,
        recommended_action="Upgrade to the latest release",
        detail="",
    )
    metrics.log_operator_event(
        event_type="update",
        action="update-check",
        client_tag="operator",
        status="unavailable",
        update_type="unknown",
        target_version="",
        eligible=False,
        recommended_action="Inspect release connectivity and retry later",
        detail="network unavailable",
    )

    events = metrics.get_operator_events(10, action="auto-update-apply")
    assert len(events) == 1
    assert events[0]["update_type"] == "minor"
    assert events[0]["eligible"] == 1

    breakdown = metrics.get_operator_breakdown(status="ok")
    assert len(breakdown) == 1
    assert breakdown[0]["action"] == "auto-update-apply"
    assert breakdown[0]["events"] == 1

    metrics.close()
