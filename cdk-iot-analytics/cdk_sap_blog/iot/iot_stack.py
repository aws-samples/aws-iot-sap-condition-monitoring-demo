"""
Design
	- Client CSR is placed in certs/<thing_name>.csr.pem and signed by AWSIoT Core
	- AWS CLI is needed to call DescribeCertificate and written to certs/<thing_name>.cert.pem
	- All MQTT Messages are enriched and republished to topic 'repub/topic()'
	- All republished messages are written to Dynamodb and logged in CW via Lambda
"""

import os
import json
from OpenSSL import crypto
import iot.lambda_ as lambda_
import iot.rules as rules
from create_key_and_csr import (
	generate_key_and_csr,
	download_root_CA
)
import aws_cdk.aws_iot as iot
from aws_cdk import core
import aws_cdk.custom_resources as cr
import aws_cdk.aws_iam as iam
from aws_cdk.custom_resources import (
	AwsCustomResource,
	AwsCustomResourcePolicy,
	AwsSdkCall,
	PhysicalResourceId
)


class CdkSAPBlogIoTStack(core.Stack):
	account = None
	region = None
	thing_name = None

	def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
		super().__init__(scope, construct_id, **kwargs)

		self.account = os.environ["CDK_DEFAULT_ACCOUNT"]
		self.region = os.environ["CDK_DEFAULT_REGION"]
		self.thing_name = self.node.try_get_context('thing_name')
		self.Type = self.node.try_get_context('Type')
		self.Equipment = self.node.try_get_context('Equipment')
		self.FunctLoc = self.node.try_get_context('FunctLoc')

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

		download_root_CA()
		keypath, csrpath = generate_key_and_csr(
			self.thing_name,
			bitlength=int(self.node.try_get_context('RSA_bitlength'))
		)

		m_iot = iot.CfnThing(
			scope=self,
			id=self.thing_name,
			thing_name=self.thing_name,
			attribute_payload=iot.CfnThing.AttributePayloadProperty(attributes={"Type": self.Type})
		)
		m_iot.add_metadata(
			key="CFN_Stack",
			value="CDKSAPBlog"
		)

		m_policy = iot.CfnPolicy(
			scope=self,
			id=f"{self.thing_name}_ConnectPolicy",
			policy_name=f"{self.thing_name}_ConnectPolicy",
			policy_document={
				"Version":"2012-10-17",
				"Statement":[
					{
						"Effect":"Allow",
						"Action":[
							"iot:Connect",
							"iot:Publish",
							"iot:Subscribe",
							"iot:Connect",
							"iot:Receive"

						],
						"Resource":[
							f"arn:aws:iot:{self.region}:{self.account}:client/{self.thing_name}"
						]
					},
					{
						"Effect": "Allow",
						"Action": [
							"iot:Publish"
						],
						"Resource": [
							f"arn:aws:iot:{self.region}:{self.account}:topic/*"
						]
					}
				]
			}
		)

		# download_root_CA()
		# keypath, csrpath = generate_key_and_csr(self.thing_name)

		# sign client CSR
		cert = CDKSAPBlogSignedCSR(
			scope=self,
			id="CDKSAPBlogSignedCSR",
			csr=open(csrpath).read(),
		)
		# attach/detach thing to cert
		thing_princ_attchmnt = cr.AwsCustomResource(
			scope=self,
			id="CDKSAPBlog_ThingPrincipalAttachment",
			policy=AwsCustomResourcePolicy.from_statements(
				[
					iam.PolicyStatement(
						actions=[
							'iot:AttachThingPrincipal',
							'iot:DetachThingPrincipal',
						],
						resources=[cert.arn]
					)
				]
			),
			on_create=AwsSdkCall(
				action="attachThingPrincipal",
				service="Iot",
				parameters={
					"principal": cert.arn,
					"thingName": self.thing_name
				},
				physical_resource_id=PhysicalResourceId.of(cert.arn),
			),
			on_update=AwsSdkCall(
				action="attachThingPrincipal",
				service="Iot",
				parameters={
					"principal": cert.arn,
					"thingName": self.thing_name
				},
				physical_resource_id=PhysicalResourceId.of(cert.arn),
			),
			on_delete=AwsSdkCall(
				action="detachThingPrincipal",
				service="Iot",
				parameters={
					"principal": cert.arn,
					"thingName": self.thing_name
				},
				physical_resource_id=PhysicalResourceId.of(cert.arn),
			)
		)
		thing_princ_attchmnt.node.add_dependency(m_iot)
		# attach/detach policy to cert
		princ_policy_attchmnt = cr.AwsCustomResource(
			scope=self,
			id="CDKSAPBlog_PolicyPrincipalAttachment",
			policy=AwsCustomResourcePolicy.from_statements(
				[
					iam.PolicyStatement(
						actions=[
							'iot:AttachPrincipalPolicy',
							'iot:DetachPrincipalPolicy',
						],
						resources=[cert.arn]
					)
				]
			),
			on_create=AwsSdkCall(
				action="attachPrincipalPolicy",
				service="Iot",
				parameters={
					"principal": cert.arn,
					"policyName": m_policy.policy_name
				},
				physical_resource_id=PhysicalResourceId.of(cert.arn),
			),
			on_update=AwsSdkCall(
				action="attachPrincipalPolicy",
				service="Iot",
				parameters={
					"principal": cert.arn,
					"policyName": m_policy.policy_name
				},
				physical_resource_id=PhysicalResourceId.of(cert.arn),
			),
			on_delete=AwsSdkCall(
				action="detachPrincipalPolicy",
				service="Iot",
				parameters={
					"principal": cert.arn,
					"policyName": m_policy.policy_name
				},
				physical_resource_id=PhysicalResourceId.of(cert.arn),
			)
		)
		princ_policy_attchmnt.node.add_dependency(m_policy)

		# create client connect/pub/sub role and policies
		mqtt_role = iam.Role(
			scope=self,
			id='CDKSAPBlog_MqttRole',
			role_name='CDKSAPBlog_MqttRole',
			assumed_by=iam.ServicePrincipal('iot.amazonaws.com')
		)
		mqtt_role.add_to_policy(
			iam.PolicyStatement(
				effect=iam.Effect.ALLOW,
				resources=[
					f'arn:aws:iot:{self.region}:{self.account}:topic/*'
				],
				actions=[
					'iot:Connect',
					'iot:Publish',
				]
			)
		)

		# create lambda loggers
		if self.node.try_get_context('debug_iot_stack'):
			all_mqtt_logger = lambda_.get_logger(self, "AllMQTT")
			error_logger = lambda_.get_logger(self, "Error")
			mqtt_role.add_to_policy(
				iam.PolicyStatement(
					effect=iam.Effect.ALLOW,
					resources=[
						all_mqtt_logger.function_arn,
						error_logger.function_arn,
					],
					actions=[
						'lambda:InvokeFunction',
					]
				)
			)
			all_mqtt_rule = rules.get_all_mqtt_rule(
				self,
				mqtt_role.role_arn,
				all_mqtt_logger.function_arn,
				error_logger.function_arn
			)

		describe_endpoint = cr.AwsCustomResource(
			scope=self,
			id="CDKSAPBlog_DescribeEndpoint",
			policy=AwsCustomResourcePolicy.from_statements(
				[
					iam.PolicyStatement(
						actions=[
							'iot:DescribeEndpoint',
						],
						resources=['*']
					)
				]
			),
			on_create=AwsSdkCall(
				action="describeEndpoint",
				service="Iot",
				parameters={
					'endpointType': 'iot:Data-ATS'
				},
				# using m_iot as physical resource, but they have no correlation. just need a resource id for call
				physical_resource_id=PhysicalResourceId.of(m_iot.logical_id),
			),
			on_update=AwsSdkCall(
				action="describeEndpoint",
				service="Iot",
				parameters={
					'endpointType': 'iot:Data-ATS'
				},
				# using m_iot as physical resource, but they have no correlation. just need a resource id for call
				physical_resource_id=PhysicalResourceId.of(m_iot.logical_id),
			),
			on_delete=AwsSdkCall(
				action="describeEndpoint",
				service="Iot",
				parameters={
					'endpointType': 'iot:Data-ATS'
				},
				# using m_iot as physical resource, but they have no correlation. just need a resource id for call
				physical_resource_id=PhysicalResourceId.of(m_iot.logical_id),
			),
		)


		core.CfnOutput(
			scope=self,
			id="DescribeEndpoint",
			export_name=f"{self.stack_name}:DescribeEndpoint",
			value=describe_endpoint.get_response_field('endpointAddress')
		)

		core.CfnOutput(
			scope=self,
			id="CertificateId",
			export_name=f"{self.stack_name}:CertificateId",
			value=cert.id_
		)


class CDKSAPBlogSignedCSR(core.Construct):
	def __init__(
		self,
		scope: core.Construct,
		id: str,
		csr: str,
	) -> None:
		super().__init__(scope, id)

		req = crypto.load_certificate_request(crypto.FILETYPE_PEM, csr)
		thing_name = req.get_subject().CN
		cert_id = f'CDKSAPBlog-{thing_name}-cert'

		cert = iot.CfnCertificate(
			scope=self,
			id=cert_id,
			status="ACTIVE",
			certificate_signing_request=csr,
		)
		self.arn = cert.get_att("Arn").to_string()
		self.id_ = cert.get_att("Id").to_string()
