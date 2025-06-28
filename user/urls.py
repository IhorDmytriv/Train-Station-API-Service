from django.urls import path, include

from user.views import CreateUserView

urlpatterns = [
    path("create/", CreateUserView.as_view(), name="create"),
]

app_name = "user"
