import os
import json
from web3 import Web3
from web3.eth import Eth
from web3 import HTTPProvider
from dotenv import load_dotenv

load_dotenv()

NETWORK_CONFIGS = {
    "localhost": "http://127.0.0.1:8545",
    "hardhat": "http://127.0.0.1:8545",
    "sepolia": "https://rpc.sepolia.org",
    "mainnet": "https://eth.llamarpc.com",
}

request_kwargs = {"timeout": 60}

_w3 = None

def _get_env(key, default=None):
    return os.environ.get(key, default)

def _get_contract_address():
    return _get_env("CONTRACT_ADDRESS") or _get_contract_address_from_file() or "0xDc64a140Aa3E981100a9becA4E685f962f0cF6C9"

def _get_contract_address_from_file():
    config_path = os.path.join(os.path.dirname(__file__), "contract-config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                return config.get("contract_address")
        except (JSONDecodeError, IOError):
            pass
    return None

def _get_rpc_url(network):
    return NETWORK_CONFIGS.get(network, network)

def _init_web3():
    global _w3
    if _w3 is None:
        network = _get_env("ETHEREUM_NETWORK", "localhost")
        rpc_url = _get_env("ETHEREUM_RPC_URL") or _get_rpc_url(network)
        _w3 = Web3(HTTPProvider(rpc_url, request_kwargs=request_kwargs))
    return _w3

def w3():
    return _init_web3()

contract_address = _get_contract_address()

abi = [
    {
        "type": "event",
        "name": "TranscriptIssued",
        "inputs": [
            {"indexed": True, "internalType": "string", "name": "hash", "type": "string"},
            {"indexed": True, "internalType": "address", "name": "issuer", "type": "address"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ]
    },
    {
        "inputs": [
            {"internalType": "string", "name": "hash", "type": "string"}
        ],
        "name": "issueTranscript",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "hash", "type": "string"}
        ],
        "name": "verifyTranscript",
        "outputs": [
            {"internalType": "bool", "name": "", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "", "type": "string"}
        ],
        "name": "transcripts",
        "outputs": [
            {"internalType": "string", "name": "documentHash", "type": "string"},
            {"internalType": "address", "name": "issuer", "type": "address"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getTotalCount",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "offset", "type": "uint256"},
            {"internalType": "uint256", "name": "limit", "type": "uint256"}
        ],
        "name": "getHashes",
        "outputs": [
            {"internalType": "string[]", "name": "", "type": "string[]"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]


def _get_contract():
    return w3().eth.contract(address=contract_address, abi=abi)


def _get_account():
    network = _get_env("ETHEREUM_NETWORK", "localhost")
    private_key = _get_env("PRIVATE_KEY")
    _w3 = w3()
    
    if private_key and network not in ("localhost", "hardhat"):
        account = _w3.eth.account.from_key(private_key)
        return account.address
    
    if _w3.eth.accounts:
        return _w3.eth.accounts[0]
    
    raise RuntimeError("No account available. Set PRIVATE_KEY in .env for non-local networks.")


class DuplicateTranscriptError(Exception):
    pass


def store_hash(hash_value):
    _w3 = w3()
    contract = _get_contract()
    account = _get_account()
    try:
        tx_hash = contract.functions.issueTranscript(hash_value).transact({"from": account})
        receipt = _w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt
    except DuplicateTranscriptError:
        raise
    except ValueError as e:
        error_message = str(e)
        if "Transcript already issued" in error_message:
            raise DuplicateTranscriptError("Transcript with this hash has already been issued")
        raise RuntimeError(f"Contract call failed: {error_message}")
    except Exception as e:
        error_str = str(e).lower()
        if "connection" in error_str or "refused" in error_str or "timeout" in error_str:
            raise ConnectionError("Blockchain node not available")
        raise RuntimeError(f"Failed to store hash on blockchain: {e}")


def verify_hash(hash_value):
    try:
        contract = _get_contract()
        result = contract.functions.verifyTranscript(hash_value).call()
        return result
    except Exception as e:
        print(f"Verify error: {e}")
        raise ConnectionError("Blockchain node not available - please ensure Hardhat is running")


def get_transcript(hash_value):
    try:
        contract = _get_contract()
        doc_hash, issuer, timestamp = contract.functions.transcripts(hash_value).call()
        return {
            "document_hash": doc_hash,
            "issuer": issuer,
            "timestamp": timestamp,
        }
    except Exception as e:
        print(f"Get transcript error: {e}")
        raise ConnectionError("Blockchain node not available - please ensure Hardhat is running")


def get_total_count():
    try:
        contract = _get_contract()
        return contract.functions.getTotalCount().call()
    except Exception as e:
        print(f"Get total count error: {e}")
        raise ConnectionError("Blockchain node not available")


def list_transcripts(offset=0, limit=20):
    try:
        contract = _get_contract()
        hashes = contract.functions.getHashes(offset, limit).call()
        transcripts = []
        for h in hashes:
            doc_hash, issuer, timestamp = contract.functions.transcripts(h).call()
            transcripts.append({
                "hash": h,
                "document_hash": doc_hash,
                "issuer": issuer,
                "timestamp": timestamp,
            })
        return transcripts
    except Exception as e:
        print(f"List transcripts error: {e}")
        raise ConnectionError("Blockchain node not available")


def record_verification(hash_value):
    try:
        _w3 = w3()
        contract = _get_contract()
        account = _get_account()
        tx_hash = contract.functions.recordVerification(hash_value).transact({"from": account})
        receipt = _w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt
    except Exception as e:
        print(f"Record verification error: {e}")
        raise ConnectionError("Failed to record verification")


def record_download(hash_value):
    try:
        _w3 = w3()
        contract = _get_contract()
        account = _get_account()
        tx_hash = contract.functions.recordDownload(hash_value).transact({"from": account})
        receipt = _w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt
    except Exception as e:
        print(f"Record download error: {e}")
        raise ConnectionError("Failed to record download")


def get_events(from_block=0, to_block="latest"):
    try:
        _w3 = w3()
        contract = _get_contract()
        
        issued_events = contract.events.TranscriptIssued().get_logs(
            fromBlock=from_block,
            toBlock=to_block
        )
        
        verified_events = contract.events.TranscriptVerified().get_logs(
            fromBlock=from_block,
            toBlock=to_block
        )
        
        downloaded_events = contract.events.TranscriptDownloaded().get_logs(
            fromBlock=from_block,
            toBlock=to_block
        )
        
        return {
            "issued": [
                {
                    "hash": e["args"]["hash"],
                    "issuer": e["args"]["issuer"],
                    "timestamp": e["args"]["timestamp"],
                    "block": e["blockNumber"],
                }
                for e in issued_events
            ],
            "verified": [
                {
                    "hash": e["args"]["hash"],
                    "verifier": e["args"]["verifier"],
                    "timestamp": e["args"]["timestamp"],
                    "block": e["blockNumber"],
                }
                for e in verified_events
            ],
            "downloaded": [
                {
                    "hash": e["args"]["hash"],
                    "downloader": e["args"]["downloader"],
                    "timestamp": e["args"]["timestamp"],
                    "block": e["blockNumber"],
                }
                for e in downloaded_events
            ],
        }
    except Exception as e:
        print(f"Get events error: {e}")
        return {"issued": [], "verified": [], "downloaded": []}