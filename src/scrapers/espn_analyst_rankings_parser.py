#!/usr/bin/env python3
"""
ESPN Multi-Analyst Rankings Parser
Parses ESPN analyst rankings from Excel file and integrates with database
"""

import pandas as pd
import psycopg2
from datetime import datetime
import os
import re
from typing import List, Dict, Tuple
import numpy as np

class ESPNAnalystRankings:
    def __init__(self, excel_file='ranking from espn.xlsx'):
        self.excel_file = excel_file
        self.analysts = ['Bowen', 'Cockcroft', 'Dopp', 'Karabell', 'Loza', 'Moody', 'Yates']

    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host='localhost',
            port='5432',
            user=os.environ.get('USER', 'jeffgreenfield'),
            password='',
            database='fantasy_draft_db'
        )
    
    def load_and_parse_excel(self) -> pd.DataFrame:
        """Load and parse the ESPN rankings Excel file"""
        print("📊 Loading ESPN analyst rankings from Excel...")
        
        try:
            df = pd.read_excel(self.excel_file)
            print(f"✅ Loaded {len(df)} players from {len(self.analysts)} analysts")
            
            # Clean up the data
            df_clean = self.clean_excel_data(df)
            
            return df_clean
            
        except Exception as e:
            print(f"❌ Error reading Excel file: {e}")
            return pd.DataFrame()
    
    def normalize_team_name(self, team_raw: str) -> str:
        """Normalize team abbreviations to standard format"""
        team_mappings = {
            'Wsh': 'WAS', 'Was': 'WAS',
            'Phi': 'PHI', 'Cin': 'CIN', 'Bal': 'BAL', 'Buf': 'BUF',
            'Det': 'DET', 'Atl': 'ATL', 'Min': 'MIN', 'Chi': 'CHI',
            'Dal': 'DAL', 'Den': 'DEN', 'Hou': 'HOU', 'Jax': 'JAC',
            'Ind': 'IND', 'Ten': 'TEN', 'Cle': 'CLE', 'Pit': 'PIT',
            'Mia': 'MIA', 'Sea': 'SEA', 'Ari': 'ARI', 'Car': 'CAR',
            'Gb': 'GB', 'Ne': 'NE', 'Ny': 'NYG', 'Lv': 'LV',
            'Tb': 'TB', 'Sf': 'SF', 'Lar': 'LAR', 'Lac': 'LAC',
            'Kc': 'KC', 'No': 'NO', 'Nyj': 'NYJ', 'Nyg': 'NYG'
        }
        return team_mappings.get(team_raw, team_raw.upper())
    
    def clean_excel_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize the Excel data"""
        print("🧹 Cleaning Excel data...")
        
        df_clean = df.copy()
        
        # Parse player names and teams from "1. Player Name, Team" format
        df_clean['parsed_name'] = ''
        df_clean['parsed_team'] = ''
        
        for idx, row in df_clean.iterrows():
            player_text = str(row['Player'])
            
            # Extract name and team using more flexible regex
            # Pattern: "1. Player Name, Team" where team might have extra chars
            pattern = r'^\d+\.\s*([^,]+),\s*([A-Za-z]{2,4})\w*$'
            match = re.match(pattern, player_text)
            
            if match:
                name = match.group(1).strip()
                team_raw = match.group(2).strip()
                # Normalize team names
                team = self.normalize_team_name(team_raw)
                df_clean.at[idx, 'parsed_name'] = name
                df_clean.at[idx, 'parsed_team'] = team
            else:
                # Try pattern without leading number for DST
                pattern2 = r'^([^,]+),\s*([A-Za-z]{2,4})\w*$'
                clean_text = player_text.replace(str(row['POS Rank']) + '. ', '')
                match2 = re.match(pattern2, clean_text)
                if match2:
                    name = match2.group(1).strip()
                    team_raw = match2.group(2).strip()
                    team = self.normalize_team_name(team_raw)
                    df_clean.at[idx, 'parsed_name'] = name
                    df_clean.at[idx, 'parsed_team'] = team
                else:
                    print(f"⚠️  Could not parse: {player_text}")
                    df_clean.at[idx, 'parsed_name'] = player_text.replace(str(row['POS Rank']) + '. ', '') if 'POS Rank' in df_clean.columns else player_text
                    df_clean.at[idx, 'parsed_team'] = ''
        
        # Convert analyst rankings to numeric, handling 'NR' (Not Ranked)
        for analyst in self.analysts:
            df_clean[analyst] = pd.to_numeric(df_clean[analyst], errors='coerce')
        
        print(f"✅ Cleaned data for {len(df_clean)} players")
        return df_clean
    
    def calculate_consensus_rankings(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate consensus rankings from individual analyst rankings"""
        print("📈 Calculating consensus rankings...")
        
        df_consensus = df.copy()
        
        # Calculate average ranking (ignoring NaN/NR values)
        analyst_cols = [col for col in df.columns if col in self.analysts]
        df_consensus['consensus_avg'] = df_consensus[analyst_cols].mean(axis=1, skipna=True)
        
        # Calculate median ranking
        df_consensus['consensus_median'] = df_consensus[analyst_cols].median(axis=1, skipna=True)
        
        # Count how many analysts ranked each player
        df_consensus['analyst_count'] = df_consensus[analyst_cols].count(axis=1)
        
        # Calculate standard deviation (measure of agreement)
        df_consensus['ranking_std'] = df_consensus[analyst_cols].std(axis=1, skipna=True)
        
        # Create final consensus ranking (using average, sorted by position)
        for position in df_consensus['Position'].unique():
            pos_mask = df_consensus['Position'] == position
            pos_data = df_consensus[pos_mask].copy()
            
            # Sort by consensus average
            pos_data = pos_data.sort_values('consensus_avg')
            
            # Assign consensus position rank
            pos_data['consensus_position_rank'] = range(1, len(pos_data) + 1)
            
            # Update main dataframe
            df_consensus.loc[pos_mask, 'consensus_position_rank'] = pos_data['consensus_position_rank'].values
        
        print(f"✅ Calculated consensus rankings for {len(df_consensus)} players")
        return df_consensus
    
    def match_with_database(self, df: pd.DataFrame) -> Tuple[List[Dict], List[Dict]]:
        """Match ESPN rankings with our player database"""
        print("🔗 Matching ESPN analyst rankings with database...")
        
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        # Get all players from our database
        cur.execute("""
            SELECT player_id, name, position, team 
            FROM players 
            ORDER BY position, name
        """)
        db_players = cur.fetchall()
        
        matched_players = []
        unmatched_rankings = []
        
        for idx, row in df.iterrows():
            espn_name = row['parsed_name'].lower().strip()
            espn_position = row['Position']
            espn_team = row['parsed_team']
            
            # Skip if no name parsed
            if not espn_name or espn_name == 'nan':
                continue
            
            # Try to find match in database
            best_match = None
            best_score = 0
            
            for db_player in db_players:
                db_id, db_name, db_position, db_team = db_player
                
                # Must match position
                if db_position != espn_position:
                    continue
                
                # Calculate name match score
                db_name_clean = db_name.lower().strip()
                
                # Exact match
                if espn_name == db_name_clean:
                    best_match = db_player
                    best_score = 100
                    break
                
                # Partial name matches
                espn_parts = espn_name.split()
                db_parts = db_name_clean.split()
                
                if len(espn_parts) >= 2 and len(db_parts) >= 2:
                    # First and last name match
                    if espn_parts[0] == db_parts[0] and espn_parts[-1] == db_parts[-1]:
                        score = 95
                        # Bonus for team match
                        if espn_team and db_team == espn_team:
                            score += 5
                        if score > best_score:
                            best_match = db_player
                            best_score = score
                    
                    # Last name match
                    elif espn_parts[-1] == db_parts[-1]:
                        score = 85
                        # Bonus for team match
                        if espn_team and db_team == espn_team:
                            score += 10
                        if score > best_score:
                            best_match = db_player
                            best_score = score
            
            if best_match and best_score >= 85:  # Confidence threshold
                # Create individual analyst rankings
                for analyst in self.analysts:
                    analyst_rank = row[analyst]
                    if pd.notna(analyst_rank):  # Only include if analyst ranked this player
                        matched_players.append({
                            'db_player_id': best_match[0],
                            'db_name': best_match[1],
                            'db_position': best_match[2],
                            'db_team': best_match[3],
                            'espn_name': row['parsed_name'],
                            'position_rank': int(analyst_rank),
                            'analyst': analyst,
                            'position': row['Position'],
                            'team': row['parsed_team'],
                            'match_score': best_score
                        })
                
                # Also create consensus ranking
                if pd.notna(row['consensus_position_rank']):
                    matched_players.append({
                        'db_player_id': best_match[0],
                        'db_name': best_match[1],
                        'db_position': best_match[2],
                        'db_team': best_match[3],
                        'espn_name': row['parsed_name'],
                        'position_rank': int(row['consensus_position_rank']),
                        'analyst': 'ESPN_Consensus',
                        'position': row['Position'],
                        'team': row['parsed_team'],
                        'match_score': best_score,
                        'consensus_avg': row['consensus_avg'],
                        'analyst_count': row['analyst_count'],
                        'ranking_std': row['ranking_std'] if pd.notna(row['ranking_std']) else 0
                    })
            else:
                unmatched_rankings.append({
                    'name': row['parsed_name'],
                    'position': row['Position'],
                    'team': row['parsed_team'],
                    'pos_rank': row['POS Rank']
                })
        
        cur.close()
        conn.close()
        
        print(f"✅ Matched {len([p for p in matched_players if p['analyst'] != 'ESPN_Consensus'])} individual analyst rankings")
        print(f"🎯 Created {len([p for p in matched_players if p['analyst'] == 'ESPN_Consensus'])} consensus rankings")
        print(f"❓ {len(unmatched_rankings)} players not found in database")
        
        return matched_players, unmatched_rankings
    
    def save_rankings_to_database(self, matched_players: List[Dict]):
        """Save matched rankings to database"""
        print("💾 Saving ESPN analyst rankings to database...")
        
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        # Get unique analysts/sources to create
        unique_sources = set(p['analyst'] for p in matched_players)
        
        # Create ranking sources for each analyst
        source_ids = {}
        for source in unique_sources:
            cur.execute("""
                INSERT INTO ranking_sources (source_name, base_url)
                VALUES (%s, %s)
                ON CONFLICT (source_name) DO NOTHING
            """, (f'ESPN_{source}', 'https://www.espn.com/fantasy/football/rankings/'))
            
            # Get source ID
            cur.execute("SELECT source_id FROM ranking_sources WHERE source_name = %s", (f'ESPN_{source}',))
            source_ids[source] = cur.fetchone()[0]
        
        # Insert rankings
        inserted_count = 0
        for player in matched_players:
            try:
                source_id = source_ids[player['analyst']]
                
                cur.execute("""
                    INSERT INTO player_rankings (player_id, source_id, position_rank, ranking_date)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (player_id, source_id, ranking_date) DO UPDATE SET
                        position_rank = EXCLUDED.position_rank
                """, (
                    player['db_player_id'],
                    source_id,
                    player['position_rank'],
                    datetime.now().date()
                ))
                inserted_count += 1
            except Exception as e:
                print(f"❌ Error inserting ranking for {player['db_name']} ({player['analyst']}): {e}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Saved {inserted_count} ESPN analyst rankings to database")
    
    def generate_report(self, df: pd.DataFrame, matched_players: List[Dict], unmatched_rankings: List[Dict]):
        """Generate detailed report"""
        print("\n" + "="*70)
        print("📊 ESPN MULTI-ANALYST RANKINGS REPORT")
        print("="*70)
        
        # Analyst coverage stats
        print(f"\n📈 ANALYST COVERAGE:")
        for analyst in self.analysts:
            analyst_rankings = [p for p in matched_players if p['analyst'] == analyst]
            print(f"  {analyst}: {len(analyst_rankings)} player rankings")
        
        consensus_rankings = [p for p in matched_players if p['analyst'] == 'ESPN_Consensus']
        print(f"  ESPN_Consensus: {len(consensus_rankings)} player rankings")
        
        # Position breakdown
        print(f"\n📊 POSITION BREAKDOWN:")
        for position in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
            pos_players = df[df['Position'] == position]
            if len(pos_players) > 0:
                avg_analysts = pos_players['analyst_count'].mean()
                print(f"  {position}: {len(pos_players)} players (avg {avg_analysts:.1f} analysts per player)")
        
        print(f"\n🎯 MATCHING RESULTS:")
        print(f"  📊 Total ESPN players in file: {len(df)}")
        print(f"  ✅ Successfully matched: {len(set(p['db_player_id'] for p in matched_players))}")
        print(f"  ❓ Players not in DB: {len(unmatched_rankings)}")
        
        if unmatched_rankings:
            print(f"\n❓ UNMATCHED ESPN PLAYERS:")
            by_position = {}
            for player in unmatched_rankings:
                pos = player['position']
                if pos not in by_position:
                    by_position[pos] = []
                by_position[pos].append(player)
            
            for pos, players in sorted(by_position.items()):
                print(f"\n  {pos} ({len(players)} players):")
                for player in players[:5]:  # Show top 5
                    team_info = f" ({player['team']})" if player['team'] else ""
                    print(f"    #{player['pos_rank']:2d} {player['name']}{team_info}")
                if len(players) > 5:
                    print(f"    ... and {len(players) - 5} more")
        
        # Show consensus top 5 by position
        print(f"\n🏆 TOP 5 CONSENSUS RANKINGS BY POSITION:")
        for pos in ['QB', 'RB', 'WR', 'TE']:
            pos_consensus = [p for p in matched_players if p['analyst'] == 'ESPN_Consensus' and p['position'] == pos]
            pos_consensus.sort(key=lambda x: x['position_rank'])
            
            if pos_consensus:
                print(f"\n  {pos}:")
                for player in pos_consensus[:5]:
                    avg_rank = player.get('consensus_avg', 0)
                    analyst_count = player.get('analyst_count', 0)
                    print(f"    #{player['position_rank']:2d} {player['db_name']} ({player['db_team']}) - Avg: {avg_rank:.1f} ({analyst_count} analysts)")
        
        print("\n" + "="*70)

def main():
    parser = ESPNAnalystRankings()
    
    print("🚀 Starting ESPN Multi-Analyst Rankings Integration...")
    
    # Step 1: Load and parse Excel
    df = parser.load_and_parse_excel()
    
    if df.empty:
        print("❌ No data loaded from Excel file.")
        return
    
    # Step 2: Calculate consensus rankings
    df_with_consensus = parser.calculate_consensus_rankings(df)
    
    # Step 3: Match with database
    matched_players, unmatched_rankings = parser.match_with_database(df_with_consensus)
    
    # Step 4: Save to database
    if matched_players:
        parser.save_rankings_to_database(matched_players)
    
    # Step 5: Generate report
    parser.generate_report(df_with_consensus, matched_players, unmatched_rankings)
    
    print("\n🎉 ESPN multi-analyst rankings integration completed!")

if __name__ == "__main__":
    main()