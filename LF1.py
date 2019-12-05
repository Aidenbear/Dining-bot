import json
import logging
import os
from datetime import datetime
import time
from random import choice
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# --- Helpers that build all of the responses ---

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


# --- Helper Functions ---

def safe_int(n):
    """
    Safely convert n value to int.
    """
    if n is not None:
        return int(n)
    return n


def try_ex(func):
    """
    Used to safely access dictionary
    """
    try:
        return func()
    except KeyError:
        return None


def send_sqs_message(queue_name, message):
    # create 'sqs' resource and get the queue
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    try:
        response = queue.send_message(MessageBody=message)
    except ClientError as e:
        logging.error(e)
        return None
    return response


def push_to_sqs(intent_request):
    """
    send the message to the SQS queue
    """
    # extract data from intent_request
    slots = try_ex(lambda: intent_request['currentIntent']['slots'])
    location = try_ex(lambda: slots['Location'])
    cuisine = try_ex(lambda: slots['Cuisine'])
    dining_time = try_ex(lambda: slots['DiningTime'])
    number_of_people = safe_int(try_ex(lambda: slots['NumberOfPeople']))
    phone_number = try_ex(lambda: slots['PhoneNumber'])
    message = json.dumps({
        'Location': location,
        'Cuisine': cuisine,
        'DiningTime': dining_time,
        'NumberOfPeople': number_of_people,
        'PhoneNumber': phone_number
    })

    queue_name = 'DiningConciergeQueue'
    # Send message to SQS queue
    return send_sqs_message(queue_name, message)


def isvalid_location(location):
    location_list = ['new york', 'manhattan', 'brooklyn', 'queens', 'bronx']
    return location.lower() in location_list


def isvalid_cuisine(cuisine):
    cuisine_list = ['chinese', 'italian', 'indian', 'mexican', 'american', 'japanese']
    return cuisine.lower() in cuisine_list


def isvalid_dining_time(dining_time):
    now = datetime.now().strftime('%HH:%MM')
    return dining_time > now


def isvalid_number_of_people(number_of_people):
    return number_of_people > 0


def isvalid_phone_number(phone_number):
    length = 10
    return len(phone_number) == length


def build_validation_result(isvalid, violated_slot, message_content):
    return {
        'isValid': isvalid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def validate_dining_suggestions(slots):
    """
    Used to validate the slots of the dining suggestion intent
    """
    # get the slot values
    location = try_ex(lambda: slots['Location'])
    cuisine = try_ex(lambda: slots['Cuisine'])
    dining_time = try_ex(lambda: slots['DiningTime'])
    number_of_people = safe_int(try_ex(lambda: slots['NumberOfPeople']))
    phone_number = try_ex(lambda: slots['PhoneNumber'])

    # validate the slots and return message if any slot was not valid
    if location and not isvalid_location(location):
        return build_validation_result(
            False,
            'Location',
            'Sorry, we do not know any restaurants in {}. Please choose another location.'.format(
                location)
        )
    if cuisine and not isvalid_cuisine(cuisine):
        return build_validation_result(
            False,
            'Cuisine',
            'Sorry, we do not know any {} restaurants. Please choose another cuisine'.format(
                cuisine)
        )
    if dining_time and not isvalid_dining_time(dining_time):
        return build_validation_result(
            False,
            'DiningTime',
            'Sorry, please choose a time in the future.'
        )
    if number_of_people is not None and not isvalid_number_of_people(number_of_people):
        return build_validation_result(
            False,
            'NumberOfPeople',
            'Sorry, we could not find restaurant for {} people. Please choose another party size.'.format(
                number_of_people)
        )
    if phone_number and not isvalid_phone_number(phone_number):
        return build_validation_result(
            False,
            'PhoneNumber',
            'Sorry, {} is not a valid phone number. Please type in another phone number'.format(
                phone_number)
        )

    return {'isValid': True}


# --- Functions that control the bot's behavior ---

def greeting(intent_request):
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {
    }

    greeting_response_list = [
        'Hi there!',
        'Hi there! How can I help you?',
        'Hello!'
    ]

    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': choice(greeting_response_list)
        }
    )


def thank_you(intent_request):
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {
    }

    thank_you_response_list = [
        'You are welcome! Thank you for using our service!',
        'It\'s our pleasure',
        'You\'re welcome!'
    ]

    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': choice(thank_you_response_list)
        }
    )


def dining_suggestions(intent_request):
    # get slot values
    slots = intent_request['currentIntent']['slots']

    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {
    }

    # if the request is for initiation and validation
    if intent_request['invocationSource'] == 'DialogCodeHook':
        # Validate any slots which have been specified.  If any are invalid, re-elicit for their value
        validation_result = validate_dining_suggestions(slots)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None

            return elicit_slot(
                session_attributes,
                intent_request['currentIntent']['name'],
                slots,
                validation_result['violatedSlot'],
                validation_result['message']
            )

        # Otherwise, let native DM rules determine how to elicit for slots and prompt for confirmation.
        return delegate(session_attributes, slots)

    # Based on the parameters collected from the user, push the information collected from the user (location, cuisine, etc.) to an SQS queue (Q1).
    # TODO Push the information collected to an SQS Queue
    push_to_sqs(intent_request)

    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'Cool! We have received your request. We will notify you by SMS once we have the list of restaurant suggestions.'
        }
    )


# --- Intents ---

def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """
    logger.debug('dispatch userId={}, intentName={}'.format(
        intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'GreetingIntent':
        return greeting(intent_request)
    elif intent_name == 'ThankYouIntent':
        return thank_you(intent_request)
    elif intent_name == 'DiningSuggestionsIntent':
        return dining_suggestions(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))
    logger.debug('event={}'.format(event))

    return dispatch(event)
