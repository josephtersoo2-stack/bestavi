from django.contrib import admin
from .models import BotConfig, ExtractedOdds, BetRecord, BotLog


@admin.register(BotConfig)
class BotConfigAdmin(admin.ModelAdmin):
    list_display = ('base_stake', 'strategy', 'multiplier', 'auto_cashout', 'max_stake', 'dry_run', 'updated_at')


@admin.register(ExtractedOdds)
class ExtractedOddsAdmin(admin.ModelAdmin):
    list_display = ('id', 'multiplier', 'site', 'is_under_2x', 'is_over_10x', 'timestamp')
    list_filter = ('site', 'is_under_2x', 'is_over_10x', 'timestamp')
    search_fields = ('multiplier', 'site')


@admin.register(BetRecord)
class BetRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'stake', 'cashout_target', 'crash_multiplier', 'won', 'profit_loss', 'balance_after', 'created_at')
    list_filter = ('won', 'site', 'created_at')


@admin.register(BotLog)
class BotLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'level', 'message', 'created_at')
    list_filter = ('level', 'created_at')
    search_fields = ('message',)
