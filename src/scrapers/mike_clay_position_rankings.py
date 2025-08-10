#!/usr/bin/env python3
"""
Mike Clay's Position-Specific Fantasy Football Rankings Parser
Parses the provided Mike Clay position rankings and integrates with database
"""

import psycopg2
from datetime import datetime
import os
import re
from typing import List, Dict, Tuple

class MikeClayPositionRankings:
    def __init__(self):
        # Mike Clay's Position-Specific Rankings
        self.position_rankings = {
            'QB': [
                'Josh Allen, BUF', 'Lamar Jackson, BAL', 'Jayden Daniels, WAS', 'Jalen Hurts, PHI',
                'Joe Burrow, CIN', 'Patrick Mahomes, KC', 'Baker Mayfield, TB', 'Bo Nix, DEN',
                'Kyler Murray, ARI', 'Brock Purdy, SF', 'Caleb Williams, CHI', 'Justin Herbert, LAC',
                'Dak Prescott, DAL', 'Justin Fields, NYJ', 'Drake Maye, NE', 'Jordan Love, GB',
                'Jared Goff, DET', 'J.J. McCarthy, MIN', 'Tua Tagovailoa, MIA', 'Matthew Stafford, LAR',
                'C.J. Stroud, HOU', 'Trevor Lawrence, JAC', 'Cameron Ward, TEN', 'Michael Penix Jr., ATL',
                'Bryce Young, CAR', 'Geno Smith, LV', 'Anthony Richardson, IND', 'Sam Darnold, SEA',
                'Aaron Rodgers, PIT', 'Russell Wilson, NYG', 'Tyler Shough, NO', 'Daniel Jones, IND'
            ],
            'RB': [
                'Bijan Robinson, ATL', 'Saquon Barkley, PHI', 'Jahmyr Gibbs, DET', 'Christian McCaffrey, SF',
                'Ashton Jeanty, LV', 'De\'Von Achane, MIA', 'Jonathan Taylor, IND', 'Josh Jacobs, GB',
                'Derrick Henry, BAL', 'Bucky Irving, TB', 'Kyren Williams, LAR', 'Chase Brown, CIN',
                'James Cook, BUF', 'Kenneth Walker III, SEA', 'Alvin Kamara, NO', 'Chuba Hubbard, CAR',
                'James Conner, ARI', 'Omarion Hampton, LAC', 'Breece Hall, NYJ', 'Joe Mixon, HOU',
                'D\'Andre Swift, CHI', 'Aaron Jones, MIN', 'David Montgomery, DET', 'Kaleb Johnson, PIT',
                'TreVeyon Henderson, NE', 'RJ Harvey, DEN', 'Tony Pollard, TEN', 'Isiah Pacheco, KC',
                'Javonte Williams, DAL', 'Tyrone Tracy Jr., NYG', 'Brian Robinson Jr., WAS', 'Jaylen Warren, PIT',
                'Rhamondre Stevenson, NE', 'Cam Skattebo, NYG', 'J.K. Dobbins, DEN', 'Austin Ekeler, WAS',
                'Travis Etienne Jr., JAC', 'Tyjae Spears, TEN', 'Tank Bigsby, JAC', 'Jerome Ford, CLE',
                'Rachaad White, TB', 'Jordan Mason, MIN', 'Quinshon Judkins, CLE', 'Dylan Sampson, CLE',
                'Zach Charbonnet, SEA', 'Trey Benson, ARI', 'Tyler Allgeier, ATL', 'Najee Harris, LAC',
                'Jaylen Wright, MIA', 'Bhayshul Tuten, JAC'
            ],
            'WR': [
                'Ja\'Marr Chase, CIN', 'Justin Jefferson, MIN', 'CeeDee Lamb, DAL', 'Puka Nacua, LAR',
                'Malik Nabers, NYG', 'Amon-Ra St. Brown, DET', 'Nico Collins, HOU', 'Brian Thomas Jr., JAC',
                'A.J. Brown, PHI', 'Drake London, ATL', 'Ladd McConkey, LAC', 'Tee Higgins, CIN',
                'Tyreek Hill, MIA', 'Davante Adams, LAR', 'Jaxon Smith-Njigba, SEA', 'Terry McLaurin, WAS',
                'Garrett Wilson, NYJ', 'Mike Evans, TB', 'Marvin Harrison Jr., ARI', 'DK Metcalf, PIT',
                'DJ Moore, CHI', 'Rashee Rice, KC', 'Xavier Worthy, KC', 'Zay Flowers, BAL',
                'Courtland Sutton, DEN', 'Calvin Ridley, TEN', 'DeVonta Smith, PHI', 'Jaylen Waddle, MIA',
                'Jerry Jeudy, CLE', 'Jameson Williams, DET', 'George Pickens, DAL', 'Rome Odunze, CHI',
                'Tetairoa McMillan, CAR', 'Travis Hunter, JAC', 'Chris Godwin, TB', 'Jakobi Meyers, LV',
                'Chris Olave, NO', 'Cooper Kupp, SEA', 'Stefon Diggs, NE', 'Matthew Golden, GB',
                'Jordan Addison, MIN', 'Khalil Shakir, BUF', 'Jauan Jennings, SF', 'Deebo Samuel Sr., WAS',
                'Ricky Pearsall, SF', 'Keon Coleman, BUF', 'Michael Pittman Jr., IND', 'Jayden Reed, GB',
                'Darnell Mooney, ATL', 'Josh Downs, IND', 'Rashid Shaheed, NO', 'Tre Harris, LAC',
                'Jayden Higgins, HOU', 'Emeka Egbuka, TB', 'Adam Thielen, CAR', 'Xavier Legette, CAR',
                'Cedric Tillman, CLE', 'Hollywood Brown, KC', 'Brandon Aiyuk, SF', 'Quentin Johnston, LAC',
                'Jack Bech, LV', 'Wan\'Dale Robinson, NYG', 'Marvin Mims Jr., DEN', 'Kyle Williams, NE',
                'Rashod Bateman, BAL', 'Luther Burden III, CHI', 'Jalen McMillan, TB', 'Michael Wilson, ARI',
                'Pat Bryant, DEN', 'Christian Kirk, HOU'
            ],
            'TE': [
                'Brock Bowers, LV', 'Trey McBride, ARI', 'George Kittle, SF', 'Sam LaPorta, DET',
                'T.J. Hockenson, MIN', 'Travis Kelce, KC', 'David Njoku, CLE', 'Mark Andrews, BAL',
                'Evan Engram, DEN', 'Tucker Kraft, GB', 'Colston Loveland, CHI', 'Dallas Goedert, PHI',
                'Jake Ferguson, DAL', 'Dalton Kincaid, BUF', 'Tyler Warren, IND', 'Hunter Henry, NE',
                'Kyle Pitts, ATL', 'Chigoziem Okonkwo, TEN', 'Darren Waller, MIA', 'Zach Ertz, WAS',
                'Jonnu Smith, PIT', 'Brenton Strange, JAC', 'Mike Gesicki, CIN', 'Elijah Arroyo, SEA',
                'Mason Taylor, NYJ', 'Cade Otton, TB', 'Pat Freiermuth, PIT', 'Dalton Schultz, HOU',
                'Tyler Higbee, LAR', 'Theo Johnson, NYG'
            ],
            'DST': [
                'Texans D/ST, HOU', 'Steelers D/ST, PIT', 'Broncos D/ST, DEN', 'Vikings D/ST, MIN',
                'Seahawks D/ST, SEA', 'Ravens D/ST, BAL', 'Patriots D/ST, NE', 'Lions D/ST, DET',
                'Eagles D/ST, PHI', 'Bills D/ST, BUF', 'Colts D/ST, IND', 'Jets D/ST, NYJ',
                'Giants D/ST, NYG', 'Buccaneers D/ST, TB', 'Cardinals D/ST, ARI', 'Packers D/ST, GB',
                'Chiefs D/ST, KC', 'Bears D/ST, CHI', 'Rams D/ST, LAR', '49ers D/ST, SF'
            ],
            'K': [
                'Jake Bates, DET', 'Chase McLaughlin, TB', 'Cameron Dicker, LAC', 'Brandon Aubrey, DAL',
                'Jason Sanders, MIA', 'Tyler Bass, BUF', 'Jake Elliott, PHI', 'Chris Boswell, PIT',
                'Harrison Butker, KC', 'Cairo Santos, CHI', 'Tyler Loop, BAL', 'Matt Gay, WAS',
                'Ka\'imi Fairbairn, HOU', 'Joshua Karty, LAR', 'Brandon McManus, GB', 'Evan McPherson, CIN',
                'Jason Myers, SEA', 'Wil Lutz, DEN', 'Cam Little, JAC', 'Will Reichard, MIN'
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
    
    def parse_position_rankings(self) -> List[Dict]:
        """Parse Mike Clay's position rankings"""
        print("📊 Parsing Mike Clay's Position Rankings...")
        
        all_rankings = []
        
        for position, player_list in self.position_rankings.items():
            print(f"   Processing {position}: {len(player_list)} players")
            
            for rank, player_entry in enumerate(player_list, 1):
                # Parse "Player Name, TEAM" format
                if ', ' in player_entry:
                    name_part, team_part = player_entry.rsplit(', ', 1)
                    name = name_part.strip()
                    team = team_part.strip()
                    
                    # Handle D/ST names specially
                    if position == 'DST':
                        # Convert "Texans D/ST" to just "Texans" for name, keep HOU as team
                        if ' D/ST' in name:
                            name = name.replace(' D/ST', ' DST')
                    
                    all_rankings.append({
                        'rank': rank,
                        'name': name,
                        'team': team,
                        'position': position,
                        'source': 'Mike_Clay_Position_Rankings',
                        'raw_text': player_entry
                    })
                else:
                    print(f"⚠️  Could not parse: {player_entry}")
        
        print(f"✅ Parsed {len(all_rankings)} position-specific rankings")
        return all_rankings
    
    def match_with_database(self, rankings: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Match rankings with our player database"""
        print("🔗 Matching Mike Clay position rankings with database...")
        
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
        
        for ranking in rankings:
            ranking_name = ranking['name'].lower().strip()
            ranking_position = ranking['position']
            ranking_team = ranking['team']
            
            # Try to find match in database
            best_match = None
            best_score = 0
            
            for db_player in db_players:
                db_id, db_name, db_position, db_team = db_player
                
                # Must match position
                if db_position != ranking_position:
                    continue
                
                # Calculate name match score
                db_name_clean = db_name.lower().strip()
                
                # Exact match
                if ranking_name == db_name_clean:
                    best_match = db_player
                    best_score = 100
                    break
                
                # Handle DST matching
                if ranking_position == 'DST':
                    # Try matching team names
                    if ranking_team and db_team == ranking_team:
                        best_match = db_player
                        best_score = 95
                        break
                    # Try matching DST name patterns
                    if 'dst' in ranking_name and 'dst' in db_name_clean:
                        if ranking_team in db_name_clean or db_team in ranking_name:
                            best_match = db_player
                            best_score = 90
                            break
                
                # Partial name matches for players
                ranking_parts = ranking_name.split()
                db_parts = db_name_clean.split()
                
                if len(ranking_parts) >= 2 and len(db_parts) >= 2:
                    # First and last name match
                    if ranking_parts[0] == db_parts[0] and ranking_parts[-1] == db_parts[-1]:
                        score = 95
                        # Bonus for team match
                        if ranking_team and db_team == ranking_team:
                            score += 5
                        if score > best_score:
                            best_match = db_player
                            best_score = score
                    
                    # Last name match
                    elif ranking_parts[-1] == db_parts[-1]:
                        score = 85
                        # Bonus for team match
                        if ranking_team and db_team == ranking_team:
                            score += 10
                        if score > best_score:
                            best_match = db_player
                            best_score = score
                    
                    # Handle special cases like "Jr." suffix
                    elif 'jr.' in ranking_name or 'jr.' in db_name_clean:
                        # Try matching without Jr.
                        ranking_clean = ranking_name.replace('jr.', '').replace(' jr', '').strip()
                        db_clean = db_name_clean.replace('jr.', '').replace(' jr', '').strip()
                        
                        if ranking_clean == db_clean:
                            score = 90
                            if score > best_score:
                                best_match = db_player
                                best_score = score
            
            if best_match and best_score >= 85:  # Confidence threshold
                matched_players.append({
                    'db_player_id': best_match[0],
                    'db_name': best_match[1],
                    'db_position': best_match[2],
                    'db_team': best_match[3],
                    'ranking_name': ranking['name'],
                    'position_rank': ranking['rank'],
                    'position': ranking['position'],
                    'team': ranking['team'],
                    'match_score': best_score,
                    'source': 'Mike_Clay_Position_Rankings'
                })
            else:
                unmatched_rankings.append(ranking)
        
        cur.close()
        conn.close()
        
        print(f"✅ Matched {len(matched_players)} players")
        print(f"❓ {len(unmatched_rankings)} rankings not found in database")
        
        return matched_players, unmatched_rankings
    
    def save_rankings_to_database(self, matched_players: List[Dict]):
        """Save matched rankings to database"""
        print("💾 Saving Mike Clay position rankings to database...")
        
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        # Ensure Mike Clay Position Rankings source exists
        cur.execute("""
            INSERT INTO ranking_sources (source_name, base_url)
            VALUES (%s, %s)
            ON CONFLICT (source_name) DO NOTHING
        """, ('Mike_Clay_Position_Rankings', 'https://www.espn.com/fantasy/football/story/_/id/43261183/2025-fantasy-football-rankings-ppr-mike-clay-positions'))
        
        # Get Mike Clay Position Rankings source ID
        cur.execute("SELECT source_id FROM ranking_sources WHERE source_name = 'Mike_Clay_Position_Rankings'")
        source_id = cur.fetchone()[0]
        
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
                    source_id,
                    player['position_rank'],
                    datetime.now().date()
                ))
                inserted_count += 1
            except Exception as e:
                print(f"❌ Error inserting ranking for {player['db_name']}: {e}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Saved {inserted_count} Mike Clay position rankings to database")
    
    def generate_report(self, matched_players: List[Dict], unmatched_rankings: List[Dict]):
        """Generate detailed report"""
        print("\n" + "="*70)
        print("📊 MIKE CLAY POSITION RANKINGS REPORT")
        print("="*70)
        
        # Summary by position
        position_stats = {}
        for player in matched_players:
            pos = player['db_position']
            if pos not in position_stats:
                position_stats[pos] = {'matched': 0}
            position_stats[pos]['matched'] += 1
        
        # Count total rankings by position
        for position, players in self.position_rankings.items():
            if position not in position_stats:
                position_stats[position] = {'matched': 0, 'total': len(players)}
            else:
                position_stats[position]['total'] = len(players)
        
        print(f"\n📈 POSITION RANKING COVERAGE:")
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
            if pos in position_stats:
                matched = position_stats[pos]['matched']
                total = position_stats[pos]['total']
                percentage = (matched / total * 100) if total > 0 else 0
                print(f"  {pos}: {matched}/{total} position rankings matched ({percentage:.1f}%)")
        
        print(f"\n🎯 MATCHING RESULTS:")
        total_rankings = sum(len(players) for players in self.position_rankings.values())
        print(f"  📊 Total position rankings: {total_rankings}")
        print(f"  ✅ Successfully matched: {len(matched_players)} players")
        print(f"  ❓ Rankings not in DB: {len(unmatched_rankings)} players")
        
        if unmatched_rankings:
            print(f"\n❓ UNMATCHED POSITION RANKINGS:")
            by_position = {}
            for ranking in unmatched_rankings:
                pos = ranking['position']
                if pos not in by_position:
                    by_position[pos] = []
                by_position[pos].append(ranking)
            
            for pos, rankings in sorted(by_position.items()):
                print(f"\n  {pos} ({len(rankings)} players):")
                for ranking in rankings[:10]:  # Show top 10
                    print(f"    #{ranking['rank']:2d} {ranking['name']} ({ranking['team']})")
                if len(rankings) > 10:
                    print(f"    ... and {len(rankings) - 10} more")
        
        # Show sample of top matches by position
        print(f"\n🏆 TOP 5 MATCHED PLAYERS BY POSITION:")
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
            pos_players = [p for p in matched_players if p['db_position'] == pos]
            pos_players.sort(key=lambda x: x['position_rank'])
            
            if pos_players:
                print(f"\n  {pos}:")
                for player in pos_players[:5]:
                    print(f"    #{player['position_rank']:2d} {player['db_name']} ({player['db_team']})")
        
        print("\n" + "="*70)

def main():
    parser = MikeClayPositionRankings()
    
    print("🚀 Starting Mike Clay Position Rankings Integration...")
    
    # Step 1: Parse rankings
    rankings = parser.parse_position_rankings()
    
    if not rankings:
        print("❌ No rankings parsed from position data.")
        return
    
    # Step 2: Match with database
    matched_players, unmatched_rankings = parser.match_with_database(rankings)
    
    # Step 3: Save to database
    if matched_players:
        parser.save_rankings_to_database(matched_players)
    
    # Step 4: Generate report
    parser.generate_report(matched_players, unmatched_rankings)
    
    print("\n🎉 Mike Clay position rankings integration completed!")

if __name__ == "__main__":
    main()