# app/schemas.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ForecastRequest(BaseModel):
    quarters: int = 2
    company: str = "TCS"
    include_market_data: bool = False
