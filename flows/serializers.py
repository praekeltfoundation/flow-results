from uuid import uuid4

from django.utils import timezone
from rest_framework import serializers


class FlowSerializer(serializers.Serializer):
    class DataSerializer(serializers.Serializer):
        type = serializers.ChoiceField(["packages"])

        class AttributesSerializer(serializers.Serializer):
            profile = serializers.ChoiceField(["flow-results-package"])
            name = serializers.CharField(max_length=255, allow_blank=True, default="")
            flow_results_specification = serializers.CharField()
            created = serializers.DateTimeField(
                default=timezone.now(), default_timezone=timezone.utc
            )
            modified = serializers.DateTimeField(
                default=timezone.now(), default_timezone=timezone.utc
            )
            id = serializers.UUIDField(allow_null=True, default=uuid4)
            title = serializers.CharField(max_length=255, allow_blank=True, default="")

            class ResourcesSerializer(serializers.Serializer):
                mediatype = serializers.ChoiceField(["application/json"])
                encoding = serializers.ChoiceField(["utf-8"])

                class SchemaSerializer(serializers.Serializer):
                    language = serializers.CharField(
                        max_length=3, default="", allow_blank=True
                    )

                    class QuestionSerializer(serializers.Serializer):
                        type = serializers.CharField()
                        label = serializers.CharField(max_length=255)
                        type_options = serializers.DictField()

                    questions = serializers.DictField(child=QuestionSerializer())

                schema = SchemaSerializer()

            resources = serializers.ListField(child=ResourcesSerializer())

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.fields["flow-results-specification"] = self.fields.pop(
                    "flow_results_specification"
                )

        attributes = AttributesSerializer()

    data = DataSerializer()


class FlowResponsesSerializer(serializers.Serializer):
    class DataSerializer(serializers.Serializer):
        type = serializers.ChoiceField(["responses"])
        id = serializers.CharField()

        class AttributesSerializer(serializers.Serializer):
            responses = serializers.ListField(
                child=serializers.ListField(min_length=7, max_length=7)
            )

        attributes = AttributesSerializer()

    data = DataSerializer()
