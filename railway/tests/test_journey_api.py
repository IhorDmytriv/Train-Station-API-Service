from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.db.models import F, Count
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from railway.models import Journey, Route, Train, TrainType, Station, Crew
from railway.serializers import JourneyListSerializer, JourneyDetailSerializer

JOURNEY_URL = reverse("railway:journey-list")


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
        name=name, source=source, destination=destination, distance=100
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


def detail_url(journey_id):
    return reverse("railway:journey-detail", args=[journey_id])


class UnauthenticatedJourneyApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(JOURNEY_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedJourneyApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="pass123"
        )
        self.client.force_login(self.user)
        self.train_type = sample_train_type()

    def test_list_journeys(self):
        train = sample_train(train_type=self.train_type)
        sample_journey(train=train)
        sample_journey(train=train)

        response = self.client.get(JOURNEY_URL)
        journeys = Journey.objects.all().annotate(
            tickets_available=(
                F("train__cargo_num")
                * F("train__places_in_cargo")
                - Count("tickets")
            )
        )
        serializer = JourneyListSerializer(journeys, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_filter_by_train_name(self):
        train_1 = sample_train(
            name="FilteredTrain", train_type=self.train_type
        )
        train_2 = sample_train(
            name="OtherTrain", train_type=self.train_type
        )
        sample_journey(train=train_1)
        sample_journey(train=train_2)

        res = self.client.get(JOURNEY_URL, {"train": "FilteredTrain"})
        self.assertEqual(len(res.data["results"]), 1)

    def test_filter_by_route_name(self):
        train = sample_train(train_type=self.train_type)
        route = sample_route(name="A-B")
        sample_journey(route=route, train=train)
        sample_journey(route=sample_route(name="OtherRoute"), train=train)

        res = self.client.get(JOURNEY_URL, {"route": "A"})
        self.assertEqual(len(res.data["results"]), 1)

    def test_filter_by_departure_date_range(self):
        now = datetime.now()
        train = sample_train(train_type=self.train_type)
        journey1 = sample_journey(
            train=train,
            departure_time=now + timedelta(days=1),
            arrival_time=now + timedelta(days=2),
        )
        sample_journey(
            train=train,
            departure_time=now + timedelta(days=5),
            arrival_time=now + timedelta(days=6),
        )

        res = self.client.get(JOURNEY_URL, {
            "departure_after": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
            "departure_before": (now + timedelta(days=2)).strftime("%Y-%m-%d"),
        })

        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["id"], journey1.id)

    def test_filter_by_arrival_date_range(self):
        now = datetime.now()
        train = sample_train(train_type=self.train_type)

        journey_in_range = sample_journey(
            train=train,
            departure_time=now + timedelta(days=1),
            arrival_time=now + timedelta(days=3),
        )
        sample_journey(
            train=train,
            departure_time=now + timedelta(days=1),
            arrival_time=now + timedelta(days=6),
        )

        res = self.client.get(JOURNEY_URL, {
            "arrival_after": (now + timedelta(days=2)).strftime("%Y-%m-%d"),
            "arrival_before": (now + timedelta(days=4)).strftime("%Y-%m-%d"),
        })

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["id"], journey_in_range.id)

    def test_retrieve_journey_detail(self):
        train = sample_train(train_type=self.train_type)
        journey = sample_journey(train=train)
        url = detail_url(journey.id)
        res = self.client.get(url)

        serializer = JourneyDetailSerializer(journey)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_journey_forbidden(self):
        train = sample_train(train_type=self.train_type)
        route = sample_route()
        payload = {
            "train": train.id,
            "route": route.id,
            "departure_time": datetime.now().isoformat(),
            "arrival_time": (datetime.now() + timedelta(hours=2)).isoformat(),
        }

        res = self.client.post(JOURNEY_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminJourneyApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_user(
            email="admin@admin.com", password="pass123", is_staff=True
        )
        self.client.force_login(self.admin)

    def test_create_journey(self):
        train = sample_train()
        route = sample_route()
        crew_member = sample_crew()
        payload = {
            "train": train.id,
            "route": route.id,
            "departure_time": datetime.now().isoformat(),
            "arrival_time": (datetime.now() + timedelta(hours=1)).isoformat(),
            "crew": [crew_member.id],
        }

        res = self.client.post(JOURNEY_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        journey = Journey.objects.get(id=res.data["id"])
        self.assertEqual(journey.crew.count(), 1)
        self.assertEqual(journey.train.id, train.id)
        self.assertEqual(journey.route.id, route.id)

    def test_invalid_time_validation(self):
        train = sample_train()
        route = sample_route()
        payload = {
            "train": train.id,
            "route": route.id,
            "departure_time": datetime.now().isoformat(),
            "arrival_time": datetime.now().isoformat(),  # same as departure
        }

        res = self.client.post(JOURNEY_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_journey(self):
        journey = sample_journey()
        url = detail_url(journey.id)

        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
