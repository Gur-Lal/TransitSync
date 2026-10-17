# AI contribution: 50% or more AI-generated
"""Shared test fixtures.

The tiny network, minimal scenario and stream factory here stand in for the
network model (Task 1.1.4, #97), the scenario configuration (Task 1.1.5, #98)
and the seed manager (Task 1.1.3, #9) until those are merged. They only
provide what the runner reads, so the tests do not depend on how those tasks
are built.
"""

from dataclasses import dataclass

import pytest

from simulator.engine.event_queue import Scheduler
from simulator.engine.events import Event, TrainArrival, TrainDeparture

MASTER_SEED = 20261017


@dataclass(frozen=True)
class MinimalScenario:
    """Smallest scenario the runner accepts."""

    duration_s: float = 600.0
    master_seed: int = MASTER_SEED


@dataclass(frozen=True)
class SeedOnlyStreams:
    """Stand-in for the random substreams. Records the seed it was built from.

    The tiny network draws no random values, so no generator is needed.
    """

    master_seed: int


@dataclass(frozen=True)
class StopVisit:
    """One train calling at one platform. Times in seconds."""

    train_id: str
    station_id: str
    platform_id: str
    arrival_s: float
    dwell_s: float


# One interchange (McGill), one REM line and one metro line (green). The REM
# platform ID is the real GTFS one; the metro platform ID is made up.
TINY_TIMETABLE = (
    StopVisit("green-1", "mcgill", "green-mcgill-west", 100.0, 20.0),
    StopVisit("rem-1", "mcgill", "STA_ZCD_BT_QUAI_01_MCG", 120.0, 30.0),
    StopVisit("green-2", "mcgill", "green-mcgill-west", 280.0, 20.0),
)


class TimetableComponent:
    """Runs trains exactly to the timetable, with no control strategy.

    Each train arrives on time and leaves after its dwell. Nobody is held and
    there are no disruptions, so every delay field is 0.
    """

    def __init__(self, visits: tuple[StopVisit, ...]) -> None:
        self._visits = {visit.train_id: visit for visit in visits}

    def start(self, scheduler: Scheduler) -> None:
        for visit in self._visits.values():
            scheduler.schedule(
                TrainArrival(
                    time_s=visit.arrival_s,
                    train_id=visit.train_id,
                    station_id=visit.station_id,
                    platform_id=visit.platform_id,
                    scheduled_s=visit.arrival_s,
                    disruption_delay_s=0.0,
                )
            )

    def handle(self, event: Event, scheduler: Scheduler) -> None:
        if not isinstance(event, TrainArrival):
            return
        visit = self._visits[event.train_id]
        departure_s = event.time_s + visit.dwell_s
        scheduler.schedule(
            TrainDeparture(
                time_s=departure_s,
                train_id=visit.train_id,
                station_id=visit.station_id,
                platform_id=visit.platform_id,
                scheduled_s=departure_s,
                disruption_delay_s=0.0,
                hold_s=0.0,
                boarded_count=0,
                alighted_count=0,
                onboard_load=0,
            )
        )


@pytest.fixture
def minimal_scenario():
    return MinimalScenario()


@pytest.fixture
def build_streams():
    """Stream factory with the signature the runner expects."""
    return SeedOnlyStreams


@pytest.fixture
def build_tiny_network():
    """Component factory that runs the tiny timetable."""

    def build(_scenario, _streams):
        return [TimetableComponent(TINY_TIMETABLE)]

    return build
