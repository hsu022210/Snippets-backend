"""Test suite for the Snippets API."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Snippet
from unittest.mock import patch
from datetime import datetime, timedelta
from django.urls import reverse

User = get_user_model()


class SnippetTestMixin:
    """Mixin providing common snippet test functionality."""
    
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


class SnippetListTests(SnippetTestMixin, TestCase):
    """Test suite for snippet list functionality."""

    def setUp(self):
        """Set up test data and authentication."""
        super().setUp()
        self.url = '/snippets/'

    def test_list_snippets_authenticated(self):
        """Test listing snippets when authenticated - should only show user's own snippets."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Snippet 1')

    def test_list_snippets_unauthenticated(self):
        """Test listing snippets without authentication."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Should see all snippets
        self.assertEqual(response.data['results'][0]['title'], 'Snippet 2')
        self.assertEqual(response.data['results'][1]['title'], 'Snippet 1')

    def test_list_snippets_pagination(self):
        """Test snippet list pagination with default page size."""
        # Create 15 snippets for user1
        for i in range(15):
            Snippet.objects.create(
                title=f'Pagination Test {i}',
                code=f'print("Test {i}")',
                owner=self.user1
            )
        
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Default page size
        self.assertTrue('next' in response.data)
        self.assertTrue('previous' in response.data)

    def test_list_snippets_custom_page_size(self):
        """Test snippet list pagination with custom page size."""
        # Create 15 snippets for user1
        for i in range(15):
            Snippet.objects.create(
                title=f'Custom Page Size Test {i}',
                code=f'print("Test {i}")',
                owner=self.user1
            )
        
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get(f'{self.url}?page_size=6')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 6)  # Custom page size
        self.assertTrue('next' in response.data)
        self.assertTrue('previous' in response.data)

    def test_list_snippets_page_size_limits(self):
        """Test snippet list pagination with page size limits."""
        # Create 150 snippets for user1 to test max page size
        for i in range(150):
            Snippet.objects.create(
                title=f'Page Size Limits Test {i}',
                code=f'print("Test {i}")',
                owner=self.user1
            )
        
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        
        # Test minimum page size (should use default)
        response = self.client.get(f'{self.url}?page_size=0')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Default page size
        
        # Test maximum page size
        response = self.client.get(f'{self.url}?page_size=101')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 100)  # Max page size

    def test_list_snippets_pagination_with_filters(self):
        """Test snippet list pagination with filters."""
        # Create 15 snippets for user1 with different languages
        for i in range(15):
            Snippet.objects.create(
                title=f'Filtered Pagination Test {i}',
                code=f'print("Test {i}")',
                language='python' if i % 2 == 0 else 'javascript',
                owner=self.user1
            )
        
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get(f'{self.url}?language=python&page_size=6')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 6)  # Custom page size
        self.assertTrue(all(s['language'] == 'python' for s in response.data['results']))
        self.assertTrue('next' in response.data)
        self.assertTrue('previous' in response.data)

    def test_list_snippets_filter_by_language(self):
        """Test filtering snippets by language."""
        # Create snippets with different languages
        Snippet.objects.create(
            title='Python Snippet',
            code='print("Hello")',
            language='python',
            owner=self.user1
        )
        Snippet.objects.create(
            title='JavaScript Snippet',
            code='console.log("Hello")',
            language='javascript',
            owner=self.user1
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get(f'{self.url}?language=python')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Original + new python snippet
        self.assertTrue(all(s['language'] == 'python' for s in response.data['results']))

    def test_list_snippets_filter_by_created_after(self):
        """Test filtering snippets by creation date (after)."""
        # Create a snippet with specific creation time
        old_time = datetime.now() - timedelta(days=2)
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = old_time
            Snippet.objects.create(
                title='Old Snippet',
                code='print("Old")',
                owner=self.user1
            )
        
        # Create a new snippet
        Snippet.objects.create(
            title='New Snippet',
            code='print("New")',
            owner=self.user1
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.get(f'{self.url}?created_after={yesterday}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Original + new snippet
        self.assertTrue(all('New' in s['title'] or 'Snippet 1' in s['title'] for s in response.data['results']))

    def test_list_snippets_filter_by_created_before(self):
        """Test filtering snippets by creation date (before)."""
        # Create a snippet with specific creation time
        old_time = datetime.now() - timedelta(days=2)
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = old_time
            Snippet.objects.create(
                title='Old Snippet',
                code='print("Old")',
                owner=self.user1
            )
        
        # Create a new snippet
        Snippet.objects.create(
            title='New Snippet',
            code='print("New")',
            owner=self.user1
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.get(f'{self.url}?created_before={yesterday}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only old snippet
        self.assertEqual(response.data['results'][0]['title'], 'Old Snippet')

    def test_list_snippets_search_by_title(self):
        """Test searching snippets by title."""
        Snippet.objects.create(
            title='Search Test Title',
            code='print("Search")',
            owner=self.user1
        )
        Snippet.objects.create(
            title='Another Snippet',
            code='print("Another")',
            owner=self.user1
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get(f'{self.url}?search_title=Search')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Search Test Title')

    def test_list_snippets_search_by_code(self):
        """Test searching snippets by code content."""
        Snippet.objects.create(
            title='Code Search Test',
            code='def search_function(): return "found"',
            owner=self.user1
        )
        Snippet.objects.create(
            title='Another Snippet',
            code='print("Another")',
            owner=self.user1
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get(f'{self.url}?search_code=search_function')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Code Search Test')

    def test_list_snippets_multiple_filters(self):
        """Test filtering snippets with multiple criteria."""
        Snippet.objects.create(
            title='Python Search Test',
            code='def search_function(): return "found"',
            language='python',
            owner=self.user1
        )
        Snippet.objects.create(
            title='JavaScript Search Test',
            code='function searchFunction() { return "found"; }',
            language='javascript',
            owner=self.user1
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get(f'{self.url}?language=python&search_code=search_function')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Python Search Test')

    def test_list_snippets_invalid_filter_values(self):
        """Test handling of invalid filter values."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get(f'{self.url}?page_size=invalid')
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Should handle gracefully

    def test_list_snippets_empty_results(self):
        """Test listing snippets when no snippets match filters."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get(f'{self.url}?language=nonexistent')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)


class SnippetCreateTests(SnippetTestMixin, TestCase):
    """Test suite for snippet creation functionality."""

    def setUp(self):
        """Set up test data and authentication."""
        super().setUp()
        self.url = '/snippets/'

    def test_create_snippet_authenticated(self):
        """Test creating a new snippet when authenticated."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        data = {
            'title': 'New Snippet',
            'code': 'console.log("New")',
            'language': 'javascript'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Snippet.objects.count(), 3)
        self.assertTrue(Snippet.objects.filter(title='New Snippet').exists())

    def test_create_snippet_unauthenticated(self):
        """Test creating a snippet without authentication."""
        data = {'title': 'Unauthorized', 'code': 'test'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_snippet_invalid_data(self):
        """Test creating a snippet with invalid data."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        data = {
            'code': ''    # Empty code
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('code', response.data)

    def test_create_snippet_with_all_fields(self):
        """Test creating a snippet with all available fields."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        data = {
            'title': 'Complete Snippet',
            'code': 'print("Complete")',
            'language': 'python',
            'style': 'monokai',
            'linenos': True
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        snippet = Snippet.objects.get(title='Complete Snippet')
        self.assertEqual(snippet.language, 'python')
        self.assertEqual(snippet.style, 'monokai')
        self.assertTrue(snippet.linenos)

    def test_create_snippet_without_title(self):
        """Test creating a snippet without a title (should use default)."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        data = {
            'code': 'print("No Title")'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        snippet = Snippet.objects.get(code='print("No Title")')
        self.assertEqual(snippet.title, '')  # Default empty title

    def test_create_snippet_invalid_language(self):
        """Test creating a snippet with invalid language."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        data = {
            'title': 'Invalid Language',
            'code': 'print("test")',
            'language': 'invalid_language'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('language', response.data)

    def test_create_snippet_invalid_style(self):
        """Test creating a snippet with invalid style."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        data = {
            'title': 'Invalid Style',
            'code': 'print("test")',
            'style': 'invalid_style'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('style', response.data)

    def test_create_snippet_owner_assignment(self):
        """Test that the snippet owner is correctly assigned."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        data = {
            'title': 'Owner Test',
            'code': 'print("Owner")'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        snippet = Snippet.objects.get(title='Owner Test')
        self.assertEqual(snippet.owner, self.user1)


class SnippetDetailTests(SnippetTestMixin, TestCase):
    """Test suite for snippet detail functionality."""

    def setUp(self):
        """Set up test data and authentication."""
        super().setUp()
        self.url = f'/snippets/{self.snippet1.id}/'

    def test_retrieve_snippet_owner(self):
        """Test retrieving a snippet by its owner."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Snippet 1')

    def test_retrieve_snippet_non_owner(self):
        """Test retrieving a snippet by a non-owner."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token2)
        response = self.client.get(f'/snippets/{self.snippet1.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_nonexistent_snippet(self):
        """Test retrieving a snippet that doesn't exist."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get('/snippets/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_snippet_owner(self):
        """Test updating a snippet by its owner."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        data = {'title': 'Updated Title', 'code': 'print("Updated")'}
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.snippet1.refresh_from_db()
        self.assertEqual(self.snippet1.title, 'Updated Title')

    def test_update_snippet_non_owner(self):
        """Test updating a snippet by a non-owner."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token2)
        data = {'title': 'Unauthorized Update'}
        response = self.client.put(f'/snippets/{self.snippet1.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_snippet_invalid_data(self):
        """Test updating a snippet with invalid data."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        data = {'code': ''}  # Empty code
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('code', response.data)

    def test_delete_snippet_owner(self):
        """Test deleting a snippet by its owner."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Snippet.objects.filter(id=self.snippet1.id).exists())

    def test_delete_snippet_non_owner(self):
        """Test deleting a snippet by a non-owner."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token2)
        response = self.client.delete(f'/snippets/{self.snippet1.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_nonexistent_snippet(self):
        """Test deleting a snippet that doesn't exist."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.delete('/snippets/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_partial_update_snippet(self):
        """Test partial update of a snippet."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        data = {'title': 'Partially Updated'}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.snippet1.refresh_from_db()
        self.assertEqual(self.snippet1.title, 'Partially Updated')
        self.assertEqual(self.snippet1.code, 'print("Hello")')  # Code unchanged

    def test_update_snippet_all_fields(self):
        """Test updating all fields of a snippet."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        data = {
            'title': 'Fully Updated',
            'code': 'print("Fully Updated")',
            'language': 'javascript',
            'style': 'monokai',
            'linenos': True
        }
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.snippet1.refresh_from_db()
        self.assertEqual(self.snippet1.title, 'Fully Updated')
        self.assertEqual(self.snippet1.code, 'print("Fully Updated")')
        self.assertEqual(self.snippet1.language, 'javascript')
        self.assertEqual(self.snippet1.style, 'monokai')
        self.assertTrue(self.snippet1.linenos)

    def test_retrieve_snippet_unauthenticated(self):
        """Test retrieving a snippet without authentication."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Unauthenticated users can see all snippets

    def test_update_snippet_unauthenticated(self):
        """Test updating a snippet without authentication."""
        data = {'title': 'Unauthorized'}
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_snippet_unauthenticated(self):
        """Test deleting a snippet without authentication."""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SnippetHighlightTests(SnippetTestMixin, TestCase):
    """Test suite for snippet highlight functionality."""

    def setUp(self):
        """Set up test data and authentication."""
        super().setUp()
        self.url = f'/snippets/{self.snippet1.id}/highlight/'

    def test_snippet_highlight(self):
        """Test the snippet highlight action."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The highlight endpoint returns HTML content, not JSON
        self.assertIn('highlight', response.content.decode())

    def test_snippet_highlight_nonexistent(self):
        """Test highlighting a snippet that doesn't exist."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get('/snippets/99999/highlight/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_snippet_highlight_unauthenticated(self):
        """Test highlighting a snippet without authentication."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Unauthenticated users can see highlights

    def test_snippet_highlight_non_owner(self):
        """Test highlighting a snippet by non-owner."""
        self.client.credentials(HTTP_AUTHORIZATION=self.token2)
        response = self.client.get(f'/snippets/{self.snippet1.id}/highlight/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_snippet_highlight_with_different_languages(self):
        """Test highlighting snippets with different languages."""
        # Create snippets with different languages
        python_snippet = Snippet.objects.create(
            title='Python Highlight',
            code='def hello(): return "world"',
            language='python',
            owner=self.user1
        )
        js_snippet = Snippet.objects.create(
            title='JavaScript Highlight',
            code='function hello() { return "world"; }',
            language='javascript',
            owner=self.user1
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        
        # Test Python highlighting
        response = self.client.get(f'/snippets/{python_snippet.id}/highlight/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('highlight', response.content.decode())
        
        # Test JavaScript highlighting
        response = self.client.get(f'/snippets/{js_snippet.id}/highlight/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('highlight', response.content.decode())

    def test_snippet_highlight_with_linenos(self):
        """Test highlighting snippets with line numbers."""
        snippet_with_linenos = Snippet.objects.create(
            title='Linenos Test',
            code='line1\nline2\nline3',
            language='python',
            linenos=True,
            owner=self.user1
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=self.token1)
        response = self.client.get(f'/snippets/{snippet_with_linenos.id}/highlight/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('highlight', response.content.decode())


class UserViewTests(TestCase):
    """Test suite for user view functionality."""

    def setUp(self):
        """Set up test data and authentication."""
        self.client = APIClient()
        
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
        
        # Create JWT token
        refresh = RefreshToken.for_user(self.user1)
        self.token = f'Bearer {refresh.access_token}'
        self.client.credentials(HTTP_AUTHORIZATION=self.token)

    def test_user_list(self):
        """Test listing users."""
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_user_list_pagination(self):
        """Test user list pagination."""
        # Create additional users
        for i in range(15):
            User.objects.create_user(
                username=f'user{i+3}',
                email=f'user{i+3}@example.com',
                password=f'password{i+3}'
            )
        
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Default page size
        self.assertTrue('next' in response.data)
        self.assertTrue('previous' in response.data)

    def test_user_detail(self):
        """Test retrieving user details."""
        response = self.client.get(f'/users/{self.user1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'user1')

    def test_user_detail_nonexistent(self):
        """Test retrieving details of a non-existent user."""
        response = self.client.get('/users/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_detail_invalid_id(self):
        """Test retrieving user details with an invalid ID."""
        response = self.client.get('/users/invalid/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_detail_unauthenticated(self):
        """Test retrieving user details without authentication."""
        self.client.credentials()  # Remove authentication
        response = self.client.get(f'/users/{self.user1.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list_unauthenticated(self):
        """Test listing users without authentication."""
        self.client.credentials()  # Remove authentication
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_detail_wrong_method(self):
        """Test user detail with wrong HTTP method."""
        response = self.client.post(f'/users/{self.user1.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_user_list_wrong_method(self):
        """Test user list with wrong HTTP method."""
        response = self.client.post('/users/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class SnippetModelTests(TestCase):
    """Test suite for Snippet model functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

    def test_snippet_creation(self):
        """Test basic snippet creation."""
        snippet = Snippet.objects.create(
            title='Test Snippet',
            code='print("Hello")',
            owner=self.user
        )
        self.assertEqual(snippet.title, 'Test Snippet')
        self.assertEqual(snippet.code, 'print("Hello")')
        self.assertEqual(snippet.owner, self.user)
        self.assertEqual(snippet.language, 'python')  # Default
        self.assertEqual(snippet.style, 'friendly')  # Default
        self.assertFalse(snippet.linenos)  # Default

    def test_snippet_highlighted_generation(self):
        """Test that highlighted HTML is generated on save."""
        snippet = Snippet.objects.create(
            title='Highlight Test',
            code='def hello(): return "world"',
            language='python',
            owner=self.user
        )
        self.assertIsNotNone(snippet.highlighted)
        self.assertIn('<pre', snippet.highlighted)
        self.assertIn('def', snippet.highlighted)

    def test_snippet_highlighted_with_linenos(self):
        """Test highlighted HTML generation with line numbers."""
        snippet = Snippet.objects.create(
            title='Linenos Test',
            code='line1\nline2\nline3',
            language='python',
            linenos=True,
            owner=self.user
        )
        self.assertIsNotNone(snippet.highlighted)
        self.assertIn('table', snippet.highlighted)  # Should use table format for line numbers

    def test_snippet_highlighted_with_style(self):
        """Test highlighted HTML generation with custom style."""
        snippet = Snippet.objects.create(
            title='Style Test',
            code='print("Style")',
            language='python',
            style='monokai',
            owner=self.user
        )
        self.assertIsNotNone(snippet.highlighted)
        # Check for monokai style characteristics in the CSS
        self.assertIn('background: #272822', snippet.highlighted)

    def test_snippet_ordering(self):
        """Test that snippets are ordered by creation date (newest first)."""
        snippet1 = Snippet.objects.create(
            title='First',
            code='print("First")',
            owner=self.user
        )
        snippet2 = Snippet.objects.create(
            title='Second',
            code='print("Second")',
            owner=self.user
        )
        
        snippets = Snippet.objects.all()
        self.assertEqual(snippets[0], snippet2)  # Newest first
        self.assertEqual(snippets[1], snippet1)

    def test_snippet_string_representation(self):
        """Test snippet string representation."""
        snippet = Snippet.objects.create(
            title='String Test',
            code='print("String")',
            owner=self.user
        )
        # Django's default string representation is "ModelName object (id)"
        self.assertEqual(str(snippet), f'Snippet object ({snippet.id})')

    def test_snippet_without_title(self):
        """Test snippet creation without title."""
        snippet = Snippet.objects.create(
            code='print("No Title")',
            owner=self.user
        )
        self.assertEqual(snippet.title, '')
        # Django's default string representation doesn't depend on title
        self.assertEqual(str(snippet), f'Snippet object ({snippet.id})')


class ContactEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('contact')

    @patch('snippets.views.send_mail')
    def test_contact_valid_submission(self, mock_send_mail):
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'Test Subject',
            'message': 'Hello, this is a test.'
        }
        mock_send_mail.return_value = 1
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('detail', response.data)
        mock_send_mail.assert_called_once()

    def test_contact_missing_fields(self):
        data = {
            'name': '',
            'email': '',
            'subject': '',
            'message': ''
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('name', response.data)
        self.assertIn('email', response.data)
        self.assertIn('subject', response.data)
        self.assertIn('message', response.data)

    def test_contact_invalid_email(self):
        data = {
            'name': 'Test User',
            'email': 'not-an-email',
            'subject': 'Test',
            'message': 'Test message'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)
