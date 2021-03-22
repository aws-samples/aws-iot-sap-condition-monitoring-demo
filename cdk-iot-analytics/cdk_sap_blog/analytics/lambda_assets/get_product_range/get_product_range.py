import os
import sys
import json
import logging
import traceback
import boto3


logger = logging.getLogger()
logger.setLevel(logging.INFO)
streamHandler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])
def handler(event, context):
    logger.info("events before processing: {}".format(event))
    transformedEvents = []    
    for evt in event:
        # extract thing 'Type'
        try:
            item = table.get_item(
                Key = {
                    'Type': evt['registry']['attributes']['Type']
                }
            )
            evt['range'] = item['Item']['range']
            evt['Type'] = item['Item']['Type']
            evt['FunctLoc'] = item['Item']['FunctLoc']
            evt['Equipment'] = item['Item']['Equipment']
            logger.info("transformed event {}".format(evt))        
        except Exception as exc:
            logger.info("Exception: " + str(type(exc)))
            logger.info("couldn't find range for event: {}".format(traceback.format_exc(), exc_info=True))        
        finally:
            transformedEvents.append(evt)    
            
    return transformedEvents
