from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

from notifications.models import Notification
from notifications.send_notification import send_notification
from quizz.models import Quiz, Result


@shared_task
def notify_users():
    notifications = []

    for user in get_user_model().objects.all():
        for quiz in Quiz.objects.filter(company__members=user):
            result = Result.objects.filter(user=user, quiz=quiz).order_by('-timestamp').first()

            if result and ((timezone.now() - result.timestamp).days >= quiz.frequency):
                notifications.append(Notification(
                    user=user,
                    text=f"Pass the quiz again: {quiz.title}"
                ))

    Notification.objects.bulk_create(notifications)
    for notification in notifications:
        send_notification(notification)
