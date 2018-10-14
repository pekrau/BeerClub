"Home page; account status if logged in."

import logging

import tornado.web

from .requesthandler import RequestHandler


class Home(RequestHandler):
    "Home page."

    def get(self):
        if self.current_user:
            self.render('home.html')
        else:
            self.render('home.html')
