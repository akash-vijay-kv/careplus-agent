"""Consultation management toolkit for physician consultations."""

import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from agno.tools import Toolkit

from app.models.consultation_request import ConsultationRequest


AVAILABLE_PHYSICIANS = [
    {"name": "Dr. Emily Carter", "specialty": "General Practice", "available": True},
    {"name": "Dr. Amanda Torres", "specialty": "Cardiology", "available": True},
    {"name": "Dr. Robert Chen", "specialty": "Internal Medicine", "available": True},
    {"name": "Dr. Lisa Park", "specialty": "Endocrinology", "available": False},
]


class ConsultationTools(Toolkit):
    """Tools for managing physician consultations (Scenario 5)."""

    def __init__(self, db_session: Session, user_id: int, **kwargs):
        tools = [
            self.request_physician_consultation,
            self.list_available_physicians,
            self.check_consultation_status,
        ]
        super().__init__(name="consultation_tools", tools=tools, **kwargs)
        self.db_session = db_session
        self.user_id = user_id

    def request_physician_consultation(
        self,
        consultation_type: str,
        reason: str,
        preferred_physician: str = "",
    ) -> str:
        """Request a manual consultation with a physician for document/data review.

        Args:
            consultation_type: Type of consultation (e.g., 'Document Review', 'Lab Results Review', 'General Consultation').
            reason: Reason for requesting the consultation.
            preferred_physician: Optional preferred physician name.

        Returns:
            Confirmation with consultation request details.
        """
        assigned = preferred_physician or "Dr. Emily Carter"

        physician_available = any(
            p["name"] == assigned and p["available"]
            for p in AVAILABLE_PHYSICIANS
        )
        if not physician_available and preferred_physician:
            available = [p["name"] for p in AVAILABLE_PHYSICIANS if p["available"]]
            assigned = available[0] if available else "Dr. Emily Carter"

        estimated_date = datetime.now() + timedelta(days=2)

        consultation = ConsultationRequest(
            user_id=self.user_id,
            consultation_type=consultation_type,
            status="pending",
            reason=reason,
            assigned_physician=assigned,
            scheduled_at=estimated_date,
        )
        self.db_session.add(consultation)
        self.db_session.commit()

        return json.dumps({
            "status": "success",
            "consultation": {
                "id": consultation.id,
                "type": consultation_type,
                "reason": reason,
                "assigned_physician": assigned,
                "status": "pending",
                "estimated_date": estimated_date.strftime("%B %d, %Y"),
                "message": f"Consultation request submitted. {assigned} will review your documents and data. You will be contacted within 48 hours.",
            },
        })

    def list_available_physicians(self) -> str:
        """List available physicians for consultation.

        Returns:
            List of physicians with availability status.
        """
        return json.dumps({
            "physicians": AVAILABLE_PHYSICIANS,
            "available_count": sum(1 for p in AVAILABLE_PHYSICIANS if p["available"]),
        })

    def check_consultation_status(self, consultation_id: int | None = None) -> str:
        """Check the status of consultation requests.

        Args:
            consultation_id: Optional specific consultation ID to check. If not provided, returns all recent requests.

        Returns:
            Status of the consultation request(s).
        """
        if consultation_id:
            consultation = (
                self.db_session.query(ConsultationRequest)
                .filter(
                    ConsultationRequest.id == consultation_id,
                    ConsultationRequest.user_id == self.user_id,
                )
                .first()
            )
            if not consultation:
                return json.dumps({"status": "error", "message": "Consultation request not found."})

            return json.dumps({
                "id": consultation.id,
                "type": consultation.consultation_type,
                "status": consultation.status,
                "physician": consultation.assigned_physician,
                "reason": consultation.reason,
                "scheduled_at": consultation.scheduled_at.strftime("%B %d, %Y") if consultation.scheduled_at else None,
            })

        consultations = (
            self.db_session.query(ConsultationRequest)
            .filter(ConsultationRequest.user_id == self.user_id)
            .order_by(ConsultationRequest.created_at.desc())
            .limit(5)
            .all()
        )

        result = []
        for c in consultations:
            result.append({
                "id": c.id,
                "type": c.consultation_type,
                "status": c.status,
                "physician": c.assigned_physician,
                "created_at": c.created_at.strftime("%B %d, %Y"),
            })

        return json.dumps({"consultations": result, "count": len(result)})
