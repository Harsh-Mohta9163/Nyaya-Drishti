from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Department
from .serializers import (
    DepartmentSerializer,
    EmailTokenObtainPairSerializer,
    RegisterSerializer,
    TokenWithUserSerializer,
    UserSerializer,
)


class _NoPagination(PageNumberPagination):
    """The dept list is small (48 rows) — frontend wants the whole list at once."""
    page_size = 100


class DepartmentListView(generics.ListAPIView):
    """GET /api/auth/departments/ — list all 48 active departments.

    Public-readable so the registration page can populate its dept dropdown
    before the user has a JWT.
    """
    queryset = Department.objects.filter(is_active=True).order_by("sector", "name")
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = _NoPagination


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(TokenWithUserSerializer.for_user(user), status=201)


class LoginView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
