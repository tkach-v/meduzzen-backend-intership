from django.contrib.auth import get_user_model
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from helpers.count_score_with_dynamics import count_score_with_dynamics
from helpers.count_user_score import count_user_score
from helpers.export_results import export_results
from helpers.redis import set_quiz_result
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
        if self.action == 'export_results':
            return serializers.ExportResultsSerializer
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
        redis_data = {"questions": []}
        for user_answer in user_answers:
            question = user_answer.get("question")
            answers = user_answer.get("answers")

            if question is None or answers is None:
                raise ValidationError({"detail": "Each user_answer must include question_id and answer_ids"})

            try:
                question = quiz.questions.get(pk=question)
            except models.Question.DoesNotExist:
                raise ValidationError({"detail": f"Question with id #{question} not found"})

            question_data = {
                'question': question.id,
                'user_answers': answers,
                'is_correct': False
            }

            correct_answers = question.answers.filter(is_correct=True).values_list('id', flat=True)
            # Check if user's answer matches all correct answer IDs
            if set(answers) == set(correct_answers):
                score += 1
                question_data['is_correct'] = True

            redis_data['questions'].append(question_data)

        user = request.user
        total_questions = len(quiz.get_questions())
        result_data = {
            "quiz": quiz.id,
            "user": user.id,
            "correct_questions": score,
            "total_questions": total_questions,
        }
        redis_data['quiz'] = quiz.id
        redis_data['company'] = quiz.company.id
        redis_data['user'] = user.id

        serializer = serializers.ResultSerializer(data=result_data)
        if serializer.is_valid():
            instance = serializer.save()
            set_quiz_result(quiz.id, user.id, instance.timestamp, redis_data)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
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
            average_score = count_user_score(results)
            return Response({'average_score': average_score}, status=status.HTTP_200_OK)
        raise ValidationError({"detail": "User ID is required in query parameters."})

    @action(detail=True, methods=['GET'], url_path='last-taken-time')
    def last_taken_time(self, request, pk=None):
        quiz = self.get_object()
        user_id = request.query_params.get('user')

        if user_id is not None:
            try:
                user_id = int(user_id)
            except ValueError:
                return ValidationError({"detail": "Invalid user ID format."})

            try:
                result = models.Result.objects.filter(quiz=quiz, user_id=user_id).latest('timestamp')
                last_taken_time = result.timestamp
            except models.Result.DoesNotExist:
                last_taken_time = None

            return Response({'last_taken_time': last_taken_time}, status=status.HTTP_200_OK)
        raise ValidationError({"detail": "User ID is required in query parameters."})

    @action(detail=True, methods=['GET'], url_path='export-results/(?P<file_type>csv|json)')
    def export_results(self, request, file_type, pk=None):
        """ An action to export the results of quizzes that the user has passed """
        quiz = self.get_object()
        user = self.request.user

        return export_results(models.Result.objects.filter(quiz=quiz, user=user), file_type)

    @action(detail=False, methods=['GET'], url_path='user-quizzes-scores')
    def user_quizzes_scores(self, request):
        """ List of average scores for all quizzes of the selected user with dynamics over time """
        user_id = request.query_params.get('user')

        if user_id is not None:
            try:
                user_id = int(user_id)
            except ValueError:
                return ValidationError({"detail": "Invalid user ID format."})

            try:
                user = get_user_model().objects.get(pk=user_id)
            except get_user_model().DoesNotExist:
                raise ValidationError({'detail': 'User not found'})

            quizzes = models.Quiz.objects.filter(company__members=user).prefetch_related('company')
            data = []
            for quiz in quizzes:
                quiz_results = count_score_with_dynamics(models.Result.objects.filter(user=user, quiz=quiz))
                data.append({
                    'quiz_id': quiz.id,
                    'title': quiz.title,
                    'results': quiz_results,
                })
            serializer = serializers.QuizScoresSerializer(data, many=True)
            return Response(serializer.data)
        raise ValidationError({"detail": "User ID is required in query parameters."})

    @action(detail=False, methods=['GET'], url_path='all-users-scores')
    def all_users_scores(self, request):
        """ List of average scores of all users with dynamics over time """
        results = models.Result.objects.all()
        serializer = serializers.ScoreTimestampSerializer(count_score_with_dynamics(results), many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'], url_path='quizzes-scores')
    def quizzes_scores(self, request):
        """ List of average scores for each of the quiz from all companies with dynamics over time """
        quizzes = models.Quiz.objects.all()
        data = []

        for quiz in quizzes:
            quiz_results = count_score_with_dynamics(models.Result.objects.filter(quiz=quiz))
            data.append({
                'quiz_id': quiz.id,
                'title': quiz.title,
                'results': quiz_results,
            })
        serializer = serializers.QuizScoresSerializer(data, many=True)
        return Response(serializer.data)


class ResultViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.ResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        quiz_id = self.kwargs.get('quiz_pk')
        return models.Result.objects.filter(quiz_id=quiz_id)
