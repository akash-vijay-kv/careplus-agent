"""Load test script for CarePlus Medical Assistant using Locust.

Simulates ~50 concurrent users performing realistic user journeys:
  - Login (authenticated users) or guest access
  - Creating chat sessions
  - Sending various chat messages (health queries, appointments, medications)
  - Health check polling

Usage:
    # Web UI mode (recommended for first run):
    locust -f loadtest/locustfile.py --host http://localhost:8000

    # Headless mode (~50 users, ramp up 5/sec, run for 2 minutes):
    locust -f loadtest/locustfile.py --host http://localhost:8000 \
        --headless -u 50 -r 5 -t 2m

    # Headless with HTML report:
    locust -f loadtest/locustfile.py --host http://localhost:8000 \
        --headless -u 50 -r 5 -t 2m --html loadtest/report.html
"""

import random
import uuid

from locust import HttpUser, between, task, tag

# ---------------------------------------------------------------------------
# Demo credentials seeded via db/init.sql
# ---------------------------------------------------------------------------
DEMO_USERS: list[dict[str, str]] = [
    {"email": "sarah.johnson@email.com", "password": "sarah123"},
    {"email": "john.doe@email.com", "password": "john123"},
]

# ---------------------------------------------------------------------------
# Realistic chat messages grouped by category
# ---------------------------------------------------------------------------
AUTHENTICATED_MESSAGES: list[str] = [
    "Show my upcoming appointments",
    "What medications am I currently taking?",
    "Can you check my blood test results?",
    "I need to reschedule my next appointment",
    "What are my allergies?",
    "Show my health profile",
    "Do I have any prescriptions that need refilling?",
    "What is my blood type?",
    "List my past medical procedures",
    "Can you show my consultation requests?",
    "What is my address on file?",
    "Show my medication adherence history",
    "I need to schedule a new appointment with a cardiologist",
    "What is the status of my latest order?",
    "Can you show my family medical history?",
]

GUEST_MESSAGES: list[str] = [
    "What are the symptoms of the flu?",
    "How do I manage high blood pressure?",
    "What should I do if I have a fever?",
    "Tell me about diabetes management",
    "What are common side effects of ibuprofen?",
    "How much water should I drink daily?",
    "What are signs of a heart attack?",
    "How can I improve my sleep quality?",
    "What is a normal resting heart rate?",
    "How do I check my blood pressure at home?",
]

EMERGENCY_MESSAGES: list[str] = [
    "I'm having severe chest pain",
    "I can't breathe properly",
    "I think I'm having an allergic reaction",
]


class AuthenticatedUser(HttpUser):
    """Simulates a logged-in patient interacting with the chat agent.

    Weight 3 means 75% of spawned users will be authenticated.
    """

    weight = 3
    wait_time = between(3, 8)

    def on_start(self) -> None:
        """Login and create an initial chat session."""
        self.token: str | None = None
        self.session_id: str = str(uuid.uuid4())
        self._login()
        self._new_session()

    def _login(self) -> None:
        """Authenticate with a random demo user."""
        creds = random.choice(DEMO_USERS)
        with self.client.post(
            "/api/auth/login",
            json=creds,
            name="/api/auth/login",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("token")
                resp.success()
            else:
                resp.failure(f"Login failed: {resp.status_code}")

    def _new_session(self) -> None:
        """Fetch a fresh session ID from the server."""
        with self.client.get(
            "/api/chat/session",
            name="/api/chat/session",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                self.session_id = resp.json().get("session_id", self.session_id)
                resp.success()
            else:
                resp.failure(f"Session creation failed: {resp.status_code}")

    @task(5)
    @tag("chat", "authenticated")
    def send_chat_message(self) -> None:
        """Send a random authenticated-user chat message."""
        message = random.choice(AUTHENTICATED_MESSAGES)
        self.client.post(
            "/api/chat",
            json={
                "message": message,
                "session_id": self.session_id,
                "token": self.token,
            },
            name="/api/chat [authenticated]",
            timeout=120,
        )

    @task(1)
    @tag("chat", "emergency")
    def send_emergency_message(self) -> None:
        """Occasionally send an emergency/symptom message."""
        message = random.choice(EMERGENCY_MESSAGES)
        self.client.post(
            "/api/chat",
            json={
                "message": message,
                "session_id": self.session_id,
                "token": self.token,
            },
            name="/api/chat [emergency]",
            timeout=120,
        )

    @task(1)
    @tag("session")
    def start_new_conversation(self) -> None:
        """Start a new conversation (mimics clicking 'New Conversation')."""
        self._new_session()

    @task(1)
    @tag("health")
    def health_check(self) -> None:
        """Hit the health endpoint (background polling)."""
        self.client.get("/api/health", name="/api/health")


class GuestUser(HttpUser):
    """Simulates a guest user asking general health questions.

    Weight 1 means 25% of spawned users will be guests.
    """

    weight = 1
    wait_time = between(5, 12)

    def on_start(self) -> None:
        """Create an initial chat session (no login)."""
        self.session_id: str = str(uuid.uuid4())
        self._new_session()

    def _new_session(self) -> None:
        """Fetch a fresh session ID from the server."""
        with self.client.get(
            "/api/chat/session",
            name="/api/chat/session",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                self.session_id = resp.json().get("session_id", self.session_id)
                resp.success()
            else:
                resp.failure(f"Session creation failed: {resp.status_code}")

    @task(5)
    @tag("chat", "guest")
    def send_chat_message(self) -> None:
        """Send a random general health question."""
        message = random.choice(GUEST_MESSAGES)
        self.client.post(
            "/api/chat",
            json={
                "message": message,
                "session_id": self.session_id,
            },
            name="/api/chat [guest]",
            timeout=120,
        )

    @task(1)
    @tag("session")
    def start_new_conversation(self) -> None:
        """Start a new conversation."""
        self._new_session()

    @task(1)
    @tag("health")
    def health_check(self) -> None:
        """Hit the health endpoint."""
        self.client.get("/api/health", name="/api/health")
