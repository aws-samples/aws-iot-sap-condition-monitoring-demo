#!/usr/bin/env python3
import os
from aws_cdk import core

from cdk_sap_blog.iot.iot_stack import CdkSAPBlogIoTStack
from cdk_sap_blog.analytics.analytics_stack import CdkSAPBlogAnalyticsStack
from cdk_sap_blog.sap.sap_stack import CdkSAPBlogSAPStack



app = core.App(context={'odata_function_name': 'CDK-SAP-Blog-OData-Function'})
CdkSAPBlogIoTStack(
    app,
    "iot",
    stack_name="cdk-iot-for-sap-iot",
    env=core.Environment(
        account=os.environ['CDK_DEFAULT_ACCOUNT'],
        region=os.environ['CDK_DEFAULT_REGION']
    )
)

CdkSAPBlogAnalyticsStack(
    app,
    "analytics",
    stack_name="cdk-iot-for-sap-analytics",
    env=core.Environment(
        account=os.environ['CDK_DEFAULT_ACCOUNT'],
        region=os.environ['CDK_DEFAULT_REGION'],
    )
)

CdkSAPBlogSAPStack(
    app,
    "sap",
    stack_name="cdk-iot-for-sap-sap",
    env=core.Environment(
        account=os.environ['CDK_DEFAULT_ACCOUNT'],
        region=os.environ['CDK_DEFAULT_REGION'],
    ),
)

app.synth()
