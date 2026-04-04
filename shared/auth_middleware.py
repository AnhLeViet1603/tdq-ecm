import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class JWTUser:
    """Lightweight user object built from JWT claims. No DB query needed."""

    def __init__(self, payload: dict):
        self.id = payload.get("user_id")
        self.email = payload.get("email", "")
        self.full_name = payload.get("full_name", "")
        self.roles = payload.get("roles", [])
        self.is_staff = payload.get("is_staff", False)
        self.is_active = True
        self.is_authenticated = True

    def __str__(self):
        return self.email

    def has_role(self, role: str) -> bool:
        return role in self.roles


class ServiceJWTAuthentication(BaseAuthentication):
    """
    Lightweight JWT authentication for downstream microservices.
    Verifies tokens locally using the shared JWT_SECRET_KEY — no round-trip to auth service.
    """

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ", 1)[1]

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=["HS256"],
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token has expired.")
        except jwt.InvalidTokenError as exc:
            raise AuthenticationFailed(f"Invalid token: {exc}")

        return JWTUser(payload), token

    def authenticate_header(self, request):
        return "Bearer"
