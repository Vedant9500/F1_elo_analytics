"""
Update F1 ELO Rankings After New Race
Automates the process of updating ELO ratings after a new race
"""

import sys
import os
from datetime import datetime
import sqlite3

# Add parent directory to path to import ELO calculator
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from elo_calculation.calculate_driver_elo import TeammateBasedF1Elo


def check_database_exists(db_path='DB/f1_database.db'):
    """Check if database file exists"""
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return False
    return True


def get_latest_race_info(db_path='DB/f1_database.db'):
    """Get information about the latest race in database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT r.year, r.round, r.name, r.date
        FROM races r
        ORDER BY r.date DESC
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'year': result[0],
            'round': result[1],
            'name': result[2],
            'date': result[3]
        }
    return None


def update_elo_ratings():
    """Main function to update ELO ratings"""
    print("=" * 60)
    print("F1 ELO RATINGS UPDATE SCRIPT")
    print("=" * 60)
    
    # Check database exists
    if not check_database_exists():
        return False
    
    # Get latest race info
    latest_race = get_latest_race_info()
    if latest_race:
        print(f"\nLatest race in database:")
        print(f"  {latest_race['name']}")
        print(f"  Date: {latest_race['date']}")
        print(f"  Season: {latest_race['year']}, Round: {latest_race['round']}")
    else:
        print("\nWarning: No races found in database")
    
    print("\nStarting ELO calculation...")
    print("-" * 60)
    
    try:
        # Initialize ELO calculator
        elo_system = TeammateBasedF1Elo(db_path='DB/f1_database.db')
        
        # Run full ELO calculation
        print("Calculating driver ELO ratings...")
        elo_system.calculate_all_elos()
        
        print("\n" + "=" * 60)
        print("ELO RATINGS UPDATED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\nUpdate completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nYou can now refresh the web application to see updated rankings.")
        
        return True
        
    except Exception as e:
        print(f"\nError updating ELO ratings: {str(e)}")
        print("\nPlease check:")
        print("1. Database connection is working")
        print("2. All required data tables exist")
        print("3. Race results are properly imported")
        return False


def main():
    """Entry point"""
    print("\nThis script will recalculate all ELO ratings based on current database.")
    print("Make sure you have imported the latest race results first.\n")
    
    response = input("Continue with ELO update? (y/n): ").strip().lower()
    
    if response == 'y':
        success = update_elo_ratings()
        sys.exit(0 if success else 1)
    else:
        print("\nUpdate cancelled.")
        sys.exit(0)


if __name__ == '__main__':
    main()
