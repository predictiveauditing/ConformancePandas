# Pandas Conformance Checker
This python package is a fork from bptlab/bpic implementing conformance checking and data labeling in pandas.

# Examples

## Import XES log as pandas DataFrame
Follow the steps below, to import an XES event log as a pandas DataFrame:
```python
from ConformancePandas.util.log import EventLog

eventlog = EventLog(id_col='case:concept:name', 
              activity_col='case:concept:name', 
              timestamp_col='time:timestamp')
path_to_log = '<path_to_xes_file>'
log = eventlog.read_xes(path_to_log)
```

## Conformance Checking and Labeling
Enabeling labeling for exact point of violation in the trace:

```python
from ConformancePandas.conformance_checking.rule_check import RuleChecker

rulechecker = RuleChecker(id_col='case:concept:name', 
              activity_col='case:concept:name', 
              timestamp_col='time:timestamp')
         
log = rulechecker.check_precedence(log, 'Record Goods Receipt', 'Clear Invoice', label=True)

```
