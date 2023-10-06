from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users import views

invitations_router = DefaultRouter()
invitations_router.register('',
                views.UserInvitations,
                basename='invitations')

urlpatterns = [
    path('me/invitations/', include(invitations_router.urls)),
]
