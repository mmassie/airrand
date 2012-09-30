__author__ = 'robertralian'

# moving most of our import statements to their own file
from ext import *
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from jinja2.ext import autoescape
from gaesessions import get_current_session
from google.appengine.api import urlfetch
from django.utils import simplejson
import pprint
import logging

from django.conf import settings

import utilities
import re

import urllib
from urllib import urlencode
global DOMAIN

# set vars depending on if we're in dev or production
ON_LOCALHOST = ('Development' == os.environ['SERVER_SOFTWARE'][:11])
if ON_LOCALHOST:

    # dev environment
    CLIENT_ID = "KGGAHON5HTGBL1Y2GIV0KJDRN1JQNR5YC1C2ISHL5DP1CJNV"
    CLIENT_SECRET = "BGDGQVBM0UIMYNOURPOTWVZ2WYU5ADZXXQGNCIWRLNPCVSKB"
    REDIRECT_URI = 'http://localhost:%s%s' % (os.environ['SERVER_PORT'], "/fscallback")
    DOMAIN = 'http://localhost:%s' % os.environ['SERVER_PORT']

else:
    # prod environment
    CLIENT_ID = "PWVLFTF4V4VB1UVA4AHOWGNF0UKD5QBJ5IKDHBVE22VPZGPZ"
    CLIENT_SECRET = "MRE4XSFFTMFG3JPRQQKSJR05IPBMZOVOZ4LDRX2Y4KSAPCN2"
#    REDIRECT_URI = "http://www.airrand.com/fscallback"
#    DOMAIN = "http://www.airrand.com"
    REDIRECT_URI = "https://airrand.appspot.com/fscallback"
    #DOMAIN = "http://airrand.appspot.com"
    DOMAIN = "http://www.airrand.com"

class BaseHandler(webapp.RequestHandler):


    # the following block sets up a context dictionary so you can pass
    # standard variables to all your pages if that floats your boat
    context = {}

    def __init__(self):
        self.populateContext()
        
    def populateContext(self):

        self.context = {}
        self.session = get_current_session()
        self.context["page"] = None
        self.context["inviteCouple"] = None
        self.context["isAdmin"] = None
        self.context["fslogin"] = ""
        self.context["bannerHeader"] = False
        self.context["showshare"] = True

        # set firstName/lastName
        if self.session.has_key("firstName"):
            self.context["firstName"]=self.session["firstName"]
            self.context["lastName"]=self.session["lastName"]

        # check if admin
        currentUser = users.get_current_user()
        if (currentUser):
            # self.context['currentUser'] = currentUser
            if users.is_current_user_admin():
                self.context['isAdmin'] = True

            # TODO, this looks fishy, doubt it's working
            userProfile = db.GqlQuery("SELECT * FROM UserProfile WHERE users = :1",currentUser)
            if (userProfile):
                self.context['userProfile'] = userProfile
        return

    def render(self, template_name):

        env = Environment(loader = FileSystemLoader([os.path.join(os.path.dirname(__file__), 'templates')]),
                          autoescape=True,
                          extensions=['jinja2.ext.autoescape'])
        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            raise TemplateNotFound(template_name)

        logging.info("-----------------------")
        logging.info(template_name)
        content = template.render(self.context)
        self.response.out.write(content)

#-------------------------------------------------------------------------------

class MainHandler(BaseHandler):
    def get(self):

        import models

        code_url = "https://foursquare.com/oauth2/authenticate?client_id=%s&response_type=code&redirect_uri=%s" % (CLIENT_ID,REDIRECT_URI)

        self.context["fslogin"] = code_url
        self.context["page"] = "home"

        self.context["justRegistered"] = self.session.pop("justRegistered", default=None)
        logging.info("-----------------------")
        logging.info("getting justRegistered value")
        logging.info(self.context["justRegistered"])

        tasks=[]
        partnerTasks=[]
        user = None
        #----------------------------------------------
        # get user if we have one
        if self.session.has_key("userKey"):
            user_identifier = self.session["userKey"]
            user = UserProfile.get_by_key_name(user_identifier)
        #----------------------------------------------

        # redirect to settings to complete registration if we need to
        if user is not None:

            if user.status==0:
                return self.redirect('/settings')
            else:

                tasks = user.getActiveTasks()

            if user.partner:
                partnerTasks = user.partner.getActiveTasks()
#                for partnerTask in partnerTasks:
#                    tasks.append(partnerTask)
        else:
            self.context["bannerHeader"] = True
            from gae_bingo.gae_bingo import ab_test
            self.context["showshare"] = ab_test("showshare", conversion_name="registered")


        if "inviteCouple" in self.session:
            thisInvite = EmailInvite.get_by_key_name(self.session["inviteCouple"])
            if thisInvite is not None:
                logging.info("definining firstname here")
                self.context["inviteCouple"] = thisInvite
                self.context["inviter"] = thisInvite.inviter

        self.context["tasks"] = tasks
        self.context["partnerTasks"] = partnerTasks
        self.context["user"] = user
        self.render('index.html')


