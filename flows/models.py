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

    def _validate_choice_order(self, errors):
        choices = self.question.type_options["choices"]
        choice_order = self.response_metadata["choice_order"]
        if not isinstance(choice_order, list):
            errors["response_metadata"].append("choice_order must be an array")
        elif not all(choice in choice_order for choice in choices):
            errors["response_metadata"].append(
                f"choice_order {choice_order} contains choices not in {choices}"
            )

    def _validate_media(self, errors):
        if not isinstance(self.response, URL) and isinstance(self.response, str):
            self.response = URL(str)
        if not isinstance(self.response, URL):
            errors["response"].append("must be a URL")
        if "format" in self.response_metadata:
            if not isinstance(self.response_metadata["format"], str):
                errors["response_metadata"].append("format must be a string")
        if "dimensions" in self.response_metadata:
            dimensions = self.response_metadata["dimensions"]
            if not isinstance(dimensions, list):
                errors["response_metadata"].append("dimensions must be an array")
            else:
                if len(dimensions) != 2:
                    errors["response_metadata"].append(
                        "dimensions must have a length of 2"
                    )
                if not all(isinstance(item, int) for item in dimensions):
                    errors["response_metadata"].append(
                        "dimensions items must be integers"
                    )
        if "file_size_mb" in self.response_metadata:
            file_size_mb = self.response_metadata["file_size_mb"]
            if not isinstance(file_size_mb, int) and not isinstance(
                file_size_mb, float
            ):
                errors["response_metadata"].append(
                    "file_size_mb must be integer or float"
                )
        if "duration_s" in self.response_metadata:
            duration_s = self.response_metadata["duration_s"]
            if not isinstance(duration_s, int) and not isinstance(duration_s, float):
                errors["response_metadata"].append(
                    "duration_s must be integer or float"
                )
        if "language" in self.response_metadata:
            language = self.response_metadata["language"]
            if not isinstance(language, str):
                errors["response_metadata"].append("language must be a string")

    def clean(self):
        errors = defaultdict(list)
        type_ = self.question.type
        type_options = self.question.type_options

        if type_ == FlowQuestion.Type.OPEN:
            type_options = {}
            valid_types = {
                t.value for t in FlowQuestion.Type if t is not FlowQuestion.Type.OPEN
            }
            if "type" not in self.response_metadata:
                errors["response_metadata"].append("type is required")
            elif self.response_metadata["type"] not in valid_types:
                errors["response_metadata"].append(
                    f"type must be one of {sorted(valid_types)}"
                )
            else:
                type_ = self.response_metadata["type"]

            if "type_options" not in self.response_metadata:
                errors["response_metadata"].append("type_options is required")
            elif not isinstance(self.response_metadata["type_options"], dict):
                errors["response_metadata"].append("type_options must be an object")
            else:
                type_options = self.response_metadata["type_options"]

            FlowQuestion.validate_type_options(errors, type_, type_options)
            if errors:
                errors["response_metadata"].extend(
                    [f"type_options.{e}" for e in errors.pop("type_options", [])]
                )
                raise ValidationError(errors)

        if type_ == FlowQuestion.Type.SELECT_ONE:
            choices = type_options["choices"]
            if self.response not in choices:
                errors["response"].append(
                    f"{self.response} is not a valid choice. Valid choices are "
                    f"{choices}"
                )
            if "choice_order" in self.response_metadata:
                self._validate_choice_order(errors)
        elif type_ == FlowQuestion.Type.SELECT_MANY:
            choices = type_options["choices"]
            if not isinstance(self.response, list):
                errors["response"].append("must be an array")
            elif not all(r in choices for r in self.response):
                errors["response"].append(
                    f"{self.response} contains choices not in {choices}"
                )
            if "choice_order" in self.response_metadata:
                self._validate_choice_order(errors)
        elif type_ == FlowQuestion.Type.NUMERIC:
            if not isinstance(self.response, int) and not isinstance(
                self.response, float
            ):
                errors["response"].append("must be float or integer")
        elif type_ == FlowQuestion.Type.TEXT:
            if not isinstance(self.response, str):
                errors["response"].append("must be a string")
            if "language" in self.response_metadata:
                language = self.response_metadata["language"]
                if not isinstance(language, str):
                    errors["response_metadata"].append("language must be a string")
        elif type_ == FlowQuestion.Type.IMAGE:
            self._validate_media(errors)
        elif type_ == FlowQuestion.Type.VIDEO:
            self._validate_media(errors)
        elif type_ == FlowQuestion.Type.AUDIO:
            self._validate_media(errors)
        elif type_ == FlowQuestion.Type.GEO_POINT:
            if not isinstance(self.response, list):
                errors["response"].append("must be an array")
            else:
                if not all(isinstance(item, float) for item in self.response):
                    errors["response"].append("array may only contain floats")
                if len(self.response) < 2 or len(self.response) > 4:
                    errors["response"].append(
                        "number of array elements must be between 2 and 4 inclusive"
                    )
        elif type_ == FlowQuestion.Type.DATETIME:
            if isinstance(self.response, str):
                try:
                    self.response = datetime.fromisoformat(self.response)
                except ValueError:
                    pass
            if not isinstance(self.response, datetime):
                errors["response"].append("must be an RFC 3339 date-time")
        elif type_ == FlowQuestion.Type.DATE:
            if isinstance(self.response, str):
                try:
                    self.response = date.fromisoformat(self.response)
                except ValueError:
                    pass
            if not isinstance(self.response, date):
                errors["response"].append("must be an RFC 3339 date")
        elif type_ == FlowQuestion.Type.TIME:
            if isinstance(self.response, str):
                try:
                    self.response = time.fromisoformat(self.response)
                except ValueError:
                    pass
            if not isinstance(self.response, time):
                errors["response"].append("must be an RFC 3339 time")
        if errors:
            raise ValidationError(errors)
