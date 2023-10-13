from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from companies import views

router = DefaultRouter()
router.register('',
                views.CompanyViewSet,
                basename='company')

# routers for invitations and requests based on company_id
nested_router = NestedSimpleRouter(router, '', lookup='company')
nested_router.register('invitations',
                       views.CompanyInvitationViewSet,
                       basename='invitations')
nested_router.register('requests',
                       views.CompanyRequestViewSet,
                       basename='requests')

app_name = 'companies'
urlpatterns = [
    path('', include(router.urls)),
    path('', include(nested_router.urls)),
]
