
from django.contrib.auth import get_user_model
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from companies import models, serializers
from companies import permissions as custom_permissions
from helpers.count_user_score import count_user_score
from helpers.export_results import export_results
from quizz.models import Quiz, Result
from quizz.serializers import QuizSerializer
from users.models import RequestStatuses, UserRequest


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
        if self.action in [
            'update',
            'partial_update',
            'destroy',
            'remove_user',
            'add_admin',
            'remove_admin'
        ]:
            # Allow editing only for the owner of the company
            return [permissions.IsAuthenticated(), custom_permissions.IsCompanyOwner()]
        if self.action == 'export_results':
            return [permissions.IsAuthenticated(), custom_permissions.IsCompanyOwnerOrAdmin()]

        # Allow reading and creating for any authenticated user
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        # Set the owner of the company to the current user, and add the user to the members
        owner = self.request.user
        members = self.request.data.get('members', [])

        if owner.id not in members:
            members.append(owner.id)

        serializer.save(owner=owner, members=members)

    def validate_user_id(self, user_id):
        if user_id is None:
            raise ValidationError({'detail': 'user_id is required'})

        try:
            user_id = int(user_id)
        except ValueError:
            raise ValidationError({'detail': 'user_id must be an integer'})

        try:
            user = get_user_model().objects.get(pk=user_id)
        except get_user_model().DoesNotExist:
            raise ValidationError({'detail': 'User not found'})

        return user

    @action(detail=True,
            url_path='remove-user',
            methods=['POST'])
    def remove_user(self, request, pk=None):
        company = self.get_object()
        user = self.validate_user_id(request.data.get('user_id'))

        if user == company.owner:
            raise ValidationError({'detail': 'Cannot remove the owner of the company'})

        if user in company.members.all():
            if user in company.administrators.all():
                company.administrators.remove(user)
            company.members.remove(user)
            return Response({'message': 'User removed successfully'})

        raise ValidationError({'detail': 'User is not a member of the company'})

    @action(detail=True,
            url_path='add-admin',
            methods=['POST'])
    def add_admin(self, request, pk=None):
        company = self.get_object()
        user = self.validate_user_id(request.data.get('user_id'))

        if user not in company.members.all():
            raise ValidationError({'detail': 'User is not a member of the company'})

        if user == company.owner:
            raise ValidationError({'detail': 'Cannot add the owner to the administrators'})

        company.administrators.add(user)
        return Response({'message': 'Administrator added successfully'})

    @action(detail=True,
            url_path='remove-admin',
            methods=['POST'])
    def remove_admin(self, request, pk=None):
        company = self.get_object()
        user = self.validate_user_id(request.data.get('user_id'))

        if user in company.administrators.all():
            company.administrators.remove(user)
            return Response({'message': 'Administrator removed successfully'})

        raise ValidationError({'detail': 'User is not an administrator of the company'})

    @action(detail=True, methods=['GET'])
    def quizzes(self, request, pk=None):
        company = self.get_object()

        # Check if the user is a member of the company before retrieving quizzes
        if request.user in company.members.all():
            quizzes = Quiz.objects.filter(company=company)
            serializer = QuizSerializer(quizzes, many=True)
            return Response(serializer.data)

        return Response({"detail": "You are not a member of this company."}, status=403)

    @action(detail=True, methods=['GET'], url_path='user-score')
    def user_score(self, request, pk=None):
        """ Show average score of user per company """
        company = self.get_object()
        user_id = request.query_params.get('user')

        if user_id is not None:
            try:
                user_id = int(user_id)
            except ValueError:
                return ValidationError({"detail": "Invalid user ID format."})

            if user_id not in company.members.values_list('id', flat=True):
                raise ValidationError({"detail": "User is not a member of this company."})

            results = Result.objects.filter(quiz__company=company, user_id=user_id)
            average_score = count_user_score(results)
            return Response({'average_score': average_score}, status=status.HTTP_200_OK)
        raise ValidationError({"detail": "User ID is required in query parameters."})

    @action(detail=True, methods=['GET'], url_path='export-results/(?P<file_type>csv|json)')
    def export_results(self, request, file_type, pk=None):
        """ An action to export the results of quizzes within the company """
        company = self.get_object()
        user_id = request.query_params.get('user')

        if user_id is not None:
            try:
                user_id = int(user_id)
            except ValueError:
                return ValidationError({"detail": "Invalid user ID format."})

            if user_id not in company.members.values_list('id', flat=True):
                raise ValidationError({"detail": "User is not a member of this company."})

            results = Result.objects.filter(quiz__company=company, user_id=user_id)

        else:
            results = Result.objects.filter(quiz__company=company)

        return export_results(results, file_type)


class CompanyInvitationViewSet(mixins.ListModelMixin,
                               mixins.RetrieveModelMixin,
                               mixins.CreateModelMixin,
                               viewsets.GenericViewSet):
    """
    ViewSet for listing, creating and cancelling invitations in the company
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
            status=models.InvitationStatuses.PENDING
        ).first()

        if existing_invitation:
            raise ValidationError("There is already a pending invitation for the same recipient.")

        serializer.save(sender=sender, company_id=company_id)

    @action(detail=True, methods=['POST'], url_path='revoke')
    def revoke_invitation(self, request, pk=None, company_pk=None):
        instance = self.get_object()
        data = {'status': models.InvitationStatuses.REVOKED}
        serializer = self.get_serializer(instance=instance, data=data, partial=True)

        if serializer.is_valid():
            serializer.update(instance, data)
            return Response({'message': 'Invitation revoked'})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompanyRequestViewSet(mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            viewsets.GenericViewSet):
    """
    ViewSet for listing requests in the company
    Owner can see list of requests for his company, approve or reject it
    """
    serializer_class = serializers.CompanyRequestSerializer
    permission_classes = [permissions.IsAuthenticated, custom_permissions.IsCompanyOwnerNested]

    def get_queryset(self):
        company_id = self.kwargs.get('company_pk')
        return UserRequest.objects.filter(company_id=company_id)

    @action(detail=True, methods=['POST'], url_path='approve')
    def approve_request(self, request, pk=None, company_pk=None):
        instance = self.get_object()
        data = {'status': RequestStatuses.APPROVED}
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
        data = {'status': RequestStatuses.REJECTED}
        serializer = self.get_serializer(instance=instance, data=data, partial=True)

        if serializer.is_valid():
            serializer.update(instance, data)
            return Response({'message': 'Request rejected'})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
