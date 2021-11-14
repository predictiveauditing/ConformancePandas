import pandas as pd
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.algo.filtering.pandas.timestamp import timestamp_filter


class EventLog(object):
	def __init__(self, id="case:concept:name",
				 trace="concept:name",
				 timestamp="time:timestamp"):
		self.id = id
		self.trace = trace
		self.timestamp = timestamp

	def read_xes(self, file: str):
		df = xes_importer.apply(file)
		df = log_converter.apply(df, variant=log_converter.Variants.TO_DATA_FRAME)
		return df

	def read_feather(self, file: str):
		df = pd.read_feather(file)
		return df

	def count_activity(self, df: pd.DataFrame, count_activity:str) -> pd.DataFrame:
		df = df.merge(df.groupby([self.id])[self.trace]
					  .value_counts().unstack(fill_value=0
											  ).loc[:, count_activity].reset_index()
					  .rename(columns={count_activity: "Count "+ count_activity}),
					  on=[self.id], how="left")
		return df

	def count_traces(self, df: pd.DataFrame) -> int:
		return len(df[self.id].unique())

	def timefilter(self, df: pd.DataFrame, start, end) -> pd.DataFrame:
		df = timestamp_filter.filter_traces_intersecting(df,start, end)
		df[self.timestamp] = pd.to_datetime(df[self.timestamp])
		df[self.timestamp] = df[self.timestamp].dt.tz_localize(None)
		return df

	def filter_activity(self, log: pd.DataFrame, activity: str, min: int) -> pd.DataFrame:
		log = self.count_activity(log, activity)
		log = log[log["Count "+activity]>=min]
		log = log.drop(columns=["Count "+activity])
		return log






