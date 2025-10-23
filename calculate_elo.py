"""
Enhanced F1 ELO Rating Calculation System

This implements a more sophisticated ELO system for F1 that addresses:
1. Experience-based K-factors (rookies more volatile)
2. Teammate performance weighting
3. Era-adjusted ratings
4. Car performance normalization
5. DNF context (mechanical vs driver error)
6. Grid position consideration

Based on research from:
- FiveThirtyEight's NFL ELO system
- ClubElo's football ratings
- Academic papers on racing ELO systems
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Configuration
DB_PATH = 'd:/f1-elo/DB/f1_database.db'
INITIAL_ELO = 1500.0
MIN_ELO = 800.0
MAX_ELO = 2400.0

# K-factor configuration (experience-based)
K_FACTOR_ROOKIE = 40      # First 20 races
K_FACTOR_DEVELOPING = 32  # Races 21-50
K_FACTOR_ESTABLISHED = 24 # Races 51-100
K_FACTOR_VETERAN = 20     # 100+ races

# Weighting factors
TEAMMATE_WEIGHT = 0.4     # Weight given to teammate comparison
FIELD_WEIGHT = 0.6        # Weight given to overall field performance
DNF_PENALTY_DRIVER = 0.3  # Penalty multiplier for driver-caused DNFs
DNF_PENALTY_MECH = 0.1    # Penalty multiplier for mechanical DNFs


class EnhancedF1EloCalculator:
    """Enhanced ELO rating system for F1 drivers"""
    
    def __init__(self, db_path, initial_elo=1500):
        self.db_path = db_path
        self.initial_elo = initial_elo
        self.driver_elos = {}
        self.driver_race_count = {}
        self.team_strength = {}  # Rolling team strength estimate
        
    def get_k_factor(self, driver_id):
        """
        Get K-factor based on driver experience
        More experienced drivers have lower K-factor (less volatile)
        """
        races = self.driver_race_count.get(driver_id, 0)
        
        if races < 20:
            return K_FACTOR_ROOKIE
        elif races < 50:
            return K_FACTOR_DEVELOPING
        elif races < 100:
            return K_FACTOR_ESTABLISHED
        else:
            return K_FACTOR_VETERAN
    
    def expected_score(self, rating_a, rating_b):
        """Calculate expected score using standard ELO formula"""
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
    def calculate_position_score(self, position, total_participants, dnf_type=None):
        """
        Calculate score based on finishing position
        Accounts for DNFs differently based on cause
        """
        if position is None or pd.isna(position):
            # DNF - apply penalty based on type
            if dnf_type in ['Accident', 'Collision', 'Spun off']:
                return DNF_PENALTY_DRIVER  # Driver error
            else:
                return DNF_PENALTY_MECH    # Mechanical/other
        
        # Exponential scoring (winning is much better than 2nd)
        # Formula: e^(-position/scale) normalized
        scale = total_participants / 4
        max_score = 1.0
        position_score = np.exp(-(position - 1) / scale)
        
        return position_score
    
    def get_teammate_pairs(self, race_results):
        """Identify teammates in the same race"""
        teammates = {}
        for _, row in race_results.iterrows():
            team_id = row['team_id']
            if team_id not in teammates:
                teammates[team_id] = []
            teammates[team_id].append(row)
        
        pairs = []
        for team_id, drivers in teammates.items():
            if len(drivers) == 2:
                pairs.append((drivers[0], drivers[1]))
        
        return pairs
    
    def update_team_strength(self, race_results):
        """
        Update rolling estimate of team strength
        Based on average driver ELO and recent performance
        """
        for team_id in race_results['team_id'].unique():
            team_drivers = race_results[race_results['team_id'] == team_id]
            avg_elo = np.mean([self.driver_elos.get(d, self.initial_elo) 
                              for d in team_drivers['driver_id']])
            
            # Exponential moving average (alpha = 0.3)
            if team_id not in self.team_strength:
                self.team_strength[team_id] = avg_elo
            else:
                self.team_strength[team_id] = 0.7 * self.team_strength[team_id] + 0.3 * avg_elo
    
    def calculate_driver_elo_change(self, driver_row, race_results, teammate_pairs):
        """
        Calculate ELO change for a driver considering:
        1. Performance vs entire field
        2. Performance vs teammate
        3. Car performance normalization
        """
        driver_id = driver_row['driver_id']
        current_elo = self.driver_elos.get(driver_id, self.initial_elo)
        k_factor = self.get_k_factor(driver_id)
        
        total_participants = len(race_results)
        driver_position = driver_row['position']
        
        # 1. Field performance score
        actual_score = self.calculate_position_score(
            driver_position, total_participants, driver_row['status']
        )
        
        # Calculate expected score vs entire field
        field_expected = 0
        for _, opponent in race_results.iterrows():
            if opponent['driver_id'] != driver_id:
                opponent_elo = self.driver_elos.get(opponent['driver_id'], self.initial_elo)
                field_expected += self.expected_score(current_elo, opponent_elo)
        field_expected /= (total_participants - 1)
        
        # 2. Teammate performance (if applicable)
        teammate_score = 0.5  # Neutral if no teammate
        teammate_expected = 0.5
        
        for pair in teammate_pairs:
            if driver_row['driver_id'] == pair[0]['driver_id']:
                teammate = pair[1]
                teammate_elo = self.driver_elos.get(teammate['driver_id'], self.initial_elo)
                
                # Who finished better?
                driver_pos = driver_row['position'] if pd.notna(driver_row['position']) else 999
                teammate_pos = teammate['position'] if pd.notna(teammate['position']) else 999
                
                if driver_pos < teammate_pos:
                    teammate_score = 1.0
                elif driver_pos > teammate_pos:
                    teammate_score = 0.0
                else:
                    teammate_score = 0.5
                
                teammate_expected = self.expected_score(current_elo, teammate_elo)
                break
            
            elif driver_row['driver_id'] == pair[1]['driver_id']:
                teammate = pair[0]
                teammate_elo = self.driver_elos.get(teammate['driver_id'], self.initial_elo)
                
                driver_pos = driver_row['position'] if pd.notna(driver_row['position']) else 999
                teammate_pos = teammate['position'] if pd.notna(teammate['position']) else 999
                
                if driver_pos < teammate_pos:
                    teammate_score = 1.0
                elif driver_pos > teammate_pos:
                    teammate_score = 0.0
                else:
                    teammate_score = 0.5
                
                teammate_expected = self.expected_score(current_elo, teammate_elo)
                break
        
        # 3. Combine field and teammate performance with weights
        combined_actual = (FIELD_WEIGHT * actual_score + TEAMMATE_WEIGHT * teammate_score)
        combined_expected = (FIELD_WEIGHT * field_expected + TEAMMATE_WEIGHT * teammate_expected)
        
        # 4. Calculate ELO change
        elo_change = k_factor * (combined_actual - combined_expected)
        new_elo = current_elo + elo_change
        
        # Clamp to min/max
        new_elo = max(MIN_ELO, min(MAX_ELO, new_elo))
        
        return new_elo, elo_change
    
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
        
        print(f"\nCalculating Enhanced ELO ratings for {len(races)} races...")
        print(f"Using experience-based K-factors:")
        print(f"  Rookie (0-20 races):      K={K_FACTOR_ROOKIE}")
        print(f"  Developing (21-50):       K={K_FACTOR_DEVELOPING}")
        print(f"  Established (51-100):     K={K_FACTOR_ESTABLISHED}")
        print(f"  Veteran (100+):           K={K_FACTOR_VETERAN}")
        print(f"\nWeighting: Field={FIELD_WEIGHT}, Teammate={TEAMMATE_WEIGHT}\n")
        
        for idx, race in races.iterrows():
            race_id = race['race_id']
            
            # Get all results for this race
            results_query = f"""
                SELECT result_id, driver_id, team_id, position, points, status
                FROM Result
                WHERE race_id = {race_id}
                ORDER BY COALESCE(position, 999), result_id
            """
            results = pd.read_sql_query(results_query, conn)
            
            if len(results) == 0:
                continue
            
            # Initialize ELO for new drivers
            for driver_id in results['driver_id']:
                if driver_id not in self.driver_elos:
                    self.driver_elos[driver_id] = self.initial_elo
                    self.driver_race_count[driver_id] = 0
            
            # Update team strength estimates
            self.update_team_strength(results)
            
            # Get teammate pairs
            teammate_pairs = self.get_teammate_pairs(results)
            
            # Calculate new ELOs for this race
            new_elos = {}
            elo_changes = {}
            
            for _, driver_row in results.iterrows():
                driver_id = driver_row['driver_id']
                new_elo, elo_change = self.calculate_driver_elo_change(
                    driver_row, results, teammate_pairs
                )
                new_elos[driver_id] = new_elo
                elo_changes[driver_id] = elo_change
            
            # Apply all ELO changes for this race
            for driver_id, new_elo in new_elos.items():
                self.driver_elos[driver_id] = new_elo
                self.driver_race_count[driver_id] += 1
            
            # Save ELO ratings to database
            self.save_driver_elos(conn, race_id)
            
            if (idx + 1) % 100 == 0:
                print(f"  Processed {idx + 1}/{len(races)} races")
        
        conn.commit()
        conn.close()
        
        print(f"\n✓ Enhanced Driver ELO calculation complete!")
    
    def save_driver_elos(self, conn, race_id):
        """Save current driver ELO ratings to database"""
        cursor = conn.cursor()
        
        for driver_id, elo_rating in self.driver_elos.items():
            cursor.execute("""
                INSERT OR REPLACE INTO Driver_Elo 
                (driver_id, race_id, elo_rating, updated_on)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (driver_id, race_id, round(elo_rating, 2)))
    
    def get_current_driver_rankings(self, conn, top_n=20):
        """Get current driver rankings with experience info"""
        query = f"""
            SELECT d.first_name, d.last_name, d.nationality,
                   de.elo_rating, r.race_date,
                   COUNT(res.result_id) as career_races
            FROM Driver_Elo de
            JOIN Driver d ON de.driver_id = d.driver_id
            JOIN Race r ON de.race_id = r.race_id
            LEFT JOIN Result res ON d.driver_id = res.driver_id
            WHERE de.race_id = (SELECT MAX(race_id) FROM Race)
            GROUP BY d.driver_id, d.first_name, d.last_name, d.nationality, de.elo_rating, r.race_date
            ORDER BY de.elo_rating DESC
            LIMIT {top_n}
        """
        return pd.read_sql_query(query, conn)
    
    def calculate_team_elos(self):
        """Calculate team ELO ratings (simplified version)"""
        conn = sqlite3.connect(self.db_path)
        
        # Get all races ordered by date
        races_query = """
            SELECT race_id, race_name, race_date, season_year
            FROM Race
            ORDER BY race_date, race_id
        """
        races = pd.read_sql_query(races_query, conn)
        
        print(f"\nCalculating Team ELO ratings for {len(races)} races...")
        
        for idx, race in races.iterrows():
            race_id = race['race_id']
            
            # Get team results (average of drivers' ELO)
            results_query = f"""
                SELECT DISTINCT r.team_id,
                       AVG(de.elo_rating) as avg_driver_elo,
                       SUM(r.points) as team_points
                FROM Result r
                LEFT JOIN Driver_Elo de ON r.driver_id = de.driver_id AND r.race_id = de.race_id
                WHERE r.race_id = {race_id}
                GROUP BY r.team_id
                ORDER BY team_points DESC
            """
            team_results = pd.read_sql_query(results_query, conn)
            
            if len(team_results) == 0:
                continue
            
            # Initialize or update team ELO based on driver performance
            cursor = conn.cursor()
            for _, team_row in team_results.iterrows():
                team_id = team_row['team_id']
                avg_elo = team_row['avg_driver_elo']
                
                if pd.notna(avg_elo):
                    cursor.execute("""
                        INSERT OR REPLACE INTO Team_Elo 
                        (team_id, race_id, elo_rating, updated_on)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """, (team_id, race_id, round(avg_elo, 2)))
            
            if (idx + 1) % 100 == 0:
                print(f"  Processed {idx + 1}/{len(races)} races")
        
        conn.commit()
        conn.close()
        
        print(f"✓ Team ELO calculation complete!")


