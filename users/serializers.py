"""
Serializers for the user API View
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from companies.models import UserRequest
from companies.serializers import CompanyInvitationSerializer, CompanySerializer


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

        user.set_password(password)
        user.save()
        return user


class InvitationSerializer(CompanyInvitationSerializer):
    class Meta(CompanyInvitationSerializer.Meta):
        read_only_fields = ('company', 'sender', 'recipient', 'status')


class RequestsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRequest
        fields = '__all__'
        read_only_fields = ('sender', 'status')


class UserCompaniesSerializer(CompanySerializer):
    class Meta(CompanySerializer.Meta):
        fields = ['id', 'name']
        read_only_fields = ('name',)
