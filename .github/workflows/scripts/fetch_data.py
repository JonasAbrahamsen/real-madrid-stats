#!/usr/bin/env python3
"""
Real Madrid Stats - Data Fetcher for GitHub Actions
Henter data fra API-Football og lagrer til JSON
"""

import os
import requests
import json
import time
from datetime import datetime
from typing import Dict, List

class RealMadridDataFetcher:
    """Henter Real Madrid data fra API-Football"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "v3.football.api-sports.io"
        }
        
        # Real Madrid & La Liga IDs (hardkodet for effektivitet)
        self.team_id = 541  # Real Madrid
        self.league_id = 140  # La Liga
        self.season = "2024"  # Oppdateres automatisk i find_current_season()
        
        self.data = {
            "team_info": {},
            "players": [],
            "fixtures": [],
            "standings": [],
            "statistics": {},
            "h2h": {},
            "predictions": {},
            "last_updated": None
        }
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """API request med error handling"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            print(f"📡 API: {endpoint}")
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'errors' in result and result['errors']:
                print(f"⚠️  Error: {result['errors']}")
                return None
            
            time.sleep(0.5)  # Rate limiting
            return result
            
        except Exception as e:
            print(f"❌ Request error: {e}")
            return None
    
    def find_current_season(self) -> bool:
        """Finn current/aktiv sesong for La Liga"""
        print("\n📅 Finner current season...")
        
        result = self._make_request("leagues", {
            "id": self.league_id,
            "current": "true"
        })
        
        if result and result.get('response'):
            for league in result['response']:
                if league.get('seasons'):
                    # Finn current season
                    for season in league['seasons']:
                        if season.get('current'):
                            self.season = str(season['year'])
                            print(f"✅ Current season: {self.season}/{int(self.season)+1}")
                            return True
            
            # Fallback: bruk siste sesong
            if league.get('seasons'):
                self.season = str(league['seasons'][-1]['year'])
                print(f"✅ Latest season: {self.season}/{int(self.season)+1}")
                return True
        
        print(f"⚠️  Bruker default: {self.season}")
        return False
    
    def fetch_team_info(self) -> bool:
        """Hent team info"""
        print("\n🏆 Henter team info...")
        
        result = self._make_request("teams", {"id": self.team_id})
        
        if result and result.get('response'):
            team_data = result['response'][0]
            self.data['team_info'] = {
                'team': team_data['team'],
                'venue': team_data.get('venue', {})
            }
            print(f"✅ Team: {team_data['team']['name']}")
            return True
        
        return False
    
    def fetch_standings(self) -> bool:
        """Hent La Liga tabell"""
        print("\n📊 Henter tabell...")
        
        result = self._make_request("standings", {
            "league": self.league_id,
            "season": self.season
        })
        
        if result and result.get('response'):
            standings = result['response'][0]['league']['standings'][0]
            self.data['standings'] = standings
            
            # Finn Real Madrid posisjon
            for team in standings:
                if team['team']['id'] == self.team_id:
                    print(f"✅ Tabell hentet! RM posisjon: {team['rank']}")
                    break
            
            return True
        
        return False
    
    def fetch_fixtures(self) -> bool:
        """Hent kamper"""
        print("\n⚽ Henter kamper...")
        
        result = self._make_request("fixtures", {
            "team": self.team_id,
            "league": self.league_id,
            "season": self.season
        })
        
        if result and result.get('response'):
            self.data['fixtures'] = result['response']
            
            finished = sum(1 for f in result['response'] if f['fixture']['status']['short'] == 'FT')
            upcoming = sum(1 for f in result['response'] if f['fixture']['status']['short'] == 'NS')
            
            print(f"✅ Kamper: {len(result['response'])} (Spilt: {finished}, Kommende: {upcoming})")
            return True
        
        return False
    
    def fetch_players(self) -> bool:
        """Hent spillere"""
        print("\n👥 Henter spillere...")
        
        result = self._make_request("players", {
            "team": self.team_id,
            "league": self.league_id,
            "season": self.season,
            "page": 1
        })
        
        if result and result.get('response'):
            self.data['players'] = result['response']
            print(f"✅ Spillere: {len(result['response'])}")
            return True
        
        return False
    
    def fetch_team_statistics(self) -> bool:
        """Hent lagstatistikk"""
        print("\n📈 Henter lagstatistikk...")
        
        result = self._make_request("teams/statistics", {
            "team": self.team_id,
            "league": self.league_id,
            "season": self.season
        })
        
        if result and result.get('response'):
            self.data['statistics'] = result['response']
            print(f"✅ Statistikk hentet!")
            return True
        
        return False
    
    def fetch_h2h(self, opponent_id: int, opponent_name: str) -> bool:
        """Hent H2H"""
        print(f"\n🆚 H2H: {opponent_name}...")
        
        result = self._make_request("fixtures/headtohead", {
            "h2h": f"{self.team_id}-{opponent_id}",
            "last": 10
        })
        
        if result and result.get('response'):
            self.data['h2h'][opponent_name] = result['response']
            print(f"✅ H2H: {len(result['response'])} kamper")
            return True
        
        return False
    
    def fetch_predictions(self) -> bool:
        """Hent predictions for neste kamp"""
        print("\n🔮 Henter predictions...")
        
        if not self.data.get('fixtures'):
            return False
        
        upcoming = [f for f in self.data['fixtures'] if f['fixture']['status']['short'] == 'NS']
        
        if not upcoming:
            print("⚠️  Ingen kommende kamper")
            return False
        
        upcoming.sort(key=lambda x: x['fixture']['date'])
        fixture_id = upcoming[0]['fixture']['id']
        
        result = self._make_request("predictions", {"fixture": fixture_id})
        
        if result and result.get