#-------------------------------------------------------------------------------

class SettingsHandler(BaseHandler):

    def get(self):

        self.context["page"] = "settings"

        #----------------------------------------------
        # get user info // redirect for logged out user
        if not self.session.has_key("userKey"):
            return self.redirect('/')
        user_identifier = self.session["userKey"]
        user = UserProfile.get_by_key_name(user_identifier)
        if user is None:
            return self.redirect('/')
        #----------------------------------------------

        # create input object
        input = {}
        input["email"] = user.email
        input["phone"] = user.phone
        if input["phone"] == None:
            input["phone"] = ""
        input["smsPref"] = user.smsPref
        input["emailPref"] = user.emailPref
        input["success"] = None
        input["inviteCoupleEmail"] = ""
        input["inviteCoupleMsg"] = ""
        self.context["input"] = input

        # create error object
        error = {}
        error["phone"] = None
        error["email"] = None
        error["terms"] = None
        self.context["error"] = error

        self.context["partner"] = ""
        self.context["inviteCouple"] = ""
        self.context["inviter"] = ""

        # get all current partners (couple stuff)
        partners = []
        for partner in user.partners:
            partners.append(partner)
        self.context["partners"] = partners
        # pull up invite info from invite cookie
        if "inviteCouple" in self.session:
            thisInvite = EmailInvite.get_by_key_name(self.session["inviteCouple"])
            if thisInvite is not None:
                logging.info("definining firstname here")
                self.context["inviteCouple"] = thisInvite
                self.context["inviter"] = thisInvite.inviter
        # get all couple invites sent by this user
        sentInvites = EmailInvite.all().filter('inviter =',user).filter('status IN',(1,2)).fetch(1000)
        self.context["sentInvites"] = sentInvites

        # get completed tasks
        tasks = user.getCompletedTasks()

        if user.partner:
            partnerTasks = user.partner.getCompletedTasks()
            for partnerTask in partnerTasks:
                tasks.append(partnerTask)

        self.context["tasks"] = tasks
        self.context["user"] = user
        self.context["bannerHeader"] = True
        self.render('settings.html')

    def post(self):

        #----------------------------------------------
        # get user info // redirect for logged out user
        if not self.session.has_key("userKey"):
            return self.redirect('/')
        user_identifier = self.session["userKey"]
        user = UserProfile.get_by_key_name(user_identifier)
        if user is None:
            return self.redirect('/')
        #----------------------------------------------

        # create input object
        input = {}
        input["email"] = self.request.get("email")
        input["phone"] = re.sub('[^\d]+',"",self.request.get("phone")).lstrip('1') #sanitizing for us here
        input["smsPref"] = self.request.get("smsPref")
        input["emailPref"] = self.request.get("emailPref")
        input["terms"] = self.request.get("terms")
        input["inviteCoupleEmail"] = self.request.get("inviteCoupleEmail")
        input["inviteCoupleMsg"] = self.request.get("inviteCoupleMsg")[:140]
        self.context["input"] = input

        # get all current partners
        partners = []
        for partner in user.partners:
            partners.append(partner)
        self.context["partners"] = partners

        # get all previously sent invites, but don't add to context until we know if we're sending one now
        sentInvites = EmailInvite.all().filter('inviter =',user).filter('status IN',(1,2)).fetch(1000)

        # create error object
        error = self.validateSettings(input,user,partners,sentInvites)
        self.context["error"] = error

        # create some blank variables for couple invite stuff
        self.context["partner"] = ""
        self.context["inviteCouple"] = ""
        self.context["inviter"] = ""

        # if no errors, save the info
        if not len(error):

            user.email = input["email"]
            user.phone = input["phone"]
            user.emailPref = bool(input["emailPref"])
            user.smsPref = bool(input["smsPref"])

            if input["inviteCoupleEmail"] and not len(partners):
                # create new emailInvite object
                thisInvite = EmailInvite(key_name=uniqid(14),
                    type = 1, #couple invite
                    inviter = user,
                    email = input["inviteCoupleEmail"],
                    message = input["inviteCoupleMsg"]
                )
                thisInvite.send()
                sentInvites.append(thisInvite)

            # if this was first-time registration, send to homepage
            if user.status == 0:
                # score this as a new registration in our gae bingo module
                from gae_bingo.gae_bingo import bingo
                bingo("registered")
                user.status = 1
                user.put();
                logging.info("--------------------------------")
                logging.info("setting justRegistered to True")
                self.session["justRegistered"] = True
                self.session.save()
                return self.redirect('/')


            user.put()
            input["success"] = "Your changes have been saved."

        # do the couples stuff
        if "inviteCouple" in self.session:
            thisInvite = EmailInvite.get_by_key_name(self.session["inviteCouple"])
            if thisInvite is not None:
                logging.info("definining firstname here")
                self.context["inviteCouple"] = thisInvite
                self.context["inviter"] = thisInvite.inviter

        # get completed tasks
        tasks = user.getCompletedTasks()

        if user.partner:
            partnerTasks = user.partner.getCompletedTasks()
            for partnerTask in partnerTasks:
                tasks.append(partnerTask)

        self.context["tasks"] = tasks

        self.context["sentInvites"] = sentInvites
        self.context["page"] = "settings"
        self.context["user"] = user
        self.context["bannerHeader"] = True
        self.render('settings.html')

    def validateSettings(self,input,user,partners,sentInvites):

        error = {}

        email = input["email"]
        phone = input["phone"]
        smsPref = input["smsPref"]
        emailPref = input["emailPref"]
        terms = input["terms"]

        # validate terms
        if not user.status and not terms:
            error["terms"] = "You must agree to our terms to use our service."

        # validate email
        if email == "":
            error["email"] = "Your email address is required to use airrand.com."
        elif not utilities.isValidEmail(email):
            error["email"] = "Please enter a valid email address."

        # validate phone
        if smsPref and len(phone) != 10:
            error["phone"] = "Your phone number must be in the format (###) ###-####."
        if not smsPref and not emailPref:
            error["phone"] = "You must agree to be notified by sms and/or email to use airrand.com."
        
        # validate inviteCouple
        if input["inviteCoupleEmail"] and not utilities.isValidEmail(input["inviteCoupleEmail"]):
            error["inviteCouple"] = "The email address you entered to invite your partner is not valid."
        if input["inviteCoupleEmail"] and len(partners):
            error["inviteCouple"] = "You're already a couple with %s %s." % (user.partner.firstName,user.partner.lastName)
        if input["inviteCoupleEmail"] and len(sentInvites):
            error["inviteCouple"] = "You've already invited someone: %s." % (sentInvites[0].email)


        return error


