from django.contrib import admin

from quizz import models


class QuizzAdmin(admin.ModelAdmin):
    list_display = ["title", "company"]
    search_fields = ["title", "company", "description"]
    list_filter = ["title", "company"]


class QuestionAdmin(admin.ModelAdmin):
    list_display = ["text", "quiz"]
    search_fields = ["text"]
    list_filter = ["text", "quiz"]


class AnswearAdmin(admin.ModelAdmin):
    list_display = ["text", "question"]
    search_fields = ["text"]
    list_filter = ["text", "question"]


admin.site.register(models.Quiz, QuizzAdmin)
admin.site.register(models.Question, QuestionAdmin)
admin.site.register(models.Answer, AnswearAdmin)
