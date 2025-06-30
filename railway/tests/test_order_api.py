from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from railway.models import (
    Order,
    Station,
    TrainType,
    Train,
    Route,
    Crew,
    Journey
)
from railway.serializers import OrderListSerializer


ORDER_URL = reverse("railway:order-list")


def detail_url(order_id):
    return reverse("railway:order-detail", args=[order_id])


def sample_order(user):
    return Order.objects.create(user=user)


def sample_station(name="Station"):
    return Station.objects.create(
        name=name, latitude=48.7, longitude=21.2
    )


def sample_train_type(name="Express"):
    return TrainType.objects.create(name=name)


def sample_train(name="Train", train_type=None):
    if train_type is None:
        train_type = sample_train_type()
    return Train.objects.create(
        name=name, cargo_num=5, places_in_cargo=20, train_type=train_type
    )


def sample_route(name="Route"):
    source = sample_station(name="Source")
    destination = sample_station(name="Destination")
    return Route.objects.create(
        name=name,
        source=source,
        destination=destination,
        distance=100
    )


def sample_crew(name="John"):
    return Crew.objects.create(first_name=name, last_name="Doe")


def sample_journey(**params):
    if "train" in params:
        train = params["train"]
    else:
        train = sample_train()
    defaults = {
        "route": sample_route(),
        "train": train,
        "departure_time": datetime.now(),
        "arrival_time": datetime.now() + timedelta(hours=2),
    }
    defaults.update(params)
    journey = Journey.objects.create(
        route=defaults["route"],
        train=defaults["train"],
        departure_time=defaults["departure_time"],
        arrival_time=defaults["arrival_time"],
    )
    if "crew" in params:
        journey.crew.set(params["crew"])
    return journey


class UnauthenticatedOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ORDER_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="pass123",
            first_name="Will",
            last_name="Smith"
        )
        self.client.force_login(self.user)
        self.train_type = sample_train_type()
        self.train = sample_train(train_type=self.train_type)
        self.journey = sample_journey(train=self.train)

    def test_list_orders_returns_only_user_orders(self):
        sample_order(self.user)
        sample_order(self.user)

        other_user = get_user_model().objects.create_user(
            email="other@test.com", password="other123"
        )
        sample_order(other_user)

        response = self.client.get(ORDER_URL)
        orders = Order.objects.filter(user=self.user)
        serializer = OrderListSerializer(orders, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["results"], serializer.data)

    def test_create_order(self):
        payload = {
            "tickets" : []
        }
        response = self.client.post(ORDER_URL, payload)

        print(response.status_code)
        print(response.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(id=response.data["id"])
        self.assertEqual(order.user, self.user)

    def test_retrieve_order_detail(self):
        order = sample_order(self.user)
        url = detail_url(order.id)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], order.id)

    def test_user_cannot_retrieve_others_order(self):
        other_user = get_user_model().objects.create_user(
            email="other@test.com", password="other123"
        )
        other_order = sample_order(other_user)

        url = detail_url(other_order.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_delete_order(self):
        order = sample_order(self.user)
        url = detail_url(order.id)

        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = get_user_model().objects.create_user(
            email="admin@test.com",
            password="adminpass",
            is_staff=True,
        )
        self.client.force_login(self.admin_user)

    def test_admin_can_delete_order(self):
        user = get_user_model().objects.create_user(
            email="user2@test.com", password="pass123"
        )
        order = sample_order(user)

        url = detail_url(order.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Order.objects.filter(id=order.id).exists())
