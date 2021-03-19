from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models


class Flow(models.Model):
    class Version(models.TextChoices):
        V1_0_0_RC1 = "1.0.0-rc.1"

    id = models.UUIDField(primary_key=True, default=uuid4)
    name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        validators=[
            RegexValidator(
                r"^[a-z0-9-\._]*$",
                "can only contain lowercase, alphanumeric characters and '-', '_', '.'",
            )
        ],
    )
    version = models.CharField(max_length=255, choices=Version.choices)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=255, blank=True, default="")
    language = models.CharField(
        max_length=3, blank=True, default="", validators=[MinLengthValidator(3)]
    )

    class Meta:
        ordering = ["modified"]
        indexes = [models.Index(fields=["modified"])]


class FlowQuestion(models.Model):
    class Type(models.TextChoices):
        SELECT_ONE = "select_one"
        SELECT_MANY = "select_many"
        NUMERIC = "numeric"
        OPEN = "open"
        TEXT = "text"
        IMAGE = "image"
        VIDEO = "video"
        AUDIO = "audio"
        GEO_POINT = "geo_point"
        DATETIME = "datetime"
        DATE = "date"
        TIME = "time"

    primary_key = models.AutoField(primary_key=True, editable=False)
    flow = models.ForeignKey(Flow, models.CASCADE)
    id = models.CharField(max_length=255)
    type = models.CharField(max_length=11, choices=Type.choices)
    label = models.CharField(max_length=255)
    type_options = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [["flow_id", "id"]]

    def clean(self):
        if self.type == self.Type.SELECT_ONE:
            if "choices" not in self.type_options:
                raise ValidationError(
                    {"type_options": "'choices' is required for select_one type"}
                )
            if not isinstance(self.type_options["choices"], list):
                raise ValidationError({"type_options": "'choices' must be a list"})

        elif self.type == self.Type.SELECT_MANY:
            if "choices" not in self.type_options:
                raise ValidationError(
                    {"type_options": "'choices' is required for select_many type"}
                )
            if not isinstance(self.type_options["choices"], list):
                raise ValidationError({"type_options": "'choices' must be a list"})

        elif self.type == self.Type.NUMERIC:
            if "range" in self.type_options:
                if not isinstance(self.type_options["range"], list):
                    raise ValidationError({"type_options": "'range' must be a list"})
                if not all(isinstance(v, int) for v in self.type_options["range"]):
                    raise ValidationError(
                        {"type_options": "'range' can only contain integers"}
                    )
                if not len(self.type_options["range"]) == 2:
                    raise ValidationError(
                        {"type_options": "'range' must contain exactly 2 items"}
                    )
