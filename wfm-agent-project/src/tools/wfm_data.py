import pandas as pd


def load_wfm_data(file_path: str) -> pd.DataFrame:
    """Loads the WFM intraday data from the Excel file.

    Args:
        file_path: path to the Excel file

    Returns:
        A pandas DataFrame with the Intraday_raw data
    """
    df = pd.read_excel(file_path, sheet_name="Intraday_raw")
    return df

def get_daily_metrics(df: pd.DataFrame, language: str, lob: str, date: str) -> dict:
    """Calculates the totals of offered, handled, and abandoned calls.

    Args:
        df: DataFrame created from the Excel file
        language: language to filter by
        lob: LOB (line of business) to filter by
        date: the date to filter by

    Returns:
        A dictionary with total_offered, total_handled, and total_abandoned 
    """

    str_date = pd.to_datetime(date)    
    filtered = df[(df["Dim_Language"]==language) & (df["LOB"]==lob) & (df["repdate"]==str_date)]


    return {
        "total_offered": int(filtered["offered"].sum()),
        "total_handled": int(filtered["handled"].sum()),
        "total_abandoned": int(filtered["abandoned"].sum())
    }
    

def calculate_service_level(df: pd.DataFrame, language: str, lob: str, date: str) -> dict:
    """Calculates service level and abandon rate percentages.

    Args:
        df: DataFrame created from the Excel file
        language: language to filter by
        lob: LOB (line of business) to filter by
        date: the date to filter by

    Returns:
        A dictionary with service_level_pct and abandon_rate_pct
    """
    str_date = pd.to_datetime(date)
    filtered = df[(df["Dim_Language"] == language) & (df["LOB"] == lob) & (df["repdate"] == str_date)]

    total_offered = int(filtered["offered"].sum())
    total_callswisl = int(filtered["callswisl"].sum())
    total_abandoned = int(filtered["abandoned"].sum())

    if total_offered == 0:
        return {
            "service_level_pct": None,
            "abandon_rate_pct": None,
            "message": f"No calls were received on {date}"
        }

    service_level = total_callswisl / total_offered * 100
    abandon_rate = total_abandoned / total_offered * 100

    return {
        "service_level_pct": round(service_level, 2),
        "abandon_rate_pct": round(abandon_rate, 2)
    }


def get_talktime_by_period(df: pd.DataFrame, language: str, lob: str, start_date: str, end_date: str) -> dict:
    """Calculates the total talk time for a certain period.

    Args:
        df: DataFrame created from the Excel file
        language: language to filter by
        lob: LOB (line of business) to filter by
        start_date: the start date to filter by
        end_date: the end date to filter by

    Returns:
        A dictionary with total talk time in seconds, minutes, and hours
    """
    str_start_date = pd.to_datetime(start_date)
    str_end_date = pd.to_datetime(end_date)
    filtered = df[(df["repdate"] >= str_start_date) & (df["repdate"] <= str_end_date) & (df["Dim_Language"] == language) & (df["LOB"] == lob)]
    
    total_talktime_seconds = int(filtered["tottalktime"].sum())
    
    return {
        "total_seconds": total_talktime_seconds,
        "total_minutes": round(total_talktime_seconds / 60, 2),
        "total_hours": round(total_talktime_seconds / 3600, 2)
    }


def get_monthly_distribution_by_language(df: pd.DataFrame, lob: str) -> dict:
    """Calculates the percentage distribution of offered calls by language.

    Args:
        df: DataFrame created from the Excel file
        lob: LOB (line of business) to filter by

    Returns:
        A dictionary with each language's percentage of total offered calls
    """
    filtered = df[df["LOB"] == lob]
    
    sum_by_language = filtered.groupby("Dim_Language")["offered"].sum()
    total = int(filtered["offered"].sum())
    
    result = {}
    for language, calls in sum_by_language.items():
        result[language] = round(calls / total * 100, 2)
    
    return result


def add_timezone_column(df: pd.DataFrame, offset_hours: int, column_name: str) -> pd.DataFrame:
    """Adds a new column with times shifted by a given number of hours.

    Args:
        df: DataFrame created from the Excel file
        offset_hours: how many hours to shift (positive or negative)
        column_name: name of the new column to create

    Returns:
        The same DataFrame, with the new shifted-time column added
    """
    time_as_datetime = pd.to_datetime(df["Intvl_UTC"], format="%H:%M")
    shifted = time_as_datetime + pd.Timedelta(hours=offset_hours)
    df[column_name] = shifted.dt.strftime("%H:%M")
    return df


def compare_two_days(df: pd.DataFrame, language: str, lob: str, date1: str, date2: str) -> dict:
    """Comparing 2 days metrics
    
    Args:
        df: DataFrame created from the Excel file
        language: language to filter by
        lob: LOB (line of business) to filter by
        date1: date to be compared with
        date2: date to be compared with

    Return:
        A dict with the comparation betwen the 2 days
    """
    metrics_day1 = get_daily_metrics(df, language, lob, date1)
    metrics_day2 = get_daily_metrics(df, language, lob, date2)
    
    sl_day1 = calculate_service_level(df, language, lob, date1)
    sl_day2 = calculate_service_level(df, language, lob, date2)
    
    metrics_difference = {k: round((metrics_day2[k] - metrics_day1[k]), 2) for k in metrics_day2}
    sl_difference = {k: round((sl_day2[k] - sl_day1[k]), 2) for k in sl_day2}
    return {
        "day1": {
           "metrics_day1": metrics_day1,
           "sl_day1": sl_day1
        },
        "day2": {
            "metrics_day2": metrics_day2,
            "sl_day2": sl_day2
        },
        "metric_difference": metrics_difference,
        "sl_difference": sl_difference
    }
    

if __name__ == "__main__":
    df = load_wfm_data("wfm-agent-project/data/wfm.xlsx")
    print(df.shape)
    
    metrics = get_daily_metrics(df, "Language 1", "LOB 1", "2015-10-20")
    print(metrics)

    sl = calculate_service_level(df, "Language 1", "LOB 1", "2015-10-20")
    print(sl)

    tt = get_talktime_by_period(df, "Language 1", "LOB 1", "2015-10-14", "2015-10-20")
    print(tt)

    dist = get_monthly_distribution_by_language(df, "LOB 1")
    print(dist)

    for key in dist.keys():
        print(key, type(key))

    print(type(df["Intvl_UTC"].iloc[0]))
    print(df["Intvl_UTC"].iloc[0])

    df = add_timezone_column(df, -4, "Intvl_UTC-4")
    print(df[["Intvl_UTC", "Intvl_UTC-4"]].head())

    df = add_timezone_column(df, 5, "Intvl_UTC+5")
    print(df[["Intvl_UTC", "Intvl_UTC+5"]].head())

    comparison = compare_two_days(df, "Language 1", "LOB 1", "2015-10-20", "2015-10-21")
    print(comparison)