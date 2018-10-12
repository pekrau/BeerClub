"Home page."

from __future__ import print_function

import logging

from .requesthandler import RequestHandler


class Home(RequestHandler):
    "Home page."

    def get(self):
        self.render('home.html')
