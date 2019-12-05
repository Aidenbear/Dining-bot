from __future__ import print_function # Python 2/3 compatibility
import boto3
import csv
import time

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
client = boto3.client('dynamodb')
table = dynamodb.create_table(
    TableName='yelp-restaurant',
    KeySchema=[
        {
            'AttributeName': 'Business_ID',
            'KeyType': 'HASH'
        },
        {
            'AttributeName': 'insertedAtTimestamp',
            'KeyType': 'RANGE'
        }
    ],
    AttributeDefinitions=[
        {
            'AttributeName': 'Business_ID',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'insertedAtTimestamp',
            'AttributeType': 'S'
        },
    ],
    ProvisionedThroughput={
        'ReadCapacityUnits': 5,
        'WriteCapacityUnits': 5
    }
)

table.meta.client.get_waiter('table_exists').wait(TableName='yelp-restaurant')

print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

with table.batch_writer() as batch:
    with open('yelp.csv') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            try:
                batch.put_item(
                Item={
                    'insertedAtTimestamp': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    'cuisine': row[7],
                    'Business_ID': row[0],
                    'Name': row[1],
                    'Address': row[2],
                    'Coordinates': row[3],
                    'Num_of_Reviews':row[4],
                    'Rating':row[5],
                    'Zip_Code':row[6]
                })
            except:
                print(row)
