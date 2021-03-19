from django.urls import include, path
from rest_framework.routers import DefaultRouter

from flows.views import FlowViewSet

v1router = DefaultRouter()
v1router.register("flow-results/packages", FlowViewSet, basename="flow")

urlpatterns = [
    path("api/v1/", include(v1router.urls)),
]
