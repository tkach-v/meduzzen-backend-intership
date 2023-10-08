from django.contrib.auth import get_user_model
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from companies import models, serializers
from companies import permissions as custom_permissions


class CompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for company CRUD operations, removing users from the company
    """
    serializer_class = serializers.CompanySerializer

    def get_queryset(self):
        if self.request.method in permissions.SAFE_METHODS:
            # Filter companies to include only visible companies
            return models.Company.objects.filter(visible=True)

        # Include all companies
        return models.Company.objects.all()

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy', 'remove_user']:
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

    @action(detail=True,
            url_path='remove-user',
            methods=['POST'])
    def remove_user(self, request, pk=None):
        company = self.get_object()
        user_id = request.data.get('user_id')

        if user_id is None:
            return Response({'detail': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = int(user_id)
        except ValueError:
            return Response({'detail': 'user_id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = get_user_model().objects.get(pk=user_id)
        except get_user_model().DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if user == company.owner:
            return Response({'detail': 'Cannot remove the owner of the company'}, status=status.HTTP_400_BAD_REQUEST)

        if user in company.members.all():
            company.members.remove(user)
            return Response({'message': 'User removed successfully'})

        return Response({'detail': 'User is not a member of the company'}, status=status.HTTP_400_BAD_REQUEST)


class CompanyInvitationViewSet(mixins.ListModelMixin,
                               mixins.RetrieveModelMixin,
                               mixins.CreateModelMixin,
                               mixins.DestroyModelMixin,
                               viewsets.GenericViewSet):
    """
    Viewset for listing invitations in the company, creating and deleting it
    """
    serializer_class = serializers.CompanyInvitationSerializer
    permission_classes = [permissions.IsAuthenticated, custom_permissions.IsCompanyOwnerNested]

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


class UserRequestViewSet(mixins.ListModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.CreateModelMixin,
                         mixins.DestroyModelMixin,
                         viewsets.GenericViewSet):
    """
    ViewSet for listing requests in the company
    User can create and delete request
    Company owner can see list of requests for his company, approve or reject it
    """
    serializer_class = serializers.UserRequestSerializer

    def get_queryset(self):
        company_id = self.kwargs.get('company_pk')
        return models.UserRequest.objects.filter(company_id=company_id, pending=True)

    def get_permissions(self):
        if self.action in ['list', 'approve_request', 'reject_request']:
            return [permissions.IsAuthenticated(), custom_permissions.IsCompanyOwnerNested()]
        if self.action == 'retrieve':
            return [permissions.IsAuthenticated(), custom_permissions.IsRequestOwnerOrCompanyOwner()]
        if self.action == 'destroy':
            return [permissions.IsAuthenticated(), custom_permissions.IsRequestOwner()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        sender = self.request.user
        company_id = self.kwargs.get('company_pk')
        company = models.Company.objects.get(pk=company_id)

        if company.members.filter(pk=sender.id).exists():
            return Response({'detail': 'You are already a member of the company.'}, status=status.HTTP_400_BAD_REQUEST)

        existing_request = self.get_queryset().filter(
            sender=sender,
            company_id=company_id,
            pending=True
        ).first()

        if existing_request:
            return Response({'detail': 'There is already a pending request to the same company.'},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer.save(sender=sender, company_id=company_id)
        return None

    @action(detail=True, methods=['POST'], url_path='approve')
    def approve_request(self, request, pk=None, company_pk=None):
        instance = self.get_object()
        data = {'accepted': True, 'pending': False}
        serializer = self.get_serializer(instance=instance, data=data, partial=True)

        if serializer.is_valid():
            # Add the user to the company and change status of invitation
            user = instance.sender
            company = instance.company
            company.members.add(user)

            serializer.update(instance, data)
            return Response({'message': 'Request approved'})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['POST'], url_path='reject')
    def reject_request(self, request, pk=None, company_pk=None):
        instance = self.get_object()
        data = {'accepted': False, 'pending': False}
        serializer = self.get_serializer(instance=instance, data=data, partial=True)

        if serializer.is_valid():
            serializer.update(instance, data)
            return Response({'message': 'Request rejected'})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
