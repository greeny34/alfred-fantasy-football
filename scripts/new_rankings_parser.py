#!/usr/bin/env python3
"""
New Rankings Parser
Handles FantasyPros and Underdog rankings integration
"""

import pandas as pd
import psycopg2
from datetime import datetime
import os
import re
from typing import List, Dict, Tuple
import csv

class NewRankingsParser:
    def __init__(self):
        self.fantasypros_file = 'fantasypros rank.xlsx'
        self.underdog_file = 'underdog rankings.csv'

    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host='localhost',
            port='5432',
            user=os.environ.get('USER', 'jeffgreenfield'),
            password='',
            database='fantasy_draft_db'
        )
    
    def parse_fantasypros_rankings(self) -> List[Dict]:
        """Parse FantasyPros rankings - straightforward position ranks"""
        print("📊 Parsing FantasyPros rankings...")
        
        try:
            df = pd.read_excel(self.fantasypros_file)
            print(f"✅ Loaded {len(df)} FantasyPros rankings")
            
            rankings = []
            for idx, row in df.iterrows():
                # Parse player name and team from "Player Name (TEAM)" format
                player_text = str(row['Player'])
                
                # Extract name and team using regex
                pattern = r'^([^(]+)\s*\(([A-Z]{2,4})\)$'
                match = re.match(pattern, player_text.strip())
                
                if match:
                    name = match.group(1).strip()
                    team = match.group(2).strip()
                    
                    rankings.append({
                        'name': name,
                        'position': row['Position'],
                        'team': team,
                        'position_rank': int(row['Rank']),
                        'source': 'FantasyPros'
                    })
                else:
                    print(f"⚠️  Could not parse FantasyPros player: {player_text}")
            
            print(f"✅ Parsed {len(rankings)} FantasyPros rankings")
            return rankings
            
        except Exception as e:
            print(f"❌ Error parsing FantasyPros file: {e}")
            return []
    
    def parse_underdog_rankings(self) -> List[Dict]:
        """Parse Underdog rankings with positionRank parsing and ADP/projected points"""
        print("📊 Parsing Underdog rankings...")
        
        try:
            df = pd.read_csv(self.underdog_file)
            print(f"✅ Loaded {len(df)} Underdog rankings")
            
            rankings = []
            for idx, row in df.iterrows():
                # Skip rows with missing position rank
                if pd.isna(row['positionRank']):
                    continue
                    
                # Parse position rank from format like "WR1", "RB5", "QB12", etc.
                position_rank_text = str(row['positionRank']).strip()
                
                # Extract position and rank number
                pattern = r'^([A-Z]+)(\d+)$'
                match = re.match(pattern, position_rank_text)
                
                if match:
                    position = match.group(1)
                    rank_num = int(match.group(2))
                    
                    # Combine first and last name
                    name = f"{row['firstName']} {row['lastName']}"
                    
                    ranking_data = {
                        'name': name.strip(),
                        'position': position,
                        'team': row['teamName'],
                        'position_rank': rank_num,
                        'source': 'Underdog',
                        'adp': float(row['adp']) if pd.notna(row['adp']) else None,
                        'projected_points': float(row['projectedPoints']) if pd.notna(row['projectedPoints']) else None
                    }
                    
                    rankings.append(ranking_data)
                else:
                    print(f"⚠️  Could not parse Underdog position rank: {position_rank_text}")
            
            print(f"✅ Parsed {len(rankings)} Underdog rankings")
            return rankings
            
        except Exception as e:
            print(f"❌ Error parsing Underdog file: {e}")
            return []
    
    def normalize_team_name(self, team_name: str) -> str:
        """Normalize team names to match database format"""
        team_mappings = {
            'Cincinnati Bengals': 'CIN',
            'Atlanta Falcons': 'ATL',
            'Minnesota Vikings': 'MIN',
            'Philadelphia Eagles': 'PHI',
            'Dallas Cowboys': 'DAL',
            'Detroit Lions': 'DET',
            'San Francisco 49ers': 'SF',
            'Los Angeles Rams': 'LAR',
            'New York Giants': 'NYG',
            'Buffalo Bills': 'BUF',
            'Baltimore Ravens': 'BAL',
            'Washington Commanders': 'WAS',
            'Houston Texans': 'HOU',
            'Miami Dolphins': 'MIA',
            'New York Jets': 'NYJ',
            'Indianapolis Colts': 'IND',
            'Jacksonville Jaguars': 'JAC',
            'Tennessee Titans': 'TEN',
            'Cleveland Browns': 'CLE',
            'Pittsburgh Steelers': 'PIT',
            'Kansas City Chiefs': 'KC',
            'Los Angeles Chargers': 'LAC',
            'Las Vegas Raiders': 'LV',
            'Denver Broncos': 'DEN',
            'Green Bay Packers': 'GB',
            'Chicago Bears': 'CHI',
            'Tampa Bay Buccaneers': 'TB',
            'New Orleans Saints': 'NO',
            'Carolina Panthers': 'CAR',
            'Arizona Cardinals': 'ARI',
            'Seattle Seahawks': 'SEA',
            'New England Patriots': 'NE'
        }
        
        # Handle NaN or None values
        if pd.isna(team_name) or team_name is None:
            return ''
            
        team_str = str(team_name).strip()
        
        # If it's already an abbreviation, return as is
        if len(team_str) <= 4:
            return team_str.upper()
        
        return team_mappings.get(team_str, team_str)
    
    def match_with_database(self, rankings: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Match rankings with database players"""
        print(f"🔗 Matching {len(rankings)} rankings with database...")
        
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        # Get all players from database
        cur.execute("""
            SELECT player_id, name, position, team 
            FROM players 
            ORDER BY position, name
        """)
        db_players = cur.fetchall()
        
        matched_rankings = []
        unmatched_rankings = []
        
        for ranking in rankings:
            name = ranking['name'].lower().strip()
            position = ranking['position']
            team = self.normalize_team_name(ranking['team'])
            
            # Try to find match in database
            best_match = None
            best_score = 0
            
            for db_player in db_players:
                db_id, db_name, db_position, db_team = db_player
                
                # Must match position
                if db_position != position:
                    continue
                
                # Calculate name match score
                db_name_clean = db_name.lower().strip()
                
                # Exact match
                if name == db_name_clean:
                    best_match = db_player
                    best_score = 100
                    break
                
                # Name parts matching
                name_parts = name.split()
                db_parts = db_name_clean.split()
                
                if len(name_parts) >= 2 and len(db_parts) >= 2:
                    # First and last name match
                    if name_parts[0] == db_parts[0] and name_parts[-1] == db_parts[-1]:
                        score = 95
                        # Bonus for team match
                        if team and db_team == team:
                            score += 5
                        if score > best_score:
                            best_match = db_player
                            best_score = score
                    
                    # Last name match
                    elif name_parts[-1] == db_parts[-1]:
                        score = 85
                        # Bonus for team match
                        if team and db_team == team:
                            score += 10
                        if score > best_score:
                            best_match = db_player
                            best_score = score
            
            if best_match and best_score >= 85:
                # Create matched ranking
                matched_data = {
                    'db_player_id': best_match[0],
                    'db_name': best_match[1],
                    'db_position': best_match[2],
                    'db_team': best_match[3],
                    'source_name': ranking['source'],
                    'position_rank': ranking['position_rank'],
                    'match_score': best_score,
                    'original_name': ranking['name'],
                    'original_team': ranking['team']
                }
                
                # Add ADP and projected points if available (Underdog data)
                if 'adp' in ranking:
                    matched_data['adp'] = ranking['adp']
                if 'projected_points' in ranking:
                    matched_data['projected_points'] = ranking['projected_points']
                
                matched_rankings.append(matched_data)
            else:
                unmatched_rankings.append(ranking)
        
        cur.close()
        conn.close()
        
        print(f"✅ Matched {len(matched_rankings)} rankings")
        print(f"❓ {len(unmatched_rankings)} rankings not found in database")
        
        return matched_rankings, unmatched_rankings
    
    def save_rankings_to_database(self, matched_rankings: List[Dict]):
        """Save matched rankings to database"""
        print("💾 Saving rankings to database...")
        
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        # Create ranking sources
        sources = set(r['source_name'] for r in matched_rankings)
        source_ids = {}
        
        for source in sources:
            cur.execute("""
                INSERT INTO ranking_sources (source_name, base_url)
                VALUES (%s, %s)
                ON CONFLICT (source_name) DO NOTHING
            """, (source, f'https://www.{source.lower()}.com'))
            
            # Get source ID
            cur.execute("SELECT source_id FROM ranking_sources WHERE source_name = %s", (source,))
            source_ids[source] = cur.fetchone()[0]
        
        # Insert rankings
        inserted_count = 0
        for ranking in matched_rankings:
            try:
                source_id = source_ids[ranking['source_name']]
                
                cur.execute("""
                    INSERT INTO player_rankings (player_id, source_id, position_rank, ranking_date)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (player_id, source_id, ranking_date) DO UPDATE SET
                        position_rank = EXCLUDED.position_rank
                """, (
                    ranking['db_player_id'],
                    source_id,
                    ranking['position_rank'],
                    datetime.now().date()
                ))
                inserted_count += 1
            except Exception as e:
                print(f"❌ Error inserting ranking for {ranking['db_name']}: {e}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Saved {inserted_count} rankings to database")
    
    def generate_report(self, fp_rankings: List[Dict], ud_rankings: List[Dict], 
                       matched_rankings: List[Dict], unmatched_rankings: List[Dict]):
        """Generate comprehensive report"""
        print("\n" + "="*70)
        print("📊 NEW RANKINGS INTEGRATION REPORT")
        print("="*70)
        
        print(f"\n📈 DATA SOURCES:")
        print(f"  📊 FantasyPros: {len(fp_rankings)} rankings")
        print(f"  🎯 Underdog: {len(ud_rankings)} rankings (with ADP & projections)")
        print(f"  📋 Total: {len(fp_rankings) + len(ud_rankings)} rankings")
        
        print(f"\n🎯 MATCHING RESULTS:")
        print(f"  ✅ Successfully matched: {len(matched_rankings)}")
        print(f"  ❓ Not found in database: {len(unmatched_rankings)}")
        
        # Position breakdown
        print(f"\n📊 POSITION BREAKDOWN:")
        position_stats = {}
        for ranking in matched_rankings:
            pos = ranking['db_position']
            source = ranking['source_name']
            key = f"{pos}_{source}"
            position_stats[key] = position_stats.get(key, 0) + 1
        
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
            fp_count = position_stats.get(f"{pos}_FantasyPros", 0)
            ud_count = position_stats.get(f"{pos}_Underdog", 0)
            print(f"  {pos}: FantasyPros={fp_count}, Underdog={ud_count}")
        
        # Show some unmatched players if any
        if unmatched_rankings:
            print(f"\n❓ SAMPLE UNMATCHED PLAYERS:")
            by_source = {}
            for player in unmatched_rankings:
                source = player['source']
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append(player)
            
            for source, players in by_source.items():
                print(f"\n  {source} ({len(players)} unmatched):")
                for player in players[:5]:  # Show first 5
                    team_info = f" ({player['team']})" if player.get('team') else ""
                    print(f"    {player['position']} #{player['position_rank']} {player['name']}{team_info}")
                if len(players) > 5:
                    print(f"    ... and {len(players) - 5} more")
        
        # Underdog specific stats
        ud_matched = [r for r in matched_rankings if r['source_name'] == 'Underdog']
        if ud_matched:
            adp_data = [r.get('adp') for r in ud_matched if r.get('adp')]
            proj_data = [r.get('projected_points') for r in ud_matched if r.get('projected_points')]
            
            if adp_data:
                print(f"\n🎯 UNDERDOG ADP DATA:")
                print(f"  Players with ADP: {len(adp_data)}")
                print(f"  ADP Range: {min(adp_data):.1f} - {max(adp_data):.1f}")
            
            if proj_data:
                print(f"\n📈 UNDERDOG PROJECTIONS:")
                print(f"  Players with projections: {len(proj_data)}")
                print(f"  Points Range: {min(proj_data):.1f} - {max(proj_data):.1f}")
        
        print("\n" + "="*70)

def main():
    parser = NewRankingsParser()
    
    print("🚀 Starting new rankings integration...")
    
    # Parse FantasyPros rankings
    fp_rankings = parser.parse_fantasypros_rankings()
    
    # Parse Underdog rankings
    ud_rankings = parser.parse_underdog_rankings()
    
    if not fp_rankings and not ud_rankings:
        print("❌ No rankings data loaded.")
        return
    
    # Combine all rankings
    all_rankings = fp_rankings + ud_rankings
    
    # Match with database
    matched_rankings, unmatched_rankings = parser.match_with_database(all_rankings)
    
    # Save to database
    if matched_rankings:
        parser.save_rankings_to_database(matched_rankings)
    
    # Generate report
    parser.generate_report(fp_rankings, ud_rankings, matched_rankings, unmatched_rankings)
    
    print("\n🎉 New rankings integration completed!")

if __name__ == "__main__":
    main()