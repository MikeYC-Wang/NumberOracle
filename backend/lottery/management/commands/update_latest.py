"""
自動更新最新開獎資料 Management Command

自動抓取三種彩券最近 1 個月的開獎資料，適合用排程 (cron) 每日執行。
用法: python manage.py update_latest
"""

import logging
import random
import time
from datetime import date

import requests
from django.core.management.base import BaseCommand

from lottery.models import DrawResult, LotteryGame

from .fetch_draws import (
    BASE_URL,
    GAME_CONFIG,
    MAX_RETRIES,
    REQUEST_HEADERS,
    REQUEST_TIMEOUT,
    RETRY_BACKOFF_BASE,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "自動抓取三種彩券最近 1 個月的最新開獎資料"

    def handle(self, *args, **options):
        today = date.today()
        year = today.year
        month = today.month

        # 抓當月以及上個月 (避免月初漏抓)
        months_to_fetch = [(year, month)]
        if month == 1:
            months_to_fetch.append((year - 1, 12))
        else:
            months_to_fetch.append((year, month - 1))

        total_created = 0
        total_updated = 0

        for code, config in GAME_CONFIG.items():
            try:
                game = LotteryGame.objects.get(code=code)
            except LotteryGame.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(
                        f"找不到遊戲 '{code}'，請先執行 seed_games 建立遊戲資料"
                    )
                )
                continue

            self.stdout.write(
                self.style.NOTICE(f"更新: {game.name} ({code})")
            )

            for yr, mo in months_to_fetch:
                created, updated = self._fetch_month(game, config, yr, mo)
                total_created += created
                total_updated += updated

        self.stdout.write(
            self.style.SUCCESS(
                f"\n完成！新增 {total_created} 筆，更新 {total_updated} 筆"
            )
        )

    def _fetch_month(self, game, config, year, month):
        """抓取某遊戲某年某月的開獎資料，回傳 (created_count, updated_count)"""
        month_str = f"{year}-{month:02d}"
        url = f"{BASE_URL}/{config['api_path']}"
        params = {
            "period": "",
            "month": month_str,
            "pageSize": "50",
        }

        data = self._request_with_retry(url, params)
        if data is None:
            self.stderr.write(
                self.style.ERROR(f"  {month_str} 資料抓取失敗，跳過")
            )
            return 0, 0

        content = data.get("content") or {}
        lottery_items = content.get(config["result_key"]) or []

        if not lottery_items:
            logger.debug("No data for %s %s", game.code, month_str)
            return 0, 0

        created_count = 0
        updated_count = 0

        for item in lottery_items:
            try:
                created = self._save_draw(game, config, item)
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

        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"  {month_str}: 新增 {created_count} 筆, 更新 {updated_count} 筆"
                )
            )

        return created_count, updated_count

    def _request_with_retry(self, url, params):
        """帶重試邏輯的 GET 請求，回傳 JSON dict 或 None"""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if attempt > 1:
                    backoff = RETRY_BACKOFF_BASE ** attempt + random.uniform(0, 1)
                    logger.info("Retry #%d after %.1fs", attempt, backoff)
                    time.sleep(backoff)
                else:
                    time.sleep(random.uniform(0.3, 0.8))

                response = requests.get(
                    url,
                    params=params,
                    headers=REQUEST_HEADERS,
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                data = response.json()

                if data.get("rtCode") is not None and data["rtCode"] != 0:
                    logger.warning(
                        "API returned error: rtCode=%s, rtMsg=%s",
                        data.get("rtCode"),
                        data.get("rtMsg", ""),
                    )
                    continue

                return data

            except requests.exceptions.Timeout:
                logger.warning("Request timeout (attempt %d/%d)", attempt, MAX_RETRIES)
            except requests.exceptions.HTTPError as e:
                logger.warning("HTTP error (attempt %d/%d): %s", attempt, MAX_RETRIES, e)
            except requests.exceptions.RequestException as e:
                logger.warning("Request failed (attempt %d/%d): %s", attempt, MAX_RETRIES, e)
            except ValueError as e:
                logger.warning("JSON decode error (attempt %d/%d): %s", attempt, MAX_RETRIES, e)

        logger.error("All %d attempts failed for %s", MAX_RETRIES, url)
        return None

    def _save_draw(self, game, config, item):
        """解析單筆開獎資料並 update_or_create，回傳 True=新增 / False=更新"""
        from datetime import datetime

        draw_term = str(item["period"]).strip()
        date_str = item["lotteryDate"].strip()
        draw_date = datetime.fromisoformat(date_str).date()

        main_count = config["main_count"]
        has_special = config["has_special"]

        all_numbers_sorted = item.get("drawNumberSize", [])
        all_numbers_appear = item.get("drawNumberAppear", [])

        numbers_sorted = sorted(all_numbers_sorted[:main_count])
        numbers_ordered = list(all_numbers_appear[:main_count])

        special_number = None
        if has_special and len(all_numbers_sorted) > main_count:
            special_number = all_numbers_sorted[main_count]

        total_sales = None
        sell_amount = item.get("sellAmount") or item.get("totalAmount")
        if sell_amount is not None:
            try:
                total_sales = int(sell_amount)
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
        logger.debug("%s %s 第%s期 (%s)", action, game.code, draw_term, draw_date)
        return created
