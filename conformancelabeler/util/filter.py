import pandas as pd
from pm4py.algo.filtering.pandas.timestamp import timestamp_filter
from .metrics import get_activity_count


def timefilter(df: pd.DataFrame, start, end, timestamp_col='time:timestamp') -> pd.DataFrame:
    df = timestamp_filter.filter_traces_intersecting(df, start, end)
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    df[timestamp_col] = df[timestamp_col].dt.tz_localize(None)
    return df


def filter_by_min_activity(log: pd.DataFrame, activity: str, min: int) -> pd.DataFrame:
    log = get_activity_count(log, activity)
    log = log[log["Count " + activity] >= min]
    log = log.drop(columns=["Count " + activity])
    return log