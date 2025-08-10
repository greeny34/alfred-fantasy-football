#!/usr/bin/env python3
"""
Mock ESPN Rankings Generator
Creates realistic ESPN fantasy football rankings for testing our integration
"""

import psycopg2
import os
from datetime import datetime
from typing import List, Dict, Tuple

class MockESPNRankings:
    def __init__(self):
        # Mock ESPN rankings based on typical 2024/2025 consensus
        self.mock_rankings = {
            'QB': [
                'Josh Allen', 'Lamar Jackson', 'Jalen Hurts', 'Patrick Mahomes', 'Dak Prescott',
                'Tua Tagovailoa', 'Joe Burrow', 'Justin Herbert', 'Kyler Murray', 'C.J. Stroud',
                'Anthony Richardson', 'Aaron Rodgers', 'Trevor Lawrence', 'Brock Purdy', 'Geno Smith',
                'Caleb Williams', 'Jordan Love', 'Kirk Cousins', 'Matthew Stafford', 'Jayden Daniels',
                'Daniel Jones', 'Russell Wilson', 'Derek Carr', 'Gardner Minshew', 'Andy Dalton',
                'Sam Darnold', 'Jameis Winston', 'Jacoby Brissett', 'Will Levis', 'Aidan O\'Connell'
            ],
            'RB': [
                'Christian McCaffrey', 'Austin Ekeler', 'Derrick Henry', 'Jonathan Taylor', 'Alvin Kamara',
                'Saquon Barkley', 'Nick Chubb', 'Josh Jacobs', 'Tony Pollard', 'Isiah Pacheco',
                'Kenneth Walker III', 'Joe Mixon', 'Aaron Jones', 'Rachaad White', 'Rhamondre Stevenson',
                'James Cook', 'De\'Von Achane', 'Jahmyr Gibbs', 'Najee Harris', 'David Montgomery',
                'Travis Etienne', 'Breece Hall', 'Kyren Williams', 'Javonte Williams', 'Brian Robinson Jr.',
                'Ezekiel Elliott', 'Alexander Mattison', 'Gus Edwards', 'Jerome Ford', 'Tyjae Spears',
                'Rico Dowdle', 'Chuba Hubbard', 'Raheem Mostert', 'Tyler Allgeier', 'Antonio Gibson',
                'Zack Moss', 'Miles Sanders', 'D\'Onta Foreman', 'Roschon Johnson', 'Justice Hill'
            ],
            'WR': [
                'Tyreek Hill', 'Stefon Diggs', 'A.J. Brown', 'Cooper Kupp', 'Davante Adams',
                'Mike Evans', 'DK Metcalf', 'CeeDee Lamb', 'Ja\'Marr Chase', 'Justin Jefferson',
                'Keenan Allen', 'DeVonta Smith', 'Chris Olave', 'Amari Cooper', 'Tee Higgins',
                'Calvin Ridley', 'DJ Moore', 'Jaylen Waddle', 'Nico Collins', 'Michael Pittman Jr.',
                'Terry McLaurin', 'Brandon Aiyuk', 'Courtland Sutton', 'Christian Kirk', 'Tyler Lockett',
                'Diontae Johnson', 'Jerry Jeudy', 'George Pickens', 'Marquise Goodwin', 'Gabe Davis',
                'Jordan Addison', 'Rome Odunze', 'Marvin Harrison Jr.', 'Malik Nabers', 'Xavier Worthy',
                'Jameson Williams', 'Zay Flowers', 'Tank Dell', 'Rashee Rice', 'Puka Nacua'
            ],
            'TE': [
                'Travis Kelce', 'Mark Andrews', 'T.J. Hockenson', 'George Kittle', 'Sam LaPorta',
                'Evan Engram', 'David Njoku', 'Kyle Pitts', 'Dallas Goedert', 'Jake Ferguson',
                'Pat Freiermuth', 'Tyler Higbee', 'Dalton Kincaid', 'Cole Kmet', 'Trey McBride',
                'Noah Fant', 'Hunter Henry', 'Mike Gesicki', 'Jonnu Smith', 'Isaiah Likely',
                'Chigoziem Okonkwo', 'Luke Musgrave', 'Gerald Everett', 'Zach Ertz', 'Austin Hooper',
                'Tyler Conklin', 'Dawson Knox', 'Daniel Bellinger', 'Cade Otton', 'Durham Smythe'
            ],
            'K': [
                'Justin Tucker', 'Harrison Butker', 'Tyler Bass', 'Younghoe Koo', 'Chris Boswell',
                'Brandon McManus', 'Daniel Carlson', 'Jake Moody', 'Cameron Dicker', 'Jason Sanders',
                'Greg Zuerlein', 'Matt Gay', 'Nick Folk', 'Wil Lutz', 'Ka\'imi Fairbairn',
                'Mason Crosby', 'Ryan Succop', 'Robbie Gould', 'Matt Prater', 'Joey Slye',
                'Chase McLaughlin', 'Cairo Santos', 'Dustin Hopkins', 'Jake Elliott', 'Evan McPherson',
                'Graham Gano', 'Jason Myers', 'Anders Carlson', 'Brandon Aubrey', 'Chad Ryland'
            ],
            'DST': [
                'San Francisco 49ers', 'Philadelphia Eagles', 'Buffalo Bills', 'Dallas Cowboys', 'Miami Dolphins',
                'Cleveland Browns', 'Pittsburgh Steelers', 'New York Jets', 'Baltimore Ravens', 'Kansas City Chiefs',
                'Denver Broncos', 'Seattle Seahawks', 'New Orleans Saints', 'Green Bay Packers', 'Detroit Lions',
                'Cincinnati Bengals', 'Los Angeles Chargers', 'Tampa Bay Buccaneers', 'Minnesota Vikings', 'Indianapolis Colts',
                'Jacksonville Jaguars', 'Houston Texans', 'Las Vegas Raiders', 'Tennessee Titans', 'Atlanta Falcons',
                'Los Angeles Rams', 'Washington Commanders', 'Chicago Bears', 'New York Giants', 'Arizona Cardinals',
                'Carolina Panthers', 'New England Patriots'
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
    
    def generate_mock_rankings(self) -> List[Dict]:
        """Generate mock ESPN rankings with proper format"""
        all_rankings = []
        
        for position, player_names in self.mock_rankings.items():
            for rank, name in enumerate(player_names, 1):
                # For DST, clean up team names
                if position == 'DST':
                    # Convert "San Francisco 49ers" to just the city/name part
                    team_name = name.replace(' Defense', '').replace(' DST', '')
                    # Map to team abbreviations
                    team_mapping = {
                        'San Francisco 49ers': 'SF',
                        'Philadelphia Eagles': 'PHI',
                        'Buffalo Bills': 'BUF',
                        'Dallas Cowboys': 'DAL',
                        'Miami Dolphins': 'MIA',
                        'Cleveland Browns': 'CLE',
                        'Pittsburgh Steelers': 'PIT',
                        'New York Jets': 'NYJ',
                        'Baltimore Ravens': 'BAL',
                        'Kansas City Chiefs': 'KC',
                        'Denver Broncos': 'DEN',
                        'Seattle Seahawks': 'SEA',
                        'New Orleans Saints': 'NO',
                        'Green Bay Packers': 'GB',
                        'Detroit Lions': 'DET',
                        'Cincinnati Bengals': 'CIN',
                        'Los Angeles Chargers': 'LAC',
                        'Tampa Bay Buccaneers': 'TB',
                        'Minnesota Vikings': 'MIN',
                        'Indianapolis Colts': 'IND',
                        'Jacksonville Jaguars': 'JAX',
                        'Houston Texans': 'HOU',
                        'Las Vegas Raiders': 'LV',
                        'Tennessee Titans': 'TEN',
                        'Atlanta Falcons': 'ATL',
                        'Los Angeles Rams': 'LAR',
                        'Washington Commanders': 'WAS',
                        'Chicago Bears': 'CHI',
                        'New York Giants': 'NYG',
                        'Arizona Cardinals': 'ARI',
                        'Carolina Panthers': 'CAR',
                        'New England Patriots': 'NE'
                    }
                    
                    team_abbr = team_mapping.get(name, '')
                    
                    all_rankings.append({
                        'name': team_name,
                        'position': position,
                        'team': team_abbr,
                        'rank': rank,
                        'source': 'ESPN',
                        'raw_text': name
                    })
                else:
                    all_rankings.append({
                        'name': name,
                        'position': position,
                        'team': '',  # Will be filled in by matching
                        'rank': rank,
                        'source': 'ESPN',
                        'raw_text': name
                    })
        
        return all_rankings
    
    def match_with_database(self, mock_rankings: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Match mock rankings with our player database
        Returns (matched_players, unmatched_espn_players)
        """
        print("🔗 Matching mock ESPN rankings with database...")
        
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
        unmatched_espn_players = []
        
        # Group rankings by position for easier processing
        rankings_by_pos = {}
        for ranking in mock_rankings:
            pos = ranking['position']
            if pos not in rankings_by_pos:
                rankings_by_pos[pos] = []
            rankings_by_pos[pos].append(ranking)
        
        for position, espn_players in rankings_by_pos.items():
            print(f"📊 Matching {position} players...")
            
            for espn_player in espn_players:
                espn_name = espn_player['name'].lower().strip()
                espn_position = espn_player['position']
                
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
                    
                    # For DST, match team names
                    if espn_position == 'DST':
                        # Try to match team abbreviation or city name
                        if (espn_player['team'] and db_team == espn_player['team']) or \
                           (espn_name in db_name_clean or db_name_clean in espn_name):
                            best_match = db_player
                            best_score = 95
                            break
                    
                    # Partial name matches for players
                    else:
                        espn_parts = espn_name.split()
                        db_parts = db_name_clean.split()
                        
                        if len(espn_parts) >= 2 and len(db_parts) >= 2:
                            # First and last name match
                            if espn_parts[0] == db_parts[0] and espn_parts[-1] == db_parts[-1]:
                                score = 95
                                if score > best_score:
                                    best_match = db_player
                                    best_score = score
                            
                            # Last name match (common for fantasy)
                            elif espn_parts[-1] == db_parts[-1]:
                                score = 80
                                if score > best_score:
                                    best_match = db_player
                                    best_score = score
                            
                            # First name match
                            elif espn_parts[0] == db_parts[0]:
                                score = 60
                                if score > best_score:
                                    best_match = db_player
                                    best_score = score
                
                if best_match and best_score >= 60:  # Lower threshold for mock data
                    matched_players.append({
                        'db_player_id': best_match[0],
                        'db_name': best_match[1],
                        'db_position': best_match[2],
                        'db_team': best_match[3],
                        'espn_name': espn_player['name'],
                        'espn_rank': espn_player['rank'],
                        'espn_position': espn_player['position'],
                        'espn_team': espn_player['team'],
                        'match_score': best_score,
                        'source': 'ESPN'
                    })
                else:
                    unmatched_espn_players.append(espn_player)
        
        cur.close()
        conn.close()
        
        print(f"✅ Matched {len(matched_players)} players")
        print(f"❓ {len(unmatched_espn_players)} ESPN players not found in database")
        
        return matched_players, unmatched_espn_players
    
    def save_rankings_to_database(self, matched_players: List[Dict]):
        """Save matched rankings to database"""
        print("💾 Saving mock ESPN rankings to database...")
        
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        # Ensure ESPN source exists
        cur.execute("""
            INSERT INTO ranking_sources (source_name, base_url)
            VALUES (%s, %s)
            ON CONFLICT (source_name) DO NOTHING
        """, ('ESPN', 'https://www.espn.com/fantasy/football/'))
        
        # Get ESPN source ID
        cur.execute("SELECT source_id FROM ranking_sources WHERE source_name = 'ESPN'")
        espn_source_id = cur.fetchone()[0]
        
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
                    espn_source_id,
                    player['espn_rank'],
                    datetime.now().date()
                ))
                inserted_count += 1
            except Exception as e:
                print(f"❌ Error inserting ranking for {player['db_name']}: {e}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Saved {inserted_count} ESPN rankings to database")
    
    def generate_report(self, matched_players: List[Dict], unmatched_espn_players: List[Dict]):
        """Generate a detailed report of the mock ranking results"""
        print("\n" + "="*60)
        print("📊 MOCK ESPN RANKINGS INTEGRATION REPORT")
        print("="*60)
        
        # Summary by position
        position_stats = {}
        for player in matched_players:
            pos = player['db_position']
            if pos not in position_stats:
                position_stats[pos] = {'matched': 0, 'total_espn': 0}
            position_stats[pos]['matched'] += 1
        
        # Count unmatched by position too
        for player in unmatched_espn_players:
            pos = player['position'] 
            if pos not in position_stats:
                position_stats[pos] = {'matched': 0, 'total_espn': 0}
        
        # Count total ESPN rankings by position
        for position, player_names in self.mock_rankings.items():
            if position not in position_stats:
                position_stats[position] = {'matched': 0, 'total_espn': len(player_names)}
            else:
                position_stats[position]['total_espn'] = len(player_names)
        
        print(f"\n📈 ESPN RANKING COVERAGE:")
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
            if pos in position_stats:
                matched = position_stats[pos]['matched']
                total_espn = position_stats[pos]['total_espn']
                percentage = (matched / total_espn * 100) if total_espn > 0 else 0
                print(f"  {pos}: {matched}/{total_espn} ESPN rankings matched ({percentage:.1f}%)")
        
        print(f"\n🎯 MATCHING RESULTS:")
        print(f"  ✅ Successfully matched: {len(matched_players)} players")
        print(f"  ❓ ESPN players not in DB: {len(unmatched_espn_players)} players")
        
        if unmatched_espn_players:
            print(f"\n❓ UNMATCHED ESPN PLAYERS (Not in our database):")
            by_position = {}
            for player in unmatched_espn_players:
                pos = player['position']
                if pos not in by_position:
                    by_position[pos] = []
                by_position[pos].append(player)
            
            for pos, players in sorted(by_position.items()):
                print(f"\n  {pos} ({len(players)} players):")
                for player in players[:10]:  # Show top 10
                    print(f"    #{player['rank']:2d} {player['name']}")
                if len(players) > 10:
                    print(f"    ... and {len(players) - 10} more")
        
        print(f"\n💡 NEXT STEPS:")
        print(f"  1. Review unmatched players - may need to add to our database")
        print(f"  2. Check team assignments for matched players") 
        print(f"  3. Build scrapers for other ranking sources (FantasyPros, Yahoo, etc.)")
        print(f"  4. Set up automated ranking updates")
        
        print("\n" + "="*60)

def main():
    generator = MockESPNRankings()
    
    print("🚀 Starting Mock ESPN Rankings Integration...")
    
    # Step 1: Generate mock rankings
    mock_rankings = generator.generate_mock_rankings()
    print(f"✅ Generated {len(mock_rankings)} mock ESPN rankings")
    
    # Step 2: Match with database
    matched_players, unmatched_espn_players = generator.match_with_database(mock_rankings)
    
    # Step 3: Save to database
    if matched_players:
        generator.save_rankings_to_database(matched_players)
    
    # Step 4: Generate report
    generator.generate_report(matched_players, unmatched_espn_players)
    
    print("\n🎉 Mock ESPN rankings integration completed!")
    print("💡 You can now test the ranking features in your web app!")

if __name__ == "__main__":
    main()