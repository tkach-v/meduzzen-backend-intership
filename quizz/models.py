from django.conf import settings
from django.db import models

from common.models import TimeStampedModel
from companies.models import Company


class Quiz(TimeStampedModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    frequency = models.PositiveIntegerField()
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return self.title

    def get_questions(self):
        return self.questions.all()


class Question(models.Model):
    text = models.TextField()
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')

    def __str__(self):
        return self.text

    def get_answers(self):
        return self.answers.all()


class Answer(models.Model):
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')

    def __str__(self):
        return self.text


class Result(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.SET_NULL, blank=True, null=True)
    correct_questions = models.PositiveIntegerField()
    total_questions = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} passed quiz '{self.quiz}'"
