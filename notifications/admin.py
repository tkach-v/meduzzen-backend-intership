from django.contrib import admin

from notifications import models


class NotificationsAdmin(admin.ModelAdmin):
    list_display = ["user", "status", "text"]
    search_fields = ["user", "status", "text"]
    list_filter = ["user", "status", "text"]


admin.site.register(models.Notification, NotificationsAdmin)
