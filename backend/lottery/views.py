import time
from collections import defaultdict

from django.core.management import call_command
from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import LotteryGame, DrawResult
from .serializers import LotteryGameSerializer, DrawResultSerializer

# 簡易限流：記錄上次 refresh 的時間戳
_last_refresh_time = 0.0
_REFRESH_COOLDOWN = 60  # 秒


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

    # ------------------------------------------------------------------
    # GET /api/v1/draws/trend/?game={code}&number={N}&recent={期數}
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='trend')
    def trend(self, request):
        """查詢指定號碼在近 N 期的出現走勢。"""
        game_code = request.query_params.get('game')
        game, err = self._get_game_or_error(game_code)
        if err:
            return err

        # 驗證 number 參數
        number_param = request.query_params.get('number')
        if number_param is None:
            return Response(
                {"error": "query parameter 'number' is required."},
                status=400,
            )
        try:
            number = int(number_param)
            if number < 1 or number > game.main_pool_size:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"error": f"'number' must be an integer between 1 and {game.main_pool_size}."},
                status=400,
            )

        # 驗證 recent 參數
        try:
            recent = int(request.query_params.get('recent', 100))
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

        trend = []
        for draw in draws:
            trend.append({
                "draw_term": draw.draw_term,
                "draw_date": draw.draw_date.isoformat(),
                "appeared": number in draw.numbers_sorted,
            })

        return Response({
            "game": game.code,
            "number": number,
            "recent_draws": recent,
            "trend": trend,
        })

    # ------------------------------------------------------------------
    # GET /api/v1/draws/summary/?game={code}
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """回傳指定彩種的摘要統計資訊。"""
        game_code = request.query_params.get('game')
        game, err = self._get_game_or_error(game_code)
        if err:
            return err

        draws_qs = DrawResult.objects.filter(game=game)
        total_draws = draws_qs.count()

        if total_draws == 0:
            return Response({
                "game": game.code,
                "game_name": game.name,
                "total_draws": 0,
                "date_range": {"earliest": None, "latest": None},
                "latest_draw": None,
                "top5_hot": [],
                "top5_cold": [],
            })

        # 日期範圍
        earliest_draw = draws_qs.order_by('draw_date').first()
        latest_draw = draws_qs.order_by('-draw_date', '-draw_term').first()

        # 統計所有號碼出現次數
        counter: dict[int, int] = defaultdict(int)
        for numbers in draws_qs.values_list('numbers_sorted', flat=True):
            for num in numbers:
                counter[num] += 1

        # 產生完整頻率表 (確保沒出現過的號碼也有 count=0)
        full_freq = []
        for num in range(1, game.main_pool_size + 1):
            full_freq.append({"number": num, "count": counter.get(num, 0)})

        # top5 hot / cold
        sorted_by_count = sorted(full_freq, key=lambda x: x["count"], reverse=True)
        top5_hot = sorted_by_count[:5]
        top5_cold = sorted(full_freq, key=lambda x: x["count"])[:5]

        return Response({
            "game": game.code,
            "game_name": game.name,
            "total_draws": total_draws,
            "date_range": {
                "earliest": earliest_draw.draw_date.isoformat(),
                "latest": latest_draw.draw_date.isoformat(),
            },
            "latest_draw": {
                "draw_term": latest_draw.draw_term,
                "draw_date": latest_draw.draw_date.isoformat(),
                "numbers_sorted": latest_draw.numbers_sorted,
                "special_number": latest_draw.special_number,
            },
            "top5_hot": top5_hot,
            "top5_cold": top5_cold,
        })

    # ------------------------------------------------------------------
    # POST /api/v1/draws/refresh/
    # ------------------------------------------------------------------

    @action(detail=False, methods=['post'], url_path='refresh')
    def refresh(self, request):
        """即時更新最新開獎資料。"""
        global _last_refresh_time

        now = time.time()
        if now - _last_refresh_time < _REFRESH_COOLDOWN:
            remaining = int(_REFRESH_COOLDOWN - (now - _last_refresh_time))
            return Response(
                {
                    "status": "error",
                    "message": f"請求過於頻繁，請 {remaining} 秒後再試",
                },
                status=429,
            )

        # 記錄更新前各彩種的數量
        game_codes = ['daily_cash', 'lotto649', 'super_lotto']
        counts_before = {}
        for code in game_codes:
            counts_before[code] = DrawResult.objects.filter(game__code=code).count()

        # 執行更新
        _last_refresh_time = time.time()
        try:
            call_command('update_latest')
        except Exception as e:
            return Response(
                {
                    "status": "error",
                    "message": f"更新失敗: {str(e)}",
                },
                status=500,
            )

        # 計算新增筆數
        updated_counts = {}
        for code in game_codes:
            counts_after = DrawResult.objects.filter(game__code=code).count()
            updated_counts[code] = counts_after - counts_before[code]

        return Response({
            "status": "success",
            "message": "資料更新完成",
            "updated_counts": updated_counts,
        })
