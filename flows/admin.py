from django.contrib import admin

from flows.models import Flow, FlowQuestion


class FlowQuestionInline(admin.TabularInline):
    model = FlowQuestion


@admin.register(Flow)
class FlowAdmin(admin.ModelAdmin):
    date_hierarchy = "modified"
    fields = ("id", "name", "version", "title", "language")
    list_display = ("name", "title", "language", "modified")
    inlines = [FlowQuestionInline]
