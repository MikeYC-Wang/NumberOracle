from django.contrib.auth.models import User
from django.db import models
from django.contrib.postgres.fields import ArrayField


class SavedPrediction(models.Model):
    """使用者收藏的預測號碼"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='saved_predictions'
    )
    game = models.ForeignKey(
        'lottery.LotteryGame', on_delete=models.CASCADE
    )
    numbers = ArrayField(
        models.IntegerField(),
        help_text="主號碼 (已排序)",
    )
    special_number = models.IntegerField(null=True, blank=True)
    strategy = models.CharField(max_length=30, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    # 對獎結果 (開獎後填入)
    checked_term = models.CharField(max_length=20, null=True, blank=True)
    matched_count = models.IntegerField(null=True, blank=True)
    special_matched = models.BooleanField(default=False)
    checked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'saved_predictions'
        ordering = ['-created_at']
        verbose_name = '收藏預測'
        verbose_name_plural = '收藏預測'

    def __str__(self):
        return f"{self.user.username} - {self.game_id} - {self.numbers}"
