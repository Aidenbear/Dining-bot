# DiningConcierge
Build a dining concierge bot to give customers dinning suggestions based on their conservation with the bot.

The yelp files contain how to use yelp api get data from yelp website(yelp_data.py) and how to save them into a DynamoDB(create_table.py).

The Lambda Functions(LF) files contain how to call the Lex chatbot which could process customers intent from LF0, how to send message to customers about the dining suggestions LF1(push message to SQS) and LF2(send message to customers). 
