"""Core Agno agent setup for CarePlus medical assistant."""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.postgres import PostgresDb

from app.config import settings
from app.agent.instructions import SYSTEM_PROMPT
from app.database import SessionLocal
from app.tools.appointment_tools import AppointmentTools
from app.tools.medication_tools import MedicationTools
from app.tools.blood_result_tools import BloodResultTools
from app.tools.health_profile_tools import HealthProfileTools
from app.tools.address_tools import AddressTools
from app.tools.consultation_tools import ConsultationTools
from app.tools.emergency_tools import EmergencyTools


def _get_agno_db_url() -> str:
    """Get the database URL in a format compatible with Agno's PostgresDb."""
    return settings.database_url


def create_agent(session_id: str | None = None) -> Agent:
    """Create and return a configured CarePlus agent instance.

    Parameters
    ----------
    session_id : str | None
        Optional session identifier for conversation continuity.

    Returns
    -------
    Agent
        Configured Agno agent with all toolkits attached.
    """
    db_session = SessionLocal()

    agno_db = PostgresDb(
        db_url=_get_agno_db_url(),
        session_table="agno_sessions",
    )

    agent = Agent(
        name="CarePlus Medical Assistant",
        model=OpenAIChat(id="gpt-4o-mini", api_key=settings.openai_api_key),
        db=agno_db,
        tools=[
            AppointmentTools(db_session=db_session, user_id=settings.default_user_id),
            MedicationTools(db_session=db_session, user_id=settings.default_user_id),
            BloodResultTools(db_session=db_session, user_id=settings.default_user_id),
            HealthProfileTools(db_session=db_session, user_id=settings.default_user_id),
            AddressTools(db_session=db_session, user_id=settings.default_user_id),
            ConsultationTools(db_session=db_session, user_id=settings.default_user_id),
            EmergencyTools(user_id=settings.default_user_id),
        ],
        instructions=[SYSTEM_PROMPT],
        add_history_to_context=True,
        num_history_runs=10,
        markdown=True,
        session_id=session_id,
    )

    return agent
