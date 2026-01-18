from rest_framework import serializers
from main.models import *
from main.serializers.user import UserDataSerializer

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

class AccRatesSerializer(serializers.Serializer):
    avgRate = serializers.FloatField()
    countRate = serializers.IntegerField() 
