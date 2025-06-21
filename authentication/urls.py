from django.urls import path
from .views import (
    RegisterView, 
    UserDetailView, 
    LogoutView, 
    CustomPasswordResetRequest, 
    CustomPasswordResetConfirm,
    CustomLoginView,
    CustomTokenRefreshView
)

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('user/', UserDetailView.as_view(), name='user_detail'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('password-reset/', CustomPasswordResetRequest.as_view(), name='password-reset'),
    path('password-reset/confirm/', CustomPasswordResetConfirm.as_view(), name='password-reset-confirm'),
] 