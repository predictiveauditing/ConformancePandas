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
	dur = False
	if not "duration" in log.columns.tolist():
		log = event_duration(log, case_id_col=case_id_col, timestamp_col=timestamp_col)
	log["cumulative_duration"] = log.groupby(case_id_col)["duration"].apply(lambda x: x.cumsum())
	if dur:
		log = log.drop(columns=["duration"])
	return log

def total_duration(log: pd.DataFrame, case_id_col='case:concept:name', timestamp_col='time:timestamp'):
	dur = False
	if not "duration" in log.columns.tolist():
		log = event_duration(log, case_id_col=case_id_col, timestamp_col=timestamp_col)
		dur = True
	log["total_duration"] = log.groupby(case_id_col)["duration"].transform('sum')
	if dur:
		log = log.drop(columns=["duration"])
	return log


def get_time_attributes(log: pd.DataFrame,  timestamp_col='time:timestamp'):
	log["month"] = log[timestamp_col].dt.month
	log["weekday"] = log[timestamp_col].dt.weekday
	log["hour"] = log[timestamp_col].dt.hour
	return log

def cat_cols_one_hot_encoding(log: pd.DataFrame, case_id_col='case:concept:name',
							  timestamp_col='time:timestamp',
							  resource_col='org:resource',
							  activity_col='concept:name',
							  cat_col_list = None,
							  cat_col_pattern =None):
	if cat_col_list is not None:
		cat_cols = cat_col_list
	else:
		if cat_col_pattern is not None:
			cat_cols = [cat for cat in log.columns.tolist() if cat.startswith(cat_col_pattern)]
		else:
			cat_cols = log.columns.tolist()

		if case_id_col in cat_cols:
			cat_cols.remove(case_id_col)
		if timestamp_col in cat_cols:
			cat_cols.remove(timestamp_col)
		if resource_col not in cat_cols:
			cat_cols.append(resource_col)
		if activity_col not in cat_cols:
			cat_cols.append(activity_col)
	log1 = log[log.columns.difference(cat_cols).tolist()]
	log2 = pd.get_dummies(log[cat_cols].copy())
	log = pd.concat([log1, log2], axis=1)
	return log
