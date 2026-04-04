from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from shared.responses import success_response, created_response, error_response
from .models import Role, Permission
from .serializers import (
    UserSerializer, RegisterSerializer, RoleSerializer,
    PermissionSerializer, ChangePasswordSerializer, CustomTokenObtainPairSerializer,
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Auto-assign "customer" role on registration
        try:
            customer_role = Role.objects.get(name="customer")
            user.roles.add(customer_role)
        except Role.DoesNotExist:
            pass  # Roles not seeded yet — harmless, assign later

        return created_response(
            data=UserSerializer(user).data,
            message="User registered successfully.",
        )


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return success_response(message="Password changed successfully.")


class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return success_response(message="Logged out successfully.")
        except Exception:
            return error_response(message="Invalid token.", status_code=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-created_at")
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=["post"], url_path="assign-role")
    def assign_role(self, request, pk=None):
        user = self.get_object()
        role_id = request.data.get("role_id")
        try:
            role = Role.objects.get(id=role_id)
            user.roles.add(role)
            return success_response(
                data=UserSerializer(user).data,
                message=f"Role '{role.name}' assigned.",
            )
        except Role.DoesNotExist:
            return error_response(message="Role not found.", status_code=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["post"], url_path="remove-role")
    def remove_role(self, request, pk=None):
        user = self.get_object()
        role_id = request.data.get("role_id")
        try:
            role = Role.objects.get(id=role_id)
            user.roles.remove(role)
            return success_response(message=f"Role '{role.name}' removed.")
        except Role.DoesNotExist:
            return error_response(message="Role not found.", status_code=status.HTTP_404_NOT_FOUND)


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().prefetch_related("permissions")
    serializer_class = RoleSerializer
    permission_classes = [IsAdminUser]


class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAdminUser]
