# Transcript Verification

A blockchain-based system for issuing and verifying academic transcript documents. Generates a SHA-256 hash of transcript files and stores it on an Ethereum blockchain via a Solidity smart contract. Original files are encrypted and stored on IPFS.

## Project Structure

```
transcript-verification/
├── backend/              # FastAPI backend
│   ├── main.py          # API endpoints
│   ├── hash_service.py  # SHA-256 hashing
│   ├── blockchain.py     # Web3 integration
│   ├── storage_service.py # IPFS + AES encryption
│   ├── storage_db.json   # File metadata (auto-created)
│   ├── .env             # Encryption key (do not commit)
│   └── requirements.txt
├── blockchain/          # Hardhat project
│   ├── contracts/       # Solidity smart contracts
│   ├── scripts/        # Deployment scripts
│   └── test/           # Hardhat tests
├── frontend/            # Streamlit frontend
│   ├── main.py         # Hub — role selection
│   ├── auth.py         # Authentication logic
│   ├── config.py       # Shared settings
│   ├── backend_client.py
│   ├── start_all.py    # One-click startup script
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

### Prerequisites

1. **Node.js** — for Hardhat
2. **Python 3.10+** — for backend and frontend
3. **IPFS** — for file storage
   ```bash
   # Install IPFS: https://docs.ipfs.tech/install/
   # Or via Chocolatey:
   choco install ipfs
   # Initialize IPFS:
   ipfs init
   ```

### Option A — One-Click Startup (Recommended)

```bash
# Terminal 1 — IPFS Daemon (must be running for file storage)
ipfs daemon

# Terminal 2 — Start all other services
cd frontend
pip install -r requirements.txt
python start_all.py
```

This starts automatically:
- Hardhat node
- Contract deployment
- Backend (FastAPI on port 8000)
- Frontend (Streamlit on port 8501)

### Option B — Manual Start

**Terminal 1 — IPFS Daemon**
```bash
ipfs daemon
```

**Terminal 2 — Hardhat Node**
```bash
cd blockchain
npx hardhat node
```

**Terminal 3 — Deploy Contract**
```bash
cd blockchain
npx hardhat compile
npx hardhat run scripts/deploy.cjs --network localhost
```

**Terminal 4 — Backend**
```bash
cd backend
pip install -r requirements.txt
# Set encryption key (auto-generated, stored in .env)
python -m uvicorn main:app --reload
```

**Terminal 5 — Frontend**
```bash
cd frontend
pip install -r requirements.txt
python -m streamlit run main.py
```

Frontend runs at `http://localhost:8501`.

## User Roles

### Issuer (University)
Access restricted — requires login. Issue transcripts, store hashes on-chain, upload files to IPFS, and generate shareable verification links.

**Default credentials:** `admin / admin123`

### Verifier (Employer)
Public access. Enter a transcript hash to verify its existence on the blockchain and download the original file.

### Student
Public access. Open a shareable verification link to check if a transcript has been issued and download the original file.

## Features

### Blockchain Verification
Transcripts are verified by storing their SHA-256 hash on an Ethereum blockchain. The hash is immutable and cannot be tampered with.

### IPFS File Storage
Original transcript files are:
1. Encrypted with AES-256-GCM
2. Uploaded to IPFS
3. CIDs stored locally mapped to the hash

### Shareable Verification Links
After storing a transcript, a verification link is generated:
```
http://localhost:8501/pages/3_Student.py?verify=a1b2c3d4e5f6...
```

### Issuer Authentication
Issuers must create an account and log in before issuing transcripts. Credentials stored in `frontend/data/users.json` (bcrypt hashed).

### Issue History
Issuers can view all transcripts issued during their session.

### Duplicate Prevention
The smart contract prevents duplicate issuance of the same hash.

### Verification Details
When verifying a transcript, the issuer address and timestamp are displayed alongside the verification result.

### Original File Download
Verified transcripts can be downloaded as original files (issuer, verifier, and student can all download).

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/hash` | Generate SHA-256 hash of uploaded file |
| POST | `/store` | Store hash on blockchain (returns 409 if duplicate) |
| GET | `/verify/{hash}` | Verify hash exists on blockchain (returns boolean) |
| GET | `/transcript/{hash}` | Get full transcript details — issuer address, timestamp, document hash |
| POST | `/store-file` | Upload and encrypt file to IPFS |
| GET | `/file-status/{hash}` | Check if original file is stored |
| GET | `/download/{hash}` | Download original file |

## Tech Stack

- **Backend:** Python, FastAPI, Web3.py
- **Blockchain:** Solidity 0.8.20, Hardhat, Ethereum
- **Frontend:** Streamlit (Python)
- **Authentication:** bcrypt
- **File Storage:** IPFS + AES-256-GCM encryption

## Configuration

### Environment Variables (backend/.env)

```bash
# Required: Encryption key (auto-generated on first run)
TRANSCRIPT_ENCRYPTION_KEY=<32-byte hex key>

# Blockchain configuration
ETHEREUM_NETWORK=localhost  # Options: localhost, sepolia, mainnet
CONTRACT_ADDRESS=0x...     # Auto-populated after deploy
PRIVATE_KEY=<your key>       # Required for sepolia/mainnet

# IPFS configuration
IPFS_HOST=127.0.0.1
IPFS_PORT=5001
```

### Network Modes

| Network | Use | Requirements |
|---------|-----|--------------|
| `localhost` (default) | Development | Hardhat node runs automatically |
| `sepolia` | Testing | Infura/Alchemy RPC URL + private key |
| `mainnet` | Production | Infura/Alchemy RPC URL + private key |

### Switching Networks

1. Edit `backend/.env`:
   ```
   ETHEREUM_NETWORK=sepolia
   PRIVATE_KEY=0x...
   CONTRACT_ADDRESS=<deployed contract>
   ```

2. Deploy contract to the target network:
   ```bash
   cd blockchain
   npx hardhat run scripts/deploy.cjs --network sepolia
   ```

3. Start services (Hardhat will be skipped):
   ```bash
   python start_all.py
   ```

## Security

- **Files are encrypted before upload** — AES-256-GCM encryption ensures files are secure at rest
- **Encryption key** stored in `backend/.env` — never commit this file
- **Hash immutability** — once on blockchain, transcript hashes cannot be altered
- **Private key** — never commit; use environment variables only
