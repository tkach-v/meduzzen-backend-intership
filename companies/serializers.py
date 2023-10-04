from django.conf import settings
from rest_framework import serializers
from .models import Company


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ('id', 'name', 'description', 'owner', 'members', 'visible')
        read_only_fields = ('owner', )
