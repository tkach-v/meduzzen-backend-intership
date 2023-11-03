from rest_framework import serializers

from notifications.models import Notification, NotificationStatuses


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