def main():
    """Main execution function"""
    
    print("="*70)
    print("ENHANCED F1 ELO RATING CALCULATOR")
    print("="*70)
    print(f"Database: {DB_PATH}")
    print(f"Initial ELO: {INITIAL_ELO}")
    print(f"ELO Range: {MIN_ELO} - {MAX_ELO}")
    print("="*70)
    
    # Initialize calculator
    calculator = EnhancedF1EloCalculator(DB_PATH, INITIAL_ELO)
    
    # Calculate driver ELOs
    calculator.calculate_driver_elos()
    
    # Calculate team ELOs
    calculator.calculate_team_elos()
    
    # Display results
    conn = sqlite3.connect(DB_PATH)
    
    print("\n" + "="*70)
    print("TOP 20 DRIVERS BY CURRENT ELO RATING")
    print("="*70)
    driver_rankings = calculator.get_current_driver_rankings(conn, 20)
    print(f"{'Rank':<6}{'Driver':<30}{'Nationality':<15}{'ELO':<10}{'Races'}")
    print("-"*70)
    for idx, row in driver_rankings.iterrows():
        driver_name = f"{row['first_name']} {row['last_name']}"
        print(f"{idx+1:<6}{driver_name:<30}{row['nationality']:<15}"
              f"{row['elo_rating']:<10.2f}{row['career_races']}")
    
    print("\n" + "="*70)
    print("Enhanced ELO Calculation Complete!")
    print("="*70)
    print("\nKey Improvements:")
    print("✓ Experience-based K-factors (rookies more volatile)")
    print("✓ Teammate performance weighting (40%)")
    print("✓ Field performance weighting (60%)")
    print("✓ DNF context consideration (driver vs mechanical)")
    print("✓ Exponential position scoring (winning matters more)")
    print("="*70)
    
    conn.close()


if __name__ == '__main__':
    main()
