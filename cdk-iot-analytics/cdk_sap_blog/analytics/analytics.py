import json
import analytics.rules as rules
import analytics.lambda_ as _lambda_
from aws_cdk import core
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_iam as iam
import aws_cdk.aws_iotanalytics as analytics
import aws_cdk.aws_iotevents as iotevents


def get_analytics_channel(scope):
    return analytics.CfnChannel(
        scope=scope,
        id="CDKSAPBlogAnalyticsChannel",
        channel_name="CDKSAPBlogAnalyticsChannel",
    )

def get_analytics_datastore(scope):
    return analytics.CfnDatastore(
        scope=scope,
        id="CDKSAPBlogAnalyticsDatastore",
        datastore_name="CDKSAPBlogAnalyticsDatastore",
        datastore_storage=analytics.CfnDatastore.DatastoreStorageProperty(
            service_managed_s3={}
        ),
        retention_period=analytics.CfnDatastore.RetentionPeriodProperty(
            number_of_days=1
        ),
    )

def get_analytics_pipeline(scope, datastore_name, error_log_arn=None):
    m_channel = get_analytics_channel(scope)
    m_lambda = _lambda_.get_product_range(scope)

    enrich_activity_name = "CDKSAPBlogAnalyticsRegistryEnrichActivity"

    enrich_role = iam.Role(
        scope=scope,
        id="CDKSAPBlogAnalyticsRegistryEnrichRole",
        role_name="CDKSAPBlogAnalyticsRegistryEnrichRole",
        assumed_by=iam.ServicePrincipal('iotanalytics.amazonaws.com'),
    )
    enrich_role.add_to_policy(
        iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            resources=[f'arn:aws:iot:{scope.region}:{scope.account}:thing/{scope.thing_name}'],
            actions=['iot:DescribeThing',]
        )
    )
    enrich_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSIoTThingsRegistration'))
    enrich_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSIoTLogging'))
    enrich_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSIoTRuleActions')) 
    enrich_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AWSIoTAnalyticsFullAccess'))
    enrich_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AWSIoTConfigReadOnlyAccess'))
    enrich_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AWSIoTDataAccess'))
    enrich_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AWSIoTFullAccess'))

    enrich_rule_role = iam.Role(
        scope=scope,
        id="CDKSAPBlogAnalyticsRuleRegistryEnrichRole",
        role_name="CDKSAPBlogAnalyticsRuleRegistryEnrichRole",
        assumed_by=iam.ServicePrincipal('iot.amazonaws.com'),
    )
    enrich_rule_role.add_to_policy(
        iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            resources=[f"arn:aws:iotanalytics:{scope.region}:{scope.account}:channel/{m_channel.channel_name}"],
            actions=['iotanalytics:BatchPutMessage',]
        )
    )
    enrich_rule_role.node.add_dependency(m_channel)

    iot_rule = rules.get_analytics_rule(
        scope, 
        m_channel.channel_name, 
        enrich_rule_role.role_arn,
        error_log_arn=error_log_arn
    )

    pipeline = analytics.CfnPipeline(
        scope=scope,
		id="CDKSAPBlogAnalyticsPipeline",
        pipeline_name="CDKSAPBlogAnalyticsPipeline",
        pipeline_activities=[
            analytics.CfnPipeline.ActivityProperty(
                channel={
                    "channelName": m_channel.channel_name,
                    "name" : m_channel.channel_name,
                    "next" : enrich_activity_name
                }
            ),
            analytics.CfnPipeline.ActivityProperty(
                device_registry_enrich={
                    "name": enrich_activity_name,
                    "attribute": "registry",
                    "thingName": "thingname", # scope.thing_name,
                    "roleArn": enrich_role.role_arn,
                    "next": "RemoveAttributesActivity"
                }
            ),
            analytics.CfnPipeline.ActivityProperty(
                remove_attributes={
                    "name": "RemoveAttributesActivity",
                    "attributes": [
                        "registry.billingGroupName",
                        "registry.defaultClientId",
                        "registry.thingArn",
                        "registry.thingId",
                        "registry.thingName",
                        # "registry.attributes",
                        "registry.thingTypeName",
                        "registry.version"
                    ],
                    "next": m_lambda.function_name
                }
            ),
            analytics.CfnPipeline.ActivityProperty(
                lambda_={
                    "batchSize" : 3,
                    "lambdaName" : m_lambda.function_name,
                    "name" : m_lambda.function_name,
                    "next" : "SAPBlogDatastore"
                }
            ),
            analytics.CfnPipeline.ActivityProperty(
                datastore={
                    "name": "SAPBlogDatastore",
                    "datastoreName": datastore_name
                }
            )
        ]
    )
    return pipeline

