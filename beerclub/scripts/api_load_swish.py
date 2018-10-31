"""Use the BeerClub API to load Swish repayments from CSV derived 
from SEB Excel output.

This script is independent of the rest of the BeerClub code base.

It uses the third-party package 'requests'.

It requires a settings file 'swish.json' which contains the base URL,
the API key to use and the Swish number prefix replacements.
"""

from __future__ import print_function

import csv

import requests

# These are specific to the CSV from the SEB Excel file.
N_HEADER_ROWS  = 5
DATE_COLUMN    = 1
AMOUNT_COLUMN  = 3
SWISH_COLUMN   = 5
NAME_COLUMN    = 6
MESSAGE_COLUMN = 11


def load_swish(settings, csvfilename):
    with open(csvfilename, 'rb') as infile:
        reader = csv.reader(infile)
        # Skip past header records
        for i in range(N_HEADER_ROWS):
            row = reader.next()
        rows = list(reader)
    members = []
    bail = False
    for row in rows:
        event = dict(action='payment',
                     payment='swish',
                     date=row[DATE_COLUMN],
                     amount=float(row[AMOUNT_COLUMN]),
                     description=row[MESSAGE_COLUMN].strip())
        swish = row[SWISH_COLUMN]
        name  = row[NAME_COLUMN]
        if ',' in name:
            name = ' '.join(reversed(name.split(',')))
        name = ' '.join([n.capitalize() for n in name.split()])
        for prefix, replacement in settings['PREFIX'].items():
            if swish.startswith(prefix):
                swish = replacement + swish[len(prefix):]
                break
        # print(date, amount, swish)
        url = settings['BASE_URL'] + 'member/' + swish
        response = requests.get(url, headers={'X-BeerClub-API-key':
                                              settings['API_KEY']})
        if response.status_code == 200:
            member = response.json()
            member['event'] = event
            members.append(member)
        else:
            print('>>>', swish, name)
            bail = True
    if bail: return
    for member in members:
        url = base_url + 'event/member/' + member['email']
        response = requests.post(url, headers={'X-BeerClub-API-key': api_key},
                                 json=member['event'])
        if response.status_code == 200:
            print(member['email'])
        else:
            print('Error:', member['email'], str(response))


if __name__ == '__main__':
    import sys
    import json
    with open('swish.json', 'rb') as infile:
        settings = json.load(infile)
    if len(sys.argv) != 2:
        sys.exit('no CSV file specified')
    load_swish(settings, sys.argv[1])
