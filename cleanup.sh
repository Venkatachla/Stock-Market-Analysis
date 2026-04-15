#!/bin/bash

# PROJECT CLEANUP SCRIPT FOR LINUX/MAC
# This script removes redundant and obsolete files from the project
# BACKUP YOUR PROJECT FIRST using: git stash or external backup

set -e

echo
echo "========================================"
echo "  STOCK TRADING SYSTEM - CLEANUP SCRIPT"
echo "========================================"
echo
echo "WARNING: This script will delete files."
echo "BACKUP YOUR PROJECT FIRST!"
echo

# Ask for confirmation
read -p "Continue with cleanup? (yes/no): " confirm
if [[ "$confirm" != "yes" ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo
echo "[1/4] Deleting old troubleshooting scripts..."
files_to_delete=(
    "debug_app.py"
    "debug_auth.py"
    "debug_predict.py"
    "check_users.py"
    "add_demo_users.py"
    "add_routes.py"
    "inject_routes.py"
    "patch_app.py"
    "update_ui.py"
    "cli.py"
    "main.py"
    "startup.py"
    "quant_system.py"
    "A_Cover_in_Water.java"
    "SYSTEM_STATUS.txt"
)

for file in "${files_to_delete[@]}"; do
    if [ -f "$file" ]; then
        rm -f "$file"
        echo "✓ Deleted $file"
    fi
done

echo
echo "[2/4] Deleting old test scripts..."
find . -maxdepth 1 -name "test_*.py" -delete -print | sed 's/^/✓ Deleted /'
find . -maxdepth 1 -name "integration_test.py" -delete -print | sed 's/^/✓ Deleted /'

echo
echo "[3/4] Deleting backup folders..."
folders_to_delete=(
    "frontend.backup"
    "stockpulse-project"
    "tmp_report_format"
)

for folder in "${folders_to_delete[@]}"; do
    if [ -d "$folder" ]; then
        rm -rf "$folder"
        echo "✓ Deleted $folder/"
    fi
done

echo
echo "[4/4] Deleting build artifacts and cache..."
cache_folders=(
    "dist"
    "build"
    "__pycache__"
    ".cache_yf"
    ".pytest_cache"
    "tmp"
    "logs"
)

for folder in "${cache_folders[@]}"; do
    if [ -d "$folder" ]; then
        rm -rf "$folder"
        echo "✓ Deleted $folder/"
    fi
done

# Recursively delete __pycache__ in subdirectories
echo "✓ Deleting __pycache__ in subdirectories..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo
echo "[5/5] OPTIONAL - Deleting node_modules (will need npm install to regenerate)..."
read -p "Delete frontend/node_modules? (yes/no): " del_nm
if [[ "$del_nm" == "yes" ]]; then
    if [ -d "frontend/node_modules" ]; then
        rm -rf frontend/node_modules
        echo "✓ Deleted frontend/node_modules/"
    fi
fi

echo
echo "========================================"
echo "CLEANUP COMPLETE!"
echo "========================================"
echo
echo "Next steps:"
echo " 1. Verify system still starts: python -m api.app"
echo " 2. Regenerate node_modules: cd frontend && npm install"
echo " 3. Regenerate build: cd frontend && npm run build"
echo " 4. Run tests to verify functionality"
echo " 5. Commit changes: git add -A && git commit -m 'chore: cleanup obsolete files'"
echo
