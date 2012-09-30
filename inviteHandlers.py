__author__ = 'robertralian'

from ext import *
import handlers
import logging

#-------------------------------------------------------------------------------------------------------
class CouplesInviteHandler(handlers.BaseHandler):

    def get(self,inviteCode):

        logging.info("starting here: %s" % inviteCode)
        thisInvite = EmailInvite.get_by_key_name(inviteCode)
        if not thisInvite:
            logging.info("why here???")
            return self.redirect('/')
        if thisInvite.status == 1:
            logging.info("marking invite as clicked")
            thisInvite.status = 2
            thisInvite.put()
        if thisInvite.status ==2:
            logging.info("saving couple invite code to session")
            self.session["inviteCouple"] = inviteCode
        else:
            logging.info("this invite code is: %s" % str(thisInvite.status))
        #----------------------------------------------
        # get user info // redirect for logged out user
        if not self.session.has_key("userKey"):
            return self.redirect('/')
        user_identifier = self.session["userKey"]
        user = UserProfile.get_by_key_name(user_identifier)
        if user is None:
            return self.redirect('/')
        #----------------------------------------------
        else:
            return self.redirect('/settings')