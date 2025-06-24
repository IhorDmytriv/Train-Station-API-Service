from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from railway.models import Journey, Crew, TrainType, Train, Station, Route, Order, Ticket


class ModelTests(TestCase):
    def setUp(self):
        self.crew = Crew.objects.create(
            first_name="Joe",
            last_name="Smith",
        )
        self.train_type = TrainType.objects.create(
            name="High-speed",
        )
        self.train = Train.objects.create(
            name="Express",
            cargo_num=5,
            places_in_cargo=20,
            train_type=self.train_type
        )
        self.station_a = Station.objects.create(name="Station A", latitude=45.0, longitude=24.0)
        self.station_b = Station.objects.create(name="Station B", latitude=46.0, longitude=25.0)
        self.route = Route.objects.create(
            name="Route A-B",
            source=self.station_a,
            destination=self.station_b,
            distance=200
        )
        self.journey = Journey.objects.create(
            route=self.route,
            train=self.train,
            departure_time=datetime.now(),
            arrival_time=datetime.now() + timedelta(hours=2)
        )
        self.user = get_user_model().objects.create_user(
            email="test@example.com",
            password="password"
        )
        self.order = Order.objects.create(user=self.user)

    # Crew Tests
    def test_crew_str(self):
        self.assertEqual(str(self.crew), f"{self.crew.first_name} {self.crew.last_name}")

    # TrainType Tests
    def test_train_type_str(self):
        self.assertEqual(str(self.train_type), self.train_type.name)

    # Train Tests
    def test_train_cargo_num_too_high_raises_error(self):
        train = Train(
            name="SuperTrain",
            cargo_num=30,  # > 20
            places_in_cargo=50,
            train_type=self.train_type
        )
        self.assertRaises(ValidationError, train.full_clean)

    def test_train_places_in_cargo_too_low_raises_error(self):
        train = Train(
            name="MiniTrain",
            cargo_num=10,
            places_in_cargo=0, # < 1
            train_type=self.train_type
        )
        self.assertRaises(ValidationError, train.full_clean)

    def test_train_capacity_attribute(self):
        self.assertEqual(self.train.capacity, self.train.places_in_cargo * self.train.cargo_num)

    def test_train_str(self):
        self.assertEqual(str(self.train), f"{self.train.name} capacity: {self.train.capacity}")

    # Station Tests
    def test_station_str(self):
        station = self.station_a
        self.assertEqual(
            str(station), station.name
        )

    # Route Tests
    def test_route_str(self):
        route = self.route
        self.assertEqual(
            str(route), f"{route.name} ({route.source}, {route.destination})"
        )

    # Journey Tests
    def test_journey_travel_time_attribute(self):
        self.assertEqual(
            self.journey.travel_time, self.journey.arrival_time - self.journey.departure_time
        )

    def test_journey_str(self):
        journey = self.journey
        self.assertEqual(str(journey), f"Route: {self.route.name} Train: {self.train.name}")

    # Order Tests
    def test_order_str(self):
        order = self.order
        user_name = f"{order.user.first_name} {order.user.last_name}"
        self.assertEqual(str(order), f"Order(№{order.id}) {user_name}: {order.created_at}")

    # Ticket Tests
    def test_ticket_cargo_too_high_raises_error(self):
        train = self.journey.train
        ticket = Ticket(
            cargo=train.cargo_num + 1,  # > 20
            seat=train.places_in_cargo - 1,
            journey=self.journey,
            order=self.order,
        )
        self.assertRaises(ValidationError, ticket.full_clean)

    def test_ticket_seat_too_high_raises_error(self):
        train = self.journey.train
        ticket = Ticket(
            cargo=train.cargo_num - 1,  # > 20
            seat=train.places_in_cargo + 1,
            journey=self.journey,
            order=self.order,
        )
        self.assertRaises(ValidationError, ticket.full_clean)

    def test_ticket_str(self):
        ticket = Ticket.objects.create(
            cargo=5,
            seat=2,
            journey=self.journey,
            order=self.order,
        )
        self.assertEqual(str(ticket),f"{ticket.journey} (cargo: {ticket.cargo} seat: {ticket.seat})")

    def test_ticket_valid_data_saves_correctly(self):
        ticket = Ticket(
            cargo=1,
            seat=1,
            journey=self.journey,
            order=self.order,
        )
        try:
            ticket.full_clean()
            ticket.save()
        except ValidationError:
            self.fail("Valid ticket raised ValidationError unexpectedly!")

    def test_ticket_unique_constraint(self):
        Ticket.objects.create(cargo=1, seat=1, journey=self.journey, order=self.order)
        with self.assertRaises(ValidationError):
            ticket = Ticket(cargo=1, seat=1, journey=self.journey, order=self.order)
            ticket.full_clean()
