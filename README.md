# Pandas Conformance Checker and Data Labeler
This python package is a fork from bptlab/bpic implementing conformance checking and data labeling in pandas.

# Examples

# Import XES log
Follow the steps below, to import an XES event log as a pandas DataFrame:
````
from ConformancePandas.util.log import EventLog

path_to_log = './event_log.xes'
log = EventLog().read_xes(path_to_log)
´´´´´
