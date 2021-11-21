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
from auditencoder.conformance_checking.rule_check import RuleChecker

rulechecker = RuleChecker(id_col='case:concept:name', 
              activity_col='case:concept:name', 
              timestamp_col='time:timestamp')
         
print(rulechecker.check_precedence(log, 'Record Goods Receipt', 'Clear Invoice', label=False))

```
``
Conformance checking via precedence rules of 'Clear Invoice' requiring 'Record Goods Receipt' with 5665 violations: 3.08% of all cases.
``

## Labeling of Incompliance and Position within Pandas DataFrame
Returns an extra column signalling incompliance and position of the violated rule.

```python
log = rulechecker.check_precedence(log, 'Record Goods Receipt', 'Clear Invoice', label=True)
```

## Sequence Encoding
Traces with high risk are encoded with priority.
```python
r = list([0.6, 0.2, 0.15, 0.05])
label_risk_dict = dict(zip(label_list, r))

log = rulechecker.encode_traces(log,label_risk_dict = label_risk_dict, 
                                        prefix_reduction=1,
                                        min_trace_length=4, 
                                        drop_help_cols=True)

```


