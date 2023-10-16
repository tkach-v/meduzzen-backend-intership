from enum import IntEnum

from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class Company(TimeStampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_companies')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='companies_joined', blank=True)
    visible = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name


class InvitationStatuses(IntEnum):
    ACCEPTED = 1
    DECLINED = 2
    REVOKED = 3
    PENDING = 4

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class CompanyInvitation(TimeStampedModel):
    status = models.IntegerField(choices=InvitationStatuses.choices(), default=InvitationStatuses.PENDING)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_invitations')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='received_invitations')
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
