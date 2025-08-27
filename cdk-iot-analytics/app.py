#!/usr/bin/env python3
import os

from aws_cdk import (
    App,
    Aspects,
    Aws,
    Environment,
)

from cdk_sap_blog.iot.iot_stack import CdkSAPBlogIoTStack
from cdk_sap_blog.analytics.analytics_stack import CdkSAPBlogAnalyticsStack
from cdk_sap_blog.sap.sap_stack import CdkSAPBlogSAPStack



app = App(context={})
CdkSAPBlogIoTStack(
    app,
    "iot",
    stack_name="cdk-iot-for-sap-iot",
    env=Environment(
        account=os.environ['CDK_DEFAULT_ACCOUNT'],
        region=os.environ['CDK_DEFAULT_REGION']
    )
)

CdkSAPBlogAnalyticsStack(
    app,
    "analytics",
    stack_name="cdk-iot-for-sap-analytics",
    env=Environment(
        account=os.environ['CDK_DEFAULT_ACCOUNT'],
        region=os.environ['CDK_DEFAULT_REGION'],
    )
)

CdkSAPBlogSAPStack(
    app,
    "sap",
    stack_name="cdk-iot-for-sap-sap",
    env=Environment(
        account=os.environ['CDK_DEFAULT_ACCOUNT'],
        region=os.environ['CDK_DEFAULT_REGION'],
    ),
)

app.synth()
