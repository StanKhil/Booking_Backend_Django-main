from rest_framework import serializers
from main.models import *
from main.serializers import BookingItemShortSerializer, FeedbackShortSerializer

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