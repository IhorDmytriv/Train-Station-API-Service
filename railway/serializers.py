from django.db.migrations import serializer
from rest_framework import serializers

from railway.models import (
    Crew,
    TrainType,
    Train,
    Station,
    Route,
    Journey,
    Order,
    Ticket
)


# Crew Serializers
class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = [
            "id",
            "first_name",
            "last_name",
        ]


class CrewListSerializer(CrewSerializer):
    class Meta:
        model = Crew
        fields = [
            "id",
            "full_name"
        ]


# Train Type Serializers
class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = [
            "id",
            "name",
        ]


# Train Serializers
class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = [
            "id",
            "name",
            "train_type",
            "cargo_num",
            "places_in_cargo",
            "capacity"
        ]


class TrainListSerializer(TrainSerializer):
    type = serializers.SlugRelatedField(
        source="train_type",
        slug_field="name",
        read_only=True
    )

    class Meta:
        model = Train
        fields = [
            "id",
            "name",
            "type",
            "cargo_num",
            "places_in_cargo",
            "capacity"
        ]


class TrainDetailSerializer(TrainSerializer):
    train_type = TrainTypeSerializer()


# Station Serializers
class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = [
            "id",
            "name",
            "latitude",
            "longitude",
        ]


# Route Serializers
class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = [
            "id",
            "name",
            "source",
            "destination",
            "distance"
        ]


class RouteListSerializer(RouteSerializer):
    source = serializers.StringRelatedField()
    destination = serializers.StringRelatedField()

    class Meta:
        model = Route
        fields = [
            "id",
            "name",
            "source",
            "destination",
            "distance"
        ]


class RouteDetailSerializer(RouteSerializer):
    source = StationSerializer()
    destination = StationSerializer()


# Journey Serializers
class JourneySerializer(serializers.ModelSerializer):
    class Meta:
        model = Journey
        fields = [
            "id",
            "route",
            "train",
            "departure_time",
            "arrival_time",
            "crew",
            "travel_time",
        ]


# Order Serializers
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "id",
            "created_at",
            "user"
        ]


# Ticket Serializers
class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            "id",
            "cargo",
            "seat",
            "journey",
            "order"
        ]
