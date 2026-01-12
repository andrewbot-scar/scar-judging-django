"""
Discord webhook integration service
"""

import requests
from datetime import datetime


def get_robot_image(robot_images, robot_name):
    """Case-insensitive robot image lookup"""
    if not robot_images or not robot_name:
        return None
    
    # Try exact match first
    if robot_name in robot_images:
        return robot_images[robot_name]
    
    # Try case-insensitive match
    lower_name = robot_name.lower()
    for key, value in robot_images.items():
        if key.lower() == lower_name:
            return value
    
    return None


def post_match_to_discord(webhook_url, match_data):
    """
    Post match result to Discord webhook.
    
    Args:
        webhook_url: Discord webhook URL
        match_data: Dict with keys:
            - winner: Winner name
            - loser: Loser name
            - scoreA: Score for competitor A
            - scoreB: Score for competitor B
            - winMethod: 'ko' or 'points'
            - tournamentName: Name of tournament
            - matchNum: Match number
            - eventName: Event name
            - winnerImageUrl: Optional image URL for winner
            - loserImageUrl: Optional image URL for loser
    
    Returns:
        Dict with success status and optional error
    """
    if not webhook_url:
        return {'success': False, 'error': 'No webhook URL provided'}

    winner = match_data.get('winner', 'Unknown')
    loser = match_data.get('loser', 'Unknown')
    score_a = match_data.get('scoreA', 0)
    score_b = match_data.get('scoreB', 0)
    win_method = match_data.get('winMethod', 'points')
    tournament_name = match_data.get('tournamentName', 'Tournament')
    match_num = match_data.get('matchNum', '?')
    event_name = match_data.get('eventName', 'SCAR Event')
    winner_image_url = match_data.get('winnerImageUrl')

    # Determine if KO
    is_ko = win_method == 'ko' or score_a == 0 or score_b == 0
    result_text = "KNOCKOUT!" if is_ko else f"{score_a} - {score_b}"

    # Build embed
    embed = {
        'title': f"🤖 Match {match_num} Complete!",
        'description': tournament_name,
        'color': 0xFF0000 if is_ko else 0x00FF00,  # Red for KO, Green for decision
        'fields': [
            {
                'name': '🏆 Winner',
                'value': winner,
                'inline': True,
            },
            {
                'name': '💀 Defeated',
                'value': loser,
                'inline': True,
            },
            {
                'name': '📊 Result',
                'value': result_text,
                'inline': True,
            },
        ],
        'footer': {
            'text': f"{event_name} • SCAR Judge Portal",
        },
        'timestamp': datetime.utcnow().isoformat(),
    }

    # Add winner thumbnail if available
    if winner_image_url:
        embed['thumbnail'] = {'url': winner_image_url}

    try:
        response = requests.post(
            webhook_url,
            json={
                'embeds': [embed],
                'username': 'SCAR Match Reporter',
                'avatar_url': 'https://www.socalattackrobots.com/favicon.ico'
            }
        )

        if not response.ok:
            error_text = response.text
            print(f"Discord webhook failed: {response.status_code} {error_text}")
            return {'success': False, 'error': error_text}

        print(f"Discord notification sent for Match {match_num}: {winner} defeats {loser}")
        return {'success': True}

    except Exception as e:
        print(f"Discord webhook error: {e}")
        return {'success': False, 'error': str(e)}


def send_test_webhook(webhook_url, event_name):
    """Send a test message to Discord webhook"""
    return post_match_to_discord(webhook_url, {
        'winner': 'Test Bot Alpha',
        'loser': 'Test Bot Beta',
        'scoreA': 22,
        'scoreB': 11,
        'winMethod': 'points',
        'tournamentName': 'Test Tournament',
        'matchNum': 0,
        'eventName': event_name or 'Test Event',
    })
