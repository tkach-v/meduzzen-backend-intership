from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from companies.models import Company, CompanyInvitation, InvitationStatuses
from users.models import RequestStatuses, UserRequest
from users.serializers import InvitationSerializer, RequestsSerializer, UserCompaniesSerializer


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
        data = {'status': InvitationStatuses.ACCEPTED}
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
        data = {'status': InvitationStatuses.DECLINED}
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
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=['POST'], url_path='cancel')
    def cancel_request(self, request, pk=None):
        instance = self.get_object()
        data = {'status': RequestStatuses.CANCELLED}
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

        if request.user in company.administrators.all():
            company.administrators.remove(request.user)
        company.members.remove(request.user)
        return Response({'message': 'User has left the company'})
