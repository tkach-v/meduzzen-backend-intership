from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from quizz import models


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Answer
        fields = ['id', 'text', 'is_correct']


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)

    class Meta:
        model = models.Question
        fields = ['id', 'text', 'answers']

    def validate_answers(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Each question must have at least two answer options.")

        has_correct_answer = any(answer.get('is_correct', False) for answer in value)
        if not has_correct_answer:
            raise serializers.ValidationError("At least one answer must be marked as correct.")
        return value

    def create(self, validated_data):
        answers_data = validated_data.pop('answers', [])
        question = models.Question.objects.create(**validated_data)
        answers = [models.Answer(question=question, **answer_data) for answer_data in answers_data]
        models.Answer.objects.bulk_create(answers)

        return question


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = models.Quiz
        fields = ['id', 'title', 'description', 'frequency', 'company', 'created_at', 'updated_at', 'questions']

    def validate_questions(self, value):
        if len(value) < 2:
            raise ValidationError("A Quiz must have at least two questions.")

        return value

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])

        with transaction.atomic():
            quiz = models.Quiz.objects.create(**validated_data)
            questions = QuestionSerializer(data=questions_data, many=True)
            if questions.is_valid():
                questions.save(quiz=quiz)
            else:
                raise ValidationError(questions.errors)

            return quiz

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.frequency = validated_data.get('frequency', instance.frequency)
        instance.save()

        return instance


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Result
        fields = "__all__"


class ExportResultsSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    quiz = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    date_passed = serializers.SerializerMethodField()

    class Meta:
        model = models.Result
        fields = ['id', 'user', 'company', 'quiz', 'score', 'date_passed']

    # Define methods to get custom field values
    def get_user(self, obj):
        return obj.user.email

    def get_company(self, obj):
        return obj.quiz.company.name

    def get_quiz(self, obj):
        return obj.quiz.title

    def get_score(self, obj):
        return obj.correct_questions / obj.total_questions if obj.total_questions > 0 else 0

    def get_date_passed(self, obj):
        return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S')


class ScoreTimestampSerializer(serializers.Serializer):
    score = serializers.FloatField()
    timestamp = serializers.DateTimeField()


class QuizScoresSerializer(serializers.Serializer):
    quiz_id = serializers.IntegerField()
    title = serializers.CharField()
    results = ScoreTimestampSerializer(many=True)
