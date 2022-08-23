# Copyright 2010-2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# This file is licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License. A copy of the
# License is located at
#
# http://aws.amazon.com/apache2.0/
#
# This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
#

import json
import boto3
import os
import sys
import xmltodict as xml
import requests
from requests.auth import HTTPBasicAuth
from botocore.exceptions import ClientError


region = os.environ['AWS_REGION']
sapHostName=os.environ['sapHostName']
urlPrefix=os.environ['urlPrefix']
sapPort=os.environ['sapPort']
odpServiceName=os.environ['odpServiceName']
odpEntitySetName=os.environ['odpEntitySetName']
snsAlertEmailTopic = os.environ['snsAlertEmailTopic']
secretName = os.environ['SECRET_NAME']

sns_client = boto3.client('sns')

# ------------------------------------
# Get base url for HTTP calls to SAP
# ------------------------------------
def _get_base_url():
    global sapPort
    global urlPrefix
    if urlPrefix == "":
        urlPrefix = "http://"
    if sapPort == "":
        sapPort = "50000"
    return urlPrefix + sapHostName + ":" + sapPort + "/sap/opu/odata/sap/" + odpServiceName

# ------------------------------------
# Get Username and Password from Secret Manager
# ------------------------------------    
def _get_secret():

    secret_name = secretName
    region_name = region

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )

    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            return get_secret_value_response['SecretString']
        else:
            return base64.b64decode(get_secret_value_response['SecretBinary'])
    
    
# ------------------------
# Start of Program
# ------------------------  
def lambda_handler(event, context):
    print(f"event: {event}")
    
    sapcred=json.loads(_get_secret())
    sapUser=sapcred["username"]
    sapPassword=sapcred["password"]
    
    # Retrieve the CSRF token first
    url = _get_base_url()
    session = requests.Session()

    try:
        response = session.head(url, auth=HTTPBasicAuth(sapUser,sapPassword), headers={'x-csrf-token': 'fetch'})
        token = response.headers.get('x-csrf-token', '')
        print(f"SAP session response text: {response.text}")
        
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError) as err:
        print("Connection to SAP System timed out: " + str(err.__class__.__name__))
        print("Is this the correct hostname and port number?")
        sys.exit(1)
    
    print(f"SAP session response code: {response.status_code}")

    # Execute Post request
    try:
        url = _get_base_url() + "/" + odpEntitySetName
        headers = {
            "Content-Type" : "application/json; charset=utf-8",
            "X-CSRF-Token" : token
        }

        print(f"SAP POST url: {url}")
        print(f"SAP POST headers: {headers}")
        print(f"SAP POST body: {event}")

        response = session.post(
            url,
            auth=HTTPBasicAuth(sapUser,sapPassword),
            headers=headers,
            json=event,
            verify=False
        )

        print(f"SAP POST response: {response}")
        print(f"SAP POST response code: {response.status_code}")
        print(f"SAP POST response text: {response.text}")
        print(f"SAP POST response headers: {response.headers}")

        if response.status_code == 201:
            message = (response.headers["sap-message"])
            print("Data successfully created in SAP")
            print(response.headers["sap-message"])
            try:
                tmp = v = xml.parse(message)
                message = (f"SAP Service {tmp['notification']['message']} for temperature alarm!")
            except Exception as exc:
                print(f'xml parser failed: {exc}')
            sns_client.publish(
                TopicArn=snsAlertEmailTopic,
                Message=message
            )
        
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError) as err:
        print("Connection to SAP System timed out: " + str(err.__class__.__name__))
        print("Is this the correct hostname and port number?")
        sys.exit(1)
  
    print(response.status_code)

    

