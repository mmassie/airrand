__author__ = 'robertralian'

TWILIO_ID = "AC27c1a25bce1325eb3bf4bb4f09895c91"
TWILIO_TOKEN = "d6ea9d4f201e4f4f4b45e81f684d7ed4"
TWILIO_API_VERSION = "2010-04-01"
############TWILIO_NUM = "(415) 599-2671"
TWILIO_NUM = "(415) 702-3798"

from ext import *
import handlers

class UserProfile(db.Model):

    joined = db.DateTimeProperty(auto_now_add=True)
    firstName = db.StringProperty(indexed=False)
    lastName = db.StringProperty(indexed=False)
    foursquareId = db.StringProperty()
    phone = db.StringProperty(indexed=False,
        required=False)
    twitter = db.StringProperty(indexed=False)
    facebookId = db.IntegerProperty(indexed=False)
    email = db.EmailProperty(indexed=False)
    status = db.IntegerProperty(indexed=False,
        default=0) # 0->just-joined, 1-> accepted terms
    foursquarePhoto = db.LinkProperty(indexed=False)
    foursquareFriendsCount = db.IntegerProperty(indexed=False)
    foursquareType = db.StringProperty(indexed=False,
        choices=set(["brand", "celebrity","user"]))
    homeCity = db.StringProperty(indexed=False)
    gender = db.StringProperty(indexed=False,
        choices=set(["male", "female"]))
    foursquareAccessToken = db.StringProperty()
    lastCheckin = db.StringProperty(default=None)
    emailPref = db.BooleanProperty(default=True)
    smsPref = db.BooleanProperty(default=True)

    # new partner (couple) stuff, allowing for >2 people per couple for future-proofing
    partner = db.SelfReferenceProperty(
        collection_name="partners")

    def sendSMS(self,body):

        import twilio

        recipient = self.phone
        account = twilio.Account(TWILIO_ID, TWILIO_TOKEN)
        params = { 'From': TWILIO_NUM, 'To': recipient, 'Body': body, }
        account.request('/%s/Accounts/%s/SMS/Messages' % (TWILIO_API_VERSION, TWILIO_ID), 'POST', params)

    def sendEmail(self,subject,body,sendVcard=None):

        from google.appengine.api import mail

        user_address = "\"%s %s\" <%s>" % (self.firstName, self.lastName, self.email)
        if not mail.is_email_valid(user_address):
            logging.info("bad email")
        else:
            sender_address = "airrand <info@airrand.com>"
            mail.send_mail(sender_address, user_address, subject, body)

    def sendRegistrationEmail(self):

        subject = "Welcome to airrand"
        body = """
Dear %s,
Thank you for creating an account at airrand.com. We hope you
find our location-based todo list helpful. Let us know if you
have any questions or suggestions for us.

Sincerely,
Your friends at airrand.com
""" % self.firstName
        self.sendEmail(subject,body)

    def getActiveTasks(self):

        query = db.GqlQuery("SELECT * FROM Task WHERE status=1 and user = :1",self)
        results = query.fetch(300)
        return results

    def getCompletedTasks(self):

        query = db.GqlQuery("SELECT * FROM Task WHERE status=2 and user = :1 ORDER BY completed DESC",self)
        results = query.fetch(300)
        return results

class Task(db.Model):

    user = db.ReferenceProperty(UserProfile,
        collection_name='tasks')
    what = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    completed = db.DateTimeProperty()
    status = db.IntegerProperty(default=1) # 1 -> active, 2 -> finished
    where = db.StringProperty()
    whereCanonical = db.StringListProperty()

class Places(db.Model):

    # this is for the actual names of places
    name = db.StringProperty()
    user = db.ReferenceProperty(UserProfile,
        collection_name='places')

class Category(db.Model):

    name = db.StringProperty()
    icon = db.LinkProperty(indexed=False)
    count = db.IntegerProperty(default=0)

class CheckIn(db.Model):

    user = db.ReferenceProperty(UserProfile,
        collection_name='checkins')
    name = db.StringProperty()
    time = db.DateTimeProperty(auto_now_add=True)
    categories = db.StringListProperty()
    categoriesPlusName = db.StringListProperty()
    venueJSON = db.TextProperty()


