from rest_framework import permissions

from companies import models


class IsCompanyOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsCompanyOwnerNested(permissions.BasePermission):
    def has_permission(self, request, view):
        company_id = view.kwargs.get('company_pk')
        user = request.user

        try:
            company = models.Company.objects.get(id=company_id)
            return company.owner == user
        except models.Company.DoesNotExist:
            return False


class IsRequestOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        user_request = view.get_object()
        return user_request.sender == request.user


class IsRequestOwnerOrCompanyOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        is_company_owner = IsCompanyOwnerNested().has_permission(request, view)
        is_request_owner = IsRequestOwner().has_permission(request, view)
        return is_company_owner or is_request_owner
