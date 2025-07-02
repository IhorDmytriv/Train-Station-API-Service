from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from rest_framework.test import APIClient

from railway.models import Crew
from railway.serializers import CrewListSerializer, CrewSerializer

CREW_URL = reverse("railway:crew-list")


def sample_crew(**params):
    defaults = {
        "first_name": "First name",
        "last_name": "Last name"
    }
    defaults.update(params)

    return Crew.objects.create(**defaults)


def detail_url(crew_id):
    return reverse("railway:crew-detail", args=[crew_id])


class UnauthenticatedTrainApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(CREW_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTrainApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.test",
            password="test_password"
        )
        self.client.force_login(self.user)

    def test_list_crew_returns_all_crews(self):
        sample_crew(
            first_name="Crew name 1",
            last_name="Crew last name 1"
        )

        sample_crew(
            first_name="Crew name 2",
            last_name="Crew last name 2"
        )

        response = self.client.get(CREW_URL)
        crews = Crew.objects.all()
        serializer = CrewListSerializer(crews, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["results"], serializer.data)

    def test_retrieve_crew_detail(self):
        crew = sample_crew()

        url = detail_url(crew.id)
        response = self.client.get(url)

        serializer = CrewSerializer(crew)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_crew_forbidden(self):
        payload = {
            "first_name": "First name",
            "last_name": "Last name"
        }

        response = self.client.post(CREW_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_crew_not_allowed(self):
        crew = sample_crew()

        url = detail_url(crew.id)

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

    def test_create_crew(self):
        payload = {
            "first_name": "First name",
            "last_name": "Last name"
        }

        response = self.client.post(CREW_URL, payload)

        crew = Crew.objects.get(id=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key in payload:
            self.assertEqual(payload[key], getattr(crew, key))

    def test_delete_crew_allowed(self):
        train = sample_crew()

        url = detail_url(train.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
