from rest_framework import permissions

from companies.models import Company


class IsOwnerOrAdministrator(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == 'create':
            company_id = request.data.get('company')
            if company_id:
                try:
                    company = Company.objects.get(id=company_id)
                except Company.DoesNotExist:
                    company = None

                if company:
                    return company.owner == request.user or request.user in company.administrators.all()
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if view.action in ['update', 'partial_update', 'destroy']:
            if obj.company:
                return obj.company.owner == request.user or request.user in obj.company.administrators.all()

        return True
