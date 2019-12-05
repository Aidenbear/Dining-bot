import json
import boto3
from datetime import datetime

def lambda_handler(event, context):
    client = boto3.client('lex-runtime')

    try:
        response = client.post_text(
            botName='DiningConcierge',
            botAlias='latest',
            userId='front_end',
            inputText=event['messages'][0]['unstructured']['text']
        )
        text = response['message']
    except Exception as e:
        text = str(e)

    response = {
        'messages': [
            {
                'type': '',
                'unstructured': {
                    'id': '',
                    'text': text,
                    'timestamp': str(datetime.now())
                }
            }
        ]
    }
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(response)
    }
