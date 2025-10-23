"""
Add Enhanced Circuit Features and Interaction Features to v4 Dataset
Creates v5 with explicit track characteristics and driver pace differentials
"""

import pandas as pd
import numpy as np

def add_circuit_characteristics():
    """Add detailed circuit characteristic features"""
    print("Creating circuit characteristics lookup...")
    
    # Comprehensive circuit features based on F1 analysis
    circuit_features = {
        # Classic circuits
        1: {"overtake_difficulty": 8, "downforce": 2, "tire_deg": 1, "is_high_altitude": 0, "avg_speed_kph": 210},  # Albert Park
        2: {"overtake_difficulty": 10, "downforce": 3, "tire_deg": 1, "is_high_altitude": 0, "avg_speed_kph": 160},  # Monaco
        3: {"overtake_difficulty": 5, "downforce": 2, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 195},  # Indianapolis
        4: {"overtake_difficulty": 3, "downforce": 2, "tire_deg": 3, "is_high_altitude": 0, "avg_speed_kph": 205},  # Bahrain
        5: {"overtake_difficulty": 6, "downforce": 2, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 200},  # Catalunya
        6: {"overtake_difficulty": 10, "downforce": 3, "tire_deg": 1, "is_high_altitude": 0, "avg_speed_kph": 160},  # Monaco (duplicate?)
        7: {"overtake_difficulty": 5, "downforce": 2, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 210},  # Gilles Villeneuve
        8: {"overtake_difficulty": 6, "downforce": 2, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 190},  # Magny-Cours
        9: {"overtake_difficulty": 5, "downforce": 2, "tire_deg": 3, "is_high_altitude": 0, "avg_speed_kph": 230},  # Silverstone
        10: {"overtake_difficulty": 6, "downforce": 2, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 195},  # Hockenheim
        11: {"overtake_difficulty": 5, "downforce": 2, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 200},  # Hungaroring
        13: {"overtake_difficulty": 4, "downforce": 2, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 225},  # Spa
        14: {"overtake_difficulty": 4, "downforce": 1, "tire_deg": 1, "is_high_altitude": 0, "avg_speed_kph": 260},  # Monza
        15: {"overtake_difficulty": 8, "downforce": 3, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 180},  # Singapore
        16: {"overtake_difficulty": 5, "downforce": 2, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 215},  # Suzuka
        17: {"overtake_difficulty": 4, "downforce": 2, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 220},  # Fuji
        18: {"overtake_difficulty": 6, "downforce": 2, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 190},  # Shanghai
        19: {"overtake_difficulty": 7, "downforce": 3, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 185},  # Interlagos
        20: {"overtake_difficulty": 3, "downforce": 2, "tire_deg": 3, "is_high_altitude": 0, "avg_speed_kph": 215},  # Austin (COTA)
        21: {"overtake_difficulty": 5, "downforce": 2, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 200},  # Yas Marina
        22: {"overtake_difficulty": 6, "downforce": 2, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 195},  # Red Bull Ring
        24: {"overtake_difficulty": 5, "downforce": 2, "tire_deg": 3, "is_high_altitude": 0, "avg_speed_kph": 210},  # Sochi
        32: {"overtake_difficulty": 7, "downforce": 3, "tire_deg": 2, "is_high_altitude": 1, "avg_speed_kph": 190},  # Mexico City
        34: {"overtake_difficulty": 5, "downforce": 1, "tire_deg": 1, "is_high_altitude": 0, "avg_speed_kph": 240},  # Paul Ricard
        39: {"overtake_difficulty": 6, "downforce": 2, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 205},  # Nürburgring
        70: {"overtake_difficulty": 5, "downforce": 2, "tire_deg": 3, "is_high_altitude": 0, "avg_speed_kph": 215},  # Portimao
        71: {"overtake_difficulty": 6, "downforce": 2, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 210},  # Imola
        73: {"overtake_difficulty": 6, "downforce": 1, "tire_deg": 1, "is_high_altitude": 0, "avg_speed_kph": 215},  # Baku (street)
        75: {"overtake_difficulty": 5, "downforce": 2, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 205},  # Istanbul
        76: {"overtake_difficulty": 6, "downforce": 2, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 240},  # Jeddah (street)
        77: {"overtake_difficulty": 5, "downforce": 2, "tire_deg": 3, "is_high_altitude": 0, "avg_speed_kph": 220},  # Losail (Qatar)
        78: {"overtake_difficulty": 7, "downforce": 2, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 200},  # Zandvoort
        79: {"overtake_difficulty": 5, "downforce": 1, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 240},  # Las Vegas (street)
        80: {"overtake_difficulty": 7, "downforce": 2, "tire_deg": 2, "is_high_altitude": 0, "avg_speed_kph": 200},  # Miami (street)
    }
    
    # Convert to DataFrame
    circuit_df = pd.DataFrame.from_dict(circuit_features, orient='index')
    circuit_df['circuit_id'] = circuit_df.index
    
    # Normalize downforce and tire_deg to 0-1 scale
    circuit_df['circuit_downforce_level'] = circuit_df['downforce'] / 3.0
    circuit_df['circuit_tire_deg_level'] = circuit_df['tire_deg'] / 3.0
    
    # Keep original for reference
    circuit_df = circuit_df.rename(columns={
        'overtake_difficulty': 'circuit_overtake_difficulty',
        'is_high_altitude': 'circuit_is_high_altitude',
        'avg_speed_kph': 'circuit_avg_speed_kph'
    })
    
    circuit_df = circuit_df[['circuit_id', 'circuit_overtake_difficulty', 'circuit_downforce_level', 
                             'circuit_tire_deg_level', 'circuit_is_high_altitude', 'circuit_avg_speed_kph']]
    
    print(f"  ✓ Created features for {len(circuit_df)} circuits")
    return circuit_df


