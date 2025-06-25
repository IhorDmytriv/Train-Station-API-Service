from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

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


class StationListSerializer(StationSerializer):
    class Meta:
        model = Station
        fields = [
            "id",
            "name",
        ]


class StationDetailSerializer(StationSerializer):
    routes_from = serializers.SlugRelatedField(
        many=True,
        slug_field="name",
        read_only=True
    )
    routes_to = serializers.SlugRelatedField(
        many=True,
        slug_field="name",
        read_only=True
    )

    class Meta:
        model = Station
        fields = [
            "id",
            "name",
            "latitude",
            "longitude",
            "routes_from",
            "routes_to"
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
            "travel_time",
            "crew",
        ]

    def get_travel_time_pretty(self, obj):
        td = obj.travel_time
        total_minutes = int(td.total_seconds() // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}h {minutes}m" if hours else f"{minutes}m"


class JourneyListSerializer(JourneySerializer):
    route = serializers.SlugRelatedField(read_only=True, slug_field="name")
    train = serializers.SlugRelatedField(read_only=True, slug_field="name")
    train_type = serializers.CharField(
        source="train.train_type.name",
        read_only=True
    )
    travel_time_pretty = serializers.SerializerMethodField()
    crew = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Journey
        fields = [
            "id",
            "route",
            "train",
            "train_type",
            "departure_time",
            "arrival_time",
            "travel_time_pretty",
            "crew",
        ]


class JourneyDetailSerializer(JourneySerializer):
    route = RouteDetailSerializer(read_only=True)
    train = TrainDetailSerializer(read_only=True)
    travel_time_pretty = serializers.SerializerMethodField()
    crew = CrewSerializer(many=True, read_only=True)

    class Meta:
        model = Journey
        fields = [
            "id",
            "route",
            "train",
            "departure_time",
            "arrival_time",
            "travel_time",
            "travel_time_pretty",
            "crew",
        ]


# Ticket Serializers
class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["cargo"],
            attrs["seat"],
            attrs["journey"].train,
            ValidationError
        )
        return data

    class Meta:
        model = Ticket
        fields = [
            "id",
            "cargo",
            "seat",
            "journey",
        ]


# Order Serializers
class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = [
            "id",
            "tickets"
        ]

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = serializers.StringRelatedField(many=True, read_only=True)
