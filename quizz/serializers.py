from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from quizz import models


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Answer
        fields = ['text', 'is_correct']


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
        fields = ['id', 'title', 'description', 'frequency', 'company', 'questions']

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
