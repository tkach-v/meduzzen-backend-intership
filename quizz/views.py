from rest_framework import permissions, viewsets

from quizz import models, serializers
from quizz.permissions import IsOwnerOrAdministrator


class QuizViewSet(viewsets.ModelViewSet):
    """
    ViewSet for quizzes CRUD operations
    """
    serializer_class = serializers.QuizSerializer

    def get_queryset(self):
        # show users only quizzes from companies of which they are members
        user = self.request.user
        return models.Quiz.objects.filter(company__members=user)

    def get_permissions(self):
        if self.action in [
            'create',
            'update',
            'partial_update',
            'destroy',
        ]:
            return [permissions.IsAuthenticated(), IsOwnerOrAdministrator()]

        return [permissions.IsAuthenticated()]
