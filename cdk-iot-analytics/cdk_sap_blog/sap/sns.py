import aws_cdk.aws_sns as awssns


def get_sap_response_email_sns_topic(scope, alarm_emails):
    return awssns.CfnTopic(
        scope=scope,
        id=f"CDKSAPBlogSNSSAPResponseTopic",
        display_name=scope.sns_alert_email_topic,
        topic_name=scope.sns_alert_email_topic,
        subscription=[
            awssns.CfnTopic.SubscriptionProperty(
                endpoint=email,
                protocol="EMAIL"
            ) for email in alarm_emails     
        ]
    )

