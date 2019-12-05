# -*- coding: utf-8 -*-
"""
Yelp Fusion API code sample.
Please refer to http://www.yelp.com/developers/v3/documentation for the API
documentation.

"""
from __future__ import print_function

import argparse
import json
import pprint
import requests
import sys
import urllib
from datetime import datetime
import csv
import time, threading

# This client code can run on Python 2.x or 3.x.  Your imports can be
# simpler if you only need one of those.
try:
    # For Python 3.0 and later
    from urllib.error import HTTPError
    from urllib.parse import quote
    from urllib.parse import urlencode
except ImportError:
    # Fall back to Python 2's urllib2 and urllib
    from urllib2 import HTTPError
    from urllib import quote
    from urllib import urlencode

API_KEY= '-Nzuru_2dqd-FkN3ncN84iBlGH4wYqfJDu6KxDZQpsPP3AInTGQuGHe99r9fjxy_AAf2rK79F1Tl6aav5ZyX_M5up5mmh8vjB0UQ3j2JB54oamLILterrROcCaaWXXYx'
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'

DEFAULT_TERM = 'american'
DEFAULT_LOCATION = 'New York, NY'
DEFAULT_DATE = datetime.now()
SEARCH_LIMIT = 50


def request(host, path, api_key, params=None):
    params = params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }
    response = requests.request('GET', url, headers=headers, params=params)
    return response.json()


def search(api_key, term, location, params):
    return request(API_HOST, SEARCH_PATH, api_key, params)


def get_business(api_key, business_id):
    business_path = BUSINESS_PATH + business_id
    return request(API_HOST, business_path, api_key)


def query_api(num_of_requests, term, location):
    if num_of_requests == 0:
        offset = 0
    else:
        offset = num_of_requests*SEARCH_LIMIT+1
    print(num_of_requests, offset)
    location.replace(' ', '+')
    term.replace(' ', '+')
    params = {
        'term': term,
        'location': location,
        'limit': SEARCH_LIMIT,
        'offset': offset
    }
    response = search(API_KEY, term, location, params)
    businesses = response.get('businesses')
    if not businesses:
        print(u'No businesses for {0} in {1} found.'.format(term, location))
        return
    data = []
    for i in range(len(businesses)):
        try:
            response = get_business(API_KEY, businesses[i]['id'])
            data.append((response['id'], response['name'], str(response['location']['address1']), response['coordinates'], response['review_count'], response['rating'], response['location']['zip_code']))
        except:
            pass
    return data

def writeDataintoCSV(num_of_requests, term = DEFAULT_TERM, location = DEFAULT_LOCATION):
    data = query_api(num_of_requests, term, location)
    filename = 'yelp_'+term+'.csv'
    with open(filename,'a') as out:
        csvdata=csv.writer(out)
        if num_of_requests == 0:
            csvdata.writerow(['Business_ID', 'Name', 'Address', 'Coordinates', 'Number_of_Reviews', 'Rating', 'Zip_Code'])
        for row in data:
            csvdata.writerow(row)


if __name__ == '__main__':
    terms = ['american']
    for term in terms:
        i = 0
        while i < 15:
            writeDataintoCSV(i, term=term, location=DEFAULT_LOCATION)
            i += 1

            
