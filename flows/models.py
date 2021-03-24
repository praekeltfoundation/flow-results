from collections import defaultdict
from datetime import date, datetime, time
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinLengthValidator, RegexValidator
from django.db import models
from django.utils import timezone

from flows.types import URL


class Flow(models.Model):
    class Version(models.TextChoices):
        V1_0_0_RC1 = "1.0.0-rc1"

    primary_key = models.AutoField(primary_key=True, editable=False)
    id = models.UUIDField(default=uuid4, unique=True)
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
    created = models.DateTimeField(default=timezone.now)
    modified = models.DateTimeField(default=timezone.now)
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

    @staticmethod
    def validate_type_options(errors, type_, type_options):
        if type_ == FlowQuestion.Type.SELECT_ONE:
            if "choices" not in type_options:
                errors["type_options"].append("choices is required for select_one type")
            elif not isinstance(type_options["choices"], list):
                errors["type_options"].append("choices must be an array")

        elif type_ == FlowQuestion.Type.SELECT_MANY:
            if "choices" not in type_options:
                errors["type_options"].append(
                    "choices is required for select_many type"
                )
            elif not isinstance(type_options["choices"], list):
                errors["type_options"].append("choices must be an array")

        elif type_ == FlowQuestion.Type.NUMERIC:
            if "range" in type_options:
                if not isinstance(type_options["range"], list):
                    errors["type_options"].append("range must be an array")
                elif not all(isinstance(v, int) for v in type_options["range"]):
                    errors["type_options"].append("range can only contain integers")
                elif not len(type_options["range"]) == 2:
                    errors["type_options"].append("range must contain exactly 2 items")

    def clean(self):
        errors = defaultdict(list)
        self.validate_type_options(errors, self.type, self.type_options)
        if errors:
            raise ValidationError(errors)


class FlowResponse(models.Model):
    # Some of the fields can have multiple types, so we use a JSON field to maintain the
    # type. But there are some types that JSON doesn't support, like datetime, so we
    # also maintain a type field, so that we know how to deserialize the value
    class Type(models.IntegerChoices):
        STRING = 0
        INTEGER = 1
        ARRAY_OF_STRING = 2
        FLOAT = 3
        URL = 4
        ARRAY_OF_FLOAT = 5
        DATETIME = 6
        DATE = 7
        TIME = 8

    question = models.ForeignKey(FlowQuestion, models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    row_id_type = models.PositiveSmallIntegerField(
        choices=Type.choices,
        validators=[MaxValueValidator(Type.INTEGER, "must be string or integer")],
    )
    row_id_value = models.JSONField()
    contact_id_type = models.PositiveSmallIntegerField(
        choices=Type.choices,
        validators=[MaxValueValidator(Type.INTEGER, "must be string or integer")],
    )
    contact_id_value = models.JSONField()
    session_id_type = models.PositiveSmallIntegerField(
        choices=Type.choices,
        validators=[MaxValueValidator(Type.INTEGER, "must be string or integer")],
    )
    session_id_value = models.JSONField()
    response_type = models.PositiveSmallIntegerField(choices=Type.choices)
    response_value = models.JSONField(blank=True)
    response_metadata = models.JSONField(blank=True)

    class Meta:
        unique_together = [["question_id", "row_id_value"]]
        indexes = [models.Index(fields=["row_id_value"])]

    @staticmethod
    def _deserialize(type_, value):
        if type_ == FlowResponse.Type.URL:
            return URL(value)
        elif type_ == FlowResponse.Type.DATETIME:
            return datetime.fromisoformat(value)
        elif type_ == FlowResponse.Type.DATE:
            return date.fromisoformat(value)
        elif type_ == FlowResponse.Type.TIME:
            return time.fromisoformat(value)
        return value

    @staticmethod
    def _get_type(value):
        if isinstance(value, URL):
            # Since URLs are just strings, check it before string
            return FlowResponse.Type.URL
        elif isinstance(value, str):
            return FlowResponse.Type.STRING
        elif isinstance(value, int):
            return FlowResponse.Type.INTEGER
        elif isinstance(value, float):
            return FlowResponse.Type.FLOAT
        elif isinstance(value, datetime):
            return FlowResponse.Type.DATETIME
        elif isinstance(value, date):
            return FlowResponse.Type.DATE
        elif isinstance(value, time):
            return FlowResponse.Type.TIME
        elif isinstance(value, list):
            if all(isinstance(item, str) for item in value):
                return FlowResponse.Type.ARRAY_OF_STRING
            elif all(isinstance(item, float) for item in value):
                return FlowResponse.Type.ARRAY_OF_FLOAT

    @staticmethod
    def _serialize(value):
        type_ = FlowResponse._get_type(value)
        if type_ in (
            FlowResponse.Type.DATETIME,
            FlowResponse.Type.DATE,
            FlowResponse.Type.TIME,
        ):
            return type_, value.isoformat()
        return type_, value

    @property
    def row_id(self):
        return self._deserialize(self.row_id_type, self.row_id_value)

    @row_id.setter
    def row_id(self, value):
        self.row_id_type, self.row_id_value = self._serialize(value)

    @property
    def contact_id(self):
        return self._deserialize(self.contact_id_type, self.contact_id_value)

    @contact_id.setter
    def contact_id(self, value):
        self.contact_id_type, self.contact_id_value = self._serialize(value)

    @property
    def session_id(self):
        return self._deserialize(self.session_id_type, self.session_id_value)

    @session_id.setter
    def session_id(self, value):
        self.session_id_type, self.session_id_value = self._serialize(value)

    @property
    def response(self):
        return self._deserialize(self.response_type, self.response_value)

    @response.setter
    def response(self, value):
        self.response_type, self.response_value = self._serialize(value)
