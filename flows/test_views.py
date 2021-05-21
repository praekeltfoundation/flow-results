import json
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlencode
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.shortcuts import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from flows.models import Flow, FlowQuestion, FlowResponse
from flows.views import SCHEMA_FIELDS


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
                                            "type_options": ["choices must be an array"]
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
            json.dumps(
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
                                        "fields": SCHEMA_FIELDS,
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
                }
            ),
            content_type="application/vnd.api+json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        [flow] = Flow.objects.all()
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
                                "api-data-url": "http://testserver"
                                f"{reverse('flowresponse-list', args=[flow.id])}",
                                "mediatype": "application/json",
                                "encoding": "utf-8",
                                "schema": {
                                    "language": "eng",
                                    "fields": SCHEMA_FIELDS,
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
                    "links": {
                        "self": "http://testserver"
                        f"{reverse('flow-detail', args=[str(flow.id)])}"
                    },
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

    def test_detail_view(self):
        flow = Flow.objects.create(
            name="test-flow", title="Test Flow", version=Flow.Version.V1_0_0_RC1
        )
        flow.flowquestion_set.create(
            id="q1",
            label="Question 1",
            type=FlowQuestion.Type.SELECT_ONE,
            type_options={"choices": ["1", "2"]},
        )
        flow.flowquestion_set.create(
            id="q2", label="Question 2", type=FlowQuestion.Type.OPEN
        )
        url = reverse("flow-detail", args=[flow.id])
        # Count queries to ensure we're not doing n + 1 queries
        # 1: validate auth token
        # 2: validate user permissions
        # 3: validate user group permissions
        # 4: get flow by ID
        # 5: get all questions for flow
        with self.assertNumQueries(5):
            response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "links": {
                    "self": f"http://testserver{reverse('flow-detail', args=[flow.id])}"
                },
                "data": {
                    "id": str(flow.id),
                    "type": "packages",
                    "attributes": {
                        "id": str(flow.id),
                        "flow-results-specification": flow.version.value,
                        "name": flow.name,
                        "profile": "flow-results-package",
                        "created": flow.created.isoformat(),
                        "modified": flow.modified.isoformat(),
                        "title": flow.title,
                        "resources": [
                            {
                                "api-data-url": "http://testserver"
                                f"{reverse('flowresponse-list', args=[flow.id])}",
                                "encoding": "utf-8",
                                "mediatype": "application/json",
                                "path": None,
                                "schema": {
                                    "language": "",
                                    "fields": SCHEMA_FIELDS,
                                    "questions": {
                                        "q1": {
                                            "label": "Question 1",
                                            "type": FlowQuestion.Type.SELECT_ONE.value,
                                            "type_options": {"choices": ["1", "2"]},
                                        },
                                        "q2": {
                                            "label": "Question 2",
                                            "type": FlowQuestion.Type.OPEN.value,
                                            "type_options": {},
                                        },
                                    },
                                },
                            }
                        ],
                    },
                },
                "relationships": {
                    "responses": {
                        "links": {
                            "related": "http://testserver"
                            f"{reverse('flowresponse-list', args=[flow.id])}"
                        }
                    }
                },
            },
        )


class FlowResultViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("test")
        self.user.user_permissions.add(
            Permission.objects.get(codename="add_flowresponse")
        )
        self.user.user_permissions.add(
            Permission.objects.get(codename="view_flowresponse")
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        self.flow = Flow.objects.create()
        self.list_url = reverse("flowresponse-list", args=[self.flow.id])
        self.timestamp = datetime(2021, 2, 3, 4, 5, 6, 7, tzinfo=timezone.utc)

    def test_authentication(self):
        """
        You need to authenticate to gain access to the endpoint
        """
        self.client.credentials()
        response = self.client.post(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission(self):
        """
        You need permission to access the endpoint
        """
        self.user.user_permissions.remove(
            Permission.objects.get(codename="add_flowresponse")
        )
        self.user.user_permissions.remove(
            Permission.objects.get(codename="view_flowresponse")
        )
        response = self.client.post(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_serializer_error(self):
        """
        The serializer provides basic request validation, so if the request format is
        incorrect, an error should be returned
        """
        response = self.client.post(self.list_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"data": ["This field is required."]})

    def test_flow_missing_error(self):
        """
        Should return a 404 if we don't have a flow with the given ID
        """
        url = reverse("flowresponse-list", args=["invalid"])
        data = {
            "data": {
                "id": "invalid",
                "type": "responses",
                "attributes": {"responses": []},
            }
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url = reverse("flowresponse-list", args=[str(uuid4())])
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_question_not_exists(self):
        """
        If the body references a question that doesn't exist, then it should return an
        error
        """
        data = {
            "data": {
                "id": self.flow.id,
                "type": "responses",
                "attributes": {
                    "responses": [[self.timestamp.isoformat(), 1, 1, 1, 1, "test", {}]]
                },
            }
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "attributes": {
                        "responses": {
                            "0": {"question_id": ["Question with ID 1 not found"]}
                        }
                    }
                }
            },
        )

    def test_invalid_answer_for_question(self):
        """
        If the answer isn't valid for the question, an error should be returned
        """
        FlowQuestion.objects.create(
            flow=self.flow,
            id="1",
            type=FlowQuestion.Type.SELECT_ONE,
            label="q1",
            type_options={"choices": ["a", "b"]},
        )
        data = {
            "data": {
                "id": self.flow.id,
                "type": "responses",
                "attributes": {
                    "responses": [[self.timestamp.isoformat(), 1, 1, 1, "1", "c", {}]]
                },
            }
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "attributes": {
                        "responses": {
                            "0": {
                                "response": [
                                    "c is not a valid choice. Valid choices are "
                                    "['a', 'b']"
                                ]
                            }
                        }
                    }
                }
            },
        )

    def test_valid_answers(self):
        """
        If the answers are valid, should be stored
        """
        FlowQuestion.objects.create(
            flow=self.flow,
            id="1",
            type=FlowQuestion.Type.SELECT_ONE,
            label="q1",
            type_options={"choices": ["a", "b"]},
        )
        data = {
            "data": {
                "id": self.flow.id,
                "type": "responses",
                "attributes": {
                    "responses": [
                        [self.timestamp.isoformat(), i, 1, 1, "1", "a", {}]
                        for i in range(10)
                    ]
                },
            }
        }
        # Count queries to ensure we're not doing n + 1 queries
        # 1: validate auth token
        # 2: validate user permissions
        # 3: validate user group permissions
        # 4: get flow by ID
        # 5: get all questions for flow
        # 6: insert responses
        with self.assertNumQueries(6):
            response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_validate_row_id_uniqueness(self):
        """
        Each row id should be unique. We're testing this because we're telling django
        to ignore the row_id uniqueness checks, and have the database do it instead,
        to avoid the extra database call
        """
        FlowQuestion.objects.create(
            flow=self.flow,
            id="1",
            type=FlowQuestion.Type.SELECT_ONE,
            label="q1",
            type_options={"choices": ["a", "b"]},
        )
        data = {
            "data": {
                "id": self.flow.id,
                "type": "responses",
                "attributes": {
                    "responses": [[self.timestamp.isoformat(), 1, 1, 1, "1", "a", {}]]
                    * 2
                },
            }
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "attributes": {
                        "responses": ["row_id is not unique for flow question"]
                    }
                }
            },
        )

    def test_list_view_not_found(self):
        """
        If the give flow ID is not valid, should return a not found error
        """
        url = reverse("flowresponse-list", args=["invalid"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url = reverse("flowresponse-list", args=[str(uuid4())])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_view(self):
        question = FlowQuestion.objects.create(
            flow=self.flow,
            id="1",
            type=FlowQuestion.Type.SELECT_ONE,
            label="q1",
            type_options={"choices": ["a", "b"]},
        )
        for i in range(5):
            FlowResponse.objects.create(
                question=question,
                flow=self.flow,
                timestamp=self.timestamp,
                row_id=i,
                contact_id=1,
                session_id=1,
                response="a",
                response_metadata={},
            )
        # token, permission, group permission, flow, answers
        with self.assertNumQueries(5):
            response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "type": "flow-results-data",
                    "id": str(self.flow.id),
                    "attributes": {
                        "responses": [
                            ["2021-02-03T04:05:06.000007Z", i, 1, 1, "1", "a", {}]
                            for i in range(5)
                        ]
                    },
                    "relationships": {
                        "descriptor": {
                            "links": {"self": f"http://testserver{self.list_url}"}
                        },
                        "links": {
                            "self": f"http://testserver{self.list_url}",
                            "next": None,
                            "previous": None,
                        },
                    },
                }
            },
        )

    def test_list_view_filter(self):
        question = FlowQuestion.objects.create(
            flow=self.flow,
            id="1",
            type=FlowQuestion.Type.SELECT_ONE,
            label="q1",
            type_options={"choices": ["a", "b"]},
        )
        for i in range(5):
            FlowResponse.objects.create(
                question=question,
                flow=self.flow,
                timestamp=datetime(2021, 2, 3, 4, 5, i, tzinfo=timezone.utc),
                row_id=i,
                contact_id=1,
                session_id=1,
                response="a",
                response_metadata={},
            )
        querystring = urlencode(
            {
                "filter[start-timestamp]": datetime(
                    2021, 2, 3, 4, 5, 0, tzinfo=timezone.utc
                ).isoformat(),
                "filter[end-timestamp]": datetime(
                    2021, 2, 3, 4, 5, 3, tzinfo=timezone.utc
                ).isoformat(),
            }
        )
        # token, permission, group permission, flow, answers
        with self.assertNumQueries(5):
            response = self.client.get(f"{self.list_url}?{querystring}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["data"]["attributes"]["responses"]), 3)

        querystring = urlencode(
            {"filter[start-timestamp]": "invalid", "filter[end-timestamp]": "invalid"}
        )
        response = self.client.get(f"{self.list_url}?{querystring}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["data"]["attributes"]["responses"]), 5)

    def test_list_view_first_page(self):
        """
        First page should have a next page, but not a previous page
        """
        question = FlowQuestion.objects.create(
            flow=self.flow,
            id="1",
            type=FlowQuestion.Type.SELECT_ONE,
            label="q1",
            type_options={"choices": ["a", "b"]},
        )
        for i in range(5):
            FlowResponse.objects.create(
                question=question,
                flow=self.flow,
                timestamp=datetime(2021, 2, 3, 4, 5, i, tzinfo=timezone.utc),
                row_id=i,
                contact_id=1,
                session_id=1,
                response="a",
                response_metadata={},
            )
        querystring = urlencode({"page[size]": 2})
        # token, permission, group permission, flow, answers
        with self.assertNumQueries(5):
            response = self.client.get(f"{self.list_url}?{querystring}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["data"]["attributes"]["responses"]), 2)
        self.assertEqual(
            parse_qs(
                response.json()["data"]["relationships"]["links"]["next"].split("?")[1]
            ),
            {"page[afterCursor]": ["1"], "page[size]": ["2"]},
        )
        self.assertEqual(
            response.json()["data"]["relationships"]["links"]["previous"], None
        )

    def test_list_view_middle_page(self):
        """
        Middle page should have a next and previous page
        """
        question = FlowQuestion.objects.create(
            flow=self.flow,
            id="1",
            type=FlowQuestion.Type.SELECT_ONE,
            label="q1",
            type_options={"choices": ["a", "b"]},
        )
        for i in range(5):
            FlowResponse.objects.create(
                question=question,
                flow=self.flow,
                timestamp=datetime(2021, 2, 3, 4, 5, i, tzinfo=timezone.utc),
                row_id=i,
                contact_id=1,
                session_id=1,
                response="a",
                response_metadata={},
            )
        querystring = urlencode({"page[size]": 2, "page[afterCursor]": 1})
        # token, permission, group permission, flow, pagination answer, answers
        with self.assertNumQueries(6):
            response = self.client.get(f"{self.list_url}?{querystring}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["data"]["attributes"]["responses"]), 2)
        self.assertEqual(
            parse_qs(
                response.json()["data"]["relationships"]["links"]["next"].split("?")[1]
            ),
            {"page[afterCursor]": ["3"], "page[size]": ["2"]},
        )
        self.assertEqual(
            parse_qs(
                response.json()["data"]["relationships"]["links"]["previous"].split(
                    "?"
                )[1]
            ),
            {"page[beforeCursor]": ["2"], "page[size]": ["2"]},
        )

    def test_list_view_last_page(self):
        """
        Last page should have previous page, but no next
        """
        question = FlowQuestion.objects.create(
            flow=self.flow,
            id="1",
            type=FlowQuestion.Type.SELECT_ONE,
            label="q1",
            type_options={"choices": ["a", "b"]},
        )
        for i in range(5):
            FlowResponse.objects.create(
                question=question,
                flow=self.flow,
                timestamp=datetime(2021, 2, 3, 4, 5, i, tzinfo=timezone.utc),
                row_id=f"a{i}",
                contact_id=1,
                session_id=1,
                response="a",
                response_metadata={},
            )
        querystring = urlencode({"page[size]": 2, "page[afterCursor]": "a3"})
        # token, permission, group permission, flow, pagination answer, answers
        with self.assertNumQueries(6):
            response = self.client.get(f"{self.list_url}?{querystring}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["data"]["attributes"]["responses"]), 1)
        self.assertEqual(
            response.json()["data"]["relationships"]["links"]["next"], None
        )
        self.assertEqual(
            parse_qs(
                response.json()["data"]["relationships"]["links"]["previous"].split(
                    "?"
                )[1]
            ),
            {"page[beforeCursor]": ["a4"], "page[size]": ["2"]},
        )

    def test_list_view_before_cursor(self):
        """
        We should also be able to paginate backwards
        """
        question = FlowQuestion.objects.create(
            flow=self.flow,
            id="1",
            type=FlowQuestion.Type.SELECT_ONE,
            label="q1",
            type_options={"choices": ["a", "b"]},
        )
        for i in range(5):
            FlowResponse.objects.create(
                question=question,
                flow=self.flow,
                timestamp=datetime(2021, 2, 3, 4, 5, i, tzinfo=timezone.utc),
                row_id=f"a{i}",
                contact_id=1,
                session_id=1,
                response="a",
                response_metadata={},
            )
        querystring = urlencode({"page[size]": 2, "page[beforeCursor]": "a4"})
        # token, permission, group permission, flow, pagination answer, answers
        with self.assertNumQueries(6):
            response = self.client.get(f"{self.list_url}?{querystring}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["data"]["attributes"]["responses"]), 2)
        self.assertEqual(
            parse_qs(
                response.json()["data"]["relationships"]["links"]["next"].split("?")[1]
            ),
            {"page[afterCursor]": ["a3"], "page[size]": ["2"]},
        )
        self.assertEqual(
            parse_qs(
                response.json()["data"]["relationships"]["links"]["previous"].split(
                    "?"
                )[1]
            ),
            {"page[beforeCursor]": ["a2"], "page[size]": ["2"]},
        )
