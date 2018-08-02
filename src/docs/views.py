# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import schemas, response, renderers
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, renderer_classes, authentication_classes, \
    permission_classes, schema
from rest_framework.permissions import AllowAny
from rest_framework_swagger.renderers import SwaggerUIRenderer, OpenAPIRenderer


@api_view()
@renderer_classes([SwaggerUIRenderer, OpenAPIRenderer, renderers.CoreJSONRenderer])
@authentication_classes((SessionAuthentication,))
@permission_classes((AllowAny,))
@schema(None)
def schema_view(request):
    generator = schemas.SchemaGenerator(
        title='Bullet Train API'
    )
    return response.Response(generator.get_schema(request=request))
