from workflow.graph import app as lead_lifecycle_graph

def run_lead_lifecycle_workflow(lead_id: str,
    org_id: str,
    event_type: str,
    metadata: dict | None = None,
):
    initial_state = {
        "lead_id": lead_id,
        "org_id": org_id,
        "current_event": event_type,
        "lead_context": {},
        "latest_action": None,
        "requires_approval": False,
        "next_wait_until": None,
        "outcome": "",
        "metadata": metadata or {},
    }

    return lead_lifecycle_graph.invoke(initial_state)
