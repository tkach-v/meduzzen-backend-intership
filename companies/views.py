from rest_framework import permissions
from rest_framework import viewsets

from companies import models, serializers
from companies import permissions as custom_permissions


class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.CompanySerializer

    def get_queryset(self):
        if self.request.method in permissions.SAFE_METHODS:
            # Filter companies to include only visible companies
            return models.Company.objects.filter(visible=True)
        else:
            # Include all companies
            return models.Company.objects.all()

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            # Allow editing only for the owner of the company
            return [permissions.IsAuthenticated(), custom_permissions.IsCompanyOwner()]
        else:
            # Allow reading and creating for any authenticated user
            return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        # Set the owner of the company to the current user, and add the user to the members
        owner = self.request.user
        members = self.request.data.get('members', [])

        if owner.id not in members:
            members.append(owner.id)

        serializer.save(owner=owner, members=members)

