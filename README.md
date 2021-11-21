# Audit Conformance Encoder
This python package is a fork from bptlab/bpic implementing conformance checking and data labeling in pandas for predictive process mining.

# Installation
``
pip install git+https://github.com/timbaessler/ConformancePandas.git@master
``

# Examples

## Import XES log as pandas DataFrame
Follow the steps below, to import an XES event log as a pandas DataFrame:
```python
from conformancepandas.util.log import EventLog

eventlog = EventLog(id_col='case:concept:name', 
              activity_col='case:concept:name', 
              timestamp_col='time:timestamp')
path_to_log = '<path_to_xes_file>'
log = eventlog.read_xes(path_to_log)
```

## Conformance Checking
Enabeling labeling for exact point of violation in the trace:

```python
from conformancepandas.conformance_checking.rule_check import RuleChecker

rulechecker = RuleChecker(id_col='case:concept:name', 
              activity_col='case:concept:name', 
              timestamp_col='time:timestamp')
         
print(rulechecker.check_precedence(log, 'Record Goods Receipt', 'Clear Invoice', label=False))

```
``
Conformance checking via precedence rules of 'Clear Invoice' requiring 'Record Goods Receipt' with 5665 violations: 3.08% of all cases.
``

## Labeling for Predictive Process Mining

```python
log = rulechecker.check_precedence(log, 'Record Goods Receipt', 'Clear Invoice', label=True)
```

