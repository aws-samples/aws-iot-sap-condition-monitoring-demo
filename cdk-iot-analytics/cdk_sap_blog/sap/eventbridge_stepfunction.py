import aws_cdk.aws_events as events
import aws_cdk.aws_events_targets as targets
import aws_cdk.aws_stepfunctions as sfn
import aws_cdk.aws_iam as iam
import json
import os

def create_eventbridge_stepfunction_workflow(scope, m_lambda):
    # EventBridge connection for SAP
    sap_connection = events.CfnConnection(
        scope=scope,
        id="SAPConnection",
        name="sap-odp-connection",
        description="EventBridge connection to SAP ODP",
        authorization_type="BASIC",
        auth_parameters=events.CfnConnection.AuthParametersProperty(
            basic_auth_parameters=events.CfnConnection.BasicAuthParametersProperty(
                username=scope.sapUsername,
                password=scope.sapPassword
            )
        )
    )

    # IAM role for Step Function
    stepfunction_role = iam.Role(
        scope=scope,
        id="StepFunctionRole",
        assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
        inline_policies={
            "DynamoDBReadPolicy": iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=["dynamodb:GetItem"],
                        resources=[f"arn:aws:dynamodb:{scope.region}:{scope.account}:table/{scope.table_name}"]
                    )
                ]
            ),
            "LambdaInvokePolicy": iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=["lambda:InvokeFunction"],
                        resources=[m_lambda.function_arn]
                    )
                ]
            )
        }
    )

    # Read ASL file and substitute variables
    asl_file_path = os.path.join(os.path.dirname(__file__), "sap_workflow.asl.json")
    with open(asl_file_path, 'r') as f:
        asl_definition = f.read()
    
    # Substitute variables in ASL
    asl_definition = asl_definition.replace("${DynamoDBTable}", scope.table_name)
    asl_definition = asl_definition.replace("${ThingName}", scope.thing_name)
    asl_definition = asl_definition.replace("${SAPLambdaFunction}", m_lambda.function_name)

    # Step Function state machine using ASL file
    state_machine = sfn.StateMachine(
        scope=scope,
        id="AlarmProcessingStateMachine",
        state_machine_name="sap-iot-temperature-alarm-processing",
        definition_body=sfn.DefinitionBody.from_string(asl_definition),
        role=stepfunction_role
    )

    # EventBridge rule to capture CloudWatch alarms
    alarm_rule = events.Rule(
        scope=scope,
        id="CloudWatchAlarmRule",
        rule_name="sap-iot-temperature-alarm-rule",
        event_pattern=events.EventPattern(
            source=["aws.cloudwatch"],
            detail_type=["CloudWatch Alarm State Change"],
            detail={
                "state": {
                    "value": ["ALARM"]
                },
                "alarmName": [{"prefix": "sap-iot-temperature"}]
            }
        ),
        targets=[targets.SfnStateMachine(state_machine)]
    )

    return {
        "state_machine": state_machine,
        "eventbridge_rule": alarm_rule,
        "sap_connection": sap_connection
    }