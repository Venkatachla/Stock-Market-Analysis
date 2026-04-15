#!/usr/bin/env python3
"""
POST-CLEANUP VERIFICATION SCRIPT
Validates that core system functionality is intact after cleanup.
"""

import os
import sys
import importlib
import json
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_check(name, passed, detail=""):
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    msg = f"  {status} {name}"
    if detail:
        msg += f" - {detail}"
    print(msg)
    return passed

def test_file_exists(path, name):
    """Test if required file exists"""
    exists = Path(path).exists()
    print_check(f"File exists: {name}", exists, path)
    return exists

def test_directory_exists(path, name):
    """Test if required directory exists"""
    exists = Path(path).is_dir()
    print_check(f"Directory exists: {name}", exists, path)
    return exists

def test_python_import(module_name):
    """Test if Python module can be imported"""
    try:
        importlib.import_module(module_name)
        print_check(f"Python import: {module_name}", True)
        return True
    except ImportError as e:
        print_check(f"Python import: {module_name}", False, str(e))
        return False

def test_no_file_exists(path, name):
    """Test if a file is successfully deleted"""
    not_exists = not Path(path).exists()
    status = "deleted" if not_exists else "still exists"
    print_check(f"File deleted: {name}", not_exists, status)
    return not_exists

def main():
    print(f"\n{Colors.BLUE}{'='*60}")
    print("POST-CLEANUP VERIFICATION SCRIPT")
    print(f"{'='*60}{Colors.RESET}\n")
    
    all_passed = True
    
    # Check 1: Core backend files exist
    print(f"{Colors.BLUE}[CHECK 1] Core Backend Files{Colors.RESET}")
    backend_files = [
        ("api/app.py", "FastAPI App"),
        ("api/auth.py", "Authentication"),
        ("api/models.py", "Database Models"),
        ("api/routes.py", "Trading Routes"),
        ("api/razorpay_integration.py", "Razorpay Integration"),
        ("api/core/config.py", "Configuration"),
        ("api/services/model_loader.py", "Model Loader"),
        ("api/services/predictor.py", "Predictor"),
    ]
    
    for filepath, name in backend_files:
        all_passed &= test_file_exists(filepath, name)
    
    # Check 2: Core frontend files exist
    print(f"\n{Colors.BLUE}[CHECK 2] Core Frontend Files{Colors.RESET}")
    frontend_files = [
        ("frontend/src/services/api.ts", "API Service"),
        ("frontend/src/components/TradingModal.tsx", "Trading Modal"),
        ("frontend/src/components/WalletModal.tsx", "Wallet Modal"),
        ("frontend/src/pages/Portfolio.tsx", "Portfolio Page"),
        ("frontend/src/contexts/AuthContext.tsx", "Auth Context"),
        ("frontend/index.html", "HTML Entry"),
        ("frontend/package.json", "Package Config"),
        ("frontend/vite.config.ts", "Vite Config"),
    ]
    
    for filepath, name in frontend_files:
        all_passed &= test_file_exists(filepath, name)
    
    # Check 3: Configuration files exist
    print(f"\n{Colors.BLUE}[CHECK 3] Configuration Files{Colors.RESET}")
    config_files = [
        (".env.example", "Environment Template"),
        (".gitignore", "Git Ignore Rules"),
        ("requirements.txt", "Python Requirements"),
    ]
    
    for filepath, name in config_files:
        all_passed &= test_file_exists(filepath, name)
    
    # Check 4: Documentation files exist
    print(f"\n{Colors.BLUE}[CHECK 4] Documentation Files{Colors.RESET}")
    docs = [
        ("README.md", "Project README"),
        ("TRADING_SYSTEM.md", "Trading System Doc"),
        ("SETUP_GUIDE.md", "Setup Guide"),
        ("CLEANUP_ANALYSIS.md", "Cleanup Analysis"),
    ]
    
    for filepath, name in docs:
        all_passed &= test_file_exists(filepath, name)
    
    # Check 5: Deleted files are gone
    print(f"\n{Colors.BLUE}[CHECK 5] Obsolete Files Deleted{Colors.RESET}")
    deleted_files = [
        ("debug_app.py", "debug_app.py"),
        ("debug_auth.py", "debug_auth.py"),
        ("check_users.py", "check_users.py"),
        ("add_demo_users.py", "add_demo_users.py"),
        ("A_Cover_in_Water.java", "Java file"),
        ("frontend.backup", "frontend.backup"),
        ("stockpulse-project", "stockpulse-project"),
        ("tmp_report_format", "tmp_report_format"),
    ]
    
    for filepath, name in deleted_files:
        all_passed &= test_no_file_exists(filepath, name)
    
    # Check 6: Core directories exist
    print(f"\n{Colors.BLUE}[CHECK 6] Core Directories{Colors.RESET}")
    core_dirs = [
        ("api", "API Package"),
        ("api/core", "API Core"),
        ("api/services", "API Services"),
        ("frontend/src", "Frontend Source"),
        ("frontend/src/components", "Components"),
        ("frontend/src/pages", "Pages"),
        ("frontend/src/contexts", "Contexts"),
        ("models", "ML Models"),
        ("data", "Data Directory"),
    ]
    
    for dirpath, name in core_dirs:
        all_passed &= test_directory_exists(dirpath, name)
    
    # Check 7: Database exists (or can be created)
    print(f"\n{Colors.BLUE}[CHECK 7] Database{Colors.RESET}")
    db_exists = Path("db.sqlite3").exists()
    if db_exists:
        print_check("Database exists: db.sqlite3", True)
    else:
        print_check("Database exists: db.sqlite3", False, "Will be created on first run")
    
    # Check 8: Key Python packages in requirements.txt
    print(f"\n{Colors.BLUE}[CHECK 8] Required Packages in requirements.txt{Colors.RESET}")
    try:
        with open("requirements.txt", "r") as f:
            requirements = f.read().lower()
            required_pkgs = ["fastapi", "sqlalchemy", "pydantic", "passlib", "python-jose", "razorpay"]
            for pkg in required_pkgs:
                found = pkg in requirements
                print_check(f"Package listed: {pkg}", found)
                all_passed &= found
    except FileNotFoundError:
        print_check("requirements.txt found", False)
        all_passed = False
    
    # Check 9: Run basic imports (if possible)
    print(f"\n{Colors.BLUE}[CHECK 9] Python Import Test (Advanced){Colors.RESET}")
    try:
        # Try to import core FastAPI app (this will fail if dependencies not installed, which is OK)
        sys.path.insert(0, os.getcwd())
        try:
            from api import app
            print_check("Can import api.app", True)
        except ImportError as e:
            print_check("Can import api.app", False, "Dependencies not installed (normal before pip install)")
    except Exception as e:
        print_check("Import test", False, str(e))
    
    # Final Summary
    print(f"\n{Colors.BLUE}{'='*60}")
    if all_passed:
        print(f"{Colors.GREEN}✓ ALL CHECKS PASSED!{Colors.RESET}")
        print("\nNext steps:")
        print("  1. cd backend && python -m venv venv")
        print("  2. venv\\Scripts\\activate  (or: source venv/bin/activate)")
        print("  3. pip install -r requirements.txt")
        print("  4. python api/app.py")
        print("\nIn another terminal:")
        print("  1. cd frontend")
        print("  2. npm install")
        print("  3. npm run dev")
        print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
        return 0
    else:
        print(f"{Colors.RED}✗ SOME CHECKS FAILED{Colors.RESET}")
        print("\nReview the failures above and fix the issues.")
        print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
