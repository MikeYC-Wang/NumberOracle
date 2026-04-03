from django.contrib import admin
from .models import LotteryGame, DrawResult


@admin.register(LotteryGame)
class LotteryGameAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'main_pool_size', 'main_pick_count', 'has_special', 'is_active')
    list_filter = ('is_active', 'has_special')
    search_fields = ('code', 'name')


@admin.register(DrawResult)
class DrawResultAdmin(admin.ModelAdmin):
    list_display = ('game', 'draw_term', 'draw_date', 'numbers_sorted', 'special_number')
    list_filter = ('game',)
    search_fields = ('draw_term',)
    ordering = ('-draw_date',)
