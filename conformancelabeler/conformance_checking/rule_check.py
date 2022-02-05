import numpy as np
import pandas as pd
import sys


class EventLog(object):
    def __init__(self, id_col="case:concept:name",
                 activity_col="concept:name",
                 timestamp_col="time:timestamp"):
        self.id = id_col
        self.trace = activity_col
        self.timecol = timestamp_col


class RuleChecker(EventLog):

    def __init__(self, id="case:concept:name", trace="concept:name", timestamp="time:timestamp"):
        EventLog.__init__(self, id, trace, timestamp)
        self.violations = int(0)
        self.cases = int(0)
        self.rule = str()
        self.label_list = list()
        self.checked_activity = str()
        self.case_id_dict = dict()
        self.compliant_case_id_dict = dict()

    def get_percentage(self) -> float:
        return round((self.violations / self.cases) * 100, 2)

    def get_compliant_cases(self, log):
        self.compliant_case_id_dict = dict()
        incompliant_cases = list(self.case_id_dict.keys())
        for case_id, events in log.groupby([self.id])[self.trace].apply(list).items():
            if case_id not in incompliant_cases:
                self.compliant_case_id_dict[case_id] = len(events)

    def label_sequences(self, log: pd.DataFrame) -> pd.DataFrame:
        self.get_compliant_cases(log)
        self.label_name = "_".join([self.rule, self.checked_activity])
        self.label_list.append(self.label_name)
        self.pos_name = "_".join(["Pos", self.rule, self.checked_activity])
        log[self.label_name] = np.where(log[self.id].isin(self.case_id_dict.keys()), 1, 0)
        log = log.merge(pd.DataFrame({self.id: list(self.case_id_dict.keys())
                                               + list(self.compliant_case_id_dict.keys()),
                                      self.pos_name: (list(self.case_id_dict.values())
                                                      + list(self.compliant_case_id_dict.values()))}),
                        on=[self.id], how="left")
        return log


    def encode_traces(self, log: pd.DataFrame, single_rule=False, prefix_reduction=1,
                      min_trace_length=2, max_trace_length=None, drop_help_cols=True,
                      hierarchical=False) -> pd.DataFrame:
        y_dict = dict()
        y_pos = dict()
        if single_rule is False:
            label_list = self.label_list
        else:
            label_list = [self.label_name]
        pos_cols = list(["Pos_" + str(label) for label in label_list])
        log2 = log.groupby(self.id).agg(dict(zip(label_list + pos_cols,
                                                 ["first"] * (len(label_list) * 2))))
        idx = log2.index
        rows = log2.values

        if hierarchical:
            for i, case_id in enumerate(idx):
                tracked = False
                row = rows[i]
                for j, val in enumerate(row[:len(label_list)]):
                    if val == 1:
                        y_dict[case_id] = j + 1
                        y_pos[case_id] = row[len(label_list):][j]
                        tracked = True
                        break
                    if not tracked:
                        y_dict[case_id] = 0
                        y_pos[case_id] = np.max(row[len(label_list):])
        else:
            for i, case_id in enumerate(idx):
                row = rows[i]
                if len(label_list) > 1:
                    label = row[:len(label_list)]
                    pos = row[len(label_list):]
                    if 1 in label:
                        y_dict[case_id] = 1
                        y_pos[case_id] = np.min(pos)
                    else:
                        y_dict[case_id] = 0
                        y_pos[case_id] = np.min(pos)
                else:
                    y_dict[case_id] = row[0]
                    y_pos[case_id] = row[1]

        log = log.merge(pd.DataFrame({self.id: y_dict.keys(),
                                      "y": y_dict.values(),
                                      "y_pos": y_pos.values()}),
                        on=[self.id], how="left")

        log["y_pos"] = log.y_pos - prefix_reduction
        log = log[log["y_pos"] >= min_trace_length]
        if not max_trace_length is None:
            log = log[log["y_pos"] <= max_trace_length + prefix_reduction]
        log["idx"] = 0
        log["idx"] = log.groupby([self.id])["idx"].cumcount()
        log = log[log.idx < log.y_pos]
        if drop_help_cols:
            log = log.drop(columns=label_list + pos_cols + ["idx", "y_pos"])
        return log

    def check_cardinality(self, log: pd.DataFrame, activity: str, upper: int, lower: int,
                          label=True, encode=False,
                          prefix_reduction=1, min_trace_length=2,
                          max_trace_length=None, drop_help_cols=True):
        self.rule = "cardinality"
        self.checked_activity = "_".join([activity, str(upper), str(lower)])
        self.cases = 0
        self.violations = 0
        self.case_id_dict = dict()

        for case_id, events in log.groupby([self.id])[self.trace].apply(list).items():
            self.cases += 1
            tracked = False

            counter = 0
            for i, event in enumerate(events):
                if event == activity:
                    counter += 1
                    if counter > upper:
                        if not tracked:
                            self.violations += 1
                            self.case_id_dict[case_id] = i
                            tracked = True

                if counter < lower and i == len(events) - 1 and not tracked:
                    # lower cardinality incompliance only gets labeled  when the trace is finalized
                    tracked = True
                    self.violations += 1
                    self.case_id_dict[case_id] = len(events)

        msg = ("Conformance checking via cardinality rules of '" + activity
               + "' with " + str(self.violations) + " violations: " + str(self.get_percentage())
               + "% of all cases.")

        if label:
            print()
            print(msg)
            print()
            log = self.label_sequences(log)
            if encode:
                log = self.encode_traces(log, single_rule=True,
                                         prefix_reduction=prefix_reduction,
                                         min_trace_length=min_trace_length,
                                         max_trace_length=max_trace_length,
                                         drop_help_cols=drop_help_cols)
            return log
        elif not label:
            return msg

    def check_order(self, log, first: str, second: str, label=True, encode=False,
                    prefix_reduction=1, min_trace_length=2,
                    max_trace_length=None, drop_help_cols=True):
        """
        Check the order of the given activities.

        :param log: event log
        :param first: activity
        :param second: activity
        :return: report
        """
        self.rule = "order"
        self.checked_activity = first + "_" + second
        self.cases = 0
        self.violations = 0
        self.case_id_dict = dict()

        for case_id, events in log.groupby([self.id])[self.trace].apply(list).items():
            first_stack = []
            if first in events and second in events:
                self.cases += 1
                tracked = False
                for i, event in enumerate(events):
                    if event == first:
                        first_stack.append(event)
                    elif event == second and len(first_stack) == 0 and not tracked:
                        tracked = True
                        self.violations += 1
                        self.case_id_dict[case_id] = i
        msg = ("Conformance checking via order rule of first '" + first + "' followed by '" + second
               + "' with " + str(self.violations) + " violations: " + str(self.get_percentage())
               + "% of all cases.")
        if label:
            print()
            print(msg)
            print()
            log = self.label_sequences(log)
            if encode:
                log = self.encode_traces(log, single_rule=True,
                                         prefix_reduction=prefix_reduction,
                                         min_trace_length=min_trace_length,
                                         max_trace_length=max_trace_length,
                                         drop_help_cols=drop_help_cols)
            return log
        elif not label:
            return msg

    def check_response(self, log, request: str, response: str,
                       single_occurrence=False, label=True, encode=False,
                       prefix_reduction=1, min_trace_length=2,
                       max_trace_length=None, drop_help_cols=True):

        """
        Check response requirements of the given activity.


        :param log: event log
        :param request: activity which expects a requested activity
        :param response: requested activity
        :param single_occurrence: specifies whether a single occurrence of the
        responding activity already satisfies the rule
        :return: report
        """
        self.rule = "response"
        self.checked_activity = request + "_" + response
        self.cases = 0
        self.violations = 0
        self.case_id_dict = dict()

        for case_id, events in log.groupby([self.id])[self.trace].apply(list).items():
            req_stack = []
            tracked = False
            if request in events:
                self.cases += 1
                if single_occurrence:
                    if response in events:
                        req_idx = events[::-1].index(request)
                        res_idx = events[::-1].index(response)
                        if req_idx < res_idx:
                            self.violations += 1
                            self.case_id_dict[case_id] = len(events)
                    else:
                        self.violations += 1
                else:
                    for event in events:
                        if event == request:
                            req_stack.append(event)
                        elif event == response and len(req_stack) > 0:
                            req_stack.pop()
                    if len(req_stack) > 0:
                        self.violations += 1
                        self.case_id_dict[case_id] = len(events)

        msg = ("Conformance checking via response rules of '" + request + "' requiring '" + response
               + "' with " + str(self.violations) + " violations: " + str(self.get_percentage())
               + "% of all cases.")
        if label:
            print()
            print(msg)
            print()
            log = self.label_sequences(log)
            if encode:
                log = self.encode_traces(log, single_rule=True,
                                         prefix_reduction=prefix_reduction,
                                         min_trace_length=min_trace_length,
                                         max_trace_length=max_trace_length,
                                         drop_help_cols=drop_help_cols)
            return log
        elif not label:
            return msg

    def check_precedence(self, log: pd.DataFrame, preceding: str, request: str,
                         single_occurrence=False, label=False, encode=False,
                         prefix_reduction=1, min_trace_length=2,
                         max_trace_length=None, drop_help_cols=True):
        """
        Check precedence requirements of the given activity.

        :param log: event log
        :param preceding: activity that should precede the requesting activity
        :param request: requesting activity
        :param single_occurrence: specifies whether a single occurrence of the
        preceding activity already satisfies the rule
        :return: report
        """

        self.rule = "precedence"
        self.checked_activity = preceding + "_" + request
        self.cases = 0
        self.violations = 0
        self.case_id_dict = dict()

        for case_id, events in log.groupby([self.id])[self.trace].apply(list).items():
            if request in events:
                self.cases += 1
                tracked = False
                pre_stack = list()
                if single_occurrence:
                    if preceding in events:
                        request_idx = events.index(request)
                        preceding_idx = events.index(preceding)
                        if request_idx < preceding_idx:
                            self.violations += 1
                            self.case_id_dict[case_id] = request_idx


                    else:
                        self.violations += 1
                        request_idx = events.index(request)
                        self.case_id_dict[case_id] = request_idx

                else:
                    for i, event in enumerate(events):
                        if event == preceding:
                            pre_stack.append(event)
                        elif event == request and len(pre_stack) > 0:
                            pre_stack.pop()
                        elif event == request:
                            if not tracked:
                                self.case_id_dict[case_id] =  i
                                self.violations += 1
                                tracked = True
                                break


        msg = ("Conformance checking via precedence rules of '" + request + "' requiring '" + preceding
               + "' with " + str(self.violations) + " violations: " + str(self.get_percentage())
               + "% of all cases.")
        if label:
            print()
            print(msg)
            print()
            log = self.label_sequences(log)
            if encode:
                log = self.encode_traces(log, single_rule=True,
                                 prefix_reduction=prefix_reduction,
                                 min_trace_length=min_trace_length,
                                 max_trace_length=max_trace_length,
                                 drop_help_cols=drop_help_cols)
            return log
        elif not label:
            return msg

    def check_exclusive(self, log, first_activity: str, second_activity: str,
                        label=False, encode=False, prefix_reduction=1, min_trace_length=2,
                        max_trace_length=None, drop_help_cols=True):
        """
        Check the exclusiveness of two activities.


        :param log: event log
        :param first_activity: activity
        :param second_activity: activity
        :return: report
        """

        self.rule = "precedence"
        self.checked_activity = first_activity + "_" + second_activity
        self.cases = 0
        self.violations = 0
        self.case_id_dict = dict()

        for case_id, events in log.groupby([self.id])[self.trace].apply(list).items():
            if first_activity in events or second_activity in events:
                self.cases += 1
            if first_activity in events and second_activity in events:
                self.violations += 1
                idx = max(events.index(first_activity), events.index(second_activity))
                self.case_id_dict[case_id] = idx
        msg = ("Conformance checking via exclusiveness rule of '" + first_activity + "' and '" + second_activity
               + "' with " + str(self.violations) + " violations: " + str(self.get_percentage())
               + "% of all cases.")
        if label:
            print()
            print(msg)
            print()
            log = self.label_sequences(log)
            if encode:
                log = self.encode_traces(log, single_rule=True,
                                 prefix_reduction=prefix_reduction,
                                 min_trace_length=min_trace_length,
                                 max_trace_length=max_trace_length,
                                 drop_help_cols=drop_help_cols)
            return log
        elif not label:
            return msg

    def check_time_elapse_bpic2018(self, log, end_activity, label=False,
                                   encode=False, prefix_reduction=1, min_trace_length=2,
                                   max_trace_length=None, drop_help_cols=True):

        self.rule = "time_elapse"
        self.checked_activity = end_activity
        self.cases = 0
        self.violations = 0
        self.case_id_dict = dict()

        log2 = log[[self.id, self.trace, self.timecol]]
        log2[self.timecol] = pd.to_datetime(log2[self.timecol])
        log2[self.timecol] = log2[self.timecol].dt.tz_localize(None)

        for case_id, vals in log2.groupby([self.id]):
            events = vals[self.trace].tolist()
            times = vals[self.timecol].dt.year.tolist()
            if end_activity in events:
                self.cases += 1
                start_year = times[0]
                req_idx = events[::-1].index(end_activity)
                end_year = times[::-1][req_idx]
                if end_year > start_year:
                    self.violations += 1
                    self.case_id_dict[case_id] = [start_year == year for year in times].index(False)

        msg = ("Time elapse checking of with " + str(self.violations) + " violations: " + str(self.get_percentage())
               + "% of all cases.")
        if label:
            print()
            print(msg)
            print()
            log = self.label_sequences(log)
            if encode:
                log = self.encode_traces(log, single_rule=True,
                                         prefix_reduction=prefix_reduction,
                                         min_trace_length=min_trace_length,
                                         max_trace_length=max_trace_length,
                                         drop_help_cols=drop_help_cols)
            return log
        elif not label:
            return msg
