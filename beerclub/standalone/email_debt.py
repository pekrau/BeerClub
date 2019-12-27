"Send email to enabled members having a debt to the SciLifeLab Beer Club."

import argparse
import csv
import json
import time

from email_server import EmailServer

DEFAULT_PAUSE = 3.0

EMAIL      = 0
FIRST_NAME = 1
LAST_NAME  = 2
BALANCE    = 3
STATUS     = 5


def email_debt(settings, csvfile, subject, messagefile, execute=True):
    "Send email to enabled members having a debt to the Beer Club."
    emailserver = EmailServer(settings)
    message = messagefile.read()
    reader = csv.reader(csvfile)
    next(reader)               # Skip past header.
    for row in reader:
        balance = float(row[BALANCE])
        if balance >= 0 : continue
        if row[STATUS] != 'enabled': continue
        name = f"{row[FIRST_NAME]} {row[LAST_NAME]}"
        recipient = f"{name} <{row[EMAIL]}>"
        msg = message.format(name=name, amount=abs(balance))
        print(recipient, balance)
        if execute:
            emailserver.send(recipient, subject, msg)
            time.sleep(settings['EMAIL'].get('PAUSE', DEFAULT_PAUSE))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Send email to indebted enabled members.')
    parser.add_argument('-s', '--settings',
                        type=argparse.FileType('r'),
                        default='email_settings.json',
                        help='Settings for connecting to the email server.')
    parser.add_argument('-c', '--csvfile',
                        type=argparse.FileType('r'),
                        default='members.csv',
                        help='CSV file of BeerClub members.')
    parser.add_argument('-S', '--subject',
                        type=str,
                        default='Your debt to the SciLifeLab Beer Club',
                        help='Subject of the email message.')
    parser.add_argument('-t', '--messagefile',
                        type=argparse.FileType('r'),
                        default='email_debt_message.txt',
                        help='File containing the email message.')
    parser.add_argument('-x', '--execute',
                        action='store_true', default=False,
                        help='Actually send the messages.')
    args = parser.parse_args()
    email_debt(json.load(args.settings),
               args.csvfile,
               args.subject,
               args.messagefile,
               execute=args.execute)
