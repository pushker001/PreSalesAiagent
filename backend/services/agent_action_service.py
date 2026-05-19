from datetime import datetime, timezone

from models.agent_action import AgentAction
from models.enums import AgentActionStatus


OPEN_ACTION_STATUSES = {
    AgentActionStatus.PENDING_REVIEW,
    AgentActionStatus.APPROVED,
    AgentActionStatus.SENT,
}


def create_agent_action(db, action_data: dict):
    action = AgentAction(**action_data)
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


def get_agent_actions(db, org_id: str, status: str | None = None):
    query = db.query(AgentAction).filter(AgentAction.org_id == org_id)

    if status:
        query = query.filter(AgentAction.status == status)

    return query.order_by(AgentAction.created_at.desc()).all()


def get_agent_action_by_id(db, action_id: str, org_id: str):
    return (
        db.query(AgentAction)
        .filter(AgentAction.id == action_id, AgentAction.org_id == org_id)
        .first()
    )


def find_open_agent_action(db, org_id: str, lead_id: str, action_type):
    return (
        db.query(AgentAction)
        .filter(
            AgentAction.org_id == org_id,
            AgentAction.lead_id == lead_id,
            AgentAction.action_type == action_type,
            AgentAction.status.in_(OPEN_ACTION_STATUSES),
        )
        .order_by(AgentAction.created_at.desc())
        .first()
    )


def approve_agent_action(db, action_id: str, org_id: str, approved_by: str):
    action = get_agent_action_by_id(db, action_id, org_id)
    if not action:
        return None

    action.status = AgentActionStatus.APPROVED
    action.approved_by = approved_by
    action.approved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(action)
    return action


def dismiss_agent_action(db, action_id: str, org_id: str):
    action = get_agent_action_by_id(db, action_id, org_id)
    if not action:
        return None

    action.status = AgentActionStatus.DISMISSED

    db.commit()
    db.refresh(action)
    return action


def mark_agent_action_sent(db, action_id: str, org_id: str):
    action = get_agent_action_by_id(db, action_id, org_id)
    if not action:
        return None

    action.status = AgentActionStatus.SENT
    action.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(action)
    return action


def complete_agent_action(db, action_id: str, org_id: str):
    action = get_agent_action_by_id(db, action_id, org_id)
    if not action:
        return None

    action.status = AgentActionStatus.COMPLETED
    action.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(action)
    return action


def fail_agent_action(db, action_id: str, org_id: str):
    action = get_agent_action_by_id(db, action_id, org_id)
    if not action:
        return None

    action.status = AgentActionStatus.FAILED

    db.commit()
    db.refresh(action)
    return action
