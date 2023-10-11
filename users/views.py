"""
Views for the recipe APIs.
"""
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from companies.models import Company, CompanyInvitation, UserRequest
from companies.serializers import UserRequestSerializer
from users.serializers import InvitationSerializer, UserCompaniesSerializer, RequestsSerializer


class UserInvitations(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing users invitation, accepting or declining it
    """
    serializer_class = InvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return CompanyInvitation.objects.filter(recipient=user)

    @action(detail=True, methods=['POST'], url_path='accept')
    def accept_invitation(self, request, pk=None):
        instance = self.get_object()
        data = {'status': CompanyInvitation.ACCEPTED}
        serializer = self.get_serializer(instance=instance, data=data, partial=True)

        if serializer.is_valid():
            # Add the user to the company and change status of invitation
            user = self.request.user
            company = instance.company
            company.members.add(user)

            serializer.update(instance, data)
            return Response({'message': 'Invitation accepted'})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['POST'], url_path='decline')
    def decline_invitation(self, request, pk=None):
        instance = self.get_object()
        data = {'status': CompanyInvitation.DECLINED}
        serializer = self.get_serializer(instance=instance, data=data, partial=True)

        if serializer.is_valid():
            serializer.update(instance, data)
            return Response({'message': 'Invitation declined'})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRequests(mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.CreateModelMixin,
                   viewsets.GenericViewSet):
    """
    ViewSet for listing, creating, cancelling users request to the company
    """
    serializer_class = RequestsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return UserRequest.objects.filter(sender=user)

    def perform_create(self, serializer):
        sender = self.request.user
        company_id = self.request.data.get('company')

        company = Company.objects.get(pk=company_id)
        if company.members.filter(pk=sender.id).exists():
            return ValidationError({'detail': 'You are already a member of the company.'})

        existing_request = self.get_queryset().filter(
            sender=sender,
            company_id=company_id,
            status=UserRequest.PENDING
        ).first()
        if existing_request:
            return ValidationError({'detail': 'There is already a pending request to the same company.'})

        serializer.save(sender=sender)
        return None

    @action(detail=True, methods=['POST'], url_path='cancel')
    def cancel_request(self, request, pk=None):
        instance = self.get_object()
        data = {'status': UserRequest.CANCELLED}
        serializer = self.get_serializer(instance=instance, data=data, partial=True)

        if serializer.is_valid():
            serializer.update(instance, data)
            return Response({'message': 'Request cancelled'})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserCompanies(mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    """
    ViewSet for listing users companies, leaving company
    """
    serializer_class = UserCompaniesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Company.objects.filter(members=user)

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        company = self.get_object()

        if company.owner == request.user:
            return Response({'detail': 'Owner cannot leave the company'}, status=status.HTTP_400_BAD_REQUEST)

        company.members.remove(request.user)
        return Response({'message': 'User has left the company'})
