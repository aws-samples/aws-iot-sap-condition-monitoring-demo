# IoT For SAP CDK Solution

This solution was written by Kenny Rajan, Patrick Leung, Scott Francis, Will Charlton & Ganesh Suryanarayan for the [Predictive Maintenance using SAP and AWS IoT to reduce operational cost](https://aws.amazon.com/blogs/awsforsap/predictive-maintenance-using-sap-and-aws-iot-to-reduce-operational-cost/) blog post.

The purpose of this project is to deploy AWS `cdk` stacks that provide an end-to-end solution for creating SAP ticket alerts by monitoring device telemetry.

*AWS Resources created in this project include:*

|||||
|:-:|:-:|-|-|
| IoT Thing | IoT Events | IAM Policies | IoT Rules |
| IoT Analytics | IAM Roles | IoT Policy | IoT Certificate |
| DynamoDB Tables | Lambdas | SNS | Secrets Manager |


*Other items include:*

|||||
|:-:|:-:|-|-|
| X509 Private Key | X509 Certificate Signing Request (CSR) |  |  |

**NOTE:**

- If you are using a device or other simulator with its own private key, place the CSR in the `certs/` directory with:
  - The filename `<thing_name>.csr.pem`
  - The X509 Certificate Subject's `CommonName` is the `<thing_name>`
  - e.g. `certs/my_device_1.csr.pem` == `/CN=my_device_1` 

- If you do not have a private key and CSR you want to use, they will be created for you on when the stack is deployed.

Once the `iot` stack is deployed the device X509 Certificate will be located in `certs/<thing_name>.cert.pem`.

### Prerequisites

| Tool            | Link                                                                           |
|-----------------|--------------------------------------------------------------------------------|
| AWS CDK         | https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html              |
| `python3`       | https://www.python.org/downloads/                                              |

### Set Up Local Environment

```bash
git clone https://github.com/aws-samples/aws-iot-sap-condition-monitoring-demo.git
cd aws-iot-sap-condition-monitoring-demo
cd cdk-iot-analytics
python3 -m venv .venv
source .venv/bin/activate
mkdir certs
pip install -r requirements.txt
```

## Define Variables

Configure stack variables in `cdk.json`:

| Variable                | Description                                      |
|-------------------------|--------------------------------------------------|
| `thing_name`            | The AWS IoT Thing name                           |
| `Type`                  | A setting specific to the SAP customer           |
| `Equipment`             | A setting specific to the SAP customer           |
| `FunctLoc`              | A setting specific to the SAP customer           |
| `temperature_min`       | Value used for determining Alarm condition       |
| `temperature_max`       | Value used for determining Alarm condition       |
| `sns_alert_email_topic` | The SNS topic name used for sending alarm emails |
| `alarm_emails`          | A list of email addresses to send alarm emails   |
| `odpEntitySetName`      | An Open Data Protocol setting                    |
| `odpServiceName`        | An Open Data Protocol setting                    |
| `sapHostName`           | The hostname or IP of the SAP server             |
| `sapPort`               | The port or IP of the SAP server                 |
| `sapUsername`           | The SAP server username                          |
| `sapPassword`           | The SAP server password                          |
| `urlPrefix`             | Either http:// or https://                       |


## Deploy the IoT Stack

**NOTE:** You might need to update your CDK before deployment:

```bash
npm install aws-cdk -g --force
```

**NOTE:** Bootstrapping CDK to the target account/region may be necessary: 

```bash
cdk bootstrap aws://<account>/<region>
```

Deploy initial stack

```bash
cdk deploy iot -O=iot-outputs.json
```

**IMPORTANT:** The CloudFormation outputs must be saved to `iot-outputs.json` in order for the device simulator to work (see below).

## Deploy the SAP Stack

For technical and legal reasons, we do not package some dependencies in this repository, so they must be packaged before deploying the SAP stack. Do this with the command, below:

```bash
pip install \
    requests \
    xmltodict \
    -t ./cdk_sap_blog/sap/lambda_assets/layer/python/
```

Once `requests` and `xmltodict` are packaged for the lambda layer, the stack can be deployed with the command, below:

```bash
cdk deploy sap
```

**IMPORTANT:** You should recieve a subscription notification to the emails in `cdk.json/alarm_emails`). _Make sure you Confirm the subscription_.

## Deploy the Analytics Stack

```bash
cdk deploy analytics -O=analytics-outputs.json
```

## Update Detector Model to latest version

```bash
cd cdk_sap_blog/analytics
AWSACCOUNTID=$(aws sts get-caller-identity --query Account --output text)
sed -i 's/AWSACCOUNTID/'$AWSACCOUNTID'/g' detector_model.json
aws iotevents update-detector-model --cli-input-json file://detector_model.json
cd..
cd..
```

## Test Alarm

### Test Configuration Variables

The simulator uses the `temperature_min`/`temperature_max` variables you defined in `cdk.json` to report temperatures uniformly to be a few degrees hotter than the maximum (see `simulator.py:L50`).

An alarm should be triggered shortly after starting the simulator.

### Runing The Simulator

The `AWS_REGION` is needs to be set to the same AWS Region used to bootstrap CDK (above). 

```bash
python simulator.py --region=<AWS_REGION>
python simulator.py --region=<AWS_REGION> --overtemp
python simulator.py --region=<AWS_REGION> --undertemp
```

Once the Alarm is triggered, the end-to-end solution has completed.

**NOTE:** See `python simulator.py --help` for more options.

## Cleanup

The destroy operation (below) will fail unless we first remove (or save somewhere else) the objects in the S3 bucket we used to store the IoT Analytics data. Get the name of the bucket from the `analytics-outputs.json` file we created in the `deploy` operation.

```bash
aws s3 rm <analytics.AnalyticsBucketURI> --recursive
```

Then feel free to take down the 3 stacks.

```bash
cdk destroy --all
```

**NOTE 1:** Sometimes the `destroy` command (above) needs to be run twice.
**NOTE 2:** Once everything is destroyed, make sure to delete the keys and certs in the `certs/` directory before re-deploying.

# APPENDIX

## Diagram

Architecture diagram was designed with [PlantUML](https://plantuml.com/) and [AWS Icons for PlantUML](https://github.com/awslabs/aws-icons-for-plantuml). Once your system is configured, run the following command to generate the diagram:

```bash
java -jar plantuml.jar iot-for-sap-architecture.puml
```

**NOTE:** If you don't know the path to your `plantuml.jar` file, find it with `find / -name plantuml.jar 2>/dev/null`.

The diagram will be saved as `iot-for-sap-architecture.png`.

