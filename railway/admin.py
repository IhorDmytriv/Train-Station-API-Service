from django.contrib import admin
from django.contrib.auth.models import Group

from railway.models import (
    Journey,
    Crew,
    TrainType,
    Train,
    Station,
    Route,
    Order,
    Ticket
)


models = [Journey, Crew, TrainType, Train, Station, Route, Order, Ticket]
for model in models:
    admin.site.register(model)

admin.site.unregister(Group)
