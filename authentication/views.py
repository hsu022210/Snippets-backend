import os
import logging
from rest_framework import generics, permissions, status
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

# Set up logging
logger = logging.getLogger(__name__)

User = get_user_model()

# Create your views here.

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            return Response({
                "message": "User registered successfully",
                "user": response.data
            }, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as e:
            return Response({"detail": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer):
        user = serializer.save()
        # Send welcome email
        try:
            send_welcome_email(user.email, user.username)
        except Exception as e:
            # Log the error but don't fail the registration
            logger.error(f"Failed to send welcome email: {str(e)}")
        return user


class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            # Simply return a success response as JWT tokens are stateless
            # The client should handle token removal
            return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CustomLoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {"error": "Please provide both email and password."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                refresh = RefreshToken.for_user(user)
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                })
            else:
                return Response(
                    {"error": "Invalid credentials."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED
            )


class CustomPasswordResetRequest(ResetPasswordRequestToken):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # Get the token
            email = request.data.get('email')
            token = ResetPasswordToken.objects.filter(user__email=email).first()
            
            if token:
                # Prepare email context
                reset_url = f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/reset-password/{token.key}"
                context = {
                    'reset_url': reset_url,
                    'email': email
                }
                
                # Render email templates
                html_message = render_to_string('email/password_reset_request.html', context)
                plain_message = strip_tags(html_message)
                
                # Send email
                send_mail(
                    subject='Password Reset Request - Code Snippets',
                    message=plain_message,
                    html_message=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
        return response


class CustomPasswordResetConfirm(ResetPasswordConfirm):
    def post(self, request, *args, **kwargs):
        logger.info("Starting password reset confirmation process")
        logger.info(f"Request data: {request.data}")
        
        # Get token from request data before calling super()
        token = request.data.get('token')
        if not token:
            logger.error("No token provided in request")
            return Response(
                {"error": "Token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Get user email from token before password reset
        reset_token = ResetPasswordToken.objects.filter(key=token).first()
        if not reset_token:
            logger.error(f"No reset token found for token: {token}")
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        email = reset_token.user.email
        logger.info(f"Found user email: {email}")
        
        # Call super() to perform the actual password reset
        response = super().post(request, *args, **kwargs)
        logger.info(f"Super response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                # Prepare email context
                context = {
                    'frontend_url': os.environ.get('FRONTEND_URL', 'http://localhost:3000'),
                    'email': email
                }
                logger.info(f"Email context prepared: {context}")
                
                # Render email templates
                html_message = render_to_string('email/password_reset_confirm.html', context)
                plain_message = strip_tags(html_message)
                logger.info("Email templates rendered successfully")
                
                # Send confirmation email
                logger.info(f"Attempting to send email to: {email}")
                logger.info(f"From email: {settings.DEFAULT_FROM_EMAIL}")
                logger.info(f"Email settings: HOST={settings.EMAIL_HOST}, PORT={settings.EMAIL_PORT}, USE_TLS={settings.EMAIL_USE_TLS}")
                
                send_mail(
                    subject='Password Reset Successful - Code Snippets',
                    message=plain_message,
                    html_message=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                logger.info("Confirmation email sent successfully")
            except Exception as e:
                logger.error(f"Error sending confirmation email: {str(e)}", exc_info=True)
                # Don't return error to user since password was already reset
        else:
            logger.warning(f"Password reset confirmation failed with status: {response.status_code}")
            logger.warning(f"Response data: {response.data}")
            
        return response
