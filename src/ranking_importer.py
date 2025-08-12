#!/usr/bin/env python3
"""
ALFRED Ranking Importer - Import Rankings with Master Index Validation
Streamlined process for importing new ranking sources
"""

import pandas as pd
import psycopg2
import os
import sys
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

# Import our validation system
sys.path.append(os.path.dirname(__file__))
from db.player_validation import PlayerValidator, PlayerValidationResult

@dataclass
class RankingImportResult:
    """Result of ranking import process"""
    source_name: str
    total_rows: int
    matched_players: int
    unmatched_players: int
    errors: List[str]
    warnings: List[str]
    success: bool

class RankingImporter:
    """Import ranking data with master index validation"""
    
    def __init__(self, db_config: Dict[str, str] = None):
        self.db_config = db_config or {
            'host': 'localhost',
            'user': os.environ.get('USER', 'jeffgreenfield'),
            'database': 'fantasy_draft_db'
        }
        self.validator = PlayerValidator(self.db_config)
    
    def examine_xlsx_file(self, file_path: str) -> Dict:
        """Examine XLSX file structure and show first few rows"""
        try:
            # Read the file to see all sheets
            excel_file = pd.ExcelFile(file_path)
            
            result = {
                'file_path': file_path,
                'sheets': [],
                'recommended_sheet': None
            }
            
            print(f"📊 Examining: {file_path}")
            print(f"📋 Found {len(excel_file.sheet_names)} sheet(s): {', '.join(excel_file.sheet_names)}")
            
            for sheet_name in excel_file.sheet_names:
                try:
                    # Read first few rows
                    df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=10)
                    
                    sheet_info = {
                        'name': sheet_name,
                        'rows': len(df),
                        'columns': list(df.columns),
                        'sample_data': df.head(3).to_dict('records') if not df.empty else []
                    }
                    
                    print(f"\n📄 Sheet: {sheet_name}")
                    print(f"   Columns ({len(df.columns)}): {', '.join(str(col) for col in df.columns)}")
                    print(f"   First 3 rows:")
                    if not df.empty:
                        for i, row in df.head(3).iterrows():
                            print(f"     Row {i+1}: {dict(row)}")
                    else:
                        print("     (Empty sheet)")
                    
                    result['sheets'].append(sheet_info)
                    
                    # Try to identify the best sheet (has player names and rankings)
                    if self._looks_like_rankings_sheet(df):
                        result['recommended_sheet'] = sheet_name
                        
                except Exception as e:
                    print(f"❌ Error reading sheet '{sheet_name}': {e}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error examining file: {e}")
            return {'error': str(e)}
    
    def _looks_like_rankings_sheet(self, df: pd.DataFrame) -> bool:
        """Check if a sheet looks like it contains player rankings"""
        if df.empty:
            return False
            
        # Look for common column patterns
        columns_str = ' '.join(str(col).lower() for col in df.columns)
        
        # Must have player names
        has_names = any(word in columns_str for word in ['name', 'player'])
        
        # Should have rankings or numbers
        has_rankings = any(word in columns_str for word in ['rank', 'position', 'tier', '#'])
        
        # Should have position info
        has_position = any(word in columns_str for word in ['pos', 'position'])
        
        return has_names and (has_rankings or has_position)
    
    def import_rankings(self, file_path: str, source_name: str, sheet_name: str = None, 
                       name_col: str = None, position_col: str = None, 
                       rank_col: str = None, team_col: str = None,
                       force_position: str = None) -> RankingImportResult:
        """Import rankings from XLSX file"""
        
        try:
            # Read the Excel file
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(file_path)
            
            print(f"📊 Importing from {file_path}")
            print(f"📋 Sheet: {sheet_name or 'default'}")
            print(f"📈 Total rows: {len(df)}")
            
            # Auto-detect columns if not specified
            if not name_col:
                name_col = self._detect_column(df, ['name', 'player'])
            if not position_col and not force_position:
                position_col = self._detect_column(df, ['pos', 'position'])
            if not rank_col:
                rank_col = self._detect_column(df, ['rank', 'ranking', '#', 'pos rank'])
            if not team_col:
                team_col = self._detect_column(df, ['team', 'tm'])
            
            print(f"🔍 Using columns:")
            print(f"   Name: {name_col}")
            if force_position:
                print(f"   Position: {force_position} (forced)")
            else:
                print(f"   Position: {position_col}")
            print(f"   Rank: {rank_col}")
            print(f"   Team: {team_col}")
            
            if not all([name_col, rank_col]) or (not position_col and not force_position):
                if force_position:
                    error_msg = f"Could not detect required columns. Found: name={name_col}, rank={rank_col}, force_position={force_position}"
                else:
                    error_msg = f"Could not detect required columns. Found: name={name_col}, position={position_col}, rank={rank_col}"
                
                return RankingImportResult(
                    source_name=source_name,
                    total_rows=len(df),
                    matched_players=0,
                    unmatched_players=0,
                    errors=[error_msg],
                    warnings=[],
                    success=False
                )
            
            # Process each row
            matched_players = []
            unmatched_players = []
            errors = []
            warnings = []
            
            for index, row in df.iterrows():
                try:
                    name = str(row[name_col]).strip()
                    if force_position:
                        position = force_position.upper()
                    else:
                        position = str(row[position_col]).strip().upper()
                    rank = row[rank_col]
                    team = str(row[team_col]).strip().upper() if team_col and pd.notna(row[team_col]) else None
                    
                    # Extract team from player name if missing (common in some formats)
                    if not team:
                        if position == 'DST':
                            team = self._extract_team_from_dst_name(name)
                        else:
                            team = self._extract_team_from_parentheses(name)
                            
                    # Clean player name (remove team from name if present)
                    clean_name = self._clean_player_name(name) if position != 'DST' else name
                    
                    # Skip empty rows
                    if not name or name.lower() == 'nan':
                        continue
                    
                    # Convert rank to integer
                    try:
                        rank = int(float(rank))
                    except (ValueError, TypeError):
                        warnings.append(f"Row {index+1}: Invalid rank '{rank}' for {name}")
                        continue
                    
                    # Smart player matching - try exact match first, then fuzzy match
                    if not team:
                        # Search for player in master index
                        all_players = self.validator.get_all_players()
                        matches = [p for p in all_players 
                                 if p['name'].lower() == clean_name.lower() and p['position'] == position]
                        
                        # If no exact match, try fuzzy matching for Jr./III/II suffixes
                        if not matches:
                            matches = self._fuzzy_name_match(clean_name, position, all_players)
                        
                        if len(matches) == 1:
                            team = matches[0]['team']
                            player_id = matches[0]['player_id']
                        elif len(matches) > 1:
                            warnings.append(f"Row {index+1}: Multiple matches for {clean_name} ({position})")
                            continue
                        else:
                            unmatched_players.append({
                                'name': clean_name,
                                'position': position,
                                'rank': rank,
                                'row': index+1
                            })
                            continue
                    else:
                        # Try exact validation first
                        validation = self.validator.validate_player(clean_name, position, team)
                        if validation.is_valid:
                            player_id = validation.player_id
                        else:
                            # Try fuzzy matching with known team
                            fuzzy_match = self._fuzzy_name_match_with_team(clean_name, position, team)
                            if fuzzy_match:
                                player_id = fuzzy_match['player_id']
                                # Update name to matched name for consistency
                                clean_name = fuzzy_match['name']
                                print(f"🎯 Fuzzy matched: {row[name_col]} -> {clean_name}")
                            else:
                                unmatched_players.append({
                                    'name': clean_name,
                                    'position': position,
                                    'team': team,
                                    'rank': rank,
                                    'row': index+1,
                                    'error': validation.error_message,
                                    'suggestions': validation.suggestions
                                })
                                continue
                    
                    matched_players.append({
                        'player_id': player_id,
                        'name': clean_name,
                        'position': position,
                        'team': team,
                        'rank': rank
                    })
                    
                except Exception as e:
                    errors.append(f"Row {index+1}: {str(e)}")
                    continue
            
            print(f"✅ Matched: {len(matched_players)} players")
            print(f"❌ Unmatched: {len(unmatched_players)} players")
            print(f"⚠️  Warnings: {len(warnings)}")
            print(f"🚨 Errors: {len(errors)}")
            
            # Show some unmatched players for debugging
            if unmatched_players:
                print(f"\n🔍 First 5 unmatched players:")
                for player in unmatched_players[:5]:
                    print(f"   Row {player['row']}: {player['name']} ({player['position']}, {player.get('team', 'NO TEAM')}) - {player.get('error', 'Not found')}")
                    if player.get('suggestions'):
                        print(f"      Suggestions: {', '.join(player['suggestions'][:3])}")
            
            # If we have matches, offer to import them
            if matched_players:
                success = self._import_to_database(source_name, matched_players)
            else:
                success = False
            
            return RankingImportResult(
                source_name=source_name,
                total_rows=len(df),
                matched_players=len(matched_players),
                unmatched_players=len(unmatched_players),
                errors=errors,
                warnings=warnings,
                success=success
            )
            
        except Exception as e:
            return RankingImportResult(
                source_name=source_name,
                total_rows=0,
                matched_players=0,
                unmatched_players=0,
                errors=[f"Failed to process file: {str(e)}"],
                warnings=[],
                success=False
            )
    
    def _detect_column(self, df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        """Auto-detect column name from list of possibilities"""
        columns_lower = [str(col).lower() for col in df.columns]
        
        for col_name in possible_names:
            for i, col_lower in enumerate(columns_lower):
                if col_name in col_lower:
                    return df.columns[i]
        return None
    
    def _fuzzy_name_match(self, name: str, position: str, all_players: List[Dict]) -> List[Dict]:
        """Find players with fuzzy name matching (handles Jr./III/II suffixes)"""
        matches = []
        name_clean = name.lower().strip()
        
        # Common suffix variations
        suffixes = [' jr.', ' jr', ' ii', ' iii', ' iv', ' sr.', ' sr']
        
        for player in all_players:
            if player['position'] != position:
                continue
                
            player_name = player['name'].lower().strip()
            
            # Try adding suffixes to the input name
            for suffix in suffixes:
                if (name_clean + suffix) == player_name:
                    matches.append(player)
                    break
            
            # Try removing suffixes from the player name
            for suffix in suffixes:
                if player_name.endswith(suffix):
                    base_name = player_name[:-len(suffix)].strip()
                    if base_name == name_clean:
                        matches.append(player)
                        break
        
        return matches
    
    def _fuzzy_name_match_with_team(self, name: str, position: str, team: str) -> Optional[Dict]:
        """Find single player match with fuzzy name matching for specific team"""
        all_players = self.validator.get_all_players()
        team_players = [p for p in all_players if p['team'] == team and p['position'] == position]
        
        # Special handling for D/ST - try team-based matching
        if position == 'DST':
            dst_match = self._match_dst_player(name, team, team_players)
            if dst_match:
                return dst_match
        
        matches = self._fuzzy_name_match(name, position, team_players)
        return matches[0] if len(matches) == 1 else None
    
    def _match_dst_player(self, name: str, team: str, team_players: List[Dict]) -> Optional[Dict]:
        """Special matching for D/ST players"""
        name_lower = name.lower()
        
        # Common D/ST name patterns
        dst_patterns = ['defense', 'dst', 'def', team.lower()]
        
        for player in team_players:
            player_name_lower = player['name'].lower()
            
            # If the name contains the team abbreviation and common D/ST words
            if any(pattern in name_lower for pattern in dst_patterns):
                if team.lower() in player_name_lower or 'dst' in player_name_lower:
                    return player
        
        return None
    
    def _extract_team_from_dst_name(self, name: str) -> Optional[str]:
        """Extract team abbreviation from D/ST player name"""
        # Mapping of team names to abbreviations
        team_mapping = {
            'arizona cardinals': 'ARI', 'atlanta falcons': 'ATL', 'baltimore ravens': 'BAL',
            'buffalo bills': 'BUF', 'carolina panthers': 'CAR', 'chicago bears': 'CHI',
            'cincinnati bengals': 'CIN', 'cleveland browns': 'CLE', 'dallas cowboys': 'DAL',
            'denver broncos': 'DEN', 'detroit lions': 'DET', 'green bay packers': 'GB',
            'houston texans': 'HOU', 'indianapolis colts': 'IND', 'jacksonville jaguars': 'JAX',
            'kansas city chiefs': 'KC', 'los angeles chargers': 'LAC', 'los angeles rams': 'LAR',
            'las vegas raiders': 'LV', 'miami dolphins': 'MIA', 'minnesota vikings': 'MIN',
            'new england patriots': 'NE', 'new orleans saints': 'NO', 'new york giants': 'NYG',
            'new york jets': 'NYJ', 'philadelphia eagles': 'PHI', 'pittsburgh steelers': 'PIT',
            'seattle seahawks': 'SEA', 'san francisco 49ers': 'SF', 'tampa bay buccaneers': 'TB',
            'tennessee titans': 'TEN', 'washington commanders': 'WAS'
        }
        
        name_lower = name.lower()
        
        # Remove common D/ST suffixes to get team name
        for suffix in [' dst', ' defense', ' def', ' d/st']:
            if name_lower.endswith(suffix):
                name_lower = name_lower[:-len(suffix)].strip()
                break
        
        # Look for exact team name match
        if name_lower in team_mapping:
            return team_mapping[name_lower]
        
        # Look for partial matches (in case of slight variations)
        for team_name, abbrev in team_mapping.items():
            if team_name in name_lower or name_lower in team_name:
                return abbrev
        
        return None
    
    def _extract_team_from_parentheses(self, name: str) -> Optional[str]:
        """Extract team abbreviation from player name like 'Josh Allen (BUF)'"""
        import re
        match = re.search(r'\(([A-Z]{2,3})\)', name)
        if match:
            team_abbrev = match.group(1).upper()
            # Validate it's a real team abbreviation
            valid_teams = {
                'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
                'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
                'LAC', 'LAR', 'LV', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
                'NYJ', 'PHI', 'PIT', 'SEA', 'SF', 'TB', 'TEN', 'WAS'
            }
            if team_abbrev in valid_teams:
                return team_abbrev
        return None
    
    def _clean_player_name(self, name: str) -> str:
        """Remove team abbreviation from player name like 'Josh Allen (BUF)' -> 'Josh Allen'"""
        import re
        return re.sub(r'\s*\([A-Z]{2,3}\)\s*', '', name).strip()
    
    def _import_to_database(self, source_name: str, players: List[Dict]) -> bool:
        """Import matched players to database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # Check if ranking source exists, create if not
            cur.execute("SELECT source_id FROM ranking_sources WHERE source_name = %s", (source_name,))
            result = cur.fetchone()
            
            if result:
                source_id = result[0]
                print(f"📋 Using existing ranking source: {source_name} (ID: {source_id})")
            else:
                cur.execute("""
                    INSERT INTO ranking_sources (source_name, base_url, has_position_ranks, is_active) 
                    VALUES (%s, %s, TRUE, TRUE) 
                    RETURNING source_id
                """, (source_name, f"https://{source_name.lower()}.com"))
                source_id = cur.fetchone()[0]
                print(f"📋 Created new ranking source: {source_name} (ID: {source_id})")
            
            # Clear existing rankings for this source
            cur.execute("DELETE FROM player_rankings WHERE source_id = %s", (source_id,))
            deleted_count = cur.rowcount
            if deleted_count > 0:
                print(f"🗑️  Cleared {deleted_count} existing rankings for {source_name}")
            
            # Insert new rankings
            for player in players:
                cur.execute("""
                    INSERT INTO player_rankings (player_id, source_id, position_rank, overall_rank)
                    VALUES (%s, %s, %s, %s)
                """, (player['player_id'], source_id, player['rank'], player['rank']))
            
            conn.commit()
            print(f"💾 Imported {len(players)} rankings for {source_name}")
            
            cur.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Database import failed: {e}")
            return False

def main():
    """Main function for testing"""
    importer = RankingImporter()
    
    # Examine the Rotowire file
    rotowire_path = "/Users/jeffgreenfield/dev/ff_draft_vibe/data/rankings/rotowire rankings.xlsx"
    
    print("🏈 ALFRED Ranking Importer")
    print("=" * 50)
    
    if not os.path.exists(rotowire_path):
        print(f"❌ File not found: {rotowire_path}")
        return
    
    # Examine file structure
    file_info = importer.examine_xlsx_file(rotowire_path)
    
    if 'error' in file_info:
        print(f"❌ Error: {file_info['error']}")
        return
    
    # If we found a recommended sheet, try to import it
    if file_info.get('recommended_sheet'):
        print(f"\n🎯 Importing from recommended sheet: {file_info['recommended_sheet']}")
        result = importer.import_rankings(
            rotowire_path, 
            "Rotowire", 
            sheet_name=file_info['recommended_sheet']
        )
        
        print(f"\n📊 Import Result:")
        print(f"   Source: {result.source_name}")
        print(f"   Total rows: {result.total_rows}")
        print(f"   Matched: {result.matched_players}")
        print(f"   Unmatched: {result.unmatched_players}")
        print(f"   Success: {result.success}")
        
        if result.errors:
            print(f"   Errors: {len(result.errors)}")
        if result.warnings:
            print(f"   Warnings: {len(result.warnings)}")

if __name__ == "__main__":
    main()