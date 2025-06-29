from datetime import datetime

from django.db.models import Count, F
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample
)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
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
    TrainImageSerializer,
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
        elif self.action == "upload_image":
            return TrainImageSerializer
        return self.serializer_class

    @extend_schema(
        request=TrainImageSerializer,
        responses={200: TrainImageSerializer},
        description="Upload or update an image for a specific train.",
        examples=[
            OpenApiExample(
                name="Image upload example",
                value={"image": "train_images/blue_train.jpg"},
                summary="Train image upload",
                description="Upload an image file for the selected train."
            )
        ],
    )
    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
    )
    def upload_image(self, request, pk=None):
        bus = self.get_object()
        serializer = self.get_serializer(bus, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="train_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Comma-separated list of train type IDs to filter. "
                    "Example: `1,2,3`"
                ),
                examples=[
                    OpenApiExample(
                        name="Filter example",
                        value="1,2",
                        summary="Filter by multiple train type IDs",
                        description=(
                            "Only return trains that "
                            "match the given train_type IDs."
                        ),
                    )
                ],
            ),
        ],
        responses={200: TrainListSerializer},
        description=(
            "Returns a list of trains. "
            "You can filter by `train_type` ID using a comma-separated string."
        ),
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="name",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Filter stations by name "
                    "(case-insensitive, partial match allowed)."
                ),
            ),
        ],
        description=(
            "Returns a list of stations. "
            "Supports filtering by the `name` query parameter."
        ),
        responses={200: StationListSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="route",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Filter journeys by route name "
                    "(case-insensitive, partial match)."
                ),
            ),
            OpenApiParameter(
                name="train",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Filter journeys by train name "
                    "(case-insensitive, partial match)."
                ),
            ),
            OpenApiParameter(
                name="departure_after",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description=(
                    "Filter journeys that depart after this date (inclusive)."
                ),
            ),
            OpenApiParameter(
                name="departure_before",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description=(
                    "Filter journeys that depart before this date (inclusive)."
                ),
            ),
            OpenApiParameter(
                name="arrival_after",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description=(
                    "Filter journeys that arrive after this date (inclusive)."
                ),
            ),
            OpenApiParameter(
                name="arrival_before",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description=(
                    "Filter journeys that arrive before this date (inclusive)."
                ),
            ),
        ],
        description=(
            "List all journeys, "
            "optionally filtered by route, train, or date ranges."
        ),
        responses={200: JourneyListSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


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
