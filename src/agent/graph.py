from langgraph.graph import StateGraph, END

from src.agent.state import AgentState
from src.agent.nodes import pre_process_transactions, detect_subscriptions_and_recommend

def build_graph() -> StateGraph:
    """Builds the LangGraph execution graph for the AI Expense Auditor."""
    
    # 1. Initialize Graph with State Definition
    workflow = StateGraph(AgentState)
    
    # 2. Add Nodes
    workflow.add_node("pre_process", pre_process_transactions)
    workflow.add_node("detect_and_recommend", detect_subscriptions_and_recommend)
    
    # 3. Define Edges
    workflow.set_entry_point("pre_process")
    workflow.add_edge("pre_process", "detect_and_recommend")
    workflow.add_edge("detect_and_recommend", END)
    
    # 4. Compile
    return workflow.compile()

# Instantiate the graph for execution later
audit_graph = build_graph()
