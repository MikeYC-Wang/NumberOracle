import csv
import math
import random
import time
from collections import defaultdict
from datetime import date
from itertools import combinations

from django.core.management import call_command
from django.db.models import Count
from django.http import HttpResponse
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

    # ------------------------------------------------------------------
    # helpers (shared validation)
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_recent(request, default=100):
        """Parse and validate the 'recent' query param."""
        try:
            recent = int(request.query_params.get('recent', default))
            if recent <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return None, Response(
                {"error": "'recent' must be a positive integer."},
                status=400,
            )
        return recent, None

    # ------------------------------------------------------------------
    # GET /api/v1/draws/consecutive_tail/?game={code}&recent={N}
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='consecutive_tail')
    def consecutive_tail(self, request):
        """連號/同尾分析。"""
        game_code = request.query_params.get('game')
        game, err = self._get_game_or_error(game_code)
        if err:
            return err

        recent, err = self._parse_recent(request)
        if err:
            return err

        draws = list(
            DrawResult.objects
            .filter(game=game)
            .order_by('-draw_date', '-draw_term')[:recent]
        )

        # 連號統計
        consecutive_counter: dict[int, int] = defaultdict(int)
        # 同尾統計
        tail_counter: dict[int, int] = defaultdict(int)

        for draw in draws:
            nums = sorted(draw.numbers_sorted)

            # 計算連號對數
            pairs = 0
            for i in range(len(nums) - 1):
                if nums[i + 1] - nums[i] == 1:
                    pairs += 1
            consecutive_counter[pairs] += 1

            # 計算尾數頻率
            for num in nums:
                tail_counter[num % 10] += 1

        # 格式化連號結果
        consecutive = {}
        for pairs_count, draw_count in sorted(consecutive_counter.items()):
            key = f"{pairs_count}對"
            consecutive[key] = draw_count

        # 格式化同尾結果
        tail_frequency = [
            {"tail": t, "count": tail_counter.get(t, 0)}
            for t in range(10)
        ]

        return Response({
            "game": game.code,
            "recent_draws": recent,
            "consecutive": consecutive,
            "tail_frequency": tail_frequency,
        })

    # ------------------------------------------------------------------
    # GET /api/v1/draws/zone_distribution/?game={code}&recent={N}
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='zone_distribution')
    def zone_distribution(self, request):
        """區間分布圖。"""
        game_code = request.query_params.get('game')
        game, err = self._get_game_or_error(game_code)
        if err:
            return err

        recent, err = self._parse_recent(request)
        if err:
            return err

        draws = list(
            DrawResult.objects
            .filter(game=game)
            .order_by('-draw_date', '-draw_term')[:recent]
        )

        pool_size = game.main_pool_size
        # 建立區間
        zone_counter: dict[str, int] = {}
        zone_labels = []
        start = 1
        while start <= pool_size:
            end = min(start + 9, pool_size)
            label = f"{start}-{end}"
            zone_labels.append((label, start, end))
            zone_counter[label] = 0
            start += 10

        for draw in draws:
            for num in draw.numbers_sorted:
                for label, lo, hi in zone_labels:
                    if lo <= num <= hi:
                        zone_counter[label] += 1
                        break

        zones = [{"zone": label, "count": zone_counter[label]} for label, _, _ in zone_labels]

        return Response({
            "game": game.code,
            "recent_draws": recent,
            "zones": zones,
        })

    # ------------------------------------------------------------------
    # GET /api/v1/draws/odd_even_size/?game={code}&recent={N}
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='odd_even_size')
    def odd_even_size(self, request):
        """奇偶比/大小比走勢。"""
        game_code = request.query_params.get('game')
        game, err = self._get_game_or_error(game_code)
        if err:
            return err

        recent, err = self._parse_recent(request)
        if err:
            return err

        draws = list(
            DrawResult.objects
            .filter(game=game)
            .order_by('-draw_date', '-draw_term')[:recent]
        )

        threshold = math.ceil(game.main_pool_size / 2)

        data = []
        for draw in draws:
            nums = draw.numbers_sorted
            odd = sum(1 for n in nums if n % 2 == 1)
            even = len(nums) - odd
            small = sum(1 for n in nums if n <= threshold)
            large = len(nums) - small
            data.append({
                "draw_term": draw.draw_term,
                "draw_date": draw.draw_date.isoformat(),
                "odd": odd,
                "even": even,
                "small": small,
                "large": large,
            })

        return Response({
            "game": game.code,
            "recent_draws": recent,
            "data": data,
        })

    # ------------------------------------------------------------------
    # GET /api/v1/draws/ac_value/?game={code}&recent={N}
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='ac_value')
    def ac_value(self, request):
        """AC 值分析。"""
        game_code = request.query_params.get('game')
        game, err = self._get_game_or_error(game_code)
        if err:
            return err

        recent, err = self._parse_recent(request)
        if err:
            return err

        draws = list(
            DrawResult.objects
            .filter(game=game)
            .order_by('-draw_date', '-draw_term')[:recent]
        )

        data = []
        ac_values = []
        for draw in draws:
            nums = sorted(draw.numbers_sorted)
            # 計算所有兩兩差值的不重複個數
            diffs = set()
            for a, b in combinations(nums, 2):
                diffs.add(abs(b - a))
            ac = len(diffs) - (len(nums) - 1)
            ac_values.append(ac)
            data.append({
                "draw_term": draw.draw_term,
                "draw_date": draw.draw_date.isoformat(),
                "ac_value": ac,
                "numbers": nums,
            })

        if ac_values:
            summary = {
                "avg": round(sum(ac_values) / len(ac_values), 1),
                "max": max(ac_values),
                "min": min(ac_values),
            }
        else:
            summary = {"avg": 0, "max": 0, "min": 0}

        return Response({
            "game": game.code,
            "recent_draws": recent,
            "summary": summary,
            "data": data,
        })

    # ------------------------------------------------------------------
    # GET /api/v1/draws/pair_frequency/?game={code}&recent={N}&top={M}
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='pair_frequency')
    def pair_frequency(self, request):
        """號碼組合頻率。"""
        game_code = request.query_params.get('game')
        game, err = self._get_game_or_error(game_code)
        if err:
            return err

        recent, err = self._parse_recent(request)
        if err:
            return err

        try:
            top = int(request.query_params.get('top', 20))
            if top <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"error": "'top' must be a positive integer."},
                status=400,
            )

        draws = list(
            DrawResult.objects
            .filter(game=game)
            .order_by('-draw_date', '-draw_term')[:recent]
        )

        pair_counter: dict[tuple[int, int], int] = defaultdict(int)
        for draw in draws:
            nums = sorted(draw.numbers_sorted)
            for a, b in combinations(nums, 2):
                pair_counter[(a, b)] += 1

        # 按次數排序取前 M 名
        sorted_pairs = sorted(pair_counter.items(), key=lambda x: x[1], reverse=True)[:top]

        top_pairs = [
            {"pair": list(pair), "count": count}
            for pair, count in sorted_pairs
        ]

        return Response({
            "game": game.code,
            "recent_draws": recent,
            "top_pairs": top_pairs,
        })

    # ------------------------------------------------------------------
    # POST /api/v1/draws/check_numbers/
    # ------------------------------------------------------------------

    @action(detail=False, methods=['post'], url_path='check_numbers')
    def check_numbers(self, request):
        """對獎：比對使用者選號與開獎號碼。"""
        game_code = request.data.get('game')
        game, err = self._get_game_or_error(game_code)
        if err:
            return err

        draw_term = request.data.get('draw_term')
        user_numbers = request.data.get('numbers')
        user_special = request.data.get('special_number')

        # 驗證 numbers
        if not user_numbers or not isinstance(user_numbers, list):
            return Response(
                {"error": "'numbers' is required and must be a list of integers."},
                status=400,
            )
        try:
            user_numbers = [int(n) for n in user_numbers]
        except (TypeError, ValueError):
            return Response(
                {"error": "'numbers' must be a list of integers."},
                status=400,
            )

        # 查詢開獎紀錄
        if draw_term:
            draw = (
                DrawResult.objects
                .filter(game=game, draw_term=draw_term)
                .first()
            )
            if not draw:
                return Response(
                    {"error": f"找不到 {game_code} 第 {draw_term} 期的開獎紀錄。"},
                    status=404,
                )
        else:
            draw = (
                DrawResult.objects
                .filter(game=game)
                .order_by('-draw_date', '-draw_term')
                .first()
            )
            if not draw:
                return Response(
                    {"error": f"{game_code} 尚無任何開獎紀錄。"},
                    status=404,
                )

        # 計算交集
        winning_set = set(draw.numbers_sorted)
        user_set = set(user_numbers)
        matched = sorted(winning_set & user_set)
        matched_count = len(matched)

        # 特別號比對
        special_matched = False
        if game.has_special and user_special is not None and draw.special_number is not None:
            try:
                special_matched = int(user_special) == draw.special_number
            except (TypeError, ValueError):
                pass

        # 結果描述
        if matched_count == 0:
            result_description = "未中獎"
        else:
            result_description = f"中{matched_count}個號碼"
        if special_matched:
            result_description += " + 特別號"

        return Response({
            "game": game.code,
            "draw_term": draw.draw_term,
            "draw_date": draw.draw_date.isoformat(),
            "winning_numbers": draw.numbers_sorted,
            "winning_special": draw.special_number,
            "your_numbers": user_numbers,
            "your_special": user_special,
            "matched_numbers": matched,
            "matched_count": matched_count,
            "special_matched": special_matched,
            "result_description": result_description,
        })

    # ------------------------------------------------------------------
    # GET /api/v1/draws/road_map/?game={code}&recent={N}
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='road_map')
    def road_map(self, request):
        """號碼走勢路珠圖：回傳近 N 期每期開獎號碼，供前端繪製矩陣。"""
        game_code = request.query_params.get('game')
        game, err = self._get_game_or_error(game_code)
        if err:
            return err

        recent, err = self._parse_recent(request, default=30)
        if err:
            return err

        draws = list(
            DrawResult.objects
            .filter(game=game)
            .order_by('-draw_date', '-draw_term')[:recent]
        )

        draws_data = [
            {
                "draw_term": draw.draw_term,
                "draw_date": draw.draw_date.isoformat(),
                "numbers_sorted": draw.numbers_sorted,
                "special_number": draw.special_number,
            }
            for draw in draws
        ]

        return Response({
            "game": game.code,
            "pool_size": game.main_pool_size,
            "recent_draws": recent,
            "draws": draws_data,
        })

    # ------------------------------------------------------------------
    # GET /api/v1/draws/export_csv/?game={code}&recent={N}
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='export_csv')
    def export_csv(self, request):
        """匯出開獎紀錄 CSV。"""
        game_code = request.query_params.get('game')
        game, err = self._get_game_or_error(game_code)
        if err:
            return err

        draws_qs = (
            DrawResult.objects
            .filter(game=game)
            .order_by('-draw_date', '-draw_term')
        )

        recent_param = request.query_params.get('recent')
        if recent_param:
            try:
                recent = int(recent_param)
                if recent <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                return Response(
                    {"error": "'recent' must be a positive integer."},
                    status=400,
                )
            draws_qs = draws_qs[:recent]

        draws = list(draws_qs)

        today = date.today().strftime('%Y%m%d')
        filename = f"{game.code}_draws_{today}.csv"

        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)

        # 標頭
        header = ['期數', '開獎日期']
        for i in range(1, game.main_pick_count + 1):
            header.append(f'號碼{i}')
        if game.has_special:
            header.append('特別號')
        writer.writerow(header)

        # 資料
        for draw in draws:
            row = [draw.draw_term, draw.draw_date.isoformat()]
            nums = draw.numbers_sorted
            for i in range(game.main_pick_count):
                row.append(nums[i] if i < len(nums) else '')
            if game.has_special:
                row.append(draw.special_number if draw.special_number is not None else '')
            writer.writerow(row)

        return response

    # ------------------------------------------------------------------
    # GET /api/v1/draws/export_stats_csv/?game={code}&recent={N}
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='export_stats_csv')
    def export_stats_csv(self, request):
        """匯出統計數據 CSV。"""
        game_code = request.query_params.get('game')
        game, err = self._get_game_or_error(game_code)
        if err:
            return err

        draws_qs = (
            DrawResult.objects
            .filter(game=game)
            .order_by('-draw_date', '-draw_term')
        )

        recent_param = request.query_params.get('recent')
        if recent_param:
            try:
                recent = int(recent_param)
                if recent <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                return Response(
                    {"error": "'recent' must be a positive integer."},
                    status=400,
                )
            draws_qs = draws_qs[:recent]

        draws = list(draws_qs)
        total_draws = len(draws)

        # 統計每個號碼出現次數
        counter: dict[int, int] = defaultdict(int)
        for draw in draws:
            for num in draw.numbers_sorted:
                counter[num] += 1

        # 計算遺漏值
        last_seen: dict[int, int] = {}
        for idx, draw in enumerate(draws):
            for num in draw.numbers_sorted:
                if num not in last_seen:
                    last_seen[num] = idx

        today = date.today().strftime('%Y%m%d')
        filename = f"{game.code}_stats_{today}.csv"

        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(['號碼', '出現次數', '出現率(%)', '遺漏值'])

        for num in range(1, game.main_pool_size + 1):
            count = counter.get(num, 0)
            pct = round(count / total_draws * 100, 2) if total_draws else 0.0
            missing = last_seen.get(num, total_draws)
            writer.writerow([num, count, pct, missing])

        return response

    # ------------------------------------------------------------------
    # POST /api/v1/draws/backtest/
    # ------------------------------------------------------------------

    @action(detail=False, methods=['post'], url_path='backtest')
    def backtest(self, request):
        """回測系統：模擬選號策略並計算命中統計。"""
        game_code = request.data.get('game')
        game, err = self._get_game_or_error(game_code)
        if err:
            return err

        strategy = request.data.get('strategy', 'random')
        if strategy not in ('random', 'hot_weighted', 'cold_weighted', 'balanced'):
            return Response(
                {"error": "strategy must be one of: random, hot_weighted, cold_weighted, balanced"},
                status=400,
            )

        try:
            recent = int(request.data.get('recent', 100))
            test_draws_count = int(request.data.get('test_draws', 50))
            simulations = int(request.data.get('simulations', 100))
        except (TypeError, ValueError):
            return Response(
                {"error": "recent, test_draws, simulations must be positive integers."},
                status=400,
            )

        # 上限檢查
        test_draws_count = min(test_draws_count, 200)
        simulations = min(simulations, 500)

        # 取所有開獎紀錄 (按日期降序)
        all_draws = list(
            DrawResult.objects
            .filter(game=game)
            .order_by('-draw_date', '-draw_term')
        )

        if len(all_draws) < test_draws_count + recent:
            available_test = max(0, len(all_draws) - recent)
            if available_test <= 0:
                return Response(
                    {"error": f"資料不足。需要至少 {recent + 1} 期資料，目前僅有 {len(all_draws)} 期。"},
                    status=400,
                )
            test_draws_count = available_test

        pool_size = game.main_pool_size
        pick_count = game.main_pick_count

        def _run_backtest(strat):
            """Run backtest for a given strategy, return results dict."""
            match_counts = []

            # 驗證集 = 最近 test_draws_count 期
            for test_idx in range(test_draws_count):
                target_draw = all_draws[test_idx]
                winning_set = set(target_draw.numbers_sorted)

                # 訓練集 = 該期之前 recent 期
                train_start = test_idx + 1
                train_end = train_start + recent
                train_draws = all_draws[train_start:train_end]

                # 計算訓練集頻率
                freq: dict[int, int] = defaultdict(int)
                for d in train_draws:
                    for num in d.numbers_sorted:
                        freq[num] += 1

                for _ in range(simulations):
                    picked = _pick_numbers(strat, pool_size, pick_count, freq)
                    matched = len(set(picked) & winning_set)
                    match_counts.append(matched)

            # 統計
            total = len(match_counts)
            distribution: dict[int, int] = defaultdict(int)
            for m in match_counts:
                distribution[m] += 1

            avg_match = round(sum(match_counts) / total, 2) if total else 0
            max_match = max(match_counts) if match_counts else 0
            hit_any = sum(1 for m in match_counts if m >= 1)
            hit_3plus = sum(1 for m in match_counts if m >= 3)

            return {
                "avg_match": avg_match,
                "max_match": max_match,
                "match_distribution": {
                    str(k): v for k, v in sorted(distribution.items())
                },
                "hit_rate_any": round(hit_any / total * 100, 1) if total else 0,
                "hit_rate_3plus": round(hit_3plus / total * 100, 1) if total else 0,
            }

        def _pick_numbers(strat, pool, pick, freq):
            """Generate a set of numbers based on strategy."""
            numbers = list(range(1, pool + 1))

            if strat == 'random':
                return sorted(random.sample(numbers, pick))

            elif strat == 'hot_weighted':
                weights = [1 + freq.get(n, 0) for n in numbers]
                chosen = _weighted_sample(numbers, weights, pick)
                return sorted(chosen)

            elif strat == 'cold_weighted':
                max_count = max(freq.values()) if freq else 0
                weights = [1 + (max_count - freq.get(n, 0)) for n in numbers]
                chosen = _weighted_sample(numbers, weights, pick)
                return sorted(chosen)

            elif strat == 'balanced':
                # 熱門取 ceil(n/2)，冷門取其餘
                hot_pick = math.ceil(pick / 2)
                cold_pick = pick - hot_pick

                sorted_by_freq = sorted(
                    numbers, key=lambda n: freq.get(n, 0), reverse=True
                )
                hot_pool = sorted_by_freq[:len(numbers) // 2]
                cold_pool = sorted_by_freq[len(numbers) // 2:]

                if len(hot_pool) < hot_pick:
                    hot_pick = len(hot_pool)
                    cold_pick = pick - hot_pick
                if len(cold_pool) < cold_pick:
                    cold_pick = len(cold_pool)
                    hot_pick = pick - cold_pick

                chosen = random.sample(hot_pool, hot_pick) + random.sample(cold_pool, cold_pick)
                return sorted(chosen)

            return sorted(random.sample(numbers, pick))

        def _weighted_sample(population, weights, k):
            """Weighted sampling without replacement."""
            pool = list(zip(population, weights))
            chosen = []
            for _ in range(k):
                total_w = sum(w for _, w in pool)
                r = random.uniform(0, total_w)
                cumulative = 0
                for idx, (item, w) in enumerate(pool):
                    cumulative += w
                    if cumulative >= r:
                        chosen.append(item)
                        pool.pop(idx)
                        break
            return chosen

        # 執行主策略
        main_results = _run_backtest(strategy)

        # 如果不是 random，同時跑 random 對照
        comparison = None
        if strategy != 'random':
            comparison = _run_backtest('random')

        return Response({
            "game": game.code,
            "strategy": strategy,
            "test_draws": test_draws_count,
            "simulations_per_draw": simulations,
            "total_simulations": test_draws_count * simulations,
            "results": main_results,
            "comparison": comparison,
        })
