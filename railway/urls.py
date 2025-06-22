from django.urls import path, include
from rest_framework import routers
router = routers.DefaultRouter()
# router.register("", "Name"ViewSet)

urlpatterns = [path("", include(router.urls))]

app_name = "railway"
