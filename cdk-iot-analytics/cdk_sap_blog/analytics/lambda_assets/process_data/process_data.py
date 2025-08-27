import os
import sys
import json
import logging
import traceback
import boto3
from datetime import datetime, timezone


logger = logging.getLogger()
logger.setLevel(logging.INFO)
streamHandler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')
table = dynamodb.Table(os.environ['TABLE_NAME'])

# Cache for DynamoDB values
cache = {}

def handler(event, context):
    logger.info("events before processing: {}".format(event))
    
    # device_id = event['thingname']
    # current_temp = event['temperature_degC']
    # current_timestamp = datetime.now(timezone.utc).isoformat()
    
    # try:
    #     # Check if we have cached data for this device
    #     if device_id not in cache:
    #         # Initial read from DynamoDB
    #         item = table.get_item(Key={'DeviceID': device_id})
    #         if 'Item' in item:
    #             cache[device_id] = item['Item']
    #         else:
    #             logger.error(f"Device {device_id} not found in DynamoDB")
    #             return event
        
    #     cached_item = cache[device_id]
    #     temp_range = cached_item['range']['temperature']
    #     temp_min = float(temp_range['min'])
    #     temp_max = float(temp_range['max'])
        
    #     # Check if temperature is out of range
    #     temp_out_of_range = current_temp < temp_min or current_temp > temp_max
        
    #     if temp_out_of_range:
    #         logger.info("Temperature breach detected")
    #         # Check if we need to read from DynamoDB (1 minute threshold)
    #         should_read_db = True
    #         if 'Last_temperature_timestamp' in cached_item:
    #             last_timestamp = datetime.fromisoformat(cached_item['Last_temperature_timestamp'].replace('Z', '+00:00'))
    #             time_diff = (datetime.now(timezone.utc) - last_timestamp).total_seconds()
    #             should_read_db = time_diff >= 60
            
    #         if should_read_db:
    #             # Read fresh data from DynamoDB
    #             item = table.get_item(Key={'DeviceID': device_id})
    #             if 'Item' in item:
    #                 cache[device_id] = item['Item']
                
    #             # Update DynamoDB with new temperature and timestamp
    #             table.update_item(
    #                 Key={'DeviceID': device_id},
    #                 UpdateExpression='SET Last_temperature_degC = :temp, Last_temperature_timestamp = :ts',
    #                 ExpressionAttributeValues={
    #                     ':temp': current_temp,
    #                     ':ts': current_timestamp
    #                 }
    #             )

    #             logger.info("Update database/cache")
                
    #             # Update cache
    #             cache[device_id]['Last_temperature_degC'] = current_temp
    #             cache[device_id]['Last_temperature_timestamp'] = current_timestamp
        
    #     # Write temperature to CloudWatch as custom metric
    #     cloudwatch.put_metric_data(
    #         Namespace='IoT/Temperature',
    #         MetricData=[
    #             {
    #                 'MetricName': 'Temperature',
    #                 'Dimensions': [
    #                     {
    #                         'Name': 'DeviceID',
    #                         'Value': device_id
    #                     },
    #                     {
    #                         'Name': 'Equipment',
    #                         'Value': cached_item['SAPEquipmentNr']
    #                     }
    #                 ],
    #                 'Value': current_temp,
    #                 'Unit': 'None'
    #             }
    #         ]
    #     )
        
    #     # Set event properties from cached data
    #     event['range'] = cached_item['range']
    #     event['FunctLoc'] = cached_item['SAPFunctLoc']
    #     event['Equipment'] = cached_item['SAPEquipmentNr']
    #     event['Last_temperature_degC'] = cached_item.get('Last_temperature_degC', 0)
    #     event['Last_temperature_timestamp'] = cached_item.get('Last_temperature_timestamp', current_timestamp)
        
    #     logger.info("transformed event {}".format(event))
        
    # except Exception as exc:
    #     logger.error("Exception: " + str(type(exc)))
    #     logger.error("couldn't process event: {}".format(traceback.format_exc()))
            
    return event
