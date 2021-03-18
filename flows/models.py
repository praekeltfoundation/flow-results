from uuid import uuid4

from django.db import models


class Flow(models.Model):
    class Version(models.TextChoices):
        V1_0_0_RC1 = "1.0.0-rc.1"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, default="")
    version = models.CharField(max_length=255, choices=Version.choices)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=255, blank=True, default="")
    language = models.CharField(max_length=3, blank=True, default="")

    class Meta:
        ordering = ["modified"]
        indexes = [models.Index(fields=["modified"])]
