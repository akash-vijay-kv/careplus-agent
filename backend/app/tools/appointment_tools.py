"""Appointment management toolkit for scheduling, listing, cancelling, and rescheduling."""

import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from agno.tools import Toolkit

from app.models.appointment import Appointment


class AppointmentTools(Toolkit):
    """Tools for managing patient appointments (Scenarios 2, 10, 11)."""

    def __init__(self, db_session: Session, user_id: int, **kwargs):
        tools = [
            self.schedule_phlebotomist_test,
            self.list_upcoming_appointments,
            self.cancel_appointment,
            self.reschedule_appointment,
        ]
        super().__init__(name="appointment_tools", tools=tools, **kwargs)
        self.db_session = db_session
        self.user_id = user_id

    def schedule_phlebotomist_test(self, date: str, time: str, location: str = "Home Visit") -> str:
        """Schedule a phlebotomist test for the patient.

        Args:
            date: The date for the test in YYYY-MM-DD format.
            time: The preferred time in HH:MM format (24-hour).
            location: The location for the test (default: Home Visit).

        Returns:
            Confirmation message with appointment details.
        """
        try:
            scheduled_at = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        except ValueError:
            return "Error: Invalid date or time format. Please use YYYY-MM-DD for date and HH:MM for time."

        if scheduled_at <= datetime.now():
            return "Error: Cannot schedule an appointment in the past. Please provide a future date and time."

        appointment = Appointment(
            user_id=self.user_id,
            appointment_type="Phlebotomist Test",
            status="scheduled",
            scheduled_at=scheduled_at,
            location=location,
            provider_name="Mobile Phlebotomy Service",
            notes="Blood draw for lab testing",
        )
        self.db_session.add(appointment)
        self.db_session.commit()

        return json.dumps({
            "status": "success",
            "appointment_id": appointment.id,
            "type": "Phlebotomist Test",
            "scheduled_at": scheduled_at.strftime("%B %d, %Y at %I:%M %p"),
            "location": location,
            "provider": "Mobile Phlebotomy Service",
        })

    def list_upcoming_appointments(self) -> str:
        """List all upcoming appointments for the patient.

        Returns:
            JSON string with list of upcoming appointments.
        """
        appointments = (
            self.db_session.query(Appointment)
            .filter(
                Appointment.user_id == self.user_id,
                Appointment.status == "scheduled",
                Appointment.scheduled_at > datetime.now(),
            )
            .order_by(Appointment.scheduled_at)
            .all()
        )

        if not appointments:
            return json.dumps({"appointments": [], "message": "No upcoming appointments found."})

        result = []
        for appt in appointments:
            result.append({
                "id": appt.id,
                "type": appt.appointment_type,
                "date": appt.scheduled_at.strftime("%B %d, %Y"),
                "time": appt.scheduled_at.strftime("%I:%M %p"),
                "location": appt.location,
                "provider": appt.provider_name,
                "notes": appt.notes,
            })

        return json.dumps({"appointments": result, "count": len(result)})

    def cancel_appointment(self, appointment_id: int, reason: str = "") -> str:
        """Cancel an existing appointment.

        Args:
            appointment_id: The ID of the appointment to cancel.
            reason: Optional reason for cancellation.

        Returns:
            Confirmation of cancellation or error message.
        """
        appointment = (
            self.db_session.query(Appointment)
            .filter(
                Appointment.id == appointment_id,
                Appointment.user_id == self.user_id,
            )
            .first()
        )

        if not appointment:
            return json.dumps({"status": "error", "message": "Appointment not found."})

        if appointment.status == "cancelled":
            return json.dumps({"status": "error", "message": "This appointment is already cancelled."})

        hours_until = (appointment.scheduled_at - datetime.now()).total_seconds() / 3600
        if hours_until < 24:
            return json.dumps({
                "status": "warning",
                "message": f"This appointment is within 24 hours (cancellation policy: {appointment.cancellation_policy}). A late cancellation fee may apply.",
                "appointment_type": appointment.appointment_type,
                "scheduled_at": appointment.scheduled_at.strftime("%B %d, %Y at %I:%M %p"),
            })

        appointment.status = "cancelled"
        appointment.notes = f"{appointment.notes or ''}\nCancelled: {reason}".strip()
        self.db_session.commit()

        return json.dumps({
            "status": "success",
            "message": "Appointment cancelled successfully.",
            "cancelled_appointment": {
                "type": appointment.appointment_type,
                "was_scheduled_for": appointment.scheduled_at.strftime("%B %d, %Y at %I:%M %p"),
            },
        })

    def reschedule_appointment(self, appointment_id: int, new_date: str, new_time: str) -> str:
        """Reschedule an existing appointment to a new date and time.

        Args:
            appointment_id: The ID of the appointment to reschedule.
            new_date: The new date in YYYY-MM-DD format.
            new_time: The new time in HH:MM format (24-hour).

        Returns:
            Confirmation of rescheduling or error message.
        """
        appointment = (
            self.db_session.query(Appointment)
            .filter(
                Appointment.id == appointment_id,
                Appointment.user_id == self.user_id,
                Appointment.status == "scheduled",
            )
            .first()
        )

        if not appointment:
            return json.dumps({"status": "error", "message": "Active appointment not found."})

        try:
            new_scheduled_at = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            return json.dumps({"status": "error", "message": "Invalid date or time format."})

        if new_scheduled_at <= datetime.now():
            return json.dumps({"status": "error", "message": "Cannot reschedule to a past date/time."})

        old_time = appointment.scheduled_at.strftime("%B %d, %Y at %I:%M %p")
        appointment.scheduled_at = new_scheduled_at
        self.db_session.commit()

        return json.dumps({
            "status": "success",
            "message": "Appointment rescheduled successfully.",
            "appointment": {
                "type": appointment.appointment_type,
                "previous_time": old_time,
                "new_time": new_scheduled_at.strftime("%B %d, %Y at %I:%M %p"),
                "location": appointment.location,
                "provider": appointment.provider_name,
            },
        })
