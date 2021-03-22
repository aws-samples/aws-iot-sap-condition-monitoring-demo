import aws_cdk.aws_iot as iot

def get_all_mqtt_rule(scope, role_arn, logger_arn, error_log_arn):
    return iot.CfnTopicRule(
        scope=scope,
        rule_name='CDKSAPBlog_AllMQTTRule',
        id="CDKSAPBlog_AllMQTTRule",
        topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
            description='Log all MQTT messages.',
            aws_iot_sql_version='2016-03-23',
            sql=f"""SELECT * as payload, topic() as topic FROM '#'""",
            rule_disabled=False,
            actions=[
                iot.CfnTopicRule.ActionProperty(
                    lambda_=iot.CfnTopicRule.LambdaActionProperty(
                        function_arn=logger_arn
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