#-------------------------------------------------------------------------------------------------------
class ListHandler(BaseHandler):

    def get(self, checkinId=None):

        #----------------------------------------------
        # get user if we have one
        user = None
        if self.session.has_key("userKey"):
            user_identifier = self.session["userKey"]
            user = UserProfile.get_by_key_name(user_identifier)
        #----------------------------------------------

        if checkinId == "":
            checkinId = None

        # if we don't have a checkinId and we don't have a user, redirect to homepage
        if checkinId is None and user is None:
            return self.redirect('/')

        # pull last checkinId from user record if it's not in url
        if checkinId == None or checkinId =="":
            checkinId = user.lastCheckin

        if checkinId == None:
            return self.redirect('/')

        # get checkin
        checkin = CheckIn.get_by_key_name(checkinId)
        if checkin is None:
            return self.redirect('/')

        thisUser = checkin.user
        categoriesPlusNameList = checkin.categoriesPlusName



        # get all appropriate tasks
        query = "SELECT * FROM Task WHERE "
        users = []
        users.append(thisUser.key())
        if thisUser.partner:
            users.append(thisUser.partner.key())
        query = db.GqlQuery("SELECT * FROM Task WHERE status=1 AND user in :1 AND whereCanonical in :2",users,categoriesPlusNameList)
        results = query.fetch(200)

        tasks = []
        partnerTasks = []

        for task in results:
            if task.user.key() == checkin.user.key():
                tasks.append(task)
            else:
                partnerTasks.append(task)


        self.context["tasks"] = tasks
        self.context["partnerTasks"] = partnerTasks
        self.context["page"] = "list"
        self.render('list.html')



#-------------------------------------------------------------------------------

class FSCallbackHandler(BaseHandler):

    def get(self):

        # we have the auth code
        auth_code = self.request.get("code")
        redirectCallbackUrl = "%s/rcb?code=%s" % (DOMAIN,auth_code)
        return self.redirect(redirectCallbackUrl)

