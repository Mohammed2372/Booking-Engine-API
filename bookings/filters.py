import django_filters as df
from django_filters import FilterSet

from inventory.models import RoomType


class RoomTypeFilter(FilterSet):
    city = df.CharFilter(field_name="property__city", lookup_expr="iexact")
    min_price = df.NumberFilter(field_name="base_price", lookup_expr="gte")
    max_price = df.NumberFilter(field_name="base_price", lookup_expr="lte")
    capacity = df.NumberFilter(field_name="capacity", lookup_expr="gte")
    amenities = df.CharFilter(field_name="amenities", lookup_expr="contains")
    name = df.CharFilter(field_name="name", choices=RoomType.RoomKind.choices)

    class Meta:
        model = RoomType
        fields = ["name", "view_type", "is_smoking"]
