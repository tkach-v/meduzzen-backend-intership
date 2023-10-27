"""
Serializers for the user API View
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from companies.serializers import CompanyInvitationSerializer, CompanySerializer
from users.models import RequestStatuses, UserRequest


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object."""

    class Meta:
        model = get_user_model()
        fields = [
            'id',
            'email',
            'password',
            'first_name',
            'last_name',
            'created_at',
            'updated_at',
            'avatar'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8},
        }
        ordering = ['created_at']

    def create(self, validated_data):
        """Create and return a user with encrypted password."""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update and return user."""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)

        user.save()
        return user


class InvitationSerializer(CompanyInvitationSerializer):
    class Meta(CompanyInvitationSerializer.Meta):
        read_only_fields = ('company', 'sender', 'recipient', 'status')


class RequestsSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = UserRequest
        fields = '__all__'
        read_only_fields = ('sender', 'status')

    def validate_company(self, value):
        request = self.context.get("request")
        sender = request.user

        if value.members.filter(pk=sender.id).exists():
            raise serializers.ValidationError('You are already a member of the company.')
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        sender = request.user
        company_id = validated_data.get('company')

        existing_request = UserRequest.objects.filter(
            sender=sender,
            company_id=company_id,
            status=RequestStatuses.PENDING
        ).first()
        if existing_request:
            raise serializers.ValidationError({'detail': 'There is already a pending request to the same company.'})

        return super().create(validated_data)

    def get_status(self, obj):
        return RequestStatuses(obj.status).name.capitalize()


class UserCompaniesSerializer(CompanySerializer):
    class Meta(CompanySerializer.Meta):
        fields = ['id', 'name']
        read_only_fields = ('name',)
