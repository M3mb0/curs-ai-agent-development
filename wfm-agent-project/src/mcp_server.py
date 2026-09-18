import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from mcp.server.mcpserver import MCPServer
from tools.wfm_data import (
    load_wfm_data,
    get_daily_metrics,
    calculate_service_level,
    get_talktime_by_period,
    get_monthly_distribution_by_language,
    add_timezone_column,
    compare_two_days,
    forecast_by_pattern,
    forecast_by_weekday_pattern,
)

mcp = MCPServer("wfm-agent")

data_path = Path(__file__).parent.parent / "data" / "wfm.xlsx"
df = load_wfm_data(str(data_path))


@mcp.tool()
def daily_metrics(language: str, lob: str, date: str) -> dict:
    """Retrieves daily call metrics (offered, handled, abandoned) for
    a given language, LOB, and date.

    Args:
        language: the language to filter by (e.g. "Language 1")
        lob: the LOB to filter by (e.g. "LOB 1")
        date: the date to filter by, in YYYY-MM-DD format

    Returns:
        A dictionary with total_offered, total_handled, and total_abandoned
    """
    return get_daily_metrics(df, language, lob, date)


@mcp.tool()
def service_level(language: str, lob: str, date: str) -> dict:
    """Retrieves service level and abandon rate percentages for a
    given language, LOB, and date.

    Args:
        language: the language to filter by (e.g. "Language 1")
        lob: the LOB to filter by (e.g. "LOB 1")
        date: the date to filter by, in YYYY-MM-DD format

    Returns:
        A dictionary with service_level_pct and abandon_rate_pct
    """
    return calculate_service_level(df, language, lob, date)


@mcp.tool()
def talktime(language: str, lob: str, start_date: str, end_date: str) -> dict:
    """Retrieves total talk time for a date range.

    Args:
        language: the language to filter by
        lob: the LOB to filter by
        start_date: start of the range, YYYY-MM-DD
        end_date: end of the range, YYYY-MM-DD

    Returns:
        A dictionary with total_seconds, total_minutes, total_hours
    """
    return get_talktime_by_period(df, language, lob, start_date, end_date)


@mcp.tool()
def distribution(lob: str) -> dict:
    """Retrieves the percentage distribution of calls by language,
    for a given LOB.

    Args:
        lob: the LOB to filter by

    Returns:
        A dictionary mapping each language to its percentage of calls
    """
    return get_monthly_distribution_by_language(df, lob)


@mcp.tool()
def timezone_shift(offset_hours: int, column_name: str) -> str:
    """Adds a timezone-shifted column and returns a text summary.

    Args:
        offset_hours: how many hours to shift (can be negative)
        column_name: name for the new column

    Returns:
        A short confirmation message
    """
    add_timezone_column(df, offset_hours, column_name)
    return f"Column '{column_name}' added with a {offset_hours}h shift."


@mcp.tool()
def compare_days(language: str, lob: str, date1: str, date2: str) -> dict:
    """Compares WFM metrics between two days.

    Args:
        language: the language to filter by
        lob: the LOB to filter by
        date1: first date, YYYY-MM-DD
        date2: second date, YYYY-MM-DD

    Returns:
        A dict with both days' metrics and the differences
    """
    return compare_two_days(df, language, lob, date1, date2)


@mcp.tool()
def forecast(language: str, lob: str, historical_date: str, target_volume: int) -> dict:
    """Forecasts call volume distribution based on a historical date's pattern.

    Args:
        language: the language to filter by
        lob: the LOB to filter by
        historical_date: the date whose pattern to use, YYYY-MM-DD
        target_volume: total estimated call volume to distribute

    Returns:
        A dictionary with the forecasted volume for each interval
    """
    return forecast_by_pattern(df, language, lob, historical_date, target_volume)


@mcp.tool()
def forecast_weekday(language: str, lob: str, weekday: str, target_volume: int) -> dict:
    """Forecasts call volume distribution based on a weekday's aggregated pattern.

    Args:
        language: the language to filter by
        lob: the LOB to filter by
        weekday: the day of week (e.g. "Monday")
        target_volume: total estimated call volume to distribute

    Returns:
        A dictionary with the forecasted volume for each interval
    """
    return forecast_by_weekday_pattern(df, language, lob, weekday, target_volume)


if __name__ == "__main__":
    mcp.run()