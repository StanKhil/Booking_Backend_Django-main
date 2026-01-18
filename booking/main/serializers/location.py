from rest_framework import serializers
from main.models import *

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = (
            'name',
        )

class CitySerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)
    class Meta:
        model = City
        fields = (
            'name',
            'country',
        )

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = (
            'name',
        )
