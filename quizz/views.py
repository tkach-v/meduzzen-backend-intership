from django.db.models import Sum
from rest_framework import permissions, status, viewsets
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

    @action(detail=True, url_path='undergo', methods=['POST'])
    def undergo(self, request, pk=None):
        quiz = self.get_object()
        user_answers = request.data.get("user_answers")

        if not user_answers:
            raise ValidationError({"detail": "user_answers is required"})

        if not isinstance(user_answers, list):
            raise ValidationError({"detail": "Invalid format for user_answers"})

        score = 0

        for user_answer in user_answers:
            question = user_answer.get("question")
            answers = user_answer.get("answers")

            if question is None or answers is None:
                raise ValidationError({"detail": "Each user_answer must include question_id and answer_ids"})

            try:
                question = quiz.questions.get(pk=question)
            except models.Question.DoesNotExist:
                raise ValidationError({"detail": f"Question with id #{question} not found"})

            correct_answers = question.answers.filter(is_correct=True).values_list('id', flat=True)
            # Check if user's answer matches all correct answer IDs
            if set(answers) == set(correct_answers):
                score += 1

        user = request.user
        total_questions = len(quiz.get_questions())
        result_data = {
            "quiz": quiz.id,
            "user": user.id,
            "correct_questions": score,
            "total_questions": total_questions,
        }

        serializer = serializers.ResultSerializer(data=result_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'], url_path='user-score')
    def user_score(self, request):
        """ Show average score of user across the entire system """
        user_id = request.query_params.get('user')

        if user_id is not None:
            try:
                user_id = int(user_id)
            except ValueError:
                return ValidationError({"detail": "Invalid user ID format."})

            results = models.Result.objects.filter(user_id=user_id)
            if results.exists():
                total_correct_questions = results.aggregate(Sum('correct_questions'))['correct_questions__sum']
                total_total_questions = results.aggregate(Sum('total_questions'))['total_questions__sum']

                if total_correct_questions is not None and total_total_questions is not None:
                    average_score = total_correct_questions / total_total_questions
                else:
                    average_score = 0
                return Response({'average_score': average_score}, status=status.HTTP_200_OK)
            else:
                return Response({'average_score': 0}, status=status.HTTP_200_OK)
        else:
            raise ValidationError({"detail": "User ID is required in query parameters."})


class ResultViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.ResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        quiz_id = self.kwargs.get('quiz_pk')
        return models.Result.objects.filter(quiz_id=quiz_id)
