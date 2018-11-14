"Send reminder email to indebted enabled members."

from __future__ import print_function

import argparse
import csv
import email.mime.text
import json
import smtplib
import time

EMAIL      = 0
FIRST_NAME = 1
LAST_NAME  = 2
BALANCE    = 3
STATUS     = 5


def email_reminders(settings, csvfile, execute=True):
    "Send reminder email to indebted enabled members."
    assert settings.get('EMAIL')
    assert settings['EMAIL'].get('SENDER')
    assert settings.get('DEBT_EMAIL_SUBJECT_TEXT')
    assert settings.get('DEBT_EMAIL_MESSAGE_TEXT')
    emailserver = EmailServer(settings)
    reader = csv.reader(csvfile)
    reader.next()               # Skip past header.
    for row in reader:
        balance = float(row[BALANCE])
        if balance >= settings['DEBT_INSIGNIFICANT']: continue
        if row[STATUS] != 'enabled': continue
        name = u"{} {}".format(row[FIRST_NAME].decode('utf8'),
                               row[LAST_NAME].decode('utf8'))
        message = settings['DEBT_EMAIL_MESSAGE_TEXT'].format(
            name=name, amount=abs(balance))
        print(row[EMAIL], balance)
        if execute:
            emailserver.send(row[EMAIL],
                             settings['DEBT_EMAIL_SUBJECT_TEXT'],
                             message)
            time.sleep(settings['EMAIL'].get('PAUSE', 3.0))


class EmailServer(object):
    "A connection to an email server for sending emails."

    def __init__(self, settings):
        """Open the connection to the email server.
        Raise ValueError if no email server host has been defined.
        """
        self.settings = settings
        host = settings['EMAIL'].get('HOST')
        if not host:
            raise ValueError('no email server host defined')
        try:
            port = settings['EMAIL']['PORT']
        except KeyError:
            self.server = smtplib.SMTP(host)
        else:
            self.server = smtplib.SMTP(host, port=port)
        if settings['EMAIL'].get('TLS'):
            self.server.starttls()
        try:
            user = settings['EMAIL']['USER']
            password = settings['EMAIL']['PASSWORD']
        except KeyError:
            pass
        else:
            self.server.login(user, password)

    def __del__(self):
        "Close the connection to the email server."
        try:
            self.server.quit()
        except AttributeError:
            pass

    def send(self, recipient, subject, text):
        "Send an email."
        mail = email.mime.text.MIMEText(text, 'plain', 'utf-8')
        mail['Subject'] = subject
        mail['From'] = self.settings['EMAIL']['SENDER']
        mail['To'] = recipient
        self.server.sendmail(self.settings['EMAIL']['SENDER'],
                             [recipient],
                             mail.as_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Send email to indebted members.')
    parser.add_argument('-s', '--settings',
                        type=argparse.FileType('rb'),
                        default='email_settings.json',
                        help='Settings for connecting to the email server.')
    parser.add_argument('-c', '--csvfile',
                        type=argparse.FileType('rb'),
                        default='members.csv',
                        help='CSV file of BeerClub members.')
    parser.add_argument('-x', '--execute',
                        action='store_true', default=False)
    args = parser.parse_args()
    email_reminders(json.load(args.settings),
                    args.csvfile,
                    execute=args.execute)
