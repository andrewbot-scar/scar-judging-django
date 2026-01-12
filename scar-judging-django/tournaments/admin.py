"""
Django admin configuration for SCAR Judge Portal
"""

from django.contrib import admin
from .models import Event, JudgeScore, ActiveMatch, RepairTimerReset


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['event_id', 'name', 'tournament_count', 'has_webhook', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['event_id', 'name']
    readonly_fields = ['created_at', 'updated_at']
    
    def tournament_count(self, obj):
        return len(obj.tournaments) if obj.tournaments else 0
    tournament_count.short_description = 'Tournaments'
    
    def has_webhook(self, obj):
        return bool(obj.discord_webhook_url)
    has_webhook.boolean = True
    has_webhook.short_description = 'Discord'


@admin.register(JudgeScore)
class JudgeScoreAdmin(admin.ModelAdmin):
    list_display = ['match_id', 'tournament_id', 'judge_count', 'finalized', 'updated_at']
    list_filter = ['finalized', 'created_at']
    search_fields = ['match_id', 'tournament_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ActiveMatch)
class ActiveMatchAdmin(admin.ModelAdmin):
    list_display = ['event_id', 'tournament_id', 'match_id', 'started_at']
    list_filter = ['event_id', 'started_at']
    search_fields = ['event_id', 'tournament_id', 'match_id']


@admin.register(RepairTimerReset)
class RepairTimerResetAdmin(admin.ModelAdmin):
    list_display = ['event_id', 'robot_name', 'reset_at']
    list_filter = ['event_id', 'reset_at']
    search_fields = ['event_id', 'robot_name']