class EmailInvite(db.Model):

    created = db.DateTimeProperty(auto_now_add=True)
    type = db.IntegerProperty() #1=couple
    inviter = db.ReferenceProperty(UserProfile,
        collection_name='coupleInvites')
    invitee = db.ReferenceProperty(UserProfile,
        collection_name='coupleInvitesReceived')
    email = db.EmailProperty()
    name = db.StringProperty(indexed=False)
    firstName = db.StringProperty(indexed=False)
    lastName = db.StringProperty(indexed=False)
    message = db.TextProperty(indexed=False)
    clicked = db.DateTimeProperty()
    status = db.IntegerProperty(default=0)#0->created,1->sent,2->visited,3->accepted,-1->rejected,-2->rescinded

    # method mail invite

    def send(self):

        import logging
        from google.appengine.api import mail
        import os
        ON_LOCALHOST = ('Development' == os.environ['SERVER_SOFTWARE'][:11])
        if ON_LOCALHOST:
            DOMAIN = 'http://localhost:%s' % os.environ['SERVER_PORT']
        else:
            DOMAIN = "http://www.airrand.com"

        logging.info("sending invite email")
        sender_address = "airrand <info@airrand.com>"
        subject = "%s %s invites you to share a to-do list" % (self.inviter.firstName,self.inviter.lastName)
        inviteMsg = ""
        if self.message:
            inviteMsg = """
%s has this to say...
--------
%s
--------
""" % (self.inviter.firstName,self.message)
        body = """%s %s invites you to share a to-do list using airrand, a location smart to-do list.
%s
Click here to accept %s's invitation:
%s/share/%s



Thanks!
The airrand team

""" % (self.inviter.firstName,
                self.inviter.lastName,
                inviteMsg,
                self.inviter.firstName,
                DOMAIN,
                self.key().name()
                )
        mail.send_mail(sender_address, self.email, subject, body)
        self.status=1
        self.put()

    # method accept invite





#def base62_encode(num, alphabet=ALPHABET):
#    """Encode a number in Base X
#
#    `num`: The number to encode
#    `alphabet`: The alphabet to use for encoding
#    """
#    if (num == 0):
#        return alphabet[0]
#    arr = []
#    base = len(alphabet)
#    while num:
#        rem = num % base
#        num = num // base
#        arr.append(alphabet[rem])
#    arr.reverse()
#    return ''.join(arr)
#
#def base62_decode(string, alphabet=ALPHABET):
#    """Decode a Base X encoded string into the number
#
#    Arguments:
#    - `string`: The encoded string
#    - `alphabet`: The alphabet to use for encoding
#    """
#    base = len(alphabet)
#    strlen = len(string)
#    num = 0
#
#    idx = 0
#    for char in string:
#        power = (strlen - (idx + 1))
#        num += alphabet.index(char) * (base ** power)
#        idx += 1
#
#    return num




#-------------------------------------------------------------------------------
def uniqid(chars, alphabet="23456789abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"):
    import random
    arr = []
    for i in range(0,chars):
        arr.append(alphabet[random.randint(0, len(alphabet)-1)])
    return ''.join(arr)

class GeneralCounterShardConfig(db.Model):
    """Tracks the number of shards for each named counter."""
    name = db.StringProperty(required=True)
    num_shards = db.IntegerProperty(required=True, default=20)


class GeneralCounterShard(db.Model):
    """Shards for each named counter"""
    name = db.StringProperty(required=True)
    count = db.IntegerProperty(required=True, default=0)


def get_count(name):
    """Retrieve the value for a given sharded counter.

    Parameters:
      name - The name of the counter
    """
    total = memcache.get(name)
    import logging
    logging.info("total from memcache: %s: "% total)
    if total is None:
        total = 0
        for counter in GeneralCounterShard.all().filter('name = ', name):
            total += counter.count
        memcache.add(name, str(total), 60)
    logging.info("total get_count for %s: %s" % (name,total))
    return int(total)


def increment(name):
    import random
    """Increment the value for a given sharded counter.

    Parameters:
      name - The name of the counter
    """
    config = GeneralCounterShardConfig.get_or_insert(name, name=name)
    def txn():
        index = random.randint(0, config.num_shards - 1)
        shard_name = name + str(index)
        counter = GeneralCounterShard.get_by_key_name(shard_name)
        if counter is None:
            counter = GeneralCounterShard(key_name=shard_name, name=name)
        counter.count += 1
        counter.put()
    db.run_in_transaction(txn)
    memcache.incr(name, initial_value=0)


def increase_shards(name, num):
    """Increase the number of shards for a given sharded counter.
    Will never decrease the number of shards.

    Parameters:
      name - The name of the counter
      num - How many shards to use

    """
    config = GeneralCounterShardConfig.get_or_insert(name, name=name)
    def txn():
        if config.num_shards < num:
            config.num_shards = num
            config.put()
    db.run_in_transaction(txn)