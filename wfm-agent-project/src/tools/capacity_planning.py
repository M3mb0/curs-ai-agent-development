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
    

def distribute_breaks_for_shift_with_meetings(pattern: pd.DataFrame, shift: dict, meeting_times: list) -> dict:
    """Distributes available break minutes across 30-minute intervals
    for a given shift, excluding intervals that overlap with team
    meetings, and allocating more break time to lower-traffic
    intervals.

    Args:
        pattern: DataFrame with the arrival pattern (hour, offered_calls)
        shift: dict with the shift's start, end, and number of agents
        meeting_times: list of (start, end) string tuples, each
            representing a meeting period excluded from break eligibility

    Returns:
        A dict mapping each eligible interval (as a string) to the
        number of break minutes allocated to it
    """
    shift_start = pd.to_datetime(shift["start"]).time()
    shift_end = pd.to_datetime(shift["end"]).time()

    filtered = pattern[(pattern["hour"] >= shift_start) & (pattern["hour"] <= shift_end)]
    eligible = filtered.iloc[2:-2]

    for meeting_start_str, meeting_end_str in meeting_times:
        meeting_start = pd.to_datetime(meeting_start_str).time()
        meeting_end = pd.to_datetime(meeting_end_str).time()
        not_in_meeting = ~((eligible["hour"] >= meeting_start) & (eligible["hour"] <= meeting_end))
        eligible = eligible[not_in_meeting]

    max_calls = eligible["offered_calls"].max()
    eligible["weight"] = max_calls - eligible["offered_calls"]
    total_weight = eligible["weight"].sum()
    total_break_minutes = shift["agents"] * 30

    break_allocation = {}
    for index, row in eligible.iterrows():
        fraction = row["weight"] / total_weight
        minutes = fraction * total_break_minutes
        break_allocation[str(row["hour"])] = float(round(minutes, 2))

    return break_allocation


def distribute_breaks_all_shifts_with_meetings(pattern: pd.DataFrame, shifts: list, meeting_times: list) -> dict:
    """Distributes break minutes across all shifts, excluding meeting
    times, combining results per shift name.

    Args:
        pattern: DataFrame with the arrival pattern (hour, offered_calls)
        shifts: list of shift dicts, each with start, end, and agents
        meeting_times: list of (start, end) string tuples, each
            representing a meeting period excluded from break eligibility

    Returns:
        A dict mapping each shift name to its own break allocation dict
    """
    all_shifts_breaks = {}
    for shift in shifts:
        breaks = distribute_breaks_for_shift_with_meetings(pattern, shift, meeting_times)
        all_shifts_breaks[shift["name"]] = breaks
    return all_shifts_breaks

def active_agents_at(hour: str, shifts: list) -> int:
    """Calculates how many agents are active for each interval

    Args:
        hour: represent the hour when we do the checking
        shifts: list of shift dicts, each with start, end, and agents

    Returns:
        Total number of agents of a certain hour
    """
    hour_time = pd.to_datetime(hour).time()
    
    total = 0
    for shift in shifts:
        start_time = pd.to_datetime(shift["start"]).time()
        end_time = pd.to_datetime(shift["end"]).time()
        if hour_time >= start_time and hour_time <= end_time:
            total += shift["agents"]
    return total


def calculate_staffing(pattern: pd.DataFrame, shifts: list, meeting_times: list = None) -> dict:
    """Calculates effective staffing per interval, as active agents
    minus agents on break, optionally excluding meeting times from
    break eligibility.

    Args:
        pattern: DataFrame with the arrival pattern (hour, offered_calls)
        shifts: list of shift dicts, each with start, end, and agents
        meeting_times: optional list of (start, end) string tuples for
            meeting periods excluded from break eligibility; if None,
            breaks are distributed without excluding any meetings

    Returns:
        A dict mapping each interval (as a string) to the effective
        number of agents staffed (active minus on break)
    """
    if meeting_times:
        all_breaks = distribute_breaks_all_shifts_with_meetings(pattern, shifts, meeting_times)
    else:
        all_breaks = distribute_breaks_all_shifts(pattern, shifts)
    
    breaks_aggregated = aggregate_breaks_by_interval(all_breaks)
    
    staffing = {}
    for index, row in pattern.iterrows():
        hour_str = str(row["hour"])
        active = active_agents_at(hour_str, shifts)
        on_break = breaks_aggregated.get(hour_str, 0)
        staffing[hour_str] = active - on_break
    
    return staffing


def load_site_params(file_path: str) -> dict:
    """Loads the site capacity parameters from the Excel file.

    Args:
        file_path: path to the Excel file

    Returns:
        A dict with aht, occupancy, offline, and shrinkage values
    """
    df = pd.read_excel(
        file_path,
        sheet_name="Capacity Calculation",
        skiprows=6,
        nrows=1,
        usecols="B:F",
        header=None
    )
    df.columns = ["site", "aht", "occupancy", "offline", "shrinkage"]
    
    row = df.iloc[0]
    return {
        "aht": float(row["aht"]),
        "occupancy": float(row["occupancy"]),
        "offline": float(row["offline"]),
        "shrinkage": float(row["shrinkage"])
    }


def calculate_capacity(staffing: dict, params: dict) -> dict:
    """..."""
    capacity = {}
    for interval, staff in staffing.items():
        capacity_staff = (staff * (1 - params["offline"]) * (1 - params["shrinkage"]) * params["occupancy"] * 30) / params["aht"]
        capacity[interval] = round(capacity_staff, 2)
    return capacity


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

    print("-"*50)

    meetings = [("09:00", "10:30"), ("15:00", "16:30")]
    result_b = distribute_breaks_for_shift_with_meetings(pattern, shift1, meetings)
    print(result_b)

    print("-"*50)

    all_breaks_b = distribute_breaks_all_shifts_with_meetings(pattern, SHIFTS, meetings)
    
    for shift_name, breaks in all_breaks_b.items():
        total = sum(breaks.values())
        print(f"{shift_name}: total = {total}, agents = {total/30:.2f}")


    print(active_agents_at("11:30", SHIFTS))  
    print(active_agents_at("11:30:00", SHIFTS))    # testezi și cu secunde, ca să vezi diferența

    staffing_a = calculate_staffing(pattern, SHIFTS)  # fără meeting_times
    print("Task A staffing:", staffing_a)

    staffing_b = calculate_staffing(pattern, SHIFTS, [("09:00", "10:30"), ("15:00", "16:30")])
    print("Task B staffing:", staffing_b)

    params = load_site_params("wfm-agent-project/data/wfm.xlsx")
    print(params)

    capacity = calculate_capacity(staffing_a, params)
    print(capacity)