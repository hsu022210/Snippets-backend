import os
import logging
from typing import Dict, Any, Optional

from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, RegisterSerializer
from rest_framework.views import APIView
from .utils import send_welcome_email
from django_rest_passwordreset.views import ResetPasswordRequestToken, ResetPasswordConfirm
from django_rest_passwordreset.models import ResetPasswordToken
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from rest_framework.renderers import JSONRenderer
from .schemas import (
    REGISTER_SCHEMA,
    USER_PROFILE_SCHEMA,
    LOGOUT_SCHEMA,
    LOGIN_SCHEMA,
    TOKEN_REFRESH_SCHEMA,
    PASSWORD_RESET_REQUEST_SCHEMA,
    PASSWORD_RESET_CONFIRM_SCHEMA,
)
from rest_framework_simplejwt.views import TokenRefreshView

# Set up logging
logger = logging.getLogger(__name__)

# Constants
User = get_user_model()
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
EMAIL_SUBJECTS = {
    'password_reset_request': 'Password Reset Request - Code Snippets',
    'password_reset_confirm': 'Password Reset Successful - Code Snippets',
}
EMAIL_TEMPLATES = {
    'password_reset_request': 'email/password_reset_request.html',
    'password_reset_confirm': 'email/password_reset_confirm.html',
}


class AuthenticationMixin:
    """Mixin providing common authentication utility methods."""
    
    @staticmethod
    def create_error_response(message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> Response:
        """Create a standardized error response."""
        return Response({"error": message}, status=status_code)
    
    @staticmethod
    def create_success_response(data: Dict[str, Any], status_code: int = status.HTTP_200_OK) -> Response:
        """Create a standardized success response."""
        return Response(data, status=status_code)
    
    @staticmethod
    def send_email_notification(
        email: str, 
        subject: str, 
        template_name: str, 
        context: Dict[str, Any]
    ) -> bool:
        """
        Send an email notification using the specified template.
        
        Args:
            email: Recipient email address
            subject: Email subject
            template_name: Template name to render
            context: Context data for template rendering
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            html_message = render_to_string(template_name, context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            logger.info(f"Email sent successfully to {email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {str(e)}", exc_info=True)
            return False


@REGISTER_SCHEMA
class RegisterView(generics.CreateAPIView, AuthenticationMixin):
    """View for user registration."""
    
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer
    renderer_classes = [JSONRenderer]

    def create(self, request, *args, **kwargs):
        """Handle user registration with proper error handling."""
        try:
            response = super().create(request, *args, **kwargs)
            return self.create_success_response({
                "message": "User registered successfully",
                "user": response.data
            }, status.HTTP_201_CREATED)
        except serializers.ValidationError as e:
            return Response({"detail": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Registration failed. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer):
        """Create user and send welcome email."""
        user = serializer.save()
        self._send_welcome_email(user)
        return user
    
    def _send_welcome_email(self, user) -> None:
        """Send welcome email to newly registered user."""
        try:
            send_welcome_email(user.email, user.username)
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")


@USER_PROFILE_SCHEMA
class UserDetailView(generics.RetrieveUpdateAPIView):
    """View for retrieving and updating user details."""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        """Return the authenticated user."""
        return self.request.user


@LOGOUT_SCHEMA
class LogoutView(APIView, AuthenticationMixin):
    """View for user logout."""
    
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        """Handle user logout."""
        try:
            # JWT tokens are stateless, so we just return success
            # Client should handle token removal
            return self.create_success_response({
                "message": "Successfully logged out."
            })
        except Exception as e:
            logger.error(f"Logout error: {str(e)}", exc_info=True)
            return self.create_error_response("Logout failed", status.HTTP_400_BAD_REQUEST)


@LOGIN_SCHEMA
class CustomLoginView(APIView, AuthenticationMixin):
    """View for user login with JWT token generation."""
    
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        """Handle user login and return JWT tokens."""
        email = request.data.get('email')
        password = request.data.get('password')

        if not self._validate_login_credentials(email, password):
            return self.create_error_response(
                "Please provide both email and password.",
                status.HTTP_400_BAD_REQUEST
            )

        user = self._authenticate_user(email, password)
        if not user:
            return self.create_error_response(
                "Invalid credentials.",
                status.HTTP_401_UNAUTHORIZED
            )

        return self._generate_token_response(user)
    
    def _validate_login_credentials(self, email: str, password: str) -> bool:
        """Validate that both email and password are provided."""
        return bool(email and password)
    
    def _authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            pass
        return None
    
    def _generate_token_response(self, user: User) -> Response:
        """Generate and return JWT tokens for authenticated user."""
        refresh = RefreshToken.for_user(user)
        return self.create_success_response({
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        })


@TOKEN_REFRESH_SCHEMA
class CustomTokenRefreshView(TokenRefreshView):
    """Custom JWT token refresh view with proper schema documentation."""
    
    permission_classes = (permissions.AllowAny,)


@PASSWORD_RESET_REQUEST_SCHEMA
class CustomPasswordResetRequest(ResetPasswordRequestToken, AuthenticationMixin):
    """View for requesting password reset with custom email handling."""
    
    def post(self, request, *args, **kwargs):
        """Handle password reset request and send email."""
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            self._send_password_reset_email(request.data.get('email'))
        
        return response
    
    def _send_password_reset_email(self, email: str) -> None:
        """Send password reset email with reset link."""
        token = ResetPasswordToken.objects.filter(user__email=email).first()
        
        if not token:
            logger.warning(f"No reset token found for email: {email}")
            return
        
        reset_url = f"{FRONTEND_URL}/reset-password/{token.key}"
        context = {
            'reset_url': reset_url,
            'email': email
        }
        
        self.send_email_notification(
            email=email,
            subject=EMAIL_SUBJECTS['password_reset_request'],
            template_name=EMAIL_TEMPLATES['password_reset_request'],
            context=context
        )


@PASSWORD_RESET_CONFIRM_SCHEMA
class CustomPasswordResetConfirm(ResetPasswordConfirm, AuthenticationMixin):
    """View for confirming password reset with custom email handling."""
    
    def post(self, request, *args, **kwargs):
        """Handle password reset confirmation and send confirmation email."""
        logger.info("Starting password reset confirmation process")
        
        # Validate token before proceeding
        token = request.data.get('token')
        if not token:
            logger.error("No token provided in request")
            return self.create_error_response("Token is required")
        
        # Get user email from token
        reset_token = self._get_reset_token(token)
        if not reset_token:
            return self.create_error_response("Invalid or expired token")
        
        email = reset_token.user.email
        logger.info(f"Processing password reset for user: {email}")
        
        # Perform password reset
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            self._send_password_reset_confirmation_email(email)
        else:
            logger.warning(f"Password reset failed with status: {response.status_code}")
        
        return response
    
    def _get_reset_token(self, token: str) -> Optional[ResetPasswordToken]:
        """Get reset token from database."""
        reset_token = ResetPasswordToken.objects.filter(key=token).first()
        if not reset_token:
            logger.error(f"No reset token found for token: {token}")
        return reset_token
    
    def _send_password_reset_confirmation_email(self, email: str) -> None:
        """Send password reset confirmation email."""
        context = {
            'frontend_url': FRONTEND_URL,
            'email': email
        }
        
        success = self.send_email_notification(
            email=email,
            subject=EMAIL_SUBJECTS['password_reset_confirm'],
            template_name=EMAIL_TEMPLATES['password_reset_confirm'],
            context=context
        )
        
        if success:
            logger.info(f"Password reset confirmation email sent to {email}")
        else:
            logger.error(f"Failed to send password reset confirmation email to {email}")
