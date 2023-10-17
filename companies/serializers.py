from rest_framework import serializers

from companies import models
from users.models import UserRequest


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Company
        fields = '__all__'
        read_only_fields = ('owner', 'members', 'administrators')


class CompanyInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CompanyInvitation
        fields = '__all__'
        read_only_fields = ('company', 'sender', 'status')


class CompanyRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRequest
        fields = '__all__'
        read_only_fields = ('company', 'sender', 'status')
