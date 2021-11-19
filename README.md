# Pandas Conformance Checker and Data Labeler
This python package is a fork from bptlab/bpic implementing conformance checking and data labeling in pandas.

# Examples

# Import XES log as pandas DataFrame
Follow the steps below, to import an XES event log as a pandas DataFrame:
````
from ConformancePandas.util.log import EventLog

el = EventLog(id_col='case:concept:name', activity_col='case:concept:name', timestamp_col='time:timestamp')
path_to_log = '<path_to_xes_file>'
log = el.read_xes(path_to_log)
````
