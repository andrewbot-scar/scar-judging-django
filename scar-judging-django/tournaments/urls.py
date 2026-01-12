"""
URL routing for tournaments API
"""

from django.urls import path
from . import views

urlpatterns = [
    # Health check
    path('health', views.health_check, name='health_check'),
    
    # Events
    path('events', views.event_list, name='event_list'),
    path('events/<str:event_id>', views.event_detail, name='event_detail'),
    
    # Tournaments (Challonge proxy)
    path('tournaments/<str:tournament_id>', views.tournament_detail, name='tournament_detail'),
    path('tournaments/<str:tournament_id>/participants', views.tournament_participants, name='tournament_participants'),
    path('tournaments/<str:tournament_id>/matches', views.tournament_matches, name='tournament_matches'),
    path('tournaments/<str:tournament_id>/matches/<str:match_id>', views.match_detail, name='match_detail'),
    path('tournaments/<str:tournament_id>/matches/<str:match_id>/reopen', views.match_reopen, name='match_reopen'),
    
    # Judge scoring
    path('matches/<str:match_id>/scores', views.match_scores, name='match_scores'),
    path('matches/<str:match_id>/scores/details', views.match_scores_details, name='match_scores_details'),
    path('matches/<str:match_id>/scores/<str:judge_id>', views.delete_judge_score, name='delete_judge_score'),
    
    # Active matches
    path('events/<str:event_id>/active-matches', views.active_matches, name='active_matches'),
    path('events/<str:event_id>/active-match', views.set_active_match, name='set_active_match'),
    path('events/<str:event_id>/active-match/<str:tournament_id>', views.clear_active_match, name='clear_active_match'),
    
    # Repair timers
    path('events/<str:event_id>/repair-resets', views.repair_resets, name='repair_resets'),
    path('events/<str:event_id>/repair-reset', views.reset_repair_timer, name='reset_repair_timer'),
    path('events/<str:event_id>/repair-reset/<str:robot_name>', views.clear_repair_reset, name='clear_repair_reset'),
    
    # Discord
    path('events/<str:event_id>/test-discord', views.test_discord_webhook, name='test_discord_webhook'),
    
    # RCE scraper
    path('scrape-rce', views.scrape_rce, name='scrape_rce'),
]
