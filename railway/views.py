from datetime import datetime

from django.db.models import Count, F
from rest_framework.exceptions import ParseError
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.viewsets import ModelViewSet

from railway.models import (
    Crew,
    TrainType,
    Train,
    Station,
    Route,
    Journey,
    Order,
)
from railway.serializers import (
    CrewSerializer,
    CrewListSerializer,
    TrainTypeSerializer,
    TrainSerializer,
    TrainListSerializer,
    TrainDetailSerializer,
    StationSerializer,
    StationListSerializer,
    StationDetailSerializer,
    RouteSerializer,
    RouteListSerializer,
    RouteDetailSerializer,
    JourneySerializer,
    JourneyListSerializer,
    JourneyDetailSerializer,
    OrderSerializer,
    OrderListSerializer
)


class CrewViewSet(ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return CrewListSerializer
        return CrewSerializer


class TrainTypeViewSet(ModelViewSet):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer


class TrainViewSet(ModelViewSet):
    queryset = Train.objects.all()
    serializer_class = TrainSerializer

    @staticmethod
    def _params_to_ints(query_string: str) -> list[int]:
        """Method to convert string parameters to a list of integers."""
        try:
            return list(map(int, query_string.split(',')))
        except ValueError:
            raise ParseError(
                "train_type query parameter must contain "
                "only integers separated by commas. exm:(1, 2)"
            )

    def get_queryset(self):
        queryset = self.queryset

        train_type = self.request.query_params.get("train_type")
        if train_type:
            train_type = self._params_to_ints(train_type)
            queryset = queryset.filter(train_type_id__in=train_type)

        if self.action in ["list", "retrieve"]:
            queryset = queryset.select_related("train_type")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return TrainListSerializer
        elif self.action == "retrieve":
            return TrainDetailSerializer
        return self.serializer_class


class StationViewSet(ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer

    def get_queryset(self):
        queryset = self.queryset
        name = self.request.query_params.get("name")
        if name:
            queryset = Station.objects.filter(name__icontains=name)

        if self.action in ["list", "retrieve"]:
            queryset = queryset.prefetch_related("routes_from", "routes_to")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return StationListSerializer
        if self.action == "retrieve":
            return StationDetailSerializer
        return self.serializer_class


class RouteViewSet(ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ["list", "retrieve"]:
            queryset = queryset.select_related("source", "destination")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        if self.action == "retrieve":
            return RouteDetailSerializer
        return self.serializer_class


class JourneyViewSet(ModelViewSet):
    queryset = Journey.objects.all()
    serializer_class = JourneySerializer

    def get_queryset(self):
        queryset = self.queryset
        route = self.request.query_params.get("route")
        train = self.request.query_params.get("train")
        departure_after = self.request.query_params.get("departure_after")
        departure_before = self.request.query_params.get("departure_before")
        arrival_after = self.request.query_params.get("arrival_after")
        arrival_before = self.request.query_params.get("arrival_before")

        if route:
            queryset = queryset.filter(route__name__icontains=route)

        if train:
            queryset = queryset.filter(train__name__icontains=train)

        if departure_after:
            departure_after = (
                datetime
                .strptime(departure_after, "%Y-%m-%d").date()
            )
            queryset = (
                queryset
                .filter(departure_time__date__gte=departure_after)
            )

        if departure_before:
            departure_before = (
                datetime
                .strptime(departure_before, "%Y-%m-%d").date()
            )
            queryset = (
                queryset
                .filter(departure_time__date__lte=departure_before)
            )

        if arrival_after:
            arrival_after = (
                datetime
                .strptime(arrival_after, "%Y-%m-%d").date()
            )
            queryset = (
                queryset
                .filter(arrival_time__date__gte=arrival_after)
            )

        if arrival_before:
            arrival_before = (
                datetime
                .strptime(arrival_before, "%Y-%m-%d").date()
            )
            queryset = (
                queryset
                .filter(arrival_time__date__lte=arrival_before)
            )

        if self.action in ["list", "retrieve"]:
            queryset = (
                queryset
                .select_related(
                    "route__source",
                    "route__destination",
                    "train__train_type",
                )
                .prefetch_related("crew", "tickets")
                .annotate(
                    tickets_available=(
                        F("train__cargo_num") * F("train__places_in_cargo")
                        - Count("tickets")
                    )
                )
            )
        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return JourneyListSerializer
        if self.action == "retrieve":
            return JourneyDetailSerializer
        return self.serializer_class


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_permissions(self):
        if self.action == "destroy":
            return (IsAdminUser(),)
        return (IsAuthenticated(),)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return self.serializer_class

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        if self.action in ["list", "retrieve"]:
            queryset = queryset.prefetch_related(
                "tickets__journey__route",
                "tickets__journey__train",
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
