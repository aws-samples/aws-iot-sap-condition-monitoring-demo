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
    
    #sudo yum install jq -y
    curl -H "Authorization: $AWS_CONTAINER_AUTHORIZATION_TOKEN" $AWS_CONTAINER_CREDENTIALS_FULL_URI 2>/dev/null > /tmp/credentials
    ACCESS_KEY_ID=`cat /tmp/credentials| jq -r .AccessKeyId`
    SECR_KEY=`cat /tmp/credentials| jq -r .SecretAccessKey`
    SESSION_TOKEN=`cat /tmp/credentials| jq -r .Token`
    export AWS_ACCESS_KEY_ID=${ACCESS_KEY_ID}
    export AWS_SECRET_ACCESS_KEY=${SECR_KEY}
    export AWS_SESSION_TOKEN=${SESSION_TOKEN}
    export AWS_DEFAULT_REGION=${AWS_REGION}

    AWSACCOUNTID=$(aws sts get-caller-identity --query Account --output text)
    
    cdk bootstrap aws://$AWSACCOUNTID/$AWS_DEFAULT_REGION
    
    cdk deploy iot -O=iot-outputs.json --require-approval never

    cdk deploy analytics -O=analytics-outputs.json --require-approval never
    
    pip install \
        requests \
        xmltodict \
        -t ./cdk_sap_blog/sap/lambda_assets/layer/python/

    cdk deploy sap --require-approval never

fi
