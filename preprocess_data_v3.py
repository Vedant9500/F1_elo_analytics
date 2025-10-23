"""
F1 Race Prediction - Enhanced Data Preprocessing v3
Using ALL available data from archive folder for maximum features
"""

import pandas as pd
import numpy as np
import sqlite3

class UltraEnhancedF1Preprocessor:
    def __init__(self, db_path='DB/f1_database.db', archive_path='archive/'):
        self.db_path = db_path
        self.archive_path = archive_path
        self.df = None
        
    def load_base_data(self):
        """Load base results from archive"""
        print("Loading base data from archive...")
        
        # Load main tables
        results = pd.read_csv(self.archive_path + 'results.csv')
        races = pd.read_csv(self.archive_path + 'races.csv')
        drivers = pd.read_csv(self.archive_path + 'drivers.csv')
        constructors = pd.read_csv(self.archive_path + 'constructors.csv')
        circuits = pd.read_csv(self.archive_path + 'circuits.csv')
        status = pd.read_csv(self.archive_path + 'status.csv')
        
        # Merge all (with suffixes to handle duplicate columns)
        self.df = results.merge(races, on='raceId', how='left', suffixes=('', '_race'))
        self.df = self.df.merge(drivers, on='driverId', how='left', suffixes=('', '_driver'))
        self.df = self.df.merge(constructors, left_on='constructorId', right_on='constructorId', how='left', suffixes=('', '_constructor'))
        self.df = self.df.merge(circuits, on='circuitId', how='left', suffixes=('', '_circuit'))
        self.df = self.df.merge(status, on='statusId', how='left', suffixes=('', '_status'))
        
        # Drop duplicate columns
        self.df = self.df.loc[:, ~self.df.columns.duplicated()]
        
        # Rename for consistency
        self.df = self.df.rename(columns={
            'resultId': 'result_id',
            'raceId': 'race_id',
            'driverId': 'driver_id',
            'constructorId': 'team_id',
            'circuitId': 'circuit_id',
            'grid': 'grid_position',
            'position': 'position',
            'positionOrder': 'position_order',
            'points_x': 'points',
            'fastestLapTime': 'fastest_lap_time',
            'year': 'season_year',
            'date': 'race_date',
            'name_x': 'race_name',
            'name_y': 'circuit_name',
            'status': 'status'
        })
        
        # Filter valid grid positions
        self.df = self.df[self.df['grid_position'].notna()].copy()
        
        # Create driver name
        self.df['driver_name'] = self.df['forename'] + ' ' + self.df['surname']
        self.df['team_name'] = self.df['name']
        
        print(f"  ✓ Loaded {len(self.df):,} race results")
        return self.df
    
    def load_elo_ratings(self):
        """Load Elo ratings from database"""
        print("Loading Elo ratings...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Load driver Elo
        driver_elo = pd.read_sql("""
            SELECT driver_id, qualifying_elo as driver_quali_elo, 
                   race_elo as driver_race_elo, global_elo as driver_global_elo,
                   era_adjusted_elo as driver_era_adjusted_elo,
                   reliability_score as driver_reliability
            FROM Driver_Elo
        """, conn)
        
        # Load team Elo
        team_elo = pd.read_sql("""
            SELECT team_id, qualifying_elo as team_quali_elo,
                   race_elo as team_race_elo, global_elo as team_global_elo,
                   era_adjusted_elo as team_era_adjusted_elo,
                   reliability_score as team_reliability
            FROM Team_Elo
        """, conn)
        
        conn.close()
        
        self.df = self.df.merge(driver_elo, on='driver_id', how='left')
        self.df = self.df.merge(team_elo, on='team_id', how='left')
        
        print(f"  ✓ Merged Elo ratings")
        return self.df
    
    def add_qualifying_features(self):
        """Extract qualifying session features"""
        print("Adding qualifying features...")
        
        quali = pd.read_csv(self.archive_path + 'qualifying.csv')
        
        # Convert lap times to milliseconds
        def time_to_ms(time_str):
            if pd.isna(time_str) or time_str == '\\N':
                return None
            try:
                parts = time_str.split(':')
                minutes = float(parts[0])
                seconds = float(parts[1])
                return (minutes * 60 + seconds) * 1000
            except:
                return None
        
        quali['q1_ms'] = quali['q1'].apply(time_to_ms)
        quali['q2_ms'] = quali['q2'].apply(time_to_ms)
        quali['q3_ms'] = quali['q3'].apply(time_to_ms)
        
        # Best quali time
        quali['best_quali_ms'] = quali[['q1_ms', 'q2_ms', 'q3_ms']].min(axis=1)
        
        # Gap to pole (fastest in session)
        race_pole_times = quali.groupby('raceId')['best_quali_ms'].min()
        quali['pole_time'] = quali['raceId'].map(race_pole_times)
        quali['quali_gap_to_pole_ms'] = quali['best_quali_ms'] - quali['pole_time']
        quali['quali_gap_to_pole_pct'] = (quali['quali_gap_to_pole_ms'] / quali['pole_time']) * 100
        
        # Quali position percentile
        quali['quali_position_pct'] = quali.groupby('raceId')['position'].rank(pct=True)
        
        # Prepare features for merge
        quali_features = quali[['raceId', 'driverId', 'quali_gap_to_pole_ms', 
                               'quali_gap_to_pole_pct', 'quali_position_pct']]
        
        # Merge
        self.df = self.df.merge(
            quali_features,
            left_on=['race_id', 'driver_id'],
            right_on=['raceId', 'driverId'],
            how='left'
        )
        
        # Drop duplicate ID columns
        if 'raceId' in self.df.columns:
            self.df = self.df.drop(columns=['raceId'])
        if 'driverId' in self.df.columns:
            self.df = self.df.drop(columns=['driverId'])
        
        # Fill missing with median
        self.df['quali_gap_to_pole_ms'] = self.df['quali_gap_to_pole_ms'].fillna(
            self.df['quali_gap_to_pole_ms'].median()
        )
        self.df['quali_gap_to_pole_pct'] = self.df['quali_gap_to_pole_pct'].fillna(2.0)
        self.df['quali_position_pct'] = self.df['quali_position_pct'].fillna(0.5)
        
        print(f"  ✓ Added 3 qualifying features")
        return self.df
    
    def add_lap_time_features(self):
        """Extract lap time consistency and pace features"""
        print("Adding lap time features...")
        
        lap_times = pd.read_csv(self.archive_path + 'lap_times.csv')
        
        # Calculate statistics per driver per race
        lap_stats = lap_times.groupby(['raceId', 'driverId'])['milliseconds'].agg([
            ('fastest_lap_ms', 'min'),
            ('avg_lap_ms', 'mean'),
            ('lap_consistency_std', 'std'),
            ('total_laps', 'count')
        ]).reset_index()
        
        # Consistency score (lower std = more consistent)
        lap_stats['lap_consistency_score'] = 1 / (1 + lap_stats['lap_consistency_std'] / 1000)
        
        # Pace vs field (gap to fastest lap in race)
        race_fastest = lap_times.groupby('raceId')['milliseconds'].min()
        lap_stats['race_fastest_ms'] = lap_stats['raceId'].map(race_fastest)
        lap_stats['pace_gap_to_fastest_ms'] = lap_stats['fastest_lap_ms'] - lap_stats['race_fastest_ms']
        lap_stats['pace_gap_to_fastest_pct'] = (lap_stats['pace_gap_to_fastest_ms'] / lap_stats['race_fastest_ms']) * 100
        
        # Merge
        lap_features = lap_stats[['raceId', 'driverId', 'lap_consistency_score', 
                                 'pace_gap_to_fastest_pct', 'total_laps']]
        
        self.df = self.df.merge(
            lap_features,
            left_on=['race_id', 'driver_id'],
            right_on=['raceId', 'driverId'],
            how='left'
        )
        
        # Drop duplicate ID columns
        self.df = self.df.drop(columns=['raceId', 'driverId'], errors='ignore')
        
        # Fill missing
        self.df['lap_consistency_score'] = self.df['lap_consistency_score'].fillna(0.5)
        self.df['pace_gap_to_fastest_pct'] = self.df['pace_gap_to_fastest_pct'].fillna(3.0)
        self.df['total_laps'] = self.df['total_laps'].fillna(0)
        
        print(f"  ✓ Added 3 lap time features")
        return self.df
    
    def add_pit_stop_features(self):
        """Extract pit stop strategy features"""
        print("Adding pit stop features...")
        
        pit_stops = pd.read_csv(self.archive_path + 'pit_stops.csv')
        
        # Aggregate per driver per race
        pit_stats = pit_stops.groupby(['raceId', 'driverId']).agg({
            'stop': 'count',  # Number of stops
            'milliseconds': ['mean', 'min', 'max']  # Duration stats
        }).reset_index()
        
        pit_stats.columns = ['raceId', 'driverId', 'num_pit_stops', 
                            'avg_pit_duration_ms', 'fastest_pit_ms', 'slowest_pit_ms']
        
        # Pit stop efficiency (compared to race average)
        race_avg_pit = pit_stops.groupby('raceId')['milliseconds'].mean()
        pit_stats['race_avg_pit_ms'] = pit_stats['raceId'].map(race_avg_pit)
        pit_stats['pit_efficiency'] = (pit_stats['race_avg_pit_ms'] - pit_stats['avg_pit_duration_ms']) / pit_stats['race_avg_pit_ms']
        
        # Merge
        pit_features = pit_stats[['raceId', 'driverId', 'num_pit_stops', 
                                 'avg_pit_duration_ms', 'pit_efficiency']]
        
        self.df = self.df.merge(
            pit_features,
            left_on=['race_id', 'driver_id'],
            right_on=['raceId', 'driverId'],
            how='left'
        )
        
        # Drop duplicate ID columns
        self.df = self.df.drop(columns=['raceId', 'driverId'], errors='ignore')
        
        # Fill missing (races without pit stop data)
        self.df['num_pit_stops'] = self.df['num_pit_stops'].fillna(2)  # Average F1 race
        self.df['avg_pit_duration_ms'] = self.df['avg_pit_duration_ms'].fillna(25000)
        self.df['pit_efficiency'] = self.df['pit_efficiency'].fillna(0)
        
        print(f"  ✓ Added 3 pit stop features")
        return self.df
    
    def add_driver_standings_features(self):
        """Add championship standings before race"""
        print("Adding driver standings features...")
        
        standings = pd.read_csv(self.archive_path + 'driver_standings.csv')
        
        # Keep only relevant columns
        standings_features = standings[['raceId', 'driverId', 'points', 'position', 'wins']]
        standings_features = standings_features.rename(columns={
            'points': 'championship_points_before',
            'position': 'championship_position_before',
            'wins': 'wins_before_race'
        })
        
        # Merge
        self.df = self.df.merge(
            standings_features,
            left_on=['race_id', 'driver_id'],
            right_on=['raceId', 'driverId'],
            how='left'
        )
        
        # Drop duplicate ID columns
        self.df = self.df.drop(columns=['raceId', 'driverId'], errors='ignore')
        
        # Fill first race of season
        self.df['championship_points_before'] = self.df['championship_points_before'].fillna(0)
        self.df['championship_position_before'] = self.df['championship_position_before'].fillna(10)
        self.df['wins_before_race'] = self.df['wins_before_race'].fillna(0)
        
        # Championship battle indicator
        self.df['championship_battle'] = (self.df['championship_position_before'] <= 3).astype(int)
        
        print(f"  ✓ Added 4 championship features")
        return self.df
    
    def add_sprint_race_features(self):
        """Add sprint race results if available"""
        print("Adding sprint race features...")
        
        sprints = pd.read_csv(self.archive_path + 'sprint_results.csv')
        
        # Sprint position and points
        sprint_features = sprints[['raceId', 'driverId', 'grid', 'position', 'points']]
        sprint_features = sprint_features.rename(columns={
            'grid': 'sprint_grid',
            'position': 'sprint_position',
            'points': 'sprint_points'
        })
        
        # Position change in sprint
        sprint_features['sprint_position_change'] = sprint_features['sprint_grid'] - sprint_features['sprint_position']
        
        # Merge
        self.df = self.df.merge(
            sprint_features[['raceId', 'driverId', 'sprint_position', 'sprint_position_change']],
            left_on=['race_id', 'driver_id'],
            right_on=['raceId', 'driverId'],
            how='left'
        )
        
        # Drop duplicate ID columns
        self.df = self.df.drop(columns=['raceId', 'driverId'], errors='ignore')
        
        # Fill missing (most races don't have sprints)
        self.df['has_sprint'] = self.df['sprint_position'].notna().astype(int)
        self.df['sprint_position'] = self.df['sprint_position'].fillna(0)
        self.df['sprint_position_change'] = self.df['sprint_position_change'].fillna(0)
        
        print(f"  ✓ Added 3 sprint race features")
        return self.df
    
    def add_rolling_form_features(self):
        """Calculate rolling performance metrics"""
        print("Adding rolling form features...")
        
        # Sort by driver and date
        self.df = self.df.sort_values(['driver_id', 'race_date'])
        
        # Driver recent positions (last 5 races)
        self.df['driver_recent_position'] = self.df.groupby('driver_id')['position_order'].transform(
            lambda x: x.shift(1).rolling(window=5, min_periods=1).mean()
        )
        
        # Driver recent points (last 5 races)
        self.df['driver_recent_points'] = self.df.groupby('driver_id')['points'].transform(
            lambda x: x.shift(1).rolling(window=5, min_periods=1).sum()
        )
        
        # Team recent positions
        self.df['team_recent_position'] = self.df.groupby('team_id')['position_order'].transform(
            lambda x: x.shift(1).rolling(window=5, min_periods=1).mean()
        )
        
        # DNF rate
        self.df['dnf_flag'] = (self.df['position_order'].isna() | (self.df['position_order'] > 20)).astype(int)
        self.df['driver_recent_dnf_rate'] = self.df.groupby('driver_id')['dnf_flag'].transform(
            lambda x: x.shift(1).rolling(window=10, min_periods=1).mean()
        )
        self.df['team_recent_dnf_rate'] = self.df.groupby('team_id')['dnf_flag'].transform(
            lambda x: x.shift(1).rolling(window=10, min_periods=1).mean()
        )
        
        # Fill NaN
        self.df['driver_recent_position'] = self.df['driver_recent_position'].fillna(10.0)
        self.df['driver_recent_points'] = self.df['driver_recent_points'].fillna(0.0)
        self.df['team_recent_position'] = self.df['team_recent_position'].fillna(10.0)
        self.df['driver_recent_dnf_rate'] = self.df['driver_recent_dnf_rate'].fillna(0.15)
        self.df['team_recent_dnf_rate'] = self.df['team_recent_dnf_rate'].fillna(0.15)
        
        print(f"  ✓ Added 5 rolling form features")
        return self.df
    
    def add_competitive_context_features(self):
        """Add competitive context within each race"""
        print("Adding competitive context features...")
        
        results = []
        
        for race_id, group in self.df.groupby('race_id', sort=False):
            group = group.sort_values('grid_position')
            
            grid_pos = group['grid_position'].values
            driver_elo = group['driver_global_elo'].values
            team_elo = group['team_global_elo'].values
            
            leader_driver_elo = driver_elo[0]
            leader_team_elo = team_elo[0]
            
            for idx, (i, row) in enumerate(group.iterrows()):
                # Drivers ahead with better Elo
                ahead_mask = grid_pos < row['grid_position']
                drivers_ahead_better_elo = (driver_elo[ahead_mask] > row['driver_global_elo']).sum() if ahead_mask.any() else 0
                
                # Drivers behind with better Elo  
                behind_mask = grid_pos > row['grid_position']
                drivers_behind_better_elo = (driver_elo[behind_mask] > row['driver_global_elo']).sum() if behind_mask.any() else 0
                
                # Gaps
                elo_gap_to_leader = leader_driver_elo - row['driver_global_elo']
                team_elo_gap_to_leader = leader_team_elo - row['team_global_elo']
                
                # Grid normalized
                grid_normalized = (row['grid_position'] - 1) / (len(group) - 1) if len(group) > 1 else 0
                
                results.append({
                    'result_id': row['result_id'],
                    'drivers_ahead_better_elo': drivers_ahead_better_elo,
                    'drivers_behind_better_elo': drivers_behind_better_elo,
                    'elo_gap_to_leader': elo_gap_to_leader,
                    'team_elo_gap_to_leader': team_elo_gap_to_leader,
                    'grid_normalized': grid_normalized
                })
        
        comp_df = pd.DataFrame(results)
        self.df = self.df.merge(comp_df, on='result_id', how='left')
        
        print(f"  ✓ Added 5 competitive context features")
        return self.df
    
    def create_target_variable(self):
        """Create target for prediction"""
        print("Creating target variable...")
        
        # Use position_order as target (handles DNFs better)
        self.df['position_target'] = self.df['position_order'].fillna(25)
        
        # Binary targets
        self.df['winner'] = (self.df['position_order'] == 1).astype(int)
        self.df['podium'] = (self.df['position_order'] <= 3).astype(int)
        self.df['points_finish'] = (self.df['position_order'] <= 10).astype(int)
        
        print(f"  ✓ Created target variable")
        return self.df
    
    def get_feature_columns(self):
        """Return list of feature columns"""
        features = [
            # Grid
            'grid_position',
            'grid_normalized',
            
            # Driver Elo
            'driver_quali_elo',
            'driver_race_elo',
            'driver_global_elo',
            'driver_era_adjusted_elo',
            'driver_reliability',
            
            # Team Elo
            'team_quali_elo',
            'team_race_elo',
            'team_global_elo',
            'team_era_adjusted_elo',
            'team_reliability',
            
            # Qualifying
            'quali_gap_to_pole_ms',
            'quali_gap_to_pole_pct',
            'quali_position_pct',
            
            # Lap times
            'lap_consistency_score',
            'pace_gap_to_fastest_pct',
            
            # Pit stops
            'num_pit_stops',
            'avg_pit_duration_ms',
            'pit_efficiency',
            
            # Championship
            'championship_points_before',
            'championship_position_before',
            'wins_before_race',
            'championship_battle',
            
            # Sprint
            'has_sprint',
            'sprint_position',
            'sprint_position_change',
            
            # Rolling form
            'driver_recent_position',
            'driver_recent_points',
            'team_recent_position',
            'driver_recent_dnf_rate',
            'team_recent_dnf_rate',
            
            # Competitive context
            'drivers_ahead_better_elo',
            'drivers_behind_better_elo',
            'elo_gap_to_leader',
            'team_elo_gap_to_leader',
            
            # Categorical
            'circuit_id',
            'season_year'
        ]
        
        return features
    
    def split_data(self):
        """Split chronologically"""
        print("Splitting data chronologically...")
        
        train = self.df[self.df['season_year'] <= 2021].copy()
        val = self.df[(self.df['season_year'] >= 2022) & (self.df['season_year'] <= 2023)].copy()
        test = self.df[self.df['season_year'] == 2024].copy()
        
        print(f"  ✓ Training:   {len(train):,} samples (1950-2021)")
        print(f"  ✓ Validation: {len(val):,} samples (2022-2023)")
        print(f"  ✓ Test:       {len(test):,} samples (2024)")
        
        return train, val, test
    
    def preprocess_all(self):
        """Run full preprocessing pipeline"""
        print("\n" + "="*70)
        print("ULTRA-ENHANCED F1 DATA PREPROCESSING v3")
        print("Using ALL archive data for maximum features")
        print("="*70)
        
        self.load_base_data()
        self.load_elo_ratings()
        self.add_qualifying_features()
        self.add_lap_time_features()
        self.add_pit_stop_features()
        self.add_driver_standings_features()
        self.add_sprint_race_features()
        self.add_rolling_form_features()
        self.add_competitive_context_features()
        self.create_target_variable()
        
        # Split
        train, val, test = self.split_data()
        
        # Save
        print("\nSaving preprocessed data...")
        train.to_csv('data/train_data_v3.csv', index=False)
        val.to_csv('data/val_data_v3.csv', index=False)
        test.to_csv('data/test_data_v3.csv', index=False)
        
        # Feature list
        features = self.get_feature_columns()
        with open('data/feature_list_v3.txt', 'w') as f:
            f.write('\n'.join(features))
        
        print(f"  ✓ Saved train_data_v3.csv")
        print(f"  ✓ Saved val_data_v3.csv")
        print(f"  ✓ Saved test_data_v3.csv")
        print(f"  ✓ Saved feature_list_v3.txt ({len(features)} features)")
        
        print("\n" + "="*70)
        print("PREPROCESSING COMPLETE!")
        print("="*70)
        print(f"\nTotal features: {len(features)}")
        print("\nNew feature categories from archive:")
        print("  - Qualifying: 3 features (gap to pole, position percentile)")
        print("  - Lap Times: 2 features (consistency, pace gap)")
        print("  - Pit Stops: 3 features (number, duration, efficiency)")
        print("  - Championship: 4 features (points, position, wins, battle flag)")
        print("  - Sprint: 3 features (position, position change, has_sprint flag)")
        print("  - Rolling Form: 5 features (recent positions, points, DNF rates)")
        print("  - Competitive Context: 5 features (Elo comparisons)")
        print("  - Driver/Team Elo: 12 features")
        print("  - Grid: 2 features")


if __name__ == "__main__":
    preprocessor = UltraEnhancedF1Preprocessor()
    preprocessor.preprocess_all()
