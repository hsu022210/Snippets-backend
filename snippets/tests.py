"""Test suite for the Snippets API."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Snippet


class SnippetTests(TestCase):
    """Test suite for Snippet-related functionality."""

    def setUp(self):
        """Set up test data and authentication."""
        self.client = APIClient()
        
        # Clean up any existing data
        Snippet.objects.all().delete()
        User.objects.all().delete()
        
        # Create users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='password1'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='password2'
        )
        
        # Create snippets
        self.snippet1 = Snippet.objects.create(
            title='Snippet 1',
            code='print("Hello")',
            owner=self.user1
        )
        self.snippet2 = Snippet.objects.create(
            title='Snippet 2',
            code='print("World")',
            owner=self.user2
        )
        
        # Create JWT tokens
        refresh1 = RefreshToken.for_user(self.user1)
        self.token1 = f'Bearer {refresh1.access_token}'
        
        refresh2 = RefreshToken.for_user(self.user2)
        self.token2 = f'Bearer {refresh2.access_token}'

    # List tests
    def test_list_snippets_authenticated(self):
        """Test listing snippets when authenticated - should only show user's own snippets."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get('/snippets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Snippet 1')

    def test_list_snippets_unauthenticated(self):
        """Test listing snippets without authentication."""
        response = self.client.get('/snippets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)  # Unauthenticated users see no snippets

    def test_list_snippets_pagination(self):
        """Test snippet list pagination."""
        # Create 15 snippets for user1
        for i in range(15):
            Snippet.objects.create(
                title=f'Pagination Test {i}',
                code=f'print("Test {i}")',
                owner=self.user1
            )
        
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get('/snippets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Default page size
        self.assertTrue('next' in response.data)
        self.assertTrue('previous' in response.data)

    # Create tests
    def test_create_snippet_authenticated(self):
        """Test creating a new snippet when authenticated."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        data = {
            'title': 'New Snippet',
            'code': 'console.log("New")',
            'language': 'javascript'
        }
        response = self.client.post('/snippets/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Snippet.objects.count(), 3)
        self.assertTrue(Snippet.objects.filter(title='New Snippet').exists())

    def test_create_snippet_unauthenticated(self):
        """Test creating a snippet without authentication."""
        data = {'title': 'Unauthorized', 'code': 'test'}
        response = self.client.post('/snippets/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_snippet_invalid_data(self):
        """Test creating a snippet with invalid data."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        data = {
            'code': ''    # Empty code
        }
        response = self.client.post('/snippets/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('code', response.data)

    # Retrieve tests
    def test_retrieve_snippet_owner(self):
        """Test retrieving a snippet by its owner."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get(f'/snippets/{self.snippet1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Snippet 1')

    def test_retrieve_snippet_non_owner(self):
        """Test retrieving a snippet by a non-owner."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get(f'/snippets/{self.snippet2.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_nonexistent_snippet(self):
        """Test retrieving a snippet that doesn't exist."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get('/snippets/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Update tests
    def test_update_snippet_owner(self):
        """Test updating a snippet by its owner."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        data = {'title': 'Updated Snippet'}
        response = self.client.patch(f'/snippets/{self.snippet1.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.snippet1.refresh_from_db()
        self.assertEqual(self.snippet1.title, 'Updated Snippet')

    def test_update_snippet_non_owner(self):
        """Test updating a snippet by a non-owner."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        data = {'title': 'Should Not Update'}
        response = self.client.patch(f'/snippets/{self.snippet2.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_snippet_invalid_data(self):
        """Test updating a snippet with invalid data."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        data = {
            'code': ''    # Empty code
        }
        response = self.client.patch(f'/snippets/{self.snippet1.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('code', response.data)

    # Delete tests
    def test_delete_snippet_owner(self):
        """Test deleting a snippet by its owner."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.delete(f'/snippets/{self.snippet1.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Snippet.objects.count(), 1)

    def test_delete_snippet_non_owner(self):
        """Test deleting a snippet by a non-owner."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.delete(f'/snippets/{self.snippet2.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Snippet.objects.count(), 2)

    def test_delete_nonexistent_snippet(self):
        """Test deleting a snippet that doesn't exist."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.delete('/snippets/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Special action tests
    def test_snippet_highlight(self):
        """Test the snippet highlight action."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get(f'/snippets/{self.snippet1.id}/highlight/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('<span class="nb">print</span>', response.content.decode())
        self.assertIn('<span class="s2">&quot;Hello&quot;</span>', response.content.decode())

    def test_snippet_highlight_nonexistent(self):
        """Test highlighting a snippet that doesn't exist."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get('/snippets/99999/highlight/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UserViewTests(TestCase):
    """Test suite for User-related functionality."""

    def setUp(self):
        """Set up test data and authentication."""
        self.client = APIClient()
        # Clean up any existing data
        User.objects.all().delete()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        # Authenticate client
        refresh = RefreshToken.for_user(self.user)
        self.token = f'Bearer {refresh.access_token}'

    def test_user_list(self):
        """Test listing users."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token)
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['username'], 'testuser')

    def test_user_list_pagination(self):
        """Test user list pagination."""
        # Create 15 users
        for i in range(15):
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='password'
            )
        
        self.client.credentials(HTTP_AUTHORIZATION=self.token)
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Default page size
        self.assertTrue('next' in response.data)
        self.assertTrue('previous' in response.data)

    def test_user_detail(self):
        """Test retrieving user details."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token)
        response = self.client.get(f'/users/{self.user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')

    def test_user_detail_nonexistent(self):
        """Test retrieving details of a non-existent user."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token)
        response = self.client.get('/users/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_detail_invalid_id(self):
        """Test retrieving user details with an invalid ID."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token)
        response = self.client.get('/users/invalid/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
