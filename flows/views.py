from django.core.exceptions import ValidationError
from django.db.transaction import atomic
from rest_framework import viewsets
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
        for i, resource in enumerate(data["resources"]):
            flow = Flow(
                id=data["id"],
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
        return Response({})
