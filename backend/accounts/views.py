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


class RegisterView(APIView):
    """POST /api/v1/auth/register/"""

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
        token, _ = Token.objects.get_or_create(user=user)
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
