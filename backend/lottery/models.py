from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex


class LotteryGame(models.Model):
    """遊戲種類主表"""

    code = models.CharField(
        max_length=20, unique=True,
        help_text="遊戲代碼，如 daily_cash, lotto649, super_lotto"
    )
    name = models.CharField(max_length=50, help_text="遊戲名稱，如 今彩539")
    main_pool_size = models.SmallIntegerField(help_text="主區可選號碼上限")
    main_pick_count = models.SmallIntegerField(help_text="主區開出幾球")
    has_special = models.BooleanField(default=False, help_text="是否有特別號")
    special_pool_size = models.SmallIntegerField(
        null=True, blank=True,
        help_text="特別號池大小 (大樂透=49, 威力彩=8)"
    )
    draw_schedule = models.CharField(
        max_length=100, blank=True, default='',
        help_text="開獎日描述，如 Mon,Thu"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'lottery_games'
        verbose_name = '彩券遊戲'
        verbose_name_plural = '彩券遊戲'

    def __str__(self):
        return f"{self.name} ({self.code})"


class DrawResult(models.Model):
    """開獎紀錄明細表"""

    game = models.ForeignKey(
        LotteryGame, on_delete=models.CASCADE,
        related_name='draws', help_text="所屬彩券遊戲"
    )
    draw_term = models.CharField(max_length=20, help_text="期數，如 113000001")
    draw_date = models.DateField(help_text="開獎日期")
    numbers_ordered = ArrayField(
        models.IntegerField(),
        help_text="依落球順序 (原始開出順序)"
    )
    numbers_sorted = ArrayField(
        models.IntegerField(),
        help_text="依大小排序 (方便統計查詢)"
    )
    special_number = models.IntegerField(
        null=True, blank=True,
        help_text="特別號 (大樂透/威力彩第二區)"
    )
    total_sales = models.BigIntegerField(
        null=True, blank=True,
        help_text="該期銷售額"
    )
    raw_data = models.JSONField(
        null=True, blank=True,
        help_text="原始爬蟲回傳資料 (備查)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'draw_results'
        verbose_name = '開獎紀錄'
        verbose_name_plural = '開獎紀錄'
        constraints = [
            models.UniqueConstraint(
                fields=['game', 'draw_term'],
                name='uq_game_term'
            )
        ]
        indexes = [
            GinIndex(fields=['numbers_sorted'], name='idx_numbers_sorted_gin'),
            GinIndex(fields=['numbers_ordered'], name='idx_numbers_ordered_gin'),
            models.Index(fields=['game', '-draw_date'], name='idx_game_date'),
            models.Index(fields=['game', 'draw_term'], name='idx_game_term'),
        ]

    def __str__(self):
        return f"{self.game.name} 第{self.draw_term}期 - {self.draw_date}"
