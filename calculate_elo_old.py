"""
F1 ELO Rating Calculation Script

This script calculates ELO ratings for F1 drivers and teams based on race results.
The ELO system is adapted for F1 racing where multiple competitors race simultaneously.

ELO Formula for racing:
- Expected score is based on relative ELO differences
- K-factor determines rating volatility (higher K = more volatile)
- Points are distributed based on finishing positions
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

# Configuration
DB_PATH = 'd:/f1-elo/DB/f1_database.db'
INITIAL_ELO = 1500.0
K_FACTOR = 32  # Standard chess K-factor, adjust as needed
MIN_ELO = 1000.0
MAX_ELO = 3000.0


class F1EloCalculator:
    """Calculate ELO ratings for F1 drivers and teams"""
    
    def __init__(self, db_path, k_factor=32, initial_elo=1500):
        self.db_path = db_path
        self.k_factor = k_factor
        self.initial_elo = initial_elo
        self.driver_elos = {}
        self.team_elos = {}
    
    def expected_score(self, rating_a, rating_b):
        """Calculate expected score for rating_a against rating_b"""
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
    def calculate_position_score(self, position, total_participants):
        """
        Calculate score based on finishing position
        1st place = 1.0, last place = 0.0, with linear distribution
        DNF or non-classified = 0.0
        """
        if position is None or pd.isna(position):
            return 0.0
        
        # Linear scoring: 1st gets 1.0, last gets 0.0
        return (total_participants - position) / (total_participants - 1)
    
    def update_elo_rating(self, current_elo, actual_score, expected_score):
        """Update ELO rating based on actual vs expected score"""
        new_elo = current_elo + self.k_factor * (actual_score - expected_score)
        return max(MIN_ELO, min(MAX_ELO, new_elo))
    
    def calculate_driver_elos(self):
        """Calculate ELO ratings for all drivers across all races"""
        
        conn = sqlite3.connect(self.db_path)
        
        # Get all races ordered by date
        races_query = """
            SELECT race_id, race_name, race_date, season_year
            FROM Race
            ORDER BY race_date, race_id
        """
        races = pd.read_sql_query(races_query, conn)
        
        print(f"Calculating ELO ratings for {len(races)} races...")
        
        for idx, race in races.iterrows():
            race_id = race['race_id']
            
            # Get all results for this race
            results_query = f"""
                SELECT result_id, driver_id, team_id, position, points
                FROM Result
                WHERE race_id = {race_id}
                ORDER BY COALESCE(position, 999), result_id
            """
            results = pd.read_sql_query(results_query, conn)
            
            if len(results) == 0:
                continue
            
            total_participants = len(results)
            
            # Initialize ELO for new drivers
            for driver_id in results['driver_id']:
                if driver_id not in self.driver_elos:
                    self.driver_elos[driver_id] = self.initial_elo
            
            # Calculate new ELOs for this race
            new_elos = {}
            
            for _, result in results.iterrows():
                driver_id = result['driver_id']
                position = result['position']
                current_elo = self.driver_elos[driver_id]
                
                # Calculate actual score based on position
                actual_score = self.calculate_position_score(position, total_participants)
                
                # Calculate expected score against all other drivers
                expected_score = 0
                for _, opponent in results.iterrows():
                    if opponent['driver_id'] != driver_id:
                        opponent_elo = self.driver_elos[opponent['driver_id']]
                        expected_score += self.expected_score(current_elo, opponent_elo)
                
                # Normalize expected score to 0-1 range
                expected_score = expected_score / (total_participants - 1)
                
                # Update ELO
                new_elos[driver_id] = self.update_elo_rating(
                    current_elo, actual_score, expected_score
                )
            
            # Apply all ELO changes for this race
            for driver_id, new_elo in new_elos.items():
                self.driver_elos[driver_id] = new_elo
            
            # Save ELO ratings to database
            self.save_driver_elos(conn, race_id)
            
            if (idx + 1) % 50 == 0:
                print(f"  Processed {idx + 1}/{len(races)} races")
        
        conn.commit()
        conn.close()
        
        print("Driver ELO calculation complete!")
    
    def calculate_team_elos(self):
        """Calculate ELO ratings for all teams across all races"""
        
        conn = sqlite3.connect(self.db_path)
        
        # Get all races ordered by date
        races_query = """
            SELECT race_id, race_name, race_date, season_year
            FROM Race
            ORDER BY race_date, race_id
        """
        races = pd.read_sql_query(races_query, conn)
        
        print(f"Calculating Team ELO ratings for {len(races)} races...")
        
        for idx, race in races.iterrows():
            race_id = race['race_id']
            
            # Get team results (average position of team's drivers)
            results_query = f"""
                SELECT team_id,
                       AVG(COALESCE(position, 999)) as avg_position,
                       SUM(points) as team_points,
                       COUNT(*) as driver_count
                FROM Result
                WHERE race_id = {race_id}
                GROUP BY team_id
                ORDER BY avg_position
            """
            team_results = pd.read_sql_query(results_query, conn)
            
            if len(team_results) == 0:
                continue
            
            total_teams = len(team_results)
            
            # Initialize ELO for new teams
            for team_id in team_results['team_id']:
                if team_id not in self.team_elos:
                    self.team_elos[team_id] = self.initial_elo
            
            # Assign positions based on average driver position
            team_results = team_results.sort_values('avg_position').reset_index(drop=True)
            team_results['team_position'] = range(1, len(team_results) + 1)
            
            # Calculate new ELOs for this race
            new_elos = {}
            
            for _, team_result in team_results.iterrows():
                team_id = team_result['team_id']
                position = team_result['team_position']
                current_elo = self.team_elos[team_id]
                
                # Calculate actual score based on position
                actual_score = self.calculate_position_score(position, total_teams)
                
                # Calculate expected score against all other teams
                expected_score = 0
                for _, opponent in team_results.iterrows():
                    if opponent['team_id'] != team_id:
                        opponent_elo = self.team_elos[opponent['team_id']]
                        expected_score += self.expected_score(current_elo, opponent_elo)
                
                # Normalize expected score to 0-1 range
                expected_score = expected_score / (total_teams - 1)
                
                # Update ELO
                new_elos[team_id] = self.update_elo_rating(
                    current_elo, actual_score, expected_score
                )
            
            # Apply all ELO changes for this race
            for team_id, new_elo in new_elos.items():
                self.team_elos[team_id] = new_elo
            
            # Save ELO ratings to database
            self.save_team_elos(conn, race_id)
            
            if (idx + 1) % 50 == 0:
                print(f"  Processed {idx + 1}/{len(races)} races")
        
        conn.commit()
        conn.close()
        
        print("Team ELO calculation complete!")
    
    def save_driver_elos(self, conn, race_id):
        """Save current driver ELO ratings to database"""
        cursor = conn.cursor()
        
        for driver_id, elo_rating in self.driver_elos.items():
            cursor.execute("""
                INSERT OR REPLACE INTO Driver_Elo 
                (driver_id, race_id, elo_rating, updated_on)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (driver_id, race_id, round(elo_rating, 2)))
    
    def save_team_elos(self, conn, race_id):
        """Save current team ELO ratings to database"""
        cursor = conn.cursor()
        
        for team_id, elo_rating in self.team_elos.items():
            cursor.execute("""
                INSERT OR REPLACE INTO Team_Elo 
                (team_id, race_id, elo_rating, updated_on)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (team_id, race_id, round(elo_rating, 2)))
    
    def get_current_driver_rankings(self, conn, top_n=20):
        """Get current driver rankings"""
        query = f"""
            SELECT d.first_name, d.last_name, d.nationality,
                   de.elo_rating, r.race_date
            FROM Driver_Elo de
            JOIN Driver d ON de.driver_id = d.driver_id
            JOIN Race r ON de.race_id = r.race_id
            WHERE de.race_id = (SELECT MAX(race_id) FROM Race)
            ORDER BY de.elo_rating DESC
            LIMIT {top_n}
        """
        return pd.read_sql_query(query, conn)
    
    def get_current_team_rankings(self, conn, top_n=10):
        """Get current team rankings"""
        query = f"""
            SELECT t.team_name, t.base_country,
                   te.elo_rating, r.race_date
            FROM Team_Elo te
            JOIN Team t ON te.team_id = t.team_id
            JOIN Race r ON te.race_id = r.race_id
            WHERE te.race_id = (SELECT MAX(race_id) FROM Race)
            ORDER BY te.elo_rating DESC
            LIMIT {top_n}
        """
        return pd.read_sql_query(query, conn)


def main():
    """Main execution function"""
    
    print("="*60)
    print("F1 ELO Rating Calculator")
    print("="*60)
    print(f"Database: {DB_PATH}")
    print(f"Initial ELO: {INITIAL_ELO}")
    print(f"K-Factor: {K_FACTOR}")
    print("="*60)
    
    # Initialize calculator
    calculator = F1EloCalculator(DB_PATH, K_FACTOR, INITIAL_ELO)
    
    # Calculate driver ELOs
    print("\n1. Calculating Driver ELO Ratings...")
    calculator.calculate_driver_elos()
    
    # Calculate team ELOs
    print("\n2. Calculating Team ELO Ratings...")
    calculator.calculate_team_elos()
    
    # Display results
    conn = sqlite3.connect(DB_PATH)
    
    print("\n" + "="*60)
    print("TOP 20 DRIVERS BY CURRENT ELO RATING")
    print("="*60)
    driver_rankings = calculator.get_current_driver_rankings(conn, 20)
    for idx, row in driver_rankings.iterrows():
        print(f"{idx+1:2d}. {row['first_name']} {row['last_name']:20s} "
              f"({row['nationality']:15s}) - ELO: {row['elo_rating']:.2f}")
    
    print("\n" + "="*60)
    print("TOP 10 TEAMS BY CURRENT ELO RATING")
    print("="*60)
    team_rankings = calculator.get_current_team_rankings(conn, 10)
    for idx, row in team_rankings.iterrows():
        print(f"{idx+1:2d}. {row['team_name']:25s} "
              f"({row['base_country']:15s}) - ELO: {row['elo_rating']:.2f}")
    
    print("\n" + "="*60)
    print("ELO Calculation Complete!")
    print("="*60)
    
    conn.close()


if __name__ == '__main__':
    main()
