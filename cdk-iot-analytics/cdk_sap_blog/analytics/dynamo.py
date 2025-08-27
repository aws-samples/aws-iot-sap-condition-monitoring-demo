import aws_cdk.aws_dynamodb as dyndb

import aws_cdk.custom_resources as cr
import aws_cdk.aws_iam as iam
from aws_cdk.custom_resources import (
    AwsCustomResource,
    AwsCustomResourcePolicy,
    AwsSdkCall,
    PhysicalResourceId
)


def get_ddb(scope):
    m_table = dyndb.CfnTable(
        scope=scope,
        id=f"CDKSAPBlogTable_{scope.table_name}",
        table_name=f"{scope.table_name}",
        key_schema=[
            dyndb.CfnTable.KeySchemaProperty(attribute_name="DeviceID",key_type="HASH"),
        ],
        attribute_definitions=[
            dyndb.CfnTable.AttributeDefinitionProperty(attribute_name='DeviceID', attribute_type="S"),
        ],
        billing_mode="PAY_PER_REQUEST"
    )

    initialize_ddb = cr.AwsCustomResource(
        scope=scope,
        id="CDKSAPBlog_InitializeDynamoDB",
        policy=AwsCustomResourcePolicy.from_statements(
            [
                iam.PolicyStatement(
                    actions=[
                        'dynamodb:PutItem',
                    ],
                    resources=[m_table.get_att("Arn").to_string()]
                )
            ]
        ),
        on_create=AwsSdkCall(
            action="putItem",
            service="DynamoDB",
            parameters={
                'TableName': m_table.table_name,
                'Item': {
                    "DeviceID": {
                        "S": scope.thing_name
                    },
                    "SAPEquipmentNr": {
                        "S": scope.sapEquipment
                    },
                    "SAPFunctLoc": {
                        "S": scope.sapFunctLoc
                    }
                }
            },
            physical_resource_id=PhysicalResourceId.of(m_table.logical_id),
        ),
        on_update=AwsSdkCall(
            action="putItem",
            service="DynamoDB",
            parameters={
                'TableName': m_table.table_name,
                'Item': {
                    "DeviceId": {
                        "S": scope.thing_name
                    },
                    "SAPEquipmentNr": {
                        "S": scope.sapEquipment
                    },
                    "SAPFunctLoc": {
                        "S": scope.sapFunctLoc
                    }
                }
            },
            physical_resource_id=PhysicalResourceId.of(m_table.logical_id),
        ),
    )
    initialize_ddb.node.add_dependency(m_table)

    return m_table