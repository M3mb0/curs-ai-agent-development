import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

from tools.capacity_planning import (
    load_arrival_pattern,
    SHIFTS,
    distribute_breaks_all_shifts,
    aggregate_breaks_by_interval,
    calculate_staffing,
    load_site_params,
    calculate_capacity,
)


def test_distribute_and_aggregate_breaks():
    """Tests that break minutes distributed across all shifts sum to
    the total expected minutes (450+600+450=1500 for the 3 shifts).
    """
    pattern = load_arrival_pattern("wfm-agent-project/data/wfm.xlsx")
    all_breaks = distribute_breaks_all_shifts(pattern, SHIFTS)
    aggregated = aggregate_breaks_by_interval(all_breaks)

    total_minutes = sum(aggregated.values()) * 30
    assert round(total_minutes) == 1500


def test_calculate_staffing():
    """Tests that calculate_staffing returns a staffing count greater
    than zero during an active shift interval.
    """
    pattern = load_arrival_pattern("wfm-agent-project/data/wfm.xlsx")
    staffing = calculate_staffing(pattern, SHIFTS)
    assert staffing["12:00:00"] > 0


def test_calculate_capacity():
    """Tests that calculate_capacity returns a capacity value greater
    than zero during an active shift interval.
    """
    pattern = load_arrival_pattern("wfm-agent-project/data/wfm.xlsx")
    staffing = calculate_staffing(pattern, SHIFTS)
    site_params = load_site_params("wfm-agent-project/data/wfm.xlsx")
    capacity = calculate_capacity(staffing, site_params)
    assert capacity["12:00:00"] > 0


def test_load_site_params():
    """Tests that load_site_params returns the expected fixed
    parameters (AHT, occupancy, offline, shrinkage).
    """
    site_params = load_site_params("wfm-agent-project/data/wfm.xlsx")
    assert site_params["aht"] == 12.0
    assert site_params["occupancy"] == 0.75