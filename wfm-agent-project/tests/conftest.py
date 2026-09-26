"""Shared pytest fixtures: load the wfm.xlsx sheets once per test session."""


import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent / "src"))

from tools.wfm_data import load_wfm_data
from tools.capacity_planning import load_arrival_pattern, load_site_params

DATA_PATH = "wfm-agent-project/data/wfm.xlsx"


@pytest.fixture(scope="session")
def wfm_df():
    """Loads the Intraday_raw sheet once for the whole session.

    Tests that mutate the DataFrame must work on a copy.

    Returns:
        pd.DataFrame: Raw intraday WFM data.
    """
    return load_wfm_data(DATA_PATH)


@pytest.fixture(scope="session")
def arrival_pattern():
    """Loads the arrival pattern once for the whole session.

    Returns:
        pd.DataFrame: Offered calls per interval.
    """
    return load_arrival_pattern(DATA_PATH)


@pytest.fixture(scope="session")
def site_params():
    """Loads the site parameters once for the whole session.

    Returns:
        dict: AHT, occupancy, offline and shrinkage parameters.
    """
    return load_site_params(DATA_PATH)