class FSMainDomainCallbackHandler(BaseHandler):

    def get(self):

        # we have the auth code
        auth_code = self.request.get("code")
        
        # now get the auth-token
        url = "https://foursquare.com/oauth2/access_token?client_id=%s&client_secret=%s&grant_type=authorization_code&redirect_uri=%s&code=%s" % (CLIENT_ID,CLIENT_SECRET,REDIRECT_URI,auth_code)
        result = urlfetch.fetch(url)
        if not result.status_code == 200:
            return self.response.out.write("something wrong with foursquare oauth")

        data = simplejson.loads(result.content)
        access_token = data["access_token"]

        # now get user info
        url = "https://api.foursquare.com/v2/users/self?oauth_token=%s" % access_token
        result = urlfetch.fetch(url)
        if not result.status_code == 200:
            return self.response.out.write("problem getting user info")

        data = simplejson.loads(result.content)
        logging.info(data)

        # get or create this user
        user_identifier = "foursquare%s" % data["response"]["user"]["id"]



        user = UserProfile.get_by_key_name(user_identifier)
        if user is None and "user" in data["response"]:

            logging.info("creating new user")
            user = UserProfile(key_name=user_identifier)
            userObj = data["response"]["user"]

            if "firstName" in userObj:
                user.firstName=userObj["firstName"]
            if "lastName" in userObj:
                user.lastName=userObj["lastName"]
            else:
                user.lastName=""
            if "id" in userObj:
                user.foursquareId=userObj["id"]
            if "contact" in userObj and "phone" in userObj["contact"]:
                user.phone=userObj["contact"]["phone"]
            if "contact" in userObj and "twitter" in userObj["contact"]:
                user.twitter=userObj["contact"]["twitter"]
            if "contact" in userObj and "facebook" in userObj["contact"]:
                user.facebookId=int(userObj["contact"]["facebook"])
            if "contact" in userObj and "email" in userObj["contact"]:
                user.email=userObj["contact"]["email"]
            if "friends" in userObj and "count" in userObj["friends"]:
                user.foursquareFriendsCount=userObj["friends"]["count"]
            if "type" in userObj:
                user.foursquareType=userObj["type"]
            if "homeCity" in userObj:
                user.homeCity=userObj["homeCity"]
            if "gender" in userObj and userObj["gender"]!="none":
                user.gender=userObj["gender"]
            if "photo" in userObj:
                user.photo=userObj["photo"]
            user.foursquareAccessToken=access_token
            user.put()

        elif user is not None:
            logging.info("no need to pull a new user, this one already exists")

        else:
            logging.info("didn't have a user in data['response']")

        logging.info(user.key().name())

        # set new session info
        self.session["firstName"] = user.firstName
        self.session["lastName"] = user.lastName
        self.session["userKey"] = user_identifier
        self.session.regenerate_id()

        if user.status == 0:

            # send new user to settings page to complete registration
            user.put()
            return self.redirect('/settings')

        # returning user (status==1), just take to homepage
        return self.redirect(DOMAIN)


#-------------------------------------------------------------------------------

class TermsHandler(BaseHandler):

    def get(self):

        #self.response.out.write(uniqid(14))
        self.context["page"] = "terms"
        self.context["bannerHeader"] = True
        self.render('terms.html')

#-------------------------------------------------------------------------------

class AboutHandler(BaseHandler):

    def get(self):

        #self.response.out.write(uniqid(14))
        self.context["page"] = "about"
        self.context["bannerHeader"] = True
        self.render('about.html')

#-------------------------------------------------------------------------------

class LogoutHandler(BaseHandler):

    def get(self):

        session = get_current_session()
        if session.has_key('firstName'):
            del session['firstName']
            del session['lastName']
            del session['userKey']
        
        self.session.regenerate_id()
        return self.redirect('/')



