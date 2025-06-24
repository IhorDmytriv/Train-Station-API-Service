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


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = [
            "id",
            "first_name",
            "last_name",
        ]


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = [
            "id",
            "name",
        ]


class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = [
            "id",
            "name",
            "cargo_num",
            "places_in_cargo",
            "train_type",
            "capacity"
        ]


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = [
            "id",
            "name",
            "latitude",
            "longitude",
        ]


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


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "id",
            "created_at",
            "user"
        ]


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
