from django.urls import include, path

app_name = 'custom_auth'

urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('trench.urls')),  # MFA
    path('', include('trench.urls.djoser')),  # override necessary urls for MFA auth
]
