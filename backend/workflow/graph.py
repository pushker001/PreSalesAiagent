from langgraph.graph import StateGraph, END
from workflow.state import LeadLifecycleState
from workflow.node import (
    load_context,
    evaluate_trigger,
    run_booking_agent,
    run_follow_up_agent,
    run_conversation_agent,
    create_action,
    wait_for_approval,
    log_memory
)

def route_trigger(state: LeadLifecycleState):
    """This is our Conditional Edge! It decides which agent to run based on the event."""
    event = state.get("current_event")
    
    if event == "qualification_created":
        return "run_booking"
    elif event == "booking_link_sent":
        return "run_booking"
    elif event == "proposal_sent":
        return "run_follow_up"
    elif event == "message_received":
        return "run_conversation"
        
    return "end"

# 1. Initialize the Graph with our State Schema
workflow = StateGraph(LeadLifecycleState)

# 2. Add all of our Nodes
workflow.add_node("load_context", load_context)
workflow.add_node("evaluate_trigger", evaluate_trigger)
workflow.add_node("run_booking_agent", run_booking_agent)
workflow.add_node("run_follow_up_agent", run_follow_up_agent)
workflow.add_node("run_conversation_agent", run_conversation_agent)
workflow.add_node("create_action", create_action)
workflow.add_node("wait_for_approval", wait_for_approval)
workflow.add_node("log_memory", log_memory)

# 3. Set the Entry Point
workflow.set_entry_point("load_context")

# 4. Connect load_context to evaluate_trigger
workflow.add_edge("load_context", "evaluate_trigger")

# 5. Add Conditional Edges (The Router)
workflow.add_conditional_edges(
    "evaluate_trigger",
    route_trigger,
    {
        "run_booking": "run_booking_agent",
        "run_follow_up": "run_follow_up_agent",
        "run_conversation": "run_conversation_agent",
        "end": END
    }
)

# 6. Route all agents back to the final common steps
for agent_node in ["run_booking_agent", "run_follow_up_agent", "run_conversation_agent"]:
    workflow.add_edge(agent_node, "create_action")

workflow.add_edge("create_action", "wait_for_approval")
workflow.add_edge("wait_for_approval", "log_memory")
workflow.add_edge("log_memory", END)

# 7. Compile it into an executable app
app = workflow.compile()