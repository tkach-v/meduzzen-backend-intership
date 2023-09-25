from django.contrib import admin
from health_check import models

admin.site.register(models.TimeStampedModel)
