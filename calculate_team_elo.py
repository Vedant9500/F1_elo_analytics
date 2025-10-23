"""
F1 Team Elo Rating System
Calculates team performance ratings based on race results
Uses head-to-head comparisons between all teams in each race
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

class TeamBasedF1Elo:
    def __init__(self, db_path='DB/f1_database.db', initial_rating=1500):
        self.db_path = db_path
        self.initial_rating = initial_rating
        self.team_ratings = {}  # {team_id: {'qualifying_elo': X, 'race_elo': Y, ...}}
        self.team_info = {}     # {team_id: {'name': X, 'first_year': Y, 'last_year': Z}}
        
    def get_k_factor(self, team_id, is_elite=False):
        """
        Dynamic K-factor based on team experience
        - New teams (< 20 races): K=40 (learn quickly)
        - Established teams (20-60 races): K=20 (moderate adjustment)
        - Veteran teams (> 60 races): K=10 (stable ratings)
        - Elite teams (ever > 1650): K=10 (reduced volatility)
        """
        if is_elite:
            return 10
        
        total_races = self.team_ratings[team_id].get('total_races', 0)
        if total_races < 20:
            return 40
        elif total_races < 60:
            return 20
        else:
            return 10
    
    def expected_score(self, rating_a, rating_b):
        """Calculate expected score using standard Elo formula"""
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
    def update_rating(self, current_rating, expected, actual, k_factor):
        """Update Elo rating"""
        return current_rating + k_factor * (actual - expected)
    
    def get_team_race_performance(self, race_id, team_id):
        """
        Get team's race performance score
        Uses average finishing position of both drivers (or single driver if one DNF)
        Lower average = better performance
        Returns: (avg_position, driver_count, dnf_both)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all results for this team in this race
        cursor.execute("""
            SELECT position, status
            FROM Result
            WHERE race_id = ? AND team_id = ?
            ORDER BY position
        """, (race_id, team_id))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return None, 0, True
        
        # Filter out mechanical DNFs (not driver's fault)
        mechanical_keywords = ['engine', 'gearbox', 'transmission', 'hydraulics', 
                              'electrical', 'fuel', 'clutch', 'suspension', 'brakes',
                              'overheating', 'mechanical', 'throttle', 'driveshaft']
        
        valid_positions = []
        for pos, status in results:
            # Include finished positions
            if pos and pos <= 30:
                valid_positions.append(pos)
            # Include driver error DNFs (exclude mechanical)
            elif status and not any(keyword in status.lower() for keyword in mechanical_keywords):
                # Penalize driver errors heavily (count as last place + 5)
                valid_positions.append(35)
        
        if not valid_positions:
            return None, 0, True
        
        avg_position = sum(valid_positions) / len(valid_positions)
        both_dnf = len(valid_positions) == 0
        
        return avg_position, len(valid_positions), both_dnf
    
    def get_team_qualifying_performance(self, race_id, team_id):
        """
        Get team's qualifying performance score
        Uses average grid position of both drivers
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT grid_position
            FROM Result
            WHERE race_id = ? AND team_id = ? AND grid_position IS NOT NULL AND grid_position > 0
            ORDER BY grid_position
        """, (race_id, team_id))
        
        positions = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not positions:
            return None, 0
        
        avg_grid = sum(positions) / len(positions)
        return avg_grid, len(positions)
    
    def process_race_matchups(self, race_id, race_year):
        """
        Process all team head-to-head matchups in a race
        Every team is compared against every other team
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all teams that participated in this race
        cursor.execute("""
            SELECT DISTINCT team_id
            FROM Result
            WHERE race_id = ?
        """, (race_id,))
        
        team_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if len(team_ids) < 2:
            return 0
        
        # Get performance for each team
        team_performances = {}
        for team_id in team_ids:
            avg_pos, driver_count, both_dnf = self.get_team_race_performance(race_id, team_id)
            if avg_pos is not None:
                team_performances[team_id] = avg_pos
        
        if len(team_performances) < 2:
            return 0
        
        matchups = 0
        # Compare each team against all others
        for i, team_a in enumerate(team_performances.keys()):
            for team_b in list(team_performances.keys())[i+1:]:
                pos_a = team_performances[team_a]
                pos_b = team_performances[team_b]
                
                # Determine actual score (1 = win, 0.5 = tie, 0 = loss)
                if pos_a < pos_b:
                    actual_a, actual_b = 1.0, 0.0
                elif pos_a > pos_b:
                    actual_a, actual_b = 0.0, 1.0
                else:
                    actual_a, actual_b = 0.5, 0.5
                
                # Calculate expected scores
                rating_a = self.team_ratings[team_a]['race_elo']
                rating_b = self.team_ratings[team_b]['race_elo']
                
                expected_a = self.expected_score(rating_a, rating_b)
                expected_b = 1 - expected_a
                
                # Check if elite
                is_elite_a = self.team_ratings[team_a]['race_elo'] > 1650
                is_elite_b = self.team_ratings[team_b]['race_elo'] > 1650
                
                # Get K-factors
                k_a = self.get_k_factor(team_a, is_elite_a)
                k_b = self.get_k_factor(team_b, is_elite_b)
                
                # Update ratings
                new_rating_a = self.update_rating(rating_a, expected_a, actual_a, k_a)
                new_rating_b = self.update_rating(rating_b, expected_b, actual_b, k_b)
                
                self.team_ratings[team_a]['race_elo'] = new_rating_a
                self.team_ratings[team_b]['race_elo'] = new_rating_b
                
                # Update race counts
                self.team_ratings[team_a]['race_count'] += 1
                self.team_ratings[team_b]['race_count'] += 1
                
                matchups += 1
        
        return matchups
    
    def process_qualifying_matchups(self, race_id, race_year):
        """
        Process all team head-to-head matchups in qualifying
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT team_id
            FROM Result
            WHERE race_id = ? AND grid_position IS NOT NULL AND grid_position > 0
        """, (race_id,))
        
        team_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if len(team_ids) < 2:
            return 0
        
        # Get qualifying performance for each team
        team_performances = {}
        for team_id in team_ids:
            avg_grid, driver_count = self.get_team_qualifying_performance(race_id, team_id)
            if avg_grid is not None:
                team_performances[team_id] = avg_grid
        
        if len(team_performances) < 2:
            return 0
        
        matchups = 0
        # Compare each team against all others
        for i, team_a in enumerate(team_performances.keys()):
            for team_b in list(team_performances.keys())[i+1:]:
                grid_a = team_performances[team_a]
                grid_b = team_performances[team_b]
                
                # Determine actual score
                if grid_a < grid_b:
                    actual_a, actual_b = 1.0, 0.0
                elif grid_a > grid_b:
                    actual_a, actual_b = 0.0, 1.0
                else:
                    actual_a, actual_b = 0.5, 0.5
                
                # Calculate expected scores
                rating_a = self.team_ratings[team_a]['qualifying_elo']
                rating_b = self.team_ratings[team_b]['qualifying_elo']
                
                expected_a = self.expected_score(rating_a, rating_b)
                expected_b = 1 - expected_a
                
                # Check if elite
                is_elite_a = self.team_ratings[team_a]['qualifying_elo'] > 1650
                is_elite_b = self.team_ratings[team_b]['qualifying_elo'] > 1650
                
                # Get K-factors
                k_a = self.get_k_factor(team_a, is_elite_a)
                k_b = self.get_k_factor(team_b, is_elite_b)
                
                # Update ratings
                new_rating_a = self.update_rating(rating_a, expected_a, actual_a, k_a)
                new_rating_b = self.update_rating(rating_b, expected_b, actual_b, k_b)
                
                self.team_ratings[team_a]['qualifying_elo'] = new_rating_a
                self.team_ratings[team_b]['qualifying_elo'] = new_rating_b
                
                # Update qualifying counts
                self.team_ratings[team_a]['qualifying_count'] += 1
                self.team_ratings[team_b]['qualifying_count'] += 1
                
                matchups += 1
        
        return matchups
    
    def normalize_ratings(self, season):
        """
        Normalize all ratings for a season back to mean of 1500
        Prevents rating inflation/deflation over time
        """
        # Get all teams that raced this season
        active_teams = [tid for tid, info in self.team_ratings.items() 
                       if info.get('last_year') == season]
        
        if len(active_teams) < 2:
            return
        
        # Calculate means
        quali_ratings = [self.team_ratings[tid]['qualifying_elo'] for tid in active_teams]
        race_ratings = [self.team_ratings[tid]['race_elo'] for tid in active_teams]
        
        quali_mean = np.mean(quali_ratings)
        race_mean = np.mean(race_ratings)
        
        # Calculate adjustments
        quali_adj = 1500 - quali_mean
        race_adj = 1500 - race_mean
        
        print(f"  Season {season} normalized: Quali mean {quali_mean:.1f}→1500, Race mean {race_mean:.1f}→1500")
        
        # Apply adjustments to all teams (not just active ones)
        for tid in self.team_ratings:
            self.team_ratings[tid]['qualifying_elo'] += quali_adj
            self.team_ratings[tid]['race_elo'] += race_adj
    
    def calculate_reliability_score(self, total_matchups):
        """
        Calculate reliability score based on sample size
        Uses sigmoid function: reliability = 100 / (1 + e^(-(matchups-100)/50))
        - 200+ matchups: ~95-100% reliability
        - 100 matchups: ~50% reliability
        - <30 matchups: <25% reliability
        """
        return 100 / (1 + np.exp(-(total_matchups - 100) / 50))
    
    def calculate_era_adjustment(self, first_year, total_matchups):
        """
        Adjust ratings based on era and sample size
        Early eras had smaller grids and less competition
        """
        # Era multipliers
        if first_year < 1960:
            era_mult = 0.92
        elif first_year < 1970:
            era_mult = 0.95
        elif first_year < 1980:
            era_mult = 0.97
        elif first_year < 2000:
            era_mult = 0.99
        else:
            era_mult = 1.00
        
        # Small sample penalty
        if total_matchups < 100:
            sample_penalty = 0.95
        else:
            sample_penalty = 1.00
        
        return era_mult * sample_penalty
    
    def calculate_global_elo(self, team_id):
        """
        Calculate global Elo as weighted average
        30% qualifying (one-lap pace) + 70% race (race pace/strategy)
        """
        quali_elo = self.team_ratings[team_id]['qualifying_elo']
        race_elo = self.team_ratings[team_id]['race_elo']
        
        global_elo = 0.3 * quali_elo + 0.7 * race_elo
        return global_elo
    
    def calculate_all_elos(self):
        """Main calculation loop"""
        print("\nInitializing Team-Based F1 Elo Calculator...")
        print("=" * 70)
        print("F1 TEAM ELO RATING SYSTEM")
        print("=" * 70)
        print(f"Initial Rating: {self.initial_rating}")
        print("K-Factors: New=40, Established=20, Veteran=10")
        print("Global Elo Weights: 30% Qualifying, 70% Race")
        print("=" * 70)
        
        # Load all teams and races
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Initialize team ratings
        cursor.execute("SELECT team_id, team_name FROM Team")
        teams = cursor.fetchall()
        
        for team_id, team_name in teams:
            self.team_ratings[team_id] = {
                'name': team_name,
                'qualifying_elo': self.initial_rating,
                'race_elo': self.initial_rating,
                'qualifying_count': 0,
                'race_count': 0,
                'total_races': 0,
                'first_year': None,
                'last_year': None
            }
        
        # Get all races ordered by date
        cursor.execute("""
            SELECT race_id, season_year, round_number, race_name
            FROM Race
            ORDER BY season_year, round_number
        """)
        races = cursor.fetchall()
        conn.close()
        
        total_quali_matchups = 0
        total_race_matchups = 0
        current_season = None
        
        for idx, (race_id, year, round_num, race_name) in enumerate(races, 1):
            # Track team participation years
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT team_id FROM Result WHERE race_id = ?", (race_id,))
            race_teams = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            for team_id in race_teams:
                if self.team_ratings[team_id]['first_year'] is None:
                    self.team_ratings[team_id]['first_year'] = year
                self.team_ratings[team_id]['last_year'] = year
                self.team_ratings[team_id]['total_races'] += 1
            
            # Process qualifying and race matchups
            quali_matchups = self.process_qualifying_matchups(race_id, year)
            race_matchups = self.process_race_matchups(race_id, year)
            
            total_quali_matchups += quali_matchups
            total_race_matchups += race_matchups
            
            # Normalize at end of each season
            if current_season is not None and year != current_season:
                self.normalize_ratings(current_season)
            current_season = year
            
            # Progress indicator
            if idx % 50 == 0:
                print(f"Processed {idx}/{len(races)} races... (Quali: {total_quali_matchups}, Race: {total_race_matchups} matchups)")
        
        # Final season normalization
        if current_season:
            self.normalize_ratings(current_season)
        
        print("=" * 70)
        print("CALCULATION COMPLETE")
        print(f"Total Races Processed: {len(races)}")
        print(f"Total Qualifying Matchups: {total_quali_matchups}")
        print(f"Total Race Matchups: {total_race_matchups}")
        print(f"Teams Rated: {len([t for t in self.team_ratings.values() if t['total_races'] > 0])}")
        print("=" * 70)
    
    def save_to_database(self):
        """Save team ratings to Team_Elo table"""
        print("\nSaving ratings to database...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM Team_Elo")
        
        saved_count = 0
        for team_id, ratings in self.team_ratings.items():
            # Only save teams that have actually raced
            if ratings['total_races'] == 0:
                continue
            
            # Calculate global Elo
            global_elo = self.calculate_global_elo(team_id)
            
            # Calculate total matchups
            total_matchups = ratings['qualifying_count'] + ratings['race_count']
            
            # Calculate reliability score
            reliability_score = self.calculate_reliability_score(total_matchups)
            
            # Calculate era-adjusted Elo
            era_mult = self.calculate_era_adjustment(ratings['first_year'], total_matchups)
            era_adjusted_elo = global_elo * era_mult
            
            cursor.execute("""
                INSERT INTO Team_Elo (
                    team_id, qualifying_elo, race_elo, global_elo, 
                    era_adjusted_elo, total_races, reliability_score,
                    first_race_year, last_race_year
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                team_id,
                round(ratings['qualifying_elo'], 1),
                round(ratings['race_elo'], 1),
                round(global_elo, 1),
                round(era_adjusted_elo, 1),
                ratings['total_races'],
                round(reliability_score, 1),
                ratings['first_year'],
                ratings['last_year']
            ))
            saved_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"✓ Saved {saved_count} team ratings to database")
    
    def display_top_teams(self, limit=20):
        """Display top teams by Elo rating"""
        # Prepare data
        team_data = []
        for team_id, ratings in self.team_ratings.items():
            if ratings['total_races'] == 0:
                continue
            
            global_elo = self.calculate_global_elo(team_id)
            total_matchups = ratings['qualifying_count'] + ratings['race_count']
            reliability = self.calculate_reliability_score(total_matchups)
            
            era_mult = self.calculate_era_adjustment(ratings['first_year'], total_matchups)
            era_adjusted = global_elo * era_mult
            
            team_data.append({
                'team_id': team_id,
                'name': ratings['name'],
                'global_elo': global_elo,
                'qualifying_elo': ratings['qualifying_elo'],
                'race_elo': ratings['race_elo'],
                'era_adjusted_elo': era_adjusted,
                'total_races': ratings['total_races'],
                'total_matchups': total_matchups,
                'reliability': reliability,
                'first_year': ratings['first_year'],
                'last_year': ratings['last_year']
            })
        
        # Sort by raw global Elo
        df_raw = pd.DataFrame(team_data).sort_values('global_elo', ascending=False).head(limit)
        
        print("\n" + "=" * 80)
        print(f"TOP {limit} TEAMS BY GLOBAL ELO (Raw - Not Era Adjusted)")
        print("=" * 80)
        print(f"{'Rank':<6}{'Team':<25}{'Global':<10}{'Quali':<10}{'Race':<10}{'Races':<8}{'Reliability'}")
        print("-" * 80)
        
        for idx, row in df_raw.iterrows():
            print(f"{df_raw.index.tolist().index(idx)+1:<6}{row['name'][:24]:<25}"
                  f"{row['global_elo']:<10.1f}{row['qualifying_elo']:<10.1f}"
                  f"{row['race_elo']:<10.1f}{row['total_races']:<8}{row['reliability']:.1f}%")
        
        # Sort by era-adjusted Elo
        df_era = pd.DataFrame(team_data).sort_values('era_adjusted_elo', ascending=False).head(limit)
        
        print("\n" + "=" * 80)
        print(f"TOP {limit} TEAMS BY ERA-ADJUSTED ELO (Accounts for competition depth)")
        print("=" * 80)
        print(f"{'Rank':<6}{'Team':<25}{'Adj. Elo':<12}{'Raw Elo':<10}{'Years':<15}{'Reliability'}")
        print("-" * 80)
        
        for idx, row in df_era.iterrows():
            years = f"{row['first_year']}-{row['last_year']}" if row['first_year'] != row['last_year'] else str(row['first_year'])
            print(f"{df_era.index.tolist().index(idx)+1:<6}{row['name'][:24]:<25}"
                  f"{row['era_adjusted_elo']:<12.1f}{row['global_elo']:<10.1f}"
                  f"{years:<15}{row['reliability']:.1f}%")
        
        print("=" * 80)
        print("\nRELIABILITY GUIDE:")
        print("  >90% = Very Reliable (200+ matchups)")
        print("  70-90% = Reliable (80-200 matchups)")
        print("  50-70% = Moderate (30-80 matchups)")
        print("  <50% = Low Confidence (<30 matchups)")
        print("=" * 80)


def main():
    calculator = TeamBasedF1Elo()
    calculator.calculate_all_elos()
    calculator.save_to_database()
    calculator.display_top_teams()
    
    print("\n✓ Team Elo calculation complete!")
    print("  Ratings saved to Team_Elo table")
    print("  Query with: SELECT * FROM Team_Elo ORDER BY global_elo DESC")


if __name__ == "__main__":
    main()
