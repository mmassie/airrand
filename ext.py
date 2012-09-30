__author__ = 'robertralian'

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

# import from appengine's libs
from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache

from django.utils import simplejson
# import models
from models import *