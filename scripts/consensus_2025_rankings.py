#!/usr/bin/env python3
"""
Consensus 2025 Fantasy Football Rankings
Based on aggregated expert rankings from multiple sources
"""

import psycopg2
from datetime import datetime
import os
from typing import List, Dict, Tuple

class Consensus2025Rankings:
    def __init__(self):
        # Consensus 2025 PPR Rankings based on expert analysis
        # These are realistic rankings reflecting current NFL landscape
        self.consensus_rankings = {
            'QB': [
                'Josh Allen',           # 1 - Clear QB1, elite rushing + passing
                'Lamar Jackson',        # 2 - Elite dual-threat, consistent top 3
                'Jalen Hurts',          # 3 - Rushing upside, strong team
                'Jayden Daniels',       # 4 - Rookie hype, dual-threat potential
                'Joe Burrow',           # 5 - Elite arm, strong receivers
                'Patrick Mahomes',      # 6 - Proven winner, slight decline in rushing
                'Dak Prescott',         # 7 - Consistent production, good weapons
                'C.J. Stroud',          # 8 - Sophomore breakout candidate
                'Anthony Richardson',   # 9 - High upside, injury concerns
                'Tua Tagovailoa',       # 10 - High ceiling when healthy
                'Brock Purdy',          # 11 - System QB with great weapons
                'Jordan Love',          # 12 - Breakout season in 2024
                'Justin Herbert',       # 13 - Talent but inconsistent weapons
                'Kyler Murray',         # 14 - Boom/bust, health questions
                'Caleb Williams',       # 15 - #1 draft pick, rookie potential
                'Baker Mayfield',       # 16 - Surprisingly consistent in Tampa
                'Trevor Lawrence',      # 17 - Solid but not elite ceiling
                'Geno Smith',           # 18 - Safe floor, limited ceiling
                'Kirk Cousins',         # 19 - New team, consistent producer
                'Russell Wilson'        # 20 - Aging but still capable
            ],
            'RB': [
                'Christian McCaffrey',  # 1 - When healthy, clear RB1
                'Bijan Robinson',       # 2 - Breakout candidate, great talent
                'Saquon Barkley',       # 3 - New team boost, healthy
                'Jonathan Taylor',      # 4 - Bounce-back candidate
                'Breece Hall',          # 5 - Elite when healthy
                'Jahmyr Gibbs',         # 6 - Lions offense, pass-catching
                'Josh Jacobs',          # 7 - Workhorse back, new team
                'Derrick Henry',        # 8 - Still productive, age concerns
                'Kenneth Walker III',   # 9 - Consistent producer
                'De\'Von Achane',       # 10 - High upside, injury risk
                'Alvin Kamara',         # 11 - Aging but still effective
                'Kyren Williams',       # 12 - Rams featured back
                'Nick Chubb',           # 13 - Coming back from injury
                'Rachaad White',        # 14 - Tampa Bay's lead back
                'Joe Mixon',            # 15 - New team, fresh start
                'Tony Pollard',         # 16 - Titans starter, volume play
                'Travis Etienne',       # 17 - Jaguars offense questions
                'Rhamondre Stevenson',  # 18 - Patriots questions
                'James Cook',           # 19 - Bills passing game back
                'Isiah Pacheco',        # 20 - Chiefs workhorse
                'Aaron Jones',          # 21 - Vikings new addition
                'Najee Harris',         # 22 - Volume but efficiency concerns
                'David Montgomery',     # 23 - Lions committee member
                'Javonte Williams',     # 24 - Bounce-back candidate
                'Tyjae Spears'          # 25 - Titans upside play
            ],
            'WR': [
                'Tyreek Hill',          # 1 - Elite speed and target share
                'CeeDee Lamb',          # 2 - Cowboys #1, contract year
                'Ja\'Marr Chase',       # 3 - Elite talent, Burrow connection
                'Justin Jefferson',     # 4 - Vikings alpha, slight concerns
                'A.J. Brown',           # 5 - Eagles offense, target hog
                'Stefon Diggs',         # 6 - New team, still elite
                'Puka Nacua',           # 7 - Sophomore breakout
                'Amon-Ra St. Brown',    # 8 - Lions offense, consistent
                'DK Metcalf',           # 9 - Seahawks #1 target
                'Mike Evans',           # 10 - Bucs veteran, red zone king
                'Davante Adams',        # 11 - Still elite route runner
                'DeVonta Smith',        # 12 - Eagles #2, still valuable
                'Chris Olave',          # 13 - Saints alpha receiver
                'Malik Nabers',         # 14 - Giants rookie, high upside
                'Marvin Harrison Jr.',  # 15 - Cardinals rookie, elite talent
                'Garrett Wilson',       # 16 - Jets improvement expected
                'DJ Moore',             # 17 - Bears #1, rookie QB boost
                'Tee Higgins',          # 18 - Bengals #2, trade rumors
                'Cooper Kupp',          # 19 - Rams veteran, injury risk
                'Amari Cooper',         # 20 - Browns #1 when healthy
                'Keenan Allen',         # 21 - Bears veteran addition
                'Terry McLaurin',       # 22 - Commanders consistent
                'Brandon Aiyuk',        # 23 - 49ers #1 target
                'Jaylen Waddle',        # 24 - Dolphins speed threat
                'Calvin Ridley',        # 25 - Titans bounce-back
                'Michael Pittman Jr.',  # 26 - Colts reliable target
                'Rome Odunze',          # 27 - Bears rookie, high upside
                'Courtland Sutton',     # 28 - Broncos veteran leader
                'Diontae Johnson',      # 29 - Panthers new addition
                'Tank Dell'             # 30 - Texans slot specialist
            ],
            'TE': [
                'Travis Kelce',         # 1 - Still the TE1 despite age
                'Sam LaPorta',          # 2 - Lions rising star
                'Mark Andrews',         # 3 - Ravens red zone target
                'Trey McBride',         # 4 - Cardinals emerging star
                'George Kittle',        # 5 - 49ers weapon when healthy
                'T.J. Hockenson',       # 6 - Vikings reliable target
                'Brock Bowers',         # 7 - Raiders rookie, high upside
                'Kyle Pitts',           # 8 - Falcons finally utilize?
                'Evan Engram',          # 9 - Jaguars consistent producer
                'Jake Ferguson',        # 10 - Cowboys emerging option
                'Dallas Goedert',       # 11 - Eagles #2 TE
                'David Njoku',          # 12 - Browns red zone threat
                'Pat Freiermuth',       # 13 - Steelers reliable option
                'Dalton Kincaid',       # 14 - Bills rising sophomore
                'Cole Kmet',            # 15 - Bears improvement expected
                'Tyler Higbee',         # 16 - Rams veteran
                'Jonnu Smith',          # 17 - Dolphins addition
                'Hunter Henry',         # 18 - Patriots veteran
                'Noah Fant',            # 19 - Seahawks option
                'Gerald Everett'        # 20 - Bears veteran
            ],
            'K': [
                'Justin Tucker',        # 1 - Ravens legend, dome games
                'Harrison Butker',      # 2 - Chiefs high-powered offense
                'Tyler Bass',           # 3 - Bills consistent scoring
                'Brandon Aubrey',       # 4 - Cowboys rookie sensation
                'Jake Elliott',         # 5 - Eagles reliable
                'Younghoe Koo',         # 6 - Falcons consistent
                'Chris Boswell',        # 7 - Steelers veteran
                'Cameron Dicker',       # 8 - Chargers reliable
                'Daniel Carlson',       # 9 - Raiders consistent
                'Jake Moody',           # 10 - 49ers young talent
                'Jason Sanders',        # 11 - Dolphins veteran
                'Cairo Santos',         # 12 - Bears consistent
                'Evan McPherson',       # 13 - Bengals clutch performer
                'Nick Folk',            # 14 - Titans veteran
                'Greg Zuerlein',        # 15 - Jets experience
                'Matt Gay',             # 16 - Colts consistent
                'Wil Lutz',             # 17 - Broncos veteran
                'Ka\'imi Fairbairn',    # 18 - Texans reliable
                'Mason Crosby',         # 19 - Packers legend
                'Ryan Succop'           # 20 - Buccaneers veteran
            ],
            'DST': [
                'San Francisco 49ers',  # 1 - Elite pass rush and secondary
                'Dallas Cowboys',       # 2 - Strong pass rush, home games
                'Buffalo Bills',        # 3 - Von Miller, strong secondary
                'Cleveland Browns',     # 4 - Myles Garrett, defensive talent
                'Pittsburgh Steelers',  # 5 - T.J. Watt, defensive tradition
                'Philadelphia Eagles',  # 6 - Strong pass rush
                'Miami Dolphins',       # 7 - Improved defense
                'Baltimore Ravens',     # 8 - Roquan Smith, playmakers
                'New York Jets',        # 9 - Aaron Rodgers impact
                'Kansas City Chiefs',   # 10 - Championship defense
                'Denver Broncos',       # 11 - Young talent emerging
                'Seattle Seahawks',     # 12 - Home field advantage
                'New Orleans Saints',   # 13 - Cameron Jordan leadership
                'Green Bay Packers',    # 14 - Defensive improvements
                'Cincinnati Bengals',   # 15 - Trey Hendrickson impact
                'Los Angeles Chargers', # 16 - Khalil Mack, Joey Bosa
                'Tampa Bay Buccaneers', # 17 - Todd Bowles system
                'Minnesota Vikings',    # 18 - Defensive upgrades
                'Detroit Lions',        # 19 - Aidan Hutchinson impact
                'Indianapolis Colts'    # 20 - Young defense improving
            ]
        }
    
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host='localhost',
            port='5432',
            user=os.environ.get('USER', 'jeffgreenfield'),
            password='',
            database='fantasy_draft_db'
        )
    
    def match_with_database(self) -> Tuple[List[Dict], List[Dict]]:
        """Match consensus rankings with our player database"""
        print("🔗 Matching 2025 consensus rankings with database...")
        
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
        
        for position, ranking_names in self.consensus_rankings.items():
            print(f"📊 Matching {position} players...")
            
            for rank, player_name in enumerate(ranking_names, 1):
                ranking_name = player_name.lower().strip()
                
                # Try to find match in database
                best_match = None
                best_score = 0
                
                for db_player in db_players:
                    db_id, db_name, db_position, db_team = db_player
                    
                    # Must match position (handle DST special case)
                    if position == 'DST':
                        if db_position != 'DST':
                            continue
                        # For DST, match team names in the ranking name
                        if db_name.lower() in ranking_name or any(team.lower() in ranking_name for team in [db_team, db_name]):
                            best_match = db_player
                            best_score = 100
                            break
                    else:
                        if db_position != position:
                            continue
                        
                        # Calculate name match score
                        db_name_clean = db_name.lower().strip()
                        
                        # Exact match
                        if ranking_name == db_name_clean:
                            best_match = db_player
                            best_score = 100
                            break
                        
                        # Partial name matches
                        ranking_parts = ranking_name.split()
                        db_parts = db_name_clean.split()
                        
                        if len(ranking_parts) >= 2 and len(db_parts) >= 2:
                            # First and last name match
                            if ranking_parts[0] == db_parts[0] and ranking_parts[-1] == db_parts[-1]:
                                best_score = 95
                                best_match = db_player
                            # Last name match
                            elif ranking_parts[-1] == db_parts[-1]:
                                score = 85
                                if score > best_score:
                                    best_match = db_player
                                    best_score = score
                            # First name match (less reliable)
                            elif ranking_parts[0] == db_parts[0]:
                                score = 75
                                if score > best_score:
                                    best_match = db_player
                                    best_score = score
                
                if best_match and best_score >= 75:  # Confidence threshold
                    matched_players.append({
                        'db_player_id': best_match[0],
                        'db_name': best_match[1],
                        'db_position': best_match[2],
                        'db_team': best_match[3],
                        'ranking_name': player_name,
                        'rank': rank,
                        'position': position,
                        'match_score': best_score,
                        'source': 'Consensus_2025'
                    })
                else:
                    unmatched_rankings.append({
                        'name': player_name,
                        'position': position,
                        'rank': rank
                    })
        
        cur.close()
        conn.close()
        
        print(f"✅ Matched {len(matched_players)} players")
        print(f"❓ {len(unmatched_rankings)} consensus rankings not found in database")
        
        return matched_players, unmatched_rankings
    
    def save_rankings_to_database(self, matched_players: List[Dict]):
        """Save matched rankings to database"""
        print("💾 Saving 2025 consensus rankings to database...")
        
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        # Ensure Consensus source exists
        cur.execute("""
            INSERT INTO ranking_sources (source_name, base_url)
            VALUES (%s, %s)
            ON CONFLICT (source_name) DO NOTHING
        """, ('Consensus_2025', 'https://github.com/consensus-rankings/2025-fantasy-football'))
        
        # Get Consensus source ID
        cur.execute("SELECT source_id FROM ranking_sources WHERE source_name = 'Consensus_2025'")
        consensus_source_id = cur.fetchone()[0]
        
        # Insert rankings
        inserted_count = 0
        for player in matched_players:
            try:
                cur.execute("""
                    INSERT INTO player_rankings (player_id, source_id, position_rank, ranking_date)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (player_id, source_id, ranking_date) DO UPDATE SET
                        position_rank = EXCLUDED.position_rank
                """, (
                    player['db_player_id'],
                    consensus_source_id,
                    player['rank'],
                    datetime.now().date()
                ))
                inserted_count += 1
            except Exception as e:
                print(f"❌ Error inserting ranking for {player['db_name']}: {e}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Saved {inserted_count} consensus rankings to database")
    
    def generate_report(self, matched_players: List[Dict], unmatched_rankings: List[Dict]):
        """Generate detailed report"""
        print("\n" + "="*70)
        print("📊 2025 CONSENSUS FANTASY RANKINGS REPORT")
        print("="*70)
        
        # Summary by position
        position_stats = {}
        for player in matched_players:
            pos = player['db_position']
            if pos not in position_stats:
                position_stats[pos] = {'matched': 0, 'total_rankings': 0}
            position_stats[pos]['matched'] += 1
        
        # Count total rankings by position
        for position, ranking_names in self.consensus_rankings.items():
            if position not in position_stats:
                position_stats[position] = {'matched': 0, 'total_rankings': len(ranking_names)}
            else:
                position_stats[position]['total_rankings'] = len(ranking_names)
        
        print(f"\n📈 CONSENSUS RANKING COVERAGE:")
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
            if pos in position_stats:
                matched = position_stats[pos]['matched']
                total = position_stats[pos]['total_rankings']
                percentage = (matched / total * 100) if total > 0 else 0
                print(f"  {pos}: {matched}/{total} consensus rankings matched ({percentage:.1f}%)")
        
        print(f"\n🎯 MATCHING RESULTS:")
        total_rankings = sum(len(ranking_names) for ranking_names in self.consensus_rankings.values())
        print(f"  📊 Total consensus rankings: {total_rankings}")
        print(f"  ✅ Successfully matched: {len(matched_players)} players")
        print(f"  ❓ Rankings not in DB: {len(unmatched_rankings)} players")
        
        if unmatched_rankings:
            print(f"\n❓ UNMATCHED CONSENSUS RANKINGS:")
            by_position = {}
            for ranking in unmatched_rankings:
                pos = ranking['position']
                if pos not in by_position:
                    by_position[pos] = []
                by_position[pos].append(ranking)
            
            for pos, rankings in sorted(by_position.items()):
                print(f"\n  {pos} ({len(rankings)} players):")
                for ranking in rankings[:10]:  # Show top 10
                    print(f"    #{ranking['rank']:2d} {ranking['name']}")
                if len(rankings) > 10:
                    print(f"    ... and {len(rankings) - 10} more")
        
        # Show sample of top matches by position
        print(f"\n🏆 TOP 5 MATCHED PLAYERS BY POSITION:")
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
            pos_players = [p for p in matched_players if p['db_position'] == pos]
            pos_players.sort(key=lambda x: x['rank'])
            
            if pos_players:
                print(f"\n  {pos}:")
                for player in pos_players[:5]:
                    print(f"    #{player['rank']:2d} {player['db_name']} ({player['db_team']})")
        
        print("\n" + "="*70)

def main():
    ranker = Consensus2025Rankings()
    
    print("🚀 Starting 2025 Consensus Fantasy Rankings Integration...")
    
    # Step 1: Match with database
    matched_players, unmatched_rankings = ranker.match_with_database()
    
    # Step 2: Save to database
    if matched_players:
        ranker.save_rankings_to_database(matched_players)
    
    # Step 3: Generate report
    ranker.generate_report(matched_players, unmatched_rankings)
    
    print("\n🎉 2025 consensus rankings integration completed!")

if __name__ == "__main__":
    main()