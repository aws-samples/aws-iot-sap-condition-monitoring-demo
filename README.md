# IoT For SAP CDK Solution

> [!IMPORTANT]  
> This solution has been updated to replace IoT Events, IoT Analytics

This solution was written by Kenny Rajan, Patrick Leung, Scott Francis, Will Charlton & Ganesh Suryanarayan for the [Predictive Maintenance using SAP and AWS IoT to reduce operational cost](https://aws.amazon.com/blogs/awsforsap/predictive-maintenance-using-sap-and-aws-iot-to-reduce-operational-cost/) blog post.

The purpose of this project is to deploy AWS `cdk` stacks that provide an end-to-end solution for creating SAP ticket alerts by monitoring device telemetry.

*AWS Resources created in this project include:*

|||||
|:-:|:-:|-|-|
| IoT Thing | IoT Rules  | IoT Policy | IoT Certificate |
| CloudWatch Metric | CloudWatch Alarm | EventBridge Rule | StepFunction |
| IAM Policies | IAM Roles | SNS Topic | |
| DynamoDB Table | Lambda Functions | Lambda Layer | Secrets Manager |


*Other items include:*

|||||
|:-:|:-:|-|-|
| X509 Private Key | X509 Certificate Signing Request (CSR) |  |  |

## Target Architecture

<todo>

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
| AWS CDK v2         | https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html              |
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
| `Type`                  | Thing description/tag                 |
| `sapEquipment`             | A setting specific to the SAP env.          |
| `sapFunctLoc`              | A setting specific to the SAP env.          |
| `temperature_min`       | Low Value used for determining Alarm condition       |
| `temperature_max`       | High Value used for determining Alarm condition       |
| `dynamodb_table`        |     The Amazon DynamoDb table name                         |
| `alarm_emails`          | A list of email addresses to send alarm emails   |
| `sapOdpEntitySetName`      | Odata service entity set name                    |
| `sapOdpServiceName`        | Odata service service name                  |
| `sapHostName`           | The hostname or IP address of the SAP server             |
| `sapPort`               | The port or IP address of the SAP server                 |
| `sapUsername`           | The SAP server username                          |
| `sapPassword`           | The SAP server password                          |
| `sapUrlPrefix`             | Either http:// or https://                       |


## Deploy the IoT Stack

**NOTE:** You might need to update your CDK before deployment:

```bash
npm install -g aws-cdk@latest --force
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

Take down the 3 stacks.

```bash
cdk destroy --all
```

**NOTE 1:** Sometimes the `destroy` command (above) needs to be run twice.
**NOTE 2:** Once everything is destroyed, make sure to delete the keys and certs in the `certs/` directory before re-deploying.