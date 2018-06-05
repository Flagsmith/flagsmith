# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Identity, Environment

admin.site.register(Identity)
admin.site.register(Environment)
