#!/bin/bash

mkdir certs

pip install -r requirements.txt

AWSACCOUNTID=$(aws sts get-caller-identity --query Account --output text)

cdk bootstrap aws://$AWSACCOUNTID/us-east-1

cdk deploy iot -O=iot-outputs.json --require-approval never

pip install \
    requests \
    xmltodict \
    -t ./cdk_sap_blog/sap/lambda_assets/layer/python/

cdk deploy sap --require-approval never

cdk deploy analytics -O=analytics-outputs.json --require-approval never

sed -i 's/AWSACCOUNTID/'$AWSACCOUNTID'/g' cdk_sap_blog/analytics/detector_model.json
aws iotevents update-detector-model --cli-input-json file://cdk_sap_blog/analytics/detector_model.json