#-------------------------------------------------------------------------------------------------------
class JSONHandler(BaseHandler):
    
    def get(self, mode=""):


        #--------------------------------------------
        if mode=="addTask":

            if not self.session.has_key("userKey"):
                content = {
                    "success":False,
                    "reason":"not logged in"
                }
            else:

                user_identifier = self.session["userKey"]

                user = UserProfile.get_by_key_name(user_identifier)
                whatInput = self.request.get("whatinput")
                whereInput = self.request.get("whereinput")

                categoryMap = {
                    'home':'Homes',
                    'grocery store':"Grocery Stores",
                    'work':"Offices",
                    'school':"Schools",
                    'hotel':"Hotels",
                    'gym':"Gyms or Fitness Center",
                    'bookstore':"Bookstores",
                    'department store':"Department Stores"
                }
                whereCanonical = []
                whereCanonical.append(categoryMap[whereInput])

                newTask = Task(
                    user = user,
                    what = whatInput,
                    where = whereInput,
                    whereCanonical = whereCanonical
                    )

                newTask.put()

                date = newTask.created.strftime("%m/%d")
                taskId = str(newTask.key())
                logging.info(newTask.what)
                what = newTask.what
                where = newTask.where


                content = {
                    "success":True,
                    "taskId":taskId,
                    "when":date,
                    "what":what,
                    "where":where
                }

        #--------------------------------------------
        elif mode=="deleteTask":

            taskToken = self.request.get("task")
            task = Task.get(taskToken)
            if task is None:
                content = {
                    "success":False,
                    "reason":"task key invalid"
                }
            else:
                task.delete()
                content = {
                    "success":True,
                    "task":taskToken
                }

        #--------------------------------------------
        elif mode=="finishTask":

            taskToken = self.request.get("task")
            status = int(self.request.get("status"))
            
            task = Task.get(taskToken)
            if task is None:
                content = {
                    "success":False,
                    "reason":"task key invalid"
                }
            else:
                task.status=status
                task.put()
                content = {
                    "success":True,
                    "task":taskToken
                }
        
        #--------------------------------------------
        # handle couple invites
        #--------------------------------------------
        elif mode=="handleInvite":
            # make sure invitecode is valid and user is authorized
            inviteCode = self.request.get("inviteCode")
            action = self.request.get("action")
            invite = EmailInvite.get_by_key_name(inviteCode)
            if self.session.has_key("userKey"):
                user_identifier = self.session["userKey"]
                user = UserProfile.get_by_key_name(user_identifier)
            if not user:
                content = {
                    "success":False,
                    "inviteCode":inviteCode,
                    "reason":"not logged in"
                }
            elif not invite:
                content = {
                    "success":False,
                    "inviteCode":inviteCode,
                    "reason":"invalid invite code"
                }
            elif action=="acceptInvite" and user.partners.count():
                content = {
                    "success":False,
                    "inviteCode":inviteCode,
                    "reason":"already partner relationship"
                }
            else:
                # all the checks came back ok, so do the stuff
                if action=="rejectInvite":
                    invite.status = -1
                    invite.put()
                    logging.info("successful %s" % action)
                    content = {
                        "success":True,
                        "inviteCode":inviteCode,
                        "action":action
                    }
                    # drop the inviteCouple cookie
                    self.session.pop("inviteCouple")
                    self.session.save()

                elif action=="cancelInvite":
                    invite.status = -2
                    invite.put()
                    logging.info("successful %s" % action)
                    content = {
                        "success":True,
                        "inviteCode":inviteCode,
                        "action":action
                    }
                elif action=="acceptInvite":
                    invite.status = 3
                    invite.put()
                    inviter = invite.inviter
                    if user.partner and user.partner.key().name()==inviter.key().name():
                        reasonString = "%s %s is already your partner." % (invite.inviter.firstName,invite.inviter.lastName)
                        content = {
                            "success":False,
                            "inviteCode":inviteCode,
                            "reason":reasonString
                        }
                    elif inviter.partner and inviter.partner.key().name() == user.key().name():
                        reasonString = "You are already a couple with %s %s" % (invite.inviter.firstName,invite.inviter.lastName)
                        content = {
                            "success":False,
                            "inviteCode":inviteCode,
                            "reason":reasonString
                        }
                    else:
                        # Success! Now do it!
                        inviter.partner = user
                        user.partner = inviter
                        user.put()
                        inviter.put()
                        content = {
                            "success":True,
                            "inviteCode":inviteCode,
                            "action":action,
                            "firstName":invite.inviter.firstName,
                            "lastName":invite.inviter.lastName,
                            "partnerKey":invite.inviter.key().name()
                        }
                    logging.info("successful %s" % action)



        #--------------------------------------------
        # remove couple
        #--------------------------------------------
        elif mode=="removePartner":
            # make sure user is authorized
            partnerKey = self.request.get("partnerKey")
            partner = UserProfile.get_by_key_name(partnerKey)
            if self.session.has_key("userKey"):
                user_identifier = self.session["userKey"]
                user = UserProfile.get_by_key_name(user_identifier)
            if not user:
                content = {
                    "success":False,
                    "reason":"not logged in",
                    "action":"removePartner"
                }
            elif not partner:
                content = {
                    "success":False,
                    "reason":"invalid user key",
                    "action":"removePartner"
                }
            else:
                partner.partner = None
                user.partner = None
                user.put()
                partner.put()
                content = {
                    "success":True,
                    "action":"removePartner"
                }


        # output whatever response we have
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(simplejson.dumps(content))
        #self.response.out.write(content)


#-------------------------------------------------------------------------------

class PushHandler(BaseHandler):

    def post(self):

        import logging

        logging.info("checkin happening!")

        #json = simplejson.loads(self.request.body)
        checkin = simplejson.loads(self.request.get("checkin"))
        user = simplejson.loads(self.request.get("user"))
        self.handleJson(checkin,user)

    def handleJson(self,checkin,user):

