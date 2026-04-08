from web3 import Web3

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

contract_address = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

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
    }
]


def _get_contract():
    return w3.eth.contract(address=contract_address, abi=abi)


def _get_account():
    return w3.eth.accounts[0]


class DuplicateTranscriptError(Exception):
    pass


def store_hash(hash_value):
    try:
        if not w3.is_connected():
            raise ConnectionError("Blockchain node is not connected")
        contract = _get_contract()
        account = _get_account()
        try:
            tx_hash = contract.functions.issueTranscript(hash_value).transact({"from": account})
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            return receipt
        except ValueError as e:
            error_message = str(e)
            if "Transcript already issued" in error_message:
                raise DuplicateTranscriptError("Transcript with this hash has already been issued")
            raise RuntimeError(f"Contract call failed: {error_message}")
    except ConnectionError:
        raise
    except DuplicateTranscriptError:
        raise
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to store hash on blockchain: {str(e)}")


def verify_hash(hash_value):
    try:
        if not w3.is_connected():
            raise ConnectionError("Blockchain node is not connected")
        contract = _get_contract()
        return contract.functions.verifyTranscript(hash_value).call()
    except ConnectionError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to verify hash on blockchain: {str(e)}")


def get_transcript(hash_value):
    try:
        if not w3.is_connected():
            raise ConnectionError("Blockchain node is not connected")
        contract = _get_contract()
        doc_hash, issuer, timestamp = contract.functions.transcripts(hash_value).call()
        return {
            "document_hash": doc_hash,
            "issuer": issuer,
            "timestamp": timestamp,
        }
    except ConnectionError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to get transcript: {str(e)}")
