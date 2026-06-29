"""Load test suite for the CarePlus Medical Assistant API.

Simulates ~50 concurrent users interacting with the application through
health checks, authentication, session management, and chat conversations.

Usage:
    # Web UI mode (default)
    locust -f locustfile.py --host http://localhost:8000

    # Headless mode for ~50 users
    locust -f locustfile.py --host http://localhost:8000 \
        --headless -u 50 -r 5 --run-time 5m
"""

import random
import uuid

from locust import HttpUser, between, tag, task

# ---------------------------------------------------------------------------
# Demo credentials seeded in db/init.sql
# ---------------------------------------------------------------------------
DEMO_USERS: list[dict[str, str]] = [
    {"email": "sarah.johnson@email.com", "password": "sarah123"},
    {"email": "john.doe@email.com", "password": "john123"},
]

# ---------------------------------------------------------------------------
# Chat prompts grouped by domain to simulate realistic conversations
# ---------------------------------------------------------------------------
APPOINTMENT_PROMPTS: list[str] = [
    "What appointments do I have coming up?",
    "Can you show me my upcoming appointments?",
    "When is my next doctor visit?",
]

MEDICATION_PROMPTS: list[str] = [
    "What medications am I currently taking?",
    "Show me my medication list.",
    "Do I have any prescriptions that need refilling?",
]

HEALTH_PROMPTS: list[str] = [
    "What is my blood type?",
    "Show me my health profile.",
    "What allergies do I have on file?",
]

BLOOD_RESULT_PROMPTS: list[str] = [
    "Show me my latest blood test results.",
    "What were my cholesterol levels last time?",
    "How has my blood sugar trended over the past year?",
]

ORDER_PROMPTS: list[str] = [
    "What is the status of my medicine orders?",
    "Do I have any orders being shipped?",
    "Show me my order history.",
]

GUEST_PROMPTS: list[str] = [
    "I have a headache and slight fever, what should I do?",
    "What are common symptoms of the flu?",
    "When should I go to the emergency room?",
]

ALL_AUTHENTICATED_PROMPTS: list[str] = (
    APPOINTMENT_PROMPTS
    + MEDICATION_PROMPTS
    + HEALTH_PROMPTS
    + BLOOD_RESULT_PROMPTS
    + ORDER_PROMPTS
)