#        checkin_json = json['checkin']
#        user_json = json['user']
        checkin_json = checkin
        user_json = user

        logging.info(checkin_json)
        logging.info(user_json)

        # get or create this user
        user_identifier = "foursquare%s" % user_json["id"]
        user = UserProfile.get_by_key_name(user_identifier)
        if user is None:

            logging.info("not a valid user")
            return

        # rename to match the code in CronHandler
        lastCheckin = checkin_json

        # this stuff is blindly copied from the CronHandler
        # build category lists to save in checkin object and to query tasks
        categoriesList = []
        for category in lastCheckin["venue"]["categories"]:
            if "pluralName" in category:
                categoriesList.append(category["pluralName"])
            else:
                categoriesList.append(category["name"])
        categoriesPlusNameList = [lastCheckin["venue"]["name"]]
        categoriesPlusNameList.extend(categoriesList)

        # create new checkin object
        thisCheckin = CheckIn(key_name=lastCheckin["id"],
            user = user,
            name = lastCheckin["venue"]["name"],
            categories = categoriesList,
            categoriesPlusName = categoriesPlusNameList,
            venueJSON = str(lastCheckin)
        ).put()

        logging.info("------------------ User -------------------")
        logging.info(user.key().name())
        logging.info("------------------ thisCheckin -------------------")
        logging.info(thisCheckin)
        logging.info("------------------ categoriesList -------------------")
        logging.info(categoriesList)
        logging.info("------------------ categoriesPlusNameList -------------------")
        logging.info(categoriesPlusNameList)

        # update user record
        user.lastCheckin = lastCheckin["id"]
        user.put()

        # are there any tasks associated with this?
        if user.partner:
            logging.info("this user has a partner")
            users = []
            users.append(user.key())
            users.append(user.partner.key())
            logging.info(users)
            logging.info("i was able to append users to the user list")
            query = db.GqlQuery("SELECT * FROM Task WHERE status=1 AND user in :1 AND whereCanonical in :2", users, categoriesPlusNameList)
        else:
            query = db.GqlQuery("SELECT * FROM Task WHERE status=1 AND user=:1 AND whereCanonical in :2",user,categoriesPlusNameList)
        results = query.get()
        if results:
            # send a text message
            listLink = "%s/list/%s" % (DOMAIN,lastCheckin["id"])
            subject = "You have some to-do items at %s" % lastCheckin["venue"]["name"]
            body = """Dear %s
You have some to-do items at %s.

%s

Sincerely,
The airrand team
""" % (
    user.firstName,
    lastCheckin["venue"]["name"],
    listLink
    )

            if user.smsPref:
                logging.info("------------------ SENDING SMS -------------------")
                logging.info(listLink)
                self.response.out.write("sending sms<br />")
                user.sendSMS("You have some airrands to do at %s: %s" % (lastCheckin["venue"]["name"],listLink))
            else:
                logging.info("--------------------no sms pref--------------------")
            if user.emailPref:
                logging.info("------------------ SENDING EMAIL -------------------")
                logging.info(subject)
                logging.info(body)
                self.response.out.write("sending email<br />")
                user.sendEmail(subject,body)
            else:
                logging.info("--------------------no email pref--------------------")
        else:
            self.response.out.write("no tasks matched the category or name<br />")
            self.response.out.write(", ".join(categoriesPlusNameList))
            logging.info("NO RESULTS")

    def get(self):

        import logging
        logging.info("placeholder")
        if not ON_LOCALHOST:
            logging.info("get outta here")
            return

        json = {
    "checkin": {
        "id": "4da3610a2939b1f72a1e1d57",
        "createdAt": 1302552842,
        "type": "checkin",
        "timeZone": "America/Chicago",
        "user": {
            "id": "79875",
            "firstName": "Bob",
            "lastName": "Ralian",
            "photo": "https://playfoursquare.s3.amazonaws.com/userpix_thumbs/XOXJX0TSKHYTQDTG.jpg",
            "gender": "male",
            "homeCity": "Milwaukee, WI",
            "relationship": "self"
        },
        "venue": {
            "id": "4a6e2600f964a52008d41fe3",
            "name": "Groupon",
            "contact": {
                "phone": "8777887858",
                "twitter": "groupon"
            },
            "location": {
                "address": "600 W Chicago Ave",
                "crossStreet": "N Larrabee St",
                "city": "Chicago",
                "state": "IL",
                "postalCode": "60654",
                "country": "USA",
                "lat": 41.89748567413128,
                "lng": -87.64381885528564,
            },
            "categories": [{
                "id": "4bf58dd8d48988d125941735",
                "name": "Tech Startup",
                "pluralName": "Tech Startups",
                "icon": "https://foursquare.com/img/categories/building/default.png",
                "parents": ["Homes, Work, Others""Offices"],
                "primary": True
            }, {
                "id": "4bf58dd8d48988d124941735",
                "name": "Grocery Store", # modifying here to trigger list
                "pluralName": "Grocery Stores", # modifying here to trigger list
                "icon": "https://foursquare.com/img/categories/building/default.png",
                "parents": ["Homes, Work, Others"]
            }],
            "verified": True,
            "stats": {
                "checkinsCount": 2294,
                "usersCount": 331
            },
            "todos": {
                "count": 0
            }
        },
        "source": {
            "name": "foursquare for iPhone",
            "url": "https://foursquare.com/download"
        },
        "photos": {
            "count": 0,
            "items": []
        },
        "comments": {
            "count": 0,
            "items": []
        },
        "overlaps": {
            "count": 1,
            "items": [{
                "id": "4da361782939b1f7c0251d57",
                "createdAt": 1302552952,
                "type": "checkin",
                "timeZone": "America/Chicago",
                "user": {
                    "id": "149404",
                    "firstName": "Mike",
                    "lastName": "Massie",
                    "photo": "https://playfoursquare.s3.amazonaws.com/userpix_thumbs/M4YAJIVDPINWGSNQ.jpg",
                    "gender": "male",
                    "homeCity": "Milwaukee, WI",
                    "relationship": "friend"
                }
            }]
        }
    },

    "user": {
        "id": "79875",
        "firstName": "Bob",
        "lastName": "Ralian",
        "photo": "https://playfoursquare.s3.amazonaws.com/userpix_thumbs/XOXJX0TSKHYTQDTG.jpg",
        "gender": "male",
        "homeCity": "Milwaukee, WI",
        "relationship": "self",
        "type": "user",
        "pings": False,
        "contact": {
            "phone": "4146986933",
            "email": "bob.ralian@gmail.com",
            "twitter": "rralian",
            "facebook": "2418120"
        },
        "badges": {
            "count": 5
        },
        "mayorships": {
            "count": 1,
            "items": [{
                "id": "4d58f0f64d9a721ed88a3b0e",
                "name": "Casa de Bob",
                "contact": {},
                "location": {
                    "address": "2792 n 69th St",
                    "city": "Milwaukee",
                    "state": "WI",
                    "lat": 43.0700226,
                    "lng": -87.9982531
                },
                "categories": [{
                    "id": "4bf58dd8d48988d103941735",
                    "name": "Home",
                    "pluralName": "Homes",
                    "icon": "https://foursquare.com/img/categories/building/home.png",
                    "parents": ["Homes, Work, Others"],
                    "primary": True
                }],
                "verified": False,
                "stats": {
                    "checkinsCount": 13,
                    "usersCount": 1
                },
                "todos": {
                    "count": 0
                }
            }]
        },
        "checkins": {
            "count": 71,
            "items": [{
                "id": "4da3610a2939b1f72a1e1d57",
                "createdAt": 1302552842,
                "type": "checkin",
                "timeZone": "America/Chicago",
                "venue": {
                    "id": "4a6e2600f964a52008d41fe3",
                    "name": "Groupon",
                    "contact": {
                        "phone": "8777887858",
                        "twitter": "groupon"
                    },
                    "location": {
                        "address": "600 W Chicago Ave",
                        "crossStreet": "N Larrabee St",
                        "city": "Chicago",
                        "state": "IL",
                        "postalCode": "60654",
                        "country": "USA",
                        "lat": 41.89748567413128,
                        "lng": -87.64381885528564
                    },
                    "categories": [{
                        "id": "4bf58dd8d48988d125941735",
                        "name": "Tech Startup",
                        "pluralName": "Tech Startups",
                        "icon": "https://foursquare.com/img/categories/building/default.png",
                        "parents": ["Homes, Work, Others""Offices"],
                        "primary": True
                    }, {
                        "id": "4bf58dd8d48988d124941735",
                        "name": "Office",
                        "pluralName": "Offices",
                        "icon": "https://foursquare.com/img/categories/building/default.png",
                        "parents": ["Homes, Work, Others"]
                    }],
                    "verified": True,
                    "stats": {
                        "checkinsCount": 2294,
                        "usersCount": 331
                    },
                    "todos": {
                        "count": 0
                    }
                }
            }]
        },
        "friends": {
            "count": 39,
            "groups": [{
                "type": "others",
                "name": "other friends",
                "count": 39,
                "items": []
            }]
        },
        "following": {
            "count": 2
        },
        "requests": {
            "count": 1
        },
        "tips": {
            "count": 0
        },
        "todos": {
            "count": 1
        },
        "scores": {
            "recent": 0,
            "max": 82,
            "checkinsCount": 0
        }
    }
}

        self.handleJson(json)
        self.response.out.write("well, looks like we were able to trigger this :-)")

