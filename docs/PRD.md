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
| Frontend | Python / Streamlit | |

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

### 5.4 Get Transcript Details

| Property | Detail |
|----------|--------|
| Endpoint | `GET /transcript/{hash_value}` |
| Input | SHA-256 hash as path parameter |
| Output | `{ hash, document_hash, issuer, timestamp, issued_at }` |
| Validation | SHA-256 format enforced via regex |
| Behavior | Returns full transcript struct from contract mapping |

### 5.5 Store File on IPFS

| Property | Detail |
|----------|--------|
| Endpoint | `POST /store-file` |
| Input | Uploaded file (multipart/form-data) |
| Output | `{ hash, cid, filename }` |
| Validation | File must be present, non-empty, under 10MB |
| Behavior | Generates SHA-256 hash, encrypts with AES-256-GCM, uploads to IPFS, stores CID in metadata DB |

### 5.6 File Status

| Property | Detail |
|----------|--------|
| Endpoint | `GET /file-status/{hash_value}` |
| Input | SHA-256 hash as path parameter |
| Output | `{ hash, stored, filename, size, cid }` |
| Behavior | Returns file metadata if stored on IPFS |

### 5.7 Download File

| Property | Detail |
|----------|--------|
| Endpoint | `GET /download/{hash_value}` |
| Input | SHA-256 hash as path parameter |
| Output | File stream with Content-Disposition header |
| Behavior | Fetches encrypted file from IPFS, decrypts, returns original file |

### 5.8 Health Check

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
| 404 | Transcript not found (GET /transcript/{hash}) |
| 409 | Duplicate transcript (POST /store) |
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

| Area | Gap | Status |
|------|-----|--------|
| No Frontend | API-only; no web UI for end users | **Implemented** (Streamlit — 3-role pages) |
| Shareable Verification Link | No shareable link for students to share | **Implemented** |
| No Duplicate Prevention | `issueTranscript()` silently overwrites existing entries | **Implemented** (require check in contract) |
| Issuer Authentication | Anyone can issue transcripts — no login required | **Implemented** (username/password with bcrypt) |
| Verification Details | Verifier and Student see only boolean result — no issuer address or timestamp | **Implemented** (GET /transcript endpoint + UI display) |
| No File Storage | Only hash is stored; original files are not retained | **Implemented** (IPFS + AES-256-GCM encryption) |
| Hardcoded Contract Address | Address is hardcoded in `backend/blockchain.py` | **Implemented** (reads from .env or contract-config.json) |
| Local Blockchain Only | Configured for Hardhat local node, no testnet/mainnet support | **Implemented** (sepolia/mainnet via env) |
| No Issuer Validation | Any address can issue transcripts; no institution registry | Open |
| No Pagination/Search | No way to list all issued transcripts | **Implemented** (getTotalCount, getHashes in contract + /transcripts API) |
| No Event Logging | Contract doesn't emit events for off-chain indexing | **Implemented** (TranscriptIssued event) |
| No Tests | No backend tests | **Implemented** (91 pytest tests, all pass) |

---

## 10. Future Enhancements

1. ~~**Frontend**~~ — **Done** — Streamlit 3-role pages (Issuer, Verifier, Student)
2. ~~**Shareable Verification Link**~~ — **Done** — URL-based hash pre-fill and auto-verify
3. ~~**Duplicate Check**~~ — **Done** — Revert in contract if hash already exists
4. ~~**Issuer Authentication**~~ — **Done** — Username/password login with bcrypt, protected Issuer portal
5. ~~**IPFS Integration**~~ — **Done** — Store encrypted original documents with AES-256-GCM
6. ~~**Contract Events**~~ — **Done** — Emit `TranscriptIssued(hash, issuer, timestamp)` for indexing
7. ~~**List Transcripts**~~ — **Done** — Paginated /transcripts endpoint with getTotalCount, getHashes
8. ~~**Unit & Integration Tests**~~ — **Done** — 91 pytest tests for backend
9. ~~**Batch Operations**~~ — **Done** — /batch-store endpoint for multiple transcripts
10. ~~**Testnet Deployment**~~ — **Done** — Sepolia config, hardhat networks, deployment ready
11. **CI/CD Pipeline** — Automated lint, test, and deploy

