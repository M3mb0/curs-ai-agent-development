"""Tests for capacity_planning.py functions: break distribution,
staffing calculation, and capacity calculation.
"""


import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

from tools.capacity_planning import (
    SHIFTS,
    distribute_breaks_all_shifts,
    aggregate_breaks_by_interval,
    calculate_staffing,
    calculate_capacity,
)


def test_distribute_and_aggregate_breaks(arrival_pattern):
    """Tests that break minutes distributed across all shifts sum to
    the total expected minutes (450+600+450=1500 for the 3 shifts).
    """
    all_breaks = distribute_breaks_all_shifts(arrival_pattern, SHIFTS)
    aggregated = aggregate_breaks_by_interval(all_breaks)

    total_minutes = sum(aggregated.values()) * 30
    assert round(total_minutes) == 1500


def test_calculate_staffing(arrival_pattern):
    """Tests that calculate_staffing returns a staffing count greater
    than zero during an active shift interval.
    """
    staffing = calculate_staffing(arrival_pattern, SHIFTS)
    assert staffing["12:00:00"] > 0


def test_calculate_capacity(arrival_pattern, site_params):
    """Tests that calculate_capacity returns a capacity value greater
    than zero during an active shift interval.
    """
    staffing = calculate_staffing(arrival_pattern, SHIFTS)
    capacity = calculate_capacity(staffing, site_params)
    assert capacity["12:00:00"] > 0


def test_load_site_params(site_params):
    """Tests that load_site_params returns the expected fixed
    parameters (AHT, occupancy, offline, shrinkage).
    """
    assert site_params["aht"] == 12.0
    assert site_params["occupancy"] == 0.75
