from pydantic import BaseModel
from typing import List

class OwnFundsField(BaseModel):
    field_code: str
    description: str
    value: float
    justification: str

class OwnFundsReport(BaseModel):
    template_name: str
    fields: List[OwnFundsField]
