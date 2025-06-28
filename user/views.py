from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView

from user.serializers import UserSerializer


class CreateUserView(CreateAPIView):
    serializer_class = UserSerializer

class ManageUserView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
