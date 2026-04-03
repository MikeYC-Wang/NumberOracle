from django.core.management.base import BaseCommand
from lottery.models import LotteryGame


class Command(BaseCommand):
    help = '初始化三種彩券遊戲基礎資料'

    def handle(self, *args, **options):
        games = [
            {
                'code': 'daily_cash',
                'name': '今彩539',
                'main_pool_size': 39,
                'main_pick_count': 5,
                'has_special': False,
                'special_pool_size': None,
                'draw_schedule': 'Mon,Tue,Wed,Thu,Fri,Sat',
            },
            {
                'code': 'lotto649',
                'name': '大樂透',
                'main_pool_size': 49,
                'main_pick_count': 6,
                'has_special': True,
                'special_pool_size': 49,
                'draw_schedule': 'Tue,Fri',
            },
            {
                'code': 'super_lotto',
                'name': '威力彩',
                'main_pool_size': 38,
                'main_pick_count': 6,
                'has_special': True,
                'special_pool_size': 8,
                'draw_schedule': 'Mon,Thu',
            },
        ]

        for game_data in games:
            game, created = LotteryGame.objects.update_or_create(
                code=game_data['code'],
                defaults=game_data,
            )
            status = '新建' if created else '更新'
            self.stdout.write(self.style.SUCCESS(f'{status}: {game.name}'))

        self.stdout.write(self.style.SUCCESS('彩券遊戲基礎資料初始化完成'))
