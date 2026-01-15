from rest_framework import serializers
from .models import *

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = (
            'id',
            'text',
            'rate',
            'created_at',
            'updated_at',
            'user_access',
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
    city = serializers.CharField(source='city.name')
    country = serializers.CharField(source='city.country.name')
    group = serializers.CharField(source='realty_group.name')

    feedbacks = FeedbackSerializer(many=True, read_only=True)
    booking_items = BookingItemSerializer(many=True, read_only=True)

    class Meta:
        model = Realty
        fields = (
            'id',
            'name',
            'description',
            'slug',
            'price',
            'city',
            'country',
            'group',
            'feedbacks',
            'booking_items',
        )

class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = (
            'id',
            'description',
            'can_create',
            'can_read',
            'can_update',
            'can_delete',
        )

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = (
            'id',
            'number',
            'cardholder_name',
            'expiration_date',
        )

class BookingItemShortSerializer(serializers.ModelSerializer):
    realty_name = serializers.CharField(source='realty.name')

    class Meta:
        model = BookingItem
        fields = (
            'id',
            'start_date',
            'end_date',
            'realty_name',
        )

class FeedbackShortSerializer(serializers.ModelSerializer):
    realty_name = serializers.CharField(source='realty.name')

    class Meta:
        model = Feedback
        fields = (
            'id',
            'text',
            'rate',
            'created_at',
            'realty_name',
        )

class UserDataSerializer(serializers.ModelSerializer):
    cards = CardSerializer(many=True, read_only=True)

    class Meta:
        model = UserData
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'birth_date',
            'registered_at',
            'cards',
        )

class UserDetailSerializer(serializers.ModelSerializer):
    user_data = UserDataSerializer(read_only=True)
    user_role = UserRoleSerializer(read_only=True)

    booking_items = BookingItemShortSerializer(many=True, read_only=True)
    feedbacks = FeedbackShortSerializer(many=True, read_only=True)

    class Meta:
        model = UserAccess
        fields = (
            'id',
            'login',
            'created_at',
            'user_role',
            'user_data',
            'booking_items',
            'feedbacks',
        )
