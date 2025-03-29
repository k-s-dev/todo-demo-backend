from django.contrib import admin

from core import models


class CustomAdmin(admin.ModelAdmin):
    def delete_queryset(self, request, queryset):
        for obj in queryset.all():
            obj.delete()


admin.site.register(models.Workspace)
admin.site.register(models.Category)
admin.site.register(models.Tag)
admin.site.register(models.Priority)
admin.site.register(models.Status)
admin.site.register(models.Project, CustomAdmin)
admin.site.register(models.Task, CustomAdmin)
