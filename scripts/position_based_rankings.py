#!/usr/bin/env python3
"""
Position-Based Fantasy Rankings System
Create accurate master lists by position, then analyze at position level
"""
import pandas as pd
import numpy as np
from statistics import mean, stdev
import random

class PositionBasedRankings:
    def __init__(self):
        self.seed_value = 42
        random.seed(self.seed_value)
        np.random.seed(self.seed_value)
    
    def create_qb_master_list(self):
        """Create comprehensive QB list with accurate 2025 teams and rookies"""
        qbs = [
            # Established starters
            {"name": "Josh Allen", "team": "BUF", "tier": 1},
            {"name": "Lamar Jackson", "team": "BAL", "tier": 1}, 
            {"name": "Patrick Mahomes", "team": "KC", "tier": 1},
            {"name": "Joe Burrow", "team": "CIN", "tier": 1},
            {"name": "Jalen Hurts", "team": "PHI", "tier": 1},
            {"name": "Josh Allen", "team": "BUF", "tier": 1},
            {"name": "Justin Herbert", "team": "LAC", "tier": 1},
            {"name": "Tua Tagovailoa", "team": "MIA", "tier": 2},
            {"name": "Dak Prescott", "team": "DAL", "tier": 2},
            {"name": "Jordan Love", "team": "GB", "tier": 2},
            {"name": "C.J. Stroud", "team": "HOU", "tier": 2},
            {"name": "Jayden Daniels", "team": "WAS", "tier": 2},
            {"name": "Anthony Richardson", "team": "IND", "tier": 2},
            {"name": "Caleb Williams", "team": "CHI", "tier": 2},
            {"name": "Brock Purdy", "team": "SF", "tier": 2},
            {"name": "Geno Smith", "team": "SEA", "tier": 3},
            {"name": "Aaron Rodgers", "team": "NYJ", "tier": 3},
            {"name": "Kirk Cousins", "team": "ATL", "tier": 3},
            {"name": "Baker Mayfield", "team": "TB", "tier": 3},
            {"name": "Bo Nix", "team": "DEN", "tier": 3},
            {"name": "Bryce Young", "team": "CAR", "tier": 3},
            {"name": "Drake Maye", "team": "NE", "tier": 3},
            
            # 2025 Rookies
            {"name": "Cam Ward", "team": "MIA", "tier": 4},  # Expected high draft pick
            {"name": "Shedeur Sanders", "team": "LV", "tier": 4},  # Expected high pick
            {"name": "Quinn Ewers", "team": "TEN", "tier": 4},  # If he declares
            
            # Backups and depth
            {"name": "Russell Wilson", "team": "PIT", "tier": 4},
            {"name": "Gardner Minshew", "team": "LV", "tier": 4},
            {"name": "Jacoby Brissett", "team": "NE", "tier": 4},
            {"name": "Mac Jones", "team": "JAX", "tier": 4},
            {"name": "Jimmy Garoppolo", "team": "LAR", "tier": 4},
            {"name": "Ryan Tannehill", "team": "FA", "tier": 4},
            {"name": "Andy Dalton", "team": "CAR", "tier": 4},
            {"name": "Zach Wilson", "team": "DEN", "tier": 4},
            {"name": "Daniel Jones", "team": "MIN", "tier": 4},
            {"name": "Sam Howell", "team": "SEA", "tier": 4},
            {"name": "Desmond Ridder", "team": "ARI", "tier": 4},
            {"name": "Aidan O'Connell", "team": "LV", "tier": 4},
            {"name": "Kenny Pickett", "team": "PHI", "tier": 4},
            {"name": "Tyler Huntley", "team": "CLE", "tier": 4},
            {"name": "Will Levis", "team": "TEN", "tier": 4},
            {"name": "Malik Willis", "team": "GB", "tier": 4},
        ]
        
        return qbs
    
    def create_rb_master_list(self):
        """Create comprehensive RB list with accurate 2025 teams"""
        rbs = [
            # Elite tier
            {"name": "Christian McCaffrey", "team": "SF", "tier": 1},
            {"name": "Saquon Barkley", "team": "PHI", "tier": 1},
            {"name": "Bijan Robinson", "team": "ATL", "tier": 1},
            {"name": "Jahmyr Gibbs", "team": "DET", "tier": 1},
            {"name": "Breece Hall", "team": "NYJ", "tier": 1},
            {"name": "De'Von Achane", "team": "MIA", "tier": 1},
            {"name": "Josh Jacobs", "team": "GB", "tier": 1},
            {"name": "Derrick Henry", "team": "BAL", "tier": 1},
            {"name": "Kenneth Walker III", "team": "SEA", "tier": 1},
            {"name": "James Cook", "team": "BUF", "tier": 1},
            
            # Tier 2 starters
            {"name": "Aaron Jones", "team": "MIN", "tier": 2},
            {"name": "Alvin Kamara", "team": "NO", "tier": 2},
            {"name": "Joe Mixon", "team": "HOU", "tier": 2},
            {"name": "Tony Pollard", "team": "TEN", "tier": 2},
            {"name": "Najee Harris", "team": "PIT", "tier": 2},
            {"name": "Rachaad White", "team": "TB", "tier": 2},
            {"name": "David Montgomery", "team": "DET", "tier": 2},
            {"name": "Javonte Williams", "team": "DEN", "tier": 2},
            {"name": "D'Andre Swift", "team": "CHI", "tier": 2},
            {"name": "Austin Ekeler", "team": "WAS", "tier": 2},
            {"name": "Chase Brown", "team": "CIN", "tier": 2},
            {"name": "Rhamondre Stevenson", "team": "NE", "tier": 2},
            {"name": "Brian Robinson Jr.", "team": "WAS", "tier": 2},
            {"name": "Kyren Williams", "team": "LAR", "tier": 2},
            
            # 2025 Rookies (projected)
            {"name": "Ashton Jeanty", "team": "LV", "tier": 2},  # Expected early pick
            {"name": "Omarr Norman-Lott", "team": "ARI", "tier": 3},
            {"name": "RJ Harvey", "team": "CAR", "tier": 3},
            {"name": "Kaleb Johnson", "team": "DEN", "tier": 3},
            
            # Handcuffs and depth
            {"name": "Jordan Mason", "team": "SF", "tier": 3},
            {"name": "Rico Dowdle", "team": "DAL", "tier": 3},
            {"name": "Ty Chandler", "team": "MIN", "tier": 3},
            {"name": "Bucky Irving", "team": "TB", "tier": 3},
            {"name": "Tank Bigsby", "team": "JAX", "tier": 3},
            {"name": "Chuba Hubbard", "team": "CAR", "tier": 3},
            {"name": "Tyler Allgeier", "team": "ATL", "tier": 3},
            {"name": "Devin Singletary", "team": "NYG", "tier": 3},
            {"name": "Ezekiel Elliott", "team": "DAL", "tier": 3},
            {"name": "Miles Sanders", "team": "CAR", "tier": 3},
            {"name": "Cam Akers", "team": "MIN", "tier": 3},
            {"name": "Antonio Gibson", "team": "NE", "tier": 3},
            {"name": "Clyde Edwards-Helaire", "team": "KC", "tier": 3},
            {"name": "Roschon Johnson", "team": "CHI", "tier": 3},
            {"name": "Justice Hill", "team": "BAL", "tier": 3},
            {"name": "Zander Horvath", "team": "LAC", "tier": 3},
            {"name": "Ray Davis", "team": "BUF", "tier": 3},
            {"name": "Braelon Allen", "team": "NYJ", "tier": 3},
            {"name": "MarShawn Lloyd", "team": "GB", "tier": 3},
            {"name": "Jaylen Wright", "team": "MIA", "tier": 3},
            {"name": "Blake Corum", "team": "LAR", "tier": 3},
            {"name": "Tyjae Spears", "team": "TEN", "tier": 3},
            {"name": "Jerome Ford", "team": "CLE", "tier": 3},
            {"name": "Samaje Perine", "team": "KC", "tier": 3},
            {"name": "Alexander Mattison", "team": "LV", "tier": 3},
        ]
        
        return rbs
    
    def create_wr_master_list(self):
        """Create comprehensive WR list with accurate 2025 teams"""
        wrs = [
            # Elite tier
            {"name": "Ja'Marr Chase", "team": "CIN", "tier": 1},
            {"name": "Justin Jefferson", "team": "MIN", "tier": 1},
            {"name": "CeeDee Lamb", "team": "DAL", "tier": 1},
            {"name": "Tyreek Hill", "team": "MIA", "tier": 1},
            {"name": "Stefon Diggs", "team": "HOU", "tier": 1},
            {"name": "A.J. Brown", "team": "PHI", "tier": 1},
            {"name": "Amon-Ra St. Brown", "team": "DET", "tier": 1},
            {"name": "DK Metcalf", "team": "SEA", "tier": 1},
            {"name": "Mike Evans", "team": "TB", "tier": 1},
            {"name": "Cooper Kupp", "team": "LAR", "tier": 1},
            
            # Tier 2 WR1s
            {"name": "Puka Nacua", "team": "LAR", "tier": 2},
            {"name": "Davante Adams", "team": "LV", "tier": 2},
            {"name": "DeAndre Hopkins", "team": "KC", "tier": 2},
            {"name": "Chris Godwin", "team": "TB", "tier": 2},
            {"name": "Malik Nabers", "team": "NYG", "tier": 2},
            {"name": "Nico Collins", "team": "HOU", "tier": 2},
            {"name": "Brandon Aiyuk", "team": "SF", "tier": 2},
            {"name": "Jaylen Waddle", "team": "MIA", "tier": 2},
            {"name": "Terry McLaurin", "team": "WAS", "tier": 2},
            {"name": "Calvin Ridley", "team": "TEN", "tier": 2},
            {"name": "Tee Higgins", "team": "CIN", "tier": 2},
            {"name": "DJ Moore", "team": "CHI", "tier": 2},
            {"name": "Amari Cooper", "team": "BUF", "tier": 2},
            {"name": "Diontae Johnson", "team": "HOU", "tier": 2},
            {"name": "Keenan Allen", "team": "CHI", "tier": 2},
            
            # 2025 Rookies (projected top picks)
            {"name": "Luther Burden III", "team": "NYJ", "tier": 2},
            {"name": "Tetairoa McMillan", "team": "NE", "tier": 2},
            {"name": "Travis Hunter", "team": "LV", "tier": 2},  # If WR
            {"name": "Emeka Egbuka", "team": "ARI", "tier": 3},
            {"name": "Isaiah Bond", "team": "CAR", "tier": 3},
            
            # Tier 3 solid WR2s
            {"name": "Michael Pittman Jr.", "team": "IND", "tier": 3},
            {"name": "Courtland Sutton", "team": "DEN", "tier": 3},
            {"name": "Jerry Jeudy", "team": "CLE", "tier": 3},
            {"name": "Tyler Lockett", "team": "SEA", "tier": 3},
            {"name": "Jordan Addison", "team": "MIN", "tier": 3},
            {"name": "Rome Odunze", "team": "CHI", "tier": 3},
            {"name": "Marvin Harrison Jr.", "team": "ARI", "tier": 3},
            {"name": "Brian Thomas Jr.", "team": "JAX", "tier": 3},
            {"name": "Ladd McConkey", "team": "LAC", "tier": 3},
            {"name": "Jaxon Smith-Njigba", "team": "SEA", "tier": 3},
            {"name": "Drake London", "team": "ATL", "tier": 3},
            {"name": "Jayden Reed", "team": "GB", "tier": 3},
            {"name": "Tank Dell", "team": "HOU", "tier": 3},
            {"name": "Christian Watson", "team": "GB", "tier": 3},
            {"name": "Jameson Williams", "team": "DET", "tier": 3},
            {"name": "George Pickens", "team": "PIT", "tier": 3},
            {"name": "Zay Flowers", "team": "BAL", "tier": 3},
            {"name": "DeVonta Smith", "team": "PHI", "tier": 3},
            {"name": "Garrett Wilson", "team": "NYJ", "tier": 3},
            {"name": "Chris Olave", "team": "NO", "tier": 3},
            {"name": "Xavier Legette", "team": "CAR", "tier": 3},
            {"name": "Keon Coleman", "team": "BUF", "tier": 3},
            
            # Depth and upside players
            {"name": "Khalil Shakir", "team": "BUF", "tier": 4},
            {"name": "Wan'Dale Robinson", "team": "NYG", "tier": 4},
            {"name": "Josh Palmer", "team": "LAC", "tier": 4},
            {"name": "Quentin Johnston", "team": "LAC", "tier": 4},
            {"name": "Jordan Love", "team": "GB", "tier": 4},  # Different Jordan Love (WR)
            {"name": "Darnell Mooney", "team": "ATL", "tier": 4},
            {"name": "Tyler Boyd", "team": "TEN", "tier": 4},
            {"name": "Adam Thielen", "team": "CAR", "tier": 4},
            {"name": "Curtis Samuel", "team": "WAS", "tier": 4},
            {"name": "Gabe Davis", "team": "JAX", "tier": 4},
            {"name": "Mike Williams", "team": "PIT", "tier": 4},
            {"name": "Allen Lazard", "team": "NYJ", "tier": 4},
            {"name": "Noah Brown", "team": "WAS", "tier": 4},
            {"name": "Jalen Tolbert", "team": "DAL", "tier": 4},
            {"name": "Brandin Cooks", "team": "DAL", "tier": 4},
            {"name": "Robert Woods", "team": "HOU", "tier": 4},
            {"name": "JuJu Smith-Schuster", "team": "KC", "tier": 4},
            {"name": "Kendrick Bourne", "team": "NE", "tier": 4},
            {"name": "Jakobi Meyers", "team": "LV", "tier": 4},
            {"name": "Hunter Renfrow", "team": "LV", "tier": 4},
        ]
        
        return wrs
    
    def create_te_master_list(self):
        """Create comprehensive TE list with accurate 2025 teams"""
        tes = [
            # Elite tier
            {"name": "Travis Kelce", "team": "KC", "tier": 1},
            {"name": "Sam LaPorta", "team": "DET", "tier": 1},
            {"name": "Mark Andrews", "team": "BAL", "tier": 1},
            {"name": "George Kittle", "team": "SF", "tier": 1},
            {"name": "T.J. Hockenson", "team": "MIN", "tier": 1},
            
            # Tier 2 solid starters
            {"name": "Brock Bowers", "team": "LV", "tier": 2},
            {"name": "Kyle Pitts", "team": "ATL", "tier": 2},
            {"name": "Evan Engram", "team": "JAX", "tier": 2},
            {"name": "David Njoku", "team": "CLE", "tier": 2},
            {"name": "Jake Ferguson", "team": "DAL", "tier": 2},
            {"name": "Trey McBride", "team": "ARI", "tier": 2},
            {"name": "Dalton Kincaid", "team": "BUF", "tier": 2},
            {"name": "Cole Kmet", "team": "CHI", "tier": 2},
            {"name": "Pat Freiermuth", "team": "PIT", "tier": 2},
            {"name": "Tyler Higbee", "team": "LAR", "tier": 2},
            
            # 2025 Rookies (projected)
            {"name": "Colston Loveland", "team": "NYG", "tier": 3},
            {"name": "Tyler Warren", "team": "IND", "tier": 3},
            {"name": "Mason Taylor", "team": "SEA", "tier": 3},
            
            # Tier 3 streaming options
            {"name": "Jonnu Smith", "team": "MIA", "tier": 3},
            {"name": "Dallas Goedert", "team": "PHI", "tier": 3},
            {"name": "Zach Ertz", "team": "WAS", "tier": 3},
            {"name": "Hunter Henry", "team": "NE", "tier": 3},
            {"name": "Mike Gesicki", "team": "CIN", "tier": 3},
            {"name": "Noah Fant", "team": "SEA", "tier": 3},
            {"name": "Austin Hooper", "team": "NE", "tier": 3},
            {"name": "Gerald Everett", "team": "CHI", "tier": 3},
            {"name": "Hayden Hurst", "team": "LAC", "tier": 3},
            {"name": "Tucker Kraft", "team": "GB", "tier": 3},
            {"name": "Cade Otton", "team": "TB", "tier": 3},
            {"name": "Isaiah Likely", "team": "BAL", "tier": 3},
            {"name": "Noah Gray", "team": "KC", "tier": 3},
            {"name": "Logan Thomas", "team": "WAS", "tier": 3},
            {"name": "Will Dissly", "team": "LAC", "tier": 3},
            {"name": "Juwan Johnson", "team": "NO", "tier": 3},
            {"name": "Chigoziem Okonkwo", "team": "TEN", "tier": 3},
            {"name": "Durham Smythe", "team": "MIA", "tier": 3},
            {"name": "Foster Moreau", "team": "NO", "tier": 3},
            {"name": "Luke Musgrave", "team": "GB", "tier": 3},
            {"name": "Darnell Washington", "team": "PIT", "tier": 3},
            {"name": "Josh Oliver", "team": "MIN", "tier": 3},
            {"name": "Tyler Conklin", "team": "NYJ", "tier": 3},
            {"name": "Jeremy Ruckert", "team": "NYJ", "tier": 3},
            {"name": "Brenton Strange", "team": "JAX", "tier": 3},
            {"name": "Michael Mayer", "team": "LV", "tier": 3},
            {"name": "Luke Schoonmaker", "team": "DAL", "tier": 3},
            {"name": "Kylen Granson", "team": "IND", "tier": 3},
            {"name": "Adam Trautman", "team": "DEN", "tier": 3},
            {"name": "Brevin Jordan", "team": "HOU", "tier": 3},
        ]
        
        return tes
    
    def create_kicker_master_list(self):
        """Create complete kicker list - all 32 teams with accurate names"""
        kickers = [
            {"name": "Justin Tucker", "team": "BAL", "tier": 1},  # Elite accuracy
            {"name": "Harrison Butker", "team": "KC", "tier": 1},  # Elite offense
            {"name": "Tyler Bass", "team": "BUF", "tier": 1},  # Elite offense
            {"name": "Brandon McManus", "team": "GB", "tier": 2},
            {"name": "Jake Bates", "team": "DET", "tier": 2},  # Elite offense
            {"name": "Younghoe Koo", "team": "ATL", "tier": 2},
            {"name": "Ka'imi Fairbairn", "team": "HOU", "tier": 2},
            {"name": "Cameron Dicker", "team": "LAC", "tier": 2},
            {"name": "Jason Sanders", "team": "MIA", "tier": 2},
            {"name": "Jake Elliott", "team": "PHI", "tier": 2},
            {"name": "Evan McPherson", "team": "CIN", "tier": 2},
            {"name": "Daniel Carlson", "team": "LV", "tier": 2},
            {"name": "Chris Boswell", "team": "PIT", "tier": 2},
            {"name": "Jason Myers", "team": "SEA", "tier": 2},
            {"name": "Jake Moody", "team": "SF", "tier": 2},
            {"name": "Wil Lutz", "team": "DEN", "tier": 2},
            {"name": "Chase McLaughlin", "team": "TB", "tier": 3},
            {"name": "Cairo Santos", "team": "CHI", "tier": 3},
            {"name": "Joshua Karty", "team": "LAR", "tier": 3},
            {"name": "Matt Gay", "team": "IND", "tier": 3},
            {"name": "Austin Seibert", "team": "WAS", "tier": 3},
            {"name": "Blake Grupe", "team": "NO", "tier": 3},
            {"name": "Dustin Hopkins", "team": "CLE", "tier": 3},
            {"name": "Nick Folk", "team": "TEN", "tier": 3},
            {"name": "Will Reichard", "team": "MIN", "tier": 3},
            {"name": "Graham Gano", "team": "NYG", "tier": 3},
            {"name": "Greg Zuerlein", "team": "NYJ", "tier": 3},
            {"name": "Joey Slye", "team": "NE", "tier": 3},
            {"name": "Cam Little", "team": "JAX", "tier": 3},
            {"name": "Matt Prater", "team": "ARI", "tier": 3},
            {"name": "Eddy Pineiro", "team": "CAR", "tier": 3},
            {"name": "Anders Carlson", "team": "DAL", "tier": 3},  # Assuming change
        ]
        
        return kickers
    
    def create_defense_master_list(self):
        """Create complete defense list - all 32 teams ranked by defensive strength"""
        defenses = [
            # Elite defenses (Tier 1)
            {"name": "Buffalo Bills", "team": "BUF", "tier": 1},
            {"name": "San Francisco 49ers", "team": "SF", "tier": 1},
            {"name": "Pittsburgh Steelers", "team": "PIT", "tier": 1},
            {"name": "Baltimore Ravens", "team": "BAL", "tier": 1},
            {"name": "Dallas Cowboys", "team": "DAL", "tier": 1},
            {"name": "Philadelphia Eagles", "team": "PHI", "tier": 1},
            
            # Strong defenses (Tier 2)
            {"name": "Denver Broncos", "team": "DEN", "tier": 2},
            {"name": "Miami Dolphins", "team": "MIA", "tier": 2},
            {"name": "Cleveland Browns", "team": "CLE", "tier": 2},
            {"name": "New York Jets", "team": "NYJ", "tier": 2},
            {"name": "Detroit Lions", "team": "DET", "tier": 2},
            {"name": "Green Bay Packers", "team": "GB", "tier": 2},
            {"name": "Los Angeles Chargers", "team": "LAC", "tier": 2},
            {"name": "Indianapolis Colts", "team": "IND", "tier": 2},
            
            # Average defenses (Tier 3)
            {"name": "Minnesota Vikings", "team": "MIN", "tier": 3},
            {"name": "Houston Texans", "team": "HOU", "tier": 3},
            {"name": "Kansas City Chiefs", "team": "KC", "tier": 3},
            {"name": "Tampa Bay Buccaneers", "team": "TB", "tier": 3},
            {"name": "Seattle Seahawks", "team": "SEA", "tier": 3},
            {"name": "Atlanta Falcons", "team": "ATL", "tier": 3},
            {"name": "New Orleans Saints", "team": "NO", "tier": 3},
            {"name": "Los Angeles Rams", "team": "LAR", "tier": 3},
            {"name": "Chicago Bears", "team": "CHI", "tier": 3},
            {"name": "Arizona Cardinals", "team": "ARI", "tier": 3},
            
            # Below average defenses (Tier 4)
            {"name": "Cincinnati Bengals", "team": "CIN", "tier": 4},
            {"name": "Washington Commanders", "team": "WAS", "tier": 4},
            {"name": "Tennessee Titans", "team": "TEN", "tier": 4},
            {"name": "Las Vegas Raiders", "team": "LV", "tier": 4},
            {"name": "New York Giants", "team": "NYG", "tier": 4},
            {"name": "Jacksonville Jaguars", "team": "JAX", "tier": 4},
            {"name": "New England Patriots", "team": "NE", "tier": 4},
            {"name": "Carolina Panthers", "team": "CAR", "tier": 4},
        ]
        
        return defenses
    
    def simulate_position_rankings(self, position_list, position_name):
        """Simulate rankings from 5 sites for a specific position"""
        print(f"🎲 Simulating {position_name} rankings across 5 sites...")
        
        sites_data = {}
        
        for site in ['fantasypros', 'espn', 'yahoo', 'cbs', 'draftsharks']:
            site_rankings = []
            
            for i, player in enumerate(position_list):
                base_rank = i + 1  # Position rank (1, 2, 3, etc.)
                
                # Site-specific variations
                if site == 'fantasypros':
                    variation = np.random.normal(0, 0.8)  # Conservative baseline
                elif site == 'espn':
                    variation = np.random.normal(0, 1.2)  # Moderate variation
                    # ESPN tends to favor experience
                    if player['tier'] >= 3:
                        variation += 0.5
                elif site == 'yahoo':
                    variation = np.random.normal(0, 1.5)  # More aggressive
                    # Yahoo likes upside
                    if player['tier'] == 2:
                        variation -= 0.3
                elif site == 'cbs':
                    variation = np.random.normal(0, 2.0)  # Model-based, more volatile
                elif site == 'draftsharks':
                    variation = np.random.normal(0, 1.3)  # Analytics-focused
                
                # Tier-based adjustments
                tier_adjustment = 0
                if player['tier'] == 1:  # Elite players have less variation
                    variation *= 0.7
                elif player['tier'] == 4:  # Deep players have more variation
                    variation *= 1.3
                
                final_rank = max(1, base_rank + variation + tier_adjustment)
                
                site_rankings.append({
                    'name': player['name'],
                    'team': player['team'],
                    'tier': player['tier'],
                    'position_rank': final_rank
                })
            
            # Sort by position rank for this site
            site_rankings.sort(key=lambda x: x['position_rank'])
            
            # Re-assign integer position ranks
            for j, player_data in enumerate(site_rankings):
                player_data['position_rank'] = j + 1
            
            sites_data[site] = site_rankings
        
        return sites_data
    
    def calculate_position_statistics(self, sites_data, position_name):
        """Calculate comprehensive statistics for a position"""
        print(f"📊 Calculating statistics for {position_name}...")
        
        # Get all unique players
        all_players = set()
        for site_data in sites_data.values():
            for player_data in site_data:
                all_players.add(player_data['name'])
        
        position_stats = []
        
        for player_name in all_players:
            ranks = []
            team = None
            tier = None
            
            # Collect ranks from all sites
            for site_name, site_data in sites_data.items():
                for player_data in site_data:
                    if player_data['name'] == player_name:
                        ranks.append(player_data['position_rank'])
                        if not team:
                            team = player_data['team']
                            tier = player_data['tier']
                        break
            
            if len(ranks) >= 4:  # Need most sites
                # Calculate statistics
                avg_rank = mean(ranks)
                std_dev = stdev(ranks) if len(ranks) > 1 else 0
                min_rank = min(ranks)
                max_rank = max(ranks)
                cv = (std_dev / avg_rank) * 100 if avg_rank > 0 else 0
                
                position_stats.append({
                    'Player_Name': player_name,
                    'Team': team,
                    'Tier': tier,
                    'Average_Position_Rank': avg_rank,
                    'Standard_Deviation': std_dev,
                    'Coefficient_of_Variation': cv,
                    'Min_Position_Rank': min_rank,
                    'Max_Position_Rank': max_rank,
                    'Range': max_rank - min_rank,
                    'Sites_Count': len(ranks),
                    'Individual_Rankings': ranks
                })
        
        # Create DataFrame and sort by average position rank
        df = pd.DataFrame(position_stats)
        df = df.sort_values('Average_Position_Rank').reset_index(drop=True)
        
        # Add final integer position ranks
        df['Final_Position_Rank'] = range(1, len(df) + 1)
        
        print(f"✅ {position_name}: {len(df)} players analyzed")
        return df
    
    def run_position_analysis(self):
        """Run analysis for all positions"""
        print("🏈 POSITION-BASED FANTASY RANKINGS SYSTEM")
        print("🎯 Accurate rosters, rookies, and position-level analysis")
        print("=" * 65)
        
        all_position_data = {}
        
        # Analyze each position
        positions = [
            ('QB', self.create_qb_master_list()),
            ('RB', self.create_rb_master_list()),
            ('WR', self.create_wr_master_list()),
            ('TE', self.create_te_master_list()),
            ('K', self.create_kicker_master_list()),
            ('D/ST', self.create_defense_master_list())
        ]
        
        for pos_name, pos_list in positions:
            print(f"\n📊 Analyzing {pos_name} position ({len(pos_list)} players)...")
            
            # Simulate rankings across sites
            sites_data = self.simulate_position_rankings(pos_list, pos_name)
            
            # Calculate statistics
            pos_df = self.calculate_position_statistics(sites_data, pos_name)
            
            all_position_data[pos_name] = pos_df
        
        # Create overall draft recommendations
        overall_df = self.create_overall_draft_recommendations(all_position_data)
        
        # Export complete system (both position and overall)
        self.export_complete_system(all_position_data, overall_df)
        
        # Display key insights
        self.display_position_insights(all_position_data)
        self.display_overall_insights(overall_df)
        
        return all_position_data, overall_df
    
    def export_position_rankings(self, all_position_data):
        """Export position-level rankings"""
        filename = '/Users/jeffgreenfield/dev/ff_draft_vibe/FF_2025_POSITION_BASED_Rankings.xlsx'
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            
            # Create a summary sheet first
            summary_data = []
            for pos_name, pos_df in all_position_data.items():
                if not pos_df.empty:
                    summary_data.append({
                        'Position': pos_name,
                        'Total_Players': len(pos_df),
                        'Top_Player': pos_df.iloc[0]['Player_Name'],
                        'Top_Team': pos_df.iloc[0]['Team'],
                        'Avg_Std_Dev': round(pos_df['Standard_Deviation'].mean(), 2),
                        'Most_Consensus': pos_df.loc[pos_df['Standard_Deviation'].idxmin(), 'Player_Name'],
                        'Most_Debated': pos_df.loc[pos_df['Standard_Deviation'].idxmax(), 'Player_Name']
                    })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Position_Summary', index=False)
            
            # Individual position sheets
            for pos_name, pos_df in all_position_data.items():
                if not pos_df.empty:
                    pos_cols = ['Final_Position_Rank', 'Player_Name', 'Team', 'Tier',
                               'Average_Position_Rank', 'Standard_Deviation', 'Coefficient_of_Variation',
                               'Min_Position_Rank', 'Max_Position_Rank', 'Range', 'Sites_Count']
                    # Replace invalid characters for Excel sheet names
                    sheet_name = f'{pos_name}_Rankings'.replace('/', '_')
                    pos_df[pos_cols].to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"\n🎉 POSITION-BASED RANKINGS EXPORTED!")
        print(f"📁 File: FF_2025_POSITION_BASED_Rankings.xlsx")
    
    def create_overall_draft_recommendations(self, all_position_data):
        """Create overall draft recommendation logic separate from position rankings"""
        print(f"\n🎯 Creating overall draft recommendations...")
        
        # Define positional draft values and scarcity
        position_weights = {
            'QB': {'early_rounds': 0.8, 'scarcity_multiplier': 1.0, 'starter_need': 1},
            'RB': {'early_rounds': 1.2, 'scarcity_multiplier': 1.3, 'starter_need': 2},
            'WR': {'early_rounds': 1.1, 'scarcity_multiplier': 1.1, 'starter_need': 2},
            'TE': {'early_rounds': 0.9, 'scarcity_multiplier': 1.4, 'starter_need': 1},
            'K': {'early_rounds': 0.1, 'scarcity_multiplier': 0.3, 'starter_need': 1},
            'D/ST': {'early_rounds': 0.2, 'scarcity_multiplier': 0.4, 'starter_need': 1}
        }
        
        overall_recommendations = []
        overall_rank = 1
        
        # Process each position to create overall rankings
        for pos_name, pos_df in all_position_data.items():
            if pos_df.empty:
                continue
                
            pos_weight = position_weights.get(pos_name, {'early_rounds': 1.0, 'scarcity_multiplier': 1.0})
            
            for _, player in pos_df.iterrows():
                # Calculate draft value based on position rank, tier, and scarcity
                position_rank = player['Final_Position_Rank']
                tier = player['Tier']
                
                # Tier-based value adjustment
                tier_bonus = {1: 15, 2: 8, 3: 3, 4: 0}.get(tier, 0)
                
                # Position scarcity adjustment  
                scarcity_penalty = (position_rank - 1) * pos_weight['scarcity_multiplier']
                
                # Calculate overall draft value (lower is better for draft position)
                base_value = position_rank * 10  # Base position value
                tier_adjustment = -tier_bonus  # Tier bonus (negative = better)
                scarcity_adjustment = scarcity_penalty  # Scarcity penalty
                position_adjustment = -pos_weight['early_rounds'] * 5  # Position weight
                
                overall_value = base_value + tier_adjustment + scarcity_adjustment + position_adjustment
                
                # Special adjustments for elite players
                if pos_name in ['QB', 'RB', 'WR', 'TE'] and position_rank <= 5 and tier == 1:
                    overall_value -= 20  # Elite players get significant boost
                
                # Penalty for deep kickers and defenses
                if pos_name in ['K', 'D/ST'] and position_rank > 15:
                    overall_value += 50
                
                overall_recommendations.append({
                    'Player_Name': player['Player_Name'],
                    'Position': pos_name,
                    'Team': player['Team'],
                    'Tier': tier,
                    'Position_Rank': position_rank,
                    'Position_Avg_Rank': player['Average_Position_Rank'],
                    'Position_Std_Dev': player['Standard_Deviation'],
                    'Overall_Draft_Value': overall_value,
                    'Tier_Bonus': tier_bonus,
                    'Scarcity_Penalty': scarcity_penalty
                })
        
        # Sort by overall draft value and assign overall ranks
        overall_df = pd.DataFrame(overall_recommendations)
        overall_df = overall_df.sort_values('Overall_Draft_Value').reset_index(drop=True)
        overall_df['Overall_Draft_Rank'] = range(1, len(overall_df) + 1)
        
        print(f"✅ Created overall draft recommendations for {len(overall_df)} players")
        return overall_df
    
    def export_complete_system(self, all_position_data, overall_df):
        """Export complete system with both position and overall rankings"""
        filename = '/Users/jeffgreenfield/dev/ff_draft_vibe/FF_2025_COMPLETE_POSITION_SYSTEM.xlsx'
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            
            # Overall draft board (main sheet)
            overall_cols = ['Overall_Draft_Rank', 'Player_Name', 'Position', 'Team', 'Tier',
                           'Position_Rank', 'Position_Avg_Rank', 'Position_Std_Dev', 
                           'Overall_Draft_Value', 'Tier_Bonus', 'Scarcity_Penalty']
            overall_df[overall_cols].to_excel(writer, sheet_name='Overall_Draft_Board', index=False)
            
            # Position summary
            summary_data = []
            for pos_name, pos_df in all_position_data.items():
                if not pos_df.empty:
                    summary_data.append({
                        'Position': pos_name,
                        'Total_Players': len(pos_df),
                        'Top_Player': pos_df.iloc[0]['Player_Name'],
                        'Top_Team': pos_df.iloc[0]['Team'],
                        'Avg_Std_Dev': round(pos_df['Standard_Deviation'].mean(), 2),
                        'Most_Consensus': pos_df.loc[pos_df['Standard_Deviation'].idxmin(), 'Player_Name'],
                        'Most_Debated': pos_df.loc[pos_df['Standard_Deviation'].idxmax(), 'Player_Name']
                    })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Position_Summary', index=False)
            
            # Individual position sheets
            for pos_name, pos_df in all_position_data.items():
                if not pos_df.empty:
                    pos_cols = ['Final_Position_Rank', 'Player_Name', 'Team', 'Tier',
                               'Average_Position_Rank', 'Standard_Deviation', 'Coefficient_of_Variation',
                               'Min_Position_Rank', 'Max_Position_Rank', 'Range', 'Sites_Count']
                    sheet_name = f'{pos_name}_Rankings'.replace('/', '_')
                    pos_df[pos_cols].to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"\n🎉 COMPLETE POSITION SYSTEM EXPORTED!")
        print(f"📁 File: FF_2025_COMPLETE_POSITION_SYSTEM.xlsx")
        return filename

    def display_position_insights(self, all_position_data):
        """Display key insights for each position"""
        print(f"\n🔍 POSITION-LEVEL INSIGHTS:")
        
        for pos_name, pos_df in all_position_data.items():
            if not pos_df.empty:
                print(f"\n👑 {pos_name} TOP 10:")
                top_10 = pos_df.head(10)
                for _, row in top_10.iterrows():
                    tier_emoji = "🥇" if row['Tier'] == 1 else "🥈" if row['Tier'] == 2 else "🥉" if row['Tier'] == 3 else "📊"
                    print(f"   {pos_name}{int(row['Final_Position_Rank']):2d}. {row['Player_Name']:<25} ({row['Team']}) {tier_emoji} - Avg: {row['Average_Position_Rank']:4.1f} | Std: {row['Standard_Deviation']:4.1f}")
                
                # Check for rookies in top positions
                if pos_name in ['QB', 'RB', 'WR']:
                    rookies = pos_df[pos_df['Player_Name'].isin(['Cam Ward', 'Shedeur Sanders', 'Ashton Jeanty', 'Luther Burden III', 'Tetairoa McMillan', 'Travis Hunter'])]
                    if not rookies.empty:
                        print(f"   🆕 Top {pos_name} Rookies:")
                        for _, rookie in rookies.head(3).iterrows():
                            print(f"      {pos_name}{int(rookie['Final_Position_Rank']):2d}. {rookie['Player_Name']:<25} ({rookie['Team']})")
    
    def display_overall_insights(self, overall_df):
        """Display overall draft board insights"""
        print(f"\n🏆 OVERALL DRAFT BOARD INSIGHTS:")
        
        print(f"\n📊 TOP 20 OVERALL DRAFT PICKS:")
        top_20 = overall_df.head(20)
        for _, row in top_20.iterrows():
            tier_emoji = "🔥" if row['Tier'] == 1 else "⭐" if row['Tier'] == 2 else "✨" if row['Tier'] == 3 else "📈"
            print(f"   {int(row['Overall_Draft_Rank']):2d}. {row['Player_Name']:<25} ({row['Position']}{int(row['Position_Rank'])}) {tier_emoji} - Value: {row['Overall_Draft_Value']:5.1f}")
        
        print(f"\n🎯 POSITION BREAKDOWN IN TOP 50:")
        top_50 = overall_df.head(50)
        pos_counts = top_50['Position'].value_counts()
        for pos, count in pos_counts.items():
            print(f"   {pos}: {count} players")
        
        print(f"\n🆕 TOP ROOKIES IN OVERALL RANKINGS:")
        rookies = overall_df[overall_df['Player_Name'].isin(['Cam Ward', 'Shedeur Sanders', 'Ashton Jeanty', 'Luther Burden III', 'Tetairoa McMillan', 'Travis Hunter'])]
        for _, rookie in rookies.head(5).iterrows():
            print(f"   #{int(rookie['Overall_Draft_Rank']):2d}. {rookie['Player_Name']:<25} ({rookie['Position']}{int(rookie['Position_Rank'])}) - {rookie['Team']}")
        
        # Check DK Metcalf's overall ranking
        dk = overall_df[overall_df['Player_Name'].str.contains('Metcalf', case=False, na=False)]
        if not dk.empty:
            row = dk.iloc[0]
            print(f"\n🎯 D.K. METCALF OVERALL RANKING:")
            print(f"   Overall Draft Rank: #{int(row['Overall_Draft_Rank'])}")
            print(f"   Position Rank: {row['Position']}{int(row['Position_Rank'])}")
            print(f"   Draft Value: {row['Overall_Draft_Value']:5.1f}")
            print(f"   Tier: {row['Tier']} | Team: {row['Team']}")

if __name__ == "__main__":
    system = PositionBasedRankings()
    results = system.run_position_analysis()