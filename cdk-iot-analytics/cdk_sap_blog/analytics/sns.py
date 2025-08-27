import aws_cdk.aws_sns as awssns


def create_sns_topic(scope, alarm_emails):
    return awssns.CfnTopic(
        scope=scope,
        id=f"sap-iot-sns-topic",
        display_name="sap-iot-temperature-alarm",
        topic_name="sap-iot-temperature-alarm",
        subscription=[
            awssns.CfnTopic.SubscriptionProperty(
                endpoint=email,
                protocol="EMAIL"
            ) for email in alarm_emails     
        ]
    )

