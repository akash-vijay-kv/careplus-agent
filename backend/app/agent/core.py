"""Core Agno agent setup for CarePlus medical assistant."""

from agno.agent import Agent
from agno.models.base import Model
from agno.models.litellm import LiteLLM
from agno.models.openai import OpenAIChat
from agno.db.postgres import PostgresDb

from sqlalchemy.orm import Session

from app.config import settings
from app.agent.instructions import SYSTEM_PROMPT, GUEST_CONTEXT, LOGGED_IN_CONTEXT
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
from app.tools.shell_tools import ShellTools


def _get_agno_db_url() -> str:
    """Get the database URL in a format compatible with Agno's PostgresDb."""
    return settings.database_url


def _build_model() -> Model:
    """Build the chat model for the agent based on the configured provider.

    Selects between the direct OpenAI client and LiteLLM (proxy or direct)
    via ``settings.llm_provider``. Both providers use the same shared model
    id (``settings.llm_model_id``).

    Returns
    -------
    Model
        A configured Agno model instance.

    Raises
    ------
    ValueError
        If ``settings.llm_provider`` is not a supported value.
    """
    provider = settings.llm_provider.lower()

    if provider == "openai":
        return OpenAIChat(id=settings.llm_model_id, api_key=settings.openai_api_key)

    if provider == "litellm":
        # api_key/api_base are optional: LiteLLM falls back to its own env vars
        # (LITELLM_API_KEY) and provider defaults when these are unset.
        litellm_kwargs: dict[str, str] = {}
        if settings.litellm_api_key:
            litellm_kwargs["api_key"] = settings.litellm_api_key
        if settings.litellm_api_base:
            litellm_kwargs["api_base"] = settings.litellm_api_base
        return LiteLLM(id=settings.llm_model_id, **litellm_kwargs)

    raise ValueError(
        f"Unsupported llm_provider {settings.llm_provider!r}; "
        "expected 'openai' or 'litellm'."
    )


def _get_user_name(db_session: Session, user_id: int) -> str:
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


def create_agent(
    db_session: Session,
    session_id: str | None = None,
    user_id: int | None = None,
) -> Agent:
    """Create and return a configured CarePlus agent instance.

    The caller is responsible for closing the ``db_session`` after the
    agent interaction is complete.

    Parameters
    ----------
    db_session : Session
        Externally managed SQLAlchemy session. Must be closed by the caller.
    session_id : str | None
        Optional session identifier for conversation continuity.
    user_id : int | None
        Authenticated user ID. None indicates a guest session.

    Returns
    -------
    Agent
        Configured Agno agent with toolkits based on auth state.
    """
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
            ShellTools(),
        ]
        context_instruction = LOGGED_IN_CONTEXT.format(name=user_name)
    else:
        tools = [
            EmergencyTools(user_id=0),
            DatabaseQueryTools(db_session=db_session),
            ShellTools(),
        ]
        context_instruction = GUEST_CONTEXT

    agent = Agent(
        name="CarePlus Medical Assistant",
        model=_build_model(),
        db=agno_db,
        tools=tools,
        instructions=[SYSTEM_PROMPT, context_instruction],
        add_history_to_context=True,
        num_history_runs=10,
        markdown=True,
        session_id=session_id,
    )

    return agent
