"""
台彩歷史開獎資料爬蟲 Management Command

從台灣彩券官方 API 抓取歷史開獎資料並存入資料庫。
支援今彩539、大樂透、威力彩三種彩券。
"""

import logging
import random
import time
from datetime import date, datetime

import requests
from django.core.management.base import BaseCommand, CommandError

from lottery.models import DrawResult, LotteryGame

logger = logging.getLogger(__name__)

# 彩券遊戲代碼 → API 對應設定
GAME_CONFIG = {
    "daily_cash": {
        "api_url": "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/DailyCash",
        "game_name": "DailyCash",
    },
    "lotto649": {
        "api_url": "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/Lotto649",
        "game_name": "Lotto649",
    },
    "super_lotto": {
        "api_url": "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/SuperLotto638",
        "game_name": "SuperLotto638",
    },
}

REQUEST_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
}

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # 指數退避基底秒數
REQUEST_TIMEOUT = 30  # 秒


class Command(BaseCommand):
    help = "從台灣彩券官方 API 抓取歷史開獎資料"

    def add_arguments(self, parser):
        parser.add_argument(
            "--game",
            type=str,
            choices=list(GAME_CONFIG.keys()),
            default=None,
            help="指定彩種 code (daily_cash / lotto649 / super_lotto)，不指定則抓取全部",
        )
        parser.add_argument(
            "--year",
            type=int,
            default=None,
            help="指定年份 (西元)，不指定則抓取最近 2 年",
        )

    def handle(self, *args, **options):
        game_code = options["game"]
        year = options["year"]

        # 決定要抓哪些遊戲
        if game_code:
            game_codes = [game_code]
        else:
            game_codes = list(GAME_CONFIG.keys())

        # 決定年份範圍
        current_year = date.today().year
        if year:
            years = [year]
        else:
            years = [current_year - 1, current_year]

        total_created = 0
        total_updated = 0

        for code in game_codes:
            try:
                game = LotteryGame.objects.get(code=code)
            except LotteryGame.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(
                        f"找不到遊戲 '{code}'，請先執行 seed_games 建立遊戲資料"
                    )
                )
                continue

            config = GAME_CONFIG[code]
            self.stdout.write(
                self.style.NOTICE(f"\n{'='*50}")
            )
            self.stdout.write(
                self.style.NOTICE(f"開始抓取: {game.name} ({code})")
            )

            for yr in years:
                created, updated = self._fetch_year(game, config, yr)
                total_created += created
                total_updated += updated

        self.stdout.write(
            self.style.SUCCESS(
                f"\n完成！新增 {total_created} 筆，更新 {total_updated} 筆"
            )
        )

    def _fetch_year(self, game, config, year):
        """抓取某遊戲某年度的開獎資料，回傳 (created_count, updated_count)"""
        self.stdout.write(f"  抓取 {year} 年資料...")
        logger.info("Fetching %s for year %d", game.code, year)

        payload = {
            "GameName": config["game_name"],
            "StartYear": str(year),
            "EndYear": str(year),
            "StartMonth": "01",
            "EndMonth": "12",
            "StartShowOrder": "",
            "EndShowOrder": "",
        }

        data = self._request_with_retry(config["api_url"], payload)
        if data is None:
            self.stderr.write(
                self.style.ERROR(f"  {year} 年資料抓取失敗，跳過")
            )
            return 0, 0

        # 解析回傳結構
        lottery_datas = (
            data.get("content", {}).get("lotteryDatas") or []
        )
        if not lottery_datas:
            self.stdout.write(
                self.style.WARNING(f"  {year} 年無開獎資料")
            )
            return 0, 0

        created_count = 0
        updated_count = 0

        for item in lottery_datas:
            try:
                created = self._save_draw(game, item)
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                logger.exception(
                    "Error saving draw term=%s for %s: %s",
                    item.get("period", "?"),
                    game.code,
                    e,
                )
                self.stderr.write(
                    self.style.ERROR(
                        f"  儲存第 {item.get('period', '?')} 期失敗: {e}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"  {year} 年: 新增 {created_count} 筆, 更新 {updated_count} 筆"
            )
        )
        return created_count, updated_count

    def _request_with_retry(self, url, payload):
        """帶重試邏輯的 POST 請求，回傳 JSON dict 或 None"""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # 請求間隔 1~2 秒
                if attempt > 1:
                    backoff = RETRY_BACKOFF_BASE ** attempt + random.uniform(0, 1)
                    logger.info("Retry #%d after %.1fs", attempt, backoff)
                    time.sleep(backoff)
                else:
                    time.sleep(random.uniform(1.0, 2.0))

                response = requests.post(
                    url,
                    json=payload,
                    headers=REQUEST_HEADERS,
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()

                data = response.json()

                # 台彩 API 可能回傳自定義錯誤碼
                if data.get("errorCode") and data["errorCode"] != "0":
                    logger.warning(
                        "API returned error: %s - %s",
                        data.get("errorCode"),
                        data.get("errorMessage", ""),
                    )
                    continue

                return data

            except requests.exceptions.Timeout:
                logger.warning(
                    "Request timeout (attempt %d/%d): %s",
                    attempt, MAX_RETRIES, url,
                )
            except requests.exceptions.HTTPError as e:
                logger.warning(
                    "HTTP error (attempt %d/%d): %s",
                    attempt, MAX_RETRIES, e,
                )
            except requests.exceptions.RequestException as e:
                logger.warning(
                    "Request failed (attempt %d/%d): %s",
                    attempt, MAX_RETRIES, e,
                )
            except ValueError as e:
                logger.warning(
                    "JSON decode error (attempt %d/%d): %s",
                    attempt, MAX_RETRIES, e,
                )

        logger.error("All %d attempts failed for %s", MAX_RETRIES, url)
        return None

    def _save_draw(self, game, item):
        """
        解析單筆開獎資料並 update_or_create 到資料庫。
        回傳 True 表示新增，False 表示更新。
        """
        draw_term = str(item["period"]).strip()

        # 解析日期 "2024/01/02"
        draw_date = datetime.strptime(
            item["lotteryDate"].strip(), "%Y/%m/%d"
        ).date()

        # 解析號碼 "01,15,23,31,39"
        raw_numbers_str = item.get("lotteryNo", "")
        numbers_ordered = [
            int(n.strip()) for n in raw_numbers_str.split(",") if n.strip()
        ]
        numbers_sorted = sorted(numbers_ordered)

        # 特別號
        special_number = None
        if game.has_special and item.get("specialNo"):
            special_raw = str(item["specialNo"]).strip()
            if special_raw:
                special_number = int(special_raw)

        # 銷售額
        total_sales = None
        if item.get("totalAmount") is not None:
            try:
                total_sales = int(item["totalAmount"])
            except (ValueError, TypeError):
                total_sales = None

        _, created = DrawResult.objects.update_or_create(
            game=game,
            draw_term=draw_term,
            defaults={
                "draw_date": draw_date,
                "numbers_ordered": numbers_ordered,
                "numbers_sorted": numbers_sorted,
                "special_number": special_number,
                "total_sales": total_sales,
                "raw_data": item,
            },
        )

        action = "新增" if created else "更新"
        logger.debug(
            "%s %s 第%s期 (%s)", action, game.code, draw_term, draw_date
        )
        return created
