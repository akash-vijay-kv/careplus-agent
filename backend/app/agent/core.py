"""Core Agno agent setup for CarePlus medical assistant."""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.postgres import PostgresDb

from app.config import settings
from app.agent.instructions import SYSTEM_PROMPT, GUEST_CONTEXT, LOGGED_IN_CONTEXT
from app.database import SessionLocal
from app.models.user import User
from app.tools.appointment_tools import AppointmentTools
from app.tools.medication_tools import MedicationTools
from app.tools.blood_result_tools import BloodResultTools
from app.tools.health_profile_tools import HealthProfileTools
from app.tools.address_tools import AddressTools
from app.tools.consultation_tools import ConsultationTools
from app.tools.emergency_tools import EmergencyTools
from app.tools.database_tools import DatabaseQueryTools
from app.tools.order_tools import OrderTools


def _get_agno_db_url() -> str:
    """Get the database URL in a format compatible with Agno's PostgresDb."""
    return settings.database_url


def _get_user_name(db_session, user_id: int) -> str:
    """Look up the full name of a user by ID.

    Parameters
    ----------
    db_session : Session
        SQLAlchemy database session.
    user_id : int
        The user's ID.

    Returns
    -------
    str
        The user's full name, or "User" if not found.
    """
    user = db_session.query(User).filter(User.id == user_id).first()
    if user:
        return f"{user.first_name} {user.last_name}"
    return "User"


def create_agent(session_id: str | None = None, user_id: int | None = None) -> Agent:
    """Create and return a configured CarePlus agent instance.

    Parameters
    ----------
    session_id : str | None
        Optional session identifier for conversation continuity.
    user_id : int | None
        Authenticated user ID. None indicates a guest session.

    Returns
    -------
    Agent
        Configured Agno agent with toolkits based on auth state.
    """
    db_session = SessionLocal()

    agno_db = PostgresDb(
        db_url=_get_agno_db_url(),
        session_table="agno_sessions",
    )

    if user_id is not None:
        user_name = _get_user_name(db_session, user_id)
        tools = [
            AppointmentTools(db_session=db_session, user_id=user_id),
            MedicationTools(db_session=db_session, user_id=user_id),
            BloodResultTools(db_session=db_session, user_id=user_id),
            HealthProfileTools(db_session=db_session, user_id=user_id),
            AddressTools(db_session=db_session, user_id=user_id),
            ConsultationTools(db_session=db_session, user_id=user_id),
            EmergencyTools(user_id=user_id),
            OrderTools(db_session=db_session, user_id=user_id),
            DatabaseQueryTools(db_session=db_session),
        ]
        context_instruction = LOGGED_IN_CONTEXT.format(name=user_name)
    else:
        tools = [
            EmergencyTools(user_id=0),
            DatabaseQueryTools(db_session=db_session),
        ]
        context_instruction = GUEST_CONTEXT

    agent = Agent(
        name="CarePlus Medical Assistant",
        model=OpenAIChat(id="gpt-4o-mini", api_key=settings.openai_api_key),
        db=agno_db,
        tools=tools,
        instructions=[SYSTEM_PROMPT, context_instruction],
        add_history_to_context=True,
        num_history_runs=10,
        markdown=True,
        session_id=session_id,
    )

    return agent
