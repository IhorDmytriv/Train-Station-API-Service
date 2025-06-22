from django.db import models

from train_station import settings


class Crew(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class TrainType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"


class Train(models.Model):
    name = models.CharField(max_length=255)
    cargo_num = models.IntegerField()
    places_in_cargo = models.IntegerField()
    train_type = models.ForeignKey(
        TrainType,
        on_delete=models.CASCADE,
        related_name="trains",
        blank=True,
        null=True
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
        return f"{self.name} ({self.latitude}, {self.longitude})"


class Route(models.Model):
    name = models.CharField(max_length=255)
    source = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="routes",
        blank=True,
        null=True
    )
    destination = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="routes",
        blank=True,
        null=True
    )
    distance = models.IntegerField()

    def __str__(self):
        return f"{self.name} ({self.source}, {self.destination})"


class Journey(models.Model):
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="journeys",
        blank=True,
        null=True
    )
    train = models.ForeignKey(
        Train,
        on_delete=models.CASCADE,
        related_name="journeys",
        blank=True,
        null=True
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    class Meta:
        ordering = ["departure_time"]

    @property
    def travel_time(self) -> int:
        return self.arrival_time - self.departure_time

    def __str__(self):
        return f"Route: {self.route.name} Train: {self.train.name}"


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        blank=True,
        null=True
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
        blank=True,
        null=True
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets",
        blank=True,
        null=True
    )

    def __str__(self):
        return f"Ticket: (cargo: {self.cargo} seat: {self.seat})"
