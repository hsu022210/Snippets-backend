"""
OpenAPI schema definitions for authentication endpoints.
This module contains all the schema decorators and examples for better code organization.
"""

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from rest_framework import status
from .serializers import RegisterSerializer

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

# Register endpoint schemas
REGISTER_SCHEMA = extend_schema(
    tags=["Authentication"],
    summary="Register New User",
    description="Create a new user account with email verification and welcome email.",
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(
            description="User successfully registered",
            examples=[
                OpenApiExample(
                    "Successful Registration",
                    value={
                        "message": "User registered successfully",
                        "user": {
                            "id": 1,
                            "username": "john_doe",
                            "email": "john@example.com",
                            "first_name": "John",
                            "last_name": "Doe"
                        }
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description="Invalid registration data",
            examples=[
                OpenApiExample(
                    "Validation Error - Missing Fields",
                    value={
                        "email": ["Email is required"],
                        "password2": ["Please confirm your password"]
                    }
                ),
                OpenApiExample(
                    "Validation Error - Duplicate Email",
                    value={
                        "email": ["This email is already registered. Please use a different email address."]
                    }
                ),
                OpenApiExample(
                    "Validation Error - Duplicate Username",
                    value={
                        "username": ["This username is already taken. Please choose a different username."]
                    }
                ),
                OpenApiExample(
                    "Validation Error - Password Mismatch",
                    value={
                        "password": ["Password fields didn't match."],
                        "password2": ["Password fields didn't match."]
                    }
                ),
                OpenApiExample(
                    "Validation Error - Weak Password",
                    value={
                        "password": ["This password is too common."]
                    }
                )
            ]
        ),
        500: OpenApiResponse(
            description="Internal server error",
            examples=[
                OpenApiExample(
                    "Server Error",
                    value={"detail": "Registration failed. Please try again."}
                )
            ]
        )
    },
    examples=[
        OpenApiExample(
            "Valid Registration",
            value={
                "username": "john_doe",
                "email": "john@example.com",
                "password": "securepassword123",
                "password2": "securepassword123",
                "first_name": "John",
                "last_name": "Doe"
            },
            description="Example of valid registration data"
        )
    ]
)

# User profile endpoint schemas
USER_PROFILE_SCHEMA = extend_schema(
    tags=["Authentication"],
    summary="User Profile",
    description="Retrieve and update the authenticated user's profile information.",
    responses={
        200: OpenApiResponse(
            description="User profile retrieved successfully",
            examples=[
                OpenApiExample(
                    "User Profile",
                    value={
                        "id": 1,
                        "username": "john_doe",
                        "email": "john@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "date_joined": "2024-01-15T10:30:00Z"
                    }
                )
            ]
        ),
        401: UNAUTHORIZED_RESPONSE
    }
)

# Logout endpoint schemas
LOGOUT_SCHEMA = extend_schema(
    tags=["Authentication"],
    summary="User Logout",
    description="Logout the authenticated user. Note: JWT tokens are stateless, so the client should handle token removal.",
    responses={
        200: OpenApiResponse(
            description="Successfully logged out",
            examples=[
                OpenApiExample(
                    "Logout Success",
                    value={"message": "Successfully logged out."}
                )
            ]
        ),
        400: OpenApiResponse(
            description="Logout failed",
            examples=[
                OpenApiExample(
                    "Logout Error",
                    value={"error": "Logout failed"}
                )
            ]
        ),
        401: UNAUTHORIZED_RESPONSE
    }
)

# Login endpoint schemas
LOGIN_SCHEMA = extend_schema(
    tags=["Authentication"],
    summary="User Login",
    description="Authenticate user with email and password, returning JWT access and refresh tokens.",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "User's email address"
                },
                "password": {
                    "type": "string",
                    "description": "User's password",
                    "minLength": 1
                }
            },
            "required": ["email", "password"]
        }
    },
    responses={
        200: OpenApiResponse(
            description="Login successful",
            examples=[
                OpenApiExample(
                    "Login Success",
                    value={
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description="Missing credentials",
            examples=[
                OpenApiExample(
                    "Missing Credentials",
                    value={"error": "Please provide both email and password."}
                )
            ]
        ),
        401: OpenApiResponse(
            description="Invalid credentials",
            examples=[
                OpenApiExample(
                    "Invalid Credentials",
                    value={"error": "Invalid credentials."}
                )
            ]
        )
    },
    examples=[
        OpenApiExample(
            "Valid Login",
            value={
                "email": "john@example.com",
                "password": "securepassword123"
            },
            description="Example of valid login credentials"
        )
    ]
)

# Token refresh endpoint schemas
TOKEN_REFRESH_SCHEMA = extend_schema(
    tags=["Authentication"],
    summary="Refresh JWT Token",
    description="Refresh an expired JWT access token using a valid refresh token.",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "refresh": {
                    "type": "string",
                    "description": "Valid refresh token"
                }
            },
            "required": ["refresh"]
        }
    },
    responses={
        200: OpenApiResponse(
            description="Token refreshed successfully",
            examples=[
                OpenApiExample(
                    "Token Refresh Success",
                    value={
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description="Invalid refresh token",
            examples=[
                OpenApiExample(
                    "Invalid Token",
                    value={
                        "detail": "Token is invalid or expired",
                        "code": "token_not_valid"
                    }
                )
            ]
        ),
        401: OpenApiResponse(
            description="Token validation failed",
            examples=[
                OpenApiExample(
                    "Token Error",
                    value={
                        "detail": "Token is invalid or expired",
                        "code": "token_not_valid"
                    }
                )
            ]
        )
    },
    examples=[
        OpenApiExample(
            "Token Refresh Request",
            value={
                "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            },
            description="Example of token refresh request"
        )
    ]
)

# Password reset request schemas
PASSWORD_RESET_REQUEST_SCHEMA = extend_schema(
    tags=["Authentication"],
    summary="Request Password Reset",
    description="Send a password reset email to the user's email address with a reset link.",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "User's email address"
                }
            },
            "required": ["email"]
        }
    },
    responses={
        200: OpenApiResponse(
            description="Password reset email sent successfully",
            examples=[
                OpenApiExample(
                    "Reset Request Success",
                    value={"status": "OK"}
                )
            ]
        ),
        400: OpenApiResponse(
            description="Invalid email or user not found",
            examples=[
                OpenApiExample(
                    "Invalid Email",
                    value={"email": ["Enter a valid email address."]}
                )
            ]
        )
    },
    examples=[
        OpenApiExample(
            "Password Reset Request",
            value={"email": "john@example.com"},
            description="Example of password reset request"
        )
    ]
)

# Password reset confirm schemas
PASSWORD_RESET_CONFIRM_SCHEMA = extend_schema(
    tags=["Authentication"],
    summary="Confirm Password Reset",
    description="Confirm password reset using the token from the reset email and set a new password.",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "token": {
                    "type": "string",
                    "description": "Password reset token from email"
                },
                "password": {
                    "type": "string",
                    "description": "New password",
                    "minLength": 8
                }
            },
            "required": ["token", "password"]
        }
    },
    responses={
        200: OpenApiResponse(
            description="Password reset successful",
            examples=[
                OpenApiExample(
                    "Reset Success",
                    value={"status": "OK"}
                )
            ]
        ),
        400: OpenApiResponse(
            description="Invalid token or password",
            examples=[
                OpenApiExample(
                    "Missing Token",
                    value={"error": "Token is required"}
                ),
                OpenApiExample(
                    "Invalid Token",
                    value={"error": "Invalid or expired token"}
                )
            ]
        )
    },
    examples=[
        OpenApiExample(
            "Password Reset Confirmation",
            value={
                "token": "abc123def456",
                "password": "newsecurepassword123"
            },
            description="Example of password reset confirmation"
        )
    ]
) 