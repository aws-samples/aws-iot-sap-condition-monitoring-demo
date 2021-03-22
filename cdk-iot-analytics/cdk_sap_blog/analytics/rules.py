import aws_cdk.aws_iot as iot

def get_analytics_rule(scope, channel_name, role_arn, error_log_arn):
    return iot.CfnTopicRule(
        scope=scope,
        rule_name='CDKSAPBlog_AnalyticsRule',
        id="CDKSAPBlog_AnalyticsRule",
        topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
            description='SAP Blog Rule to send device data to IoT Analytics',
            aws_iot_sql_version='2016-03-23',
            sql=f"""SELECT parse_time("yyyy-MM-dd'T'HH:mm:ssZ", timestamp() ) AS timestamp, topic(2) AS thingname, e.t AS temperature_degC, e.h AS humidity_percent, e.d AS dewpoint_degC, e.i AS heatIndex_degC, l AS location FROM 'dt/{scope.thing_name}'""",
            rule_disabled=False,
            actions=[
                iot.CfnTopicRule.ActionProperty(
                    iot_analytics=iot.CfnTopicRule.IotAnalyticsActionProperty(
                        channel_name=channel_name,
                        role_arn=role_arn
                    )
                ),
            ],
            error_action=iot.CfnTopicRule.ActionProperty(
                lambda_=iot.CfnTopicRule.LambdaActionProperty(
                    function_arn=error_log_arn
                )
            )
        ),
    )
