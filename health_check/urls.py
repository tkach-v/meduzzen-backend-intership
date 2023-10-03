from django.urls import path

from health_check import views

urlpatterns = [
    path('', views.HealthCheck.as_view()),
]
