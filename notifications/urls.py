from django.urls import include, path
from rest_framework.routers import DefaultRouter

from notifications import views

router = DefaultRouter()
router.register('',
                views.Notifications,
                basename='notifications')

urlpatterns = [
    path('', include(router.urls)),
]
