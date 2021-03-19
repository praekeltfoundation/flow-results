from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db.transaction import atomic
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from flows.models import Flow, FlowQuestion
from flows.serializers import FlowSerializer


def flatten_errors(error):
    """
    Django's ValidationError contains nested ValidationErrors, which each have a list
    of errors, so we need to flatten them.
    """
    return {k: [item for items in v for item in items] for k, v in error.items()}


class FlowViewSet(viewsets.ViewSet):
    queryset = Flow.objects.all()

    @atomic
    def create(self, request):
        serializer = FlowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data["data"]["attributes"]
        flows = []
        for i, resource in enumerate(data["resources"]):
            flow = Flow(
                id=data["id"] or uuid4(),
                name=data["name"],
                version=data["flow-results-specification"],
                created=data["created"],
                modified=data["modified"],
                title=data["title"],
                language=resource["schema"]["language"],
            )
            try:
                flow.full_clean()
            except ValidationError as e:
                error = flatten_errors(e.error_dict)
                if "version" in error:
                    error["flow-results-specification"] = error.pop("version")
                if "language" in error:
                    error["resources"] = {
                        str(i): {"schema": {"language": error.pop("language")}}
                    }
                raise DRFValidationError({"data": {"attributes": error}})
            flow.save()

            question_errors = {}
            questions = []
            for question_id, question in resource["schema"]["questions"].items():
                question = FlowQuestion(
                    flow=flow,
                    id=question_id,
                    type=question["type"],
                    label=question["label"],
                    type_options=question["type_options"],
                )
                try:
                    question.full_clean()
                except ValidationError as e:
                    question_errors[question_id] = flatten_errors(e.error_dict)
                questions.append(question)
            if question_errors:
                raise DRFValidationError(
                    {
                        "data": {
                            "attributes": {
                                "resources": {
                                    str(i): {"schema": {"questions": question_errors}}
                                }
                            }
                        }
                    }
                )
            FlowQuestion.objects.bulk_create(questions)
            flows.append((flow, questions))
        return Response(
            {
                "data": {
                    "type": "packages",
                    "id": flow.id,
                    "attributes": {
                        "profile": "flow-results-package",
                        "name": flow.name,
                        "flow-results-specification": flow.version,
                        "created": flow.created.isoformat(),
                        "modified": flow.modified.isoformat(),
                        "id": flow.id,
                        "title": flow.title,
                        "resources": [
                            {
                                "path": None,
                                # TODO: Add results URL here, once we have results
                                "api-data-url": None,
                                "mediatype": "application/json",
                                "encoding": "utf-8",
                                "schema": {
                                    "language": flow.language,
                                    "fields": [
                                        {
                                            "name": "timestamp",
                                            "title": "Timestamp",
                                            "type": "datetime",
                                        },
                                        {
                                            "name": "row_id",
                                            "title": "Row ID",
                                            "type": "string",
                                        },
                                        {
                                            "name": "contact_id",
                                            "title": "Contact ID",
                                            "type": "string",
                                        },
                                        {
                                            "name": "session_id",
                                            "title": "Session ID",
                                            "type": "string",
                                        },
                                        {
                                            "name": "question_id",
                                            "title": "Question ID",
                                            "type": "string",
                                        },
                                        {
                                            "name": "response_id",
                                            "title": "Response ID",
                                            "type": "any",
                                        },
                                        {
                                            "name": "response_metadata",
                                            "title": "Response Metadata",
                                            "type": "object",
                                        },
                                    ],
                                    "questions": {
                                        question.id: {
                                            "type": question.type,
                                            "label": question.label,
                                            "type_options": question.type_options,
                                        }
                                        for question in questions
                                    },
                                },
                            }
                            for flow, questions in flows
                        ],
                    },
                    "links": {
                        # TODO: Link to flow detail once that view exists
                        "self": None
                    },
                }
            },
            status=status.HTTP_201_CREATED,
        )
