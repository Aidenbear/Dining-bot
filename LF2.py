import json
import boto3
import logging
import os
import time
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from botocore.vendored import requests

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Initialize clients
session = boto3.Session(region_name="us-east-1")
sns_client = session.client('sns')

sqs = boto3.client('sqs')


# --- Helper Functions ---

def receive_sqs_message(sqs_queue_url):
    """
    receive messages from sqs queue
    :param sqs_queue_url: String url
    :return: list of messages received. Return None if no message received
    """
    try:
        response = sqs.receive_message(QueueUrl=sqs_queue_url,
                                       MaxNumberOfMessages=1,
                                       WaitTimeSeconds=0)
    except ClientError as e:
        logging.error(e)
        return None

    # Return the list of retrieved messages
    if 'Messages' in response:
        return response['Messages']
    else:
        return None


def delete_sqs_message(sqs_queue_url, msg):
    """
    Delete a message from an SQS queue
    :param sqs_queue_url: String URL of existing SQS queue
    :param msg: retrieved message
    """
    msg_receipt_handle = msg['ReceiptHandle']

    # Delete the message from the SQS queue
    sqs.delete_message(QueueUrl=sqs_queue_url, ReceiptHandle=msg_receipt_handle)


def retrieve_messages(sqs_queue_url):
    """

    :param sqs_queue_url: String URL of existing SQS queue
    :return: list of all messages in the queue
    """
    messages = []
    message_keys = ['MessageId', 'Body']

    msgs = receive_sqs_message(sqs_queue_url)
    if msgs:
        for msg in msgs:
            message = {
                'MessageId': msg['MessageId'],
                'Body': json.loads(msg['Body'])
            }
            messages.append(message)
            delete_sqs_message(sqs_queue_url, msg)

    return messages


def send_sms(phone_number, message):
    """

    :param phone_number: phone number
    :param message: message
    :return: response
    """
    # format phone number
    if len(phone_number) == 10:
        phone_number = '1' + phone_number

    # Send message
    response = sns_client.publish(
        PhoneNumber=phone_number,
        Message=message,
        MessageAttributes={
            'AWS.SNS.SMS.SenderID': {
                'DataType': 'String',
                'StringValue': 'CONCIERGE'
            }
        }
    )
    logger.info(response)
    return response


def get_restaurant_details(business_id):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('yelp-restaurant')
    response = table.query(KeyConditionExpression=Key('Business_ID').eq(business_id))
    # need the result from the last function
    items = response['Items']
    return items


def get_random_restaurant(cuisine, size):
    host = 'https://search-chatbot-55g4zpvq3dljfj2eurlrralw44.us-east-1.es.amazonaws.com'
    index = 'restaurants'
    url = host + '/' + index + '/_search'
    query = {
        "size": size,
        "query": {
            "function_score": {
                "query": {"match": {"Cuisine": cuisine}},
                "random_score": {}
            }
        }
    }
    headers = {"Content-Type": "application/json"}
    r = requests.get(url, headers=headers, data=json.dumps(query))

    restaurant_ids = []
    restaurants = json.loads(r.text)['hits']['hits']
    for restaurant in restaurants:
        restaurant_ids.append(restaurant['_source']['Business_ID'])
    return restaurant_ids


def lambda_handler(event, context):
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event={}'.format(event))

    # get all requests from the SQS queue
    sqs_queue_url = 'https://sqs.us-east-1.amazonaws.com/841725263252/DiningConciergeQueue'

    # sample_msgs = [
    #     {
    #         'MessageId': '986a7e29-09b0-42ff-8ee2-3254ed4f48c6',
    #         'Body': {
    #             'Location': 'new york',
    #             'Cuisine': 'chinese',
    #             'DiningTime': '18:00',
    #             'NumberOfPeople': 5,
    #             'PhoneNumber': '3474060796'
    #         }
    #     },
    #     {
    #         'MessageId': '986a7e29-09b0-42ff-8ee2-3254ed4f48c7',
    #         'Body': {
    #             'Location': 'new york',
    #             'Cuisine': 'chinese',
    #             'DiningTime': '18:00',
    #             'NumberOfPeople': 5,
    #             'PhoneNumber': '3474060796'
    #         }
    #     }
    # ]

    msgs = retrieve_messages(sqs_queue_url)
    # msgs = sample_msgs

    # send sms
    if msgs:
        for msg in msgs:
            cuisine = msg['Body']['Cuisine']
            number_of_people = msg['Body']['NumberOfPeople']
            dining_time = msg['Body']['DiningTime']
            phone_number = msg['Body']['PhoneNumber']

            text = 'Hello! Here are my {} restaurant suggestions for {} people, for today at {}: \n'.format(
                cuisine,
                number_of_people,
                dining_time
            )

            # get list of restaurant id for the current request
            restaurant_ids = get_random_restaurant(cuisine, 3)

            # get restaurant detail
            for i, restaurant_id in enumerate(restaurant_ids):
                restaurant = get_restaurant_details(restaurant_id)[0]
                name = restaurant['Name']
                address = restaurant['Address']
                text += '{}. {}, located at {}.\n'.format(
                    i + 1,
                    name,
                    address
                )
            text += 'Enjoy your meal!'
            # send the text message
            send_sms(phone_number, text)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
