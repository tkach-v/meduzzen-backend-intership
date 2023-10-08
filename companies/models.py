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


class InvitationRequestMixin(TimeStampedModel):
    """
       Abstract model containing common fields for invitations and requests.
    """

    accepted = models.BooleanField(default=False)
    pending = models.BooleanField(default=True)

    class Meta:
        abstract = True


class CompanyInvitation(InvitationRequestMixin):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_invitations')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='received_invitations')
    company = models.ForeignKey(Company, on_delete=models.CASCADE)


class UserRequest(InvitationRequestMixin):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_requests')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='received_requests')
