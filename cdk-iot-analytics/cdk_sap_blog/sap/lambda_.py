import json
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_iam as iam
import aws_cdk.aws_secretsmanager as secretsmanager

from aws_cdk import (
    Stack,
    CfnOutput,
    Tags,
    Duration,
)

from constructs import (
    Construct,
)

sapSecretName = 'sap-iot-secret'
lambda_name = "sap-iot-sap-odp-integration"

def get_odata(scope, sns_topic_arn):
    lambda_role = iam.Role(
        scope=scope,
        id=f"{lambda_name}Role",
        role_name=f"{lambda_name}Role",
        assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
    )
    lambda_role.add_to_policy(
        iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            resources=[f'arn:aws:logs:{scope.region}:{scope.account}:*'],
            actions=['logs:CreateLogGroup',]
        )
    )
    lambda_role.add_to_policy(
        iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            resources=[
                f'arn:aws:logs:{scope.region}:{scope.account}:log-group:/aws/lambda/{lambda_name}:*',
            ],
            actions=[
                'logs:CreateLogStream',
                'logs:PutLogEvents',
            ]
        )
    )

    sap_secret = secretsmanager.Secret(
        scope=scope,
        id=sapSecretName,
        secret_name=sapSecretName,
        generate_secret_string=secretsmanager.SecretStringGenerator(
            generate_string_key='secret-key',
            secret_string_template=json.dumps({
                'username': scope.sapUsername,
                'password': scope.sapPassword,
            }),
        )
    )
    sap_secret.grant_read(lambda_role)
    Tags.of(sap_secret).add('sap-iot-secret', 'True')
    lambda_role.add_to_policy(
        iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            resources=['*'],
            actions=[
                'secretsmanager:ListSecrets',
                'secretsmanager:GetSecretValue'
            ]
        )
    )
    lambda_role.add_to_policy(
        iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            resources=[sns_topic_arn],
            actions=[
                'sns:Publish',
            ]
        )
    )

    layer = lambda_.LayerVersion(
        scope=scope,
        id=f"{lambda_name}Layer",
        code=lambda_.Code.from_asset('cdk_sap_blog/sap/lambda_assets/layer'),
        compatible_runtimes=[lambda_.Runtime.PYTHON_3_12],
        license='Apache-2.0',
        description='Request library for HTTP(S) calls',
    )

    L = lambda_.Function(
        scope=scope,
        id=lambda_name,
        function_name=lambda_name,
        runtime=lambda_.Runtime.PYTHON_3_12,
        code=lambda_.Code.from_asset('cdk_sap_blog/sap/lambda_assets/function_code'),
        handler='lambda_function.lambda_handler',
        timeout=Duration.minutes(1),
        architecture=lambda_.Architecture.ARM_64,
        layers=[layer],
        role=lambda_role,
        environment={
            'sapOdpEntitySetName': scope.sapOdpEntitySetName,
            'sapOdpServiceName': scope.sapOdpServiceName,
            'sapHostName': scope.sapHostName,
            'sapUrlPrefix': scope.sapUrlPrefix,
            'sapPort': scope.sapPort,
            'snsAlertEmailTopic': sns_topic_arn,
            'sapSecretName': sapSecretName
        }
    )

    return L
