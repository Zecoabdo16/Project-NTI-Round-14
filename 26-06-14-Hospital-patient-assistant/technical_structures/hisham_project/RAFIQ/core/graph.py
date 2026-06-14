# core/graph.py
from langgraph.graph import StateGraph, END
from core.state import PatientState
from agents.supervisor import supervisor_node
from agents.triage import triage_node
from agents.operations import operations_node

def route_after_supervisor(state: PatientState) -> str:
    """Routing logic based on intent"""
    if state['detected_intent'] == 'emergency':
        return 'triage'
    elif state['detected_intent'] == 'admin':
        return 'operations'
    elif state['detected_intent'] == 'medical':
        return 'medical_memory' # Build this in Week 2
    return END

# Build the Graph
workflow = StateGraph(PatientState)

# Add Nodes
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("triage", triage_node)
workflow.add_node("operations", operations_node)

# Set Entry Point
workflow.set_entry_point("supervisor")

# Add Edges
workflow.add_conditional_edges("supervisor", route_after_supervisor)
workflow.add_edge("triage", END) # For now, triage just flags and ends
workflow.add_edge("operations", END)

# Compile
app = workflow.compile()