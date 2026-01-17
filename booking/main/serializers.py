from rest_framework import serializers
from .models import *

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = (
            'id',
            'number',
            'cardholder_name',
            'expiration_date',
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

class FeedbackSerializer(serializers.ModelSerializer):
    user_data = UserDataSerializer(source='user_access.user_data', read_only=True)
    class Meta:
        model = Feedback
        fields = (
            'id',
            'text',
            'rate',
            'created_at',
            'updated_at',
            'user_data',
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


class RealtySerializer(serializers.ModelSerializer):
    city = CitySerializer(read_only=True)
    group = serializers.CharField(source='realty_group.name')

    feedbacks = FeedbackSerializer(many=True, read_only=True)
    booking_items = BookingItemSerializer(many=True, read_only=True)
    images = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='url'
    )

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

class RealtySearchSerializer(serializers.Serializer):
    Price = serializers.FloatField(required=False)
    Rating = serializers.IntegerField(required=False, min_value=1, max_value=5)
    Checkboxes = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )

class AccRatesSerializer(serializers.Serializer):
    avgRate = serializers.FloatField()
    countRate = serializers.IntegerField() 

class UserDetailSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source="user_data.first_name")
    lastName = serializers.CharField(source="user_data.last_name")
    email = serializers.EmailField(source="user_data.email")
    birthdate = serializers.DateField(source="user_data.birth_date", allow_null=True)
    registeredAt = serializers.DateTimeField(source="user_data.registered_at")

    role = serializers.CharField(source="user_role.id")

    cards = CardSerializer(
        source="user_data.cards",
        many=True,
        read_only=True
    )

    bookingItems = BookingItemShortSerializer(
        source="booking_items",
        many=True,
        read_only=True
    )

    class Meta:
        model = UserAccess
        fields = (
            "id",
            "login",
            "role",
            "firstName",
            "lastName",
            "email",
            "birthdate",
            "registeredAt",
            "cards",
            "bookingItems",
        )