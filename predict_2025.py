"""
Predict 2025 F1 Race Results using trained XGBoost v5 model
Compare predictions vs actual results for completed races
Predict remaining races with proper analysis

Handles:
- New 2025 driver lineup (rookies: Antonelli, Hadjar, Bortoleto)
- Team changes (Hamilton to Ferrari, Sainz to Williams, etc.)
- Updated ELO ratings from database
"""

import pandas as pd
import numpy as np
import xgboost as xgb
import sqlite3
from datetime import datetime
from sklearn.metrics import mean_absolute_error


class F1_2025_Predictor:
    def __init__(self):
        self.model = None
        self.feature_list = None
        self.db_path = 'DB/f1_database.db'
        
        # 2025 driver mappings (scraped data uses different names)
        self.driver_name_mapping = {
            '#1 Max Verstappen': 'Max Verstappen',
            '#4 Lando Norris': 'Lando Norris',
            '#81 Oscar Piastri': 'Oscar Piastri',
            '#44 Lewis Hamilton': 'Lewis Hamilton',
            '#16 Charles Leclerc': 'Charles Leclerc',
            '#63 George Russell': 'George Russell',
            '#12 Andrea Kimi Antonelli': 'Andrea Kimi Antonelli',
            '#14 Fernando Alonso': 'Fernando Alonso',
            '#18 Lance Stroll': 'Lance Stroll',
            '#23 Alexander Albon': 'Alexander Albon',
            '#55 Carlos Sainz': 'Carlos Sainz',
            '#22 Yuki Tsunoda': 'Yuki Tsunoda',
            '#30 Liam Lawson': 'Liam Lawson',
            '#27 Nico Hulkenberg': 'Nico Hulkenberg',
            '#50 Oliver Bearman': 'Oliver Bearman',
            '#10 Pierre Gasly': 'Pierre Gasly',
            '#43 Franco Colapinto': 'Franco Colapinto',
            '#17 Esteban Ocon': 'Esteban Ocon',
            '#21 Isack Hadjar': 'Isack Hadjar',
            '#5 Gabriel Bortoleto': 'Gabriel Bortoleto',
        }
        
    def load_models(self):
        """Load trained XGBoost model"""
        print("Loading trained model...")
        
        # Load main XGBoost model
        self.model = xgb.XGBRegressor()
        self.model.load_model('models/xgboost_f1_predictor.json')
        
        # Load feature list
        with open('data/feature_list_v5.txt', 'r') as f:
            self.feature_list = [line.strip() for line in f.readlines()]
        
        print(f"  ✓ Loaded XGBoost model")
        print(f"  ✓ Loaded {len(self.feature_list)} features")
        
    def load_2025_race_results(self):
        """Load actual 2025 race results from scraped data"""
        print("\nLoading 2025 race data...")
        
        df_2025 = pd.read_csv('data/2025_race_results.csv')
        
        # Clean driver names
        df_2025['driver_name_clean'] = df_2025['driver_name'].map(self.driver_name_mapping)
        df_2025['driver_name_clean'] = df_2025['driver_name_clean'].fillna(df_2025['driver_name'])
        
        # Convert date (add year 2025)
        df_2025['race_date'] = pd.to_datetime(df_2025['race_date'] + ' 2025', format='%b %d %Y')
        
        print(f"  ✓ Loaded {len(df_2025)} results from {df_2025['race_name'].nunique()} races")
        print(f"  ✓ Date range: {df_2025['race_date'].min().strftime('%Y-%m-%d')} to {df_2025['race_date'].max().strftime('%Y-%m-%d')}")
        
        return df_2025
    
    def get_driver_team_elos(self):
        """Get current driver and team ELO ratings from database"""
        print("\nLoading ELO ratings from database...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Get driver ELOs
        driver_query = """
        SELECT 
            d.driver_id,
            d.first_name || ' ' || d.last_name as driver_name,
            t.team_name,
            COALESCE(de.qualifying_elo, 1500) as driver_quali_elo,
            COALESCE(de.race_elo, 1500) as driver_race_elo,
            COALESCE(de.global_elo, 1500) as driver_global_elo,
            COALESCE(de.reliability_score, 100.0) as driver_reliability
        FROM Driver d
        LEFT JOIN Team t ON d.current_team_id = t.team_id
        LEFT JOIN Driver_Elo de ON d.driver_id = de.driver_id
        WHERE d.current_team_id IS NOT NULL
        """
        
        df_drivers = pd.read_sql(driver_query, conn)
        
        # Get team ELOs (using estimated values based on 2024 performance)
        team_elos = {
            'Red Bull': {'quali': 1650, 'race': 1650, 'global': 1650, 'reliability': 98},
            'Ferrari': {'quali': 1600, 'race': 1600, 'global': 1600, 'reliability': 95},
            'McLaren': {'quali': 1620, 'race': 1620, 'global': 1620, 'reliability': 97},
            'Mercedes': {'quali': 1580, 'race': 1580, 'global': 1580, 'reliability': 96},
            'Aston Martin': {'quali': 1520, 'race': 1520, 'global': 1520, 'reliability': 94},
            'Williams': {'quali': 1480, 'race': 1480, 'global': 1480, 'reliability': 92},
            'RB': {'quali': 1500, 'race': 1500, 'global': 1500, 'reliability': 93},
            'RB F1 Team': {'quali': 1500, 'race': 1500, 'global': 1500, 'reliability': 93},
            'Haas': {'quali': 1490, 'race': 1490, 'global': 1490, 'reliability': 91},
            'Haas F1 Team': {'quali': 1490, 'race': 1490, 'global': 1490, 'reliability': 91},
            'Alpine': {'quali': 1510, 'race': 1510, 'global': 1510, 'reliability': 92},
            'Alpine F1 Team': {'quali': 1510, 'race': 1510, 'global': 1510, 'reliability': 92},
            'Sauber': {'quali': 1470, 'race': 1470, 'global': 1470, 'reliability': 90},
            'Kick Sauber': {'quali': 1470, 'race': 1470, 'global': 1470, 'reliability': 90},
        }
        
        conn.close()
        
        print(f"  ✓ Loaded ELO ratings for {len(df_drivers)} drivers")
        print(f"  ✓ Using estimated team ELOs (will be updated after ELO calculation)")
        
        return df_drivers, team_elos
    
    def prepare_minimal_features(self, df_2025, df_drivers, team_elos):
        """
        Prepare minimal feature set for prediction
        Note: This is a simplified version - full preprocessing would include:
        - Historical form (last 3 races)
        - Circuit characteristics
        - Championship standings
        - Weather conditions
        - Tire strategies
        """
        print("\nPreparing features for prediction...")
        
        # Merge driver ELOs
        df_2025 = df_2025.merge(
            df_drivers[['driver_name', 'driver_quali_elo', 'driver_race_elo', 
                       'driver_global_elo', 'driver_reliability', 'team_name']],
            left_on='driver_name_clean',
            right_on='driver_name',
            how='left'
        )
        
        # Add team ELOs
        df_2025['team_quali_elo'] = df_2025['team'].apply(
            lambda x: team_elos.get(x, {}).get('quali', 1500)
        )
        df_2025['team_race_elo'] = df_2025['team'].apply(
            lambda x: team_elos.get(x, {}).get('race', 1500)
        )
        df_2025['team_global_elo'] = df_2025['team'].apply(
            lambda x: team_elos.get(x, {}).get('global', 1500)
        )
        df_2025['team_reliability'] = df_2025['team'].apply(
            lambda x: team_elos.get(x, {}).get('reliability', 95.0)
        )
        
        # Fill missing values with defaults (for rookies)
        df_2025['driver_quali_elo'] = df_2025['driver_quali_elo'].fillna(1500)
        df_2025['driver_race_elo'] = df_2025['driver_race_elo'].fillna(1500)
        df_2025['driver_global_elo'] = df_2025['driver_global_elo'].fillna(1500)
        df_2025['driver_reliability'] = df_2025['driver_reliability'].fillna(100.0)
        
        # Convert grid_position to numeric (handle pit lane starts, etc.)
        df_2025['grid_position'] = pd.to_numeric(df_2025['grid_position'], errors='coerce').fillna(20).astype(int)
        df_2025['position'] = pd.to_numeric(df_2025['position'], errors='coerce').fillna(20).astype(int)
        
        # Create basic features
        df_2025['grid_normalized'] = (df_2025['grid_position'] - 1) / 19.0
        df_2025['dnf_flag'] = df_2025['status'].apply(lambda x: 0 if x == 'Finished' else 1)
        
        # Dummy features (would need real calculation)
        dummy_features = {
            'quali_gap_to_pole_ms': 0,
            'quali_gap_to_pole_pct': 0,
            'quali_position_pct': 0,
            'lap_consistency_score': 0,
            'pace_gap_to_fastest_pct': 0,
            'total_laps': 50,
            'num_pit_stops': 2,
            'avg_pit_duration_ms': 25000,
            'pit_efficiency': 0,
            'championship_points_before': 0,
            'championship_position_before': 10,
            'wins_before_race': 0,
            'championship_battle': 0,
            'sprint_position': 0,
            'sprint_position_change': 0,
            'has_sprint': 0,
            'driver_recent_position': 10,
            'driver_recent_points': 0,
            'team_recent_position': 10,
            'driver_recent_dnf_rate': 0,
            'team_recent_dnf_rate': 0,
            'drivers_ahead_better_elo': 0,
            'drivers_behind_better_elo': 0,
            'elo_gap_to_leader': 0,
            'team_elo_gap_to_leader': 0,
            'circuit_is_street': 0,
            'circuit_historical_dnf_rate': 0.1,
            'grid_midpack_risk': 0,
            'dnf_probability': 0.05,
            'circuit_overtake_difficulty': 5,
            'circuit_downforce_level': 5,
            'circuit_tire_deg_level': 5,
            'circuit_is_high_altitude': 0,
            'circuit_avg_speed_kph': 200,
            'driver_pace_differential': 0,
            'team_pace_differential': 0,
            'grid_pos_track_importance': 0.5,
            'elo_advantage_track_weighted': 0,
            'dnf_risk_street_circuit': 0,
            'pressure_on_difficult_track': 0,
            'team_downforce_match': 0,
            'position_change_this_race': 0,
            'recent_position_gain': 0,
        }
        
        for feature, default_value in dummy_features.items():
            df_2025[feature] = default_value
        
        print(f"  ✓ Created feature set with {len(self.feature_list)} features")
        print(f"  ⚠️  Using simplified features - full preprocessing recommended for better accuracy")
        
        return df_2025
    
    def predict_race_positions(self, df_race):
        """Predict positions for a single race"""
        # Ensure all features are present
        missing_features = [f for f in self.feature_list if f not in df_race.columns]
        for f in missing_features:
            df_race[f] = 0
        
        X = df_race[self.feature_list]
        predictions = self.model.predict(X)
        
        # Round to nearest position
        predictions = np.round(predictions).astype(int)
        
        # Clip to valid range (1-20)
        predictions = np.clip(predictions, 1, 20)
        
        # Adjust for duplicates (assign unique positions)
        pred_df = pd.DataFrame({
            'idx': range(len(predictions)),
            'pred': predictions,
            'grid': df_race['grid_position'].values
        })
        pred_df = pred_df.sort_values(['pred', 'grid'])
        pred_df['final_pred'] = range(1, len(predictions) + 1)
        pred_df = pred_df.sort_values('idx')
        
        return pred_df['final_pred'].values
    
    def evaluate_race_predictions(self, race_name, actual, predicted, df_race):
        """Evaluate predictions for a single race"""
        mae = mean_absolute_error(actual, predicted)
        
        # Accuracy metrics
        exact = (np.abs(actual - predicted) < 0.5).sum() / len(actual) * 100
        within_1 = (np.abs(actual - predicted) <= 1).sum() / len(actual) * 100
        within_2 = (np.abs(actual - predicted) <= 2).sum() / len(actual) * 100
        within_3 = (np.abs(actual - predicted) <= 3).sum() / len(actual) * 100
        
        # Classification metrics
        winner_correct = (predicted[actual == 1] == 1).any()
        podium_pred = set(df_race[predicted <= 3]['driver_name_clean'].values)
        podium_actual = set(df_race[actual <= 3]['driver_name_clean'].values)
        podium_overlap = len(podium_pred & podium_actual)
        
        return {
            'race_name': race_name,
            'mae': mae,
            'exact': exact,
            'within_1': within_1,
            'within_2': within_2,
            'within_3': within_3,
            'winner_correct': winner_correct,
            'podium_overlap': podium_overlap,
        }
    
    def display_race_prediction(self, race_name, race_date, df_race, actual, predicted):
        """Display human-readable prediction analysis for a race"""
        print("\n" + "="*80)
        print(f"🏁 {race_name}")
        print(f"📅 Date: {race_date.strftime('%B %d, %Y')}")
        print("="*80)
        
        # Create results DataFrame
        results = pd.DataFrame({
            'Driver': df_race['driver_name_clean'].values,
            'Team': df_race['team'].values,
            'Grid': df_race['grid_position'].values,
            'Actual': actual,
            'Predicted': predicted,
            'Error': np.abs(actual - predicted)
        })
        
        results = results.sort_values('Actual')
        
        # Highlight winner, podium, top 10
        print("\n📊 RACE RESULTS:")
        print("-" * 80)
        
        for idx, row in results.iterrows():
            driver = row['Driver']
            team = row['Team']
            grid = int(row['Grid'])
            actual_pos = int(row['Actual'])
            pred_pos = int(row['Predicted'])
            error = int(row['Error'])
            
            # Position change
            change = grid - actual_pos
            change_str = f"+{change}" if change > 0 else str(change)
            
            # Position indicator
            if actual_pos == 1:
                pos_icon = "🥇"
            elif actual_pos == 2:
                pos_icon = "🥈"
            elif actual_pos == 3:
                pos_icon = "🥉"
            elif actual_pos <= 10:
                pos_icon = "📍"
            else:
                pos_icon = "  "
            
            # Prediction accuracy
            if error == 0:
                acc_icon = "✓"
            elif error <= 2:
                acc_icon = "~"
            else:
                acc_icon = "✗"
            
            print(f"{pos_icon} P{actual_pos:2d} {acc_icon}  {driver:25s} {team:20s}  "
                  f"Grid: P{grid:2d} ({change_str:>3s})  Predicted: P{pred_pos:2d}  Error: {error:2d}")
        
        # Summary metrics
        mae = mean_absolute_error(actual, predicted)
        exact = (np.abs(actual - predicted) < 0.5).sum() / len(actual) * 100
        within_2 = (np.abs(actual - predicted) <= 2).sum() / len(actual) * 100
        
        winner_correct = (predicted[actual == 1] == 1).any()
        podium_pred = set(results[results['Predicted'] <= 3]['Driver'].values)
        podium_actual = set(results[results['Actual'] <= 3]['Driver'].values)
        podium_overlap = len(podium_pred & podium_actual)
        
        print("\n" + "-" * 80)
        print(f"📈 PREDICTION ACCURACY:")
        print(f"   Mean Absolute Error: {mae:.2f} positions")
        print(f"   Exact predictions: {exact:.1f}%")
        print(f"   Within ±2 positions: {within_2:.1f}%")
        print(f"   Winner predicted: {'Yes ✓' if winner_correct else 'No ✗'}")
        print(f"   Podium overlap: {podium_overlap}/3 drivers")
        
    def predict_remaining_races(self, df_drivers, team_elos):
        """
        Predict remaining 2025 races (not yet completed)
        
        Note: This requires:
        - Qualifying results
        - Current championship standings
        - Circuit data
        """
        print("\n" + "="*80)
        print("📅 UPCOMING RACES PREDICTION")
        print("="*80)
        
        print("\n⚠️  To predict upcoming races, you need:")
        print("   1. Qualifying results (grid positions)")
        print("   2. Current championship standings")
        print("   3. Circuit characteristics")
        print("   4. Recent form (last 3 races)")
        print("\n📝 Run the full preprocessing pipeline on upcoming race data")
        print("   then use this script to generate predictions.")
        
    def run_full_analysis(self):
        """Run complete 2025 prediction and analysis workflow"""
        print("\n" + "="*80)
        print("F1 2025 SEASON PREDICTION & ANALYSIS")
        print("XGBoost Model v5 with Updated Driver Lineup")
        print("="*80)
        
        # Load models and data
        self.load_models()
        df_2025 = self.load_2025_race_results()
        df_drivers, team_elos = self.get_driver_team_elos()
        
        # Prepare features
        df_2025 = self.prepare_minimal_features(df_2025, df_drivers, team_elos)
        
        # Analyze each race
        print("\n" + "="*80)
        print("ANALYZING COMPLETED 2025 RACES")
        print("="*80)
        
        all_metrics = []
        
        for race_name in sorted(df_2025['race_name'].unique()):
            df_race = df_2025[df_2025['race_name'] == race_name].copy()
            race_date = df_race['race_date'].iloc[0]
            
            # Get predictions
            predictions = self.predict_race_positions(df_race)
            actual = df_race['position'].values
            
            # Display results
            self.display_race_prediction(race_name, race_date, df_race, actual, predictions)
            
            # Store metrics
            metrics = self.evaluate_race_predictions(race_name, actual, predictions, df_race)
            all_metrics.append(metrics)
        
        # Overall season summary
        print("\n" + "="*80)
        print("📊 2025 SEASON PREDICTION SUMMARY")
        print("="*80)
        
        df_metrics = pd.DataFrame(all_metrics)
        
        print(f"\nTotal races analyzed: {len(df_metrics)}")
        print(f"\nAverage MAE: {df_metrics['mae'].mean():.2f} positions")
        print(f"Best MAE: {df_metrics['mae'].min():.2f} ({df_metrics.loc[df_metrics['mae'].idxmin(), 'race_name']})")
        print(f"Worst MAE: {df_metrics['mae'].max():.2f} ({df_metrics.loc[df_metrics['mae'].idxmax(), 'race_name']})")
        
        print(f"\nExact prediction rate: {df_metrics['exact'].mean():.1f}%")
        print(f"Within ±1 position: {df_metrics['within_1'].mean():.1f}%")
        print(f"Within ±2 positions: {df_metrics['within_2'].mean():.1f}%")
        print(f"Within ±3 positions: {df_metrics['within_3'].mean():.1f}%")
        
        winners_correct = df_metrics['winner_correct'].sum()
        print(f"\nRace winners predicted: {winners_correct}/{len(df_metrics)} ({winners_correct/len(df_metrics)*100:.1f}%)")
        print(f"Average podium overlap: {df_metrics['podium_overlap'].mean():.1f}/3 drivers")
        
        # Predict remaining races
        self.predict_remaining_races(df_drivers, team_elos)
        
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE!")
        print("="*80)


def main():
    """Main prediction pipeline"""
    predictor = F1_2025_Predictor()
    predictor.run_full_analysis()


if __name__ == "__main__":
    main()
