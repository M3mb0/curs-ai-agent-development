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
    """Distributes available break minutes across 30-minute intervals
    for a given shift, allocating more break time to lower-traffic
    intervals.

    Args:
        pattern: DataFrame with the arrival pattern (hour, offered_calls)
        shift: dict with the shift's start, end, and number of agents

    Returns:
        A dict mapping each eligible interval (as a string) to the
        number of break minutes allocated to it
    """ 
    shift_start = pd.to_datetime(shift["start"]).time()
    shift_end = pd.to_datetime(shift["end"]).time()

    filtered = pattern[(pattern["hour"] >= shift_start) & (pattern["hour"] <= shift_end)]
    no_breaks = filtered.iloc[2:-2]
    max_calls = no_breaks["offered_calls"].max()
    no_breaks["weight"] = max_calls - no_breaks["offered_calls"]
    total_weight = no_breaks["weight"].sum()
    total_break_minutes = shift["agents"] * 30
    break_allocation = {}
    for index, row in no_breaks.iterrows():
        fraction = row["weight"] / total_weight
        minutes = fraction * total_break_minutes
        break_allocation[str(row["hour"])] = float(round(minutes, 2))

    return break_allocation


def distribute_breaks_all_shifts(pattern: pd.DataFrame, shifts: list) -> dict:
    """Distributes break minutes across all shifts, combining results
    per shift name.

    Args:
        pattern: DataFrame with the arrival pattern (hour, offered_calls)
        shifts: list of shift dicts, each with start, end, and agents

    Returns:
        A dict mapping each shift name to its own break allocation dict
    """
    all_shifts_breaks = {}
    for shift in shifts:
        breaks = distribute_breaks_for_shift(pattern, shift)
        all_shifts_breaks[shift["name"]] = breaks

    return all_shifts_breaks

def aggregate_breaks_by_interval(all_shifts_breaks: dict, break_duration: int = 30) -> dict:
    """Aggregates break allocations across all shifts, per interval.

        Args:
            all_shifts_breaks: dict mapping shift names to their break
                allocation dicts (interval -> minutes)
            break_duration: length of a single break, in minutes (default: 30)

        Returns:
            A dict mapping each interval to the total number of agents
            on break at that time, combined across all shifts
    """
    aggregated = {}
    for shift_name, breaks in all_shifts_breaks.items():
        for interval, minutes in breaks.items():
            agents_on_break = minutes / break_duration
            aggregated[interval] = aggregated.get(interval, 0) + agents_on_break
    return aggregated
    


if __name__ == "__main__":
    pattern = load_arrival_pattern("wfm-agent-project/data/wfm.xlsx")
    print(pattern.shape)
    print(pattern.head())

    shift1 = SHIFTS[0]
    result = distribute_breaks_for_shift(pattern, shift1)
    print(result)

    result = distribute_breaks_for_shift(pattern, shift1)
    print(result)

    total_allocated = sum(result.values())
    print("Total allocated:", total_allocated)

    all_breaks = distribute_breaks_all_shifts(pattern, SHIFTS)
    print(all_breaks)

    aggregated = aggregate_breaks_by_interval(all_breaks)
    print(aggregated)