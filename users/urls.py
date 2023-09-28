"""
URL mappings for the users app.
"""

from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from users.views import UserViewSet

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

app_name = 'user'

urlpatterns = [
    path('', include(router.urls))
]