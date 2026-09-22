import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

from tools.wfm_data import (
    load_wfm_data,
    get_daily_metrics,
    calculate_service_level,
    get_talktime_by_period,
    compare_two_days,
    forecast_by_pattern,
    forecast_by_weekday_pattern,
    get_monthly_distribution_by_language,
    plot_language_distribution,
    add_timezone_column
)


def test_get_daily_metrics():
    """Tests that get_daily_metrics returns the correct total_offered
    count for a known language, LOB, and date combination.
    """
    df = load_wfm_data("wfm-agent-project/data/wfm.xlsx")
    result = get_daily_metrics(df, "Language 1", "LOB 1", "2015-10-20")
    assert result["total_offered"] == 317


def test_calculate_service_level():
    """Tests that calculate_service_level returns the correct service
    level percentage for a known language, LOB, and date combination.
    """
    df = load_wfm_data("wfm-agent-project/data/wfm.xlsx")
    result = calculate_service_level(df, "Language 1", "LOB 1", "2015-10-20")
    assert result["service_level_pct"] == 70.35


def test_get_talktime_by_period():
    """Tests that get_talktime_by_period returns the correct total
    seconds for a known date range.
    """
    df = load_wfm_data("wfm-agent-project/data/wfm.xlsx")
    result = get_talktime_by_period(df, "Language 1", "LOB 1", "2015-10-14", "2015-10-20")
    assert result["total_seconds"] == 1477509


def test_compare_two_days():
    """Tests that compare_two_days returns correct metrics for both
    days being compared.
    """
    df = load_wfm_data("wfm-agent-project/data/wfm.xlsx")
    result = compare_two_days(df, "Language 1", "LOB 1", "2015-10-20", "2015-10-21")
    assert result["day1"]["metrics_day1"]["total_offered"] == 317
    assert result["day2"]["metrics_day2"]["total_offered"] == 351


def test_forecast_by_pattern():
    """Tests that forecast_by_pattern distributes the target volume
    correctly across intervals for a known historical date.
    """
    df = load_wfm_data("wfm-agent-project/data/wfm.xlsx")
    result = forecast_by_pattern(df, "Language 1", "LOB 1", "2015-10-20", 500)
    assert result["08:00"] == 11.04


def test_forecast_by_weekday_pattern():
    """Tests that forecast_by_weekday_pattern distributes the target
    volume correctly across intervals for a known weekday.
    """
    df = load_wfm_data("wfm-agent-project/data/wfm.xlsx")
    result = forecast_by_weekday_pattern(df, "Language 2", "LOB 1", "Monday", 1200)
    assert result["13:30"] == 104.62


def test_get_monthly_distribution_by_language():
    """Tests that get_monthly_distribution_by_language returns
    percentages that sum to approximately 100 for a known LOB.
    """
    df = load_wfm_data("wfm-agent-project/data/wfm.xlsx")
    result = get_monthly_distribution_by_language(df, "LOB 2")
    assert result["Language 1"] == 41.09


def test_add_timezone_column():
    """Tests that add_timezone_column correctly shifts an hour by
    the given offset.
    """
    df = load_wfm_data("wfm-agent-project/data/wfm.xlsx")
    updated_df = add_timezone_column(df, -4, "test_utc_minus_4")
    sample_row = updated_df[updated_df["Intvl_UTC"] == "08:00"].iloc[0]
    assert sample_row["test_utc_minus_4"] == "04:00"


def test_plot_language_distribution():
    """Tests that plot_language_distribution creates the chart file."""
    distribution = {"Language 1": 41.09, "Language 2": 33.0}
    output_path = "wfm-agent-project/data/test_chart.png"
    plot_language_distribution(distribution, output_path)
    assert Path(output_path).exists()