from pydantic import BaseModel
from typing import List, Optional

class ReconciliationRunRequest(BaseModel):
    crm_id: str
    report_ids: List[str]
    config_id: Optional[str] = None
