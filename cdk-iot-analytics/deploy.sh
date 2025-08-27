#!/bin/bash

set -e

if grep -R "<" cdk.json
then
   echo "cdk.json invalid! Kindly check and replace all parameters!"
elif grep -R ">" cdk.json
then
   echo "cdk.json invalid! Kindly check and replace all parameters!"
else
    echo "cdk.json validation successful!"

    mkdir -p certs
    
    pip install -r requirements.txt
    
    AWSACCOUNTID=$(aws sts get-caller-identity --query Account --output text)
    sudo yum install jq -y
    curl -H "Authorization: $AWS_CONTAINER_AUTHORIZATION_TOKEN" $AWS_CONTAINER_CREDENTIALS_FULL_URI 2>/dev/null > /tmp/credentials
    export AWS_ACCESS_KEY_ID =`cat /tmp/credentials| jq -r .AccessKeyId`
    export SECRET_KEY=`cat /tmp/credentials| jq -r .SecretAccessKey`
    export AWS_SESSION_TOKEN =`cat /tmp/credentials| jq -r .Token`#
    export AWS_DEFAULT_REGION=${AWS_REGION}
    
    cdk bootstrap aws://$AWSACCOUNTID/us-east-1
    
    cdk deploy iot -O=iot-outputs.json --require-approval never
    
    pip install \
        requests \
        xmltodict \
        -t ./cdk_sap_blog/sap/lambda_assets/layer/python/
    
    cdk deploy sap --require-approval never
    
    cdk deploy analytics -O=analytics-outputs.json --require-approval never

fi
