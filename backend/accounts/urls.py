from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView, ProfileView,
    SavedPredictionListCreateView, SavedPredictionDeleteView,
    SavedPredictionCheckAllView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('profile/', ProfileView.as_view(), name='auth-profile'),
    path('predictions/', SavedPredictionListCreateView.as_view(), name='predictions-list-create'),
    path('predictions/check_all/', SavedPredictionCheckAllView.as_view(), name='predictions-check-all'),
    path('predictions/<int:pk>/', SavedPredictionDeleteView.as_view(), name='predictions-delete'),
]
