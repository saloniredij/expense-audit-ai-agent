from collections import defaultdict
from typing import Dict, Any, List, Optional
import json

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.agent.state import AgentState, AuditOutput, SubscriptionDetail, ActionableRecommendation
from src.core.config import settings

def pre_process_transactions(state: AgentState) -> Dict[str, Any]:
    """
    Deterministic pre-processing node.
    Groups transactions by merchant and filters out obvious tiny one-offs
    to save on LLM context windows and improve accuracy.
    """
    transactions = state.get("transactions", [])
    
    merchant_groups = defaultdict(list)
    for txn in transactions:
        merchant = str(txn.get("merchant_name", "Unknown")).upper().strip()
        merchant_groups[merchant].append(txn)
        
    merchant_frequencies = {}
    for merchant, txns in merchant_groups.items():
        if len(txns) > 1:
            total_amount = sum(float(t.get("amount", 0)) for t in txns)
            avg_amount = total_amount / len(txns)
            merchant_frequencies[merchant] = {
                "count": len(txns),
                "total_amount": total_amount,
                "avg_amount": avg_amount,
                "dates": sorted([t.get("date") for t in txns if t.get("date")])
            }
            
    return {"merchant_frequencies": merchant_frequencies}

async def detect_subscriptions_and_recommend(state: AgentState) -> Dict[str, Any]:
    """
    Core LLM Node.
    Takes the deterministically grouped merchant frequencies and asks the LLM
    to classify them, identify duplicates, and formulate a savings plan.
    """
    frequencies = state.get("merchant_frequencies", {})
    if not frequencies:
        return {"final_output": AuditOutput(subscriptions_found=[], recommendations=[], total_monthly_savings_potential=0.0)}

    llm = ChatOpenAI(
        api_key=settings.OPENAI_API_KEY, 
        base_url=settings.OPENAI_BASE_URL,
        model="openai/gpt-4-turbo-preview", # OpenRouter requires vendor/ prefix
        temperature=0.1
    )
    
    # Langchain structured output requires Pydantic V1 mostly, but standard V2 works in newer versions.
    # We use `.with_structured_output` to force JSON schema adherence.
    structured_llm = llm.with_structured_output(AuditOutput)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert financial auditor AI. Your job is to analyze aggregated transaction data "
                   "and identify recurring subscriptions or regular bills. You must also spot any distinct "
                   "but similar subscriptions (e.g., Netflix and Hulu) or exact duplicates. "
                   "Provide actionable recommendations to save money. Be conservative in your estimates."),
        ("user", "Here is the aggregated transaction data for this user over the last 90 days:\n{data}")
    ])
    
    chain = prompt | structured_llm
    
    try:
        # Convert the frequencies dict to a string representation for the LLM
        data_str = json.dumps(frequencies, indent=2)
        result: AuditOutput = await chain.ainvoke({"data": data_str})
        return {"final_output": result}
    except Exception as e:
        return {"error": f"LLM Processing failed: {str(e)}"}

