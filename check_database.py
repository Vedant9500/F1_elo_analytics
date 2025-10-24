"""
Quick Database Structure Checker
Shows what tables exist in your F1 database
"""

import sqlite3
import os

DB_PATH = 'DB/f1_database.db'

def check_database():
    """Check database structure and contents"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}")
        return
    
    print(f"✅ Database found at: {DB_PATH}\n")
    print("=" * 60)
    print("DATABASE STRUCTURE")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ No tables found in database!")
            conn.close()
            return
        
        print(f"\n📊 Found {len(tables)} tables:\n")
        
        for (table_name,) in tables:
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            # Get columns
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"📋 {table_name}")
            print(f"   Rows: {count:,}")
            print(f"   Columns: {', '.join([col[1] for col in columns[:5]])}", end='')
            if len(columns) > 5:
                print(f"... (+{len(columns)-5} more)")
            else:
                print()
            print()
        
        # Check for ELO data specifically
        print("=" * 60)
        print("ELO DATA CHECK")
        print("=" * 60)
        
        if 'driver_elo' in [t[0] for t in tables]:
            cursor.execute("SELECT COUNT(*) FROM driver_elo")
            elo_count = cursor.fetchone()[0]
            print(f"✅ driver_elo table exists with {elo_count} records")
            
            if elo_count > 0:
                cursor.execute("""
                    SELECT driverId, qualifying_elo, race_elo, global_elo 
                    FROM driver_elo 
                    ORDER BY global_elo DESC 
                    LIMIT 5
                """)
                top_drivers = cursor.fetchall()
                print("\n🏆 Top 5 ELO ratings:")
                for i, (driver_id, q_elo, r_elo, g_elo) in enumerate(top_drivers, 1):
                    print(f"   {i}. Driver ID {driver_id}: Global={g_elo:.0f}, Q={q_elo:.0f}, R={r_elo:.0f}")
        else:
            print("❌ driver_elo table NOT found")
            print("   Run: python elo_calculation/calculate_driver_elo.py")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Database check complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")

if __name__ == '__main__':
    check_database()
