from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users import views

invitations_router = DefaultRouter()
invitations_router.register('',
                            views.UserInvitations,
                            basename='invitations')

requests_router = DefaultRouter()
requests_router.register('',
                            views.UserRequests,
                            basename='requests')

companies_router = DefaultRouter()
companies_router.register('',
                          views.UserCompanies,
                          basename='companies')

urlpatterns = [
    path('me/companies/', include(companies_router.urls)),
    path('me/invitations/', include(invitations_router.urls)),
    path('me/requests/', include(requests_router.urls)),
]
