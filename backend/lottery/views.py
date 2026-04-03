from collections import defaultdict

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import LotteryGame, DrawResult
from .serializers import LotteryGameSerializer, DrawResultSerializer


class LotteryGameViewSet(viewsets.ReadOnlyModelViewSet):
    """彩券遊戲種類 API"""
    queryset = LotteryGame.objects.filter(is_active=True)
    serializer_class = LotteryGameSerializer
    lookup_field = 'code'


class DrawResultPagination(PageNumberPagination):
    page_size = 200
    page_size_query_param = 'page_size'
    max_page_size = 2000


class DrawResultViewSet(viewsets.ReadOnlyModelViewSet):
    """開獎紀錄 API"""
    serializer_class = DrawResultSerializer
    pagination_class = DrawResultPagination

    def get_queryset(self):
        queryset = DrawResult.objects.select_related('game').order_by('-draw_date')
        game_code = self.request.query_params.get('game')
        if game_code:
            queryset = queryset.filter(game__code=game_code)
        return queryset

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_game_or_error(game_code):
        """Return (game, None) or (None, Response)."""
        if not game_code:
            return None, Response(
                {"error": "query parameter 'game' is required."},
                status=400,
            )
        try:
            game = LotteryGame.objects.get(code=game_code, is_active=True)
        except LotteryGame.DoesNotExist:
            return None, Response(
                {"error": f"game '{game_code}' not found."},
                status=404,
            )
        return game, None

    # ------------------------------------------------------------------
    # GET /api/v1/draws/hot_cold/?game={code}&recent={N}
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='hot_cold')
    def hot_cold(self, request):
        """計算指定彩種近 N 期每個號碼的出現次數。"""
        game_code = request.query_params.get('game')
        game, err = self._get_game_or_error(game_code)
        if err:
            return err

        try:
            recent = int(request.query_params.get('recent', 50))
            if recent <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"error": "'recent' must be a positive integer."},
                status=400,
            )

        draws = (
            DrawResult.objects
            .filter(game=game)
            .order_by('-draw_date', '-draw_term')[:recent]
        )
        total_draws = len(draws)

        # 統計每個號碼的出現次數
        counter: dict[int, int] = defaultdict(int)
        for draw in draws:
            for num in draw.numbers_sorted:
                counter[num] += 1

        # 產生 1 ~ main_pool_size 的完整頻率表
        frequencies = []
        for num in range(1, game.main_pool_size + 1):
            count = counter.get(num, 0)
            pct = round(count / total_draws * 100, 1) if total_draws else 0.0
            frequencies.append({
                "number": num,
                "count": count,
                "percentage": pct,
            })

        return Response({
            "game": game.code,
            "recent_draws": recent,
            "total_draws": total_draws,
            "frequencies": frequencies,
        })

    # ------------------------------------------------------------------
    # GET /api/v1/draws/missing_values/?game={code}
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='missing_values')
    def missing_values(self, request):
        """計算每個號碼的遺漏值（距離上次出現的期數）。"""
        game_code = request.query_params.get('game')
        game, err = self._get_game_or_error(game_code)
        if err:
            return err

        draws = list(
            DrawResult.objects
            .filter(game=game)
            .order_by('-draw_date', '-draw_term')
            .values_list('draw_term', 'numbers_sorted')
        )

        if not draws:
            return Response({
                "game": game.code,
                "as_of_term": None,
                "missing_values": [],
            })

        latest_term = draws[0][0]

        # 對每個號碼，找出最近一次出現是第幾期前
        last_seen: dict[int, tuple[int, str]] = {}  # number -> (index, term)
        for idx, (term, numbers) in enumerate(draws):
            for num in numbers:
                if num not in last_seen:
                    last_seen[num] = (idx, term)

        # 產生 1 ~ main_pool_size 的完整遺漏表
        total_draws = len(draws)
        missing_list = []
        for num in range(1, game.main_pool_size + 1):
            if num in last_seen:
                missing_draws, last_term = last_seen[num]
            else:
                # 在所有紀錄中都沒出現過
                missing_draws = total_draws
                last_term = None
            missing_list.append({
                "number": num,
                "missing_draws": missing_draws,
                "last_appeared": last_term,
            })

        return Response({
            "game": game.code,
            "as_of_term": latest_term,
            "missing_values": missing_list,
        })
