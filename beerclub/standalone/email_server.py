"Email server connection."

import email.mime.text
import smtplib


class EmailServer(object):
    "A connection to an email server for sending emails."

    def __init__(self, settings):
        """Open the connection to the email server.
        Raise ValueError if no email server host has been defined.
        """
        assert settings.get('EMAIL')
        assert settings['EMAIL'].get('SENDER')
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

    def send(self, recipient, subject, text):
        "Send an email to a single recipient."
        mail = email.mime.text.MIMEText(text, 'plain', 'utf-8')
        mail['Subject'] = subject
        mail['From'] = self.settings['EMAIL']['SENDER']
        mail['To'] = recipient
        self.server.sendmail(self.settings['EMAIL']['SENDER'],
                             [recipient],
                             mail.as_string())

if __name__ == '__main__':
    import json
    server = EmailServer(json.load(open('email_settings.json')))
    for recipient in ['Per Kraulis <per.kraulis@gmail.com>',
                      'Per Kraulis <per.kraulis@scilifelab.se>']:
        server.send(recipient,
                    'testing email',
                    'testing email sender script')
