"""
F1 Race Prediction - XGBoost Model Training
Train XGBoost regressor to predict race finishing positions
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import os
from datetime import datetime

class F1XGBoostTrainer:
    def __init__(self):
        self.model = None
        self.feature_names = None
        self.best_params = None
        
    def load_data(self):
        """Load preprocessed training, validation, and test data"""
        print("Loading data...")
        
        train_df = pd.read_csv('data/train_data.csv')
        val_df = pd.read_csv('data/val_data.csv')
        test_df = pd.read_csv('data/test_data.csv')
        
        # Load feature list
        with open('data/feature_list.txt', 'r') as f:
            features = [line.strip() for line in f.readlines()]
        
        print(f"  ✓ Training:   {len(train_df):,} samples")
        print(f"  ✓ Validation: {len(val_df):,} samples")
        print(f"  ✓ Test:       {len(test_df):,} samples")
        print(f"  ✓ Features:   {len(features)}")
        
        return train_df, val_df, test_df, features
    
    def prepare_features(self, df, features, target='position'):
        """Prepare X and y from dataframe"""
        X = df[features].copy()
        y = df[target].copy()
        
        # Categorical features are already numeric IDs, just ensure they're integers
        categorical_features = ['circuit_id', 'driver_id', 'team_id']
        for cat_col in categorical_features:
            if cat_col in X.columns:
                X[cat_col] = X[cat_col].astype(int)
        
        return X, y
    
    def train_model(self, X_train, y_train, X_val, y_val):
        """Train XGBoost model with optimal hyperparameters"""
        print("\nTraining XGBoost model...")
        print("="*70)
        
        # XGBoost parameters optimized for position prediction
        params = {
            # Tree parameters
            'max_depth': 8,                    # Depth of trees
            'learning_rate': 0.05,             # Step size shrinkage
            'n_estimators': 500,               # Number of boosting rounds
            'min_child_weight': 3,             # Minimum sum of weights in child
            
            # Regularization
            'gamma': 0.1,                      # Minimum loss reduction for split
            'subsample': 0.8,                  # Fraction of samples per tree
            'colsample_bytree': 0.8,          # Fraction of features per tree
            'reg_alpha': 0.1,                  # L1 regularization
            'reg_lambda': 1.0,                 # L2 regularization
            
            # Objective and evaluation
            'objective': 'reg:squarederror',   # Regression task
            'eval_metric': 'mae',              # Mean Absolute Error
            
            # System
            'tree_method': 'hist',             # Fast histogram algorithm
            'random_state': 42,
            'n_jobs': -1,                      # Use all CPU cores
            'verbosity': 1
        }
        
        print("Hyperparameters:")
        for key, value in params.items():
            print(f"  {key}: {value}")
        
        # Add early stopping to params
        params['early_stopping_rounds'] = 50
        
        # Create model
        self.model = xgb.XGBRegressor(**params)
        
        # Train
        print("\nTraining...")
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_train, y_train), (X_val, y_val)],
            verbose=50  # Print every 50 iterations
        )
        
        print(f"\n✓ Training complete!")
        try:
            print(f"  Best iteration: {self.model.best_iteration}")
            print(f"  Best score: {self.model.best_score:.4f}")
        except AttributeError:
            print(f"  Completed all {params['n_estimators']} iterations")
        
        self.feature_names = X_train.columns.tolist()
        self.best_params = params
        
        return self.model
    
    def evaluate_model(self, X, y, dataset_name="Dataset"):
        """Evaluate model performance"""
        print(f"\n{dataset_name} Evaluation:")
        print("-"*70)
        
        # Predictions
        y_pred = self.model.predict(X)
        
        # Clip predictions to valid range (1-20)
        y_pred_clipped = np.clip(y_pred, 1, 20)
        
        # Calculate metrics
        mae = mean_absolute_error(y, y_pred_clipped)
        rmse = np.sqrt(mean_squared_error(y, y_pred_clipped))
        r2 = r2_score(y, y_pred_clipped)
        
        print(f"  MAE (Mean Absolute Error):  {mae:.3f} positions")
        print(f"  RMSE (Root Mean Squared):   {rmse:.3f} positions")
        print(f"  R² Score:                   {r2:.4f}")
        
        # Position accuracy metrics
        correct_position = np.sum(np.abs(y - y_pred_clipped) < 0.5)
        within_1 = np.sum(np.abs(y - y_pred_clipped) <= 1)
        within_2 = np.sum(np.abs(y - y_pred_clipped) <= 2)
        within_3 = np.sum(np.abs(y - y_pred_clipped) <= 3)
        
        total = len(y)
        print(f"\nPosition Accuracy:")
        print(f"  Exact position:    {correct_position/total*100:.2f}% ({correct_position:,}/{total:,})")
        print(f"  Within ±1 pos:     {within_1/total*100:.2f}% ({within_1:,}/{total:,})")
        print(f"  Within ±2 pos:     {within_2/total*100:.2f}% ({within_2:,}/{total:,})")
        print(f"  Within ±3 pos:     {within_3/total*100:.2f}% ({within_3:,}/{total:,})")
        
        # Winner prediction accuracy
        actual_winners = (y == 1)
        pred_winners = (y_pred_clipped <= 1.5)  # Predicted as P1
        winner_accuracy = np.sum(actual_winners & pred_winners) / np.sum(actual_winners) * 100
        print(f"\n  Winner prediction accuracy: {winner_accuracy:.2f}%")
        
        # Podium prediction (top 3)
        actual_podium = (y <= 3)
        pred_podium = (y_pred_clipped <= 3.5)
        podium_accuracy = np.sum(actual_podium & pred_podium) / np.sum(actual_podium) * 100
        print(f"  Podium prediction accuracy: {podium_accuracy:.2f}%")
        
        # Points prediction (top 10)
        actual_points = (y <= 10)
        pred_points = (y_pred_clipped <= 10.5)
        points_accuracy = np.sum(actual_points & pred_points) / np.sum(actual_points) * 100
        print(f"  Points prediction accuracy: {points_accuracy:.2f}%")
        
        return {
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'exact_accuracy': correct_position/total,
            'within_1': within_1/total,
            'within_2': within_2/total,
            'within_3': within_3/total,
            'winner_accuracy': winner_accuracy/100,
            'podium_accuracy': podium_accuracy/100,
            'points_accuracy': points_accuracy/100,
            'predictions': y_pred_clipped
        }
    
    def plot_feature_importance(self, top_n=20):
        """Plot feature importance"""
        print(f"\nPlotting top {top_n} feature importances...")
        
        # Get feature importance
        importance = self.model.feature_importances_
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        # Plot
        plt.figure(figsize=(10, 8))
        top_features = feature_importance.head(top_n)
        plt.barh(range(len(top_features)), top_features['importance'])
        plt.yticks(range(len(top_features)), top_features['feature'])
        plt.xlabel('Importance')
        plt.title(f'Top {top_n} Feature Importances - XGBoost')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        
        # Save plot
        os.makedirs('plots', exist_ok=True)
        plt.savefig('plots/feature_importance_xgboost.png', dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved to plots/feature_importance_xgboost.png")
        
        # Print top 10
        print(f"\nTop 10 Most Important Features:")
        for idx, row in feature_importance.head(10).iterrows():
            print(f"  {row['feature']:30s}: {row['importance']:.4f}")
        
        return feature_importance
    
    def plot_predictions_vs_actual(self, y_true, y_pred, dataset_name="Test"):
        """Plot predicted vs actual positions"""
        print(f"\nPlotting predictions vs actual for {dataset_name} set...")
        
        plt.figure(figsize=(10, 10))
        
        # Scatter plot with transparency
        plt.scatter(y_true, y_pred, alpha=0.3, s=10)
        
        # Perfect prediction line
        plt.plot([1, 20], [1, 20], 'r--', label='Perfect Prediction', linewidth=2)
        
        # ±2 position bands
        plt.plot([1, 20], [3, 22], 'g--', alpha=0.5, label='±2 positions')
        plt.plot([1, 20], [-1, 18], 'g--', alpha=0.5)
        
        plt.xlabel('Actual Position')
        plt.ylabel('Predicted Position')
        plt.title(f'XGBoost Predictions vs Actual - {dataset_name} Set')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xlim(0, 21)
        plt.ylim(0, 21)
        plt.tight_layout()
        
        plt.savefig(f'plots/predictions_vs_actual_{dataset_name.lower()}_xgboost.png', 
                   dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved to plots/predictions_vs_actual_{dataset_name.lower()}_xgboost.png")
    
    def save_model(self):
        """Save trained model"""
        print("\nSaving model...")
        
        os.makedirs('models', exist_ok=True)
        
        # Save XGBoost model
        model_path = 'models/xgboost_f1_predictor.json'
        self.model.save_model(model_path)
        
        # Save metadata
        metadata = {
            'feature_names': self.feature_names,
            'params': self.best_params,
            'training_date': datetime.now().isoformat()
        }
        
        with open('models/xgboost_metadata.pkl', 'wb') as f:
            pickle.dump(metadata, f)
        
        print(f"  ✓ Model saved to {model_path}")
        print(f"  ✓ Metadata saved to models/xgboost_metadata.pkl")
    
    def load_model(self):
        """Load trained model"""
        print("Loading model...")
        
        model_path = 'models/xgboost_f1_predictor.json'
        self.model = xgb.XGBRegressor()
        self.model.load_model(model_path)
        
        with open('models/xgboost_metadata.pkl', 'rb') as f:
            metadata = pickle.load(f)
        
        self.feature_names = metadata['feature_names']
        self.best_params = metadata['params']
        
        print(f"  ✓ Model loaded from {model_path}")


def main():
    print("="*70)
    print("F1 RACE PREDICTION - XGBOOST MODEL TRAINING")
    print("="*70)
    
    # Initialize trainer
    trainer = F1XGBoostTrainer()
    
    # Load data
    train_df, val_df, test_df, features = trainer.load_data()
    
    # Prepare features
    X_train, y_train = trainer.prepare_features(train_df, features)
    X_val, y_val = trainer.prepare_features(val_df, features)
    X_test, y_test = trainer.prepare_features(test_df, features)
    
    # Train model
    trainer.train_model(X_train, y_train, X_val, y_val)
    
    # Evaluate on all datasets
    print("\n" + "="*70)
    print("MODEL EVALUATION")
    print("="*70)
    
    train_metrics = trainer.evaluate_model(X_train, y_train, "Training")
    val_metrics = trainer.evaluate_model(X_val, y_val, "Validation")
    test_metrics = trainer.evaluate_model(X_test, y_test, "Test")
    
    # Feature importance
    feature_importance = trainer.plot_feature_importance(top_n=20)
    
    # Prediction plots
    trainer.plot_predictions_vs_actual(y_test, test_metrics['predictions'], "Test")
    
    # Save model
    trainer.save_model()
    
    # Final summary
    print("\n" + "="*70)
    print("TRAINING COMPLETE - SUMMARY")
    print("="*70)
    print(f"Test Set Performance:")
    print(f"  MAE:               {test_metrics['mae']:.3f} positions")
    print(f"  Within ±2 pos:     {test_metrics['within_2']*100:.2f}%")
    print(f"  Winner accuracy:   {test_metrics['winner_accuracy']*100:.2f}%")
    print(f"  Podium accuracy:   {test_metrics['podium_accuracy']*100:.2f}%")
    print(f"  Points accuracy:   {test_metrics['points_accuracy']*100:.2f}%")
    print("\n✓ Model ready for 2025 predictions!")
    print("  Next: Load 2025 qualifying data and predict race results")


if __name__ == "__main__":
    main()
