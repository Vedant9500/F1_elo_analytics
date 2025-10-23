"""
F1 Race Predictions - Human-Readable Output
Shows predicted winner, podium, and top 10 for each race
"""

import pandas as pd
import numpy as np
import xgboost as xgb
import pickle

class F1RacePredictor:
    def __init__(self):
        self.model = None
        self.dnf_model = None
        self.feature_columns = None
        
    def load_models(self):
        """Load trained models"""
        print("Loading trained models...")
        
        # Load XGBoost position model
        self.model = xgb.XGBRegressor()
        self.model.load_model('models/xgboost_f1_predictor.json')
        
        # Load feature list
        with open('data/feature_list_v5.txt', 'r') as f:
            self.feature_columns = [line.strip() for line in f.readlines()]
        
        print(f"  ✓ Loaded XGBoost model with {len(self.feature_columns)} features")
        
    def predict_race(self, race_df):
        """Predict finishing positions for a single race"""
        # Extract features
        X = race_df[self.feature_columns]
        
        # Predict positions
        predicted_positions = self.model.predict(X)
        
        # Create results dataframe
        results = race_df[['driver_name', 'team_name', 'grid_position']].copy()
        results['predicted_position'] = predicted_positions
        results['predicted_position_int'] = predicted_positions.round().astype(int)
        
        # Sort by predicted position
        results = results.sort_values('predicted_position')
        results['predicted_rank'] = range(1, len(results) + 1)
        
        return results
    
    def format_race_prediction(self, race_name, results):
        """Format race prediction in human-readable format"""
        print("\n" + "="*70)
        print(f"🏁 {race_name}")
        print("="*70)
        
        # Predicted Winner
        winner = results.iloc[0]
        print(f"\n🏆 PREDICTED WINNER: {winner['driver_name']} ({winner['team_name']})")
        print(f"   Starting: P{int(winner['grid_position'])}")
        print(f"   Confidence: {100 - abs(winner['predicted_position'] - 1) * 10:.1f}%")
        
        # Predicted Podium
        print(f"\n🥇 PREDICTED PODIUM:")
        for i in range(min(3, len(results))):
            driver = results.iloc[i]
            position_change = int(driver['grid_position']) - (i + 1)
            change_str = f"(+{position_change})" if position_change > 0 else f"({position_change})" if position_change < 0 else "(=)"
            print(f"   P{i+1}: {driver['driver_name']:<20} {driver['team_name']:<20} Grid: P{int(driver['grid_position'])} {change_str}")
        
        # Predicted Top 10 (Points)
        print(f"\n📊 PREDICTED TOP 10:")
        print(f"{'Pos':<4} {'Driver':<20} {'Team':<20} {'Grid':<6} {'Change'}")
        print("-" * 70)
        for i in range(min(10, len(results))):
            driver = results.iloc[i]
            position_change = int(driver['grid_position']) - (i + 1)
            change_str = f"+{position_change}" if position_change > 0 else f"{position_change}" if position_change < 0 else "="
            print(f"P{i+1:<3} {driver['driver_name']:<20} {driver['team_name']:<20} P{int(driver['grid_position']):<5} {change_str}")
        
        # Biggest Movers
        results_copy = results.copy()
        results_copy['position_change'] = results_copy['grid_position'] - results_copy['predicted_rank']
        biggest_gainers = results_copy.nlargest(3, 'position_change')
        
        print(f"\n📈 BIGGEST PREDICTED GAINERS:")
        for _, driver in biggest_gainers.iterrows():
            print(f"   {driver['driver_name']:<20} P{int(driver['grid_position'])} → P{int(driver['predicted_rank'])} (+{int(driver['position_change'])} places)")
        
        return results
    
    def predict_2024_test_races(self):
        """Predict all 2024 test set races and show results"""
        print("\n" + "="*70)
        print("F1 RACE PREDICTIONS - 2024 TEST SET")
        print("="*70)
        
        # Load test data
        test_df = pd.read_csv('data/test_data_v5.csv')
        
        print(f"\nLoaded {len(test_df)} results from {test_df['name'].nunique()} races in 2024")
        
        # Get unique races
        races = test_df['name'].unique()
        
        # Predict each race
        all_predictions = []
        
        for race_name in races:
            race_data = test_df[test_df['name'] == race_name].copy()
            predictions = self.predict_race(race_data)
            
            # Add actual results for comparison
            predictions['actual_position'] = race_data['position_target'].values
            
            # Format and display
            self.format_race_prediction(race_name, predictions)
            
            # Show accuracy if actual results available
            if 'actual_position' in predictions.columns:
                print(f"\n✅ ACCURACY CHECK:")
                
                # Winner correct?
                predicted_winner = predictions.iloc[0]['driver_name']
                actual_winner = predictions[predictions['actual_position'] == 1]['driver_name'].values
                if len(actual_winner) > 0 and predicted_winner == actual_winner[0]:
                    print(f"   🏆 Winner: CORRECT! ({predicted_winner})")
                else:
                    print(f"   🏆 Winner: INCORRECT (Predicted: {predicted_winner}, Actual: {actual_winner[0] if len(actual_winner) > 0 else 'N/A'})")
                
                # Podium accuracy
                predicted_podium = set(predictions.iloc[:3]['driver_name'])
                actual_podium = set(predictions[predictions['actual_position'] <= 3]['driver_name'])
                podium_overlap = len(predicted_podium & actual_podium)
                print(f"   🥇 Podium: {podium_overlap}/3 drivers correct ({podium_overlap/3*100:.0f}%)")
                
                # Average error
                mae = abs(predictions['predicted_rank'] - predictions['actual_position']).mean()
                print(f"   📊 Average Error: {mae:.2f} positions")
            
            all_predictions.append(predictions)
            
        return all_predictions
    
    def predict_hypothetical_race(self, race_name, circuit_id, driver_grid_positions):
        """
        Predict a hypothetical race given starting grid
        
        Args:
            race_name: str - Name of the race
            circuit_id: int - Circuit ID
            driver_grid_positions: dict - {driver_name: grid_position}
        """
        print("\n" + "="*70)
        print(f"🏁 HYPOTHETICAL RACE PREDICTION: {race_name}")
        print("="*70)
        
        # This would require building features from scratch
        # For now, show the expected format
        print("\n⚠️  To predict hypothetical races, you need:")
        print("   1. Driver Elo ratings (from database)")
        print("   2. Team Elo ratings (from database)")
        print("   3. Recent form data (last 5 races)")
        print("   4. Circuit characteristics (from circuit_features dict)")
        print("   5. Championship standings")
        print("   6. DNF probabilities")
        print("\n   Run preprocessing pipeline with new race data first.")


