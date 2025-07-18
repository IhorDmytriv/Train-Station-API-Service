import pathlib
import uuid
from datetime import timedelta

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from train_station import settings

MAX_CARGO_NUM = 20
MAX_PLACES_IN_CARGO = 100


class Crew(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name


class TrainType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


def train_image_path(instance: "Train", filename: str) -> pathlib.Path:
    filename = (
        f"{slugify(instance.name)}-{uuid.uuid4()}"
        + pathlib.Path(filename).suffix
    )
    return pathlib.Path("upload/trains/") / pathlib.Path(filename)


class Train(models.Model):
    name = models.CharField(max_length=255)
    cargo_num = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(MAX_CARGO_NUM)
        ]
    )
    places_in_cargo = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(MAX_PLACES_IN_CARGO)
        ]
    )
    train_type = models.ForeignKey(
        TrainType,
        on_delete=models.CASCADE,
        related_name="trains",
    )
    image = models.ImageField(
        null=True,
        blank=True,
        upload_to=train_image_path,
    )

    @property
    def capacity(self) -> int:
        return self.cargo_num * self.places_in_cargo

    def __str__(self):
        return f"{self.name} capacity: {self.capacity}"


class Station(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.name


class Route(models.Model):
    name = models.CharField(max_length=255)
    source = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="routes_from",
    )
    destination = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="routes_to",
    )
    distance = models.IntegerField()

    def __str__(self):
        return self.name


class Journey(models.Model):
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="journeys",
    )
    train = models.ForeignKey(
        Train,
        on_delete=models.CASCADE,
        related_name="journeys",
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crew = models.ManyToManyField(Crew, related_name="journeys")

    @property
    def travel_time(self) -> timedelta:
        return self.arrival_time - self.departure_time

    def clean(self):
        if self.arrival_time <= self.departure_time:
            raise ValidationError({
                "arrival_time": "Arrival time must be after departure time."
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["departure_time"]

    def __str__(self):
        return f"Route: {self.route.name} Train: {self.train.name}"


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        user_name = f"{self.user.first_name} {self.user.last_name}"
        return f"Order(№{self.id}) {user_name}: {self.created_at}"


class Ticket(models.Model):
    cargo = models.IntegerField()
    seat = models.IntegerField()
    journey = models.ForeignKey(
        Journey,
        on_delete=models.CASCADE,
        related_name="tickets",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets",
    )

    @property
    def cargo_and_seat(self):
        return f"Cargo {self.cargo}, Seat {self.seat}"

    @staticmethod
    def validate_ticket(cargo, seat, train, error_to_raise):
        for ticket_attr_value, ticket_attr_name, train_attr_name in [
            (cargo, "cargo", "cargo_num"),
            (seat, "seat", "places_in_cargo"),
        ]:
            count_attrs = getattr(train, train_attr_name)
            if not (1 <= ticket_attr_value <= count_attrs):
                raise error_to_raise(
                    {
                        ticket_attr_name: f"{ticket_attr_name} "
                        f"number must be in available range: "
                        f"(1, {train_attr_name}): "
                        f"(1, {count_attrs})"
                    }
                )

    def clean(self):
        Ticket.validate_ticket(
            self.cargo,
            self.seat,
            self.journey.train,
            ValidationError,
        )

    def save(
        self,
        *args,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        return super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )

    def __str__(self):
        return f"{self.journey} (cargo: {self.cargo} seat: {self.seat})"

    class Meta:
        unique_together = ("journey", "cargo", "seat")
        ordering = ["cargo", "seat"]
