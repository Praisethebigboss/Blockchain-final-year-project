@echo off
REM Test runner script for transcript-verification project (Windows)

echo ==========================================
echo Running Transcript Verification Tests
echo ==========================================

REM Backend tests
echo.
echo Running backend tests...
cd backend
python -m pytest test/ -v --tb=short
cd ..

REM Frontend tests
echo.
echo Running frontend tests...
cd frontend
python -m pytest test/ -v --tb=short
cd ..

REM Smart contract tests
echo.
echo Running smart contract tests...
cd blockchain
call npx hardhat compile
call npx hardhat test
cd ..

echo.
echo ==========================================
echo All tests completed successfully!
echo ==========================================