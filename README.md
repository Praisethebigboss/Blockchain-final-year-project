# Transcript Verification

A blockchain-based system for issuing and verifying academic transcript documents. Generates a SHA-256 hash of transcript files and stores it on an Ethereum blockchain via a Solidity smart contract.

## Project Structure

```
transcript-verification/
├── backend/              # FastAPI backend
│   ├── main.py          # API endpoints
│   ├── hash_service.py  # SHA-256 hashing
│   └── blockchain.py     # Web3 integration
├── blockchain/          # Hardhat project
│   ├── contracts/       # Solidity smart contracts
│   └── scripts/         # Deployment scripts
├── frontend/            # Streamlit frontend
│   ├── main.py         # Streamlit app
│   ├── backend_client.py
│   └── requirements.txt
└── docs/                # Documentation
    └── PRD.md
```

## Quick Start

### 1. Start Hardhat Node

```bash
cd blockchain
npx hardhat node
```

### 2. Deploy Contract

In a new terminal:

```bash
cd blockchain
npx hardhat run scripts/deploy.cjs --network localhost
```

### 3. Start Backend

In a new terminal:

```bash
cd backend
pip install fastapi uvicorn web3 pydantic
python -m uvicorn main:app --reload
```

### 4. Start Frontend

In a new terminal:

```bash
cd frontend
pip install -r requirements.txt
python -m streamlit run main.py
```

Frontend runs at `http://localhost:8501`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/hash` | Generate SHA-256 hash of uploaded file |
| POST | `/store` | Store hash on blockchain |
| GET | `/verify/{hash}` | Verify hash exists on blockchain |

## Tech Stack

- **Backend:** Python, FastAPI, Web3.py
- **Blockchain:** Solidity 0.8.20, Hardhat, Ethereum
- **Frontend:** Streamlit
