from django.contrib import admin

from companies import models


class CompaniesAdmin(admin.ModelAdmin):
    list_display = ["name", "owner"]
    search_fields = ['name', 'description']
    list_filter = ['name', 'owner']


admin.site.register(models.Company, CompaniesAdmin)
