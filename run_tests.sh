#!/bin/bash
# Test runner script for transcript-verification project

set -e

echo "=========================================="
echo "Running Transcript Verification Tests"
echo "=========================================="

# Backend tests
echo ""
echo "Running backend tests..."
cd backend
python -m pytest test/ -v --tb=short
cd ..

# Frontend tests
echo ""
echo "Running frontend tests..."
cd frontend
python -m pytest test/ -v --tb=short
cd ..

# Smart contract tests
echo ""
echo "Running smart contract tests..."
cd blockchain
npx hardhat compile
npx hardhat test
cd ..

echo ""
echo "=========================================="
echo "All tests completed successfully!"
echo "=========================================="