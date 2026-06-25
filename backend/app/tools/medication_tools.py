"""Medication management toolkit for listing, tracking, and refill requests."""

import json
from datetime import date, datetime

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from agno.tools import Toolkit

from app.models.medication import Medication
from app.models.prescription import Prescription


class MedicationTools(Toolkit):
    """Tools for managing patient medications and prescriptions (Scenarios 6, 7)."""

    def __init__(self, db_session: Session, user_id: int, **kwargs):
        tools = [
            self.list_medications,
            self.mark_medication_taken,
            self.set_medication_reminder,
            self.check_refill_eligibility,
            self.request_refill,
        ]
        super().__init__(name="medication_tools", tools=tools, **kwargs)
        self.db_session = db_session
        self.user_id = user_id

    def list_medications(self, active_only: bool = True) -> str:
        """List the patient's current medications with dosage and schedule.

        Args:
            active_only: If True, only show active medications.

        Returns:
            JSON string with medication list.
        """
        query = self.db_session.query(Medication).filter(Medication.user_id == self.user_id)
        if active_only:
            query = query.filter(Medication.is_active == True)

        medications = query.all()

        if not medications:
            return json.dumps({"medications": [], "message": "No medications found."})

        result = []
        for med in medications:
            recent_adherence = med.adherence_log[-7:] if med.adherence_log else []
            taken_count = sum(1 for entry in recent_adherence if entry.get("taken", False))

            result.append({
                "id": med.id,
                "name": med.name,
                "dosage": med.dosage,
                "frequency": med.frequency,
                "instructions": med.instructions,
                "start_date": med.start_date.isoformat() if med.start_date else None,
                "end_date": med.end_date.isoformat() if med.end_date else None,
                "is_active": med.is_active,
                "recent_adherence": f"{taken_count}/{len(recent_adherence)} doses taken in last week",
            })

        return json.dumps({"medications": result, "count": len(result)})

    def mark_medication_taken(self, medication_id: int) -> str:
        """Mark a medication as taken for today.

        Args:
            medication_id: The ID of the medication to mark as taken.

        Returns:
            Confirmation message.
        """
        medication = (
            self.db_session.query(Medication)
            .filter(
                Medication.id == medication_id,
                Medication.user_id == self.user_id,
                Medication.is_active == True,
            )
            .first()
        )

        if not medication:
            return json.dumps({"status": "error", "message": "Active medication not found."})

        today = date.today().isoformat()
        adherence_log = medication.adherence_log or []

        already_logged = any(entry.get("date") == today for entry in adherence_log)
        if already_logged:
            return json.dumps({
                "status": "info",
                "message": f"{medication.name} has already been marked as taken today.",
            })

        adherence_log.append({"date": today, "taken": True, "time": datetime.now().strftime("%H:%M")})
        medication.adherence_log = adherence_log
        flag_modified(medication, "adherence_log")
        self.db_session.commit()

        return json.dumps({
            "status": "success",
            "message": f"{medication.name} ({medication.dosage}) marked as taken for today.",
        })

    def set_medication_reminder(self, medication_id: int, reminder_time: str) -> str:
        """Set a reminder for a medication.

        Args:
            medication_id: The ID of the medication.
            reminder_time: Time for the reminder in HH:MM format.

        Returns:
            Confirmation that the reminder has been set.
        """
        medication = (
            self.db_session.query(Medication)
            .filter(
                Medication.id == medication_id,
                Medication.user_id == self.user_id,
                Medication.is_active == True,
            )
            .first()
        )

        if not medication:
            return json.dumps({"status": "error", "message": "Active medication not found."})

        return json.dumps({
            "status": "success",
            "message": f"Reminder set for {medication.name} ({medication.dosage}) at {reminder_time} daily.",
            "medication": medication.name,
            "reminder_time": reminder_time,
        })

    def check_refill_eligibility(self, medication_id: int) -> str:
        """Check if a prescription is eligible for refill.

        Args:
            medication_id: The ID of the medication to check.

        Returns:
            Eligibility status with details.
        """
        prescription = (
            self.db_session.query(Prescription)
            .filter(
                Prescription.medication_id == medication_id,
                Prescription.user_id == self.user_id,
            )
            .first()
        )

        if not prescription:
            return json.dumps({"status": "error", "message": "No prescription found for this medication."})

        medication = self.db_session.query(Medication).get(medication_id)
        today = date.today()
        is_expired = prescription.expiry_date < today
        has_refills = prescription.refills_remaining > 0

        eligible = has_refills and not is_expired

        return json.dumps({
            "medication": medication.name if medication else "Unknown",
            "eligible": eligible,
            "refills_remaining": prescription.refills_remaining,
            "expiry_date": prescription.expiry_date.isoformat(),
            "is_expired": is_expired,
            "pharmacy": prescription.pharmacy,
            "prescribing_doctor": prescription.prescribing_doctor,
            "last_refill_date": prescription.last_refill_date.isoformat() if prescription.last_refill_date else None,
            "reason_if_ineligible": (
                "Prescription has expired" if is_expired
                else "No refills remaining" if not has_refills
                else None
            ),
        })

    def request_refill(self, medication_id: int) -> str:
        """Submit a refill request for a prescription.

        Args:
            medication_id: The ID of the medication to refill.

        Returns:
            Result of the refill request.
        """
        prescription = (
            self.db_session.query(Prescription)
            .filter(
                Prescription.medication_id == medication_id,
                Prescription.user_id == self.user_id,
            )
            .first()
        )

        if not prescription:
            return json.dumps({"status": "error", "message": "No prescription found for this medication."})

        medication = self.db_session.query(Medication).get(medication_id)
        today = date.today()

        if prescription.expiry_date < today:
            return json.dumps({
                "status": "denied",
                "message": f"Refill denied: Prescription for {medication.name} expired on {prescription.expiry_date.isoformat()}. Please contact {prescription.prescribing_doctor} for a new prescription.",
            })

        if prescription.refills_remaining <= 0:
            return json.dumps({
                "status": "denied",
                "message": f"Refill denied: No refills remaining for {medication.name}. Please contact {prescription.prescribing_doctor} for a renewal.",
            })

        prescription.refills_remaining -= 1
        prescription.last_refill_date = today
        self.db_session.commit()

        return json.dumps({
            "status": "approved",
            "message": f"Refill approved for {medication.name} ({medication.dosage}).",
            "pharmacy": prescription.pharmacy,
            "refills_remaining_after": prescription.refills_remaining,
            "estimated_ready": "Within 2-4 hours at your pharmacy",
        })
