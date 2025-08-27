"""
Design

"""

import os
import json
import analytics.lambda_ as lambda_
import analytics.dynamo as dynamo
import analytics.iot_cloudwatch as iot_cloudwatch
import analytics.sns as sns

from aws_cdk import (
    Stack,
    CfnOutput,
)

from constructs import (
    Construct,
)

class CdkSAPBlogAnalyticsStack(Stack):
	account = None
	region = None
	thing_name = None

	def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
		super().__init__(scope, construct_id, **kwargs)

		self.account = os.environ["CDK_DEFAULT_ACCOUNT"]
		self.region = os.environ["CDK_DEFAULT_REGION"]
		self.table_name = self.node.try_get_context('dynamodb_table')
		self.thing_name = self.node.try_get_context('thing_name')
		self.Type = self.node.try_get_context('Type')
		self.sapEquipment = self.node.try_get_context('sapEquipment')
		self.sapFunctLoc = self.node.try_get_context('sapFunctLoc')
		self.temperature_min = self.node.try_get_context('temperature_min')
		self.temperature_max = self.node.try_get_context('temperature_max')
		self.alarm_emails = self.node.try_get_context('alarm_emails')

		if not self.thing_name:
			print("Provide thing_name in cdk.json or on command line (e.g. --context thing_name=my_thing_123)")
			exit(1)
		if not self.Type:
			print("Provide Type in cdk.json or on command line (e.g. --context Type=prod-123)")
			exit(1)
		if not self.sapEquipment:
			print("Provide sapEquipment in cdk.json or on command line (e.g. --context sapEquipment=prod-123)")
			exit(1)
		if not self.sapFunctLoc:
			print("Provide sapFunctLoc in cdk.json or on command line (e.g. --context sapFunctLoc=prod-123)")
			exit(1)
		if not self.temperature_min:
			print("Provide temperature_min in cdk.json or on command line (e.g. --context temperature_min=prod-123)")
			exit(1)
		if not self.temperature_max:
			print("Provide temperature_max in cdk.json or on command line (e.g. --context temperature_max=prod-123)")
			exit(1)


		analytics_logger = lambda_.get_logger(self)
		sns_topic = sns.create_sns_topic(self, self.alarm_emails)
		iot_cloudwatch.create_iot_cloudwatch_rule_and_alarms(self, sns_topic.ref, analytics_logger.function_arn)
		dynamo.get_ddb(self)