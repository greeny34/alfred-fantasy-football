#!/usr/bin/env python3
"""
ALFRED Player Validation - Master Index Data Integrity
Ensures all external data validates against our clean master player index
"""

import psycopg2
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

@dataclass
class PlayerValidationResult:
    """Result of player validation"""
    is_valid: bool
    player_id: Optional[int] = None
    error_message: Optional[str] = None
    suggestions: List[str] = None

class PlayerValidator:
    """Validates all external player data against master index"""
    
    def __init__(self, db_config: Dict[str, Any] = None):
        self.db_config = db_config or {
            'host': 'localhost',
            'user': os.environ.get('USER', 'jeffgreenfield'),
            'database': 'fantasy_draft_db'
        }
        
        # Valid positions and teams (from master index)
        self._valid_positions = {'QB', 'RB', 'WR', 'TE', 'K', 'DST'}
        self._valid_teams = {
            'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
            'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
            'LAC', 'LAR', 'LV', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
            'NYJ', 'PHI', 'PIT', 'SEA', 'SF', 'TB', 'TEN', 'WAS'
        }
    
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)
    
    def validate_player(self, name: str, position: str, team: str) -> PlayerValidationResult:
        """
        Validate a player against the master index
        Returns validation result with player_id if found
        """
        # Clean inputs
        name = name.strip()
        position = position.upper().strip()
        team = team.upper().strip()
        
        # Basic format validation
        if not name:
            return PlayerValidationResult(False, error_message="Player name cannot be empty")
        
        if position not in self._valid_positions:
            return PlayerValidationResult(
                False, 
                error_message=f"Invalid position '{position}'. Valid positions: {', '.join(sorted(self._valid_positions))}"
            )
        
        if team not in self._valid_teams:
            return PlayerValidationResult(
                False,
                error_message=f"Invalid team '{team}'. Valid teams: {', '.join(sorted(self._valid_teams))}"
            )
        
        # Database validation - exact match
        conn = self.get_db_connection()
        try:
            cur = conn.cursor()
            
            # Try exact match first
            cur.execute("""
                SELECT player_id, name, position, team 
                FROM players 
                WHERE LOWER(name) = LOWER(%s) 
                AND position = %s 
                AND team = %s 
                AND is_active = TRUE
            """, (name, position, team))
            
            result = cur.fetchone()
            
            if result:
                return PlayerValidationResult(
                    True,
                    player_id=result[0]
                )
            
            # If no exact match, find suggestions
            suggestions = self._find_suggestions(cur, name, position, team)
            
            return PlayerValidationResult(
                False,
                error_message=f"Player not found in master index: '{name}' ({position}, {team})",
                suggestions=suggestions
            )
            
        finally:
            conn.close()
    
    def _find_suggestions(self, cursor, name: str, position: str, team: str) -> List[str]:
        """Find similar players to suggest corrections"""
        suggestions = []
        
        # Try same position and team, similar name
        cursor.execute("""
            SELECT name, position, team 
            FROM players 
            WHERE position = %s AND team = %s 
            AND LOWER(name) LIKE %s
            AND is_active = TRUE
            LIMIT 3
        """, (position, team, f'%{name.lower()}%'))
        
        for row in cursor.fetchall():
            suggestions.append(f"{row[0]} ({row[1]}, {row[2]})")
        
        # If no suggestions yet, try same name different team/position
        if not suggestions:
            cursor.execute("""
                SELECT name, position, team 
                FROM players 
                WHERE LOWER(name) LIKE %s
                AND is_active = TRUE
                LIMIT 3
            """, (f'%{name.lower()}%',))
            
            for row in cursor.fetchall():
                suggestions.append(f"{row[0]} ({row[1]}, {row[2]})")
        
        return suggestions
    
    def validate_batch(self, players: List[Dict[str, str]]) -> List[PlayerValidationResult]:
        """Validate multiple players at once"""
        results = []
        for player in players:
            result = self.validate_player(
                player.get('name', ''),
                player.get('position', ''),
                player.get('team', '')
            )
            results.append(result)
        return results
    
    def get_all_players(self) -> List[Dict[str, Any]]:
        """Get complete master index for reference"""
        conn = self.get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT player_id, name, position, team
                FROM players
                WHERE is_active = TRUE
                ORDER BY position, team, name
            """)
            
            players = []
            for row in cur.fetchall():
                players.append({
                    'player_id': row[0],
                    'name': row[1],
                    'position': row[2],
                    'team': row[3]
                })
            
            return players
        finally:
            conn.close()
    
    def get_player_by_id(self, player_id: int) -> Optional[Dict[str, Any]]:
        """Get player by internal ID"""
        conn = self.get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT player_id, name, position, team
                FROM players
                WHERE player_id = %s AND is_active = TRUE
            """, (player_id,))
            
            result = cur.fetchone()
            if result:
                return {
                    'player_id': result[0],
                    'name': result[1],
                    'position': result[2],
                    'team': result[3]
                }
            return None
        finally:
            conn.close()

# Utility functions for easy import
def validate_player(name: str, position: str, team: str) -> PlayerValidationResult:
    """Quick validation function"""
    validator = PlayerValidator()
    return validator.validate_player(name, position, team)

def get_player_id(name: str, position: str, team: str) -> Optional[int]:
    """Get player ID if valid, None otherwise"""
    result = validate_player(name, position, team)
    return result.player_id if result.is_valid else None

# Test function
if __name__ == "__main__":
    validator = PlayerValidator()
    
    # Test some players
    test_players = [
        ("Josh Allen", "QB", "BUF"),  # Should be valid
        ("Ja'Marr Chase", "WR", "CIN"),  # Should be valid
        ("Fake Player", "RB", "NYJ"),  # Should be invalid
        ("Josh Allen", "QB", "FAKE"),  # Invalid team
    ]
    
    print("🏈 ALFRED Player Validation Test")
    print("=" * 50)
    
    for name, position, team in test_players:
        result = validator.validate_player(name, position, team)
        
        if result.is_valid:
            print(f"✅ {name} ({position}, {team}) -> ID: {result.player_id}")
        else:
            print(f"❌ {name} ({position}, {team}) -> {result.error_message}")
            if result.suggestions:
                print(f"   💡 Suggestions: {', '.join(result.suggestions)}")
    
    # Show total players
    all_players = validator.get_all_players()
    print(f"\n📊 Master Index: {len(all_players)} total players")
    
    # Show by position
    by_position = {}
    for player in all_players:
        pos = player['position']
        by_position[pos] = by_position.get(pos, 0) + 1
    
    for pos, count in sorted(by_position.items()):
        print(f"   {pos}: {count} players")