from rest_framework import serializers

from companies import models


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Company
        fields = '__all__'
        read_only_fields = ('owner', 'members')


class CompanyInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CompanyInvitation
        fields = '__all__'
        read_only_fields = ('company', 'sender', 'status')


class UserRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserRequest
        fields = '__all__'
        read_only_fields = ('company', 'sender', 'status')
