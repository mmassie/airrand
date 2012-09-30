#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#from handlers import completeRegistrationHandler
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
import handlers
import inviteHandlers
import foursquareoauth





def main():

    #map urls to handlers here
    application = webapp.WSGIApplication([

                                          # homepage
                                          ('/', handlers.MainHandler),

                                          # settings
                                          ('/settings',handlers.SettingsHandler),
                                          
                                          # settings
                                          ('/list',handlers.ListHandler),
                                          ('/list/(.*)',handlers.ListHandler),


                                          # foursquare registration
                                          ('/fscallback',handlers.FSCallbackHandler),
                                          ('/rcb',handlers.FSMainDomainCallbackHandler),

                                          # foursquare push service
                                          ('/fspushasdf',handlers.PushHandler),

                                          # log out
                                          ('/logout',handlers.LogoutHandler),

                                          # static pages
                                          ('/terms-and-privacy',handlers.TermsHandler),
                                          ('/about',handlers.AboutHandler),

                                          # json callbacks
                                          ('/json/(.*)',handlers.JSONHandler),
                                          # cron
                                          ('/cron/(.*)',handlers.CronHandler),
                                          # task queue
                                          ('/worker/(.*)',handlers.CronHandler),

                                          #invites
                                          ('/share/(.*)',inviteHandlers.CouplesInviteHandler)

                                          ],
                                         debug=True)





    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
