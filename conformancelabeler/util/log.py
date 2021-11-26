import pandas as pd
import numpy as np
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.conversion.log import converter as log_converter



def read_xes(file: str):
	df = xes_importer.apply(file)
	df = log_converter.apply(df, variant=log_converter.Variants.TO_DATA_FRAME)
	return df

def count_traces(df: pd.DataFrame, case_id_col='case:concept:name') -> int:
	return len(df[case_id_col].unique())


def to_categorical(log: pd.DataFrame,
				   			cat_cols,
							  case_id_col='case:concept:name',
							  timestamp_col='time:timestamp',
							  resource_col='org:resource',
							  activity_col='concept:name',
							  ):

	assert case_id_col not in cat_cols, RuntimeError('case_id_col is in cat_cols')
	assert timestamp_col not in cat_cols, RuntimeError('timestamp_col is in cat_cols')

	if resource_col not in cat_cols:
		Warning('org_col not in cat_cols')

	if activity_col not in cat_cols:
		Warning('activity_col not in cat_cols')

	for col in cat_cols:
		log[col] = pd.factorize(log[col])[0] +1
	return log


def scale_numerical_features(log: pd.DataFrame, num_cols: list):
	log[num_cols] = log[num_cols].astype(float)
	log[num_cols] = (log[num_cols] - log[num_cols].mean()) / log[num_cols].std()
	return log


