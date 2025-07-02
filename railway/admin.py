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


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [TicketInline,]


models = [Journey, Crew, TrainType, Train, Station, Route, Ticket]
for model in models:
    admin.site.register(model)

admin.site.unregister(Group)
