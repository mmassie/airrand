__author__="robertralian"
__date__ ="$Feb 25, 2011 4:44:38 PM$"

from ext import *
from django.core.validators import email_re
import logging

def uniqifyList(seq, idfun=None):
    # order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result

def isValidEmail(email):
    if email_re.match(email):
        return True
    return False

def allSkills(self):

    # return list of skill names
    allSkills = memcache.get("allSkills")
    if allSkills is not None:
        return allSkills
    else:
        allSkills = db.GqlQuery("SELECT name FROM skill WHERE valid=True ORDER BY numUsers DESC").fetch(100)
        memcache.add("allSkills", data, 60)
        return allSkills