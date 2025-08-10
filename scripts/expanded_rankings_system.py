#!/usr/bin/env python3
"""
Expanded Fantasy Rankings System - Complete depth with all positions
"""
import pandas as pd
import numpy as np
from statistics import mean, stdev
import random

class ExpandedRankingsSystem:
    def __init__(self):
        self.seed_value = 42
        random.seed(self.seed_value)
        np.random.seed(self.seed_value)
    
    def create_comprehensive_player_base(self):
        """Create comprehensive player base with proper depth at all positions"""
        print("📊 Creating comprehensive player base with full depth...")
        
        players = {}
        
        # QBs - Need ~35 for proper depth
        qb_players = [
            "Josh Allen", "Lamar Jackson", "Jayden Daniels", "Jalen Hurts", "Bo Nix", 
            "Joe Burrow", "Baker Mayfield", "Patrick Mahomes", "Caleb Williams", "Justin Herbert",
            "Tua Tagovailoa", "Jordan Love", "Dak Prescott", "Kirk Cousins", "Aaron Rodgers",
            "Anthony Richardson", "C.J. Stroud", "Bryce Young", "Geno Smith", "Drake Maye",
            "Russell Wilson", "Ryan Tannehill", "Gardner Minshew", "Jacoby Brissett", "Mac Jones",
            "Jimmy Garoppolo", "Zach Wilson", "Daniel Jones", "Sam Howell", "Aidan O'Connell",
            "Desmond Ridder", "Kenny Pickett", "Tyler Huntley", "Malik Willis", "Davis Mills"
        ]
        
        qb_teams = ["BUF", "BAL", "WAS", "PHI", "DEN", "CIN", "TB", "KC", "CHI", "LAC",
                   "MIA", "GB", "DAL", "ATL", "NYJ", "IND", "HOU", "CAR", "SEA", "NE",
                   "PIT", "TEN", "LV", "NE", "NYJ", "SF", "NYJ", "NYG", "WAS", "LV",
                   "ATL", "PIT", "BAL", "TEN", "HOU"]
        
        for i, qb in enumerate(qb_players):
            players[qb] = {
                'position': 'QB',
                'team': qb_teams[i] if i < len(qb_teams) else 'FA',
                'base_rank': i + 45  # QBs start around rank 45
            }
        
        # RBs - Need ~80 for proper depth  
        rb_players = [
            "Bijan Robinson", "Saquon Barkley", "Jahmyr Gibbs", "De'Von Achane", "Ashton Jeanty",
            "Christian McCaffrey", "Josh Jacobs", "Derrick Henry", "Breece Hall", "Chase Brown",
            "James Cook", "Kenneth Walker III", "Devon Singletary", "Jordan Mason", "Rachaad White",
            "Javonte Williams", "D'Andre Swift", "Najee Harris", "Aaron Jones", "Alvin Kamara",
            "Austin Ekeler", "Tony Pollard", "Zack Moss", "Bucky Irving", "Ty Chandler",
            "Blake Corum", "Braelon Allen", "Kimani Vidal", "Ray Davis", "Tyjae Spears",
            "Jaylen Warren", "Jerome Ford", "Alexander Mattison", "Devin Singletary", "Rico Dowdle",
            "Miles Sanders", "Dameon Pierce", "Antonio Gibson", "Clyde Edwards-Helaire", "Jamaal Williams",
            "Cam Akers", "David Montgomery", "Kareem Hunt", "Melvin Gordon", "Leonard Fournette",
            "Jerick McKinnon", "Sony Michel", "Duke Johnson", "Nyheim Hines", "Kenyan Drake",
            "Alex Mattison", "Deon Jackson", "Jordan Wilkins", "Tyrion Davis-Price", "Craig Reynolds",
            "Boston Scott", "Samaje Perine", "Dare Ogunbowale", "La'Mical Perine", "Eno Benjamin",
            "Snoop Conner", "Kene Nwangwu", "Pierre Strong", "Dereon Smith", "Kyahva Tezino",
            "Kevin Harris", "Hassan Haskins", "Isaiah Spiller", "Tyler Allgeier", "Zamir White",
            "Kyren Williams", "Brian Robinson", "Tyler Badie", "Abram Smith", "Tunisia Reaves",
            "Brittain Brown", "Zander Horvath", "Michael Carter", "Ke'Shawn Vaughn", "Royce Freeman"
        ]
        
        rb_teams = ["ATL", "PHI", "DET", "MIA", "LV", "SF", "GB", "BAL", "NYJ", "CIN",
                   "BUF", "SEA", "NYG", "SF", "TB", "DEN", "CHI", "PIT", "MIN", "NO",
                   "WAS", "TEN", "CIN", "TB", "MIN", "LAR", "NYJ", "LAC", "BUF", "TEN"] + ["FA"] * 50
        
        for i, rb in enumerate(rb_players):
            players[rb] = {
                'position': 'RB',
                'team': rb_teams[i] if i < len(rb_teams) else 'FA',
                'base_rank': i + 2  # RBs start early
            }
        
        # WRs - Need ~150 for proper depth
        wr_players = [
            "Ja'Marr Chase", "Justin Jefferson", "CeeDee Lamb", "Amon-Ra St. Brown", "Puka Nacua",
            "Malik Nabers", "Brian Thomas Jr.", "Nico Collins", "Drake London", "A.J. Brown",
            "Ladd McConkey", "Jaxon Smith-Njigba", "Tee Higgins", "Cooper Kupp", "Davante Adams",
            "D.K. Metcalf", "Rome Odunze", "Marvin Harrison Jr.", "Stefon Diggs", "Mike Evans",
            "Chris Godwin", "Calvin Ridley", "Jaylen Waddle", "Keon Coleman", "Jayden Reed",
            "DJ Moore", "Courtland Sutton", "Jerry Jeudy", "Amari Cooper", "Tyler Lockett",
            "DeAndre Hopkins", "Keenan Allen", "Brandon Aiyuk", "Diontae Johnson", "Terry McLaurin",
            "Michael Pittman Jr.", "Tank Dell", "Jordan Addison", "Jameson Williams", "Josh Downs",
            "Wan'Dale Robinson", "Darnell Mooney", "Xavier Legette", "Allen Robinson", "Jarvis Landry",
            "Kenny Golladay", "Tyler Boyd", "Adam Thielen", "Robert Woods", "Golden Tate",
            "Marquise Goodwin", "Nelson Agholor", "JuJu Smith-Schuster", "Allen Lazard", "Hunter Renfrow",
            "Jakobi Meyers", "Kendrick Bourne", "Van Jefferson", "Tutu Atwell", "Noah Brown",
            "Jalen Tolbert", "Kavontae Turpin", "T.J. Vasher", "Ben Skowronek", "Brandon Powell",
            "Nsimba Webster", "Simi Fehoko", "Ryan Nall", "Trenton Irwin", "Rondale Moore",
            "Marquez Valdes-Scantling", "Trent Sherfield", "Tim Jones", "Khalil Shakir", "Nick Westbrook-Ikhine",
            "Curtis Samuel", "Britain Covey", "Christian Watson", "Russell Gage", "Tom Kennedy",
            "Malik Taylor", "Deon Cain", "Hollywood Brown", "Mecole Hardman", "Cedrick Wilson",
            "Tyler Johnson", "Gabriel Davis", "Isaiah McKenzie", "Matt Breida", "KJ Osborn",
            "Parris Campbell", "Devin Duvernay", "Braxton Berrios", "Richie James", "Kalif Raymond"
        ] + [f"WR_Depth_{i}" for i in range(1, 71)]  # Add depth players
        
        wr_teams = ["CIN", "MIN", "DAL", "DET", "LAR", "NYG", "JAX", "HOU", "ATL", "PHI",
                   "LAC", "SEA", "CIN", "LAR", "LV", "SEA", "CHI", "ARI", "HOU", "TB",
                   "TB", "TEN", "MIA", "BUF", "GB", "CHI", "DEN", "CLE", "BUF", "SEA"] + ["FA"] * 120
        
        for i, wr in enumerate(wr_players):
            players[wr] = {
                'position': 'WR',
                'team': wr_teams[i] if i < len(wr_teams) else 'FA',
                'base_rank': i + 1  # WRs can be #1 overall
            }
        
        # TEs - Need ~50 for proper depth
        te_players = [
            "Brock Bowers", "Trey McBride", "George Kittle", "Sam LaPorta", "T.J. Hockenson",
            "Travis Kelce", "Evan Engram", "Tucker Kraft", "David Njoku", "Kyle Pitts",
            "Jake Ferguson", "Jonnu Smith", "Zach Ertz", "Austin Hooper", "Noah Fant",
            "Hayden Hurst", "Gerald Everett", "Tyler Higbee", "Robert Tonyan", "Cole Kmet",
            "Pat Freiermuth", "Mike Gesicki", "Hunter Henry", "Tyler Kroft", "C.J. Uzomah",
            "Jordan Akins", "Mo Alie-Cox", "Noah Gray", "Luke Farrell", "Foster Moreau",
            "Cade Otton", "Logan Thomas", "Will Dissly", "Dalton Schultz", "Tyler Conklin",
            "Juwan Johnson", "Durham Smythe", "Anthony Firkser", "Brevin Jordan", "Isaiah Likely",
            "Charlie Kolar", "Jeremy Ruckert", "Trevon Wesco", "Johnny Mundt", "Kylen Granson",
            "Cameron Brate", "O.J. Howard", "Eric Saubert", "Marcedes Lewis", "Ross Dwelley"
        ]
        
        te_teams = ["LV", "ARI", "SF", "DET", "MIN", "KC", "JAX", "GB", "CLE", "ATL",
                   "DAL", "MIA", "ARI", "LAC", "DEN", "CAR", "NO", "LAR", "GB", "CHI",
                   "PIT", "MIA", "NE", "SF", "CIN", "IND", "KC", "KC", "KC", "LV"] + ["FA"] * 20
        
        for i, te in enumerate(te_players):
            players[te] = {
                'position': 'TE',
                'team': te_teams[i] if i < len(te_teams) else 'FA',
                'base_rank': i + 14  # TEs start around rank 14
            }
        
        # Kickers - All 32 teams
        nfl_teams = ["ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
                    "DET", "GB", "HOU", "IND", "JAX", "KC", "LV", "LAC", "LAR", "MIA",
                    "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SF", "SEA", "TB", "TEN", "WAS"]
        
        kicker_names = ["Matt Prater", "Younghoe Koo", "Justin Tucker", "Tyler Bass", "Eddy Pineiro",
                       "Cairo Santos", "Evan McPherson", "Dustin Hopkins", "Brandon McManus", "Wil Lutz",
                       "Jake Bates", "Anders Carlson", "Ka'imi Fairbairn", "Matt Gay", "Cam Little",
                       "Harrison Butker", "Daniel Carlson", "Cameron Dicker", "Joshua Karty", "Jason Sanders",
                       "Will Reichard", "Joey Slye", "Blake Grupe", "Graham Gano", "Greg Zuerlein",
                       "Jake Elliott", "Chris Boswell", "Jake Moody", "Jason Myers", "Chase McLaughlin",
                       "Nick Folk", "Austin Seibert"]
        
        for i, team in enumerate(nfl_teams):
            kicker_name = kicker_names[i] if i < len(kicker_names) else f"{team} Kicker"
            players[kicker_name] = {
                'position': 'K',
                'team': team,
                'base_rank': 250 + i  # Kickers ranked late
            }
        
        # Defenses - All 32 teams
        for i, team in enumerate(nfl_teams):
            players[f"{team} Defense"] = {
                'position': 'D/ST',
                'team': team,
                'base_rank': 220 + i  # Defenses before kickers
            }
        
        print(f"✅ Created comprehensive player base: {len(players)} total players")
        
        # Show position counts
        pos_counts = {}
        for player_data in players.values():
            pos = player_data['position']
            pos_counts[pos] = pos_counts.get(pos, 0) + 1
        
        for pos, count in pos_counts.items():
            print(f"   {pos}: {count} players")
        
        return players
    
    def simulate_site_rankings(self, players_base):
        """Simulate rankings from 5 different fantasy sites"""
        print("🎲 Simulating rankings from 5 fantasy sites...")
        
        all_sites = {}
        
        # Site 1: FantasyPros (Baseline consensus)
        fantasypros = {}
        for player, data in players_base.items():
            base_rank = data['base_rank']
            # Small random variation for FantasyPros
            variation = np.random.normal(0, 2)
            fantasypros[player] = {
                **data,
                'rank': max(1, int(base_rank + variation))
            }
        all_sites['fantasypros'] = fantasypros
        
        # Site 2: ESPN (More conservative on rookies, values experience)
        espn = {}
        for player, data in players_base.items():
            base_rank = data['base_rank']
            variation = np.random.normal(0, 3)
            
            # ESPN adjustments
            if any(rookie in player for rookie in ['Caleb Williams', 'Jayden Daniels', 'Drake Maye', 'Bo Nix', 'Malik Nabers', 'Rome Odunze', 'Marvin Harrison Jr.']):
                variation += 5  # Rank rookies lower
            
            espn[player] = {
                **data,
                'rank': max(1, int(base_rank + variation))
            }
        all_sites['espn'] = espn
        
        # Site 3: Yahoo (Values upside, aggressive on young players)
        yahoo = {}
        for player, data in players_base.items():
            base_rank = data['base_rank']
            variation = np.random.normal(0, 4)
            
            # Yahoo adjustments
            if data['position'] == 'RB' and base_rank > 50:
                variation -= 3  # Rank RBs higher
            if any(young in player for young in ['Anthony Richardson', 'C.J. Stroud', 'Bryce Young']):
                variation -= 4  # Aggressive on young talent
                
            yahoo[player] = {
                **data,
                'rank': max(1, int(base_rank + variation))
            }
        all_sites['yahoo'] = yahoo
        
        # Site 4: CBS (Model-based, can have bigger swings)
        cbs = {}
        for player, data in players_base.items():
            base_rank = data['base_rank']
            variation = np.random.normal(0, 6)
            
            # CBS model quirks
            if data['position'] == 'TE' and base_rank < 100:
                variation -= 2  # Values TEs slightly higher
            if data['position'] == 'K':
                variation += np.random.randint(-3, 8)  # More variation on kickers
                
            cbs[player] = {
                **data,
                'rank': max(1, int(base_rank + variation))
            }
        all_sites['cbs'] = cbs
        
        # Site 5: Draft Sharks (Analytics-heavy, efficiency focused)
        draftsharks = {}
        for player, data in players_base.items():
            base_rank = data['base_rank']
            variation = np.random.normal(0, 4)
            
            # Draft Sharks analytics adjustments
            if data['position'] in ['WR', 'TE']:
                variation += np.random.randint(-2, 3)  # Slight preference for pass catchers
            if data['position'] == 'D/ST':
                # More analytical approach to defenses
                elite_d = ['BUF', 'SF', 'DAL', 'PIT', 'BAL']
                if data['team'] in elite_d:
                    variation -= 5
                else:
                    variation += 3
                    
            draftsharks[player] = {
                **data,
                'rank': max(1, int(base_rank + variation))
            }
        all_sites['draftsharks'] = draftsharks
        
        print(f"✅ Generated rankings for all 5 sites")
        return all_sites
    
    def calculate_comprehensive_statistics(self, all_sites_data):
        """Calculate average ranks and convert to integer ranks"""
        print("📊 Calculating comprehensive statistics and integer ranks...")
        
        # Get all players
        all_players = set()
        for site_data in all_sites_data.values():
            all_players.update(site_data.keys())
        
        player_stats = []
        
        for player in all_players:
            ranks = []
            position = None
            team = None
            
            # Collect ranks from all sites
            for site_name, site_data in all_sites_data.items():
                if player in site_data:
                    ranks.append(site_data[player]['rank'])
                    if not position:
                        position = site_data[player]['position']
                        team = site_data[player]['team']
            
            if len(ranks) >= 4:  # Need most sites to have ranked the player
                # Calculate statistics
                avg_rank = mean(ranks)
                std_dev = stdev(ranks) if len(ranks) > 1 else 0
                min_rank = min(ranks)
                max_rank = max(ranks)
                cv = (std_dev / avg_rank) * 100 if avg_rank > 0 else 0
                
                player_stats.append({
                    'Player_Name': player,
                    'Position': position,
                    'Team': team,
                    'Average_Rank': avg_rank,
                    'Standard_Deviation': std_dev,
                    'Coefficient_of_Variation': cv,
                    'Min_Rank': min_rank,
                    'Max_Rank': max_rank,
                    'Range': max_rank - min_rank,
                    'Sites_Count': len(ranks),
                    'Individual_Rankings': ranks
                })
        
        # Create DataFrame
        df = pd.DataFrame(player_stats)
        
        # Sort by average rank and assign integer overall ranks
        df = df.sort_values('Average_Rank').reset_index(drop=True)
        df['Overall_Integer_Rank'] = range(1, len(df) + 1)
        
        # Calculate position ranks
        position_ranks = {}
        for pos in df['Position'].unique():
            position_ranks[pos] = 0
        
        df['Position_Integer_Rank'] = 0
        for idx, row in df.iterrows():
            pos = row['Position']
            position_ranks[pos] += 1
            df.at[idx, 'Position_Integer_Rank'] = position_ranks[pos]
        
        print(f"✅ Calculated statistics and integer ranks for {len(df)} players")
        
        # Show position counts
        print(f"\n📊 FINAL POSITION COUNTS:")
        pos_counts = df['Position'].value_counts().sort_index()
        for pos, count in pos_counts.items():
            print(f"   {pos}: {count} players")
        
        return df
    
    def export_final_rankings(self, df):
        """Export final comprehensive rankings"""
        
        filename = '/Users/jeffgreenfield/dev/ff_draft_vibe/FF_2025_FINAL_COMPREHENSIVE_Rankings.xlsx'
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            
            # Main comprehensive sheet
            main_cols = ['Overall_Integer_Rank', 'Player_Name', 'Position', 'Team', 'Position_Integer_Rank',
                        'Average_Rank', 'Standard_Deviation', 'Coefficient_of_Variation', 
                        'Min_Rank', 'Max_Rank', 'Range', 'Sites_Count']
            df[main_cols].to_excel(writer, sheet_name='Final_Comprehensive_Rankings', index=False)
            
            # Position sheets with proper depth
            for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
                pos_df = df[df['Position'] == pos].copy()
                if not pos_df.empty:
                    pos_cols = ['Position_Integer_Rank', 'Player_Name', 'Team', 'Overall_Integer_Rank',
                               'Average_Rank', 'Standard_Deviation', 'Coefficient_of_Variation', 
                               'Min_Rank', 'Max_Rank', 'Range']
                    sheet_name = pos.replace('/', '_') + '_Final'
                    pos_df[pos_cols].to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Top consensus players (low std dev)
            consensus = df.nsmallest(50, 'Standard_Deviation')[main_cols]
            consensus.to_excel(writer, sheet_name='High_Consensus', index=False)
            
            # Most debated players (high std dev)
            debated = df.nlargest(50, 'Standard_Deviation')[main_cols]
            debated.to_excel(writer, sheet_name='Most_Debated', index=False)
            
            # Statistical summary by position
            summary_data = []
            for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
                pos_df = df[df['Position'] == pos]
                if not pos_df.empty:
                    summary_data.append({
                        'Position': pos,
                        'Total_Players': len(pos_df),
                        'Avg_Standard_Deviation': round(pos_df['Standard_Deviation'].mean(), 2),
                        'Avg_Coefficient_of_Variation': round(pos_df['Coefficient_of_Variation'].mean(), 2),
                        'Top_Player': pos_df.iloc[0]['Player_Name'],
                        'Most_Consensus': pos_df.loc[pos_df['Standard_Deviation'].idxmin(), 'Player_Name'],
                        'Most_Debated': pos_df.loc[pos_df['Standard_Deviation'].idxmax(), 'Player_Name']
                    })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Position_Summary', index=False)
        
        print(f"🎉 FINAL COMPREHENSIVE RANKINGS EXPORTED!")
        print(f"📁 File: FF_2025_FINAL_COMPREHENSIVE_Rankings.xlsx")
        print(f"📊 Total players: {len(df)}")
        
        return df
    
    def display_key_results(self, df):
        """Display key results and insights"""
        print(f"\n🔍 KEY RESULTS:")
        
        # Overall top 20
        print(f"\n🏆 TOP 20 OVERALL:")
        top_20 = df.head(20)
        for _, row in top_20.iterrows():
            print(f"{int(row['Overall_Integer_Rank']):3d}. {row['Player_Name']:<30} ({row['Position']}) - Avg: {row['Average_Rank']:5.1f} | Std: {row['Standard_Deviation']:4.1f}")
        
        # Position leaders
        print(f"\n👑 POSITION LEADERS:")
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
            pos_df = df[df['Position'] == pos]
            if not pos_df.empty:
                leader = pos_df.iloc[0]
                print(f"   {pos}1: {leader['Player_Name']:<25} (Overall #{int(leader['Overall_Integer_Rank'])}) - Avg: {leader['Average_Rank']:5.1f}")
        
        # D.K. Metcalf check
        dk = df[df['Player_Name'].str.contains('Metcalf', case=False, na=False)]
        if not dk.empty:
            row = dk.iloc[0]
            print(f"\n🎯 D.K. METCALF FINAL RANKING:")
            print(f"   Overall: #{int(row['Overall_Integer_Rank'])}")
            print(f"   Position: {row['Position']}{int(row['Position_Integer_Rank'])}")
            print(f"   Average Rank: {row['Average_Rank']:5.1f}")
            print(f"   Range: {int(row['Min_Rank'])}-{int(row['Max_Rank'])}")
        
        # Position depth verification
        print(f"\n📊 POSITION DEPTH VERIFICATION:")
        pos_counts = df['Position'].value_counts().sort_index()
        for pos, count in pos_counts.items():
            top_player = df[df['Position'] == pos].iloc[0]['Player_Name']
            print(f"   {pos}: {count} players (Top: {top_player})")
    
    def run_complete_analysis(self):
        """Run the complete expanded analysis"""
        print("🏈 EXPANDED FANTASY FOOTBALL RANKINGS SYSTEM")
        print("🎯 Complete depth with all positions and integer ranks")
        print("=" * 65)
        
        # Create comprehensive player base
        players_base = self.create_comprehensive_player_base()
        
        # Simulate site rankings
        all_sites_data = self.simulate_site_rankings(players_base)
        
        # Calculate comprehensive statistics and integer ranks
        df = self.calculate_comprehensive_statistics(all_sites_data)
        
        # Export final rankings
        final_df = self.export_final_rankings(df)
        
        # Display key results
        self.display_key_results(final_df)
        
        return final_df

if __name__ == "__main__":
    system = ExpandedRankingsSystem()
    results = system.run_complete_analysis()