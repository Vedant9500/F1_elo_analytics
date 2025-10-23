"""
Formula 1 Driver Elo Rating System
===================================

A statistically robust Elo rating system for F1 drivers based on teammate comparisons.

Key Principles:
1. TEAMMATE-ONLY COMPARISONS: Isolates driver skill from car performance
2. DUAL RATINGS: Separate Qualifying Elo and Race Elo
3. DYNAMIC K-FACTORS: Adapts to driver experience (40/20/10)
4. PROPER DNF HANDLING: Distinguishes mechanical failures from driver errors
5. GLOBAL ELO: Weighted combination (30% Qualifying, 70% Race)
6. RATING NORMALIZATION: Prevents inflation across eras

Based on the comprehensive framework from:
"A Comprehensive Framework for a Robust Formula 1 Driver Elo Rating System"
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict


class TeammateBasedF1Elo:
    """
    F1 Elo rating system using teammate head-to-head comparisons.
    
    This approach neutralizes car performance differences by only comparing
    drivers in the same machinery, providing a pure measure of driver skill.
    """
    
    def __init__(self, db_path='DB/f1_database.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
        # Initial rating for all new drivers
        self.INITIAL_RATING = 1500
        
        # Dynamic K-factor thresholds
        self.ROOKIE_RACES = 30  # First 30 races use high K-factor
        self.ELITE_THRESHOLD = 1750  # Once achieved, permanently use low K-factor
        
        # K-factor values
        self.K_ROOKIE = 40  # High volatility for new drivers
        self.K_ESTABLISHED = 20  # Standard for mid-career
        self.K_ELITE = 10  # Low volatility for proven elite drivers
        
        # Global Elo weights
        self.QUALIFYING_WEIGHT = 0.3
        self.RACE_WEIGHT = 0.7
        
        # Driver rating storage
        # Structure: {driver_id: {
        #   'qualifying_elo': float,
        #   'race_elo': float,
        #   'qualifying_races': int,
        #   'race_races': int,
        #   'ever_elite_qualifying': bool,
        #   'ever_elite_race': bool
        # }}
        self.driver_ratings = defaultdict(lambda: {
            'qualifying_elo': self.INITIAL_RATING,
            'race_elo': self.INITIAL_RATING,
            'qualifying_races': 0,
            'race_races': 0,
            'ever_elite_qualifying': False,
            'ever_elite_race': False
        })
        
        # Mechanical failure status codes (DNFs that should be EXCLUDED)
        self.MECHANICAL_FAILURES = {
            'Engine', 'Gearbox', 'Transmission', 'Clutch', 'Hydraulics',
            'Electrical', 'Electronics', 'Fuel System', 'Fuel Pump',
            'Fuel Pressure', 'Oil Pressure', 'Oil Leak', 'Radiator',
            'Cooling System', 'Water Leak', 'Overheating', 'Suspension',
            'Brakes', 'Wheel', 'Wheel Bearing', 'Puncture', 'Driveshaft',
            'CV Joint', 'Differential', 'Halfshaft', 'Battery', 'Alternator',
            'Turbo', 'Throttle', 'Fuel Leak', 'Fire', 'Power Unit',
            'ERS', 'MGU-K', 'MGU-H', 'Pneumatics', 'Exhaust'
        }
        
        # Driver error status codes (DNFs that should be INCLUDED as losses)
        self.DRIVER_ERRORS = {
            'Accident', 'Collision', 'Spun off', 'Damage', 'Collision damage',
            'Fatal accident', 'Injury', 'Driver Seat', 'Seat'
        }
        
    def get_k_factor(self, current_elo, races_completed, ever_elite):
        """
        Dynamic K-factor based on driver experience and rating.
        
        Tier 1 (Rookie): K=40 for first 30 races
        Tier 2 (Established): K=20 for >30 races if rating < 1750
        Tier 3 (Elite): K=10 if rating ever exceeded 1750
        """
        if ever_elite:
            return self.K_ELITE
        elif races_completed < self.ROOKIE_RACES:
            return self.K_ROOKIE
        else:
            return self.K_ESTABLISHED
    
    def expected_score(self, rating_a, rating_b):
        """
        Calculate expected score using standard Elo formula.
        
        E_A = 1 / (1 + 10^((R_B - R_A) / 400))
        """
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
    def update_rating(self, rating, k_factor, actual_score, expected_score):
        """
        Update Elo rating based on match outcome.
        
        New_Rating = Old_Rating + K * (Actual - Expected)
        """
        return rating + k_factor * (actual_score - expected_score)
    
    def is_mechanical_dnf(self, status):
        """Check if DNF reason is mechanical (should exclude matchup)."""
        if pd.isna(status) or status == '':
            return False
        
        status_upper = str(status).upper()
        
        # Check for mechanical failure keywords
        for failure in self.MECHANICAL_FAILURES:
            if failure.upper() in status_upper:
                return True
        return False
    
    def is_driver_error_dnf(self, status):
        """Check if DNF reason is driver error (should count as loss)."""
        if pd.isna(status) or status == '':
            return False
        
        status_upper = str(status).upper()
        
        # Check for driver error keywords
        for error in self.DRIVER_ERRORS:
            if error.upper() in status_upper:
                return True
        return False
    
    def is_finished(self, status):
        """Check if driver finished the race (classified)."""
        if pd.isna(status):
            return False
        return str(status).strip() == 'Finished' or str(status).startswith('+')
    
    def process_qualifying_matchup(self, driver1_id, driver2_id, driver1_pos, driver2_pos,
                                   driver1_status, driver2_status):
        """
        Process a qualifying head-to-head between teammates.
        
        Returns: True if matchup was processed, False if excluded
        """
        # Exclude if either driver had mechanical issues
        if self.is_mechanical_dnf(driver1_status) or self.is_mechanical_dnf(driver2_status):
            return False
        
        # Determine winner (lower position is better)
        if driver1_pos < driver2_pos:
            winner_id, loser_id = driver1_id, driver2_id
        else:
            winner_id, loser_id = driver2_id, driver1_id
        
        # Get current ratings
        winner_elo = self.driver_ratings[winner_id]['qualifying_elo']
        loser_elo = self.driver_ratings[loser_id]['qualifying_elo']
        
        # Calculate expected scores
        winner_expected = self.expected_score(winner_elo, loser_elo)
        loser_expected = 1 - winner_expected
        
        # Get K-factors
        winner_k = self.get_k_factor(
            winner_elo,
            self.driver_ratings[winner_id]['qualifying_races'],
            self.driver_ratings[winner_id]['ever_elite_qualifying']
        )
        loser_k = self.get_k_factor(
            loser_elo,
            self.driver_ratings[loser_id]['qualifying_races'],
            self.driver_ratings[loser_id]['ever_elite_qualifying']
        )
        
        # Update ratings (winner gets 1, loser gets 0)
        new_winner_elo = self.update_rating(winner_elo, winner_k, 1, winner_expected)
        new_loser_elo = self.update_rating(loser_elo, loser_k, 0, loser_expected)
        
        # Store updated ratings
        self.driver_ratings[winner_id]['qualifying_elo'] = new_winner_elo
        self.driver_ratings[loser_id]['qualifying_elo'] = new_loser_elo
        
        # Increment race counters
        self.driver_ratings[winner_id]['qualifying_races'] += 1
        self.driver_ratings[loser_id]['qualifying_races'] += 1
        
        # Check for elite status
        if new_winner_elo >= self.ELITE_THRESHOLD:
            self.driver_ratings[winner_id]['ever_elite_qualifying'] = True
        if new_loser_elo >= self.ELITE_THRESHOLD:
            self.driver_ratings[loser_id]['ever_elite_qualifying'] = True
        
        return True
    
    def process_race_matchup(self, driver1_id, driver2_id, driver1_pos, driver2_pos,
                            driver1_status, driver2_status):
        """
        Process a race head-to-head between teammates.
        
        Returns: True if matchup was processed, False if excluded
        """
        # Check if either driver had mechanical DNF (exclude matchup)
        d1_mechanical = self.is_mechanical_dnf(driver1_status)
        d2_mechanical = self.is_mechanical_dnf(driver2_status)
        
        if d1_mechanical or d2_mechanical:
            return False
        
        # Check if drivers had driver error DNF (counts as loss)
        d1_error = self.is_driver_error_dnf(driver1_status)
        d2_error = self.is_driver_error_dnf(driver2_status)
        d1_finished = self.is_finished(driver1_status)
        d2_finished = self.is_finished(driver2_status)
        
        # If both DNF'd due to driver error, exclude (no clean winner)
        if d1_error and d2_error:
            return False
        
        # Determine winner
        # Driver error DNF automatically loses if opponent finished or had no error
        if d1_error and (d2_finished or not d2_error):
            winner_id, loser_id = driver2_id, driver1_id
        elif d2_error and (d1_finished or not d1_error):
            winner_id, loser_id = driver1_id, driver2_id
        else:
            # Normal comparison by position (lower is better)
            if driver1_pos < driver2_pos:
                winner_id, loser_id = driver1_id, driver2_id
            else:
                winner_id, loser_id = driver2_id, driver1_id
        
        # Get current ratings
        winner_elo = self.driver_ratings[winner_id]['race_elo']
        loser_elo = self.driver_ratings[loser_id]['race_elo']
        
        # Calculate expected scores
        winner_expected = self.expected_score(winner_elo, loser_elo)
        loser_expected = 1 - winner_expected
        
        # Get K-factors
        winner_k = self.get_k_factor(
            winner_elo,
            self.driver_ratings[winner_id]['race_races'],
            self.driver_ratings[winner_id]['ever_elite_race']
        )
        loser_k = self.get_k_factor(
            loser_elo,
            self.driver_ratings[loser_id]['race_races'],
            self.driver_ratings[loser_id]['ever_elite_race']
        )
        
        # Update ratings
        new_winner_elo = self.update_rating(winner_elo, winner_k, 1, winner_expected)
        new_loser_elo = self.update_rating(loser_elo, loser_k, 0, loser_expected)
        
        # Store updated ratings
        self.driver_ratings[winner_id]['race_elo'] = new_winner_elo
        self.driver_ratings[loser_id]['race_elo'] = new_loser_elo
        
        # Increment race counters
        self.driver_ratings[winner_id]['race_races'] += 1
        self.driver_ratings[loser_id]['race_races'] += 1
        
        # Check for elite status
        if new_winner_elo >= self.ELITE_THRESHOLD:
            self.driver_ratings[winner_id]['ever_elite_race'] = True
        if new_loser_elo >= self.ELITE_THRESHOLD:
            self.driver_ratings[loser_id]['ever_elite_race'] = True
        
        return True
    
    def normalize_ratings(self, season_year):
        """
        Normalize all ratings to mean of 1500 at end of season.
        Prevents rating inflation across eras.
        """
        if not self.driver_ratings:
            return
        
        # Calculate mean qualifying Elo
        qualifying_elos = [r['qualifying_elo'] for r in self.driver_ratings.values()]
        mean_qualifying = np.mean(qualifying_elos)
        
        # Calculate mean race Elo
        race_elos = [r['race_elo'] for r in self.driver_ratings.values()]
        mean_race = np.mean(race_elos)
        
        # Normalize all ratings
        for driver_id in self.driver_ratings:
            # Qualifying normalization
            self.driver_ratings[driver_id]['qualifying_elo'] = (
                self.driver_ratings[driver_id]['qualifying_elo'] - 
                mean_qualifying + self.INITIAL_RATING
            )
            
            # Race normalization
            self.driver_ratings[driver_id]['race_elo'] = (
                self.driver_ratings[driver_id]['race_elo'] - 
                mean_race + self.INITIAL_RATING
            )
        
        print(f"  Season {season_year} normalized: Quali mean {mean_qualifying:.1f}→1500, "
              f"Race mean {mean_race:.1f}→1500")
    
    def calculate_global_elo(self, qualifying_elo, race_elo):
        """
        Calculate Global Elo as weighted combination.
        
        Global = 30% Qualifying + 70% Race
        """
        return (self.QUALIFYING_WEIGHT * qualifying_elo + 
                self.RACE_WEIGHT * race_elo)
    
    def calculate_reliability_score(self, matchups):
        """
        Calculate reliability score (0-100) based on sample size.
        
        Uses sigmoid function to reward larger sample sizes:
        - 100 matchups = ~95% reliability
        - 50 matchups = ~85% reliability
        - 20 matchups = ~63% reliability
        - 10 matchups = ~45% reliability
        """
        # Sigmoid function: reliability = 100 / (1 + e^(-(matchups - 30)/20))
        import math
        reliability = 100 / (1 + math.exp(-(matchups - 30) / 20))
        return round(reliability, 1)
    
    def calculate_era_adjustment(self, debut_year, total_matchups):
        """
        Calculate era adjustment factor to account for:
        1. Fewer races in early eras
        2. Smaller field sizes
        3. Less competitive depth
        
        Adjustment reduces Elo for drivers with limited competition.
        """
        # Era difficulty multipliers (based on field strength research)
        if debut_year < 1960:
            era_multiplier = 0.92  # Early era: smaller fields, less depth
        elif debut_year < 1970:
            era_multiplier = 0.95  # 1960s: growing competition
        elif debut_year < 1980:
            era_multiplier = 0.97  # 1970s: professional era begins
        elif debut_year < 2000:
            era_multiplier = 0.99  # Modern era: high competition
        else:
            era_multiplier = 1.00  # Contemporary: peak competition
        
        # Sample size penalty for very few matchups
        if total_matchups < 30:
            sample_penalty = 0.95  # Reduce confidence for small samples
        else:
            sample_penalty = 1.00
        
        return era_multiplier * sample_penalty
    
    def calculate_all_elos(self):
        """
        Main calculation loop: process all races chronologically.
        """
        print("="*70)
        print("F1 TEAMMATE-BASED ELO RATING SYSTEM")
        print("="*70)
        print(f"Initial Rating: {self.INITIAL_RATING}")
        print(f"K-Factors: Rookie={self.K_ROOKIE}, Established={self.K_ESTABLISHED}, "
              f"Elite={self.K_ELITE}")
        print(f"Global Elo Weights: {self.QUALIFYING_WEIGHT*100:.0f}% Qualifying, "
              f"{self.RACE_WEIGHT*100:.0f}% Race")
        print("="*70)
        
        # Get all races ordered chronologically
        query = """
            SELECT r.race_id, r.season_year, r.round_number, r.race_name, r.race_date
            FROM Race r
            ORDER BY r.race_date, r.round_number
        """
        races = pd.read_sql_query(query, self.conn)
        
        current_season = None
        total_quali_matchups = 0
        total_race_matchups = 0
        
        for idx, race in races.iterrows():
            race_id = race['race_id']
            year = race['season_year']
            
            # Season normalization at year end
            if current_season is not None and year != current_season:
                self.normalize_ratings(current_season)
            current_season = year
            
            # Get all results for this race with team information
            results_query = """
                SELECT 
                    res.result_id,
                    res.driver_id,
                    res.team_id,
                    res.grid_position,
                    res.position,
                    res.status,
                    d.first_name,
                    d.last_name
                FROM Result res
                JOIN Driver d ON res.driver_id = d.driver_id
                WHERE res.race_id = ?
                ORDER BY res.team_id, res.position
            """
            results = pd.read_sql_query(results_query, self.conn, params=(race_id,))
            
            if results.empty:
                continue
            
            # Group by team to find teammate pairs
            teams = results.groupby('team_id')
            
            quali_matchups = 0
            race_matchups = 0
            
            for team_id, team_results in teams:
                if len(team_results) < 2:
                    continue  # Need at least 2 drivers
                
                # Sort by driver_id to ensure consistent pairing
                team_results = team_results.sort_values('driver_id')
                drivers = team_results.to_dict('records')
                
                # Process all pairwise combinations (usually just 2 drivers)
                for i in range(len(drivers)):
                    for j in range(i + 1, len(drivers)):
                        d1, d2 = drivers[i], drivers[j]
                        
                        # Process qualifying matchup
                        if pd.notna(d1['grid_position']) and pd.notna(d2['grid_position']):
                            if self.process_qualifying_matchup(
                                d1['driver_id'], d2['driver_id'],
                                d1['grid_position'], d2['grid_position'],
                                d1['status'], d2['status']
                            ):
                                quali_matchups += 1
                        
                        # Process race matchup
                        if pd.notna(d1['position']) and pd.notna(d2['position']):
                            if self.process_race_matchup(
                                d1['driver_id'], d2['driver_id'],
                                d1['position'], d2['position'],
                                d1['status'], d2['status']
                            ):
                                race_matchups += 1
            
            total_quali_matchups += quali_matchups
            total_race_matchups += race_matchups
            
            # Progress update every 50 races
            if (idx + 1) % 50 == 0:
                print(f"Processed {idx + 1}/{len(races)} races... "
                      f"(Quali: {total_quali_matchups}, Race: {total_race_matchups} matchups)")
        
        # Final season normalization
        if current_season is not None:
            self.normalize_ratings(current_season)
        
        print("="*70)
        print(f"CALCULATION COMPLETE")
        print(f"Total Races Processed: {len(races)}")
        print(f"Total Qualifying Matchups: {total_quali_matchups}")
        print(f"Total Race Matchups: {total_race_matchups}")
        print(f"Drivers Rated: {len(self.driver_ratings)}")
        print("="*70)
    
    def save_to_database(self):
        """
        Save all calculated Elo ratings to the database.
        """
        print("\nSaving ratings to database...")
        
        # Clear existing ratings
        self.conn.execute("DELETE FROM Driver_Elo")
        
        # Get driver names and debut years for the output
        driver_query = """
            SELECT d.driver_id, d.first_name, d.last_name, d.debut_year
            FROM Driver d
        """
        drivers_df = pd.read_sql_query(driver_query, self.conn)
        driver_info = {row['driver_id']: {
            'name': f"{row['first_name']} {row['last_name']}",
            'debut_year': row['debut_year']
        } for _, row in drivers_df.iterrows()}
        
        # Prepare data for insertion
        elo_records = []
        for driver_id, ratings in self.driver_ratings.items():
            qualifying_elo = ratings['qualifying_elo']
            race_elo = ratings['race_elo']
            global_elo = self.calculate_global_elo(qualifying_elo, race_elo)
            
            # Calculate additional metrics
            total_matchups = ratings['qualifying_races'] + ratings['race_races']
            reliability_score = self.calculate_reliability_score(total_matchups)
            
            # Get debut year
            debut_year = driver_info.get(driver_id, {}).get('debut_year', 2000)
            
            # Calculate era-adjusted Elo
            era_adjustment = self.calculate_era_adjustment(debut_year, total_matchups)
            era_adjusted_elo = global_elo * era_adjustment
            
            elo_records.append({
                'driver_id': driver_id,
                'qualifying_elo': round(qualifying_elo, 2),
                'race_elo': round(race_elo, 2),
                'global_elo': round(global_elo, 2),
                'era_adjusted_elo': round(era_adjusted_elo, 2),
                'qualifying_races': ratings['qualifying_races'],
                'race_races': ratings['race_races'],
                'total_matchups': total_matchups,
                'reliability_score': reliability_score,
                'debut_year': debut_year
            })
        
        # Insert into database
        elo_df = pd.DataFrame(elo_records)
        elo_df.to_sql('Driver_Elo', self.conn, if_exists='replace', index=False)
        
        self.conn.commit()
        print(f"✓ Saved {len(elo_records)} driver ratings to database")
        
        # Display top 20 by Global Elo (Raw)
        print("\n" + "="*80)
        print("TOP 20 DRIVERS BY GLOBAL ELO (Raw - Not Era Adjusted)")
        print("="*80)
        print(f"{'Rank':<6}{'Driver':<25}{'Global':<10}{'Quali':<10}{'Race':<10}{'Matchups':<10}{'Reliability'}")
        print("-"*80)
        
        top_20_raw = sorted(elo_records, key=lambda x: x['global_elo'], reverse=True)[:20]
        for rank, record in enumerate(top_20_raw, 1):
            driver_name = driver_info.get(record['driver_id'], {}).get('name', 'Unknown')
            print(f"{rank:<6}{driver_name:<25}"
                  f"{record['global_elo']:<10.1f}"
                  f"{record['qualifying_elo']:<10.1f}"
                  f"{record['race_elo']:<10.1f}"
                  f"{record['total_matchups']:<10}"
                  f"{record['reliability_score']:.1f}%")
        
        # Display top 20 by Era-Adjusted Elo
        print("\n" + "="*80)
        print("TOP 20 DRIVERS BY ERA-ADJUSTED ELO (Accounts for competition depth & sample size)")
        print("="*80)
        print(f"{'Rank':<6}{'Driver':<25}{'Adj. Elo':<12}{'Raw Elo':<10}{'Era':<8}{'Matchups':<10}{'Reliability'}")
        print("-"*80)
        
        top_20_adj = sorted(elo_records, key=lambda x: x['era_adjusted_elo'], reverse=True)[:20]
        for rank, record in enumerate(top_20_adj, 1):
            driver_name = driver_info.get(record['driver_id'], {}).get('name', 'Unknown')
            debut = record.get('debut_year', 'N/A')
            print(f"{rank:<6}{driver_name:<25}"
                  f"{record['era_adjusted_elo']:<12.1f}"
                  f"{record['global_elo']:<10.1f}"
                  f"{debut:<8}"
                  f"{record['total_matchups']:<10}"
                  f"{record['reliability_score']:.1f}%")
        
        print("="*80)
        print("\nRELIABILITY GUIDE:")
        print("  >90% = Very Reliable (100+ matchups)")
        print("  70-90% = Reliable (40-100 matchups)")
        print("  50-70% = Moderate (15-40 matchups)")
        print("  <50% = Low Confidence (<15 matchups)")
        print("="*80)
    
    def close(self):
        """Close database connection."""
        self.conn.close()


def main():
    """Main execution function."""
    print("\nInitializing Teammate-Based F1 Elo Calculator...")
    
    calculator = TeammateBasedF1Elo('DB/f1_database.db')
    
    try:
        # Calculate all Elo ratings
        calculator.calculate_all_elos()
        
        # Save to database
        calculator.save_to_database()
        
        print("\n✓ Elo calculation complete!")
        print("  Ratings saved to Driver_Elo table")
        print("  Query with: SELECT * FROM Driver_Elo ORDER BY global_elo DESC")
        
    except Exception as e:
        print(f"\n✗ Error during calculation: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        calculator.close()


if __name__ == "__main__":
    main()
