from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from flows.models import Flow, FlowQuestion


class FlowViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("test")
        self.user.user_permissions.add(Permission.objects.get(codename="view_flow"))
        self.user.user_permissions.add(Permission.objects.get(codename="add_flow"))
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)

    def test_authentication(self):
        """
        You need to authenticate to gain access to the endpoint
        """
        self.client.credentials()
        url = reverse("flow-list")
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission(self):
        """
        You need permission to access the endpoint
        """
        self.user.user_permissions.remove(Permission.objects.get(codename="add_flow"))
        self.user.user_permissions.remove(Permission.objects.get(codename="view_flow"))
        url = reverse("flow-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_serializer_error(self):
        """
        The serializer has been kept simple, only validating that required fields are
        there. It should return errors on invalid requests.
        """
        url = reverse("flow-list")
        data = {
            "data": {
                "type": "not-packages",
                "attributes": {
                    "profile": "not-flow-results-package",
                    "resources": [
                        {"mediatype": "application/josn", "encoding": "latin1"}
                    ],
                },
            }
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "type": ['"not-packages" is not a valid choice.'],
                    "attributes": {
                        "profile": [
                            '"not-flow-results-package" is not a valid choice.'
                        ],
                        "flow-results-specification": ["This field is required."],
                        "resources": {
                            "0": {
                                "encoding": ['"latin1" is not a valid choice.'],
                                "mediatype": [
                                    '"application/josn" is not a valid choice.'
                                ],
                                "schema": ["This field is required."],
                            }
                        },
                    },
                }
            },
        )

    def test_flow_model_error(self):
        """
        If the serializer passes, but the Flow model validation fails, then an error
        should be returned, and nothing should be saved.
        """
        url = reverse("flow-list")
        data = {
            "data": {
                "type": "packages",
                "attributes": {
                    "profile": "flow-results-package",
                    "name": "InvalidName",
                    "flow-results-specification": "other-version",
                    "resources": [
                        {
                            "mediatype": "application/json",
                            "encoding": "utf-8",
                            "schema": {"language": "en", "questions": {}},
                        }
                    ],
                },
            }
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "attributes": {
                        "flow-results-specification": [
                            "Value 'other-version' is not a valid choice."
                        ],
                        "name": [
                            "can only contain lowercase, alphanumeric characters and "
                            "'-', '_', '.'"
                        ],
                        "resources": {
                            "0": {
                                "schema": {
                                    "language": [
                                        "Ensure this value has at least 3 characters "
                                        "(it has 2)."
                                    ]
                                }
                            }
                        },
                    }
                }
            },
        )
        self.assertEqual(Flow.objects.count(), 0)
        self.assertEqual(FlowQuestion.objects.count(), 0)

    def test_flow_question_model_error(self):
        """
        If the serializer passes, but the FlowQuestion model validation fails, then an
        error should be returned, and nothing should be saved.
        """
        url = reverse("flow-list")
        data = {
            "data": {
                "type": "packages",
                "attributes": {
                    "profile": "flow-results-package",
                    "name": "valid-name",
                    "flow-results-specification": Flow.Version.V1_0_0_RC1,
                    "resources": [
                        {
                            "mediatype": "application/json",
                            "encoding": "utf-8",
                            "schema": {
                                "language": "eng",
                                "questions": {
                                    "test-id": {
                                        "type": FlowQuestion.Type.SELECT_ONE,
                                        "label": "Test label",
                                        "type_options": {"choices": "invalid"},
                                    }
                                },
                            },
                        }
                    ],
                },
            }
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "attributes": {
                        "resources": {
                            "0": {
                                "schema": {
                                    "questions": {
                                        "test-id": {
                                            "type_options": ["'choices' must be a list"]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
        )

        self.assertEqual(Flow.objects.count(), 0)
        self.assertEqual(FlowQuestion.objects.count(), 0)

    def test_success(self):
        """
        Uses the example in the docs to test that the endpoint works correctly
        """
        url = reverse("flow-list")
        response = self.client.post(
            url,
            {
                "data": {
                    "type": "packages",
                    "attributes": {
                        "profile": "flow-results-package",
                        "name": "standard_test_survey",
                        "flow-results-specification": "1.0.0-rc1",
                        "created": "2015-11-26 02:59:24+00:00",
                        "modified": "2017-12-04 15:54:44+00:00",
                        "id": None,
                        "title": "Standard Test Survey",
                        "resources": [
                            {
                                "path": None,
                                "api-data-url": None,
                                "mediatype": "application/json",
                                "encoding": "utf-8",
                                "schema": {
                                    "language": "eng",
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
                                        "1448506769745_42": {
                                            "type": "select_one",
                                            "label": "Are you a woman or a man?",
                                            "type_options": {
                                                "choices": ["Woman", "Man", "Other"]
                                            },
                                        },
                                        "1448506773018_89": {
                                            "type": "numeric",
                                            "label": "How old are you? "
                                            "Please enter your age in years.",
                                            "type_options": {"range": [-99, 99]},
                                        },
                                        "1448506774930_30": {
                                            "type": "open",
                                            "label": "What was the best thing that "
                                            "happened to you today?",
                                            "type_options": {},
                                        },
                                    },
                                },
                            }
                        ],
                    },
                }
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        [flow] = Flow.objects.all()
        self.maxDiff = None
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "type": "packages",
                    "id": str(flow.id),
                    "attributes": {
                        "profile": "flow-results-package",
                        "name": "standard_test_survey",
                        "flow-results-specification": "1.0.0-rc1",
                        "created": "2015-11-26T02:59:24+00:00",
                        "modified": "2017-12-04T15:54:44+00:00",
                        "id": str(flow.id),
                        "title": "Standard Test Survey",
                        "resources": [
                            {
                                "path": None,
                                "api-data-url": None,
                                "mediatype": "application/json",
                                "encoding": "utf-8",
                                "schema": {
                                    "language": "eng",
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
                                        "1448506769745_42": {
                                            "type": "select_one",
                                            "label": "Are you a woman or a man?",
                                            "type_options": {
                                                "choices": ["Woman", "Man", "Other"]
                                            },
                                        },
                                        "1448506773018_89": {
                                            "type": "numeric",
                                            "label": "How old are you? Please enter "
                                            "your age in years.",
                                            "type_options": {"range": [-99, 99]},
                                        },
                                        "1448506774930_30": {
                                            "type": "open",
                                            "label": "What was the best thing that "
                                            "happened to you today?",
                                            "type_options": {},
                                        },
                                    },
                                },
                            }
                        ],
                    },
                    "links": {"self": None},
                }
            },
        )

    def test_list_view_rendering(self):
        flow = Flow.objects.create(name="test-flow", title="Test Flow")
        url = reverse("flow-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "links": {
                    "next": None,
                    "previous": None,
                    "self": "http://testserver/api/v1/flow-results/packages/",
                },
                "data": [
                    {
                        "id": str(flow.id),
                        "type": "packages",
                        "attributes": {
                            "created": flow.created.isoformat(),
                            "modified": flow.modified.isoformat(),
                            "name": "test-flow",
                            "title": "Test Flow",
                        },
                    }
                ],
            },
        )

    def test_list_view_pagination(self):
        for _ in range(settings.REST_FRAMEWORK["PAGE_SIZE"] + 1):
            Flow.objects.create(name="test-flow", title="Test Flow")
        url = reverse("flow-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["data"]), 100)
        self.assertTrue("?cursor=" in response.json()["links"]["next"])

        response = self.client.get(response.json()["links"]["next"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["data"]), 1)
        self.assertTrue("?cursor=" in response.json()["links"]["previous"])
