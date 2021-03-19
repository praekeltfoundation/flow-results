from django.contrib.auth.models import Permission, User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from flows.models import Flow, FlowQuestion


class FlowViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("test")
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
