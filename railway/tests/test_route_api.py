from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from railway.models import Route, Station
from railway.serializers import (
    RouteListSerializer,
    RouteDetailSerializer
)

ROUTE_URL = reverse("railway:route-list")


def sample_station(**params):
    defaults = {
        "name": "Sample Station",
        "latitude": 48.7194,
        "longitude": 21.2577,
    }
    defaults.update(params)
    return Station.objects.create(**defaults)


def sample_route(**params):
    source = params.pop("source", sample_station(name="Source Station"))
    destination = params.pop(
        "destination", sample_station(name="Destination Station")
    )

    defaults = {
        "name": "Sample Route",
        "source": source,
        "destination": destination,
        "distance": 100,
    }
    defaults.update(params)

    return Route.objects.create(**defaults)


def detail_url(route_id):
    return reverse("railway:route-detail", args=[route_id])


class UnauthenticatedRouteApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(ROUTE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedRouteApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.test",
            password="test_password"
        )
        self.client.force_login(self.user)

    def test_list_routes_returns_all_routes(self):
        sample_route(name="Route 1")
        sample_route(name="Route 2")

        response = self.client.get(ROUTE_URL)
        routes = Route.objects.all()
        serializer = RouteListSerializer(routes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["results"], serializer.data)

    def test_retrieve_route_detail(self):
        route = sample_route()

        url = detail_url(route.id)
        response = self.client.get(url)

        serializer = RouteDetailSerializer(route)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_route_forbidden(self):
        source = sample_station(name="Source Station")
        destination = sample_station(name="Destination Station")
        payload = {
            "name": "New Route",
            "source": source.id,
            "destination": destination.id,
            "distance": 150,
        }

        response = self.client.post(ROUTE_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_route_not_allowed(self):
        route = sample_route()
        url = detail_url(route.id)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminRouteApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@admin.admin",
            password="test_password",
            is_staff=True,
        )
        self.client.force_login(self.user)

    def test_create_route(self):
        source = sample_station(name="Košice")
        destination = sample_station(name="Prešov")
        payload = {
            "name": "Košice - Prešov",
            "source": source.id,
            "destination": destination.id,
            "distance": 35,
        }
        response = self.client.post(ROUTE_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        route = Route.objects.get(id=response.data["id"])
        self.assertEqual(route.name, payload["name"])
        self.assertEqual(route.source, source)
        self.assertEqual(route.destination, destination)
        self.assertEqual(route.distance, payload["distance"])

    def test_delete_route_allowed(self):
        route = sample_route()
        url = detail_url(route.id)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
