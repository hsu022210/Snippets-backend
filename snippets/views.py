from django.shortcuts import render
from django_filters import rest_framework as filters
from snippets.models import Snippet
from snippets.serializers import SnippetSerializer, UserSerializer
from snippets.permissions import IsOwnerOrReadOnly
from snippets.pagination import SnippetPagination
from django.http import Http404
from rest_framework import status, renderers, generics, permissions, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, action
from rest_framework.reverse import reverse
from datetime import datetime, timedelta
from .schemas import (
    SNIPPET_LIST_SCHEMA,
    SNIPPET_CREATE_SCHEMA,
    SNIPPET_DETAIL_SCHEMA,
    SNIPPET_UPDATE_SCHEMA,
    SNIPPET_DELETE_SCHEMA,
    SNIPPET_HIGHLIGHT_SCHEMA,
    USER_LIST_SCHEMA,
    USER_DETAIL_SCHEMA,
)

User = get_user_model()

# @api_view(['GET'])
# def api_root(request, format=None):
#     return Response({
#         'users': reverse('user-list', request=request, format=format),
#         'snippets': reverse('snippet-list', request=request, format=format)
#     })

class SnippetFilter(filters.FilterSet):
    """Filter class for Snippet model with various filtering options."""
    
    language = filters.CharFilter(lookup_expr='iexact')
    created_after = filters.DateTimeFilter(field_name='created', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created', lookup_expr='lte')
    search_title = filters.CharFilter(field_name='title', lookup_expr='icontains')
    search_code = filters.CharFilter(field_name='code', lookup_expr='icontains')

    class Meta:
        model = Snippet
        fields = ['language', 'created_after', 'created_before', 'search_title', 'search_code']


class SnippetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing code snippets.
    
    This ViewSet automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions. Additionally, it provides a `highlight` action
    for getting syntax-highlighted HTML representation of snippets.
    
    Features:
    - Pagination support
    - Filtering by language, date range, and search terms
    - Owner-based permissions (only owners can edit/delete their snippets)
    - Syntax highlighting via Pygments
    """
    serializer_class = SnippetSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filterset_class = SnippetFilter
    filter_backends = (filters.DjangoFilterBackend,)
    pagination_class = SnippetPagination

    @SNIPPET_HIGHLIGHT_SCHEMA
    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def highlight(self, request, *args, **kwargs):
        """Get syntax-highlighted HTML representation of a code snippet."""
        snippet = self.get_object()
        return Response(snippet.highlighted)

    def perform_create(self, serializer):
        """Automatically associate the snippet with the authenticated user."""
        serializer.save(owner=self.request.user)
    
    def get_queryset(self):
        """Return snippets based on user authentication status."""
        if self.request.user.is_authenticated:
            return Snippet.objects.filter(owner=self.request.user)
        # For unauthenticated users, return all snippets
        return Snippet.objects.all()

    # Override ViewSet methods to add schema documentation
    @SNIPPET_LIST_SCHEMA
    def list(self, request, *args, **kwargs):
        """List all snippets with filtering and pagination."""
        return super().list(request, *args, **kwargs)

    @SNIPPET_CREATE_SCHEMA
    def create(self, request, *args, **kwargs):
        """Create a new code snippet."""
        return super().create(request, *args, **kwargs)

    @SNIPPET_DETAIL_SCHEMA
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific snippet by ID."""
        return super().retrieve(request, *args, **kwargs)

    @SNIPPET_UPDATE_SCHEMA
    def update(self, request, *args, **kwargs):
        """Update an existing snippet (full update)."""
        return super().update(request, *args, **kwargs)

    @SNIPPET_UPDATE_SCHEMA
    def partial_update(self, request, *args, **kwargs):
        """Update an existing snippet (partial update)."""
        return super().partial_update(request, *args, **kwargs)

    @SNIPPET_DELETE_SCHEMA
    def destroy(self, request, *args, **kwargs):
        """Delete a snippet."""
        return super().destroy(request, *args, **kwargs)

# class SnippetList(APIView):
#     """
#     List all snippets, or create a new snippet.
#     """
#     permission_classes = [permissions.IsAuthenticatedOrReadOnly]

#     def get(self, request, format=None):
#         snippets = Snippet.objects.filter(owner=self.request.user)
#         serializer = SnippetSerializer(snippets, many=True, context={'request': request})
#         return Response(serializer.data)

#     def post(self, request, format=None):
#         serializer = SnippetSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#     def perform_create(self, serializer):
#         serializer.save(owner=self.request.user)

# class SnippetDetail(APIView):
#     """
#     Retrieve, update or delete a snippet instance.
#     """
#     permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

#     def get_object(self, pk):
#         try:
#             return Snippet.objects.get(pk=pk)
#         except Snippet.DoesNotExist:
#             raise Http404

#     def get(self, request, pk, format=None):
#         snippet = self.get_object(pk)
#         serializer = SnippetSerializer(snippet, context={'request': request})
#         return Response(serializer.data)

#     def put(self, request, pk, format=None):
#         snippet = self.get_object(pk)
#         serializer = SnippetSerializer(snippet, data=request.data, context={'request': request})
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, pk, format=None):
#         snippet = self.get_object(pk)
#         snippet.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)
    
# class SnippetHighlight(generics.GenericAPIView):
#     queryset = Snippet.objects.all()
#     renderer_classes = [renderers.StaticHTMLRenderer]

#     def get(self, request, *args, **kwargs):
#         snippet = self.get_object()
#         return Response(snippet.highlighted)

# Or just use generic views for CRUD
# from snippets.models import Snippet
# from snippets.serializers import SnippetSerializer
# from rest_framework import generics


# class SnippetList(generics.ListCreateAPIView):
#     queryset = Snippet.objects.all()
#     serializer_class = SnippetSerializer


# class SnippetDetail(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Snippet.objects.all()
#     serializer_class = SnippetSerializer

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user management.
    
    This viewset automatically provides `list` and `retrieve` actions.
    Only authenticated users can access user information.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Override ViewSet methods to add schema documentation
    @USER_LIST_SCHEMA
    def list(self, request, *args, **kwargs):
        """List all users with pagination."""
        return super().list(request, *args, **kwargs)

    @USER_DETAIL_SCHEMA
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific user by ID."""
        return super().retrieve(request, *args, **kwargs)

# class UserList(generics.ListAPIView):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer

# class UserDetail(generics.RetrieveAPIView):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer
