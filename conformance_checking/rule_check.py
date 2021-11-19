from util.log import EventLog
import numpy as np
import pandas as pd
import datetime as dt
desired_width = 200
pd.set_option('display.width', desired_width)
pd.set_option("display.max_rows", 40)
pd.set_option("display.max_columns", None)

class RuleChecker(EventLog):

	def __init__(self, id="case:concept:name", trace="concept:name", timestamp="time:timstamp"):
		EventLog.__init__(self, id, trace, timestamp)
		self.violations = 0
		self.cases = 0
		self.rule = str()
		self.checked_activity = str()


	def get_percentage(self) -> float:
		return round((self.violations / self.cases) *100, 2)


	def label_log(self, log: pd.DataFrame, case_id_dict: dict) -> pd.DataFrame:
		log["_".join([self.rule, self.checked_activity])] = np.where(
			log[self.id].isin(case_id_dict.keys()), 1, 0 )
		log = log.merge(pd.DataFrame({self.id:case_id_dict.keys(),
								  "_".join(["Pos", self.rule, self.checked_activity])
								  : case_id_dict.values()}),
					on=[self.id],
					how="left")
		log["idx"] = 0
		log["idx"] = log.groupby([self.id])["idx"].cumcount()
		log["_".join(["Pos", self.rule, self.checked_activity])] = log[
			"_".join(["Pos", self.rule, self.checked_activity])].fillna(np.inf)
		log["_".join(["Pos", self.rule, self.checked_activity])] = np.where(log[
			"_".join(["Pos", self.rule, self.checked_activity])]<= log["idx"], 1, 0)
		log = log.drop(columns=["idx"])
		return log


	def check_cardinality(self, log: pd.DataFrame, activity: str, lower: int,
						   upper: int, label=True)-> pd.DataFrame:
		t0 = dt.datetime.now()
		self.rule = "cardinality"
		self.checked_activity = "_".join([activity, str(0), str(1)])
		self.cases = 0
		self.violations = 0
		case_id_dict = dict()

		for case_id, events in log.groupby([self.id])[self.trace].apply(list).items():
			self.cases += 1
			violated = False
			counter = 0
			for i, event in enumerate(events):
				if event == activity:
					counter += 1
					if counter >= upper:
						if not violated:
							self.violations += 1
							case_id_dict[case_id] = i
							violated = True
				if counter < lower and i == len(events) and not violated:
					# lower cardinality incompliance only gets labeled  when the trace is finalized
					self.violations += 1
					case_id_dict[case_id] = len(events)
		if label:
			log = self.label_log(log, case_id_dict)

		print("Conformance checking via cardinality rules of '"+activity
				  + "' with "+str(self.violations) + " violations: "+ str(self.get_percentage())
				  +"% of all cases.")
		print("Execution time="+str((dt.datetime.now()-t0).seconds)+" seconds")
		return log

	def check_order(self, log, first: str, second: str) -> pd.DataFrame:
		"""
		Check the order of the given activities.

		:param log: event log
		:param first: activity
		:param second: activity
		:return: report
		"""

		violations = 0
		traces = 0

		for trace in log:
			events = trace['events']
			first_stack = []

			if first in events and second in events:
				traces += 1

				for event in events:
					if event == first:
						first_stack.append(event)
					elif event == second and len(first_stack) == 0:
						violations += 1

		return {'first': first, 'second': second,
				'violations': (violations,
							   self.get_percentage(traces, violations))}

	def check_response(self, log, request: str, response: str,
					   single_occurrence=False) -> dict:
		raise NotImplementedError
		"""
		Check response requirements of the given activity.


		:param log: event log
		:param request: activity which expects a requested activity
		:param response: requested activity
		:param single_occurrence: specifies whether a single occurrence of the
		responding activity already satisfies the rule
		:return: report
		"""

		violations = 0
		candidate_traces = 0
		violated_traces = 0

		for trace in log:
			events = trace['events']
			req_stack = []
			tracked = False
			if request in events:
				candidate_traces += 1
				if single_occurrence:
					if response in events:
						req_idx = events[::-1].index(request)
						res_idx = events[::-1].index(response)
						if req_idx < res_idx:
							violations += 1
							violated_traces += 1
					else:
						violated_traces += 1
						violations += 1
				else:
					for event in events:
						if event == request:
							req_stack.append(event)
						elif event == response and len(req_stack) > 0:
							req_stack.pop()
					if len(req_stack) > 0:
						violated_traces += 1
						violations += len(req_stack)

		return {'request': request, 'response': response,
			'violations': (violations, violated_traces,
						   self.get_percentage(candidate_traces, violated_traces)),
				'single': single_occurrence}

	def check_precedence(self, log: pd.DataFrame, preceding: str, request: str,
						 single_occurrence=False, label=True) -> pd.DataFrame:
		"""
		Check precedence requirements of the given activity.

		:param log: event log
		:param preceding: activity that should precede the requesting activity
		:param request: requesting activity
		:param single_occurrence: specifies whether a single occurrence of the
		preceding activity already satisfies the rule
		:return: report
		"""

		t0 = dt.datetime.now()
		self.rule = "precedence"
		self.checked_activity = preceding + "_" +  request
		self.cases = 0
		self.violations = 0

		case_id_dict = dict()

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
							case_id_dict[case_id] = request_idx

					else:
						self.violations += 1
						request_idx = events.index(request)
						case_id_dict[case_id] = request_idx

				else:

					for i, event in enumerate(events):
						if event == preceding:
							pre_stack.append(event)
						elif event == request and len(pre_stack) > 0:
							pre_stack.pop()
						elif event == request:
							if not tracked:
								case_id_dict[case_id] = i
								self.violations += 1
								tracked = True

		if label:
			log = self.label_log(log, case_id_dict)
		print("Conformance checking via precedence rules of '"+request+"' requiring '"+preceding
			  + "' with "+str(self.violations) + " violations: "+ str(self.get_percentage())
			  +"% of all cases.")
		print("Execution time="+str((dt.datetime.now()-t0).seconds)+" seconds")
		return log



	def check_exclusive(self, log, first_activity: str, second_activity: str) -> dict:
		"""
		Check the exclusiveness of two activities.


		:param log: event log
		:param first_activity: activity
		:param second_activity: activity
		:return: report
		"""
		raise NotImplementedError
		violations = 0
		violated_traces = 0

		for trace in log:
			events = trace['events']

			if first_activity in events and second_activity in events:
				violated_traces += 1
				violations += 1

		return {'first activity': first_activity,
				'second activity': second_activity,
				'violations': (violations,
							   self.get_percentage(len(log), violated_traces))}
