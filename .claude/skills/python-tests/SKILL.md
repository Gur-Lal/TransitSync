---
name: "python-tests"
description: "Write or review pytest tests for TransitSync simulator, API and data scripts, including Hypothesis property tests, seeded determinism checks and hand-calculated expected values."
---

# TransitSync Python tests

Use this whenever a task adds or changes Python code in `simulator/`, `api/` or `scripts/`. Every task ships with tests.

## Layout and tools

- pytest, with tests in `tests/` mirroring the source tree (`simulator/engine/queue.py` -> `tests/simulator/engine/test_queue.py`)
- Hypothesis for properties that must hold for any input
- Shared fixtures in `tests/conftest.py`: a tiny network (one REM line, one metro line, one interchange), a fixed master seed, a minimal scenario config
- Run with `pytest -q`. Slow tests (full runs, sweeps) get `@pytest.mark.slow` and are skipped by default in local runs but run in CI

## Three kinds of tests

### 1. Hand-calculated unit tests
For any formula, work the expected value out by hand first and put the working in a comment above the assert.

```python
def test_break_even_holds_when_benefit_exceeds_cost():
    # N(h)=40 caught, H=450 s, w_wait=1 -> benefit = 18000 pax-s
    # L=150 onboard, h=60 s, w_onboard=1, downstream=0 -> cost = 9000 pax-s
    assert should_hold(n_caught=40, headway=450, load=150, hold=60) is True
```

Never compute the expected value with the same function under test.

### 2. Property tests (Hypothesis)
Use for the simulator invariants. Each one should run on generated scenarios:

- Minimum gap between consecutive trains is never violated
- No hold exceeds the maximum hold cap
- The one-hop rule is never broken (no hold triggered by a train that was itself held for a connection)
- Passenger counts are conserved: generated = boarded + still waiting + left system
- Event timestamps are non-decreasing in the event log
- Transfer arrivals are never a constant rate (they cluster after train arrivals)

Keep generated scenarios small (short horizon, few trains) so each example runs in milliseconds. Use `@settings(max_examples=...)` deliberately.

### 3. Determinism and reproducibility tests
- Same scenario + same master seed -> byte-identical event log. Compare the full output, not summary metrics
- Changing one random substream (for example walking times) leaves the others unchanged
- Two strategies run with the same seed see identical exogenous randomness (common random numbers)

## Rules

- No unseeded randomness anywhere in tests. Build generators from `numpy.random.SeedSequence` like the simulator does
- Tests must not touch Supabase or the network. Use small fixture CSVs or DataFrames instead of real GTFS tables
- Times in seconds, costs in passenger-seconds, same as the simulator
- One behaviour per test, named `test_<what>_<condition>`
- When a bug is fixed, add a regression test that fails on the old code
- Floating point: use `pytest.approx` with an explicit tolerance and say why that tolerance is enough

## Before finishing

- Run the whole suite, not just the new file
- Report which tests were added and what each one protects against