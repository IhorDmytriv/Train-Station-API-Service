from django.urls import path, include

from user.views import CreateUserView, ManageUserView

urlpatterns = [
    path("create/", CreateUserView.as_view(), name="create"),
    path("me/", ManageUserView.as_view(), name="manage"),
]

app_name = "user"
