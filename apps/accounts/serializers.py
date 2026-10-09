from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "phone_number", "password")
        read_only_fields = ("id",)

    def validate_password(self, value):
        validate_password(value, user=User(username=self.initial_data.get("username", "")))
        return value

    def validate_phone_number(self, value):
        if not value:
            return None
        if value and User.objects.filter(phone_number=value, deleted_at__isnull=True).exists():
            raise serializers.ValidationError("Este teléfono ya está registrado.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
