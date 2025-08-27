import os
import json

def handler(event, context):
    print(f'{os.environ["LOGGERNAME"]} event: {json.dumps(event)}')
    return {
        'statusCode': 204,
        'headers': {
            'Content-Type': 'No-Content'
        }
    }