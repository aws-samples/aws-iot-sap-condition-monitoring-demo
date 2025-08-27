import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_iam as iam

# def process_data(scope):
#     lambda_name = f"CDK-SAP-Blog-DataProcessor"
#     lambda_role = iam.Role(
#         scope=scope,
#         id=f"{lambda_name}Role",
#         role_name=f"{lambda_name}Role",
#         assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
#     )
#     lambda_role.add_to_policy(
#         iam.PolicyStatement(
#             effect=iam.Effect.ALLOW,
#             resources=[f'arn:aws:logs:{scope.region}:{scope.account}:*'],
#             actions=['logs:CreateLogGroup',]
#         )
#     )
#     lambda_role.add_to_policy(
#         iam.PolicyStatement(
#             effect=iam.Effect.ALLOW,
#             resources=[
#                 f'arn:aws:logs:{scope.region}:{scope.account}:log-group:/aws/lambda/{lambda_name}:*',
#             ],
#             actions=[
#                 'logs:CreateLogStream',
#                 'logs:PutLogEvents',
#             ]
#         )
#     )
#     lambda_role.add_to_policy(
#         iam.PolicyStatement(
#             effect=iam.Effect.ALLOW,
#             resources=[
#                 f'arn:aws:dynamodb:{scope.region}:{scope.account}:table/{scope.table_name}'
#             ],
#             actions=[
#                 'dynamodb:GetItem',
#                 'dynamodb:UpdateItem'
#             ]
#         )
#     )

#     L = lambda_.Function(
#         scope=scope,
#         id=lambda_name,
#         function_name=lambda_name,
#         runtime=lambda_.Runtime.PYTHON_3_12,
#         architecture=lambda_.Architecture.ARM_64,
#         code=lambda_.Code.from_asset('cdk_sap_blog/analytics/lambda_assets/process_data'),
#         handler='process_data.handler',
#         role=lambda_role,
#         environment={
#             "TABLE_NAME": scope.table_name
#         }
#     )
#     L.add_permission(
#         id="invoke permissions",
#         principal=iam.ServicePrincipal('iot.amazonaws.com'),
#         action="lambda:InvokeFunction",
#         source_account=scope.account,
#         source_arn=f"arn:aws:iot:{scope.region}:{scope.account}:*"
#     )
#     return L

def get_logger(scope):
    """
        CloudFormation and CDK do not support CloudwatchLog RuleAction.

        Therefore, this lambda is used to provide a path for any Rule
        to send telemetry or ErrorActions to CloudWatch.
    """
    logger_name = f"cdk-iot-for-sap-analytics-logger"
    lambda_role = iam.Role(
        scope=scope,
        id=f"{logger_name}Role",
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
                f'arn:aws:logs:{scope.region}:{scope.account}:log-group:/aws/lambda/{logger_name}:*'
            ],
            actions=[
                'logs:CreateLogStream',
                'logs:PutLogEvents',
            ]
        )
    )

    L = lambda_.Function(
        scope=scope,
        id=logger_name,
        function_name=logger_name,
        runtime=lambda_.Runtime.PYTHON_3_12,
        architecture=lambda_.Architecture.ARM_64,
        code=lambda_.Code.from_asset('cdk_sap_blog/analytics/lambda_assets/cw_logger'),
        handler='cw_logger.handler',
        role=lambda_role,
        environment={
            "LOGGERNAME": logger_name
        }
    )
    L.add_permission(
        id="invoke permissions",
        principal=iam.ServicePrincipal('iot.amazonaws.com'),
        action="lambda:InvokeFunction",
        source_account=scope.account,
        source_arn=f"arn:aws:iot:{scope.region}:{scope.account}:rule/*"
    )
    return L