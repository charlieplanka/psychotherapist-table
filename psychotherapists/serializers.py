from rest_framework import serializers
from .models import Therapist, Method

class MethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Method
        fields = '__all__'


class TherapistSerializer(serializers.ModelSerializer):
    methods = MethodSerializer(many=True)

    class Meta:
        model = Therapist
        fields = '__all__'