import pandas as pd
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.algo.filtering.pandas.timestamp import timestamp_filter


def read_xes(file: str):
	df = xes_importer.apply(file)
	df = log_converter.apply(df, variant=log_converter.Variants.TO_DATA_FRAME)
	return df

def count_activity(df: pd.DataFrame, event_name: str, case_id_col='case:concept:name',
					   activity_col="concept:name") -> pd.DataFrame:

	df = df.merge(df.groupby([case_id_col])[activity_col]
				  .value_counts().unstack(fill_value=0
										  ).loc[:, event_name].reset_index()
				  .rename(columns={event_name: "Count " + event_name}),
				  on=[case_id_col], how="left")
	return df


def count_traces(df: pd.DataFrame, case_id_col='case:concept:name') -> int:
	return len(df[case_id_col].unique())


def timefilter(df: pd.DataFrame, start, end, timestamp_col='time:timestamp') -> pd.DataFrame:
	df = timestamp_filter.filter_traces_intersecting(df, start, end)
	df[timestamp_col] = pd.to_datetime(df[timestamp_col])
	df[timestamp_col] = df[timestamp_col].dt.tz_localize(None)
	return df


def filter_activity_count(log: pd.DataFrame, activity: str, min: int) -> pd.DataFrame:
	log = count_activity(log, activity)
	log = log[log["Count " + activity] >= min]
	log = log.drop(columns=["Count " + activity])
	return log


def event_duration(log: pd.DataFrame, case_id_col='case:concept:name', timestamp_col='time:timestamp'):
	log[timestamp_col] = log[timestamp_col].dt.tz_localize(None)
	log["duration"] = (log.groupby(case_id_col)[timestamp_col].diff()).dt.seconds.shift(-1)
	return log


def cumulative_duration(log: pd.DataFrame, case_id_col='case:concept:name', timestamp_col='time:timestamp'):
	if not "duration" in log.columns.tolist():
		log = event_duration(log, case_id_col=case_id_col, timestamp_col=timestamp_col)
	log["cumulative_duration"] = log.groupby(case_id_col)["duration"].apply(lambda x: x.cumsum())
	return log