from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from quizz import models, serializers
from quizz.permissions import IsOwnerOrAdministrator


class QuizViewSet(viewsets.ModelViewSet):
    """
    ViewSet for quizzes CRUD operations
    """

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
            'add_question',
            'remove_question'
        ]:
            return [permissions.IsAuthenticated(), IsOwnerOrAdministrator()]

        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'add_question':
            return serializers.QuestionSerializer
        return serializers.QuizSerializer

    @action(detail=True,
            url_path='remove-question',
            methods=['POST'])
    def remove_question(self, request, pk=None):
        quiz = self.get_object()

        if len(quiz.get_questions()) <= 2:
            raise ValidationError({'detail': 'You can not delete the last 2 questions!'})

        question_id = request.data.get('question_id')
        if question_id is None:
            raise ValidationError({'detail': 'question_id is required'})

        try:
            question_id = int(question_id)
        except ValueError:
            raise ValidationError({'detail': 'question_id must be an integer'})

        try:
            question = models.Question.objects.get(pk=question_id)
        except ValueError:
            raise ValidationError({'detail': 'question_id must be an integer'})

        if question.quiz == quiz and question in quiz.get_questions():
            question.delete()
            return Response({'message': 'Question removed successfully'})

        raise ValidationError({'detail': 'Question is not a part of the quiz!'})

    @action(detail=True,
            url_path='add_question',
            methods=['POST'],
            )
    def add_question(self, request, pk=None):
        quiz = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            serializer.save(quiz=quiz)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        raise ValidationError(serializer.errors)
