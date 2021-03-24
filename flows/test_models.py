from datetime import date, datetime, time, timezone

from django.core.exceptions import ValidationError
from django.test import TestCase

from flows.models import Flow, FlowQuestion, FlowResponse
from flows.types import URL


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
            {"type_options": ["choices is required for select_one type"]},
        )

        q.type_options["choices"] = "choice"

        with self.assertRaises(ValidationError) as e:
            q.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {"type_options": ["choices must be an array"]},
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
            {"type_options": ["choices is required for select_many type"]},
        )

        q.type_options["choices"] = "choice"

        with self.assertRaises(ValidationError) as e:
            q.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {"type_options": ["choices must be an array"]},
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
            {"type_options": ["range must be an array"]},
        )

        q.type_options["range"] = []
        with self.assertRaises(ValidationError) as e:
            q.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {"type_options": ["range must contain exactly 2 items"]},
        )
        q.type_options["range"] = ["a", "b"]

        with self.assertRaises(ValidationError) as e:
            q.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {"type_options": ["range can only contain integers"]},
        )

        q.type_options["range"] = [5, 10]
        q.full_clean()


class FlowResponseTests(TestCase):
    def test_row_id(self):
        """
        row_id should be either an int or a string
        """
        response = FlowResponse(row_id=1)
        self.assertEqual(response.row_id_type, FlowResponse.Type.INTEGER)
        self.assertEqual(response.row_id_value, 1)
        self.assertIsInstance(response.row_id, int)
        response = FlowResponse(row_id="1")
        self.assertEqual(response.row_id_type, FlowResponse.Type.STRING)
        self.assertEqual(response.row_id_value, "1")
        self.assertIsInstance(response.row_id, str)

        question = FlowQuestion.objects.create(flow=Flow.objects.create())
        response = FlowResponse(
            question=question,
            row_id=["1"],
            contact_id=1,
            session_id=1,
            response="test",
            response_metadata={},
        )
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict, {"row_id_type": ["must be string or integer"]}
        )

    def test_contact_id(self):
        """
        contact_id should be either an int or a string
        """
        response = FlowResponse(contact_id=1)
        self.assertEqual(response.contact_id_type, FlowResponse.Type.INTEGER)
        self.assertEqual(response.contact_id_value, 1)
        self.assertIsInstance(response.contact_id, int)
        response = FlowResponse(contact_id="1")
        self.assertEqual(response.contact_id_type, FlowResponse.Type.STRING)
        self.assertEqual(response.contact_id_value, "1")
        self.assertIsInstance(response.contact_id, str)

        question = FlowQuestion.objects.create(flow=Flow.objects.create())
        response = FlowResponse(
            question=question,
            contact_id=["1"],
            row_id=1,
            session_id=1,
            response="test",
            response_metadata={},
        )
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict, {"contact_id_type": ["must be string or integer"]}
        )

    def test_session_id(self):
        """
        session_id should be either an int or a string
        """
        response = FlowResponse(session_id=1)
        self.assertEqual(response.session_id_type, FlowResponse.Type.INTEGER)
        self.assertEqual(response.session_id_value, 1)
        self.assertIsInstance(response.session_id, int)
        response = FlowResponse(session_id="1")
        self.assertEqual(response.session_id_type, FlowResponse.Type.STRING)
        self.assertEqual(response.session_id_value, "1")
        self.assertIsInstance(response.session_id, str)

        question = FlowQuestion.objects.create(flow=Flow.objects.create())
        response = FlowResponse(
            question=question,
            session_id=["1"],
            row_id=1,
            contact_id=1,
            response="test",
            response_metadata={},
        )
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict, {"session_id_type": ["must be string or integer"]}
        )

    def test_response(self):
        """
        response can be any of the types, and should serialise and deserialise proeprly
        """
        cases = (
            ("string", FlowResponse.Type.STRING, "string"),
            (7, FlowResponse.Type.INTEGER, 7),
            (["a", "b", "c"], FlowResponse.Type.ARRAY_OF_STRING, ["a", "b", "c"]),
            (1.5, FlowResponse.Type.FLOAT, 1.5),
            (
                URL("https://example.org"),
                FlowResponse.Type.URL,
                URL("https://example.org"),
            ),
            ([1.1, 2.2, 3.3], FlowResponse.Type.ARRAY_OF_FLOAT, [1.1, 2.2, 3.3]),
            (
                datetime(2021, 2, 3, 4, 5, 6, tzinfo=timezone.utc),
                FlowResponse.Type.DATETIME,
                datetime(2021, 2, 3, 4, 5, 6, tzinfo=timezone.utc).isoformat(),
            ),
            (date(2021, 2, 3), FlowResponse.Type.DATE, date(2021, 2, 3).isoformat()),
            (time(4, 5, 6), FlowResponse.Type.TIME, time(4, 5, 6).isoformat()),
        )
        for value, flowtype, serialised in cases:
            response = FlowResponse(response=value)
            self.assertEqual(response.response_type, flowtype)
            self.assertEqual(response.response_value, serialised)
            self.assertEqual(response.response, value)
