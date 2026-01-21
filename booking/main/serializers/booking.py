from django.conf import settings
from rest_framework import serializers
from main.models import *
from main.serializers.location import CitySerializer
from main.serializers.common import *
from django.urls import reverse

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
    realtyId = serializers.ReadOnlyField(source="realty.id")
    startDate = serializers.DateTimeField(source="start_date")
    endDate = serializers.DateTimeField(source="end_date")
    userAccess = UserAccessSerializer(source="user_access", read_only=True)

    realty = BookingRealtyNameSerializer(read_only=True)
    images = serializers.SerializerMethodField()

    class Meta:
        model = BookingItem
        fields = (
            "id",
            "startDate",
            "endDate",
            "realty",
            "realtyId",
            "images",
            "userAccess",
        )

    def get_images(self, obj):
        request = self.context.get("request")
        result = []

        for img in obj.realty.images.all():
            #url = reverse('storageItem', kwargs={'itemId': img.image_url})
            url = img.image_url

            if request:
                url = request.build_absolute_uri(url)

            result.append({
                "imageUrl": url
            })

        return result

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
