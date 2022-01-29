import pandas as pd
import numpy as np
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.conversion.log import converter as log_converter
import os
import pickle


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

def num_embeddings(log, cat_cols: list)->list:
	return list([log[col].nunique() for col in cat_cols])

def to_pickle(log, processed_path, num_cols, cat_cols,
		   case_id_col='case:concept:name', target_col='y'):

	case_list = log[case_id_col].unique().tolist()

	targets = list()
	x_num = list()
	x_cat = list()

	j = 0
	for case_id in case_list:
		case_data = log[log[case_id_col]==case_id]
		label = case_data.groupby(case_id_col)[target_col].first().values.tolist()
		targets += label
		case_data = case_data.drop(columns=[case_id_col, target_col])
		x_num.append(case_data[num_cols].values.astype(float).tolist())
		x_cat.append(case_data[cat_cols].values.astype(int).tolist())
		j += 1

		if j % 10000 == 0:
			print("progress: ", round(j/len(case_list)*100, 2), "% with ",j, " cases processed")
			np.save(file=os.path.join(processed_path, 'targets.npy'), arr=targets)
			with open(os.path.join(processed_path, 'x_num.pkl'), 'wb') as f:
				pickle.dump(x_num, f)
			with open(os.path.join(processed_path, 'x_cat.pkl'), 'wb') as f:
				pickle.dump(x_cat, f)
