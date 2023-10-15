from enum import IntEnum

from django.conf import settings
from django.db import models

from common.models import CustomAbstractUser, TimeStampedModel
from companies.models import Company


class CustomUser(CustomAbstractUser):
    avatar = models.ImageField(upload_to='avatars', default='avatars/default.jpg')


class RequestStatuses(IntEnum):
    APPROVED = 1
    REJECTED = 2
    CANCELLED = 3
    PENDING = 4

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class UserRequest(TimeStampedModel):
    status = models.IntegerField(choices=RequestStatuses.choices(), default=RequestStatuses.PENDING)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_requests')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='received_requests')
