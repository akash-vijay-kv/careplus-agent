"""Health profile toolkit for retrieving patient health summaries."""

import json

from sqlalchemy.orm import Session

from agno.tools import Toolkit

from app.models.health_profile import HealthProfile
from app.models.user import User


class HealthProfileTools(Toolkit):
    """Tools for retrieving patient health profile information (Scenario 9)."""

    def __init__(self, db_session: Session, user_id: int, **kwargs):
        tools = [
            self.get_health_summary,
            self.get_allergies,
            self.get_chronic_conditions,
            self.get_family_history,
            self.get_past_procedures,
        ]
        super().__init__(name="health_profile_tools", tools=tools, **kwargs)
        self.db_session = db_session
        self.user_id = user_id

    def get_health_summary(self) -> str:
        """Get a comprehensive summary of the patient's health profile.

        Returns:
            Complete health profile including demographics, allergies, conditions, and history.
        """
        user = self.db_session.query(User).filter(User.id == self.user_id).first()
        profile = self.db_session.query(HealthProfile).filter(HealthProfile.user_id == self.user_id).first()

        if not user or not profile:
            return json.dumps({"status": "error", "message": "Health profile not found."})

        return json.dumps({
            "patient": {
                "name": f"{user.first_name} {user.last_name}",
                "date_of_birth": user.date_of_birth.isoformat(),
                "phone": user.phone,
                "email": user.email,
                "emergency_contact": {
                    "name": user.emergency_contact_name,
                    "phone": user.emergency_contact_phone,
                },
            },
            "health_data": {
                "blood_type": profile.blood_type,
                "height_cm": float(profile.height_cm) if profile.height_cm else None,
                "weight_kg": float(profile.weight_kg) if profile.weight_kg else None,
                "allergies": profile.allergies,
                "chronic_conditions": profile.chronic_conditions,
                "past_procedures": profile.past_procedures,
                "family_history": profile.family_history,
            },
        })

    def get_allergies(self) -> str:
        """Get the patient's known allergies.

        Returns:
            List of allergies.
        """
        profile = self.db_session.query(HealthProfile).filter(HealthProfile.user_id == self.user_id).first()

        if not profile:
            return json.dumps({"status": "error", "message": "Health profile not found."})

        return json.dumps({
            "allergies": profile.allergies,
            "count": len(profile.allergies),
        })

    def get_chronic_conditions(self) -> str:
        """Get the patient's chronic conditions.

        Returns:
            List of chronic conditions.
        """
        profile = self.db_session.query(HealthProfile).filter(HealthProfile.user_id == self.user_id).first()

        if not profile:
            return json.dumps({"status": "error", "message": "Health profile not found."})

        return json.dumps({
            "chronic_conditions": profile.chronic_conditions,
            "count": len(profile.chronic_conditions),
        })

    def get_family_history(self) -> str:
        """Get the patient's family medical history.

        Returns:
            Family history with conditions and relations.
        """
        profile = self.db_session.query(HealthProfile).filter(HealthProfile.user_id == self.user_id).first()

        if not profile:
            return json.dumps({"status": "error", "message": "Health profile not found."})

        return json.dumps({
            "family_history": profile.family_history,
            "count": len(profile.family_history),
        })

    def get_past_procedures(self) -> str:
        """Get the patient's past medical procedures.

        Returns:
            List of past procedures with dates and locations.
        """
        profile = self.db_session.query(HealthProfile).filter(HealthProfile.user_id == self.user_id).first()

        if not profile:
            return json.dumps({"status": "error", "message": "Health profile not found."})

        return json.dumps({
            "past_procedures": profile.past_procedures,
            "count": len(profile.past_procedures),
        })
