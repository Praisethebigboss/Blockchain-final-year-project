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
│   ├── scripts/        # Deployment scripts
│   └── test/           # Hardhat tests
├── frontend/            # Streamlit frontend
│   ├── main.py         # Hub — role selection
│   ├── auth.py         # Authentication logic
│   ├── config.py       # Shared settings
│   ├── backend_client.py
│   ├── requirements.txt
│   ├── data/           # User store (auto-created)
│   └── pages/
│       ├── Login.py    # Issuer login
│       ├── 1_Issuer.py # Issuer portal (protected)
│       ├── 2_Verifier.py # Verifier portal (public)
│       └── 3_Student.py  # Student portal (public)
└── docs/
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

```bash
cd backend
pip install fastapi uvicorn web3 pydantic
python -m uvicorn main:app --reload
```

### 4. Start Frontend

```bash
cd frontend
pip install -r requirements.txt
python -m streamlit run main.py
```

Frontend runs at `http://localhost:8501`.

## User Roles

### Issuer (University)
Access restricted — requires login. Issue transcripts, store hashes on-chain, and generate shareable verification links for students.

**Default credentials:** `admin / admin123`

### Verifier (Employer)
Public access. Enter a transcript hash to verify its existence on the blockchain.

### Student
Public access. Open a shareable verification link to check if a transcript has been issued.

## Features

### Shareable Verification Links
After storing a transcript, a verification link is generated:
```
http://localhost:8501/pages/3_Student.py?verify=a1b2c3d4e5f6...
```

### Issuer Authentication
Issuers must create an account and log in before issuing transcripts. Credentials stored in `frontend/data/users.json` (bcrypt hashed).

### Issue History
Issuers can view a history of all transcripts issued during their session.

### Duplicate Prevention
The smart contract prevents duplicate issuance of the same hash.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/hash` | Generate SHA-256 hash of uploaded file |
| POST | `/store` | Store hash on blockchain (returns 409 if duplicate) |
| GET | `/verify/{hash}` | Verify hash exists on blockchain |

## Tech Stack

- **Backend:** Python, FastAPI, Web3.py
- **Blockchain:** Solidity 0.8.20, Hardhat, Ethereum
- **Frontend:** Streamlit (Python)
- **Authentication:** bcrypt, passlib
