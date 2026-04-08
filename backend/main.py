import re
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from hash_service import generate_file_hash
from blockchain import store_hash, verify_hash, get_transcript, DuplicateTranscriptError
from storage_service import store_file, get_file, file_exists, get_file_info

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


@app.get("/transcript/{hash_value}")
def get_transcript_endpoint(hash_value: str):
    if not HASH_PATTERN.match(hash_value):
        raise HTTPException(status_code=400, detail="Invalid SHA256 hash format")
    try:
        result = get_transcript(hash_value)
        if result["timestamp"] == 0:
            raise HTTPException(status_code=404, detail="Transcript not found")
        return {
            "hash": hash_value,
            "document_hash": result["document_hash"],
            "issuer": result["issuer"],
            "timestamp": result["timestamp"],
            "issued_at": datetime.fromtimestamp(result["timestamp"]).isoformat(),
        }
    except HTTPException:
        raise
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Blockchain node not available")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/store-file")
async def store_file_endpoint(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")
    try:
        file_hash = generate_file_hash(content)
        result = store_file(content, file.filename, file_hash)
        return {
            "hash": file_hash,
            "cid": result["cid"],
            "filename": result["filename"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/file-status/{hash_value}")
def file_status(hash_value: str):
    if not HASH_PATTERN.match(hash_value):
        raise HTTPException(status_code=400, detail="Invalid SHA256 hash format")
    exists = file_exists(hash_value)
    if not exists:
        return {"hash": hash_value, "stored": False}
    info = get_file_info(hash_value)
    return {
        "hash": hash_value,
        "stored": True,
        "filename": info["filename"],
        "size": info["size"],
        "cid": info["cid"],
    }


@app.get("/download/{hash_value}")
def download(hash_value: str):
    if not HASH_PATTERN.match(hash_value):
        raise HTTPException(status_code=400, detail="Invalid SHA256 hash format")
    try:
        result = get_file(hash_value)
        if not result:
            raise HTTPException(status_code=404, detail="File not found")
        return StreamingResponse(
            [result["data"]],
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{result["filename"]}"',
                "Content-Length": str(result["size"]),
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