#-------------------------------------------------------------------------------

class CronHandler(BaseHandler):

    def get(self, mode=""):

        import logging

        if mode == "getcheckins":

            # hardcode to nothin so we can try push service
            return

            # check for new checkins
            query = db.GqlQuery("SELECT * FROM UserProfile WHERE lastCheckin!=:1",None)
            results = query.fetch(1000)

            for user in results:

                url = "https://api.foursquare.com/v2/users/self/checkins?oauth_token=%s&limit=1" % user.foursquareAccessToken
                result = urlfetch.fetch(url)
                if not result.status_code == 200:
                    logging.info("problem getting first checkin for a new user")
                    return
                data = simplejson.loads(result.content)
                
                lastCheckin = data["response"]["checkins"]["items"][0]
                logging.info("last checking")
                logging.info(lastCheckin["id"])
                logging.info(user.lastCheckin)

                if lastCheckin["id"] != user.lastCheckin:

                    # this is a new checkin -- deal with it
                    
                    # build category lists to save in checkin object and to query tasks
                    categoriesList = []
                    for category in lastCheckin["venue"]["categories"]:
                        categoriesList.append(category["name"])
                    categoriesPlusNameList = [lastCheckin["venue"]["name"]]
                    categoriesPlusNameList.extend(categoriesList)

                    # create new checkin object
                    thisCheckin = CheckIn(key_name=lastCheckin["id"],
                        user = user,
                        name = lastCheckin["venue"]["name"],
                        categories = categoriesList,
                        categoriesPlusName = categoriesPlusNameList,
                        venueJSON = str(lastCheckin)
                    ).put()

                    # update user record
                    user.lastCheckin = lastCheckin["id"]
                    user.put()

                    # are there any tasks associated with this?
                    query = db.GqlQuery("SELECT * FROM Task WHERE status=1 AND user=:1 AND whereCanonical in :2",user,categoriesPlusNameList)
                    results = query.get()
                    if results:

                        # send a text message
                        listLink = "%s/list/%s" % (DOMAIN,lastCheckin["id"])
                        subject = "You have some to-do items"
                        body = """
Dear %s
You have some to-do items at your last check-in.

%s

Sincerely,
The airrand Team
""" % (user.firstName,listLink)

                        if user.smsPref:
                            user.sendSMS("You have some airrands to do here: %s" % listLink)
                        if user.emailPref:
                            user.sendEmail(subject,body)
                    




            # check first checkin for a new user
            query = db.GqlQuery("SELECT * FROM UserProfile WHERE lastCheckin=:1",None)
            results = query.fetch(200)

            for user in results:

                url = "https://api.foursquare.com/v2/users/self/checkins?oauth_token=%s&limit=1" % user.foursquareAccessToken
                result = urlfetch.fetch(url)
                if not result.status_code == 200:
                    logging.info("problem getting first checkin for a new user")
                    return
                data = simplejson.loads(result.content)

                logging.info(data)

                if data["response"]["checkins"]["count"]>0:
                    user.lastCheckin = data["response"]["checkins"]["items"][0]["id"]
                    user.put()


        elif mode == 'getcategories':

            # get the 'general oauth user'
            oauth_user = UserProfile.gql("WHERE foursquareId = :1 ORDER BY joined ASC LIMIT 1",
                                 "7297232").get() # this generic user is bob@airrand.com

            if oauth_user is None:
                return self.response.out.write("something wrong, didn't get generic oauth user")
                                 
            url = "https://api.foursquare.com/v2/venues/categories?oauth_token=%s" % (oauth_user.foursquareAccessToken)
            result = urlfetch.fetch(url)
            if not result.status_code == 200:
                logging.info("problem getting first checkin for a new user")
                return
            data = simplejson.loads(result.content)

            categories = data["response"]["categories"]

            for category in categories:
                if "id"  in category:
                    newCategory = Category.get_or_insert(
                        category["id"],
                        name=category["name"],
                        icon=category["icon"]
                        )
                if "categories" in category:
                    for category in category["categories"]:
                        if "id" in category:
                            newCategory = Category.get_or_insert(
                                category["id"],
                                name=category["name"],
                                icon=category["icon"]
                                )
                        if "categories" in category:
                            for category in category["categories"]:
                                if "id" in category:
                                    newCategory = Category.get_or_insert(
                                        category["id"],
                                        name=category["name"],
                                        icon=category["icon"]
                                        )
                                if "categories" in category:
                                    for category in category["categories"]:
                                        if "id" in category:
                                            newCategory = Category.get_or_insert(
                                                category["id"],
                                                name=category["name"],
                                                icon=category["icon"]
                                                )