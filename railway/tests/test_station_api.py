from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from rest_framework.test import APIClient

from railway.models import Station
from railway.serializers import StationSerializer, StationListSerializer, StationDetailSerializer

STATION_URL = reverse("railway:station-list")

def sample_station(**params):
    defaults = {
        "name": "Sample Station",
        "latitude": 48.7194,
        "longitude": 21.2577,
    }
    defaults.update(params)

    return Station.objects.create(**defaults)

def detail_url(station_id):
    return reverse("railway:station-detail", args=[station_id])


class UnauthenticatedStationApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(STATION_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedStationApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.test",
            password="test_password"
        )
        self.client.force_login(self.user)

    def test_list_stations_returns_all_stations(self):
        station_1 = sample_station(name="Station 1")

        station_2 = sample_station(name="Station 2")

        response = self.client.get(STATION_URL)
        stations = Station.objects.all()
        serializer = StationListSerializer(stations, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["results"], serializer.data)

    def test_retrieve_station_detail(self):
        station = sample_station()

        url = detail_url(station.id)
        response = self.client.get(url)

        serializer = StationDetailSerializer(station)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_station_forbidden(self):
        payload = {
            "name": "Sample Station",
            "latitude": 48.7194,
            "longitude": 21.2577,
        }

        response = self.client.post(STATION_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_station_not_allowed(self):
        station = sample_station()

        url = detail_url(station.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminStationApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@admin.admin",
            password="test_password",
            is_staff=True,
        )
        self.client.force_login(self.user)

    def test_create_station(self):
        payload = {
            "name": "Sample Station",
            "latitude": 48.7194,
            "longitude": 21.2577,
        }
        response = self.client.post(STATION_URL, payload)

        station = Station.objects.get(id=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(payload["name"], station.name)

    def test_delete_station_allowed(self):
        station = sample_station()

        url = detail_url(station.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
