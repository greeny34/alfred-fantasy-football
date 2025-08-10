#!/usr/bin/env python3
"""
Mike Clay's Top 150 Fantasy Football Rankings Parser
Parses the provided Mike Clay rankings text and integrates with database
"""

import psycopg2
from datetime import datetime
import os
import re
from typing import List, Dict, Tuple

class MikeClayTop150:
    def __init__(self):
        # Mike Clay's Top 150 rankings as provided
        self.rankings_text = """1. Ja'Marr Chase, CIN -- WR1 (Bye: 10)
2. Bijan Robinson, ATL -- RB1 (Bye: 5)
3. Justin Jefferson, MIN -- WR2 (Bye: 6)
4. Saquon Barkley, PHI -- RB2 (Bye: 9)
5. Jahmyr Gibbs, DET -- RB3 (Bye: 8)
6. CeeDee Lamb, DAL -- WR3 (Bye: 10)
7. Christian McCaffrey, SF -- RB4 (Bye: 14)
8. Puka Nacua, LAR -- WR4 (Bye: 8)
9. Malik Nabers, NYG -- WR5 (Bye: 14)
10. Amon-Ra St. Brown, DET -- WR6 (Bye: 8)
11. Ashton Jeanty, LV -- RB5 (Bye: 8)
12. De'Von Achane, MIA -- RB6 (Bye: 12)
13. Nico Collins, HOU -- WR7 (Bye: 6)
14. Brian Thomas Jr., JAC -- WR8 (Bye: 8)
15. A.J. Brown, PHI -- WR9 (Bye: 9)
16. Drake London, ATL -- WR10 (Bye: 5)
17. Jonathan Taylor, IND -- RB7 (Bye: 11)
18. Josh Jacobs, GB -- RB8 (Bye: 5)
19. Derrick Henry, BAL -- RB9 (Bye: 7)
20. Brock Bowers, LV -- TE1 (Bye: 8)
21. Trey McBride, ARI -- TE2 (Bye: 8)
22. Bucky Irving, TB -- RB10 (Bye: 9)
23. Kyren Williams, LAR -- RB11 (Bye: 8)
24. Ladd McConkey, LAC -- WR11 (Bye: 12)
25. Tee Higgins, CIN -- WR12 (Bye: 10)
26. Tyreek Hill, MIA -- WR13 (Bye: 12)
27. Davante Adams, LAR -- WR14 (Bye: 8)
28. Josh Allen, BUF -- QB1 (Bye: 7)
29. Lamar Jackson, BAL -- QB2 (Bye: 7)
30. Jayden Daniels, WAS -- QB3 (Bye: 12)
31. Jalen Hurts, PHI -- QB4 (Bye: 9)
32. Chase Brown, CIN -- RB12 (Bye: 10)
33. James Cook, BUF -- RB13 (Bye: 7)
34. Jaxon Smith-Njigba, SEA -- WR15 (Bye: 8)
35. Terry McLaurin, WAS -- WR16 (Bye: 12)
36. Garrett Wilson, NYJ -- WR17 (Bye: 9)
37. Kenneth Walker III, SEA -- RB14 (Bye: 8)
38. Alvin Kamara, NO -- RB15 (Bye: 11)
39. Joe Burrow, CIN -- QB5 (Bye: 10)
40. George Kittle, SF -- TE3 (Bye: 14)
41. Chuba Hubbard, CAR -- RB16 (Bye: 14)
42. James Conner, ARI -- RB17 (Bye: 8)
43. Omarion Hampton, LAC -- RB18 (Bye: 12)
44. Breece Hall, NYJ -- RB19 (Bye: 9)
45. Joe Mixon, HOU -- RB20 (Bye: 6)
46. Mike Evans, TB -- WR18 (Bye: 9)
47. Marvin Harrison Jr., ARI -- WR19 (Bye: 8)
48. DK Metcalf, PIT -- WR20 (Bye: 5)
49. DJ Moore, CHI -- WR21 (Bye: 5)
50. Rashee Rice, KC -- WR22 (Bye: 10)
51. Xavier Worthy, KC -- WR23 (Bye: 10)
52. D'Andre Swift, CHI -- RB21 (Bye: 5)
53. Zay Flowers, BAL -- WR24 (Bye: 7)
54. Courtland Sutton, DEN -- WR25 (Bye: 12)
55. Calvin Ridley, TEN -- WR26 (Bye: 10)
56. DeVonta Smith, PHI -- WR27 (Bye: 9)
57. Jaylen Waddle, MIA -- WR28 (Bye: 12)
58. Jerry Jeudy, CLE -- WR29 (Bye: 9)
59. Jameson Williams, DET -- WR30 (Bye: 8)
60. George Pickens, DAL -- WR31 (Bye: 10)
61. Sam LaPorta, DET -- TE4 (Bye: 8)
62. Patrick Mahomes, KC -- QB6 (Bye: 10)
63. Baker Mayfield, TB -- QB7 (Bye: 9)
64. Rome Odunze, CHI -- WR32 (Bye: 5)
65. Tetairoa McMillan, CAR -- WR33 (Bye: 14)
66. Travis Hunter, JAC -- WR34 (Bye: 8)
67. Aaron Jones, MIN -- RB22 (Bye: 6)
68. David Montgomery, DET -- RB23 (Bye: 8)
69. T.J. Hockenson, MIN -- TE5 (Bye: 6)
70. Kaleb Johnson, PIT -- RB24 (Bye: 5)
71. TreVeyon Henderson, NE -- RB25 (Bye: 14)
72. RJ Harvey, DEN -- RB26 (Bye: 12)
73. Chris Godwin, TB -- WR35 (Bye: 9)
74. Jakobi Meyers, LV -- WR36 (Bye: 8)
75. Chris Olave, NO -- WR37 (Bye: 11)
76. Cooper Kupp, SEA -- WR38 (Bye: 8)
77. Stefon Diggs, NE -- WR39 (Bye: 14)
78. Matthew Golden, GB -- WR40 (Bye: 5)
79. Jordan Addison, MIN -- WR41 (Bye: 6)
80. Tony Pollard, TEN -- RB27 (Bye: 10)
81. Isiah Pacheco, KC -- RB28 (Bye: 10)
82. Javonte Williams, DAL -- RB29 (Bye: 10)
83. Travis Kelce, KC -- TE6 (Bye: 10)
84. David Njoku, CLE -- TE7 (Bye: 9)
85. Mark Andrews, BAL -- TE8 (Bye: 7)
86. Evan Engram, DEN -- TE9 (Bye: 12)
87. Bo Nix, DEN -- QB8 (Bye: 12)
88. Kyler Murray, ARI -- QB9 (Bye: 8)
89. Brock Purdy, SF -- QB10 (Bye: 14)
90. Tyrone Tracy Jr., NYG -- RB30 (Bye: 14)
91. Brian Robinson Jr., WAS -- RB31 (Bye: 12)
92. Jaylen Warren, PIT -- RB32 (Bye: 5)
93. Rhamondre Stevenson, NE -- RB33 (Bye: 14)
94. Cam Skattebo, NYG -- RB34 (Bye: 14)
95. J.K. Dobbins, DEN -- RB35 (Bye: 12)
96. Khalil Shakir, BUF -- WR42 (Bye: 7)
97. Jauan Jennings, SF -- WR43 (Bye: 14)
98. Deebo Samuel Sr., WAS -- WR44 (Bye: 12)
99. Ricky Pearsall, SF -- WR45 (Bye: 14)
100. Keon Coleman, BUF -- WR46 (Bye: 7)
101. Michael Pittman Jr., IND -- WR47 (Bye: 11)
102. Jayden Reed, GB -- WR48 (Bye: 5)
103. Caleb Williams, CHI -- QB11 (Bye: 5)
104. Justin Herbert, LAC -- QB12 (Bye: 12)
105. Dak Prescott, DAL -- QB13 (Bye: 10)
106. Justin Fields, NYJ -- QB14 (Bye: 9)
107. Darnell Mooney, ATL -- WR49 (Bye: 5)
108. Josh Downs, IND -- WR50 (Bye: 11)
109. Rashid Shaheed, NO -- WR51 (Bye: 11)
110. Tre Harris, LAC -- WR52 (Bye: 12)
111. Jayden Higgins, HOU -- WR53 (Bye: 6)
112. Emeka Egbuka, TB -- WR54 (Bye: 9)
113. Tucker Kraft, GB -- TE10 (Bye: 5)
114. Austin Ekeler, WAS -- RB36 (Bye: 12)
115. Travis Etienne Jr., JAC -- RB37 (Bye: 8)
116. Tyjae Spears, TEN -- RB38 (Bye: 10)
117. Tank Bigsby, JAC -- RB39 (Bye: 8)
118. Jerome Ford, CLE -- RB40 (Bye: 9)
119. Rachaad White, TB -- RB41 (Bye: 9)
120. Jordan Mason, MIN -- RB42 (Bye: 6)
121. Drake Maye, NE -- QB15 (Bye: 14)
122. Jordan Love, GB -- QB16 (Bye: 5)
123. Jared Goff, DET -- QB17 (Bye: 8)
124. J.J. McCarthy, MIN -- QB18 (Bye: 6)
125. Colston Loveland, CHI -- TE11 (Bye: 5)
126. Dallas Goedert, PHI -- TE12 (Bye: 9)
127. Jake Ferguson, DAL -- TE13 (Bye: 10)
128. Dalton Kincaid, BUF -- TE14 (Bye: 7)
129. Tyler Warren, IND -- TE15 (Bye: 11)
130. Quinshon Judkins, CLE -- RB43 (Bye: 9)
131. Dylan Sampson, CLE -- RB44 (Bye: 9)
132. Zach Charbonnet, SEA -- RB45 (Bye: 8)
133. Trey Benson, ARI -- RB46 (Bye: 8)
134. Tyler Allgeier, ATL -- RB47 (Bye: 5)
135. Najee Harris, LAC -- RB48 (Bye: 12)
136. Adam Thielen, CAR -- WR55 (Bye: 14)
137. Xavier Legette, CAR -- WR56 (Bye: 14)
138. Cedric Tillman, CLE -- WR57 (Bye: 9)
139. Hollywood Brown, KC -- WR58 (Bye: 10)
140. Brandon Aiyuk, SF -- WR59 (Bye: 14)
141. Hunter Henry, NE -- TE16 (Bye: 14)
142. Kyle Pitts, ATL -- TE17 (Bye: 5)
143. Tua Tagovailoa, MIA -- QB19 (Bye: 12)
144. Matthew Stafford, LAR -- QB20 (Bye: 8)
145. C.J. Stroud, HOU -- QB21 (Bye: 6)
146. Jaylen Wright, MIA -- RB49 (Bye: 12)
147. Bhayshul Tuten, JAC -- RB50 (Bye: 8)
148. Braelon Allen, NYJ -- RB51 (Bye: 9)
149. Isaac Guerendo, SF -- RB52 (Bye: 14)
150. MarShawn Lloyd, GB -- RB53 (Bye: 5)"""

    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host='localhost',
            port='5432',
            user=os.environ.get('USER', 'jeffgreenfield'),
            password='',
            database='fantasy_draft_db'
        )
    
    def parse_rankings(self) -> List[Dict]:
        """Parse Mike Clay's rankings text"""
        print("📊 Parsing Mike Clay's Top 150 Rankings...")
        
        rankings = []
        lines = self.rankings_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse pattern: "1. Ja'Marr Chase, CIN -- WR1 (Bye: 10)"
            pattern = r'^(\d+)\.\s+([^,]+),\s+([A-Z]{2,4})\s+--\s+([A-Z]+)(\d+)?\s+\(Bye:\s+(\d+)\)'
            match = re.match(pattern, line)
            
            if match:
                rank = int(match.group(1))
                name = match.group(2).strip()
                team = match.group(3).strip()
                position = match.group(4).strip()
                bye_week = int(match.group(6))
                
                rankings.append({
                    'rank': rank,
                    'name': name,
                    'team': team,
                    'position': position,
                    'bye_week': bye_week,
                    'source': 'Mike_Clay_Top_150',
                    'raw_text': line
                })
            else:
                print(f"⚠️  Could not parse line: {line}")
        
        print(f"✅ Parsed {len(rankings)} player rankings")
        return rankings
    
    def match_with_database(self, rankings: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Match rankings with our player database"""
        print("🔗 Matching Mike Clay rankings with database...")
        
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
                
                # Partial name matches
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
                    'rank': ranking['rank'],
                    'position': ranking['position'],
                    'team': ranking['team'],
                    'bye_week': ranking['bye_week'],
                    'match_score': best_score,
                    'source': 'Mike_Clay_Top_150'
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
        print("💾 Saving Mike Clay Top 150 rankings to database...")
        
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        # Ensure Mike Clay source exists
        cur.execute("""
            INSERT INTO ranking_sources (source_name, base_url)
            VALUES (%s, %s)
            ON CONFLICT (source_name) DO NOTHING
        """, ('Mike_Clay_Top_150', 'https://www.espn.com/fantasy/football/story/_/id/43261183/2025-fantasy-football-rankings-ppr-mike-clay'))
        
        # Get Mike Clay source ID
        cur.execute("SELECT source_id FROM ranking_sources WHERE source_name = 'Mike_Clay_Top_150'")
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
                    player['rank'],
                    datetime.now().date()
                ))
                inserted_count += 1
            except Exception as e:
                print(f"❌ Error inserting ranking for {player['db_name']}: {e}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Saved {inserted_count} Mike Clay rankings to database")
    
    def generate_report(self, matched_players: List[Dict], unmatched_rankings: List[Dict]):
        """Generate detailed report"""
        print("\n" + "="*70)
        print("📊 MIKE CLAY TOP 150 RANKINGS REPORT")
        print("="*70)
        
        # Summary by position
        position_stats = {}
        for player in matched_players:
            pos = player['db_position']
            if pos not in position_stats:
                position_stats[pos] = {'matched': 0}
            position_stats[pos]['matched'] += 1
        
        # Count unmatched by position
        for ranking in unmatched_rankings:
            pos = ranking['position']
            if pos not in position_stats:
                position_stats[pos] = {'matched': 0}
        
        print(f"\n📈 MIKE CLAY RANKING COVERAGE:")
        for pos in ['QB', 'RB', 'WR', 'TE']:
            if pos in position_stats:
                matched = position_stats[pos]['matched']
                print(f"  {pos}: {matched} players matched")
        
        print(f"\n🎯 MATCHING RESULTS:")
        print(f"  📊 Total Mike Clay rankings: 150")
        print(f"  ✅ Successfully matched: {len(matched_players)} players")
        print(f"  ❓ Rankings not in DB: {len(unmatched_rankings)} players")
        
        if unmatched_rankings:
            print(f"\n❓ UNMATCHED MIKE CLAY RANKINGS:")
            by_position = {}
            for ranking in unmatched_rankings:
                pos = ranking['position']
                if pos not in by_position:
                    by_position[pos] = []
                by_position[pos].append(ranking)
            
            for pos, rankings in sorted(by_position.items()):
                print(f"\n  {pos} ({len(rankings)} players):")
                for ranking in rankings[:10]:  # Show top 10
                    print(f"    #{ranking['rank']:3d} {ranking['name']} ({ranking['team']})")
                if len(rankings) > 10:
                    print(f"    ... and {len(rankings) - 10} more")
        
        # Show sample of top matches by position
        print(f"\n🏆 TOP 5 MATCHED PLAYERS BY POSITION:")
        for pos in ['QB', 'RB', 'WR', 'TE']:
            pos_players = [p for p in matched_players if p['db_position'] == pos]
            pos_players.sort(key=lambda x: x['rank'])
            
            if pos_players:
                print(f"\n  {pos}:")
                for player in pos_players[:5]:
                    print(f"    #{player['rank']:3d} {player['db_name']} ({player['db_team']})")
        
        print("\n" + "="*70)

def main():
    parser = MikeClayTop150()
    
    print("🚀 Starting Mike Clay Top 150 Rankings Integration...")
    
    # Step 1: Parse rankings
    rankings = parser.parse_rankings()
    
    if not rankings:
        print("❌ No rankings parsed from text.")
        return
    
    # Step 2: Match with database
    matched_players, unmatched_rankings = parser.match_with_database(rankings)
    
    # Step 3: Save to database
    if matched_players:
        parser.save_rankings_to_database(matched_players)
    
    # Step 4: Generate report
    parser.generate_report(matched_players, unmatched_rankings)
    
    print("\n🎉 Mike Clay Top 150 rankings integration completed!")

if __name__ == "__main__":
    main()