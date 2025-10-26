"""
F1 Team Glicko-2 Rating System with Driver Skill Adjustment
Implements the academic "gold standard" approach for F1 team ratings

Key Features:
1. Glicko-2 system with Rating (r), Rating Deviation (RD), and Volatility (σ)
2. Driver skill adjustment - isolates pure team/car performance
3. Constructor lineage tracking (team rebrands maintain history)
4. Uncertainty quantification for statistically sound cross-era comparison

Methodology:
- Uses pre-calculated driver Elos to separate driver skill from car performance
- Formula: Car Performance = Raw Performance - Driver Skill Contribution
- Each race is a rating period with simultaneous H2H matchups
- Conservative rating (r - 2×RD) for fair cross-era comparison

References:
- Glicko-2: http://www.glicko.net/glicko/glicko2.pdf
- Academic methodology: team_elo_calc_help/Calculating F1 Team Elo Ratings.txt
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import os


class Glicko2Rating:
    """Glicko-2 rating with Rating (r), Rating Deviation (RD), and Volatility (σ)"""
    def __init__(self, rating=1500, rd=350, volatility=0.06):
        self.rating = rating
        self.rd = rd
        self.volatility = volatility
        
    def to_glicko_scale(self):
        mu = (self.rating - 1500) / 173.7178
        phi = self.rd / 173.7178
        return mu, phi
    
    def from_glicko_scale(self, mu, phi):
        self.rating = mu * 173.7178 + 1500
        self.rd = phi * 173.7178
    
    def conservative_rating(self):
        return self.rating - 2 * self.rd
    
    def __repr__(self):
        return f"Rating(r={self.rating:.1f}, RD={self.rd:.1f}, σ={self.volatility:.4f})"


class ConstructorLineage:
    """Maps team rebrands to persistent lineage IDs"""
    LINEAGE_MAP = {
        'jordan': 'jordan_lineage', 'midland': 'jordan_lineage', 'spyker': 'jordan_lineage',
        'force_india': 'jordan_lineage', 'racing_point': 'jordan_lineage', 'aston_martin': 'jordan_lineage',
        'stewart': 'redbull_lineage', 'jaguar': 'redbull_lineage', 'red_bull': 'redbull_lineage',
        'sauber': 'sauber_lineage', 'bmw_sauber': 'sauber_lineage', 'alfa': 'sauber_lineage',
        'toro_rosso': 'toro_rosso_lineage', 'alphatauri': 'toro_rosso_lineage', 'rb': 'toro_rosso_lineage',
        'benetton': 'renault_lineage', 'renault': 'renault_lineage', 'lotus_f1': 'renault_lineage', 'alpine': 'renault_lineage',
        'tyrrell': 'mercedes_lineage', 'bar': 'mercedes_lineage', 'honda': 'mercedes_lineage',
        'brawn': 'mercedes_lineage', 'mercedes': 'mercedes_lineage',
    }
    
    @classmethod
    def get_lineage(cls, constructor_ref):
        ref = constructor_ref.lower().replace(' ', '_').replace('-', '_')
        return cls.LINEAGE_MAP.get(ref, constructor_ref)


class TeamEloCalculator:
    def __init__(self, archive_path='archive', db_path='DB/f1_database.db', initial_rating=1500):
        self.archive_path = archive_path
        self.db_path = db_path
        self.initial_rating = initial_rating
        self.team_ratings = {}
        self.team_info = {}
        self.driver_elos = {}
        self.tau = 0.5
        
        self.load_data()
        
    def load_data(self):
        """Load archive data and driver Elos from database"""
        print("Loading data...")
        
        # Load constructors
        self.constructors_df = pd.read_csv(os.path.join(self.archive_path, 'constructors.csv'))
        print(f"✓ Loaded {len(self.constructors_df)} constructors")
        
        # Load results from archive (has grid positions)
        self.results_df = pd.read_csv(os.path.join(self.archive_path, 'results.csv'))
        print(f"✓ Loaded {len(self.results_df)} race results")
        
        # Load races
        self.races_df = pd.read_csv(os.path.join(self.archive_path, 'races.csv'))
        print(f"✓ Loaded {len(self.races_df)} races")
        
        # Load driver Elos from database
        conn = sqlite3.connect(self.db_path)
        driver_elo_df = pd.read_sql_query("""
            SELECT driver_id, global_elo, qualifying_elo, race_elo 
            FROM Driver_Elo
        """, conn)
        conn.close()
        
        self.driver_elos = {}
        for _, row in driver_elo_df.iterrows():
            self.driver_elos[row['driver_id']] = {
                'global': row['global_elo'],
                'qualifying': row['qualifying_elo'],
                'race': row['race_elo']
            }
        print(f"✓ Loaded {len(self.driver_elos)} driver Elos from database\n")
        
        # Initialize team ratings
        for _, constructor in self.constructors_df.iterrows():
            constructor_ref = constructor['constructorRef']
            lineage_id = ConstructorLineage.get_lineage(constructor_ref)
            
            if lineage_id not in self.team_ratings:
                self.team_ratings[lineage_id] = {
                    'qualifying': Glicko2Rating(),
                    'race': Glicko2Rating(),
                    'first_race_id': None,
                    'last_race_id': None,
                    'total_races': 0,
                    'qualifying_matchups': 0,
                    'race_matchups': 0
                }
                self.team_info[lineage_id] = {
                    'name': constructor['name'],
                    'constructor_ids': [],
                    'constructor_refs': []
                }
            
            if constructor['constructorId'] not in self.team_info[lineage_id]['constructor_ids']:
                self.team_info[lineage_id]['constructor_ids'].append(constructor['constructorId'])
                self.team_info[lineage_id]['constructor_refs'].append(constructor_ref)
                self.team_info[lineage_id]['name'] = constructor['name']
    
    def g_function(self, phi):
        return 1 / np.sqrt(1 + 3 * phi**2 / np.pi**2)
    
    def E_function(self, mu, mu_j, phi_j):
        exponent = -self.g_function(phi_j) * (mu - mu_j)
        exponent = np.clip(exponent, -500, 500)
        return 1 / (1 + np.exp(exponent))
    
    def update_glicko2(self, rating, opponents, outcomes):
        """Update Glicko-2 rating after a rating period"""
        if not opponents:
            rating.rd = min(350, np.sqrt(rating.rd**2 + rating.volatility**2))
            return
        
        mu, phi = rating.to_glicko_scale()
        
        # Calculate v (variance)
        v_sum = 0
        for opp in opponents:
            mu_j, phi_j = opp.to_glicko_scale()
            g_phi_j = self.g_function(phi_j)
            E_val = self.E_function(mu, mu_j, phi_j)
            v_sum += g_phi_j**2 * E_val * (1 - E_val)
        v = 1 / v_sum if v_sum > 0 else 1e10
        
        # Calculate delta
        delta_sum = 0
        for opp, outcome in zip(opponents, outcomes):
            mu_j, phi_j = opp.to_glicko_scale()
            g_phi_j = self.g_function(phi_j)
            E_val = self.E_function(mu, mu_j, phi_j)
            delta_sum += g_phi_j * (outcome - E_val)
        delta = v * delta_sum
        
        # Calculate new volatility
        sigma = rating.volatility
        a = np.log(sigma**2)
        
        def f(x):
            ex = np.exp(x)
            num1 = ex * (delta**2 - phi**2 - v - ex)
            denom1 = 2 * ((phi**2 + v + ex)**2)
            num2 = x - a
            denom2 = self.tau**2
            return num1/denom1 - num2/denom2
        
        A = a
        if delta**2 > phi**2 + v:
            B = np.log(delta**2 - phi**2 - v)
        else:
            k = 1
            while k < 100 and f(a - k * self.tau) < 0:
                k += 1
            B = a - k * self.tau
        
        fA = f(A)
        fB = f(B)
        
        epsilon = 0.000001
        max_iterations = 100
        iteration = 0
        while abs(B - A) > epsilon and iteration < max_iterations:
            C = A + (A - B) * fA / (fB - fA)
            fC = f(C)
            if fC * fB < 0:
                A = B
                fA = fB
            else:
                fA = fA / 2
            B = C
            fB = fC
            iteration += 1
        
        new_sigma = np.exp(A / 2)
        new_sigma = np.clip(new_sigma, 0.01, 0.5)
        
        # Update phi and mu
        phi_star = np.sqrt(phi**2 + new_sigma**2)
        new_phi = 1 / np.sqrt(1/phi_star**2 + 1/v)
        
        mu_update = 0
        for opp, outcome in zip(opponents, outcomes):
            mu_j, phi_j = opp.to_glicko_scale()
            g_phi_j = self.g_function(phi_j)
            E_val = self.E_function(mu, mu_j, phi_j)
            mu_update += g_phi_j * (outcome - E_val)
        new_mu = mu + new_phi**2 * mu_update
        
        rating.from_glicko_scale(new_mu, new_phi)
        rating.volatility = new_sigma
        
        # Apply bounds
        rating.rating = np.clip(rating.rating, 800, 2200)
        rating.rd = np.clip(rating.rd, 30, 350)
    
    def get_driver_adjusted_performance(self, race_id, constructor_id, session_type='race'):
        """
        Get team's performance ADJUSTED for driver skill
        This is the key innovation of Method B
        
        Raw Performance = Car Performance + Driver Skill
        Therefore: Car Performance = Raw Performance - Driver Skill
        """
        race_results = self.results_df[
            (self.results_df['raceId'] == race_id) &
            (self.results_df['constructorId'] == constructor_id)
        ]
        
        if race_results.empty:
            return None, 0
        
        adjusted_performances = []
        
        for _, result in race_results.iterrows():
            driver_id = result['driverId']
            
            # Get driver Elo
            if driver_id not in self.driver_elos:
                continue  # Skip if no driver Elo available
            
            driver_elo = self.driver_elos[driver_id].get(session_type if session_type != 'qualifying' else 'qualifying', 1500)
            
            if session_type == 'race':
                position = result.get('positionOrder', result.get('position'))
                if pd.notna(position) and position > 0:
                    # Convert position to performance score (lower position = better)
                    # Scale: position 1 = score 100, position 20 = score 0
                    raw_performance = max(0, 100 - (position - 1) * 5)
                    
                    # Adjust for driver skill
                    # Driver skill contribution: (driver_elo - 1500) / 10 
                    # This scaling factor can be tuned
                    driver_contribution = (driver_elo - 1500) / 10
                    
                    # Car performance = Raw - Driver contribution
                    car_performance = raw_performance - driver_contribution
                    adjusted_performances.append(car_performance)
            else:  # qualifying
                grid = result.get('grid')
                if pd.notna(grid) and grid > 0:
                    raw_performance = max(0, 100 - (grid - 1) * 5)
                    driver_contribution = (driver_elo - 1500) / 10
                    car_performance = raw_performance - driver_contribution
                    adjusted_performances.append(car_performance)
        
        if not adjusted_performances:
            return None, 0
        
        # Average the adjusted performances
        avg_adjusted = sum(adjusted_performances) / len(adjusted_performances)
        return avg_adjusted, len(adjusted_performances)
    
    def process_race_matchups(self, race_id):
        """Process H2H matchups using driver-adjusted performance"""
        race_constructors = self.results_df[self.results_df['raceId'] == race_id]['constructorId'].unique()
        
        lineage_performance = {}
        for constructor_id in race_constructors:
            constructor_row = self.constructors_df[self.constructors_df['constructorId'] == constructor_id]
            if constructor_row.empty:
                continue
            
            constructor_ref = constructor_row.iloc[0]['constructorRef']
            lineage_id = ConstructorLineage.get_lineage(constructor_ref)
            
            adjusted_perf, driver_count = self.get_driver_adjusted_performance(race_id, constructor_id, 'race')
            
            if adjusted_perf is not None and driver_count > 0:
                if lineage_id not in lineage_performance or adjusted_perf > lineage_performance[lineage_id]:
                    lineage_performance[lineage_id] = adjusted_perf
        
        if len(lineage_performance) < 2:
            return 0
        
        updates = {}
        for lineage_id in lineage_performance:
            updates[lineage_id] = {'opponents': [], 'outcomes': []}
        
        lineages = list(lineage_performance.keys())
        matchup_count = 0
        
        for i, lineage_a in enumerate(lineages):
            for lineage_b in lineages[i+1:]:
                perf_a = lineage_performance[lineage_a]
                perf_b = lineage_performance[lineage_b]
                
                # Higher adjusted performance = win
                if perf_a > perf_b:
                    outcome_a, outcome_b = 1.0, 0.0
                elif perf_a < perf_b:
                    outcome_a, outcome_b = 0.0, 1.0
                else:
                    outcome_a, outcome_b = 0.5, 0.5
                
                rating_a = self.team_ratings[lineage_a]['race']
                rating_b = self.team_ratings[lineage_b]['race']
                
                updates[lineage_a]['opponents'].append(rating_b)
                updates[lineage_a]['outcomes'].append(outcome_a)
                updates[lineage_b]['opponents'].append(rating_a)
                updates[lineage_b]['outcomes'].append(outcome_b)
                
                matchup_count += 1
        
        for lineage_id, update_data in updates.items():
            rating = self.team_ratings[lineage_id]['race']
            opponent_copies = [Glicko2Rating(r.rating, r.rd, r.volatility) for r in update_data['opponents']]
            self.update_glicko2(rating, opponent_copies, update_data['outcomes'])
            self.team_ratings[lineage_id]['race_matchups'] += len(update_data['outcomes'])
        
        return matchup_count
    
    def process_qualifying_matchups(self, race_id):
        """Process qualifying H2H matchups using driver-adjusted performance"""
        race_results = self.results_df[self.results_df['raceId'] == race_id]
        quali_constructors = race_results[race_results['grid'].notna() & (race_results['grid'] > 0)]['constructorId'].unique()
        
        lineage_performance = {}
        for constructor_id in quali_constructors:
            constructor_row = self.constructors_df[self.constructors_df['constructorId'] == constructor_id]
            if constructor_row.empty:
                continue
            
            constructor_ref = constructor_row.iloc[0]['constructorRef']
            lineage_id = ConstructorLineage.get_lineage(constructor_ref)
            
            adjusted_perf, driver_count = self.get_driver_adjusted_performance(race_id, constructor_id, 'qualifying')
            
            if adjusted_perf is not None and driver_count > 0:
                if lineage_id not in lineage_performance or adjusted_perf > lineage_performance[lineage_id]:
                    lineage_performance[lineage_id] = adjusted_perf
        
        if len(lineage_performance) < 2:
            return 0
        
        updates = {}
        for lineage_id in lineage_performance:
            updates[lineage_id] = {'opponents': [], 'outcomes': []}
        
        lineages = list(lineage_performance.keys())
        matchup_count = 0
        
        for i, lineage_a in enumerate(lineages):
            for lineage_b in lineages[i+1:]:
                perf_a = lineage_performance[lineage_a]
                perf_b = lineage_performance[lineage_b]
                
                if perf_a > perf_b:
                    outcome_a, outcome_b = 1.0, 0.0
                elif perf_a < perf_b:
                    outcome_a, outcome_b = 0.0, 1.0
                else:
                    outcome_a, outcome_b = 0.5, 0.5
                
                rating_a = self.team_ratings[lineage_a]['qualifying']
                rating_b = self.team_ratings[lineage_b]['qualifying']
                
                updates[lineage_a]['opponents'].append(rating_b)
                updates[lineage_a]['outcomes'].append(outcome_a)
                updates[lineage_b]['opponents'].append(rating_a)
                updates[lineage_b]['outcomes'].append(outcome_b)
                
                matchup_count += 1
        
        for lineage_id, update_data in updates.items():
            rating = self.team_ratings[lineage_id]['qualifying']
            opponent_copies = [Glicko2Rating(r.rating, r.rd, r.volatility) for r in update_data['opponents']]
            self.update_glicko2(rating, opponent_copies, update_data['outcomes'])
            self.team_ratings[lineage_id]['qualifying_matchups'] += len(update_data['outcomes'])
        
        return matchup_count
    
    def calculate_all_ratings(self):
        """Main calculation loop"""
        print("=" * 80)
        print("F1 TEAM GLICKO-2 RATING SYSTEM (DRIVER-ADJUSTED)")
        print("=" * 80)
        print(f"Initial Rating: {self.initial_rating}")
        print(f"Initial RD: 350 (high uncertainty)")
        print(f"System Volatility (τ): {self.tau}")
        print("Global Weights: 30% Qualifying, 70% Race")
        print("\nDriver Adjustment: Using driver Elo to isolate pure team/car performance")
        print("Formula: Car Performance = Raw Performance - Driver Skill Contribution")
        print("=" * 80 + "\n")
        
        total_quali_matchups = 0
        total_race_matchups = 0
        
        races = self.races_df.sort_values(['year', 'round']).iterrows()
        
        for idx, (_, race) in enumerate(races, 1):
            race_id = race['raceId']
            year = race['year']
            
            quali_matchups = self.process_qualifying_matchups(race_id)
            race_matchups = self.process_race_matchups(race_id)
            
            total_quali_matchups += quali_matchups
            total_race_matchups += race_matchups
            
            # Track participation
            race_constructors = self.results_df[self.results_df['raceId'] == race_id]['constructorId'].unique()
            for constructor_id in race_constructors:
                constructor_row = self.constructors_df[self.constructors_df['constructorId'] == constructor_id]
                if not constructor_row.empty:
                    constructor_ref = constructor_row.iloc[0]['constructorRef']
                    lineage_id = ConstructorLineage.get_lineage(constructor_ref)
                    
                    if self.team_ratings[lineage_id]['first_race_id'] is None:
                        self.team_ratings[lineage_id]['first_race_id'] = race_id
                    self.team_ratings[lineage_id]['last_race_id'] = race_id
                    self.team_ratings[lineage_id]['total_races'] += 1
            
            if idx % 100 == 0:
                print(f"Processed {idx} races (year {year})... (Q: {total_quali_matchups}, R: {total_race_matchups} matchups)")
        
        print("\n" + "=" * 80)
        print("CALCULATION COMPLETE")
        print(f"Total Races Processed: {len(self.races_df)}")
        print(f"Total Qualifying Matchups: {total_quali_matchups}")
        print(f"Total Race Matchups: {total_race_matchups}")
        print(f"Teams Rated: {len([t for t in self.team_ratings.values() if t['total_races'] > 0])}")
        print("=" * 80)
    
    def calculate_global_rating(self, lineage_id):
        quali_rating = self.team_ratings[lineage_id]['qualifying'].rating
        race_rating = self.team_ratings[lineage_id]['race'].rating
        return 0.3 * quali_rating + 0.7 * race_rating
    
    def calculate_conservative_global(self, lineage_id):
        quali = self.team_ratings[lineage_id]['qualifying']
        race = self.team_ratings[lineage_id]['race']
        quali_conservative = quali.rating - 2 * quali.rd
        race_conservative = race.rating - 2 * race.rd
        return 0.3 * quali_conservative + 0.7 * race_conservative
    
    def get_team_data_for_export(self):
        """Prepare team data for export/display"""
        team_data = []
        for lineage_id, ratings in self.team_ratings.items():
            if ratings['total_races'] == 0:
                continue
            
            info = self.team_info[lineage_id]
            global_rating = self.calculate_global_rating(lineage_id)
            conservative_rating = self.calculate_conservative_global(lineage_id)
            
            quali = ratings['qualifying']
            race = ratings['race']
            avg_rd = (quali.rd + race.rd) / 2
            
            team_data.append({
                'lineage_id': lineage_id,
                'name': info['name'],
                'global_rating': global_rating,
                'conservative_rating': conservative_rating,
                'quali_rating': quali.rating,
                'race_rating': race.rating,
                'avg_rd': avg_rd,
                'quali_rd': quali.rd,
                'race_rd': race.rd,
                'quali_volatility': quali.volatility,
                'race_volatility': race.volatility,
                'total_races': ratings['total_races'],
                'total_matchups': ratings['qualifying_matchups'] + ratings['race_matchups'],
                'constructor_ids': info['constructor_ids']
            })
        
        return team_data
    
    def save_to_database(self):
        """Save team ratings to database"""
        print("\n" + "=" * 80)
        print("SAVING TO DATABASE")
        print("=" * 80)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if Team_Elo_Glicko2 table exists, if not create it
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Team_Elo_Glicko2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lineage_id TEXT NOT NULL,
                team_name TEXT NOT NULL,
                qualifying_rating REAL NOT NULL,
                race_rating REAL NOT NULL,
                global_rating REAL NOT NULL,
                conservative_rating REAL NOT NULL,
                qualifying_rd REAL NOT NULL,
                race_rd REAL NOT NULL,
                avg_rd REAL NOT NULL,
                qualifying_volatility REAL NOT NULL,
                race_volatility REAL NOT NULL,
                total_races INTEGER NOT NULL,
                total_matchups INTEGER NOT NULL,
                constructor_ids TEXT NOT NULL,
                calculation_method TEXT DEFAULT 'Driver_Adjusted_Glicko2',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(lineage_id)
            )
        """)
        
        # Clear existing data
        cursor.execute("DELETE FROM Team_Elo_Glicko2 WHERE calculation_method = 'Driver_Adjusted_Glicko2'")
        
        team_data = self.get_team_data_for_export()
        saved_count = 0
        
        for team in team_data:
            # Convert constructor_ids list to comma-separated string
            constructor_ids_str = ','.join(map(str, team['constructor_ids']))
            
            cursor.execute("""
                INSERT OR REPLACE INTO Team_Elo_Glicko2 (
                    lineage_id, team_name, qualifying_rating, race_rating,
                    global_rating, conservative_rating, qualifying_rd, race_rd,
                    avg_rd, qualifying_volatility, race_volatility,
                    total_races, total_matchups, constructor_ids, calculation_method
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                team['lineage_id'],
                team['name'],
                round(team['quali_rating'], 2),
                round(team['race_rating'], 2),
                round(team['global_rating'], 2),
                round(team['conservative_rating'], 2),
                round(team['quali_rd'], 2),
                round(team['race_rd'], 2),
                round(team['avg_rd'], 2),
                round(team['quali_volatility'], 4),
                round(team['race_volatility'], 4),
                team['total_races'],
                team['total_matchups'],
                constructor_ids_str,
                'Driver_Adjusted_Glicko2'
            ))
            saved_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"✓ Saved {saved_count} team ratings to Team_Elo_Glicko2 table")
        print(f"✓ Calculation method: Driver_Adjusted_Glicko2")
        print("=" * 80)
    
    def display_top_teams(self, limit=25):
        """Display top teams"""
        team_data = self.get_team_data_for_export()
        df = pd.DataFrame(team_data)
        
        # Raw ratings
        df_raw = df.sort_values('global_rating', ascending=False).head(limit)
        
        print("\n" + "=" * 100)
        print(f"TOP {limit} TEAMS BY DRIVER-ADJUSTED GLICKO-2 RATING (Pure Car/Team Performance)")
        print("=" * 100)
        print(f"{'Rank':<6}{'Team':<25}{'Global':<10}{'Quali':<10}{'Race':<10}{'Avg RD':<10}{'Races':<8}")
        print("-" * 100)
        
        for rank, (_, row) in enumerate(df_raw.iterrows(), 1):
            print(f"{rank:<6}{row['name'][:24]:<25}"
                  f"{row['global_rating']:<10.1f}{row['quali_rating']:<10.1f}"
                  f"{row['race_rating']:<10.1f}{row['avg_rd']:<10.1f}{row['total_races']:<8}")
        
        # Conservative ratings
        df_conservative = df.sort_values('conservative_rating', ascending=False).head(limit)
        
        print("\n" + "=" * 100)
        print(f"TOP {limit} TEAMS BY CONSERVATIVE RATING (Accounts for Uncertainty)")
        print("=" * 100)
        print(f"{'Rank':<6}{'Team':<25}{'Conservative':<14}{'Global':<10}{'Avg RD':<10}{'Confidence':<12}")
        print("-" * 100)
        
        for rank, (_, row) in enumerate(df_conservative.iterrows(), 1):
            if row['avg_rd'] < 50:
                confidence = "Very High"
            elif row['avg_rd'] < 100:
                confidence = "High"
            elif row['avg_rd'] < 150:
                confidence = "Moderate"
            else:
                confidence = "Low"
            
            print(f"{rank:<6}{row['name'][:24]:<25}"
                  f"{row['conservative_rating']:<14.1f}{row['global_rating']:<10.1f}"
                  f"{row['avg_rd']:<10.1f}{confidence:<12}")
        
        print("\n" + "=" * 100)
        print("KEY DIFFERENCE FROM METHOD A (Raw H2H):")
        print("  These ratings are ADJUSTED for driver skill using pre-calculated driver Elos")
        print("  This isolates true car/team performance from driver talent")
        print("  Example: A great driver in a mediocre car won't inflate the team rating")
        print("=" * 100)


def main():
    print("\nInitializing F1 Team Glicko-2 Calculator (Driver-Adjusted)...")
    calculator = TeamEloCalculator()
    calculator.calculate_all_ratings()
    calculator.display_top_teams(limit=25)
    calculator.save_to_database()
    
    print("\n✓ Team Glicko-2 calculation complete!")
    print("\nThis implementation represents the academic gold standard:")
    print("  ✓ Isolates car performance from driver skill")
    print("  ✓ Uses Glicko-2 for uncertainty quantification")
    print("  ✓ Tracks constructor lineage through rebrands")
    print("  ✓ Provides statistically sound cross-era comparison")
    print("\nQuery the results with:")
    print("  SELECT * FROM Team_Elo_Glicko2 ORDER BY global_rating DESC;")
    print("  SELECT * FROM Team_Elo_Glicko2 ORDER BY conservative_rating DESC;")


if __name__ == "__main__":
    main()
