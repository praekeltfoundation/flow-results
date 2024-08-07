from django.urls import include, path
from rest_framework_extensions.routers import ExtendedDefaultRouter

from flows.views import FlowResponseViewSet, FlowViewSet

v1router = ExtendedDefaultRouter()
flow_router = v1router.register("flow-results/packages", FlowViewSet, basename="flow")
flow_router.register(
    "responses",
    FlowResponseViewSet,
    basename="flowresponse",
    parents_query_lookups=["question__flow"],
)

urlpatterns = [
    path("api/v1/", include(v1router.urls)),
]
