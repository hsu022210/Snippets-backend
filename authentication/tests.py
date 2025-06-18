"""Test suite for authentication functionality."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock
from django.core import mail
from django_rest_passwordreset.models import ResetPasswordToken

User = get_user_model()


class AuthenticationTestMixin:
    """Mixin providing common authentication test functionality."""
    
    def setUp(self):
        """Set up test data and authentication."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.access_token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')


class RegistrationTests(TestCase):
    """Test suite for user registration functionality."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        self.url = reverse('auth_register')

    def test_register_valid_user(self):
        """Test registering a new user with valid data."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newuserpassword',
            'password2': 'newuserpassword'
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_invalid_data(self):
        """Test registration with invalid data (mismatched passwords)."""
        data = {
            'username': 'invaliduser',
            'email': 'invalid@example.com',
            'password': 'password1',
            'password2': 'password2'  # Mismatched passwords
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertIn('password', response.data['detail'])

    def test_register_missing_required_fields(self):
        """Test registration with missing required fields."""
        data = {
            'username': 'newuser',
            'password': 'newuserpassword',
            # Missing email and password2
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertIn('email', response.data['detail'])
        self.assertIn('password2', response.data['detail'])

    def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        # Create a user first
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password123'
        )
        
        data = {
            'username': 'newuser',
            'email': 'existing@example.com',  # Duplicate email
            'password': 'newuserpassword',
            'password2': 'newuserpassword'
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertIn('email', response.data['detail'])

    def test_register_duplicate_username(self):
        """Test registration with duplicate username."""
        # Create a user first
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password123'
        )
        
        data = {
            'username': 'existinguser',  # Duplicate username
            'email': 'newuser@example.com',
            'password': 'newuserpassword',
            'password2': 'newuserpassword'
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertIn('username', response.data['detail'])

    def test_register_with_optional_fields(self):
        """Test registration with optional first_name and last_name fields."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newuserpassword',
            'password2': 'newuserpassword',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='newuser')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')

    @patch('authentication.views.send_welcome_email')
    def test_register_sends_welcome_email(self, mock_send_email):
        """Test that registration sends a welcome email."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newuserpassword',
            'password2': 'newuserpassword'
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_send_email.assert_called_once_with('newuser@example.com', 'newuser')

    @patch('authentication.views.send_welcome_email')
    def test_register_email_failure_doesnt_fail_registration(self, mock_send_email):
        """Test that registration succeeds even if welcome email fails."""
        mock_send_email.side_effect = Exception("Email service down")
        
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newuserpassword',
            'password2': 'newuserpassword'
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())


class CustomLoginTests(TestCase):
    """Test suite for custom login functionality."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.url = reverse('token_obtain_pair')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

    def test_login_valid_credentials(self):
        """Test login with valid email and password."""
        data = {
            'email': 'test@example.com',
            'password': 'testpassword'
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_password(self):
        """Test login with invalid password."""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_login_nonexistent_email(self):
        """Test login with non-existent email."""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'testpassword'
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_login_missing_email(self):
        """Test login with missing email."""
        data = {
            'password': 'testpassword'
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_login_missing_password(self):
        """Test login with missing password."""
        data = {
            'email': 'test@example.com'
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_login_empty_data(self):
        """Test login with empty data."""
        data = {}
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class PasswordResetTests(TestCase):
    """Test suite for password reset functionality."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

    @patch('authentication.views.send_mail')
    def test_password_reset_request_valid_email(self, mock_send_mail):
        """Test password reset request with valid email."""
        data = {'email': 'test@example.com'}
        url = reverse('password-reset')
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_send_mail.assert_called_once()

    def test_password_reset_request_invalid_email(self):
        """Test password reset request with invalid email."""
        data = {'email': 'nonexistent@example.com'}
        url = reverse('password-reset')
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # Invalid email format

    def test_password_reset_request_missing_email(self):
        """Test password reset request with missing email."""
        data = {}
        url = reverse('password-reset')
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('authentication.views.send_mail')
    def test_password_reset_confirm_valid_token(self, mock_send_mail):
        """Test password reset confirmation with valid token."""
        # Create a reset token
        token = ResetPasswordToken.objects.create(
            user=self.user,
            key='test-token-123'
        )
        
        data = {
            'token': 'test-token-123',
            'password': 'newpassword123'
        }
        url = reverse('password-reset-confirm')
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_send_mail.assert_called_once()

    def test_password_reset_confirm_missing_token(self):
        """Test password reset confirmation with missing token."""
        data = {'password': 'newpassword123'}
        url = reverse('password-reset-confirm')
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_password_reset_confirm_invalid_token(self):
        """Test password reset confirmation with invalid token."""
        data = {
            'token': 'invalid-token',
            'password': 'newpassword123'
        }
        url = reverse('password-reset-confirm')
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    @patch('authentication.views.send_mail')
    def test_password_reset_confirm_email_failure_doesnt_fail_reset(self, mock_send_mail):
        """Test that password reset succeeds even if confirmation email fails."""
        mock_send_mail.side_effect = Exception("Email service down")
        
        # Create a reset token
        token = ResetPasswordToken.objects.create(
            user=self.user,
            key='test-token-123'
        )
        
        data = {
            'token': 'test-token-123',
            'password': 'newpassword123'
        }
        url = reverse('password-reset-confirm')
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserDetailTests(AuthenticationTestMixin, TestCase):
    """Test suite for user detail functionality."""

    def setUp(self):
        """Set up test data and authentication."""
        super().setUp()
        self.url = reverse('user_detail')

    def test_user_detail_authenticated(self):
        """Test retrieving user details when authenticated."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')

    def test_user_detail_unauthenticated(self):
        """Test accessing user details without authentication."""
        self.client.credentials()  # Remove authentication
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_details(self):
        """Test updating user details."""
        data = {'email': 'updated@example.com'}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updated@example.com')

    def test_update_user_details_invalid_data(self):
        """Test updating user details with invalid data."""
        data = {'email': 'invalid-email'}  # Invalid email format
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_update_user_details_partial(self):
        """Test partial update of user details."""
        data = {'first_name': 'John'}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'John')

    def test_update_user_details_full(self):
        """Test full update of user details."""
        data = {
            'email': 'newemail@example.com',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'username': 'testuser'  # Include username for full update
        }
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')
        self.assertEqual(self.user.first_name, 'Jane')
        self.assertEqual(self.user.last_name, 'Doe')


class LogoutTests(AuthenticationTestMixin, TestCase):
    """Test suite for logout functionality."""

    def setUp(self):
        """Set up test data and authentication."""
        super().setUp()
        self.url = reverse('auth_logout')

    def test_logout_authenticated(self):
        """Test logout when authenticated."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"message": "Successfully logged out."})

    def test_logout_unauthenticated(self):
        """Test logout without authentication."""
        self.client.credentials()  # Remove authentication
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_wrong_method(self):
        """Test logout with wrong HTTP method."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class SerializerValidationTests(TestCase):
    """Test suite for serializer validation."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password123'
        )

    def test_register_serializer_validate_email_unique(self):
        """Test email uniqueness validation in RegisterSerializer."""
        from authentication.serializers import RegisterSerializer
        
        data = {
            'username': 'newuser',
            'email': 'existing@example.com',  # Duplicate email
            'password': 'newpassword123',
            'password2': 'newpassword123'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_register_serializer_validate_username_unique(self):
        """Test username uniqueness validation in RegisterSerializer."""
        from authentication.serializers import RegisterSerializer
        
        data = {
            'username': 'existinguser',  # Duplicate username
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'password2': 'newpassword123'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_register_serializer_validate_password_match(self):
        """Test password confirmation validation in RegisterSerializer."""
        from authentication.serializers import RegisterSerializer
        
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'password2': 'differentpassword'  # Mismatched passwords
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
        self.assertIn('password2', serializer.errors)

    def test_register_serializer_create_user(self):
        """Test user creation in RegisterSerializer."""
        from authentication.serializers import RegisterSerializer
        
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'password2': 'newpassword123',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        self.assertTrue(user.check_password('newpassword123'))
