from typing import Annotated, Dict, Any, List, TypedDict, Optional
from pydantic import BaseModel, Field

class SubscriptionDetail(BaseModel):
    merchant_name: str
    amount: float
    frequency: str  # monthly, yearly
    confidence_score: float = Field(ge=0, le=1)
    is_duplicate: bool = False
    notes: Optional[str] = None

class ActionableRecommendation(BaseModel):
    title: str
    description: str
    estimated_monthly_savings: float
    action_type: str  # cancel, downgrade, negotiate

class AuditOutput(BaseModel):
    subscriptions_found: List[SubscriptionDetail]
    recommendations: List[ActionableRecommendation]
    total_monthly_savings_potential: float

class AgentState(TypedDict):
    user_id: str
    transactions: List[Dict[str, Any]]
    
    # Pre-processed aggregations
    merchant_frequencies: Dict[str, Any]
    
    # LLM Identified state
    identified_subscriptions: List[Dict[str, Any]]
    
    # Final generated output
    final_output: Optional[AuditOutput]
    
    # Error handling
    error: Optional[str]
