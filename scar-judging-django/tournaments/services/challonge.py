"""
Challonge API integration service
"""

import requests
from django.conf import settings


class ChallongeService:
    """Service for interacting with Challonge API"""
    
    BASE_URL = 'https://api.challonge.com/v1'

    def __init__(self):
        self.api_key = settings.CHALLONGE_API_KEY
        if not self.api_key:
            raise ValueError("CHALLONGE_API_KEY not configured")

    def _request(self, endpoint, method='GET', data=None):
        """Make a request to Challonge API"""
        url = f"{self.BASE_URL}{endpoint}"
        params = {'api_key': self.api_key}
        
        if method == 'GET':
            response = requests.get(url, params=params)
        elif method == 'POST':
            response = requests.post(url, params=params, json=data)
        elif method == 'PUT':
            response = requests.put(url, params=params, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, params=params)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()

    def get_tournament(self, tournament_id, include_participants=True, include_matches=True):
        """Get tournament details with participants and matches"""
        params = []
        if include_participants:
            params.append('include_participants=1')
        if include_matches:
            params.append('include_matches=1')
        
        query = '&'.join(params)
        endpoint = f"/tournaments/{tournament_id}.json"
        if query:
            endpoint += f"?{query}"
        
        return self._request(endpoint)

    def get_participants(self, tournament_id):
        """Get tournament participants"""
        return self._request(f"/tournaments/{tournament_id}/participants.json")

    def get_matches(self, tournament_id):
        """Get tournament matches"""
        return self._request(f"/tournaments/{tournament_id}/matches.json")

    def get_match(self, tournament_id, match_id):
        """Get a single match"""
        return self._request(f"/tournaments/{tournament_id}/matches/{match_id}.json")

    def update_match(self, tournament_id, match_id, winner_id, scores_csv):
        """Update match with winner and scores"""
        data = {
            'match': {
                'winner_id': winner_id,
                'scores_csv': scores_csv,
            }
        }
        return self._request(
            f"/tournaments/{tournament_id}/matches/{match_id}.json",
            method='PUT',
            data=data
        )

    def reopen_match(self, tournament_id, match_id):
        """Reopen a completed match"""
        return self._request(
            f"/tournaments/{tournament_id}/matches/{match_id}/reopen.json",
            method='POST'
        )

    def get_match_attachments(self, tournament_id, match_id):
        """Get attachments for a match"""
        return self._request(
            f"/tournaments/{tournament_id}/matches/{match_id}/attachments.json"
        )

    def create_match_attachment(self, tournament_id, match_id, description):
        """Create a match attachment (used to store judge breakdown)"""
        data = {
            'match_attachment': {
                'description': description,
            }
        }
        return self._request(
            f"/tournaments/{tournament_id}/matches/{match_id}/attachments.json",
            method='POST',
            data=data
        )

    def get_competitor_names(self, tournament_id, competitor_a_id, competitor_b_id):
        """Get competitor names from participant IDs"""
        try:
            data = self.get_tournament(tournament_id, include_participants=True, include_matches=False)
            participants = data.get('tournament', {}).get('participants', [])
            
            participant_map = {}
            for p in participants:
                participant = p.get('participant', {})
                participant_map[participant.get('id')] = participant.get('name')
            
            return {
                'competitorA': participant_map.get(competitor_a_id),
                'competitorB': participant_map.get(competitor_b_id),
            }
        except Exception as e:
            print(f"Error getting competitor names: {e}")
            return {'competitorA': None, 'competitorB': None}

    def get_tournament_name(self, tournament_id):
        """Get tournament name"""
        try:
            data = self.get_tournament(tournament_id, include_participants=False, include_matches=False)
            return data.get('tournament', {}).get('name', tournament_id)
        except Exception:
            return tournament_id

    def get_match_number(self, tournament_id, match_id):
        """Get match number (suggested play order)"""
        try:
            data = self.get_match(tournament_id, match_id)
            match = data.get('match', {})
            return match.get('suggested_play_order') or match.get('id')
        except Exception:
            return match_id


# Singleton instance
_challonge_service = None


def get_challonge_service():
    """Get or create Challonge service instance"""
    global _challonge_service
    if _challonge_service is None:
        _challonge_service = ChallongeService()
    return _challonge_service
