from rest_framework import serializers
from main.models import *
#from main.serializers.user import UserDataSerializer
from main.serializers.feeedback import FeedbackSerializer, AccRatesSerializer
from main.serializers.location import CitySerializer
from main.serializers.booking import BookingItemSerializer
from django.urls import reverse
from django.conf import settings
from main.models import RealtyGroup # Import your group model


class RealtySearchSerializer(serializers.Serializer):
    Price = serializers.FloatField(required=False)
    Rating = serializers.IntegerField(required=False, min_value=0, max_value=5)
    Checkboxes = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )

class RealtyCreateSerializer(serializers.ModelSerializer):
    country = serializers.CharField(write_only=True)
    city = serializers.CharField(write_only=True)
    group = serializers.CharField(write_only=True)

    class Meta:
        model = Realty
        fields = (
            'name',
            'description',
            'slug',
            'price',
            'country',
            'city',
            'group',
        )

    def to_internal_value(self, data):
       mutable = data.copy()

       mutable['name'] = data.get('realty-name')
       mutable['description'] = data.get('realty-description')
       mutable['slug'] = data.get('realty-slug')
       mutable['price'] = data.get('realty-price')
       mutable['country'] = data.get('realty-country')
       mutable['city'] = data.get('realty-city')
       mutable['group'] = data.get('realty-group')

       return super().to_internal_value(mutable)

    def create(self, validated_data):
        country_name = validated_data.pop('country').strip()
        city_name = validated_data.pop('city').strip()
        group_name = validated_data.pop('group').strip()

        country, _ = Country.objects.get_or_create(
            name__iexact=country_name,
            defaults={'name': country_name}
        )

        city, _ = City.objects.get_or_create(
            name__iexact=city_name,
            country=country,
            defaults={
                'name': city_name,
                'country': country
            }
        )

        group, _ = RealtyGroup.objects.get_or_create(
            name__iexact=group_name,
            defaults={
                'name': group_name,
                'slug': group_name.lower().replace(' ', '-'),
                'description': group_name
            }
        )

        realty = Realty.objects.create(
            city=city,
            realty_group=group,
            **validated_data
        )

        return realty

class RealtySerializer(serializers.ModelSerializer):
    city = CitySerializer(read_only=True)
    group = serializers.CharField(source='realty_group.name')

    feedbacks = FeedbackSerializer(many=True, read_only=True)
    booking_items = BookingItemSerializer(many=True, read_only=True)

    images = serializers.SerializerMethodField()
    accRates = serializers.SerializerMethodField()

    class Meta:
        model = Realty
        fields = (
            'id',
            'name',
            'description',
            'slug',
            'price',
            'city',
            'group',
            'accRates',
            'feedbacks',
            'booking_items',
            'images',
        )

    def update(self, instance, validated_data):
        group_data = validated_data.pop('realty-group', None)
        if group_data:
            group_name = group_data.get('name')
            group_obj = RealtyGroup.objects.filter(name=group_name).first()
            if group_obj:
                instance.realty_group = group_obj
                
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

    def get_images(self, obj):
        request = self.context.get("request")
        result = []

        for img in obj.images.all():
            url = f"{settings.SITE_URL}{reverse('storageItem', kwargs={'itemId': img.image_url})}"

            if request:
                url = request.build_absolute_uri(url)

            result.append({
                "imageUrl": url
            })

        return result


    def get_accRates(self, obj):
        avg = 0.0
        count = 0

        if hasattr(obj, "avg_rating") and obj.avg_rating is not None:
            avg = round(float(obj.avg_rating), 2)

        if hasattr(obj, "rates_count") and obj.rates_count is not None:
            count = int(obj.rates_count)

        return AccRatesSerializer({
            "avgRate": avg,
            "countRate": count
        }).data

