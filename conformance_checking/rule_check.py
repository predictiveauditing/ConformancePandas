from util.log import EventLog
import numpy as np
import pandas as pd


class RuleChecker(EventLog):

	def __init__(self, id="case:concept:name", trace="concept:name", timestamp="time:timstamp"):
		EventLog.__init__(self, id, trace, timestamp)
		self.violations = 0
		self.cases = 0

	def get_percentage(self) -> float:
		return round((self.violations / self.cases) *100, 2)

	def check_cardinality(self, log: pd.DataFrame,
						  activity: str, upper: int, lower: int, label=True) -> pd.DataFrame:
		"""
		Check cardinalities for given activity.

		:param log: event log
		:param activity: name of the activity
		:param upper: max. number of occurrence in one trace, -1 if infinite
		:param lower: min. number of occurrence in one trace
		:return: report
		"""
		log["Csum"] = np.where(log[self.trace]==activity, 1, 0)
		log["Csum"] = log.groupby([self.id])["Csum"].apply(lambda x: x.cumsum())
		log["Pos cardinality  "+ activity] = np.where(
				(log["Csum"] <=upper & log["Csum"]<=lower), 1, 0)
		self.violations = log.groupby([self.id])["Pos cardinality "+activity].min().sum()
		self.cases = len(log[self.id].unique())
		log = log.merge(log.groupby([self.id]
						 )["Pos cardinality "+activity].min()
			  .reset_index().rename(columns={"Pos cardinality "+activity
							: "cardinality "+ activity}),
			  on=[self.id], how="left")
		log = log.drop(columns=["Csum"])
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
						 single_occurrence=False, perc=False) -> pd.DataFrame:
		"""
		Check precedence requirements of the given activity.

		:param log: event log
		:param preceding: activity that should precede the requesting activity
		:param request: requesting activity
		:param single_occurrence: specifies whether a single occurrence of the
		preceding activity already satisfies the rule
		:return: report
		"""
		self.cases=0
		self.violations=0
		case_id_dict = dict()

		for case_id, events in log.groupby([self.id])[self.trace].apply(list).items():
			if request in events:
				self.cases+=1
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

		log[" ".join(["precedence", preceding, request])] = np.where(
				log[self.id].isin(case_id_dict.keys()), 1, 0 )
		log = log.merge(pd.DataFrame({self.id:case_id_dict.keys(),
								"_".join(["Pos",
										  "precedence",
										  preceding,
										  request]): case_id_dict.values()}),
				  on=[self.id],
				  how="left")
		print("Conformance checking via precedence rules of '"+request+"' requiring '"+preceding
			  + "' with "+str(self.violations) + " violations: "+ str(self.get_percentage())
			  +"% of all cases.")
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