class AuthenticatedPatient(HttpUser):
    """Simulates a logged-in patient browsing their health data.

    Workflow: health check -> login -> create session -> ask questions.
    Weight 3 means 75% of spawned users will be authenticated patients.
    """

    weight = 3
    wait_time = between(3, 8)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._token: str | None = None
        self._session_id: str | None = None

    def on_start(self) -> None:
        """Log in and create a chat session before running tasks."""
        self._login()
        self._create_session()

    # -- Setup helpers -------------------------------------------------------

    def _login(self) -> None:
        """Authenticate with a randomly chosen demo user."""
        credentials = random.choice(DEMO_USERS)
        with self.client.post(
            "/api/auth/login",
            json=credentials,
            name="/api/auth/login",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                self._token = data.get("token")
                resp.success()
            else:
                resp.failure(f"Login failed: {resp.status_code}")

    def _create_session(self) -> None:
        """Fetch a fresh chat session ID."""
        with self.client.get(
            "/api/chat/session",
            name="/api/chat/session",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                self._session_id = resp.json().get("session_id")
                resp.success()
            else:
                self._session_id = str(uuid.uuid4())
                resp.failure(f"Session creation failed: {resp.status_code}")

    # -- Tasks ---------------------------------------------------------------

    @tag("health")
    @task(5)
    def check_health(self) -> None:
        """Hit the health endpoint — lightweight canary check."""
        self.client.get("/api/health", name="/api/health")

    @tag("chat")
    @task(10)
    def send_chat_message(self) -> None:
        """Send a random authenticated chat message."""
        prompt = random.choice(ALL_AUTHENTICATED_PROMPTS)
        payload = {
            "message": prompt,
            "session_id": self._session_id or str(uuid.uuid4()),
            "token": self._token,
        }
        with self.client.post(
            "/api/chat",
            json=payload,
            name="/api/chat [authenticated]",
            catch_response=True,
            timeout=120,
        ) as resp:
            if resp.status_code == 200:
                body = resp.json()
                if body.get("message"):
                    resp.success()
                else:
                    resp.failure("Empty agent response")
            else:
                resp.failure(f"Chat failed: {resp.status_code}")

    @tag("chat", "stream")
    @task(3)
    def send_chat_stream(self) -> None:
        """Send a chat message and consume the SSE stream."""
        prompt = random.choice(ALL_AUTHENTICATED_PROMPTS)
        payload = {
            "message": prompt,
            "session_id": self._session_id or str(uuid.uuid4()),
            "token": self._token,
        }
        with self.client.post(
            "/api/chat/stream",
            json=payload,
            name="/api/chat/stream [authenticated]",
            catch_response=True,
            timeout=120,
            stream=True,
        ) as resp:
            if resp.status_code == 200:
                chunks_received = 0
                for line in resp.iter_lines():
                    if line:
                        chunks_received += 1
                if chunks_received > 0:
                    resp.success()
                else:
                    resp.failure("No SSE chunks received")
            else:
                resp.failure(f"Stream failed: {resp.status_code}")

    @tag("session")
    @task(2)
    def rotate_session(self) -> None:
        """Create a new session mid-conversation to simulate fresh chats."""
        self._create_session()


class GuestVisitor(HttpUser):
    """Simulates an unauthenticated visitor using emergency/guest features.

    Weight 1 means 25% of spawned users will be guests.
    """

    weight = 1
    wait_time = between(5, 12)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._session_id: str | None = None

    def on_start(self) -> None:
        """Create a chat session."""
        self._create_session()

    def _create_session(self) -> None:
        """Fetch a fresh chat session ID."""
        with self.client.get(
            "/api/chat/session",
            name="/api/chat/session",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                self._session_id = resp.json().get("session_id")
                resp.success()
            else:
                self._session_id = str(uuid.uuid4())
                resp.failure(f"Session creation failed: {resp.status_code}")

    @tag("health")
    @task(5)
    def check_health(self) -> None:
        """Hit the health endpoint."""
        self.client.get("/api/health", name="/api/health")

    @tag("chat")
    @task(8)
    def send_guest_chat(self) -> None:
        """Send a guest chat message (no auth token)."""
        prompt = random.choice(GUEST_PROMPTS)
        payload = {
            "message": prompt,
            "session_id": self._session_id or str(uuid.uuid4()),
        }
        with self.client.post(
            "/api/chat",
            json=payload,
            name="/api/chat [guest]",
            catch_response=True,
            timeout=120,
        ) as resp:
            if resp.status_code == 200:
                body = resp.json()
                if body.get("message"):
                    resp.success()
                else:
                    resp.failure("Empty agent response")
            else:
                resp.failure(f"Chat failed: {resp.status_code}")

    @tag("session")
    @task(2)
    def rotate_session(self) -> None:
        """Start a new conversation."""
        self._create_session()


class QuickBrowser(HttpUser):
    """Simulates a fast user that only hits lightweight endpoints.

    Useful for measuring baseline API latency without LLM overhead.
    Set weight to 0 by default — enable via CLI tags or by changing weight.
    """

    weight = 0
    wait_time = between(1, 3)

    @tag("health")
    @task(3)
    def check_health(self) -> None:
        """Hit the health endpoint."""
        self.client.get("/api/health", name="/api/health")

    @tag("auth")
    @task(2)
    def login_flow(self) -> None:
        """Log in and immediately discard the token."""
        credentials = random.choice(DEMO_USERS)
        self.client.post(
            "/api/auth/login",
            json=credentials,
            name="/api/auth/login",
        )

    @tag("session")
    @task(1)
    def get_session(self) -> None:
        """Fetch a new session ID."""
        self.client.get("/api/chat/session", name="/api/chat/session")
