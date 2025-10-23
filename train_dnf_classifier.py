"""
F1 DNF Prediction - Separate Binary Classifier
Predicts probability of Did Not Finish for each driver
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
import pickle

class F1DNFClassifier:
    def __init__(self):
        self.model = None
        self.feature_columns = None
        
    def load_data(self):
        """Load preprocessed data"""
        print("Loading data for DNF classifier...")
        
        train_df = pd.read_csv('data/train_data_v3.csv')
        val_df = pd.read_csv('data/val_data_v3.csv')
        test_df = pd.read_csv('data/test_data_v3.csv')
        
        print(f"  ✓ Training:   {len(train_df):,} samples")
        print(f"  ✓ Validation: {len(val_df):,} samples")
        print(f"  ✓ Test:       {len(test_df):,} samples")
        
        return train_df, val_df, test_df
    
    def add_circuit_features(self, df):
        """Add circuit-specific DNF risk features"""
        print("Adding circuit risk features...")
        
        # Street circuits (high crash/DNF risk)
        street_circuits = {
            # Monaco, Baku, Singapore, Jeddah, Miami, Las Vegas
            6: 1,   # Monaco
            73: 1,  # Baku
            15: 1,  # Singapore  
            76: 1,  # Jeddah
            80: 1,  # Miami
            79: 1,  # Las Vegas
        }
        
        df['circuit_is_street'] = df['circuit_id'].map(street_circuits).fillna(0).astype(int)
        
        # Calculate historical DNF rate per circuit
        circuit_dnf_rates = df.groupby('circuit_id')['dnf_flag'].mean()
        df['circuit_historical_dnf_rate'] = df['circuit_id'].map(circuit_dnf_rates)
        
        # Grid position risk (mid-pack = higher collision risk)
        df['grid_midpack_risk'] = np.where(
            (df['grid_position'] >= 6) & (df['grid_position'] <= 15), 
            1, 0
        )
        
        print(f"  ✓ Added 3 circuit risk features")
        return df
    
    def prepare_dnf_features(self, train_df, val_df, test_df):
        """Prepare features specifically for DNF prediction"""
        print("\nPreparing DNF-specific features...")
        
        # Add circuit features to all datasets
        train_df = self.add_circuit_features(train_df)
        val_df = self.add_circuit_features(val_df)
        test_df = self.add_circuit_features(test_df)
        
        # Define DNF-specific feature set
        self.feature_columns = [
            # Reliability metrics
            'driver_reliability',
            'team_reliability',
            'driver_recent_dnf_rate',
            'team_recent_dnf_rate',
            
            # Grid position risk
            'grid_position',
            'grid_normalized',
            'grid_midpack_risk',
            
            # Circuit characteristics
            'circuit_is_street',
            'circuit_historical_dnf_rate',
            'circuit_id',  # Categorical
            
            # Championship pressure (aggressive driving)
            'championship_battle',
            'championship_position_before',
            
            # Performance gaps (struggling cars more likely to break)
            'elo_gap_to_leader',
            'team_elo_gap_to_leader',
            'pace_gap_to_fastest_pct',
            
            # Recent form (struggling = more DNFs)
            'driver_recent_position',
            'team_recent_position',
            
            # Season/era
            'season_year'
        ]
        
        print(f"  ✓ Using {len(self.feature_columns)} features for DNF prediction")
        
        return train_df, val_df, test_df
    
    def train_model(self, train_df, val_df):
        """Train LightGBM binary classifier"""
        print("\n" + "="*70)
        print("TRAINING DNF CLASSIFIER")
        print("="*70)
        
        # Prepare features
        X_train = train_df[self.feature_columns]
        y_train = train_df['dnf_flag']
        
        X_val = val_df[self.feature_columns]
        y_val = val_df['dnf_flag']
        
        # Check class distribution
        print(f"\nDNF Distribution:")
        print(f"  Training:   DNF={y_train.sum():,} ({y_train.mean()*100:.2f}%), Finish={len(y_train)-y_train.sum():,}")
        print(f"  Validation: DNF={y_val.sum():,} ({y_val.mean()*100:.2f}%), Finish={len(y_val)-y_val.sum():,}")
        
        # Calculate scale_pos_weight for class imbalance
        scale_pos_weight = (len(y_train) - y_train.sum()) / y_train.sum()
        print(f"\nScale pos weight: {scale_pos_weight:.2f}")
        
        # Create LightGBM datasets
        train_data = lgb.Dataset(
            X_train,
            label=y_train,
            categorical_feature=['circuit_id', 'season_year'],
            free_raw_data=False
        )
        
        val_data = lgb.Dataset(
            X_val,
            label=y_val,
            categorical_feature=['circuit_id', 'season_year'],
            reference=train_data,
            free_raw_data=False
        )
        
        # Parameters optimized for binary classification
        params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'max_depth': 6,
            'min_child_samples': 50,
            'scale_pos_weight': scale_pos_weight,
            'lambda_l1': 1.0,
            'lambda_l2': 1.0,
            'verbose': -1,
            'seed': 42
        }
        
        print("\nTraining LightGBM classifier...")
        
        self.model = lgb.train(
            params,
            train_data,
            num_boost_round=500,
            valid_sets=[train_data, val_data],
            valid_names=['train', 'val'],
            callbacks=[
                lgb.early_stopping(stopping_rounds=50, verbose=True),
                lgb.log_evaluation(period=50)
            ]
        )
        
        print(f"\n✓ Training complete (best iteration: {self.model.best_iteration})")
        
        return self.model
    
    def evaluate_model(self, test_df):
        """Evaluate DNF classifier"""
        print("\n" + "="*70)
        print("EVALUATING DNF CLASSIFIER ON 2024 TEST SET")
        print("="*70)
        
        X_test = test_df[self.feature_columns]
        y_test = test_df['dnf_flag']
        
        # Predictions
        y_pred_proba = self.model.predict(X_test, num_iteration=self.model.best_iteration)
        y_pred = (y_pred_proba >= 0.5).astype(int)
        
        # Metrics
        if y_test.sum() == 0:
            print("\n⚠️  WARNING: Test set has zero DNF events!")
            print("  Model trained successfully but cannot evaluate metrics without positive class.")
            print("  DNF probability predictions will still be generated.")
            
            # Just show prediction distribution
            print(f"\n📊 DNF Probability Distribution in Test Set:")
            print(f"  Mean: {y_pred_proba.mean():.4f}")
            print(f"  Median: {np.median(y_pred_proba):.4f}")
            print(f"  Max: {y_pred_proba.max():.4f}")
            print(f"  Min: {y_pred_proba.min():.4f}")
            
            return y_pred_proba, None
        
        print("\n📊 Classification Metrics:")
        print(f"  Accuracy:  {accuracy_score(y_test, y_pred):.4f}")
        print(f"  Precision: {precision_score(y_test, y_pred, zero_division=0):.4f}")
        print(f"  Recall:    {recall_score(y_test, y_pred):.4f}")
        print(f"  F1 Score:  {f1_score(y_test, y_pred):.4f}")
        print(f"  ROC AUC:   {roc_auc_score(y_test, y_pred_proba):.4f}")
        
        # Feature importance
        importance = self.model.feature_importance(importance_type='gain')
        feature_importance_df = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        print("\n📈 Top 10 Most Important Features for DNF Prediction:")
        print(feature_importance_df.head(10).to_string(index=False))
        
        return y_pred_proba, None
    
    def add_dnf_probability_to_datasets(self):
        """Add DNF probability as new feature to all datasets"""
        print("\n" + "="*70)
        print("ADDING DNF PROBABILITY TO DATASETS")
        print("="*70)
        
        # Load original datasets
        train_df = pd.read_csv('data/train_data_v3.csv')
        val_df = pd.read_csv('data/val_data_v3.csv')
        test_df = pd.read_csv('data/test_data_v3.csv')
        
        # Add circuit features
        train_df = self.add_circuit_features(train_df)
        val_df = self.add_circuit_features(val_df)
        test_df = self.add_circuit_features(test_df)
        
        # Predict DNF probability
        train_df['dnf_probability'] = self.model.predict(
            train_df[self.feature_columns],
            num_iteration=self.model.best_iteration
        )
        
        val_df['dnf_probability'] = self.model.predict(
            val_df[self.feature_columns],
            num_iteration=self.model.best_iteration
        )
        
        test_df['dnf_probability'] = self.model.predict(
            test_df[self.feature_columns],
            num_iteration=self.model.best_iteration
        )
        
        # Save updated datasets
        print("\nSaving datasets with DNF probability...")
        train_df.to_csv('data/train_data_v4.csv', index=False)
        val_df.to_csv('data/val_data_v4.csv', index=False)
        test_df.to_csv('data/test_data_v4.csv', index=False)
        
        print(f"  ✓ Saved train_data_v4.csv")
        print(f"  ✓ Saved val_data_v4.csv")
        print(f"  ✓ Saved test_data_v4.csv")
        
        print(f"\n📊 DNF Probability Statistics:")
        print(f"  Training mean:   {train_df['dnf_probability'].mean():.4f}")
        print(f"  Validation mean: {val_df['dnf_probability'].mean():.4f}")
        print(f"  Test mean:       {test_df['dnf_probability'].mean():.4f}")
        
    def save_model(self):
        """Save DNF classifier"""
        print("\nSaving DNF classifier...")
        
        self.model.save_model('models/dnf_classifier.txt')
        
        metadata = {
            'feature_columns': self.feature_columns,
            'best_iteration': self.model.best_iteration
        }
        
        with open('models/dnf_classifier_metadata.pkl', 'wb') as f:
            pickle.dump(metadata, f)
        
        print("  ✓ Saved models/dnf_classifier.txt")
        print("  ✓ Saved models/dnf_classifier_metadata.pkl")


def main():
    """Main training pipeline"""
    print("\n" + "="*70)
    print("F1 DNF CLASSIFIER - TRAINING PIPELINE")
    print("="*70)
    
    # Initialize classifier
    classifier = F1DNFClassifier()
    
    # Load data
    train_df, val_df, test_df = classifier.load_data()
    
    # Prepare features
    train_df, val_df, test_df = classifier.prepare_dnf_features(train_df, val_df, test_df)
    
    # Train model
    classifier.train_model(train_df, val_df)
    
    # Evaluate
    y_pred_proba, cm = classifier.evaluate_model(test_df)
    
    # Save model
    classifier.save_model()
    
    # Add DNF probability to all datasets
    classifier.add_dnf_probability_to_datasets()
    
    print("\n" + "="*70)
    print("DNF CLASSIFIER COMPLETE!")
    print("="*70)
    print("\nNext Steps:")
    print("  1. Add circuit characteristic features (overtaking difficulty, etc.)")
    print("  2. Add quali vs race specialist features")
    print("  3. Update feature_list_v4.txt with new features")
    print("  4. Retrain main XGBoost position model with dnf_probability")


if __name__ == "__main__":
    main()
