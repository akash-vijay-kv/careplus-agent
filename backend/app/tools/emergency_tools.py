"""Emergency assessment and escalation toolkit."""

import json

from agno.tools import Toolkit


EMERGENCY_SYMPTOMS = [
    "chest pain",
    "chest tightness",
    "difficulty breathing",
    "shortness of breath",
    "sudden severe headache",
    "face drooping",
    "arm weakness",
    "speech difficulty",
    "slurred speech",
    "severe allergic reaction",
    "anaphylaxis",
    "swelling of throat",
    "difficulty swallowing",
    "uncontrolled bleeding",
    "loss of consciousness",
    "fainting",
    "seizure",
    "severe abdominal pain",
    "suicidal thoughts",
    "self-harm",
]

NEARBY_HOSPITALS = [
    {
        "name": "Springfield General Hospital",
        "address": "1200 Main Street, Springfield, IL 62701",
        "phone": "+1-555-0100",
        "er_wait_time": "~15 minutes",
        "distance": "2.3 miles",
    },
    {
        "name": "St. Mary's Medical Center",
        "address": "800 Oak Avenue, Springfield, IL 62702",
        "phone": "+1-555-0200",
        "er_wait_time": "~25 minutes",
        "distance": "4.1 miles",
    },
    {
        "name": "Memorial Health Emergency",
        "address": "450 Cedar Lane, Springfield, IL 62703",
        "phone": "+1-555-0300",
        "er_wait_time": "~10 minutes",
        "distance": "5.8 miles",
    },
]


class EmergencyTools(Toolkit):
    """Tools for symptom assessment and emergency escalation (Scenarios 12, 13)."""

    def __init__(self, user_id: int, **kwargs):
        tools = [
            self.assess_symptom_severity,
            self.get_emergency_info,
            self.escalate_to_human,
        ]
        super().__init__(name="emergency_tools", tools=tools, **kwargs)
        self.user_id = user_id

    def assess_symptom_severity(self, symptoms: str, duration: str = "", severity_scale: int = 0) -> str:
        """Assess the severity of reported symptoms and determine urgency level.

        Args:
            symptoms: Description of the symptoms the patient is experiencing.
            duration: How long the symptoms have been present.
            severity_scale: Self-reported severity on a 1-10 scale (0 if not provided).

        Returns:
            Severity assessment with recommended action level.
        """
        symptoms_lower = symptoms.lower()

        is_emergency = any(es in symptoms_lower for es in EMERGENCY_SYMPTOMS)

        if is_emergency:
            severity_level = "critical"
            action = "IMMEDIATE EMERGENCY - Call 911 or go to nearest ER"
            urgency = "immediate"
        elif severity_scale >= 8:
            severity_level = "high"
            action = "Seek urgent medical care within the next few hours"
            urgency = "urgent"
        elif severity_scale >= 5 or "days" in duration.lower():
            severity_level = "moderate"
            action = "Schedule a consultation within 24-48 hours"
            urgency = "soon"
        else:
            severity_level = "low"
            action = "Monitor symptoms. Schedule routine appointment if symptoms persist"
            urgency = "routine"

        return json.dumps({
            "severity_level": severity_level,
            "is_emergency": is_emergency,
            "recommended_action": action,
            "urgency": urgency,
            "symptoms_reported": symptoms,
            "duration": duration,
            "severity_scale": severity_scale,
            "disclaimer": "This assessment is not a medical diagnosis. Please consult a healthcare professional for proper evaluation.",
        })

    def get_emergency_info(self) -> str:
        """Get emergency contact numbers and nearby hospital information.

        Returns:
            Emergency numbers and nearby hospital details.
        """
        return json.dumps({
            "emergency_numbers": {
                "emergency_services": "911",
                "poison_control": "1-800-222-1222",
                "suicide_prevention": "988",
                "nurse_hotline": "1-800-555-NURSE",
            },
            "nearby_hospitals": NEARBY_HOSPITALS,
            "important_note": "If you are experiencing a medical emergency, please call 911 immediately. Do not rely on this chat for emergency medical assistance.",
        })

    def escalate_to_human(self, reason: str, urgency: str = "high") -> str:
        """Escalate the conversation to a human medical professional.

        Args:
            reason: Reason for escalation.
            urgency: Urgency level ('critical', 'high', 'medium').

        Returns:
            Confirmation of escalation with expected response time.
        """
        response_times = {
            "critical": "immediately (within 5 minutes)",
            "high": "within 15 minutes",
            "medium": "within 1 hour",
        }

        expected_response = response_times.get(urgency, "within 30 minutes")

        return json.dumps({
            "status": "escalated",
            "message": f"Your case has been escalated to a medical professional. Expected response: {expected_response}.",
            "reason": reason,
            "urgency": urgency,
            "reference_number": f"ESC-{self.user_id}-{urgency.upper()}",
            "next_steps": [
                "A medical professional will contact you shortly",
                "Keep your phone nearby",
                "If symptoms worsen, call 911 immediately",
                "Do not drive yourself to the hospital if feeling dizzy or faint",
            ],
        })
