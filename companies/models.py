from django.db import models
from django.conf import settings


class Company(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_companies')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='companies_joined', blank=True)
    visible = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Companies"
