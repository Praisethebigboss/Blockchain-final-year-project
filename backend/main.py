import re
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from hash_service import generate_file_hash
from blockchain import store_hash, verify_hash, DuplicateTranscriptError

app = FastAPI(title="Transcript Verification API")

HASH_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")


class HashRequest(BaseModel):
    hash: str


@app.get("/")
def home():
    return {"message": "Backend is working"}


@app.post("/hash")
async def hash_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty")
    file_hash = generate_file_hash(content)
    return {"hash": file_hash, "filename": file.filename}


@app.post("/store")
def store(request: HashRequest):
    hash_value = request.hash
    if not HASH_PATTERN.match(hash_value):
        raise HTTPException(status_code=400, detail="Invalid SHA256 hash format")
    try:
        receipt = store_hash(hash_value)
        return {"status": "stored", "tx": receipt.transactionHash.hex()}
    except DuplicateTranscriptError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Blockchain node not available")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/verify/{hash_value}")
def verify(hash_value: str):
    if not HASH_PATTERN.match(hash_value):
        raise HTTPException(status_code=400, detail="Invalid SHA256 hash format")
    try:
        result = verify_hash(hash_value)
        return {"hash": hash_value, "exists": result}
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Blockchain node not available")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
