import time
from collections import defaultdict
from functools import wraps
from threading import Lock

from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from lottery.models import DrawResult
from .models import SavedPrediction
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    SavedPredictionSerializer,
)

# ---------------------------------------------------------------------------
# Rate limiting：優先使用 django-ratelimit，若無法 import 則以記憶體限流降級
# ---------------------------------------------------------------------------
try:
    from django_ratelimit.decorators import ratelimit  # type: ignore
    from django_ratelimit.exceptions import Ratelimited  # type: ignore
    _HAS_DJANGO_RATELIMIT = True
except ImportError:  # pragma: no cover - 套件未安裝時的降級路徑
    _HAS_DJANGO_RATELIMIT = False

# 記憶體限流器狀態 (降級用)
_RATE_LIMIT_STATE: dict = defaultdict(list)
_RATE_LIMIT_LOCK = Lock()


def _get_client_ip(request) -> str:
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def simple_rate_limit(max_calls: int, period_seconds: int = 60):
    """簡易記憶體限流裝飾器，套用於 APIView.post / get 等方法。"""

    def decorator(view_method):
        @wraps(view_method)
        def wrapper(self, request, *args, **kwargs):
            key = f"{view_method.__qualname__}:{_get_client_ip(request)}"
            now = time.time()
            with _RATE_LIMIT_LOCK:
                timestamps = [
                    t for t in _RATE_LIMIT_STATE[key]
                    if now - t < period_seconds
                ]
                if len(timestamps) >= max_calls:
                    _RATE_LIMIT_STATE[key] = timestamps
                    return Response(
                        {"error": "請求過於頻繁，請稍後再試。"},
                        status=status.HTTP_429_TOO_MANY_REQUESTS,
                    )
                timestamps.append(now)
                _RATE_LIMIT_STATE[key] = timestamps
            return view_method(self, request, *args, **kwargs)

        return wrapper

    return decorator


def rate_limit(max_calls: int, period_seconds: int = 60):
    """統一對外限流裝飾器：有 django-ratelimit 就用它，否則降級。"""
    if _HAS_DJANGO_RATELIMIT:
        rate_str = f"{max_calls}/m" if period_seconds == 60 else f"{max_calls}/{period_seconds}s"

        def decorator(view_method):
            @wraps(view_method)
            def wrapper(self, request, *args, **kwargs):
                @ratelimit(key='ip', rate=rate_str, block=False)
                def _inner(req):
                    return None

                _inner(request)
                if getattr(request, 'limited', False):
                    return Response(
                        {"error": "請求過於頻繁，請稍後再試。"},
                        status=status.HTTP_429_TOO_MANY_REQUESTS,
                    )
                return view_method(self, request, *args, **kwargs)

            return wrapper

        return decorator
    return simple_rate_limit(max_calls, period_seconds)


class RegisterView(APIView):
    """POST /api/v1/auth/register/"""

    @rate_limit(max_calls=5, period_seconds=60)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """POST /api/v1/auth/login/"""

    @rate_limit(max_calls=10, period_seconds=60)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if user is None:
            return Response(
                {"error": "帳號或密碼錯誤。"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        # 刪除舊 token 再建立新的，確保 24 小時有效期從本次登入重新計算
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        return Response({
            "token": token.key,
            "user": UserSerializer(user).data,
        })


class LogoutView(APIView):
    """POST /api/v1/auth/logout/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 刪除當前使用者的 token
        request.user.auth_token.delete()
        return Response(
            {"message": "已成功登出。"},
            status=status.HTTP_200_OK,
        )


class ProfileView(APIView):
    """GET /api/v1/auth/profile/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class SavedPredictionListCreateView(APIView):
    """
    GET  /api/v1/auth/predictions/  -- 列出當前使用者的所有收藏
    POST /api/v1/auth/predictions/  -- 新增收藏
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        predictions = SavedPrediction.objects.filter(
            user=request.user
        ).select_related('game').order_by('-created_at')
        serializer = SavedPredictionSerializer(predictions, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = SavedPredictionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SavedPredictionDeleteView(APIView):
    """DELETE /api/v1/auth/predictions/{id}/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            prediction = SavedPrediction.objects.get(pk=pk, user=request.user)
        except SavedPrediction.DoesNotExist:
            return Response(
                {"error": "找不到該收藏或無權刪除。"},
                status=status.HTTP_404_NOT_FOUND,
            )
        prediction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SavedPredictionCheckAllView(APIView):
    """POST /api/v1/auth/predictions/check_all/  -- 批次對獎"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        unchecked = SavedPrediction.objects.filter(
            user=request.user,
            checked_term__isnull=True,
        ).select_related('game')

        if not unchecked.exists():
            return Response({
                "message": "沒有需要對獎的收藏。",
                "checked_count": 0,
                "results": [],
            })

        results = []
        now = timezone.now()

        for prediction in unchecked:
            # 取該彩種最新一期
            latest_draw = (
                DrawResult.objects
                .filter(game=prediction.game)
                .order_by('-draw_date', '-draw_term')
                .first()
            )
            if not latest_draw:
                continue

            # 計算命中
            winning_set = set(latest_draw.numbers_sorted)
            user_set = set(prediction.numbers)
            matched = winning_set & user_set
            matched_count = len(matched)

            special_matched = False
            if (prediction.game.has_special
                    and prediction.special_number is not None
                    and latest_draw.special_number is not None):
                special_matched = prediction.special_number == latest_draw.special_number

            # 寫入對獎結果
            prediction.checked_term = latest_draw.draw_term
            prediction.matched_count = matched_count
            prediction.special_matched = special_matched
            prediction.checked_at = now
            prediction.save(update_fields=[
                'checked_term', 'matched_count', 'special_matched', 'checked_at',
            ])

            results.append({
                "id": prediction.id,
                "game_code": prediction.game.code,
                "numbers": prediction.numbers,
                "special_number": prediction.special_number,
                "checked_term": latest_draw.draw_term,
                "matched_count": matched_count,
                "matched_numbers": sorted(matched),
                "special_matched": special_matched,
            })

        return Response({
            "message": f"已完成 {len(results)} 筆對獎。",
            "checked_count": len(results),
            "results": results,
        })
