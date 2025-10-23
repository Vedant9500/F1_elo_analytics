"""
F1 Race Prediction - Data Preprocessing Pipeline
Prepares historical data (1950-2024) for ML model training
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

class F1DataPreprocessor:
    def __init__(self, db_path='DB/f1_database.db'):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def load_base_data(self):
        """Load race results with all necessary joins"""
        print("Loading base race results...")
        
        query = """
        SELECT 
            r.result_id,
            r.race_id,
            r.driver_id,
            r.team_id,
            r.grid_position,
            r.position,
            r.points,
            r.laps_completed,
            r.status,
            ra.season_year,
            ra.circuit_id,
            ra.race_name,
            ra.race_date,
            ra.round_number,
            d.first_name || ' ' || d.last_name as driver_name,
            t.team_name,
            c.circuit_name
        FROM Result r
        JOIN Race ra ON r.race_id = ra.race_id
        JOIN Driver d ON r.driver_id = d.driver_id
        JOIN Team t ON r.team_id = t.team_id
        JOIN Circuit c ON ra.circuit_id = c.circuit_id
        WHERE r.session_type = 'race'
        ORDER BY ra.season_year, ra.round_number, r.position
        """
        
        df = pd.read_sql(query, self.conn)
        print(f"  ✓ Loaded {len(df)} race results")
        return df
    
    def load_driver_elo(self):
        """Load driver Elo ratings"""
        print("Loading driver Elo ratings...")
        
        query = """
        SELECT 
            driver_id,
            qualifying_elo as driver_quali_elo,
            race_elo as driver_race_elo,
            global_elo as driver_global_elo,
            era_adjusted_elo as driver_era_elo,
            qualifying_races,
            race_races,
            total_matchups,
            reliability_score as driver_reliability,
            debut_year
        FROM Driver_Elo
        """
        
        df = pd.read_sql(query, self.conn)
        print(f"  ✓ Loaded Elo for {len(df)} drivers")
        return df
    
    def load_team_elo(self):
        """Load team Elo ratings"""
        print("Loading team Elo ratings...")
        
        query = """
        SELECT 
            team_id,
            qualifying_elo as team_quali_elo,
            race_elo as team_race_elo,
            global_elo as team_global_elo,
            era_adjusted_elo as team_era_elo,
            total_races as team_total_races,
            reliability_score as team_reliability,
            first_race_year,
            last_race_year
        FROM Team_Elo
        """
        
        df = pd.read_sql(query, self.conn)
        print(f"  ✓ Loaded Elo for {len(df)} teams")
        return df
    
    def merge_elo_ratings(self, df_results, df_driver_elo, df_team_elo):
        """Merge Elo ratings into results"""
        print("Merging Elo ratings...")
        
        # Merge driver Elo
        df = df_results.merge(df_driver_elo, on='driver_id', how='left')
        
        # Merge team Elo
        df = df.merge(df_team_elo, on='team_id', how='left')
        
        print(f"  ✓ Merged data: {len(df)} rows")
        return df
    
    def calculate_recent_form(self, df, window=5):
        """Calculate recent form (average position in last N races)"""
        print(f"Calculating recent form (last {window} races)...")
        
        # Sort by driver and chronological order
        df = df.sort_values(['driver_id', 'season_year', 'round_number'])
        
        # Calculate rolling average position for each driver
        df['recent_form_avg_position'] = df.groupby('driver_id')['position'].transform(
            lambda x: x.shift(1).rolling(window, min_periods=1).mean()
        )
        
        # For drivers with no history, use median position (11)
        df['recent_form_avg_position'].fillna(11, inplace=True)
        
        print(f"  ✓ Calculated recent form")
        return df
    
    def calculate_circuit_performance(self, df):
        """Calculate historical performance at each circuit"""
        print("Calculating circuit-specific performance...")
        
        # Driver's average position at this specific circuit (excluding current race)
        df = df.sort_values(['driver_id', 'circuit_id', 'season_year', 'round_number'])
        
        df['circuit_driver_avg_position'] = df.groupby(['driver_id', 'circuit_id'])['position'].transform(
            lambda x: x.shift(1).expanding().mean()
        )
        
        # For first-time at circuit, use overall average
        df['circuit_driver_avg_position'].fillna(df['recent_form_avg_position'], inplace=True)
        
        # Team's average position at this circuit
        df['circuit_team_avg_position'] = df.groupby(['team_id', 'circuit_id'])['position'].transform(
            lambda x: x.shift(1).expanding().mean()
        )
        df['circuit_team_avg_position'].fillna(11, inplace=True)
        
        print(f"  ✓ Calculated circuit performance")
        return df
    
    def calculate_teammate_comparison(self, df):
        """Calculate Elo difference vs teammate"""
        print("Calculating teammate comparisons...")
        
        # For each race, find teammate and calculate Elo difference
        teammates = df.groupby(['race_id', 'team_id']).apply(
            lambda x: pd.DataFrame({
                'driver_id': x['driver_id'].values,
                'teammate_elo_diff': [
                    x['driver_global_elo'].values[i] - x['driver_global_elo'].values[1-i]
                    if len(x) == 2 else 0
                    for i in range(len(x))
                ]
            })
        ).reset_index(drop=True)
        
        df = df.merge(teammates, on='driver_id', how='left')
        df['teammate_elo_diff'].fillna(0, inplace=True)
        
        print(f"  ✓ Calculated teammate comparisons")
        return df
    
    def calculate_championship_position(self, df):
        """Calculate driver's championship standing before this race"""
        print("Calculating championship positions...")
        
        # Sort chronologically
        df = df.sort_values(['season_year', 'round_number', 'position'])
        
        # Calculate cumulative points by season
        df['cumulative_points'] = df.groupby(['driver_id', 'season_year'])['points'].cumsum()
        
        # Shift to get points BEFORE this race
        df['points_before_race'] = df.groupby(['driver_id', 'season_year'])['cumulative_points'].shift(1).fillna(0)
        
        # Calculate championship position (rank within season before this race)
        df['championship_position'] = df.groupby(['race_id'])['points_before_race'].rank(
            method='min', ascending=False
        )
        
        print(f"  ✓ Calculated championship positions")
        return df
    
    def create_target_variable(self, df):
        """Create clean target variable for position"""
        print("Creating target variable...")
        
        # Position is already there, but handle DNFs
        # For DNF, we can either:
        # 1. Exclude from training (most common)
        # 2. Predict position as 21 (last place)
        # 3. Separate DNF classifier
        
        # We'll exclude DNFs from training (option 1)
        df['is_dnf'] = df['position'].isna()
        
        # Create binary targets for classification alternatives
        df['is_winner'] = (df['position'] == 1).astype(int)
        df['is_podium'] = (df['position'] <= 3).astype(int)
        df['is_points'] = (df['position'] <= 10).astype(int)
        
        print(f"  ✓ Created target variables")
        print(f"    - Finished races: {(~df['is_dnf']).sum()}")
        print(f"    - DNFs: {df['is_dnf'].sum()}")
        return df
    
    def handle_missing_data(self, df):
        """Handle missing values"""
        print("Handling missing data...")
        
        # Grid position: If missing (back of grid penalties, etc.), use last position
        df['grid_position'] = pd.to_numeric(df['grid_position'], errors='coerce')
        df['grid_position'].fillna(20, inplace=True)
        
        # Elo ratings: If driver is new and has no Elo, use default 1500
        elo_columns = [col for col in df.columns if 'elo' in col.lower()]
        for col in elo_columns:
            df[col].fillna(1500, inplace=True)
        
        print(f"  ✓ Handled missing data")
        return df
    
    def create_feature_set(self, df):
        """Select final feature set for model"""
        print("Creating feature set...")
        
        features = [
            # Driver Elo features
            'driver_quali_elo',
            'driver_race_elo',
            'driver_global_elo',
            'driver_era_elo',
            'driver_reliability',
            
            # Team Elo features
            'team_quali_elo',
            'team_race_elo',
            'team_global_elo',
            'team_era_elo',
            'team_reliability',
            
            # Race context
            'grid_position',
            'season_year',
            
            # Engineered features
            'recent_form_avg_position',
            'circuit_driver_avg_position',
            'circuit_team_avg_position',
            'teammate_elo_diff',
            'championship_position',
            
            # Categorical features
            'circuit_id',
            'driver_id',
            'team_id'
        ]
        
        # Target
        target = 'position'
        
        # Filter to only rows with valid position (exclude DNFs for training)
        df_clean = df[~df['is_dnf']].copy()
        
        # Additional targets
        additional_targets = ['is_winner', 'is_podium', 'is_points']
        
        print(f"  ✓ Feature set created: {len(features)} features")
        print(f"    - Training samples: {len(df_clean)}")
        
        return df_clean, features, target, additional_targets
    
    def split_train_val_test(self, df, train_end_year=2021, val_end_year=2023):
        """Split data chronologically"""
        print("Splitting data into train/val/test...")
        
        train_df = df[df['season_year'] <= train_end_year]
        val_df = df[(df['season_year'] > train_end_year) & (df['season_year'] <= val_end_year)]
        test_df = df[df['season_year'] > val_end_year]
        
        print(f"  ✓ Split complete:")
        print(f"    - Training:   {len(train_df)} samples ({train_df['season_year'].min()}-{train_df['season_year'].max()})")
        print(f"    - Validation: {len(val_df)} samples ({val_df['season_year'].min()}-{val_df['season_year'].max()})")
        print(f"    - Test:       {len(test_df)} samples ({test_df['season_year'].min()}-{test_df['season_year'].max()})")
        
        return train_df, val_df, test_df
    
    def preprocess_all(self):
        """Run full preprocessing pipeline"""
        print("="*70)
        print("F1 RACE PREDICTION - DATA PREPROCESSING")
        print("="*70)
        
        self.connect()
        
        try:
            # Load data
            df_results = self.load_base_data()
            df_driver_elo = self.load_driver_elo()
            df_team_elo = self.load_team_elo()
            
            # Merge Elo ratings
            df = self.merge_elo_ratings(df_results, df_driver_elo, df_team_elo)
            
            # Feature engineering
            df = self.calculate_recent_form(df, window=5)
            df = self.calculate_circuit_performance(df)
            df = self.calculate_teammate_comparison(df)
            df = self.calculate_championship_position(df)
            
            # Target variable
            df = self.create_target_variable(df)
            
            # Handle missing data
            df = self.handle_missing_data(df)
            
            # Create feature set
            df_clean, features, target, additional_targets = self.create_feature_set(df)
            
            # Split data
            train_df, val_df, test_df = self.split_train_val_test(df_clean)
            
            print("\n" + "="*70)
            print("PREPROCESSING COMPLETE")
            print("="*70)
            
            # Save processed data
            print("\nSaving processed data...")
            train_df.to_csv('data/train_data.csv', index=False)
            val_df.to_csv('data/val_data.csv', index=False)
            test_df.to_csv('data/test_data.csv', index=False)
            
            # Save feature list
            with open('data/feature_list.txt', 'w') as f:
                f.write('\n'.join(features))
            
            print("  ✓ Saved train_data.csv")
            print("  ✓ Saved val_data.csv")
            print("  ✓ Saved test_data.csv")
            print("  ✓ Saved feature_list.txt")
            
            return train_df, val_df, test_df, features, target
            
        finally:
            self.close()


def main():
    preprocessor = F1DataPreprocessor()
    train_df, val_df, test_df, features, target = preprocessor.preprocess_all()
    
    print("\n" + "="*70)
    print("READY FOR MODEL TRAINING")
    print("="*70)
    print(f"Features: {len(features)}")
    print(f"Target: {target}")
    print(f"\nNext step: Run train_model.py to train LightGBM model")


if __name__ == "__main__":
    main()