def get_events_input(scope):
    return iotevents.CfnInput(
        scope=scope,
        id=f"CDKSAPBlogEventsInput",
        input_name=f"CDKSAPBlogEventsInput",
        input_definition=iotevents.CfnInput.InputDefinitionProperty(
            attributes=[
                iotevents.CfnInput.AttributeProperty(json_path='endTime'),
                iotevents.CfnInput.AttributeProperty(json_path='durS',),
                iotevents.CfnInput.AttributeProperty(json_path='thingname'),
                iotevents.CfnInput.AttributeProperty(json_path='temperature_degC_mean'),
                iotevents.CfnInput.AttributeProperty(json_path='humidity_percent_mean'),
                iotevents.CfnInput.AttributeProperty(json_path='dewpoint_degC_mean'),
                iotevents.CfnInput.AttributeProperty(json_path='heatIndex_degC_mean'),
                iotevents.CfnInput.AttributeProperty(json_path='maxTemp_degC'),
                iotevents.CfnInput.AttributeProperty(json_path='minTemp_degC'),
                iotevents.CfnInput.AttributeProperty(json_path='location'),
                iotevents.CfnInput.AttributeProperty(json_path='Equipment'),
                iotevents.CfnInput.AttributeProperty(json_path='FunctLoc'),
                iotevents.CfnInput.AttributeProperty(json_path='Type'),
            ]
        )
    )

def get_analytics_dataset(scope, datastore_name, input_name):
    bucket_name = f"cdksapbloganalyticsdatasetbucket-{scope.thing_name}"
    dataset_name = "CDKSAPBlogAnalyticsDataset"

    bucket_service_role = iam.Role(
        scope=scope,
        id="CDKSAPBlogDatasetBucketRole",
        role_name="CDKSAPBlogDatasetBucketRole",
        assumed_by=iam.ServicePrincipal('iotanalytics.amazonaws.com')
    )
    bucket_service_role.add_to_policy(
        iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            resources=[f'arn:aws:s3:::{bucket_name}/*'],
            actions=['s3:PutObject',]
        )
    )
    bucket = s3.Bucket(
        scope=scope,
        id=bucket_name,
        bucket_name=bucket_name,
        block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        public_read_access=False,
        removal_policy=core.RemovalPolicy.DESTROY
    )

    # outputß
    core.CfnOutput(
        scope=scope,
        id="AnalyticsBucketURI",
        export_name=f"AnalyticsBucketURI",
        value=f"s3://{bucket.bucket_name}"
    )


    dataset_service_role = iam.Role(
        scope=scope,
        id="CDKSAPBlogDatasetInputRole",
        role_name="CDKSAPBlogDatasetInputRole",
        assumed_by=iam.ServicePrincipal('iotanalytics.amazonaws.com')
    )
    dataset_service_role.add_to_policy(
        iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            resources=[f'arn:aws:iotevents:{scope.region}:{scope.account}:input/{input_name}'],
            actions=['iotevents:BatchPutMessage',]
        )
    )
    return analytics.CfnDataset(
        scope=scope,
        id=dataset_name,
        dataset_name=dataset_name,
        actions=[
            analytics.CfnDataset.ActionProperty(
                action_name="QueryAnalyticsDatastore",
                query_action=analytics.CfnDataset.QueryActionProperty(
                    sql_query=f'''SELECT max(timestamp) AS endTime, (to_unixtime(from_iso8601_timestamp(max(timestamp))) - to_unixtime(from_iso8601_timestamp(min(timestamp)))) AS durS, max_by(thingname, timestamp) as thingname, avg(temperature_degC) AS temperature_degC_mean, avg(humidity_percent) AS humidity_percent_mean, avg(dewpoint_degC) AS dewpoint_degC_mean, avg(heatIndex_degC) AS heatIndex_degC_mean, max_by(range.temperature.max, timestamp) AS maxTemp_degC, max_by(range.temperature.min, timestamp) AS minTemp_degC, max_by(location, timestamp) AS location, max_by(FunctLoc, timestamp) as FunctLoc, max_by(Equipment, timestamp) as Equipment, max_by(Type, timestamp) as Type FROM {datastore_name}''',
                    filters=[
                        analytics.CfnDataset.FilterProperty(
                            delta_time=analytics.CfnDataset.DeltaTimeProperty(
                                offset_seconds=-5,
                                time_expression='from_iso8601_timestamp(timestamp)'
                            )
                        )
                    ]
                )
            )
        ],
        triggers=[
            analytics.CfnDataset.TriggerProperty(
                schedule=analytics.CfnDataset.ScheduleProperty(
                    schedule_expression='cron(0/1 * * * ? *)'
                )
            )
        ],
        retention_period=analytics.CfnDataset.RetentionPeriodProperty(
            number_of_days=90,
            unlimited=False
        ),
        versioning_configuration=analytics.CfnDataset.VersioningConfigurationProperty(
            unlimited=True
        ),
        content_delivery_rules=[
            analytics.CfnDataset.DatasetContentDeliveryRuleProperty(
                destination=analytics.CfnDataset.DatasetContentDeliveryRuleDestinationProperty(
                    s3_destination_configuration=analytics.CfnDataset.S3DestinationConfigurationProperty(
                        bucket=bucket_name,
                        key=f"{dataset_name}/Version/!{{iotanalytics:scheduleTime}}_!{{iotanalytics:versionId}}.csv",
                        role_arn=bucket_service_role.role_arn
                    ),
                )
            ),
            analytics.CfnDataset.DatasetContentDeliveryRuleProperty(
                destination=analytics.CfnDataset.DatasetContentDeliveryRuleDestinationProperty(
                    iot_events_destination_configuration=analytics.CfnDataset.IotEventsDestinationConfigurationProperty(
                        input_name=input_name,
                        role_arn=dataset_service_role.role_arn
                    ),
                )
            )
        ],
    )

