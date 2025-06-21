"""
OpenAPI schema definitions for snippets endpoints.
This module contains all the schema decorators and examples for better code organization.
"""

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, OpenApiParameter
from rest_framework import status
from .serializers import SnippetSerializer, UserSerializer

# Common response examples
UNAUTHORIZED_RESPONSE = OpenApiResponse(
    description="Authentication required",
    examples=[
        OpenApiExample(
            "Unauthorized",
            value={"detail": "Authentication credentials were not provided."}
        )
    ]
)

FORBIDDEN_RESPONSE = OpenApiResponse(
    description="Permission denied",
    examples=[
        OpenApiExample(
            "Forbidden",
            value={"detail": "You do not have permission to perform this action."}
        )
    ]
)

NOT_FOUND_RESPONSE = OpenApiResponse(
    description="Resource not found",
    examples=[
        OpenApiExample(
            "Not Found",
            value={"detail": "Not found."}
        )
    ]
)

# Snippet list endpoint schemas
SNIPPET_LIST_SCHEMA = extend_schema(
    tags=["Snippets"],
    summary="List Snippets",
    description="Retrieve a paginated list of code snippets. Authenticated users see their own snippets, while unauthenticated users see all public snippets.",
    parameters=[
        OpenApiParameter(
            name="language",
            description="Filter snippets by programming language (case-insensitive)",
            required=False,
            type=str,
            examples=[
                OpenApiExample("Python", value="python"),
                OpenApiExample("JavaScript", value="javascript"),
                OpenApiExample("Java", value="java"),
            ]
        ),
        OpenApiParameter(
            name="created_after",
            description="Filter snippets created after this date (ISO format: YYYY-MM-DDTHH:MM:SSZ)",
            required=False,
            type=str,
            examples=[
                OpenApiExample("After Date", value="2024-01-01T00:00:00Z")
            ]
        ),
        OpenApiParameter(
            name="created_before",
            description="Filter snippets created before this date (ISO format: YYYY-MM-DDTHH:MM:SSZ)",
            required=False,
            type=str,
            examples=[
                OpenApiExample("Before Date", value="2024-12-31T23:59:59Z")
            ]
        ),
        OpenApiParameter(
            name="search_title",
            description="Search snippets by title (case-insensitive)",
            required=False,
            type=str,
            examples=[
                OpenApiExample("Search Title", value="hello world")
            ]
        ),
        OpenApiParameter(
            name="search_code",
            description="Search snippets by code content (case-insensitive)",
            required=False,
            type=str,
            examples=[
                OpenApiExample("Search Code", value="print")
            ]
        ),
        OpenApiParameter(
            name="page",
            description="Page number for pagination",
            required=False,
            type=int,
            examples=[
                OpenApiExample("Page 1", value=1),
                OpenApiExample("Page 2", value=2),
            ]
        ),
    ],
    responses={
        200: OpenApiResponse(
            description="Snippets retrieved successfully",
            examples=[
                OpenApiExample(
                    "Snippets List",
                    value={
                        "count": 25,
                        "next": "http://localhost:8000/snippets/?page=2",
                        "previous": None,
                        "results": [
                            {
                                "url": "http://localhost:8000/snippets/1/",
                                "id": 1,
                                "highlight": "http://localhost:8000/snippets/1/highlight/",
                                "owner": "john_doe",
                                "title": "Hello World in Python",
                                "code": "print('Hello, World!')",
                                "linenos": False,
                                "language": "python",
                                "style": "friendly",
                                "created": "2024-01-15T10:30:00Z"
                            }
                        ]
                    }
                )
            ]
        ),
        401: UNAUTHORIZED_RESPONSE
    }
)

