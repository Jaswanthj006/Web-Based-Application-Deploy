from rest_framework import serializers
from .models import EquipmentDataset
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class EquipmentDatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentDataset
        fields = ['id', 'name', 'uploaded_at', 'total_count', 'summary_json']


class EquipmentDatasetDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentDataset
        fields = ['id', 'name', 'uploaded_at', 'total_count', 'summary_json']
