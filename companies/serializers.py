from rest_framework import serializers

from companies import models
from users.models import RequestStatuses, UserRequest


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Company
        fields = '__all__'
        read_only_fields = ('owner', 'members', 'administrators')


class CompanyInvitationSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = models.CompanyInvitation
        fields = '__all__'
        read_only_fields = ('company', 'sender', 'status')

    def get_status(self, obj):
        return models.InvitationStatuses(obj.status).name.capitalize()


class CompanyRequestSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = UserRequest
        fields = '__all__'
        read_only_fields = ('company', 'sender', 'status')

    def get_status(self, obj):
        return RequestStatuses(obj.status).name.capitalize()
