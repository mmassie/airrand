#!/usr/bin/env python
#
# This is an sample AppEngine application that shows how to 1) log in a user
# using the Twitter OAuth API and 2) extract their timeline.
#
# INSTRUCTIONS:
#
# 1. Set up a new AppEngine application using this file, let's say on port
# 8080. Rename this file to main.py, or alternatively modify your app.yaml
# file.)
# 2. Fill in the application ("consumer") key and secret lines below.
# 3. Visit http://localhost:8080 and click the "login" link to be redirected
# to Twitter.com.
# 4. Once verified, you'll be redirected back to your app on localhost and
# you'll see some of your Twitter user info printed in the browser.
# 5. Copy and paste the token and secret info into this file, replacing the
# default values for user_token and user_secret. You'll need the user's token
# & secret info to interact with the Twitter API on their behalf from now on.
# 6. Finally, visit http://localhost:8080/timeline to see your twitter
# timeline.
#

__author__ = "Mike Knapp"

import oauth

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api.urlfetch import *
from handlers import BaseHandler

from models import *
from gaesessions import get_current_session

import logging

import pprint

class MainHandler(BaseHandler):

    def get(self, mode=""):

        # Your application Twitter application ("consumer") key and secret.
        # You'll need to register an application on Twitter first to get this
        # information: http://www.twitter.com/oauth
        application_key = "PWVLFTF4V4VB1UVA4AHOWGNF0UKD5QBJ5IKDHBVE22VPZGPZ"
        application_secret = "MRE4XSFFTMFG3JPRQQKSJR05IPBMZOVOZ4LDRX2Y4KSAPCN2"

        # Fill in the next 2 lines after you have successfully logged in to
        # Twitter per the instructions above. This is the *user's* token and
        # secret. You need these values to call the API on their behalf after
        # they have logged in to your app.
        #user_token = "b03477a7-f974-4d50-8630-590367ea5d15"
        user_token = ""
        user_secret = ""

        # In the real world, you'd want to edit this callback URL to point to your
        # production server. This is where the user is sent to after they have
        # authenticated with Twitter.
        callback_url = "%s/foursquarecallback" % self.request.host_url

        client = oauth.FourSquareClient(application_key, application_secret,
                callback_url)

        #-----

        if mode == "login":
#            logging.info(self.session)
#            self.session["redirectFromLogin"] = self.request.get("redirect","/")

            auth_url = client.get_authorization_url()
            logging.info("^^^^^^^^^^^^here's the auth url")
            logging.info(auth_url)
            return self.redirect(client.get_authorization_url())

        #-----

        if mode == "verify":

            auth_token = self.request.get("oauth_token")
            auth_verifier = self.request.get("oauth_verifier")
            auth_token_secret = self.request.get("oauth_token_secret")
            user_info = client.get_user_info(auth_token, auth_verifier=auth_verifier)

            # this is where you save to database

            # save user to session
            self.session["user"]=user

            # if this is a first-time registration, complete registration
            if not user.email:
                return self.redirect('/user/register')

            redirect = self.session.pop("redirectFromLogin","/")
            return self.redirect(redirect)



        self.response.out.write("<a href='/foursquare/login'>login to foursquare via oauth</a>")



def main():
  application = webapp.WSGIApplication([('/(.*)', MainHandler)],
                                       debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()