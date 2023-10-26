from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from quizz import views

router = DefaultRouter()
router.register('',
                views.QuizViewSet,
                basename='quiz')

result_router = NestedSimpleRouter(router, '', lookup='quiz')
result_router.register('results',
                       views.ResultViewSet,
                       basename='results')

app_name = 'quizz'
urlpatterns = [
    path('', include(router.urls)),
    path('', include(result_router.urls)),
]
