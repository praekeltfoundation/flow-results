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
            e.exception.message_dict, {"type_options": ["choices must be an array"]}
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
            e.exception.message_dict, {"type_options": ["choices must be an array"]}
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
            e.exception.message_dict, {"type_options": ["range must be an array"]}
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
    def create_response(self):
        flow = Flow.objects.create()
        question = FlowQuestion.objects.create(flow=flow)
        return FlowResponse(
            question=question,
            flow=flow,
            session_id=1,
            row_id=1,
            contact_id=1,
            response="",
            response_metadata={},
        )

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
            flow=question.flow,
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
            flow=question.flow,
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
            flow=question.flow,
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
        response can be any of the types, and should serialise and deserialise properly
        """
        cases = (
            ("string", FlowResponse.Type.STRING, "string"),
            (7, FlowResponse.Type.INTEGER, 7),
            (["a", "b", "c"], FlowResponse.Type.ARRAY_OF_STRING, ["a", "b", "c"]),
            (1.5, FlowResponse.Type.FLOAT, 1.5),
            (URL("https://example.org"), FlowResponse.Type.URL, "https://example.org"),
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

    def test_select_one_answer(self):
        """
        For answers to select_one must be a valid choice, and if choice_order is
        present, it must be valid
        """
        response = self.create_response()
        response.question.type = FlowQuestion.Type.SELECT_ONE
        response.question.type_options["choices"] = ["a", "b", "c"]
        response.response = "d"
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {
                "response": [
                    "d is not a valid choice. Valid choices are ['a', 'b', 'c']"
                ]
            },
        )

        response.response = "a"
        response.full_clean()

        response.response_metadata["choice_order"] = "invalid"
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {"response_metadata": ["choice_order must be an array"]},
        )
        response.response_metadata["choice_order"] = ["c", "d"]
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {
                "response_metadata": [
                    "choice_order ['c', 'd'] contains choices not in ['a', 'b', 'c']"
                ]
            },
        )

        response.response_metadata["choice_order"] = ["c", "b", "a"]
        response.full_clean()

    def test_select_many(self):
        """
        answer must be an array of valid choices
        """
        response = self.create_response()
        response.question.type = FlowQuestion.Type.SELECT_MANY
        response.question.type_options["choices"] = ["a", "b", "c"]

        response.response = "a"
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(e.exception.message_dict, {"response": ["must be an array"]})

        response.response = ["d"]
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {"response": ["['d'] contains choices not in ['a', 'b', 'c']"]},
        )

        response.response = ["b", "a"]
        response.full_clean()

        response.response_metadata["choice_order"] = "invalid"
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {"response_metadata": ["choice_order must be an array"]},
        )

    def test_numeric(self):
        """
        Numeric questions can be answered with an integer or float
        """
        response = self.create_response()
        response.question.type = FlowQuestion.Type.NUMERIC

        response.response = "a"
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict, {"response": ["must be float or integer"]}
        )

        response.response = 1
        response.full_clean()

        response.response = 1.1
        response.full_clean()

    def test_text(self):
        """
        Text answers must be a string, with an optional language metadata
        """
        response = self.create_response()
        response.question.type = FlowQuestion.Type.TEXT

        response.response = 1
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(e.exception.message_dict, {"response": ["must be a string"]})

        response.response = "answer"
        response.full_clean()

        response.response_metadata["language"] = 7
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {"response_metadata": ["language must be a string"]},
        )

        response.response_metadata["language"] = "eng"
        response.full_clean()

    def test_image(self):
        """
        Image answers are URLs, with optional format, dimensions, and file_size_mb
        metadata
        """
        response = self.create_response()
        response.question.type = FlowQuestion.Type.IMAGE

        response.response = 1
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(e.exception.message_dict, {"response": ["must be a URL"]})

        response.response = "https://example.org"
        response.full_clean()

        response.response_metadata["format"] = 7
        response.response_metadata["dimensions"] = "invalid"
        response.response_metadata["file_size_mb"] = "invalid"
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {
                "response_metadata": [
                    "format must be a string",
                    "dimensions must be an array",
                    "file_size_mb must be integer or float",
                ]
            },
        )

        response.response_metadata["format"] = "image/png"
        response.response_metadata["dimensions"] = ["a", "b", "c"]
        response.response_metadata["file_size_mb"] = 3
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {
                "response_metadata": [
                    "dimensions must have a length of 2",
                    "dimensions items must be integers",
                ]
            },
        )

        response.response_metadata["dimensions"] = [640, 480]
        response.response_metadata["file_size_mb"] = 3.7
        response.full_clean()

    def test_video(self):
        """
        Video answers are URLs, with optional format, language, dimensions,
        file_size_mb, and duration_s metadata
        """
        response = self.create_response()
        response.question.type = FlowQuestion.Type.VIDEO

        response.response = "https://example.org"
        response.response_metadata["format"] = "video/mp4"
        response.response_metadata["dimensions"] = [1920, 1080]
        response.response_metadata["file_size_mb"] = 243
        response.response_metadata["language"] = 7
        response.response_metadata["duration_s"] = "7"
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {
                "response_metadata": [
                    "duration_s must be integer or float",
                    "language must be a string",
                ]
            },
        )
        response.response_metadata["language"] = "eng"
        response.response_metadata["duration_s"] = 7
        response.full_clean()

    def test_audio(self):
        """
        Video answers are URLs, with optional format, language, file_size_mb, and
        duration_s metadata
        """
        response = self.create_response()
        response.question.type = FlowQuestion.Type.AUDIO

        response.response = "https://example.org"
        response.response_metadata["format"] = "audio/mp3"
        response.response_metadata["language"] = "eng"
        response.response_metadata["file_size_mb"] = 12.5
        response.response_metadata["duration_s"] = 7.2
        response.full_clean()

    def test_geo_point(self):
        """
        geo_point answers are an array of floats
        """
        response = self.create_response()
        response.question.type = FlowQuestion.Type.GEO_POINT

        response.response = "invalid"
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(e.exception.message_dict, {"response": ["must be an array"]})

        response.response = ["a"]
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {
                "response": [
                    "array may only contain floats",
                    "number of array elements must be between 2 and 4 inclusive",
                ]
            },
        )

        response.response = [12.34, -12.34]
        response.full_clean()

    def test_datetime(self):
        """
        datetime answers are an RFC 3339 date-time string
        """
        response = self.create_response()
        response.question.type = FlowQuestion.Type.DATETIME

        response.response = "2021-02-29T03:04:05.123456+00:00"
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict, {"response": ["must be an RFC 3339 date-time"]}
        )

        response.response = "2021-02-03T04:05:06.123456+00:00"
        response.full_clean()

    def test_date(self):
        """
        date answers are an RFC 3339 date string
        """
        response = self.create_response()
        response.question.type = FlowQuestion.Type.DATE

        response.response = "2021-02-29"
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict, {"response": ["must be an RFC 3339 date"]}
        )

        response.response = "2021-02-03"
        response.full_clean()

    def test_time(self):
        """
        time answers are an RFC 3339 time string
        """
        response = self.create_response()
        response.question.type = FlowQuestion.Type.TIME

        response.response = "25:26"
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict, {"response": ["must be an RFC 3339 time"]}
        )

        response.response = "04:05"
        response.full_clean()

    def test_open(self):
        """
        open question answers first get their type and type_options metadata validated,
        then they're treated as whatever type is specified
        """
        response = self.create_response()
        response.question.type = FlowQuestion.Type.OPEN

        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {"response_metadata": ["type is required", "type_options is required"]},
        )

        response.response_metadata["type"] = "invalid"
        response.response_metadata["type_options"] = "invalid"
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {
                "response_metadata": [
                    "type must be one of ['audio', 'date', 'datetime', 'geo_point', "
                    "'image', 'numeric', 'select_many', 'select_one', 'text', 'time', "
                    "'video']",
                    "type_options must be an object",
                ]
            },
        )

        response.response_metadata["type"] = FlowQuestion.Type.SELECT_ONE
        response.response_metadata["type_options"] = {}
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {
                "response_metadata": [
                    "type_options.choices is required for select_one type"
                ]
            },
        )

        response.response_metadata["type"] = FlowQuestion.Type.SELECT_ONE
        response.response_metadata["type_options"] = {"choices": ["a", "b"]}
        response.response = "invalid"
        with self.assertRaises(ValidationError) as e:
            response.full_clean()
        self.assertEqual(
            e.exception.message_dict,
            {
                "response": [
                    "invalid is not a valid choice. Valid choices are ['a', 'b']"
                ]
            },
        )

        response.response = "a"
        response.full_clean()