def get_detector_model(scope, input_name, sns_arn):
    role = iam.Role(
        scope=scope,
        id="CDKSAPBlogEventDetectorRole",
        role_name="CDKSAPBlogEventDetectorRole",
        assumed_by=iam.ServicePrincipal('iotevents.amazonaws.com')
    )
    [
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(policy)
        ) for policy in [
            'AWSIoTEventsFullAccess',
            'service-role/AmazonSNSRole',
            'AmazonSNSFullAccess',
            'AWSLambda_FullAccess',
            'service-role/AWSLambdaRole'
        ]
    ]

    def get_state_lambda_payload(state):
        return f"""'{{
    "d": {{
        "Equipment": "${{$input.{input_name}.Equipment}}",
        "FunctLoc": "${{$input.{input_name}.FunctLoc}}",
        "ShortText": "Temperature Alarm[{state}]",
        "LongText": "Temperature Alarm in ${{$input.{input_name}.Type}} Motor"
    }}
}}'"""

    return iotevents.CfnDetectorModel(
        scope=scope,
        id="CDKSAPBlogDetectorModel",
        detector_model_name="CDKSAPBlogDetectorModel",
        detector_model_description='Detect temperature in a given range.',
        evaluation_method="BATCH",
        key="thingname",
        role_arn=role.role_arn,
        detector_model_definition=iotevents.CfnDetectorModel.DetectorModelDefinitionProperty(
            initial_state_name="TempInRange",
            states=[
                iotevents.CfnDetectorModel.StateProperty(
                    state_name="OverTemp",
                    on_input=iotevents.CfnDetectorModel.OnInputProperty(
                        events=[],
                        transition_events=[
                            iotevents.CfnDetectorModel.TransitionEventProperty(
                                event_name="overTempTooLong",
                                condition="timeout(\"hiTempDur\")",
                                actions=[],
                                next_state="OverTempAlarm"
                            ),
                            iotevents.CfnDetectorModel.TransitionEventProperty(
                                event_name="tempBelowMax",
                                condition=f"convert(Decimal,$input.{input_name}.temperature_degC_mean) < convert(Decimal,$input.{input_name}.maxTemp_degC)",
                                actions=[],
                                next_state="TempInRange"
                            )
                        ]
                    ),
                    on_enter=iotevents.CfnDetectorModel.OnEnterProperty(
                        events=[
                            iotevents.CfnDetectorModel.EventProperty(
                                event_name="startTimer",
                                condition="true",
                                actions=[
                                    iotevents.CfnDetectorModel.ActionProperty(
                                        set_timer=iotevents.CfnDetectorModel.SetTimerProperty(
                                            duration_expression=None,
                                            timer_name="hiTempDur",
                                            seconds=300
                                        )
                                    )
                                ]
                            )
                        ]
                    ),
                    on_exit=iotevents.CfnDetectorModel.OnExitProperty(
                        events=[
                            iotevents.CfnDetectorModel.EventProperty(
                                event_name="deleteTimer",
                                condition="true",
                                actions=[
                                    iotevents.CfnDetectorModel.ActionProperty(
                                        clear_timer=iotevents.CfnDetectorModel.ClearTimerProperty(
                                            timer_name="hiTempDur"
                                        )
                                    )
                                ]
                            )
                        ]
                    )
                ),
                iotevents.CfnDetectorModel.StateProperty(
                    state_name="UnderTemp",
                    on_input=iotevents.CfnDetectorModel.OnInputProperty(
                        events=[],
                        transition_events=[
                            iotevents.CfnDetectorModel.TransitionEventProperty(
                                event_name="underTempTooLong",
                                condition="timeout(\"loTempDur\")",
                                actions=[],
                                next_state="UnderTempAlarm"
                            ),
                            iotevents.CfnDetectorModel.TransitionEventProperty(
                                event_name="tempAboveMin",
                                condition=f"convert(Decimal,$input.{input_name}.temperature_degC_mean) > convert(Decimal,$input.{input_name}.minTemp_degC)",
                                actions=[],
                                next_state="TempInRange"
                            )
                        ]
                    ),
                    on_enter=iotevents.CfnDetectorModel.OnEnterProperty(
                        events=[
                            iotevents.CfnDetectorModel.EventProperty(
                                event_name="startTimer",
                                condition="true",
                                actions=[
                                    iotevents.CfnDetectorModel.ActionProperty(
                                        set_timer=iotevents.CfnDetectorModel.SetTimerProperty(
                                            timer_name="loTempDur",
                                            seconds=300,
                                            duration_expression=None
                                        )
                                    )
                                ]
                            )
                        ]
                    ),
                    on_exit=iotevents.CfnDetectorModel.OnExitProperty(
                        events=[
                            iotevents.CfnDetectorModel.EventProperty(
                                event_name="deleteTimer",
                                actions=[
                                    iotevents.CfnDetectorModel.ActionProperty(
                                        clear_timer=iotevents.CfnDetectorModel.ClearTimerProperty(
                                            timer_name="loTempDur"
                                        )
                                    )
                                ]
                            )
                        ]
                    )
                ),
                iotevents.CfnDetectorModel.StateProperty(
                    state_name="TempInRange",
                    on_input=iotevents.CfnDetectorModel.OnInputProperty(
                        events=[
                            iotevents.CfnDetectorModel.EventProperty(
                                event_name="readTemp",
                                condition="true",
                                actions=[
                                    iotevents.CfnDetectorModel.ActionProperty(
                                        set_variable=iotevents.CfnDetectorModel.SetVariableProperty(
                                            variable_name="temperature_degC",
                                            value=f"convert(Decimal, $input.{input_name}.temperature_degC_mean)"
                                        )
                                    )
                                ]
                            )
                        ],
                        transition_events=[
                            iotevents.CfnDetectorModel.TransitionEventProperty(
                                event_name="tempAboveMax",
                                condition=f"convert(Decimal, $input.{input_name}.temperature_degC_mean) > convert(Decimal, $input.{input_name}.maxTemp_degC)",
                                actions=[],
                                next_state="OverTemp"
                            ),
                            iotevents.CfnDetectorModel.TransitionEventProperty(
                                event_name="tempBelowMin",
                                condition=f"convert(Decimal,$input.{input_name}.temperature_degC_mean) < convert(Decimal,$input.{input_name}.minTemp_degC)",
                                actions=[],
                                next_state="UnderTemp"
                            )
                        ]
                    ),
                    on_enter=iotevents.CfnDetectorModel.OnEnterProperty(
                        events=[
                            iotevents.CfnDetectorModel.EventProperty(
                                event_name="inRange",
                                condition="true",
                                actions=[
                                    iotevents.CfnDetectorModel.ActionProperty(
                                        lambda_=iotevents.CfnDetectorModel.LambdaProperty(
                                            function_arn=sns_arn,
                                            payload=iotevents.CfnDetectorModel.PayloadProperty(
                                                content_expression=get_state_lambda_payload("TempInRange:inRange"),
                                                type="JSON"
                                            )
                                        )
                                    )
                                ]
                            ),
                            iotevents.CfnDetectorModel.EventProperty(
                                event_name="sendAlert",
                                condition="true",
                                actions=[
                                    iotevents.CfnDetectorModel.ActionProperty(
                                        lambda_=iotevents.CfnDetectorModel.LambdaProperty(
                                            function_arn=sns_arn,
                                            payload=iotevents.CfnDetectorModel.PayloadProperty(
                                                content_expression=get_state_lambda_payload("TempInRange.sendAlert"),
                                                type="JSON"
                                            )
                                        )
                                    )
                                ]
                            )
                        ]
                    ),
                    on_exit=iotevents.CfnDetectorModel.OnExitProperty(
                        events=[]
                    )
                ),
                iotevents.CfnDetectorModel.StateProperty(
                    state_name="UnderTempAlarm",
                    on_input=iotevents.CfnDetectorModel.OnInputProperty(
                        events=[],
                        transition_events=[
                            iotevents.CfnDetectorModel.TransitionEventProperty(
                                event_name="tempAboveMin",
                                condition=f"convert(Decimal,$input.{input_name}.temperature_degC_mean) > convert(Decimal,$input.{input_name}.minTemp_degC)",
                                actions=[],
                                next_state="TempInRange"
                            )
                        ]
                    ),
                    on_enter=iotevents.CfnDetectorModel.OnEnterProperty(
                        events=[
                            iotevents.CfnDetectorModel.EventProperty(
                                event_name="sendAlert",
                                condition="true",
                                actions=[
                                    iotevents.CfnDetectorModel.ActionProperty(
                                        lambda_=iotevents.CfnDetectorModel.LambdaProperty(
                                            function_arn=sns_arn,
                                            payload=iotevents.CfnDetectorModel.PayloadProperty(
                                                content_expression=get_state_lambda_payload("UnderTempAlarm.sendAlert"),
                                                type="JSON"
                                            )
                                        )
                                    )
                                ]
                            )
                        ]
                    ),
                    on_exit=iotevents.CfnDetectorModel.OnExitProperty(
                        events=[]
                    )
                ),
                iotevents.CfnDetectorModel.StateProperty(
                    state_name="OverTempAlarm",
                    on_input=iotevents.CfnDetectorModel.OnInputProperty(
                        events=[],
                        transition_events=[
                            iotevents.CfnDetectorModel.TransitionEventProperty(
                                event_name="tempBelowMax",
                                condition=f"convert(Decimal,$input.{input_name}.temperature_degC_mean) < convert(Decimal,$input.{input_name}.maxTemp_degC)",
                                actions=[],
                                next_state="TempInRange"
                            )
                        ]
                    ),
                    on_enter=iotevents.CfnDetectorModel.OnEnterProperty(
                        events=[
                            iotevents.CfnDetectorModel.EventProperty(
                                event_name="sendAlert",
                                condition="true",
                                actions=[
                                    iotevents.CfnDetectorModel.ActionProperty(
                                        lambda_=iotevents.CfnDetectorModel.LambdaProperty(
                                            function_arn=sns_arn,
                                            payload=iotevents.CfnDetectorModel.PayloadProperty(
                                                content_expression=get_state_lambda_payload("OverTempAlarm.sendAlert"),
                                                type="JSON"
                                            )
                                        )
                                    )
                                ]
                            )
                        ]
                    ),
                    on_exit=iotevents.CfnDetectorModel.OnExitProperty(
                        events=[]
                    )
                )
            ]
        ),
    )