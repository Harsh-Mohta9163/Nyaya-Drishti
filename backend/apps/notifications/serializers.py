from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    case_number = serializers.CharField(source="case.case_number", read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "case", "case_number", "notification_type", "message", "is_read", "created_at"]