---

## 11. User Stories

### Issuer (University)

> As an issuer, I upload a transcript PDF, get its hash, and store it on the blockchain so students can share verifiable credentials.

**Acceptance Criteria:**
- Upload transcript file via API
- Receive SHA-256 hash of the file
- Hash is stored on-chain with issuer address and timestamp
- Transaction hash returned as proof
- Shareable verification link generated for easy sharing

### Verifier (Employer)

> As a verifier, I input a transcript hash and instantly confirm whether it was legitimately issued on-chain.

**Acceptance Criteria:**
- Provide a 64-character hex hash to the verification endpoint
- Receive a boolean response indicating if the hash exists on-chain
- Response returned within seconds
- Can also open a shareable verification link with hash pre-filled

### Student

> As a student, I receive a transcript and a verification link/hash that I can share with employers.

**Acceptance Criteria:**
- Receive transcript document from issuing institution
- Receive corresponding SHA-256 hash or verification link
- Hash can be independently verified by any third party
- Shareable link opens verification page with hash auto-filled

---

## 12. Project Structure

```
transcript-verification/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── hash_service.py      # SHA-256 hashing utility
│   ├── blockchain.py        # Web3 integration layer
│   ├── storage_service.py  # IPFS + AES encryption
│   ├── storage_db.json     # File metadata (auto-created)
│   ├── .env               # Encryption key
│   └── requirements.txt
├── blockchain/
│   ├── contracts/
│   │   └── TranscriptRegistry.sol   # Solidity smart contract
│   ├── scripts/
│   │   └── deploy.cjs               # Hardhat deploy script
│   ├── test/
│   │   └── TranscriptRegistry.cjs   # Hardhat tests
│   ├── hardhat.config.cjs           # Hardhat configuration
│   └── package.json                 # Node.js dependencies
├── frontend/
│   ├── main.py              # Hub — role selection page
│   ├── auth.py              # Authentication (bcrypt, session)
│   ├── config.py            # Shared settings
│   ├── backend_client.py    # Backend API client
│   ├── start_all.py         # One-click startup script
│   ├── requirements.txt     # Python dependencies
│   ├── data/                # User store (users.json)
│   └── pages/
│       ├── Login.py         # Issuer login / account creation
│       ├── 1_Issuer.py      # Issuer portal (protected)
│       ├── 2_Verifier.py    # Verifier portal (public)
│       └── 3_Student.py     # Student portal (public)
└── docs/
    └── PRD.md               # This document
```

---

## 13. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-29 | System Analysis | Initial PRD based on codebase analysis |
| 1.1 | 2026-04-04 | Build | Added Streamlit frontend with Issue/Verify tabs |
| 1.2 | 2026-04-04 | Build | Added shareable verification link feature |
| 1.3 | 2026-04-04 | Build | Added duplicate prevention with require check in contract, Hardhat tests |
| 1.4 | 2026-04-04 | Build | Refactored frontend to 3-role pages (Issuer/Verifier/Student) with authentication |
| 1.5 | 2026-04-04 | Build | Fixed verification link bug — get_verification_url() now points to Student page |
| 1.6 | 2026-04-04 | Build | Replaced passlib with raw bcrypt (compatibility fix), added start_all.py one-click startup |
| 1.7 | 2026-04-07 | Build | Added /transcript/{hash} endpoint, verifier and student pages now display issuer address and timestamp |
| 1.8 | 2026-04-07 | Build | Added IPFS file storage with AES-256-GCM encryption — store-file, file-status, download endpoints |
| 1.9 | 2026-04-13 | Build | Added contract events (TranscriptIssued), list transcripts with pagination, 91 backend tests |
| 2.0 | 2026-04-13 | Build | Added batch operations (/batch-store) for multiple transcripts, 96 tests total |
| 2.1 | 2026-04-13 | Build | Added testnet deployment (Sepolia), Hardhat network configs |
