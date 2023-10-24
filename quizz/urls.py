from django.urls import include, path
from rest_framework.routers import DefaultRouter

from quizz import views

router = DefaultRouter()
router.register('',
                views.QuizViewSet,
                basename='quizz')

app_name = 'quizz'
urlpatterns = [
    path('', include(router.urls)),
]
