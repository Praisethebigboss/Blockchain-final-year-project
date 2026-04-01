# Product Requirements Document (PRD)
## Transcript Verification System

---

## 1. Overview

A blockchain-based system for issuing and verifying academic transcript documents. It generates a cryptographic hash of transcript files and stores it on an Ethereum blockchain, ensuring tamper-proof verification of document authenticity.

---

## 2. Problem Statement

Academic transcripts are frequently forged or tampered with. Traditional verification is manual, slow, and requires contacting the issuing institution. This system provides instant, trustless verification via blockchain immutability.

---

## 3. Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python / FastAPI |
| Hashing | SHA-256 (hashlib) |
| Blockchain | Solidity 0.8.20, Hardhat (local Ethereum node) |
| Web3 Client | Web3.py |
| Deployment | Hardhat deploy script (CommonJS) |

---

## 4. System Architecture

```
Client → FastAPI Backend → SHA-256 Hashing
                        → Web3.py → Local Hardhat Node → TranscriptRegistry Contract
```

### Component Breakdown

- **`backend/main.py`** — FastAPI application with three endpoints (hash, store, verify)
- **`backend/hash_service.py`** — SHA-256 hashing utility using Python's `hashlib`
- **`backend/blockchain.py`** — Web3.py integration layer connecting to the smart contract
- **`blockchain/contracts/TranscriptRegistry.sol`** — Solidity smart contract for on-chain hash storage
- **`blockchain/scripts/deploy.cjs`** — Hardhat deployment script

---

## 5. Functional Requirements

### 5.1 File Hashing

| Property | Detail |
|----------|--------|
| Endpoint | `POST /hash` |
| Input | Uploaded file (multipart/form-data) |
| Output | `{ hash: "<64-char hex>", filename: "<name>" }` |
| Validation | File must be present and non-empty |
| Behavior | Generates SHA-256 hash of file content |

### 5.2 Hash Storage on Blockchain

| Property | Detail |
|----------|--------|
| Endpoint | `POST /store` |
| Input | `{ hash: "<sha256>" }` |
| Output | `{ status: "stored", tx: "<transaction_hash>" }` |
| Validation | SHA-256 format enforced via regex `^[a-fA-F0-9]{64}$` |
| Behavior | Calls `issueTranscript()` on smart contract, waits for transaction receipt |

### 5.3 Hash Verification

| Property | Detail |
|----------|--------|
| Endpoint | `GET /verify/{hash_value}` |
| Input | SHA-256 hash as path parameter |
| Output | `{ hash: "<sha256>", exists: true/false }` |
| Validation | SHA-256 format enforced via regex |
| Behavior | Calls `verifyTranscript()` on smart contract, returns boolean result |

### 5.4 Health Check

| Property | Detail |
|----------|--------|
| Endpoint | `GET /` |
| Output | `{ message: "Backend is working" }` |

---

## 6. Smart Contract Specification

### Contract: `TranscriptRegistry.sol`

**Solidity Version:** `^0.8.0`

### Data Structures

```solidity
struct Transcript {
    string documentHash;
    address issuer;
    uint256 timestamp;
}

mapping(string => Transcript) public transcripts;
```

### Functions

| Function | Type | Description |
|----------|------|-------------|
| `issueTranscript(string hash)` | write | Stores hash with `msg.sender` as issuer and `block.timestamp` |
| `verifyTranscript(string hash)` | view | Returns `true` if hash exists (timestamp != 0) |
| `transcripts(string)` | public mapping | Returns full `Transcript` struct for a given hash |

---

## 7. API Error Handling

| HTTP Status | Condition |
|-------------|-----------|
| 200 | Successful operation |
| 400 | Invalid input (missing file, empty file, invalid hash format) |
| 500 | Internal server error (contract call failure) |
| 503 | Blockchain node not available |

---

## 8. Non-Functional Requirements

| Requirement | Detail |
|-------------|--------|
| Input Validation | SHA-256 format enforced via regex `^[a-fA-F0-9]{64}$` |
| Error Handling | Structured HTTP error responses with descriptive messages |
| Immutability | Once stored, hashes cannot be altered or deleted |
| Local Dev Environment | Hardhat node on `http://127.0.0.1:8545` |
| API Documentation | Auto-generated via FastAPI at `/docs` endpoint |
| Async Support | File upload endpoint uses `async` for non-blocking I/O |

---

## 9. Current Limitations & Gaps

| Area | Gap |
|------|-----|
| No Frontend | API-only; no web UI for end users |
| No Authentication | Anyone can store/verify hashes; no role-based access |
| No Duplicate Prevention | `issueTranscript()` silently overwrites existing entries |
| No File Storage | Only hash is stored; original files are not retained |
| Local Blockchain Only | Configured for Hardhat local node, no testnet/mainnet support |
| No Issuer Validation | Any address can issue transcripts; no institution registry |
| No Tests | No backend tests; blockchain test suite is stubbed |
| Hardcoded Contract Address | Address is hardcoded in `backend/blockchain.py` |
| No Pagination/Search | No way to list all issued transcripts |
| No Event Logging | Contract doesn't emit events for off-chain indexing |

---

## 10. Future Enhancements

1. **React/Next.js Frontend** — File upload UI, verification portal, institution dashboard
2. **Role-Based Access Control** — Only authorized institutions can issue transcripts
3. **Contract Events** — Emit `TranscriptIssued(hash, issuer, timestamp)` for indexing
4. **Duplicate Check** — Revert in contract if hash already exists
5. **Testnet Deployment** — Sepolia/Goerli config with Infura/Alchemy
6. **IPFS Integration** — Store encrypted original documents alongside hashes
7. **Batch Operations** — Upload and issue multiple transcripts in one transaction
8. **API Authentication** — JWT or API key-based auth for institutional users
9. **Unit & Integration Tests** — Pytest for backend, Hardhat tests for contract
10. **CI/CD Pipeline** — Automated lint, test, and deploy

---

## 11. User Stories

### Issuer (University)

> As an issuer, I upload a transcript PDF, get its hash, and store it on the blockchain so students can share verifiable credentials.

**Acceptance Criteria:**
- Upload transcript file via API
- Receive SHA-256 hash of the file
- Hash is stored on-chain with issuer address and timestamp
- Transaction hash returned as proof

### Verifier (Employer)

> As a verifier, I input a transcript hash and instantly confirm whether it was legitimately issued on-chain.

**Acceptance Criteria:**
- Provide a 64-character hex hash to the verification endpoint
- Receive a boolean response indicating if the hash exists on-chain
- Response returned within seconds

### Student

> As a student, I receive a transcript and a verification link/hash that I can share with employers.

**Acceptance Criteria:**
- Receive transcript document from issuing institution
- Receive corresponding SHA-256 hash or verification link
- Hash can be independently verified by any third party

---

## 12. Project Structure

```
transcript-verification/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── hash_service.py      # SHA-256 hashing utility
│   └── blockchain.py        # Web3 integration layer
├── blockchain/
│   ├── contracts/
│   │   └── TranscriptRegistry.sol   # Solidity smart contract
│   ├── scripts/
│   │   └── deploy.cjs               # Hardhat deploy script
│   ├── hardhat.config.cjs           # Hardhat configuration
│   └── package.json                 # Node.js dependencies
└── docs/
    └── PRD.md               # This document
```

---

## 13. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-29 | System Analysis | Initial PRD based on codebase analysis |
