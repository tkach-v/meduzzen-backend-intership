from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from notifications import models, serializers


class Notifications(mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    """
    ViewSet for listing users pending notifications, marking them as read
    """
    serializer_class = serializers.NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return models.Notification.objects.filter(user=user, status=models.NotificationStatuses.PENDING)

    @action(detail=True, methods=['post'], url_path='mark-as-read')
    def mark_as_read(self, request, pk=None):
        instance = self.get_object()
        data = {'status': models.NotificationStatuses.READ}
        serializer = self.get_serializer(instance=instance, data=data, partial=True)

        if serializer.is_valid():
            serializer.update(instance, data)
            return Response({'message': 'Notification was marked as read'})

        raise ValidationError(serializer.errors)
