"""
Django REST Framework serializers for SCAR Judge Portal
"""

from rest_framework import serializers
from .models import Event, JudgeScore, ActiveMatch, RepairTimerReset


class EventSerializer(serializers.ModelSerializer):
    """Serializer for Event model"""
    
    class Meta:
        model = Event
        fields = [
            'event_id', 'name', 'tournaments', 'scoring_criteria',
            'robot_images', 'discord_webhook_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class EventListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing events"""
    
    class Meta:
        model = Event
        fields = ['event_id', 'name', 'tournaments', 'created_at', 'updated_at']


class JudgeScoreSerializer(serializers.ModelSerializer):
    """Serializer for JudgeScore model"""
    judge_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = JudgeScore
        fields = [
            'match_id', 'tournament_id', 'competitor_a_id', 'competitor_b_id',
            'judges', 'finalized', 'result', 'judge_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'judge_count']


class JudgeScoreSummarySerializer(serializers.Serializer):
    """Summary serializer for judge scores (used in GET endpoint)"""
    match_id = serializers.CharField()
    judge_count = serializers.IntegerField()
    finalized = serializers.BooleanField()
    result = serializers.JSONField(allow_null=True)


class JudgeScoreDetailSerializer(serializers.Serializer):
    """Detailed serializer for judge scores popup"""
    match_id = serializers.CharField()
    competitor_a_id = serializers.IntegerField(allow_null=True)
    competitor_b_id = serializers.IntegerField(allow_null=True)
    judges = serializers.JSONField()
    judge_count = serializers.IntegerField()
    finalized = serializers.BooleanField()
    result = serializers.JSONField(allow_null=True)


class SubmitScoreSerializer(serializers.Serializer):
    """Serializer for submitting judge scores"""
    judge_id = serializers.CharField(required=True)
    tournament_id = serializers.CharField(required=True)
    competitor_a_id = serializers.IntegerField(required=True)
    competitor_b_id = serializers.IntegerField(required=True)
    scores = serializers.JSONField(required=False, allow_null=True)
    is_ko = serializers.BooleanField(required=False, default=False)
    ko_winner_id = serializers.IntegerField(required=False, allow_null=True)


class ActiveMatchSerializer(serializers.ModelSerializer):
    """Serializer for ActiveMatch model"""
    
    class Meta:
        model = ActiveMatch
        fields = ['event_id', 'tournament_id', 'match_id', 'started_at']
        read_only_fields = ['started_at']


class SetActiveMatchSerializer(serializers.Serializer):
    """Serializer for setting active match"""
    tournament_id = serializers.CharField(required=True)
    match_id = serializers.CharField(required=True)


class RepairTimerResetSerializer(serializers.ModelSerializer):
    """Serializer for RepairTimerReset model"""
    
    class Meta:
        model = RepairTimerReset
        fields = ['event_id', 'robot_name', 'reset_at']
        read_only_fields = ['reset_at']


class ResetRepairTimerSerializer(serializers.Serializer):
    """Serializer for resetting repair timer"""
    robot_name = serializers.CharField(required=True)
