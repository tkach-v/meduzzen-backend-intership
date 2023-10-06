from rest_framework import permissions
from companies import models


class IsCompanyOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class CanAccessInvitationsAndRequests(permissions.BasePermission):
    def has_permission(self, request, view):
        company_id = view.kwargs.get('company_pk')
        user = request.user

        try:
            company = models.Company.objects.get(id=company_id)
            return company.owner == user
        except models.Company.DoesNotExist:
            return False
