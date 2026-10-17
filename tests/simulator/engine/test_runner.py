# AI contribution: 50% or more AI-generated
"""Tests for the simulation runner (US-1.1, Task 1.1.6, #99).

Uses the tiny network from ``tests/conftest.py``. Hand-worked timeline of the
tiny timetable with no control strategy. The departure becomes due at
arrival + dwell, and with no hold the train leaves at that same instant:

    green-1  arrives 100, dwell 20 -> due and departs 120
    rem-1    arrives 120, dwell 30 -> due and departs 150
    green-2  arrives 280, dwell 20 -> due and departs 300

At 120 s, rem-1 arriving comes before green-1's departure because arrivals are
earlier in the documented tie order, and departure due comes before departure.
"""

import json
from dataclasses import replace

import pytest

from simulator.engine.event_log import EVENTS_FILE, SUMMARY_FILE
from simulator.engine.runner import RunError, run_scenario

EXPECTED_TIMELINE = [
    ("train_arrival", "green-1", 100.0),
    ("train_arrival", "rem-1", 120.0),
    ("departure_due", "green-1", 120.0),
    ("train_departure", "green-1", 120.0),
    ("departure_due", "rem-1", 150.0),
    ("train_departure", "rem-1", 150.0),
    ("train_arrival", "green-2", 280.0),
    ("departure_due", "green-2", 300.0),
    ("train_departure", "green-2", 300.0),
]


def _read_log(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _timeline(records):
    return [(r["event_type"], r["train_id"], r["time_s"]) for r in records]


def test_smoke_run_with_no_control_strategy_writes_the_expected_log(
    tmp_path, minimal_scenario, build_streams, build_tiny_network
):
    result = run_scenario(minimal_scenario, build_streams, build_tiny_network, tmp_path)
    assert result.events_path == tmp_path / EVENTS_FILE
    assert _timeline(_read_log(result.events_path)) == EXPECTED_TIMELINE


def test_summary_matches_the_hand_count(
    tmp_path, minimal_scenario, build_streams, build_tiny_network
):
    result = run_scenario(minimal_scenario, build_streams, build_tiny_network, tmp_path)
    summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
    assert summary["master_seed"] == minimal_scenario.master_seed
    assert summary["duration_s"] == 600.0
    assert summary["events_processed"] == 9
    assert summary["events_pending"] == 0
    assert summary["end_time_s"] == 300.0
    assert summary["events_by_type"]["train_arrival"] == 3
    assert summary["events_by_type"]["departure_due"] == 3
    assert summary["events_by_type"]["train_departure"] == 3
    assert summary["events_by_type"]["hold"] == 0


def test_same_scenario_and_seed_give_byte_identical_output(
    tmp_path, minimal_scenario, build_streams, build_tiny_network
):
    first = run_scenario(
        minimal_scenario, build_streams, build_tiny_network, tmp_path / "first"
    )
    second = run_scenario(
        minimal_scenario, build_streams, build_tiny_network, tmp_path / "second"
    )
    # Full files, not summary metrics (US-1.1 acceptance criteria)
    assert first.events_path.read_bytes() == second.events_path.read_bytes()
    assert first.summary_path.read_bytes() == second.summary_path.read_bytes()


def test_streams_are_built_from_the_master_seed_and_passed_to_components(
    tmp_path, minimal_scenario, build_streams, build_tiny_network
):
    seen = {}

    def spy_components(scenario, streams):
        seen["streams"] = streams
        return build_tiny_network(scenario, streams)

    run_scenario(minimal_scenario, build_streams, spy_components, tmp_path)
    assert seen["streams"].master_seed == minimal_scenario.master_seed


def test_period_ending_mid_dwell_leaves_the_departure_pending(
    tmp_path, minimal_scenario, build_streams, build_tiny_network
):
    # Ends at 290 s: green-2 has arrived (280) but its departure is only due
    # at 300, so that event is still waiting
    scenario = replace(minimal_scenario, duration_s=290.0)
    result = run_scenario(scenario, build_streams, build_tiny_network, tmp_path)
    assert _timeline(_read_log(result.events_path)) == EXPECTED_TIMELINE[:7]
    assert result.summary.events_pending == 1
    assert result.summary.end_time_s == 280.0


def test_period_ending_before_the_first_event_processes_nothing(
    tmp_path, minimal_scenario, build_streams, build_tiny_network
):
    scenario = replace(minimal_scenario, duration_s=50.0)
    result = run_scenario(scenario, build_streams, build_tiny_network, tmp_path)
    assert result.events_path.read_bytes() == b""
    assert result.summary.events_processed == 0
    # The three scheduled arrivals are still waiting
    assert result.summary.events_pending == 3


def test_run_with_no_components_writes_an_empty_log(
    tmp_path, minimal_scenario, build_streams
):
    result = run_scenario(minimal_scenario, build_streams, lambda _s, _r: [], tmp_path)
    assert result.events_path.read_bytes() == b""
    assert json.loads(result.summary_path.read_text())["events_processed"] == 0


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("duration_s", -1.0, "duration_s"),
        ("duration_s", float("nan"), "duration_s"),
        ("duration_s", "600", "duration_s"),
        ("master_seed", -5, "master_seed"),
        ("master_seed", 1.5, "master_seed"),
    ],
)
def test_invalid_scenario_is_rejected_before_any_file_is_written(
    tmp_path,
    minimal_scenario,
    build_streams,
    build_tiny_network,
    field,
    value,
    message,
):
    scenario = replace(minimal_scenario, **{field: value})
    output_dir = tmp_path / "out"
    with pytest.raises(ValueError, match=message):
        run_scenario(scenario, build_streams, build_tiny_network, output_dir)
    assert not output_dir.exists()


def test_unwritable_output_folder_raises_a_run_error(
    tmp_path, minimal_scenario, build_streams, build_tiny_network
):
    # A file where the output folder should be makes mkdir fail
    blocked = tmp_path / "out"
    blocked.write_text("not a folder")
    with pytest.raises(RunError, match="could not write run output"):
        run_scenario(minimal_scenario, build_streams, build_tiny_network, blocked)


def test_failing_component_leaves_no_complete_log(
    tmp_path, minimal_scenario, build_streams, build_tiny_network
):
    class FailingComponent:
        def start(self, scheduler):
            pass

        def handle(self, event, scheduler):
            raise RuntimeError("component failed")

    def build(scenario, streams):
        return [*build_tiny_network(scenario, streams), FailingComponent()]

    with pytest.raises(RuntimeError, match="component failed"):
        run_scenario(minimal_scenario, build_streams, build, tmp_path)
    assert not (tmp_path / EVENTS_FILE).exists()
    assert not (tmp_path / SUMMARY_FILE).exists()
