from rest_framework import serializers

from companies import models


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Company
        fields = '__all__'
        read_only_fields = ('owner',)


class CompanyInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CompanyInvitation
        fields = '__all__'
        read_only_fields = ('company', 'sender', 'accepted', 'pending')
