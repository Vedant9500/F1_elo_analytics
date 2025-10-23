"""
F1 Database Import Script
This script imports CSV data into the F1 database using Python
Works with MySQL, PostgreSQL, SQLite, and other databases via SQLAlchemy
"""

import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime

# Configuration
CSV_DIR = Path('d:/f1-elo/archive')
DB_PATH = 'd:/f1-elo/DB/f1_database.db'  # For SQLite

# For MySQL/PostgreSQL, use connection string instead:
# CONNECTION_STRING = "mysql+pymysql://user:password@localhost/f1_db"
# CONNECTION_STRING = "postgresql://user:password@localhost/f1_db"


def clean_null_values(df, null_markers=['\\N', 'NULL', '']):
    """Replace various null markers with None"""
    return df.replace(null_markers, None)


def import_data_sqlite():
    """Import all CSV files into SQLite database"""
    
    print("Creating database connection...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Execute schema creation (you can read from create_database.sql)
        print("\nCreating tables...")
        create_tables_sqlite(cursor)
        
        # 1. Import Status
        print("\n1. Importing Status data...")
        df = pd.read_csv(CSV_DIR / 'status.csv')
        df.columns = ['status_id', 'status_description']
        df.to_sql('Status', conn, if_exists='append', index=False)
        print(f"   Imported {len(df)} status records")
        
        # 2. Import Team (from constructors)
        print("\n2. Importing Team data...")
        df = pd.read_csv(CSV_DIR / 'constructors.csv')
        df_team = pd.DataFrame({
            'team_id': df['constructorId'],
            'team_name': df['name'],
            'base_country': df['nationality'],
            'principal_name': None,
            'total_points': 0.0,
            'total_wins': 0
        })
        df_team.to_sql('Team', conn, if_exists='append', index=False)
        print(f"   Imported {len(df_team)} team records")
        
        # 3. Import Driver
        print("\n3. Importing Driver data...")
        df = pd.read_csv(CSV_DIR / 'drivers.csv', na_values=['\\N'])
        df_driver = pd.DataFrame({
            'driver_id': df['driverId'],
            'first_name': df['forename'],
            'last_name': df['surname'],
            'nationality': df['nationality'],
            'birth_date': pd.to_datetime(df['dob'], errors='coerce'),
            'debut_year': None,
            'current_team_id': None
        })
        df_driver.to_sql('Driver', conn, if_exists='append', index=False)
        print(f"   Imported {len(df_driver)} driver records")
        
        # 4. Import Circuit
        print("\n4. Importing Circuit data...")
        df = pd.read_csv(CSV_DIR / 'circuits.csv')
        df_circuit = pd.DataFrame({
            'circuit_id': df['circuitId'],
            'circuit_name': df['name'],
            'location': df['location'],
            'country': df['country'],
            'lap_length_km': None,
            'laps': None
        })
        df_circuit.to_sql('Circuit', conn, if_exists='append', index=False)
        print(f"   Imported {len(df_circuit)} circuit records")
        
        # 5. Import Race
        print("\n5. Importing Race data...")
        df = pd.read_csv(CSV_DIR / 'races.csv', na_values=['\\N'])
        df_race = pd.DataFrame({
            'race_id': df['raceId'],
            'season_year': df['year'],
            'circuit_id': df['circuitId'],
            'race_name': df['name'],
            'race_date': pd.to_datetime(df['date']),
            'round_number': df['round']
        })
        df_race.to_sql('Race', conn, if_exists='append', index=False)
        print(f"   Imported {len(df_race)} race records")
        
        # 6. Import Result (separating primary and additional entries)
        print("\n6. Importing Result data...")
        df = pd.read_csv(CSV_DIR / 'results.csv', na_values=['\\N'])
        
        # Get status descriptions
        status_df = pd.read_csv(CSV_DIR / 'status.csv')
        status_dict = dict(zip(status_df['statusId'], status_df['status']))
        
        # Check for duplicates
        df['is_duplicate'] = df.duplicated(subset=['raceId', 'driverId'], keep='first')
        duplicates_count = df['is_duplicate'].sum()
        
        if duplicates_count > 0:
            print(f"   Found {duplicates_count} duplicate race+driver combinations")
            print(f"   Strategy: Primary result → Result table, Duplicates → Additional_Results table")
            
            # Sort to keep best result as primary
            df = df.sort_values(['raceId', 'driverId', 'positionOrder'])
            df['entry_sequence'] = df.groupby(['raceId', 'driverId']).cumcount() + 1
            
            # Split into primary and additional results
            df_primary = df[df['entry_sequence'] == 1].copy()
            df_additional = df[df['entry_sequence'] > 1].copy()
            
            # Import primary results to Result table
            print(f"   Importing {len(df_primary)} primary results to Result table...")
            df_result = pd.DataFrame({
                'result_id': df_primary['resultId'],
                'race_id': df_primary['raceId'],
                'driver_id': df_primary['driverId'],
                'team_id': df_primary['constructorId'],
                'grid_position': pd.to_numeric(df_primary['grid'], errors='coerce'),
                'position': pd.to_numeric(df_primary['position'], errors='coerce'),
                'points': df_primary['points'],
                'fastest_lap': df_primary['fastestLapTime'].apply(lambda x: None if pd.isna(x) else str(x)),
                'laps_completed': df_primary['laps'],
                'status': df_primary['statusId'].map(status_dict),
                'session_type': 'race'
            })
            df_result.to_sql('Result', conn, if_exists='append', index=False)
            
            # Import additional results to Additional_Results table
            if len(df_additional) > 0:
                print(f"   Importing {len(df_additional)} additional/duplicate entries to Additional_Results table...")
                
                # Create mapping of resultId to original (first) resultId
                result_id_map = {}
                for _, row in df.iterrows():
                    key = (row['raceId'], row['driverId'])
                    if key not in result_id_map:
                        result_id_map[key] = row['resultId']
                
                df_additional['original_result_id'] = df_additional.apply(
                    lambda x: result_id_map[(x['raceId'], x['driverId'])], axis=1
                )
                
                # Determine session type based on data patterns
                def determine_session_type(row):
                    if pd.isna(row['position']) and row['laps'] == 0:
                        return 'dns'  # Did not start
                    elif pd.isna(row['position']) and row['laps'] < 10:
                        return 'dnf_early'  # Early retirement
                    elif row['entry_sequence'] > 1:
                        return 're-entry'  # Re-entry after repair
                    else:
                        return 'alternative'
                
                df_additional['session_type_calc'] = df_additional.apply(determine_session_type, axis=1)
                
                df_add_result = pd.DataFrame({
                    'original_result_id': df_additional['original_result_id'],
                    'race_id': df_additional['raceId'],
                    'driver_id': df_additional['driverId'],
                    'team_id': df_additional['constructorId'],
                    'grid_position': pd.to_numeric(df_additional['grid'], errors='coerce'),
                    'position': pd.to_numeric(df_additional['position'], errors='coerce'),
                    'points': df_additional['points'],
                    'fastest_lap': df_additional['fastestLapTime'].apply(lambda x: None if pd.isna(x) else str(x)),
                    'laps_completed': df_additional['laps'],
                    'status': df_additional['statusId'].map(status_dict),
                    'session_type': df_additional['session_type_calc'],
                    'entry_sequence': df_additional['entry_sequence'],
                    'notes': 'Duplicate entry from original CSV'
                })
                df_add_result.to_sql('Additional_Results', conn, if_exists='append', index=False)
                
                print(f"   ✓ Preserved all data across both tables")
        else:
            # No duplicates, import all to Result table
            print(f"   No duplicates found, importing all {len(df)} records to Result table...")
            df_result = pd.DataFrame({
                'result_id': df['resultId'],
                'race_id': df['raceId'],
                'driver_id': df['driverId'],
                'team_id': df['constructorId'],
                'grid_position': pd.to_numeric(df['grid'], errors='coerce'),
                'position': pd.to_numeric(df['position'], errors='coerce'),
                'points': df['points'],
                'fastest_lap': df['fastestLapTime'].apply(lambda x: None if pd.isna(x) else str(x)),
                'laps_completed': df['laps'],
                'status': df['statusId'].map(status_dict),
                'session_type': 'race'
            })
            df_result.to_sql('Result', conn, if_exists='append', index=False)
        
        print(f"   Completed result data import")
        
        # Update Team Statistics
        print("\n7. Updating Team statistics...")
        cursor.execute("""
            UPDATE Team 
            SET total_points = (
                SELECT COALESCE(SUM(points), 0)
                FROM Result
                WHERE Result.team_id = Team.team_id
            ),
            total_wins = (
                SELECT COUNT(*)
                FROM Result
                WHERE Result.team_id = Team.team_id AND position = 1
            )
        """)
        print("   Team statistics updated")
        
        # Update Driver Debut Year
        print("\n8. Updating Driver debut years...")
        cursor.execute("""
            UPDATE Driver
            SET debut_year = (
                SELECT MIN(Race.season_year)
                FROM Result
                JOIN Race ON Result.race_id = Race.race_id
                WHERE Result.driver_id = Driver.driver_id
            )
        """)
        print("   Driver debut years updated")
        
        # Update Driver Current Team
        print("\n9. Updating Driver current teams...")
        cursor.execute("""
            UPDATE Driver
            SET current_team_id = (
                SELECT Result.team_id
                FROM Result
                JOIN Race ON Result.race_id = Race.race_id
                WHERE Result.driver_id = Driver.driver_id
                ORDER BY Race.race_date DESC
                LIMIT 1
            )
        """)
        print("   Driver current teams updated")
        
        conn.commit()
        
        # Verify import
        print("\n" + "="*50)
        print("DATA IMPORT SUMMARY")
        print("="*50)
        
        tables = ['Status', 'Team', 'Driver', 'Circuit', 'Race', 'Result', 'Additional_Results']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table:20s}: {count:>6,} records")
        
        # Show breakdown of additional results by type
        cursor.execute("""
            SELECT session_type, COUNT(*) as count
            FROM Additional_Results
            GROUP BY session_type
            ORDER BY count DESC
        """)
        additional_breakdown = cursor.fetchall()
        
        if additional_breakdown:
            print("\n" + "-"*50)
            print("Additional Results Breakdown:")
            print("-"*50)
            for session_type, count in additional_breakdown:
                print(f"  {session_type:20s}: {count:>6,} entries")
        
        print("="*50)
        print("Import completed successfully!")
        print("✓ All race results in Result table")
        print("✓ Duplicate entries preserved in Additional_Results table")
        
    except Exception as e:
        print(f"\nError during import: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()


def create_tables_sqlite(cursor):
    """Create all tables for SQLite"""
    
    # Drop existing tables
    tables = ['Driver_Elo', 'Team_Elo', 'Additional_Results', 'Result', 'Race', 'Circuit', 'Driver', 'Team', 'Status']
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    
    # Create Status table
    cursor.execute("""
        CREATE TABLE Status (
            status_id INTEGER PRIMARY KEY,
            status_description TEXT NOT NULL
        )
    """)
    
    # Create Team table
    cursor.execute("""
        CREATE TABLE Team (
            team_id INTEGER PRIMARY KEY,
            team_name TEXT NOT NULL UNIQUE,
            base_country TEXT NOT NULL,
            principal_name TEXT,
            total_points REAL DEFAULT 0.00,
            total_wins INTEGER DEFAULT 0
        )
    """)
    
    # Create Driver table
    cursor.execute("""
        CREATE TABLE Driver (
            driver_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            nationality TEXT NOT NULL,
            birth_date DATE,
            debut_year INTEGER,
            current_team_id INTEGER,
            FOREIGN KEY (current_team_id) REFERENCES Team(team_id)
        )
    """)
    
    # Create Circuit table
    cursor.execute("""
        CREATE TABLE Circuit (
            circuit_id INTEGER PRIMARY KEY,
            circuit_name TEXT NOT NULL UNIQUE,
            location TEXT NOT NULL,
            country TEXT NOT NULL,
            lap_length_km REAL,
            laps INTEGER
        )
    """)
    
    # Create Race table
    cursor.execute("""
        CREATE TABLE Race (
            race_id INTEGER PRIMARY KEY,
            season_year INTEGER NOT NULL,
            circuit_id INTEGER NOT NULL,
            race_name TEXT NOT NULL,
            race_date DATE NOT NULL,
            round_number INTEGER NOT NULL,
            FOREIGN KEY (circuit_id) REFERENCES Circuit(circuit_id),
            UNIQUE(season_year, round_number)
        )
    """)
    
    # Create Result table - Main race results only
    cursor.execute("""
        CREATE TABLE Result (
            result_id INTEGER PRIMARY KEY,
            race_id INTEGER NOT NULL,
            driver_id INTEGER NOT NULL,
            team_id INTEGER NOT NULL,
            grid_position INTEGER,
            position INTEGER,
            points REAL DEFAULT 0.00,
            fastest_lap TEXT,
            laps_completed INTEGER DEFAULT 0,
            status TEXT,
            session_type TEXT DEFAULT 'race',
            FOREIGN KEY (race_id) REFERENCES Race(race_id),
            FOREIGN KEY (driver_id) REFERENCES Driver(driver_id),
            FOREIGN KEY (team_id) REFERENCES Team(team_id),
            UNIQUE(race_id, driver_id)
        )
    """)
    
    # Create Additional_Results table for duplicate/alternative entries
    cursor.execute("""
        CREATE TABLE Additional_Results (
            additional_result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_result_id INTEGER NOT NULL,
            race_id INTEGER NOT NULL,
            driver_id INTEGER NOT NULL,
            team_id INTEGER NOT NULL,
            grid_position INTEGER,
            position INTEGER,
            points REAL DEFAULT 0.00,
            fastest_lap TEXT,
            laps_completed INTEGER DEFAULT 0,
            status TEXT,
            session_type TEXT DEFAULT 'alternative',
            entry_sequence INTEGER DEFAULT 1,
            notes TEXT,
            FOREIGN KEY (race_id) REFERENCES Race(race_id),
            FOREIGN KEY (driver_id) REFERENCES Driver(driver_id),
            FOREIGN KEY (team_id) REFERENCES Team(team_id)
        )
    """)
    
    # Create Driver_Elo table
    cursor.execute("""
        CREATE TABLE Driver_Elo (
            elo_id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER NOT NULL,
            race_id INTEGER NOT NULL,
            elo_rating REAL NOT NULL DEFAULT 1500.00,
            updated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (driver_id) REFERENCES Driver(driver_id),
            FOREIGN KEY (race_id) REFERENCES Race(race_id),
            UNIQUE(driver_id, race_id)
        )
    """)
    
    # Create Team_Elo table
    cursor.execute("""
        CREATE TABLE Team_Elo (
            elo_id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER NOT NULL,
            race_id INTEGER NOT NULL,
            elo_rating REAL NOT NULL DEFAULT 1500.00,
            updated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES Team(team_id),
            FOREIGN KEY (race_id) REFERENCES Race(race_id),
            UNIQUE(team_id, race_id)
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX idx_driver_nationality ON Driver(nationality)")
    cursor.execute("CREATE INDEX idx_race_season ON Race(season_year)")
    cursor.execute("CREATE INDEX idx_result_race ON Result(race_id)")
    cursor.execute("CREATE INDEX idx_result_driver ON Result(driver_id)")
    cursor.execute("CREATE INDEX idx_result_team ON Result(team_id)")
    cursor.execute("CREATE INDEX idx_additional_race ON Additional_Results(race_id)")
    cursor.execute("CREATE INDEX idx_additional_driver ON Additional_Results(driver_id)")
    cursor.execute("CREATE INDEX idx_additional_original ON Additional_Results(original_result_id)")


if __name__ == '__main__':
    print("F1 Database Import Tool")
    print("="*50)
    print(f"CSV Directory: {CSV_DIR}")
    print(f"Database: {DB_PATH}")
    print("="*50)
    
    import_data_sqlite()