# Snippet create endpoint schemas
SNIPPET_CREATE_SCHEMA = extend_schema(
    tags=["Snippets"],
    summary="Create Snippet",
    description="Create a new code snippet. The snippet will be automatically associated with the authenticated user.",
    request=SnippetSerializer,
    responses={
        201: OpenApiResponse(
            description="Snippet created successfully",
            examples=[
                OpenApiExample(
                    "Snippet Created",
                    value={
                        "url": "http://localhost:8000/snippets/1/",
                        "id": 1,
                        "highlight": "http://localhost:8000/snippets/1/highlight/",
                        "owner": "john_doe",
                        "title": "Hello World in Python",
                        "code": "print('Hello, World!')",
                        "linenos": False,
                        "language": "python",
                        "style": "friendly",
                        "created": "2024-01-15T10:30:00Z"
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description="Invalid snippet data",
            examples=[
                OpenApiExample(
                    "Validation Error",
                    value={
                        "title": ["This field is required."],
                        "code": ["This field may not be blank."]
                    }
                )
            ]
        ),
        401: UNAUTHORIZED_RESPONSE
    },
    examples=[
        OpenApiExample(
            "Valid Snippet",
            value={
                "title": "Hello World in Python",
                "code": "print('Hello, World!')",
                "linenos": False,
                "language": "python",
                "style": "friendly"
            },
            description="Example of valid snippet data"
        ),
        OpenApiExample(
            "JavaScript Snippet",
            value={
                "title": "JavaScript Function",
                "code": "function greet(name) {\n    return `Hello, ${name}!`;\n}",
                "linenos": True,
                "language": "javascript",
                "style": "monokai"
            },
            description="Example of JavaScript snippet with line numbers"
        )
    ]
)

# Snippet detail endpoint schemas
SNIPPET_DETAIL_SCHEMA = extend_schema(
    tags=["Snippets"],
    summary="Get Snippet",
    description="Retrieve a specific code snippet by ID.",
    responses={
        200: OpenApiResponse(
            description="Snippet retrieved successfully",
            examples=[
                OpenApiExample(
                    "Snippet Detail",
                    value={
                        "url": "http://localhost:8000/snippets/1/",
                        "id": 1,
                        "highlight": "http://localhost:8000/snippets/1/highlight/",
                        "owner": "john_doe",
                        "title": "Hello World in Python",
                        "code": "print('Hello, World!')",
                        "linenos": False,
                        "language": "python",
                        "style": "friendly",
                        "created": "2024-01-15T10:30:00Z"
                    }
                )
            ]
        ),
        404: NOT_FOUND_RESPONSE
    }
)

# Snippet update endpoint schemas
SNIPPET_UPDATE_SCHEMA = extend_schema(
    tags=["Snippets"],
    summary="Update Snippet",
    description="Update an existing code snippet. Only the snippet owner can update it.",
    request=SnippetSerializer,
    responses={
        200: OpenApiResponse(
            description="Snippet updated successfully",
            examples=[
                OpenApiExample(
                    "Snippet Updated",
                    value={
                        "url": "http://localhost:8000/snippets/1/",
                        "id": 1,
                        "highlight": "http://localhost:8000/snippets/1/highlight/",
                        "owner": "john_doe",
                        "title": "Updated Hello World",
                        "code": "print('Hello, Updated World!')",
                        "linenos": True,
                        "language": "python",
                        "style": "friendly",
                        "created": "2024-01-15T10:30:00Z"
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description="Invalid snippet data",
            examples=[
                OpenApiExample(
                    "Validation Error",
                    value={
                        "code": ["This field may not be blank."]
                    }
                )
            ]
        ),
        401: UNAUTHORIZED_RESPONSE,
        403: FORBIDDEN_RESPONSE,
        404: NOT_FOUND_RESPONSE
    },
    examples=[
        OpenApiExample(
            "Update Snippet",
            value={
                "title": "Updated Hello World",
                "code": "print('Hello, Updated World!')",
                "linenos": True,
                "language": "python",
                "style": "friendly"
            },
            description="Example of snippet update data"
        )
    ]
)

# Snippet delete endpoint schemas
SNIPPET_DELETE_SCHEMA = extend_schema(
    tags=["Snippets"],
    summary="Delete Snippet",
    description="Delete a code snippet. Only the snippet owner can delete it.",
    responses={
        204: OpenApiResponse(
            description="Snippet deleted successfully"
        ),
        401: UNAUTHORIZED_RESPONSE,
        403: FORBIDDEN_RESPONSE,
        404: NOT_FOUND_RESPONSE
    }
)

# Snippet highlight endpoint schemas
SNIPPET_HIGHLIGHT_SCHEMA = extend_schema(
    tags=["Snippets"],
    summary="Highlight Snippet",
    description="Get syntax-highlighted HTML representation of a code snippet.",
    responses={
        200: OpenApiResponse(
            description="Highlighted snippet HTML",
            examples=[
                OpenApiExample(
                    "Highlighted HTML",
                    value="<div class=\"highlight\"><pre><span class=\"k\">print</span><span class=\"p\">(</span><span class=\"s1\">&#39;Hello, World!&#39;</span><span class=\"p\">)</span></pre></div>",
                    description="HTML with syntax highlighting"
                )
            ]
        ),
        404: NOT_FOUND_RESPONSE
    }
)

# User list endpoint schemas
USER_LIST_SCHEMA = extend_schema(
    tags=["Users"],
    summary="List Users",
    description="Retrieve a paginated list of users. Only authenticated users can access this endpoint.",
    parameters=[
        OpenApiParameter(
            name="page",
            description="Page number for pagination",
            required=False,
            type=int,
            examples=[
                OpenApiExample("Page 1", value=1),
                OpenApiExample("Page 2", value=2),
            ]
        ),
    ],
    responses={
        200: OpenApiResponse(
            description="Users retrieved successfully",
            examples=[
                OpenApiExample(
                    "Users List",
                    value={
                        "count": 10,
                        "next": "http://localhost:8000/users/?page=2",
                        "previous": None,
                        "results": [
                            {
                                "url": "http://localhost:8000/users/1/",
                                "id": 1,
                                "username": "john_doe",
                                "snippets": [
                                    "http://localhost:8000/snippets/1/",
                                    "http://localhost:8000/snippets/2/"
                                ]
                            }
                        ]
                    }
                )
            ]
        ),
        401: UNAUTHORIZED_RESPONSE
    }
)

# User detail endpoint schemas
USER_DETAIL_SCHEMA = extend_schema(
    tags=["Users"],
    summary="Get User",
    description="Retrieve a specific user by ID. Only authenticated users can access this endpoint.",
    responses={
        200: OpenApiResponse(
            description="User retrieved successfully",
            examples=[
                OpenApiExample(
                    "User Detail",
                    value={
                        "url": "http://localhost:8000/users/1/",
                        "id": 1,
                        "username": "john_doe",
                        "snippets": [
                            "http://localhost:8000/snippets/1/",
                            "http://localhost:8000/snippets/2/"
                        ]
                    }
                )
            ]
        ),
        401: UNAUTHORIZED_RESPONSE,
        404: NOT_FOUND_RESPONSE
    }
) 