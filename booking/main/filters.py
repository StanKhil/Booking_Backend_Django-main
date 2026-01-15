import django_filters
from .models import *

class RealtyFilter(django_filters.FilterSet):
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    city = django_filters.UUIDFilter(field_name="city_id")
    country = django_filters.UUIDFilter(field_name="city__country_id")
    realty_group = django_filters.UUIDFilter(field_name="realty_group_id")

    class Meta:
        model = Realty
        fields = [
            'city',
            'realty_group',
            'price_min',
            'price_max',
        ]

class UserFilter(django_filters.FilterSet):
    role = django_filters.CharFilter(
        field_name='user_role__id',
        lookup_expr='iexact'
    )

    email = django_filters.CharFilter(
        field_name='user_data__email',
        lookup_expr='icontains'
    )

    class Meta:
        model = UserAccess
        fields = ['role', 'email']
