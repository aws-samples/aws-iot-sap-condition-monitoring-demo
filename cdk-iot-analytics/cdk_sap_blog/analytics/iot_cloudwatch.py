import aws_cdk.aws_iot as iot
import aws_cdk.aws_cloudwatch as cloudwatch
import aws_cdk.aws_cloudwatch_actions as cw_actions
import aws_cdk.aws_iam as iam
import aws_cdk.aws_sns as sns

from aws_cdk import (
    Duration,
)

def create_iot_cloudwatch_rule_and_alarms(scope, sns_topic_arn, error_log_arn):
    # IAM role for IoT rule to write to CloudWatch
    iot_cloudwatch_role = iam.Role(
        scope=scope,
        id="SAPIoTCloudWatchRole",
        assumed_by=iam.ServicePrincipal("iot.amazonaws.com"),
        inline_policies={
            "CloudWatchMetricsPolicy": iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=["cloudwatch:PutMetricData"],
                        resources=["*"]
                    )
                ]
            )
        }
    )

    # IoT Core rule to push temperature to CloudWatch metrics
    iot_rule = iot.CfnTopicRule(
        scope=scope,
        id="sap_iot_TemperatureCloudWatchRule",
        rule_name="sap_iot_TemperatureToCloudWatch",
        topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
            sql=f"""SELECT parse_time("yyyy-MM-dd'T'HH:mm:ssZ", timestamp() ) AS timestamp, topic(2) AS thingname, e.t AS temperature_degC, e.h AS humidity_percent, e.d AS dewpoint_degC, e.i AS heatIndex_degC, l AS location FROM 'dt/{scope.thing_name}'""",
            actions=[
                iot.CfnTopicRule.ActionProperty(
                    cloudwatch_metric=iot.CfnTopicRule.CloudwatchMetricActionProperty(
                        metric_name="${topic(2)}",
                        metric_namespace="sap-iot-temperature",
                        metric_unit="None",
                        metric_value="${e.t}",
                        role_arn=iot_cloudwatch_role.role_arn
                    )
                )
            ],
            error_action=iot.CfnTopicRule.ActionProperty(
                lambda_=iot.CfnTopicRule.LambdaActionProperty(
                    function_arn=error_log_arn
                )
            )
        )
    )

    # CloudWatch metric for temperature with 1-minute period
    temperature_metric = cloudwatch.Metric(
        namespace="sap-iot-temperature",
        metric_name=scope.thing_name,
        period=Duration.minutes(1)
    )

    # SNS Topic for alarms
    sns_topic = sns.Topic.from_topic_arn(scope, "AlarmTopic", sns_topic_arn)
    
    # High temperature alarm
    temperature_high_alarm = cloudwatch.Alarm(
        scope=scope,
        id="TemperatureHighAlarm-"+scope.thing_name,
        alarm_name="sap-iot-temperature-high-"+scope.thing_name,
        metric=temperature_metric,
        threshold=float(scope.temperature_max),
        comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        evaluation_periods=3,
        datapoints_to_alarm=3,
        alarm_description=f"Temperature exceeds {scope.temperature_max}°C"
    )
    temperature_high_alarm.add_alarm_action(cw_actions.SnsAction(sns_topic))

    # Low temperature alarm
    temperature_low_alarm = cloudwatch.Alarm(
        scope=scope,
        id="TemperatureLowAlarm-"+scope.thing_name,
        alarm_name="sap-iot-temperature-low-"+scope.thing_name,
        metric=temperature_metric,
        threshold=float(scope.temperature_min),
        comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
        evaluation_periods=3,
        datapoints_to_alarm=3,
        alarm_description=f"Temperature below {scope.temperature_min}°C"
    )
    temperature_low_alarm.add_alarm_action(cw_actions.SnsAction(sns_topic))

    return {
        "rule": iot_rule,
        "high_alarm": temperature_high_alarm,
        "low_alarm": temperature_low_alarm
    }