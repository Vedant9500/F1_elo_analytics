"""
Predict 2025 F1 Race Results using trained XGBoost v5 model
Compare predictions vs actual results for completed races
"""

import pandas as pd
import numpy as np
import xgboost as xgb
import pickle
from sklearn.metrics import mean_absolute_error

class F1_2025_Predictor:
    def __init__(self):
        self.model = None
        self.feature_list = None
        self.dnf_model = None
        
    def load_models(self):
        """Load trained XGBoost and DNF classifier"""
        print("Loading trained models...")
        
        # Load main XGBoost model
        self.model = xgb.XGBRegressor()
        self.model.load_model('models/xgboost_f1_predictor.json')
        
        # Load feature list
        with open('data/feature_list_v5.txt', 'r') as f:
            self.feature_list = [line.strip() for line in f.readlines()]
        
        print(f"  ✓ Loaded XGBoost model")
        print(f"  ✓ Loaded {len(self.feature_list)} features")
        
    def load_2025_data(self):
        """Load 2025 race data"""
        print("\nLoading 2025 race data...")
        
        # Load scraped 2025 results
        df_2025 = pd.read_csv('data/2025_race_results.csv')
        
        print(f"  ✓ Loaded {len(df_2025)} results from {df_2025['race_name'].nunique()} races")
        print(f"  ✓ Races: {df_2025['race_name'].unique()[:5]}... (+{df_2025['race_name'].nunique()-5} more)")
        
        return df_2025
    
    def prepare_2025_features(self, df_2025):
        """Prepare features for 2025 predictions"""
        print("\nPreparing 2025 features...")
        
        # This is a simplified version - in production you'd need to:
        # 1. Load historical Elo ratings for 2025 drivers/teams
        # 2. Calculate rolling form features
        # 3. Add circuit characteristics
        # 4. Calculate DNF probability
        
        # For now, let's use the test set as proxy to show the workflow
        print("  ⚠️  Using 2024 test set as proxy for feature engineering demo")
        print("  ⚠️  Full 2025 prediction requires running preprocessing pipeline on 2025 data")
        
        test_df = pd.read_csv('data/test_data_v5.csv')
        
        return test_df
    
    def predict_race_results(self, features_df):
        """Predict race finishing positions"""
        print("\nGenerating predictions...")
        
        X = features_df[self.feature_list]
        predictions = self.model.predict(X)
        
        # Round to nearest position
        predictions = np.round(predictions).astype(int)
        
        # Clip to valid range (1-20)
        predictions = np.clip(predictions, 1, 20)
        
        return predictions
    
    def evaluate_predictions(self, actual, predicted, df):
        """Evaluate prediction accuracy"""
        print("\n" + "="*70)
        print("PREDICTION EVALUATION - 2024 TEST SET")
        print("="*70)
        
        # Overall metrics
        mae = mean_absolute_error(actual, predicted)
        
        # Accuracy metrics
        exact = (np.abs(actual - predicted) < 0.5).sum() / len(actual) * 100
        within_1 = (np.abs(actual - predicted) <= 1).sum() / len(actual) * 100
        within_2 = (np.abs(actual - predicted) <= 2).sum() / len(actual) * 100
        within_3 = (np.abs(actual - predicted) <= 3).sum() / len(actual) * 100
        
        print(f"\n📊 Overall Performance:")
        print(f"  Mean Absolute Error:     {mae:.3f} positions")
        print(f"  Exact position:          {exact:.2f}%")
        print(f"  Within ±1 position:      {within_1:.2f}%")
        print(f"  Within ±2 positions:     {within_2:.2f}%")
        print(f"  Within ±3 positions:     {within_3:.2f}%")
        
        # Classification metrics
        winner_pred = (predicted == 1).astype(int)
        winner_actual = (actual == 1).astype(int)
        winner_acc = (winner_pred == winner_actual).sum() / len(winner_actual) * 100
        
        podium_pred = (predicted <= 3).astype(int)
        podium_actual = (actual <= 3).astype(int)
        podium_acc = (podium_pred == podium_actual).sum() / len(podium_actual) * 100
        
        points_pred = (predicted <= 10).astype(int)
        points_actual = (actual <= 10).astype(int)
        points_acc = (points_pred == points_actual).sum() / len(points_actual) * 100
        
        print(f"\n📊 Classification Accuracy:")
        print(f"  Winner prediction:       {winner_acc:.2f}%")
        print(f"  Podium prediction:       {podium_acc:.2f}%")
        print(f"  Points prediction:       {points_acc:.2f}%")
        
        # Show some example predictions
        print(f"\n📋 Sample Predictions (First 10 results):")
        sample_cols = ['grid_position', 'position_target']
        if 'driver_name' in df.columns:
            sample_cols.insert(0, 'driver_name')
        sample = df.head(10)[sample_cols].copy()
        sample['predicted'] = predicted[:10]
        sample['error'] = abs(sample['position_target'] - sample['predicted'])
        print(sample.to_string(index=False))
        
        # Worst predictions
        errors = pd.Series(abs(actual - predicted), index=df.index)
        worst_indices = errors.nlargest(10).index
        
        print(f"\n❌ Worst 10 Predictions:")
        worst_cols = ['driver_name', 'grid_position', 'position_target']
        worst = df.loc[worst_indices, worst_cols].copy()
        worst['predicted'] = predicted[worst_indices]
        worst['error'] = errors[worst_indices]
        print(worst.to_string(index=False))
        
    def predict_2025_full_workflow(self):
        """
        Full workflow for 2025 predictions
        (This is a template - requires running preprocessing on 2025 data)
        """
        print("\n" + "="*70)
        print("2025 RACE PREDICTION WORKFLOW")
        print("="*70)
        
        print("\n📝 To predict 2025 races, you need to:")
        print("\n1. Update preprocessing pipeline to include 2025 data:")
        print("   - Add 2025 race results to archive/results.csv")
        print("   - Add 2025 qualifying to archive/qualifying.csv")
        print("   - Add 2025 standings to archive/driver_standings.csv")
        
        print("\n2. Run preprocessing to generate 2025 features:")
        print("   - python preprocess_data_v3.py  # Update to include 2025")
        print("   - python create_v5_features.py  # Add interaction features")
        
        print("\n3. Load 2025 features and predict:")
        print("   - Load features for races you want to predict")
        print("   - Use this script to generate predictions")
        print("   - Compare predictions vs actual for completed races")
        
        print("\n4. For future races (not yet completed):")
        print("   - You'll need qualifying results first")
        print("   - Then extract features (grid position, Elo, form, etc.)")
        print("   - Generate predictions before race starts")


def main():
    """Main prediction pipeline"""
    print("\n" + "="*70)
    print("F1 2025 RACE PREDICTIONS - XGBoost v5")
    print("="*70)
    
    predictor = F1_2025_Predictor()
    
    # Load models
    predictor.load_models()
    
    # Load 2025 data
    # df_2025 = predictor.load_2025_data()
    
    # For demo, use 2024 test set
    test_df = pd.read_csv('data/test_data_v5.csv')
    
    # Predict
    predictions = predictor.predict_race_results(test_df)
    
    # Evaluate
    predictor.evaluate_predictions(
        test_df['position_target'].values,
        predictions,
        test_df
    )
    
    # Show workflow for full 2025 predictions
    predictor.predict_2025_full_workflow()
    
    print("\n" + "="*70)
    print("PREDICTION COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    main()
