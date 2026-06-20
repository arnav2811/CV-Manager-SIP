"""
Headless CV Normalization Engine — FastAPI REST Wrapper
======================================================
Exposes the RapidFuzz-based normalizer as a production-ready REST
service with single and batch normalization endpoints.

Run:  python app.py
Docs: http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple
import os
import sys

# Add parent directory to path so we can import normalizer correctly if run directly from here
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from poc.normalizer_rapidfuzz import Normalizer

app = FastAPI(
    title="Headless CV Normalization Engine API",
    description="Production-grade REST API utilizing 3-layer algorithmic normalization for resume education credentials.",
    version="2.2.0"
)

# CORS middleware — allow all origins in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the production normalizer
# Assuming normalizer runs from poc/ or project root
base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, '..', 'data')
normalizer = Normalizer(data_dir=data_dir)

# Define schemas
class NormalizationRequest(BaseModel):
    raw_text: str = Field(..., description="The raw education string to normalize", json_schema_extra={"example": "B.Tech (Computer Science)"})

class AlternativeMatch(BaseModel):
    degree: str
    score: float

class NormalizationResponse(BaseModel):
    model_config = {
        "populate_by_name": True
    }
    
    input_text: str = Field(..., alias="input")
    layer_used: str
    canonical_degree: Optional[str]
    canonical_field: Optional[str]
    confidence: float
    status: str
    fuzzy_score: float
    alternatives: List[Tuple[str, float]]

class BatchNormalizationRequest(BaseModel):
    inputs: List[str] = Field(..., description="List of raw education strings to normalize")

class BatchNormalizationResponse(BaseModel):
    results: List[NormalizationResponse]

@app.get("/health", summary="Health check", tags=["System"])
def health_check():
    """Returns service status and loaded dictionary size."""
    return {
        "status": "healthy",
        "degree_aliases_loaded": len(normalizer.degree_aliases),
        "field_aliases_loaded": len(normalizer.field_aliases),
    }

@app.post("/api/v1/normalize", response_model=NormalizationResponse, summary="Normalize a single education text string")
def normalize_education_text(payload: NormalizationRequest):
    """
    Passes an unnormalized string to the 3-layer normalization pipeline:
    - **Layer 1**: Direct dictionary lookup.
    - **Layer 2**: Typo-resilient fuzzy similarity matching.
    - **Layer 3**: Basic rule/regex-based heuristic extraction.
    """
    raw_text = payload.raw_text.strip()
    if not raw_text:
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")
    
    result = normalizer.normalize(raw_text)
    
    if result['status'] == 'unresolved':
        raise HTTPException(
            status_code=422,
            detail=f"Could not reliably normalize '{payload.raw_text}'. No matches met confidence thresholds."
        )
    
    # Map key 'input' to schema alias
    return result

@app.post("/api/v1/normalize/batch", response_model=BatchNormalizationResponse, summary="Normalize a batch of education strings")
def batch_normalize_education_text(payload: BatchNormalizationRequest):
    """
    Processes a list of raw education strings in batch using the normalization engine.
    """
    if not payload.inputs:
        raise HTTPException(status_code=400, detail="Input list cannot be empty.")
        
    raw_results = normalizer.batch_normalize(payload.inputs)
    return {"results": raw_results}

if __name__ == "__main__":
    import uvicorn
    # Start the API server locally on port 8000
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
