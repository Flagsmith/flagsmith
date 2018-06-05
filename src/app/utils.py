import os
import random

import shortuuid


def create_hash():
    """Helper function to create a short hash"""
    return shortuuid.uuid()

def secret_key_gen():
    secret_key = ''.join(random.SystemRandom()
                         .choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)')
                         for i in range(50))
    os.environ['DJANGO_SECRET_KEY'] = secret_key
    return secret_key