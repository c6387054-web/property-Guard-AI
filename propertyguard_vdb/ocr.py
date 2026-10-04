import io
import os
from typing import List
from fastapi import UploadFile
from pypdf import PdfReader
from PIL import Image
import google.generativeai as genai

if os.environ.get("GEMINI_API_KEY"):
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

async def extract_text_from_documents(files: List[UploadFile]) -> str:
    extracted_text_chunks = []
    for file in files:
        contents = await file.read()
        filename = (file.filename or "").lower()

        if filename.endswith(".pdf"):
            reader = PdfReader(io.BytesIO(contents))
            pdf_text = ""
            for idx, page in enumerate(reader.pages):
                txt = page.extract_text() or ""
                pdf_text += f"\n--- Page {idx+1} ---\n" + txt
            
            if len(pdf_text.strip()) < 50 and os.environ.get("GEMINI_API_KEY"):
                try:
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    resp = model.generate_content([
                        {"mime_type": "application/pdf", "data": contents},
                        "Extract all text, owner names, deed numbers, plot dimensions, and boundary information."
                    ])
                    pdf_text = resp.text or ""
                except Exception:
                    pass
            extracted_text_chunks.append(f"Document [{file.filename}]:\n{pdf_text}")

        elif any(filename.endswith(ext) for ext in [".png", ".jpg", ".jpeg"]):
            if os.environ.get("GEMINI_API_KEY"):
                try:
                    img = Image.open(io.BytesIO(contents))
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    resp = model.generate_content([
                        img,
                        "Extract all visible text on this real estate deed/registry document, including property owner, square footage/marla, and survey plot numbers."
                    ])
                    extracted_text_chunks.append(f"Document Image [{file.filename}]:\n{resp.text}")
                except Exception:
                    extracted_text_chunks.append(f"Document Image [{file.filename}]: (OCR parsing error)")
            else:
                extracted_text_chunks.append(f"Document Image [{file.filename}]: (GEMINI_API_KEY not configured)")
    return "\n\n".join(extracted_text_chunks)