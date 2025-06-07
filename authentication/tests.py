"""Test suite for authentication functionality."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


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
        self.assertIn('password', response.data)

    def test_register_missing_required_fields(self):
        """Test registration with missing required fields."""
        data = {
            'username': 'newuser',
            'password': 'newuserpassword',
            # Missing email and password2
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('password2', response.data)


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
