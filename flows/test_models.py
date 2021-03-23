from django.core.exceptions import ValidationError
from django.test import TestCase

from flows.models import Flow, FlowQuestion


class FlowTests(TestCase):
    def test_name_validation(self):
        """
        `name` should only be lowercase alphanumeric, with '.', '-', and '_'
        """
        f = Flow(version=Flow.Version.V1_0_0_RC1, name="TestInvalid")
        with self.assertRaises(ValidationError) as e:
            f.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {
                "name": [
                    "can only contain lowercase, alphanumeric characters and "
                    "'-', '_', '.'"
                ]
            },
        )

        f.name = "valid_name-1.0"
        f.full_clean()


class FlowQuestionTests(TestCase):
    def test_clean_select_one(self):
        """
        'choices' is a required option, and it must be a list
        """
        flow = Flow.objects.create()
        q = FlowQuestion(
            flow=flow, type=FlowQuestion.Type.SELECT_ONE, id="test", label="test"
        )

        with self.assertRaises(ValidationError) as e:
            q.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {"type_options": ["'choices' is required for select_one type"]},
        )

        q.type_options["choices"] = "choice"

        with self.assertRaises(ValidationError) as e:
            q.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {"type_options": ["'choices' must be a list"]},
        )

    def test_clean_select_many(self):
        """
        'choices' is a required option, and it must be a list
        """
        flow = Flow.objects.create()
        q = FlowQuestion(
            flow=flow, type=FlowQuestion.Type.SELECT_MANY, id="test", label="test"
        )

        with self.assertRaises(ValidationError) as e:
            q.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {"type_options": ["'choices' is required for select_many type"]},
        )

        q.type_options["choices"] = "choice"

        with self.assertRaises(ValidationError) as e:
            q.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {"type_options": ["'choices' must be a list"]},
        )

        q.type_options["choices"] = ["choice1", "choice2"]
        q.full_clean()

    def test_clean_numeric(self):
        """
        `range` is optional, but is specified, must be a list with two integers
        """
        flow = Flow.objects.create()
        q = FlowQuestion(
            flow=flow, type=FlowQuestion.Type.NUMERIC, id="test", label="test"
        )
        q.full_clean()

        q.type_options["range"] = "test"
        with self.assertRaises(ValidationError) as e:
            q.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {"type_options": ["'range' must be a list"]},
        )

        q.type_options["range"] = []
        with self.assertRaises(ValidationError) as e:
            q.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {"type_options": ["'range' must contain exactly 2 items"]},
        )
        q.type_options["range"] = ["a", "b"]

        with self.assertRaises(ValidationError) as e:
            q.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {"type_options": ["'range' can only contain integers"]},
        )

        q.type_options["range"] = [5, 10]
        q.full_clean()
