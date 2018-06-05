# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class DocsTestCase(TestCase):
    def test_docs_should_be_accessible(self):
        client = APIClient()

        response = client.get(reverse('api:v1:docs:index'))

        self.assertEquals(response.status_code, status.HTTP_200_OK)
