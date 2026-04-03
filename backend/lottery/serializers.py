from rest_framework import serializers
from .models import LotteryGame, DrawResult


class LotteryGameSerializer(serializers.ModelSerializer):
    class Meta:
        model = LotteryGame
        fields = [
            'id', 'code', 'name',
            'main_pool_size', 'main_pick_count',
            'has_special', 'special_pool_size',
            'draw_schedule', 'is_active',
        ]


class DrawResultSerializer(serializers.ModelSerializer):
    game_name = serializers.CharField(source='game.name', read_only=True)
    game_code = serializers.CharField(source='game.code', read_only=True)

    class Meta:
        model = DrawResult
        fields = [
            'id', 'game', 'game_name', 'game_code',
            'draw_term', 'draw_date',
            'numbers_ordered', 'numbers_sorted',
            'special_number', 'total_sales',
        ]
