import os
import sys
import random

import shortuuid
import dj_database_url

if sys.version_info.major > 2:  # Python 3 or later
    from urllib.parse import quote
else:  # Python 2
    from urllib import quote

def create_hash():
    """Helper function to create a short hash"""
    return shortuuid.uuid()

def secret_key_gen():
    secret_key = ''.join(random.SystemRandom()
                         .choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)')
                         for i in range(50))
    os.environ['DJANGO_SECRET_KEY'] = secret_key
    return secret_key

def parse_database_url(db_uri):
    """Helper function to parse DB URI and handle special characters"""
    return dj_database_url.parse(quote(db_uri, ':/@'), conn_max_age=60)
