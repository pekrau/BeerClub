"""Use the BeerClub API to load Swish payments from CSV derived 
from SEB Excel output.

This script is independent of the rest of the BeerClub code base.

It uses the third-party package 'requests'.

It requires a settings file which contains the base URL,
the API key to use and the Swish number prefix replacements.
"""

import argparse
import csv
import json
import time

import requests

PAUSE = 1.0

# These are specific to the CSV from the SEB Excel file.
N_HEADER_ROWS  = 5
DATE_COLUMN    = 1
AMOUNT_COLUMN  = 3
SWISH_COLUMN   = 5
NAME_COLUMN    = 6
MESSAGE_COLUMN = 11


def load_swish(settings, csvfilepath, execute=False):
    with open(csvfilepath, 'r') as infile:
        reader = csv.reader(infile)
        # Skip past header records
        for i in range(N_HEADER_ROWS):
            row = reader.next()
        rows = list(reader)
    headers = {'X-BeerClub-API-key': settings['API_KEY']}
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
        url = settings['BASE_URL'] + 'member/' + swish
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            member = response.json()
            member['event'] = event
            members.append(member)
        else:
            print('missing >>>', swish, name)
            bail = True
    if bail: return
    print('Everything OK.')
    if not execute:
        print('Dry-run; no actions.')
        return
    else:
        print('Updating database...')
    for member in members:
        url = settings['BASE_URL'] + 'event/member/' + member['email']
        time.sleep(PAUSE)
        response = requests.post(url, headers=headers, json=member['event'])
        if response.status_code == 200:
            print(member['email'], member['event']['amount'])
        else:
            raise ValueError("%s %s" % (member['email'], response))
        if member.get('swish_lazy'):
            member['event']['action'] = 'purchase'
            member['event']['purchase'] = 'credit'
            member['event']['description'] = 'Swish lazy'
            member['event']['amount'] = member['event']['amount']
            time.sleep(PAUSE)
            response = requests.post(url, headers=headers,json=member['event'])
            if response.status_code == 200:
                print('Swish lazy')
            else:
                raise ValueError("%s %s" % (member['email'], response))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Load Swish payments from CSV from SEB Excel')
    parser.add_argument('-s', '--settings',
                        type=argparse.FileType('r'),
                        default='swish_settings.json',
                        help='Settings for Swish CSV file processing.')
    parser.add_argument('-c', '--csv',
                        action='store', dest='csvfilepath', metavar='FILE',
                        default='Export.csv', help='filename of CSV file')
    parser.add_argument('-x', action='store_const', dest='execute',
                        const=True, default=False,
                        help='actually perform the load; else dry-run')
    args = parser.parse_args()
    load_swish(json.load(args.settings), 
               args.csvfilepath,
               args.execute)
