# PropertyGuard AI – Multi-Agent Real Estate Verification System 🏠🤖

PropertyGuard AI is a multi-agent fraud screening and document verification engine designed for real estate transactions. It detects data inconsistencies between property marketing listings and official title documents, catches duplicate postings across registry databases, and outputs verifiable risk assessments.

## Multi-Agent Pipeline & Architecture

The system uses CrewAI with Google Gemini LLMs alongside ChromaDB vector storage:

1. **Document Analysis Agent**: Inspects deed scans and text-based PDFs to identify true legal area, owner names, deed IDs, and missing documentation.
2. **Duplicate Detection Agent**: Queries vector embeddings of titles and locations in ChromaDB to flag existing or overlapping real estate listings.
3. **Claim Verification Agent**: Cross-examines portal listing claims against forensic legal facts extracted from the documents.
4. **Similarity Agent**: Computes semantic similarity metrics across historical listings.
5. **Risk Analysis Agent**: Scores fraud exposure from 0 to 100 and classifies issues by severity (High, Medium, Low).
6. **Coordinator Agent**: Synthesizes the individual outputs into a single JSON schema.

## Directory Structure

```
PropertyGuard_Project/
├── app.py                      # Streamlit interactive UI dashboard
├── requirements.txt            # Python dependencies
├── .env.example                # Sample environment configurations
├── README.md                   # System documentation
└── propertyguard_vdb/
    ├── __init__.py
    ├── api.py                  # FastAPI REST API (POST /verify)
    ├── schemas.py              # Pydantic schemas
    ├── ocr.py                  # PDF & Image multimodal document parser
    ├── duplicates.py           # Vector and keyword duplicate listing checks
    ├── agents.py               # 6-agent CrewAI orchestration
    └── store.py                # ChromaDB vector store wrapper
```

## Running the Application

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
Get a free Google Gemini key from Google AI Studio (https://aistudio.google.com/app/apikey).
```bash
cp .env.example .env
# Set your GEMINI_API_KEY in .env
```

### 3. Start Backend Server (FastAPI)
```bash
uvicorn propertyguard_vdb.api:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Start Frontend Interface (Streamlit)
```bash
streamlit run app.py
```