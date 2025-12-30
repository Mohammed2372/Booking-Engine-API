import django_filters as df
from django_filters import FilterSet

from .models import RoomType


class RoomTypeFilter(FilterSet):
    city = df.CharFilter(field_name="property__city", lookup_expr="iexact")
    min_price = df.NumberFilter(field_name="base_price", lookup_expr="gte")
    max_price = df.NumberFilter(field_name="base_price", lookup_expr="lte")
    capacity = df.NumberFilter(field_name="capacity", lookup_expr="gte")
    amenities = df.CharFilter(field_name="amenities", lookup_expr="contains")
    name = df.ChoiceFilter(field_name="name", choices=RoomType.RoomKind.choices)
    view_type = df.ChoiceFilter(
        field_name="view_type", choices=RoomType.ViewType.choices
    )

    class Meta:
        model = RoomType
        fields = [
            "name",
            "view_type",
            "is_smoking",
            "capacity",
            "city",
        ]
