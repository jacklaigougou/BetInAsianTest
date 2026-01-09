from typing import Dict, List, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.match_event_helper import match_event_by_teams


class SportsbetEvents:
    """
    Sportsbet Events cache singleton
    Cache {sport: {tournament_id: {home+away: event_id}}} mapping
    """
    _instance: Optional['SportsbetEvents'] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not SportsbetEvents._initialized:
            # {sport: {tournament_id: {home+away: event_id}}}
            self._events_cache: Dict[str, Dict[str, Dict[str, str]]] = {}
            SportsbetEvents._initialized = True

    def get_events(self, sport: str, tournament_id: str) -> Optional[Dict[str, str]]:
        """
        Get event mapping for a tournament

        Args:
            sport: Sport type (e.g. 'basketball', 'soccer')
            tournament_id: Tournament ID

        Returns:
            Dict of {home+away: event_id} or None if not cached
        """
        if sport not in self._events_cache:
            return None

        events = self._events_cache[sport].get(tournament_id)
        if events is not None:
            print(f"✅ [缓存] 找到 {len(events)} 个赛事映射")
        return events

    def update_events(self, sport: str, tournament_id: str, event_mapping: Dict[str, str]):
        """
        Update events cache

        Args:
            sport: Sport type (e.g. 'basketball', 'soccer')
            tournament_id: Tournament ID
            event_mapping: Dict of {home+away: event_id}
        """
        if sport not in self._events_cache:
            self._events_cache[sport] = {}

        self._events_cache[sport][tournament_id] = event_mapping
        print(f"📦 [缓存] 已更新 {sport} tournament {tournament_id[:20]}... 的赛事 ({len(event_mapping)} 个)")

    def get_event_id(self, sport: str, tournament_id: str, spider_home_standard: str, spider_away_standard: str) -> Optional[str]:
        """
        Get event_id (only contains match by home and away teams)

        Args:
            sport: Sport type (e.g. 'basketball', 'soccer')
            tournament_id: Tournament ID
            spider_home_standard: Standardized home team name
            spider_away_standard: Standardized away team name

        Returns:
            Matched event_id or None
        """
        if sport not in self._events_cache:
            return None

        if tournament_id not in self._events_cache[sport]:
            return None

        event_mapping = self._events_cache[sport][tournament_id]

        # Use helper function for matching (only contains match)
        event_id = match_event_by_teams(spider_home_standard, spider_away_standard, event_mapping)
        if event_id:
            print(f"[缓存] ", end="")

        return event_id

    def has_tournament(self, sport: str, tournament_id: str) -> bool:
        """Check if tournament events are cached"""
        if sport not in self._events_cache:
            return False
        return tournament_id in self._events_cache[sport]

    def clear_cache(self):
        """Clear all cached events"""
        self._events_cache.clear()
        print(f"🗑️ [缓存] 已清空所有赛事数据")


# Global singleton instance
sportsbet_events = SportsbetEvents()
