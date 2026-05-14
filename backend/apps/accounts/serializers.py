from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Department, User


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "code", "name", "sector"]


class UserSerializer(serializers.ModelSerializer):
    """Read shape returned to the frontend. Includes flat dept fields so the
    AuthContext can route on role/department without an extra fetch."""

    department_id = serializers.IntegerField(source="department.id", read_only=True, allow_null=True)
    department_code = serializers.CharField(source="department.code", read_only=True, allow_null=True)
    department_name = serializers.CharField(source="department.name", read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "role", "language",
            "department_id", "department_code", "department_name",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    """Open registration. Accepts `department_code` (e.g. 'HEALTH') or null."""

    password = serializers.CharField(write_only=True, min_length=8)
    department_code = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "role", "language", "department_code"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        dept_code = (validated_data.pop("department_code", "") or "").strip().upper()
        dept = Department.objects.filter(code=dept_code).first() if dept_code else None
        user = User.objects.create_user(password=password, department=dept, **validated_data)
        return user


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Issues JWT with custom claims (`role`, `department_id`, `department_code`)
    so downstream services can authorize without re-querying the DB."""

    username_field = User.USERNAME_FIELD

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["department_id"] = user.department_id
        token["department_code"] = user.department.code if user.department_id else None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class TokenWithUserSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()

    @staticmethod
    def for_user(user: User):
        # Mirror the custom-claim injection so registration responses match login.
        refresh = RefreshToken.for_user(user)
        refresh["role"] = user.role
        refresh["department_id"] = user.department_id
        refresh["department_code"] = user.department.code if user.department_id else None
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        }
