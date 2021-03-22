"""
Design

"""

import os
import json
import analytics.lambda_ as lambda_
import analytics.dynamo as dynamo
import analytics.analytics as analytics
from aws_cdk import core


class CdkSAPBlogAnalyticsStack(core.Stack):
	account = None
	region = None
	thing_name = None

	def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
		super().__init__(scope, construct_id, **kwargs)

		self.account = os.environ["CDK_DEFAULT_ACCOUNT"]
		self.region = os.environ["CDK_DEFAULT_REGION"]
		self.table_name = "trackedProducts"
		self.thing_name = self.node.try_get_context('thing_name')
		self.Type = self.node.try_get_context('Type')
		self.Equipment = self.node.try_get_context('Equipment')
		self.FunctLoc = self.node.try_get_context('FunctLoc')
		self.temperature_min = self.node.try_get_context('temperature_min')
		self.temperature_max = self.node.try_get_context('temperature_max')
		self.alarm_emails = self.node.try_get_context('alarm_emails')

		if not self.thing_name:
			print("Provide thing_name in cdk.json or on command line (e.g. --context thing_name=my_thing_123)")
			exit(1)
		if not self.Type:
			print("Provide Type in cdk.json or on command line (e.g. --context Type=prod-123)")
			exit(1)
		if not self.Equipment:
			print("Provide Equipment in cdk.json or on command line (e.g. --context Equipment=prod-123)")
			exit(1)
		if not self.FunctLoc:
			print("Provide FunctLoc in cdk.json or on command line (e.g. --context FunctLoc=prod-123)")
			exit(1)
		if not self.temperature_min:
			print("Provide temperature_min in cdk.json or on command line (e.g. --context temperature_min=prod-123)")
			exit(1)
		if not self.temperature_max:
			print("Provide temperature_max in cdk.json or on command line (e.g. --context temperature_max=prod-123)")
			exit(1)


		analytics_logger = lambda_.get_logger(self, "AnalyticsPipelineRuleErrors")
		ddb = dynamo.get_ddb(self)
		datastore = analytics.get_analytics_datastore(self)
		pipeline = analytics.get_analytics_pipeline(self, datastore.datastore_name, error_log_arn=analytics_logger.function_arn)
		events_input = analytics.get_events_input(self)
		dataset = analytics.get_analytics_dataset(self, datastore.datastore_name, events_input.input_name)
		detector = analytics.get_detector_model(
			self, 
			events_input.input_name,
			# create dependency on the 'sap' stack here by passing sns arn for alert emails originating from SAP system
			f"arn:aws:lambda:{self.region}:{self.account}:function:{self.node.try_get_context('odata_function_name')}"
		)