def main():
    """Main prediction interface"""
    print("\n" + "="*70)
    print("🏎️  F1 RACE PREDICTION SYSTEM - XGBoost v5")
    print("="*70)
    
    # Initialize predictor
    predictor = F1RacePredictor()
    predictor.load_models()
    
    # Predict 2024 test races
    print("\n📅 Predicting 2024 Season Races...")
    predictions = predictor.predict_2024_test_races()
    
    # Summary statistics
    print("\n" + "="*70)
    print("📊 OVERALL PREDICTION SUMMARY")
    print("="*70)
    
    all_results = pd.concat(predictions, ignore_index=True)
    
    # Overall accuracy
    winner_correct = 0
    podium_correct = 0
    total_races = len(predictions)
    
    for pred in predictions:
        # Winner
        predicted_winner = pred.iloc[0]['driver_name']
        actual_winner = pred[pred['actual_position'] == 1]['driver_name'].values
        if len(actual_winner) > 0 and predicted_winner == actual_winner[0]:
            winner_correct += 1
        
        # Podium
        predicted_podium = set(pred.iloc[:3]['driver_name'])
        actual_podium = set(pred[pred['actual_position'] <= 3]['driver_name'])
        if len(predicted_podium & actual_podium) >= 2:  # At least 2/3 correct
            podium_correct += 1
    
    overall_mae = abs(all_results['predicted_rank'] - all_results['actual_position']).mean()
    
    print(f"\n🏆 Winner Predictions:  {winner_correct}/{total_races} correct ({winner_correct/total_races*100:.1f}%)")
    print(f"🥇 Podium Predictions:  {podium_correct}/{total_races} had 2+ correct ({podium_correct/total_races*100:.1f}%)")
    print(f"📊 Average Error:       {overall_mae:.2f} positions")
    print(f"\n✅ Model Performance:")
    print(f"   - Exact predictions:     {(abs(all_results['predicted_rank'] - all_results['actual_position']) == 0).sum() / len(all_results) * 100:.1f}%")
    print(f"   - Within ±1 position:    {(abs(all_results['predicted_rank'] - all_results['actual_position']) <= 1).sum() / len(all_results) * 100:.1f}%")
    print(f"   - Within ±2 positions:   {(abs(all_results['predicted_rank'] - all_results['actual_position']) <= 2).sum() / len(all_results) * 100:.1f}%")
    print(f"   - Within ±3 positions:   {(abs(all_results['predicted_rank'] - all_results['actual_position']) <= 3).sum() / len(all_results) * 100:.1f}%")
    
    print("\n" + "="*70)
    print("🏁 PREDICTION COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    main()
