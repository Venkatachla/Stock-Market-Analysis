@echo off
REM CORS Testing Script
REM Test if backend is responding with proper CORS headers

echo.
echo ====================================================
echo  CORS CONFIGURATION TEST
echo ====================================================
echo.

echo [1/5] Testing backend health...
curl -v http://localhost:8000/health 2>&1 | findstr /i "access-control"
if %ERRORLEVEL% EQU 0 (
  echo ✅ Health check passed
) else (
  echo ❌ Health check failed
)

echo.
echo [2/5] Testing CORS preflight for signup (OPTIONS)...
echo.
curl -X OPTIONS http://localhost:8000/api/auth/signup ^
  -H "Origin: http://localhost:8080" ^
  -H "Access-Control-Request-Method: POST" ^
  -v 2>&1 | findstr /i "access-control"

echo.
echo [3/5] Testing signup endpoint directly...
echo.
curl -X POST http://localhost:8000/api/auth/signup ^
  -H "Content-Type: application/json" ^
  -H "Origin: http://localhost:8080" ^
  -d "{\"email\":\"cors_test@example.com\",\"password\":\"test123\",\"name\":\"Test\"}" ^
  -v 2>&1

echo.
echo [4/5] Testing signals endpoint (should have real prices)...
echo.
curl -X GET http://localhost:8000/api/signals/active ^
  -H "Origin: http://localhost:8080" ^
  -v 2>&1 | findstr /i "access-control"

echo.
echo [5/5] Testing health check with verbose headers...
echo.
curl -i http://localhost:8000/health 2>&1

echo.
echo ====================================================
echo  KEY HEADERS TO LOOK FOR:
echo ====================================================
echo   ✓ Access-Control-Allow-Origin: *
echo   ✓ Access-Control-Allow-Methods: *
echo   ✓ Access-Control-Allow-Headers: *
echo ====================================================
echo.

pause
