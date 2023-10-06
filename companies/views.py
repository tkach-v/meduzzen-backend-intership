from rest_framework import permissions, viewsets, mixins
from rest_framework.exceptions import ValidationError

from companies import models, serializers
from companies import permissions as custom_permissions


class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.CompanySerializer

    def get_queryset(self):
        if self.request.method in permissions.SAFE_METHODS:
            # Filter companies to include only visible companies
            return models.Company.objects.filter(visible=True)

        # Include all companies
        return models.Company.objects.all()

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            # Allow editing only for the owner of the company
            return [permissions.IsAuthenticated(), custom_permissions.IsCompanyOwner()]

        # Allow reading and creating for any authenticated user
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        # Set the owner of the company to the current user, and add the user to the members
        owner = self.request.user
        members = self.request.data.get('members', [])

        if owner.id not in members:
            members.append(owner.id)

        serializer.save(owner=owner, members=members)


class CompanyInvitationViewSet(mixins.ListModelMixin,
                               mixins.RetrieveModelMixin,
                               mixins.CreateModelMixin,
                               mixins.DestroyModelMixin,
                               viewsets.GenericViewSet):
    """
    Viewset for lists invitations in the company, creating and deleting it
    """
    serializer_class = serializers.CompanyInvitationSerializer
    permission_classes = [permissions.IsAuthenticated, custom_permissions.CanAccessInvitationsAndRequests]

    def get_queryset(self):
        company_id = self.kwargs.get('company_pk')
        return models.CompanyInvitation.objects.filter(company_id=company_id)

    def perform_create(self, serializer):
        sender = self.request.user
        company_id = self.kwargs.get('company_pk')
        recipient = serializer.validated_data.get('recipient')

        company = models.Company.objects.get(pk=company_id)
        if company.members.filter(pk=recipient.id).exists():
            raise ValidationError("The recipient is already a member of the company.")

        existing_invitation = self.get_queryset().filter(
            sender=sender,
            recipient=recipient,
            company_id=company_id,
            pending=True
        ).first()

        if existing_invitation:
            raise ValidationError("There is already a pending invitation for the same recipient.")

        serializer.save(sender=sender, company_id=company_id)
