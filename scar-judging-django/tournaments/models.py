"""
Database models for SCAR Judge Portal
"""

from django.db import models
from django.utils import timezone


class Event(models.Model):
    """
    An event containing one or more tournaments.
    Example: "Clash at the Comb 2026" with 150g and 1lb brackets
    """
    event_id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    tournaments = models.JSONField(default=list, help_text="List of Challonge tournament URLs")
    scoring_criteria = models.JSONField(
        null=True, 
        blank=True,
        help_text="Custom scoring categories, e.g. [{'id': 'aggression', 'name': 'Aggression', 'points': 3}]"
    )
    robot_images = models.JSONField(
        null=True, 
        blank=True,
        help_text="Map of robot name to image URL"
    )
    discord_webhook_url = models.URLField(
        max_length=512, 
        null=True, 
        blank=True,
        help_text="Discord webhook URL for match notifications"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.event_id})"

    def get_default_scoring_criteria(self):
        """Return scoring criteria or default if not set"""
        if self.scoring_criteria:
            return self.scoring_criteria
        return [
            {'id': 'aggression', 'name': 'Aggression', 'points': 3},
            {'id': 'damage', 'name': 'Damage', 'points': 5},
            {'id': 'control', 'name': 'Control', 'points': 3},
        ]


class JudgeScore(models.Model):
    """
    Stores judge scores for a match.
    Each match has one JudgeScore record containing all 3 judges' submissions.
    """
    match_id = models.CharField(max_length=255, unique=True, help_text="Challonge match ID")
    tournament_id = models.CharField(max_length=255, help_text="Challonge tournament URL")
    competitor_a_id = models.IntegerField(null=True, blank=True)
    competitor_b_id = models.IntegerField(null=True, blank=True)
    judges = models.JSONField(
        default=dict,
        help_text="Map of judge_id to score data"
    )
    finalized = models.BooleanField(default=False)
    result = models.JSONField(
        null=True, 
        blank=True,
        help_text="Final calculated result after all judges submit"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Match {self.match_id} - {'Finalized' if self.finalized else 'Pending'}"

    @property
    def judge_count(self):
        return len(self.judges)

    def add_judge_score(self, judge_id, scores, is_ko=False, ko_winner_id=None):
        """Add or update a judge's score submission"""
        self.judges[judge_id] = {
            'scores': scores,
            'isKO': is_ko,
            'koWinnerId': ko_winner_id,
            'submittedAt': timezone.now().isoformat(),
        }
        self.save()

    def remove_judge_score(self, judge_id):
        """Remove a judge's score (for editing)"""
        if judge_id in self.judges:
            del self.judges[judge_id]
            self.save()
            return True
        return False

    def calculate_result(self):
        """
        Calculate match result based on all judge scores.
        Returns dict with winnerId, winMethod, scoreA, scoreB
        """
        judges = list(self.judges.values())
        
        # Check for KO majority (2/3 judges)
        ko_votes = {}
        for judge in judges:
            if judge.get('isKO') and judge.get('koWinnerId'):
                winner_id = judge['koWinnerId']
                ko_votes[winner_id] = ko_votes.get(winner_id, 0) + 1

        # If any competitor has 2+ KO votes, it's a KO
        for winner_id, votes in ko_votes.items():
            if votes >= 2:
                max_points_per_judge = 11  # Default total
                total_max_points = max_points_per_judge * 3  # 33 total
                
                is_winner_a = int(winner_id) == self.competitor_a_id
                return {
                    'winnerId': int(winner_id),
                    'winMethod': 'ko',
                    'scoreA': total_max_points if is_winner_a else 0,
                    'scoreB': 0 if is_winner_a else total_max_points,
                    'koVotes': votes,
                }

        # Calculate point totals
        total_a = 0
        total_b = 0

        for judge in judges:
            if judge.get('scores'):
                scores = judge['scores']
                judge_score_a = (
                    scores.get('aggression', 0) + 
                    scores.get('damage', 0) + 
                    scores.get('control', 0)
                )
                judge_score_b = 11 - judge_score_a
                total_a += judge_score_a
                total_b += judge_score_b

        # Determine winner by points
        winner_id = self.competitor_a_id if total_a > total_b else self.competitor_b_id

        return {
            'winnerId': winner_id,
            'winMethod': 'points',
            'scoreA': total_a,
            'scoreB': total_b,
        }


class ActiveMatch(models.Model):
    """
    Tracks which match is currently "Now Fighting" for each tournament.
    Only one active match per tournament at a time.
    """
    event_id = models.CharField(max_length=255)
    tournament_id = models.CharField(max_length=255)
    match_id = models.CharField(max_length=255)
    started_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['event_id', 'tournament_id']

    def __str__(self):
        return f"Active: {self.tournament_id} - Match {self.match_id}"


class RepairTimerReset(models.Model):
    """
    Tracks manual repair timer resets for robots.
    When a robot's timer is reset, their 20-minute countdown starts from this time.
    """
    event_id = models.CharField(max_length=255)
    robot_name = models.CharField(max_length=255)
    reset_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['event_id', 'robot_name']

    def __str__(self):
        return f"Repair reset: {self.robot_name} at {self.reset_at}"
