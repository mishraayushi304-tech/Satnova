from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class QueryRequest(BaseModel):
    image_id: str = Field(..., description="Uploaded satellite image ID")
    query: str = Field(..., description="Natural language question from the user")
    pair_id: Optional[str] = Field(None, description="Pair ID for bi-temporal comparison queries")

class ExecutionSummary(BaseModel):
    image_type: str = Field(..., description="Satellite sensor type (e.g. Sentinel-2, Landsat-8)")
    tools: List[str] = Field(..., description="List of AI models invoked")
    processing_time: str = Field(..., description="Total execution time in seconds")

class QueryResponse(BaseModel):
    image_id: str
    query: str
    task: str = Field(..., description="Classified AI task type (caption, vqa, grounding, etc.)")
    answer: str = Field(..., description="Natural language answer from AI models")
    confidence: float = Field(..., description="Confidence score of the answer (0-100)")
    model_used: List[str] = Field(..., description="AI model(s) used to generate the answer")
    execution_summary: ExecutionSummary
    overlay_image_path: Optional[str] = Field(None, description="Path to annotated/segmented output image")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional analysis metadata")
