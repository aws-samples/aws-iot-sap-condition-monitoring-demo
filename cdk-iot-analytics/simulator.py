import os
import json
import time
import random
import boto3
import click
from botocore.client import Config
import paho.mqtt.client as mqtt

config = json.load(open('cdk.json', 'r'))
outputs = json.load(open('iot-outputs.json', 'r'))
thing_name = config["context"]["thing_name"]
cert_file_path = f'certs/{thing_name}.cert.pem'
temp_min = float(config["context"]["temperature_min"])
temp_max = float(config["context"]["temperature_max"])

@click.command()
@click.option(
    "--region",
    prompt="Specify the AWS Region",
    help="This is the AWS Region the CDK was bootstrapped to."
)

@click.option(
    "--overtemp/--no-overtemp",
    help="When enabled, report temperatures over the max to force an alarm.",
    default=False
)

@click.option(
    "--undertemp/--no-undertemp",
    help="When enabled, report temperatures under the min to force an alarm.",
    default=False
)
def run(region, overtemp, undertemp):

    if not os.path.exists(cert_file_path):
        c = boto3.client(
            'iot',
            region_name=region,
            config=Config(connect_timeout=5)
        )
        with open(cert_file_path, 'w') as pem:
            pem.write(
                c.describe_certificate(
                    certificateId=outputs['cdk-iot-for-sap-iot']['CertificateId']
                )['certificateDescription']['certificatePem']
            )

    def on_connect(client, userdata, flags, rc):
        click.echo(f"Connected with result code: {rc}")

    client = mqtt.Client(client_id=thing_name)
    client.on_connect = on_connect
    client.tls_set(
        ca_certs='certs/AmazonRootCA1.pem', 
        certfile=f'certs/{thing_name}.cert.pem', 
        keyfile=f'certs/{thing_name}.key.pem'
    )
    client.connect(
        outputs['cdk-iot-for-sap-iot']['DescribeEndpoint'], 
        8883, 
        60
    )

    client.loop_start()
    time.sleep(1.0)


    while True:
        try:
            if overtemp:
                temperature = random.uniform(temp_max + 0.001, temp_max + 4)
            elif undertemp:
                temperature = random.uniform(temp_min - 4, temp_min - 0.001)
            else:
                temperature = random.uniform(temp_min + 0.001, temp_max - 0.001)

            payload = json.dumps({
                "e": {
                    # NOTE: to trigger alarm, edit the "t" value
                    # to be below/above min/max temperatures
                    "t": temperature,
                    "h": random.uniform(0.0, 25.0),
                    "d": random.uniform(0.0, 25.0),
                    "i": random.uniform(20.0, 25.0)
                },
                "l": {
                    "c": {
                        "o": "AT&T",
                        "a": [
                            {
                                "i": 1704630,
                                "l": 56986,
                                "c": 310,
                                "n": 410
                            }
                        ]
                    }
                }
            })
            client.publish(
                f'dt/{thing_name}',
                payload=payload,
                qos=1
            )
            click.echo(f"published: {payload}")
            time.sleep(1.0)
        except KeyboardInterrupt:
            exit(0)


if __name__ == '__main__':
    run()