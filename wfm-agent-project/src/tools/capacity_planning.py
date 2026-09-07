import pandas as pd

SHIFTS = [
    {"name": "Shift 1", "start": "07:00", "end": "15:00", "agents": 15},
    {"name": "Shift 2", "start": "10:30", "end": "18:30", "agents": 20},
    {"name": "Shift 3", "start": "14:30", "end": "22:30", "agents": 15}
]


def load_arrival_pattern(file_path: str) -> pd.DataFrame:
    """Loads the WFM planning breaks data from the Excel file.
    
        Args:
            file_path: path to the Excel file
    
        Returns:
            A pandas DataFrame with the planing breaks data
        """
    df = pd.read_excel(
        file_path, 
        sheet_name="Planning breaks",
        skiprows=12,
        usecols="B:C",
        nrows=48,
        header=None
    )
    df.columns = ["hour", "offered_calls"]
    return df


def distribute_breaks_for_shift(pattern: pd.DataFrame, shift: dict) -> dict:
    shift_start = pd.to_datetime(shift["start"]).time()
    shift_end = pd.to_datetime(shift["end"]).time()

    filtered = pattern[(pattern["hour"] >= shift_start) & (pattern["hour"] <= shift_end)]
    return filtered


if __name__ == "__main__":
    pattern = load_arrival_pattern("wfm-agent-project/data/wfm.xlsx")
    print(pattern.shape)
    print(pattern.head())

    shift1 = SHIFTS[0]
    result = distribute_breaks_for_shift(pattern, shift1)
    print(result) 