from web3 import Web3
import json

# Connect to local blockchain
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Your contract address
contract_address = "0x5FbDB2315678afecb367f032d93F642f64180aa3"


# ABI (paste it here)
abi = [
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
    }
]
  

contract = w3.eth.contract(address=contract_address, abi=abi)

# Default account (from Hardhat)
w3.eth.default_account = w3.eth.accounts[0]


def store_hash(hash_value):
    try:
        if not w3.is_connected():
            raise ConnectionError("Blockchain node is not connected")
        tx_hash = contract.functions.issueTranscript(hash_value).transact()
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt
    except ConnectionError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to store hash on blockchain: {str(e)}")


def verify_hash(hash_value):
    try:
        if not w3.is_connected():
            raise ConnectionError("Blockchain node is not connected")
        return contract.functions.verifyTranscript(hash_value).call()
    except ConnectionError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to verify hash on blockchain: {str(e)}")