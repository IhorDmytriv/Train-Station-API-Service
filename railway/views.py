from rest_framework.viewsets import ModelViewSet

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
from railway.serializers import (
    CrewSerializer,
    CrewListSerializer,
    TrainTypeSerializer,
    TrainSerializer,
    TrainListSerializer,
    TrainDetailSerializer,
    StationSerializer,
    RouteSerializer,
    RouteListSerializer,
    RouteDetailSerializer,
    JourneySerializer,
    JourneyListSerializer,
    JourneyDetailSerializer,
    TicketSerializer,
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

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "list":
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
        if self.action in ["list", "retrieve"]:
            queryset = (
                queryset
                .select_related(
                    "route__source",
                    "route__destination",
                    "train__train_type",
                )
                .prefetch_related("crew")
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return JourneyListSerializer
        if self.action == "retrieve":
            return JourneyDetailSerializer
        return self.serializer_class


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

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


class TicketViewSet(ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
