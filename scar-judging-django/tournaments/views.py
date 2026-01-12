"""
API views for SCAR Judge Portal
"""

import json
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Event, JudgeScore, ActiveMatch, RepairTimerReset
from .serializers import (
    EventSerializer, EventListSerializer, JudgeScoreSummarySerializer,
    JudgeScoreDetailSerializer, SubmitScoreSerializer, SetActiveMatchSerializer,
    ResetRepairTimerSerializer
)
from .services import (
    get_challonge_service, post_match_to_discord, send_test_webhook,
    get_robot_image, scrape_rce_robots
)


# =============================================================================
# HEALTH CHECK
# =============================================================================

@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    from django.conf import settings
    from django.db import connection
    
    health = {
        'status': 'ok',
        'database': 'unknown',
        'challonge': 'configured' if settings.CHALLONGE_API_KEY else 'not configured',
    }
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        health['database'] = 'connected'
    except Exception as e:
        health['database'] = f'error: {str(e)}'
        health['status'] = 'degraded'
    
    return Response(health)


# =============================================================================
# EVENT ENDPOINTS
# =============================================================================

@api_view(['GET', 'POST'])
def event_list(request):
    """List all events or create/update an event"""
    
    if request.method == 'GET':
        events = Event.objects.all()
        serializer = EventListSerializer(events, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        event_id = request.data.get('eventId')
        if not event_id:
            return Response({'error': 'eventId is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        tournaments = request.data.get('tournaments', [])
        if not isinstance(tournaments, list):
            return Response({'error': 'tournaments must be an array'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or update event
        event, created = Event.objects.update_or_create(
            event_id=event_id,
            defaults={
                'name': request.data.get('name', event_id),
                'tournaments': tournaments,
                'scoring_criteria': request.data.get('scoringCriteria'),
                'robot_images': request.data.get('robotImages'),
                'discord_webhook_url': request.data.get('discordWebhookUrl'),
            }
        )
        
        print(f"Event {'created' if created else 'updated'}: {event_id} with {len(tournaments)} tournaments")
        
        serializer = EventSerializer(event)
        return Response({
            'success': True,
            'event': serializer.data,
        })


@api_view(['GET', 'DELETE'])
def event_detail(request, event_id):
    """Get or delete an event"""
    
    try:
        event = Event.objects.get(event_id=event_id)
    except Event.DoesNotExist:
        return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = EventSerializer(event)
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        event.delete()
        print(f"Event deleted: {event_id}")
        return Response({'success': True, 'message': f'Event {event_id} deleted'})


# =============================================================================
# TOURNAMENT ENDPOINTS (Challonge Proxy)
# =============================================================================

@api_view(['GET'])
def tournament_detail(request, tournament_id):
    """Get tournament details from Challonge"""
    try:
        challonge = get_challonge_service()
        data = challonge.get_tournament(tournament_id)
        return Response(data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def tournament_participants(request, tournament_id):
    """Get tournament participants from Challonge"""
    try:
        challonge = get_challonge_service()
        data = challonge.get_participants(tournament_id)
        return Response(data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def tournament_matches(request, tournament_id):
    """Get tournament matches from Challonge"""
    try:
        challonge = get_challonge_service()
        data = challonge.get_matches(tournament_id)
        return Response(data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT'])
def match_detail(request, tournament_id, match_id):
    """Get or update a match"""
    challonge = get_challonge_service()
    
    if request.method == 'GET':
        try:
            data = challonge.get_match(tournament_id, match_id)
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        winner_id = request.data.get('winner_id')
        if not winner_id:
            return Response({'error': 'winner_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        scores_csv = request.data.get('scores_csv', '1-0')
        
        try:
            data = challonge.update_match(tournament_id, match_id, winner_id, scores_csv)
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def match_reopen(request, tournament_id, match_id):
    """Reopen a match"""
    try:
        challonge = get_challonge_service()
        data = challonge.reopen_match(tournament_id, match_id)
        return Response(data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# JUDGE SCORING ENDPOINTS
# =============================================================================

@api_view(['GET', 'POST'])
def match_scores(request, match_id):
    """Get or submit judge scores for a match"""
    
    if request.method == 'GET':
        try:
            score = JudgeScore.objects.get(match_id=match_id)
            return Response({
                'matchId': match_id,
                'judgeCount': score.judge_count,
                'finalized': score.finalized,
                'result': score.result,
            })
        except JudgeScore.DoesNotExist:
            return Response({
                'matchId': match_id,
                'judgeCount': 0,
                'finalized': False,
                'result': None,
            })
    
    elif request.method == 'POST':
        serializer = SubmitScoreSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        judge_id = data['judge_id']
        tournament_id = data['tournament_id']
        
        # Get or create JudgeScore
        score, created = JudgeScore.objects.get_or_create(
            match_id=match_id,
            defaults={
                'tournament_id': tournament_id,
                'competitor_a_id': data['competitor_a_id'],
                'competitor_b_id': data['competitor_b_id'],
            }
        )
        
        # Add judge's score
        score.add_judge_score(
            judge_id=judge_id,
            scores=data.get('scores'),
            is_ko=data.get('is_ko', False),
            ko_winner_id=data.get('ko_winner_id'),
        )
        
        # Check if all 3 judges have submitted
        if score.judge_count >= 3 and not score.finalized:
            # Calculate result
            result = score.calculate_result()
            score.result = result
            score.finalized = True
            score.save()
            
            # Report to Challonge
            try:
                challonge = get_challonge_service()
                challonge_result = challonge.update_match(
                    tournament_id,
                    match_id,
                    result['winnerId'],
                    f"{result['scoreA']}-{result['scoreB']}"
                )
                
                # Save judge breakdown to Challonge attachment
                try:
                    breakdown = json.dumps({
                        'type': 'judge_scores',
                        'judges': score.judges,
                        'competitorAId': score.competitor_a_id,
                        'competitorBId': score.competitor_b_id,
                        'result': result,
                    })
                    challonge.create_match_attachment(tournament_id, match_id, breakdown)
                except Exception as e:
                    print(f"Failed to save judge breakdown: {e}")
                
            except Exception as e:
                print(f"Failed to report to Challonge: {e}")
                challonge_result = {'error': str(e)}
            
            # Send Discord notification
            try:
                _send_discord_notification(score, result)
            except Exception as e:
                print(f"Discord notification error (non-fatal): {e}")
            
            return Response({
                'success': True,
                'judgeCount': score.judge_count,
                'finalized': True,
                'result': result,
                'challongeResponse': challonge_result,
            })
        
        return Response({
            'success': True,
            'judgeCount': score.judge_count,
            'finalized': False,
            'message': f'Waiting for {3 - score.judge_count} more judge(s)',
        })


def _send_discord_notification(score, result):
    """Helper to send Discord notification after match finalization"""
    tournament_id = score.tournament_id
    
    print(f"Match finalized! Attempting Discord notification for tournament: {tournament_id}")
    
    # Find event containing this tournament
    event = None
    for e in Event.objects.all():
        if tournament_id in (e.tournaments or []):
            event = e
            break
        # Also try text search as fallback
        if tournament_id in str(e.tournaments):
            event = e
            break
    
    if not event:
        print(f"No event found containing tournament: {tournament_id}")
        return
    
    if not event.discord_webhook_url:
        print(f"No Discord webhook configured for event: {event.event_id}")
        return
    
    print(f"Found event: {event.event_id}, webhook configured: True")
    
    # Get competitor names and tournament info
    try:
        challonge = get_challonge_service()
        names = challonge.get_competitor_names(
            tournament_id,
            score.competitor_a_id,
            score.competitor_b_id
        )
        tournament_name = challonge.get_tournament_name(tournament_id)
        match_num = challonge.get_match_number(tournament_id, score.match_id)
    except Exception as e:
        print(f"Error fetching Challonge data: {e}")
        names = {'competitorA': 'Unknown', 'competitorB': 'Unknown'}
        tournament_name = tournament_id
        match_num = score.match_id
    
    competitor_a = names.get('competitorA', 'Unknown')
    competitor_b = names.get('competitorB', 'Unknown')
    
    winner = competitor_a if result['winnerId'] == score.competitor_a_id else competitor_b
    loser = competitor_b if result['winnerId'] == score.competitor_a_id else competitor_a
    
    robot_images = event.robot_images or {}
    
    print(f"Posting to Discord: {winner} defeats {loser} in Match {match_num}")
    
    discord_result = post_match_to_discord(event.discord_webhook_url, {
        'winner': winner,
        'loser': loser,
        'scoreA': result['scoreA'],
        'scoreB': result['scoreB'],
        'winMethod': result['winMethod'],
        'tournamentName': tournament_name,
        'matchNum': match_num,
        'eventName': event.name,
        'winnerImageUrl': get_robot_image(robot_images, winner),
        'loserImageUrl': get_robot_image(robot_images, loser),
    })
    
    print(f"Discord notification result: {discord_result}")


@api_view(['GET'])
def match_scores_details(request, match_id):
    """Get detailed judge scores for match popup"""
    tournament_id = request.query_params.get('tournamentId', '')
    
    try:
        score = JudgeScore.objects.get(match_id=match_id)
        return Response({
            'matchId': match_id,
            'competitorAId': score.competitor_a_id,
            'competitorBId': score.competitor_b_id,
            'judges': score.judges,
            'judgeCount': score.judge_count,
            'finalized': score.finalized,
            'result': score.result,
        })
    except JudgeScore.DoesNotExist:
        # Try to fetch from Challonge attachments
        if tournament_id:
            try:
                challonge = get_challonge_service()
                attachments = challonge.get_match_attachments(tournament_id, match_id)
                
                for att in attachments:
                    attachment = att.get('match_attachment', {})
                    description = attachment.get('description', '')
                    try:
                        data = json.loads(description)
                        if data.get('type') == 'judge_scores':
                            # Cache in database
                            score = JudgeScore.objects.create(
                                match_id=match_id,
                                tournament_id=tournament_id,
                                competitor_a_id=data.get('competitorAId'),
                                competitor_b_id=data.get('competitorBId'),
                                judges=data.get('judges', {}),
                                finalized=True,
                                result=data.get('result'),
                            )
                            return Response({
                                'matchId': match_id,
                                'competitorAId': score.competitor_a_id,
                                'competitorBId': score.competitor_b_id,
                                'judges': score.judges,
                                'judgeCount': score.judge_count,
                                'finalized': score.finalized,
                                'result': score.result,
                            })
                    except (json.JSONDecodeError, KeyError):
                        pass
            except Exception as e:
                print(f"Error fetching from Challonge: {e}")
        
        return Response({
            'matchId': match_id,
            'competitorAId': None,
            'competitorBId': None,
            'judges': {},
            'judgeCount': 0,
            'finalized': False,
            'result': None,
        })


@api_view(['DELETE'])
def delete_judge_score(request, match_id, judge_id):
    """Delete a judge's score (for editing)"""
    try:
        score = JudgeScore.objects.get(match_id=match_id)
    except JudgeScore.DoesNotExist:
        return Response({'error': 'Score not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if score.finalized:
        return Response({'error': 'Match already finalized'}, status=status.HTTP_400_BAD_REQUEST)
    
    if score.remove_judge_score(judge_id):
        return Response({'success': True, 'message': 'Score deleted, you can resubmit'})
    
    return Response({'error': 'Score not found'}, status=status.HTTP_404_NOT_FOUND)


# =============================================================================
# ACTIVE MATCH ENDPOINTS
# =============================================================================

@api_view(['GET'])
def active_matches(request, event_id):
    """Get all active matches for an event"""
    matches = ActiveMatch.objects.filter(event_id=event_id)
    result = {}
    for match in matches:
        result[match.tournament_id] = {
            'matchId': match.match_id,
            'startedAt': match.started_at.isoformat(),
        }
    return Response(result)


@api_view(['POST'])
def set_active_match(request, event_id):
    """Set the currently fighting match for a tournament"""
    serializer = SetActiveMatchSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    match, created = ActiveMatch.objects.update_or_create(
        event_id=event_id,
        tournament_id=data['tournament_id'],
        defaults={'match_id': data['match_id']}
    )
    
    print(f"Active match set: event={event_id}, tournament={data['tournament_id']}, match={data['match_id']}")
    
    return Response({
        'success': True,
        'eventId': event_id,
        'tournamentId': data['tournament_id'],
        'matchId': data['match_id'],
    })


@api_view(['DELETE'])
def clear_active_match(request, event_id, tournament_id):
    """Clear the active match for a tournament"""
    deleted, _ = ActiveMatch.objects.filter(
        event_id=event_id,
        tournament_id=tournament_id
    ).delete()
    
    print(f"Active match cleared: event={event_id}, tournament={tournament_id}")
    
    return Response({'success': True, 'message': 'Active match cleared'})


# =============================================================================
# REPAIR TIMER ENDPOINTS
# =============================================================================

@api_view(['GET'])
def repair_resets(request, event_id):
    """Get all repair timer resets for an event"""
    resets = RepairTimerReset.objects.filter(event_id=event_id)
    result = {}
    for reset in resets:
        result[reset.robot_name] = reset.reset_at.isoformat()
    return Response(result)


@api_view(['POST'])
def reset_repair_timer(request, event_id):
    """Reset a robot's repair timer"""
    serializer = ResetRepairTimerSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    robot_name = serializer.validated_data['robot_name']
    
    reset, created = RepairTimerReset.objects.update_or_create(
        event_id=event_id,
        robot_name=robot_name,
    )
    
    print(f"Repair timer reset: event={event_id}, robot={robot_name}")
    
    return Response({
        'success': True,
        'eventId': event_id,
        'robotName': robot_name,
        'resetAt': reset.reset_at.isoformat(),
    })


@api_view(['DELETE'])
def clear_repair_reset(request, event_id, robot_name):
    """Clear a robot's repair timer reset"""
    deleted, _ = RepairTimerReset.objects.filter(
        event_id=event_id,
        robot_name=robot_name
    ).delete()
    
    print(f"Repair timer reset cleared: event={event_id}, robot={robot_name}")
    
    return Response({'success': True, 'message': 'Repair timer reset cleared'})


# =============================================================================
# DISCORD WEBHOOK ENDPOINTS
# =============================================================================

@api_view(['POST'])
def test_discord_webhook(request, event_id):
    """Test Discord webhook for an event"""
    try:
        event = Event.objects.get(event_id=event_id)
    except Event.DoesNotExist:
        return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if not event.discord_webhook_url:
        return Response(
            {'error': 'No Discord webhook URL configured for this event'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    result = send_test_webhook(event.discord_webhook_url, event.name)
    
    if result['success']:
        return Response({'success': True, 'message': 'Test message sent to Discord!'})
    else:
        return Response(
            {'error': f"Failed to send test message: {result.get('error')}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =============================================================================
# RCE SCRAPER ENDPOINT
# =============================================================================

@api_view(['GET'])
def scrape_rce(request):
    """Scrape robot images from RobotCombatEvents"""
    url = request.query_params.get('url')
    
    if not url:
        return Response(
            {'error': 'url parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        result = scrape_rce_robots(url)
        return Response(result)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
