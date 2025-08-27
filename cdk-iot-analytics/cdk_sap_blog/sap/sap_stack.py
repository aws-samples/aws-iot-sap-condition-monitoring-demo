import os
import json
import sap.eventbridge_stepfunction as eventbridge_stepfunction
import sap.lambda_ as lambda_

from aws_cdk import (
    Stack,
    CfnOutput,
)

from constructs import (
    Construct,
)


class CdkSAPBlogSAPStack(Stack):
	account = None
	region = None
	thing_name = None

	def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
		super().__init__(scope, construct_id, **kwargs)

		self.account = os.environ["CDK_DEFAULT_ACCOUNT"]
		self.region = os.environ["CDK_DEFAULT_REGION"]
		self.thing_name = self.node.try_get_context('thing_name')
		self.sapOdpEntitySetName = self.node.try_get_context('sapOdpEntitySetName')
		self.sapOdpServiceName = self.node.try_get_context('sapOdpServiceName')
		self.sapHostName = self.node.try_get_context('sapHostName')
		self.sapUrlPrefix = self.node.try_get_context('sapUrlPrefix')
		self.sapPort = self.node.try_get_context('sapPort')
		self.sapUsername = self.node.try_get_context('sapUsername')
		self.sapPassword = self.node.try_get_context('sapPassword')
		self.table_name = self.node.try_get_context('dynamodb_table')

		if not self.sapOdpEntitySetName:
			print("Provide sapOdpEntitySetName in cdk.json or on command line (e.g. --context sapOdpEntitySetName=myentityname)")
			exit(1)
		if not self.sapOdpServiceName:
			print("Provide sapOdpServiceName in cdk.json or on command line (e.g. --context sapOdpServiceName=myservicename)")
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

		# Create SAP Lambda function
		m_lambda = lambda_.get_odata(self, f'arn:aws:sns:{self.region}:{self.account}:sap-iot-temperature-alarm')
		
		# Create EventBridge Step Function workflow with Lambda
		sap_workflow_resources = eventbridge_stepfunction.create_eventbridge_stepfunction_workflow(self, m_lambda)