def add_interaction_features(df):
    """Add explicit interaction features"""
    print("Adding interaction features...")
    
    # 1. Driver pace differential (race vs quali specialist)
    df['driver_pace_differential'] = df['driver_race_elo'] - df['driver_quali_elo']
    # Positive = race specialist (Alonso), Negative = quali specialist (Leclerc)
    
    # 2. Team pace differential
    df['team_pace_differential'] = df['team_race_elo'] - df['team_quali_elo']
    
    # 3. Grid position * track overtaking difficulty (how much does grid matter?)
    df['grid_pos_track_importance'] = df['grid_position'] * df['circuit_overtake_difficulty']
    
    # 4. Elo advantage weighted by track overtaking
    df['elo_advantage_track_weighted'] = df['elo_gap_to_leader'] * df['circuit_overtake_difficulty'] / 10.0
    
    # 5. DNF risk on street circuits (street circuits + reliability issues = danger)
    df['dnf_risk_street_circuit'] = df['dnf_probability'] * df['circuit_is_street']
    
    # 6. Championship pressure on difficult tracks
    df['pressure_on_difficult_track'] = df['championship_battle'] * df['circuit_overtake_difficulty']
    
    # 7. High downforce car advantage
    df['team_downforce_match'] = df['team_global_elo'] * df['circuit_downforce_level']
    
    print(f"  ✓ Added 7 interaction features")
    return df


def calculate_recent_position_gain(df):
    """Calculate recent form: average position gain/loss from quali to race"""
    print("Calculating recent position gain...")
    
    # Sort by driver and date
    df = df.sort_values(['driver_id', 'race_date'])
    
    # Calculate position change for each race (quali to race)
    df['position_change_this_race'] = df['grid_position'] - df['position_target']
    
    # Rolling average of position changes (last 5 races)
    df['recent_position_gain'] = df.groupby('driver_id')['position_change_this_race'].transform(
        lambda x: x.shift(1).rolling(window=5, min_periods=1).mean()
    )
    
    # Fill NaN
    df['recent_position_gain'] = df['recent_position_gain'].fillna(0)
    
    print(f"  ✓ Added recent position gain feature")
    return df


