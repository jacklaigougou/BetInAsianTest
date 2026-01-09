from typing import Dict, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.match_helper import match_key_in_mapping


class SportsbetTournamentID:
    """
    Sportsbet Tournament ID mapping singleton
    Cache {sport: {league+tournament: tournament_id}} mapping
    """
    _instance: Optional['SportsbetTournamentID'] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not SportsbetTournamentID._initialized:
            # {sport: {league+tournament: tournament_id}}
            self._tournament_cache: Dict[str, Dict[str, str]] = {}
            SportsbetTournamentID._initialized = True

    def get_tournament_id(self, sport: str, spider_league_standard: str) -> Optional[str]:
        """
        Get tournament_id (support direct match and contains match)

        Args:
            sport: Sport type (e.g. 'basketball', 'soccer')
            spider_league_standard: Standardized league name

        Returns:
            Matched tournament_id or None
        """
        if sport not in self._tournament_cache:
            return None

        league_mapping = self._tournament_cache[sport]

        # Use helper function for matching
        tournament_id = match_key_in_mapping(spider_league_standard, league_mapping, "tournament")
        if tournament_id:
            print(f"[Cache] ", end="")

        return tournament_id

    def update_tournament_mapping(self, sport: str, league_mapping: Dict[str, str]):
        """
        Update tournament mapping

        Args:
            sport: Sport type
            league_mapping: {league+tournament: tournament_id} mapping dict
        """
        self._tournament_cache[sport] = league_mapping
        print(f"📦 [Cache] Updated {sport} mapping ({len(league_mapping)} items)")

    def has_sport(self, sport: str) -> bool:
        """Check if sport is cached"""
        return sport in self._tournament_cache

    def clear_cache(self):
        """Clear cache"""
        self._tournament_cache.clear()
        print(f"🗑️ [Cache] Cleared all mappings")


# Global singleton instance
sportsbet_tournament_id = SportsbetTournamentID()
