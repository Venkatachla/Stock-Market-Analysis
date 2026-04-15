@echo off
REM PROJECT CLEANUP SCRIPT FOR WINDOWS
REM This script removes redundant and obsolete files from the project
REM BACKUP YOUR PROJECT FIRST using: git stash or external backup

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  STOCK TRADING SYSTEM - CLEANUP SCRIPT
echo ========================================
echo.
echo WARNING: This script will delete files.
echo BACKUP YOUR PROJECT FIRST!
echo.

REM Ask for confirmation
set /p confirm="Continue with cleanup? (yes/no): "
if /i not "%confirm%"=="yes" (
    echo Cleanup cancelled.
    exit /b 0
)

echo.
echo [1/4] Deleting old troubleshooting scripts...
if exist "debug_app.py" del /f /q debug_app.py && echo Deleted debug_app.py
if exist "debug_auth.py" del /f /q debug_auth.py && echo Deleted debug_auth.py
if exist "debug_predict.py" del /f /q debug_predict.py && echo Deleted debug_predict.py
if exist "check_users.py" del /f /q check_users.py && echo Deleted check_users.py
if exist "add_demo_users.py" del /f /q add_demo_users.py && echo Deleted add_demo_users.py
if exist "add_routes.py" del /f /q add_routes.py && echo Deleted add_routes.py
if exist "inject_routes.py" del /f /q inject_routes.py && echo Deleted inject_routes.py
if exist "patch_app.py" del /f /q patch_app.py && echo Deleted patch_app.py
if exist "update_ui.py" del /f /q update_ui.py && echo Deleted update_ui.py
if exist "cli.py" del /f /q cli.py && echo Deleted cli.py
if exist "A_Cover_in_Water.java" del /f /q A_Cover_in_Water.java && echo Deleted A_Cover_in_Water.java
if exist "SYSTEM_STATUS.txt" del /f /q SYSTEM_STATUS.txt && echo Deleted SYSTEM_STATUS.txt

echo.
echo [2/4] Deleting old test scripts...
for %%f in (test_missing.py test_predict_api.py test_prediction_detail.py integration_test.py) do (
    if exist "%%f" del /f /q "%%f" && echo Deleted %%f
)

echo.
echo [3/4] Deleting backup folders...
if exist "frontend.backup" rmdir /s /q frontend.backup && echo Deleted frontend.backup
if exist "stockpulse-project" rmdir /s /q stockpulse-project && echo Deleted stockpulse-project
if exist "tmp_report_format" rmdir /s /q tmp_report_format && echo Deleted tmp_report_format

echo.
echo [4/4] Deleting build artifacts and cache...
if exist "dist" rmdir /s /q dist && echo Deleted dist/
if exist "build" rmdir /s /q build && echo Deleted build/
if exist "__pycache__" rmdir /s /q __pycache__ && echo Deleted __pycache__/
if exist ".cache_yf" rmdir /s /q .cache_yf && echo Deleted .cache_yf/
if exist ".pytest_cache" rmdir /s /q .pytest_cache && echo Deleted .pytest_cache/
if exist "tmp" rmdir /s /q tmp && echo Deleted tmp/
if exist "logs" rmdir /s /q logs && echo Deleted logs/

echo.
echo [5/4] OPTIONAL - Deleting node_modules (will need npm install to regenerate)...
set /p del_nm="Delete node_modules? (yes/no): "
if /i "%del_nm%"=="yes" (
    if exist "frontend\node_modules" rmdir /s /q frontend\node_modules && echo Deleted frontend/node_modules
)

echo.
echo ========================================
echo CLEANUP COMPLETE!
echo ========================================
echo.
echo Next steps:
echo  1. Verify system still starts: python -m api.app
echo  2. Regenerate node_modules: cd frontend ^&^& npm install
echo  3. Regenerate build: cd frontend ^&^& npm run build
echo  4. Run tests to verify functionality
echo  5. Commit changes: git add -A ^&^& git commit -m "chore: cleanup obsolete files"
echo.
pause
