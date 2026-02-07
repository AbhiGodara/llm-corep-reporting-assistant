from pydantic import BaseModel, Field, validator
from typing import List, Optional
import json

class COREPField(BaseModel):
    field_code: str = Field(description="COREP template field code (e.g., OF_010)")
    description: str = Field(description="Field description")
    value: Optional[float] = Field(None, description="Field value in reporting currency")
    confidence: float = Field(0.0, description="Extraction confidence 0-1")
    justification: str = Field("", description="Regulatory justification")
    source_rule: str = Field("", description="Source regulatory rule")
    
    @validator('confidence')
    def validate_confidence(cls, v):
        return max(0.0, min(1.0, v))
    
    @validator('value')
    def validate_value(cls, v):
        if v is not None and v < 0:
            raise ValueError(f"Negative value {v} not allowed for COREP reporting")
        return v

class COREPReport(BaseModel):
    template: str = Field("C 01.00", description="COREP template code")
    fields: List[COREPField] = Field(default_factory=list)
    
    def to_json(self):
        return json.dumps(self.dict(), indent=2)
    
    @property
    def is_empty(self) -> bool:
        """Check if report has no values"""
        return all(f.value is None for f in self.fields)
    
    @property
    def confidence_score(self) -> float:
        """Average confidence of populated fields"""
        populated = [f for f in self.fields if f.value is not None]
        if not populated:
            return 0.0
        return sum(f.confidence for f in populated) / len(populated)
