from rest_framework import serializers
from main.models import *
from main.serializers.location import CitySerializer

class BookingRealtyNameSerializer(serializers.ModelSerializer):
    city = CitySerializer(read_only=True)
    class Meta:
        model = Realty
        fields = (
            "name",
            "city",
            "price",
        )

class BookingItemShortSerializer(serializers.ModelSerializer):
    realty = BookingRealtyNameSerializer(read_only=True)
    startDate = serializers.DateTimeField(source="start_date")
    endDate = serializers.DateTimeField(source="end_date")

    images = serializers.SlugRelatedField(
        source="realty.images",
        many=True,
        read_only=True,
        slug_field="url"
    )

    class Meta:
        model = BookingItem
        fields = (
            "id",
            "startDate",
            "endDate",
            "realty",
            "images",
        )

class BookingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingItem
        fields = (
            'id',
            'start_date',
            'end_date',
            'created_at',
            'user_access',
        )
