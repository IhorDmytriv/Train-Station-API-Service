from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from rest_framework.test import APIClient

from railway.models import TrainType
from railway.serializers import TrainTypeSerializer

TRAIN_TYPE_URL = reverse("railway:traintype-list")

def sample_train_type(**params):
    defaults = {
        "name": "Sample train type",
    }
    defaults.update(params)

    return TrainType.objects.create(**defaults)

def detail_url(train_type_id):
    return reverse("railway:traintype-detail", args=[train_type_id])


class UnauthenticatedTrainApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(TRAIN_TYPE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTrainApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.test",
            password="test_password"
        )
        self.client.force_login(self.user)

    def test_list_train_types_returns_all_train_types(self):
        train_type_1 = sample_train_type(name="Sample train_type 1")

        train_type_2 = sample_train_type(name="Sample train_type 2")

        response = self.client.get(TRAIN_TYPE_URL)
        train_types = TrainType.objects.all()
        serializer = TrainTypeSerializer(train_types, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["results"], serializer.data)

    def test_retrieve_train_type_detail(self):
        train_type = sample_train_type()

        url = detail_url(train_type.id)
        response = self.client.get(url)

        serializer = TrainTypeSerializer(train_type)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_train_type_forbidden(self):
        payload = {
            "name": "Sample train type",
        }

        response = self.client.post(TRAIN_TYPE_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_train_type_not_allowed(self):
        train = sample_train_type()

        url = detail_url(train.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminTrainApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@admin.admin",
            password="test_password",
            is_staff=True,
        )
        self.client.force_login(self.user)

    def test_create_train_type(self):
        payload = {
            "name": "Sample train type",
        }
        response = self.client.post(TRAIN_TYPE_URL, payload)

        train_type = TrainType.objects.get(id=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(payload["name"], train_type.name)

    def test_delete_train_type_allowed(self):
        train_type = sample_train_type()

        url = detail_url(train_type.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
