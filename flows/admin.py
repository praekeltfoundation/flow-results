from django.contrib import admin

from flows.models import Flow


@admin.register(Flow)
class FlowAdmin(admin.ModelAdmin):
    date_hierarchy = "modified"
    fields = ("id", "name", "version", "created", "modified", "title", "language")
    list_display = ("name", "title", "language", "modified")
