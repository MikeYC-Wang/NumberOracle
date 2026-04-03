from rest_framework import viewsets
from .models import LotteryGame, DrawResult
from .serializers import LotteryGameSerializer, DrawResultSerializer


class LotteryGameViewSet(viewsets.ReadOnlyModelViewSet):
    """彩券遊戲種類 API"""
    queryset = LotteryGame.objects.filter(is_active=True)
    serializer_class = LotteryGameSerializer
    lookup_field = 'code'


class DrawResultViewSet(viewsets.ReadOnlyModelViewSet):
    """開獎紀錄 API"""
    serializer_class = DrawResultSerializer

    def get_queryset(self):
        queryset = DrawResult.objects.select_related('game').order_by('-draw_date')
        game_code = self.request.query_params.get('game')
        if game_code:
            queryset = queryset.filter(game__code=game_code)
        return queryset
