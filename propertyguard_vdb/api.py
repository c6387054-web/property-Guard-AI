import os
import json
from datetime import datetime
from typing import List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from propertyguard_vdb.ocr import extract_text_from_documents
from propertyguard_vdb.agents import build_verification_crew
from propertyguard_vdb.duplicates import check_duplicates
from propertyguard_vdb.schemas import VerificationResponse

app = FastAPI(title="PropertyGuard AI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
def index():
    return {"status": "online", "system": "PropertyGuard Multi-Agent Verification"}

@app.post("/verify", response_model=VerificationResponse)
async def verify_property(
    title: str = Form(...),
    location: str = Form(...),
    owner: str = Form(...),
    area: float = Form(...),
    unit: str = Form(...),
    documents: List[UploadFile] = File(...)
):
    try:
        listing = {"title": title, "location": location, "owner": owner, "area": area, "unit": unit}
        doc_text = await extract_text_from_documents(documents)
        dup_info = check_duplicates(title, location, owner)
        crew = build_verification_crew(listing, doc_text, dup_info)
        result = crew.kickoff()

        if hasattr(result, "pydantic") and result.pydantic:
            data = result.pydantic.model_dump()
        elif isinstance(result, dict):
            data = result
        else:
            data = json.loads(str(result))

        data["report_id"] = "PG-" + datetime.now().strftime("%Y%m%d-%H%M%S")
        data["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        data["is_dummy"] = False
        return data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))