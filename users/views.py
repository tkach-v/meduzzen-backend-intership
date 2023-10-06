"""
Views for the recipe APIs.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from companies.models import CompanyInvitation
from users.serializers import InvitationSerializer


class UserInvitations(viewsets.ReadOnlyModelViewSet):
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
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['POST'], url_path='decline')
    def decline_invitation(self, request, pk=None):
        instance = self.get_object()
        data = {'accepted': False, 'pending': False}
        serializer = self.get_serializer(instance=instance, data=data, partial=True)

        if serializer.is_valid():
            serializer.update(instance, data)
            return Response({'message': 'Invitation declined'})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)