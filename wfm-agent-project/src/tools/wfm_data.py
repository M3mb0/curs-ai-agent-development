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




if __name__ == "__main__":
    df = load_wfm_data("wfm-agent-project/data/wfm.xlsx")
    print(df.shape)
    
    metrics = get_daily_metrics(df, "Language 1", "LOB 1", "2015-10-20")
    print(metrics)

    sl = calculate_service_level(df, "Language 1", "LOB 1", "2015-10-20")
    print(sl)