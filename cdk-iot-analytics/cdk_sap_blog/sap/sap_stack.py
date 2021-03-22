import os
import json
import sap.lambda_ as lambda_
import sap.sns as sns
from aws_cdk import core


class CdkSAPBlogSAPStack(core.Stack):
	account = None
	region = None
	thing_name = None

	def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
		super().__init__(scope, construct_id, **kwargs)

		self.account = os.environ["CDK_DEFAULT_ACCOUNT"]
		self.region = os.environ["CDK_DEFAULT_REGION"]
		self.odpEntitySetName = self.node.try_get_context('odpEntitySetName')
		self.odpServiceName = self.node.try_get_context('odpServiceName')
		self.sapHostName = self.node.try_get_context('sapHostName')
		self.sapPort = self.node.try_get_context('sapPort')
		self.sapUsername = self.node.try_get_context('sapUsername')
		self.sapPassword = self.node.try_get_context('sapPassword')
		self.sns_alert_email_topic = self.node.try_get_context('sns_alert_email_topic')
		self.alarm_emails = self.node.try_get_context('alarm_emails')

		if not self.odpEntitySetName:
			print("Provide odpEntitySetName in cdk.json or on command line (e.g. --context odpEntitySetName=myentityname)")
			exit(1)
		if not self.odpServiceName:
			print("Provide odpServiceName in cdk.json or on command line (e.g. --context odpServiceName=myservicename)")
			exit(1)
		if not self.sapHostName:
			print("Provide sapHostName in cdk.json or on command line (e.g. --context sapHostName=myhostname)")
			exit(1)
		if not self.sapPort:
			print("Provide sapPort in cdk.json or on command line (e.g. --context sapPort=1234)")
			exit(1)
		if not self.sapUsername:
			print("Provide sapUsername in cdk.json or on command line (e.g. --context sapUsername=myusername)")
			exit(1)
		if not self.sapPassword:
			print("Provide sapPassword in cdk.json or on command line (e.g. --context sapPassword=Password123)")
			exit(1)
		if not self.sns_alert_email_topic:
			print("Provide sns_alert_email_topic in cdk.json or on command line (e.g. --context sns_alert_email_topic=myalerttopic)")
			exit(1)
		if not self.alarm_emails:
			print("Provide alarm_emails in cdk.json")
			exit(1)

		from_sap_topic = sns.get_sap_response_email_sns_topic(self, self.alarm_emails)
		m_lambda = lambda_.get_odata(self, from_sap_topic.ref)
		m_lambda.node.add_dependency(from_sap_topic)

		# core.CfnOutput(
		# 	scope=self,
		# 	id="SAPODataLambdaArn",
		# 	export_name=f"{self.stack_name}:SAPODataLambdaArn",
		# 	value=m_lambda.function_arn
		# )


