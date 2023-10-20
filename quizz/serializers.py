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
        fields = ['text', 'answers']

    def validate_answers(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Each question must have at least two answer options.")

        has_correct_answer = any(answer.get('is_correct', False) for answer in value)
        if not has_correct_answer:
            raise serializers.ValidationError("At least one answer must be marked as correct.")
        return value


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
        quiz = models.Quiz.objects.create(**validated_data)

        for question_data in questions_data:
            answers_data = question_data.pop('answers', [])
            question = models.Question.objects.create(quiz=quiz, **question_data)

            for answer_data in answers_data:
                models.Answer.objects.create(question=question, **answer_data)

        quiz.refresh_from_db()
        return quiz

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', [])

        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.frequency = validated_data.get('frequency', instance.frequency)
        instance.save()

        if questions_data:
            with transaction.atomic():
                instance.questions.all().delete()

                for question_data in questions_data:
                    answers_data = question_data.pop('answers', [])
                    question = models.Question.objects.create(quiz=instance, **question_data)

                    for answer_data in answers_data:
                        models.Answer.objects.create(question=question, **answer_data)

        return instance
