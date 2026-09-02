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


if __name__ == "__main__":
    df = load_wfm_data("wfm-agent-project/data/wfm.xlsx")
    print(df.shape)
    print(df.columns.tolist())
    print(df.head())