def process_dataset(input_file, output_file, circuit_features):
    """Process a single dataset file"""
    print(f"\nProcessing {input_file}...")
    
    df = pd.read_csv(input_file, low_memory=False)
    
    # Merge circuit features
    df = df.merge(circuit_features, on='circuit_id', how='left')
    
    # Fill missing circuit features with median values
    for col in ['circuit_overtake_difficulty', 'circuit_downforce_level', 
                'circuit_tire_deg_level', 'circuit_is_high_altitude', 'circuit_avg_speed_kph']:
        df[col] = df[col].fillna(df[col].median())
    
    # Add interaction features
    df = add_interaction_features(df)
    
    # Add recent position gain
    df = calculate_recent_position_gain(df)
    
    # Save
    df.to_csv(output_file, index=False)
    print(f"  ✓ Saved {output_file}")
    
    return df


def main():
    """Main processing pipeline"""
    print("\n" + "="*70)
    print("CREATING v5 DATASET WITH ENHANCED FEATURES")
    print("="*70)
    
    # Create circuit features
    circuit_features = add_circuit_characteristics()
    
    # Process all datasets
    process_dataset('data/train_data_v4.csv', 'data/train_data_v5.csv', circuit_features)
    process_dataset('data/val_data_v4.csv', 'data/val_data_v5.csv', circuit_features)
    process_dataset('data/test_data_v4.csv', 'data/test_data_v5.csv', circuit_features)
    
    # Create updated feature list
    print("\nCreating feature list v5...")
    
    features_v5 = [
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
        
        # DNF prediction
        'dnf_probability',
        'circuit_is_street',
        'circuit_historical_dnf_rate',
        'grid_midpack_risk',
        
        # NEW: Circuit characteristics
        'circuit_overtake_difficulty',
        'circuit_downforce_level',
        'circuit_tire_deg_level',
        'circuit_is_high_altitude',
        'circuit_avg_speed_kph',
        
        # NEW: Interaction features
        'driver_pace_differential',
        'team_pace_differential',
        'grid_pos_track_importance',
        'elo_advantage_track_weighted',
        'dnf_risk_street_circuit',
        'pressure_on_difficult_track',
        'team_downforce_match',
        
        # NEW: Recent position gain
        'recent_position_gain',
        
        # Categorical
        'circuit_id',
        'season_year'
    ]
    
    with open('data/feature_list_v5.txt', 'w') as f:
        f.write('\n'.join(features_v5))
    
    print(f"  ✓ Saved feature_list_v5.txt ({len(features_v5)} features)")
    
    print("\n" + "="*70)
    print("v5 DATASET COMPLETE!")
    print("="*70)
    print(f"\nTotal features: {len(features_v5)}")
    print("\nNew feature categories:")
    print("  - Circuit characteristics: 5 features")
    print("    * overtake_difficulty (1-10 scale)")
    print("    * downforce_level (0-1 normalized)")
    print("    * tire_deg_level (0-1 normalized)")
    print("    * is_high_altitude (Mexico, Brazil)")
    print("    * avg_speed_kph")
    print("\n  - Interaction features: 7 features")
    print("    * driver_pace_differential (race vs quali specialist)")
    print("    * team_pace_differential")
    print("    * grid_pos_track_importance (grid * overtake_difficulty)")
    print("    * elo_advantage_track_weighted")
    print("    * dnf_risk_street_circuit")
    print("    * pressure_on_difficult_track")
    print("    * team_downforce_match")
    print("\n  - Recent position gain: 1 feature")
    print("    * recent_position_gain (avg quali→race position change)")
    print("\n" + "="*70)
    print("READY TO TRAIN XGBoost v5!")
    print("="*70)


if __name__ == "__main__":
    main()
