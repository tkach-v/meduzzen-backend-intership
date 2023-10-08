"""
Views for the recipe APIs.
"""
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from companies.models import Company, CompanyInvitation, UserRequest
from companies.serializers import UserRequestSerializer
from users.serializers import InvitationSerializer, UserCompaniesSerializer


class UserInvitations(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing users invitation, accepting or declining it
    """
    serializer_class = InvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return CompanyInvitation.objects.filter(recipient=user, pending=True)

    @action(detail=True, methods=['POST'], url_path='accept')
    def accept_invitation(self, request, pk=None):
        instance = self.get_object()
        data = {'accepted': True, 'pending': False}
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
        data = {'accepted': False, 'pending': False}
        serializer = self.get_serializer(instance=instance, data=data, partial=True)

        if serializer.is_valid():
            serializer.update(instance, data)
            return Response({'message': 'Invitation declined'})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRequests(mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    serializer_class = UserRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    """
    ViewSet for listing users request to the company
    """

    def get_queryset(self):
        user = self.request.user
        return UserRequest.objects.filter(sender=user, pending=True)


class UserCompanies(mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    serializer_class = UserCompaniesSerializer
    permission_classes = [permissions.IsAuthenticated]
    """
    ViewSet for listing users companies, leaving company
    """

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
