"""
Test F1 ELO Web App Setup
Verifies all components are properly configured
"""

import os
import sys
import sqlite3


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_status(check_name, passed, message=""):
    """Print check status"""
    status = "✓ PASS" if passed else "✗ FAIL"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    
    print(f"{color}{status}{reset} - {check_name}")
    if message:
        print(f"       {message}")


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    required = (3, 8)
    passed = version >= required
    message = f"Python {version.major}.{version.minor}.{version.micro}"
    print_status("Python Version", passed, message)
    return passed


def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['flask', 'pandas', 'numpy']
    all_installed = True
    
    for package in required_packages:
        try:
            __import__(package)
            print_status(f"Package: {package}", True, "Installed")
        except ImportError:
            print_status(f"Package: {package}", False, "Not installed")
            all_installed = False
    
    return all_installed


def check_file_structure():
    """Check if required files and folders exist"""
    required_items = [
        ('app.py', 'file'),
        ('templates', 'dir'),
        ('templates/index.html', 'file'),
        ('static', 'dir'),
        ('static/css', 'dir'),
        ('static/css/style.css', 'file'),
        ('static/js', 'dir'),
        ('static/js/app.js', 'file'),
    ]
    
    all_exist = True
    for item, item_type in required_items:
        if item_type == 'file':
            exists = os.path.isfile(item)
        else:
            exists = os.path.isdir(item)
        
        print_status(f"{'File' if item_type == 'file' else 'Directory'}: {item}", exists)
        all_exist = all_exist and exists
    
    return all_exist


def check_database():
    """Check database exists and has required tables"""
    db_path = 'DB/f1_database.db'
    
    if not os.path.exists(db_path):
        print_status("Database File", False, f"{db_path} not found")
        return False
    
    print_status("Database File", True, f"{db_path} found")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check required tables
        required_tables = ['drivers', 'results', 'races', 'constructors']
        optional_tables = ['driver_elo']
        
        all_required = True
        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            exists = cursor.fetchone() is not None
            print_status(f"Table: {table}", exists, "Required")
            all_required = all_required and exists
        
        for table in optional_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            exists = cursor.fetchone() is not None
            if exists:
                # Check if table has data
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print_status(f"Table: {table}", exists, f"Found with {count} records")
            else:
                print_status(f"Table: {table}", False, "Not found - run ELO calculation")
        
        conn.close()
        return all_required
        
    except Exception as e:
        print_status("Database Access", False, str(e))
        return False


def check_elo_calculation():
    """Check if ELO calculation script exists"""
    script_path = 'elo_calculation/calculate_driver_elo.py'
    exists = os.path.isfile(script_path)
    print_status("ELO Calculation Script", exists, script_path)
    return exists


def main():
    """Run all checks"""
    print_header("F1 ELO Web App - Setup Verification")
    
    print("\n🔍 Checking Python Environment...")
    python_ok = check_python_version()
    
    print("\n📦 Checking Dependencies...")
    deps_ok = check_dependencies()
    
    print("\n📁 Checking File Structure...")
    files_ok = check_file_structure()
    
    print("\n🗄️  Checking Database...")
    db_ok = check_database()
    
    print("\n🧮 Checking ELO Components...")
    elo_ok = check_elo_calculation()
    
    # Summary
    print_header("Summary")
    
    all_critical = python_ok and deps_ok and files_ok and db_ok
    
    if all_critical:
        print("\n✅ All critical checks passed!")
        if not elo_ok:
            print("\n⚠️  Warning: ELO calculation script not found")
        print("\n🚀 You can start the app with: python app.py")
    else:
        print("\n❌ Some critical checks failed!")
        print("\n📋 Action Items:")
        
        if not python_ok:
            print("  • Upgrade Python to version 3.8 or higher")
        
        if not deps_ok:
            print("  • Install dependencies: pip install -r requirements.txt")
        
        if not files_ok:
            print("  • Ensure all required files are in place")
        
        if not db_ok:
            print("  • Set up database or check database path")
            print("  • Run ELO calculation: python elo_calculation/calculate_driver_elo.py")
    
    print("\n" + "=" * 60 + "\n")


if __name__ == '__main__':
    main()
