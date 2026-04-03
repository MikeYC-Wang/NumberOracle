from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LotteryGameViewSet, DrawResultViewSet

router = DefaultRouter()
router.register(r'games', LotteryGameViewSet, basename='games')
router.register(r'draws', DrawResultViewSet, basename='draws')

urlpatterns = [
    path('', include(router.urls)),
]
