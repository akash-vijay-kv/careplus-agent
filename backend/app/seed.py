"""Database seeding script for development/demo purposes.

This script is an alternative to the init.sql file for seeding via Python.
The primary seeding method uses db/init.sql mounted into the PostgreSQL container.
"""

from datetime import date, datetime, timedelta

from app.database import SessionLocal
from app.models import (
    User,
    HealthProfile,
    Appointment,
    Medication,
    Prescription,
    BloodResult,
)


def seed_database() -> None:
    """Populate the database with demo data for testing."""
    db = SessionLocal()

    existing_user = db.query(User).filter(User.id == 1).first()
    if existing_user:
        print("Database already seeded. Skipping.")
        db.close()
        return

    user = User(
        id=1,
        first_name="Sarah",
        last_name="Johnson",
        email="sarah.johnson@email.com",
        phone="+1-555-0142",
        date_of_birth=date(1985, 3, 15),
        address_line1="742 Evergreen Terrace",
        city="Springfield",
        state="Illinois",
        zip_code="62701",
        emergency_contact_name="Michael Johnson",
        emergency_contact_phone="+1-555-0198",
    )
    db.add(user)
    db.flush()

    profile = HealthProfile(
        user_id=1,
        allergies=["Penicillin", "Shellfish"],
        chronic_conditions=["Hypertension", "Mild Asthma"],
        past_procedures=[
            {"name": "Appendectomy", "year": 2019, "hospital": "Springfield General"},
            {"name": "Wisdom teeth removal", "year": 2010, "hospital": "Dental Surgery Center"},
        ],
        family_history=[
            {"condition": "Type 2 Diabetes", "relation": "Father"},
            {"condition": "Breast Cancer", "relation": "Maternal Grandmother"},
            {"condition": "Hypertension", "relation": "Mother"},
        ],
        blood_type="A+",
        height_cm=165.0,
        weight_kg=62.5,
    )
    db.add(profile)

    now = datetime.now()
    appointments = [
        Appointment(
            user_id=1,
            appointment_type="General Checkup",
            status="scheduled",
            scheduled_at=now + timedelta(days=7),
            location="Springfield Medical Center, Room 204",
            provider_name="Dr. Emily Carter",
            notes="Annual physical examination",
        ),
        Appointment(
            user_id=1,
            appointment_type="Dental Cleaning",
            status="scheduled",
            scheduled_at=now + timedelta(days=14),
            location="Bright Smile Dental, Suite 101",
            provider_name="Dr. Robert Chen",
            notes="Routine cleaning and checkup",
        ),
        Appointment(
            user_id=1,
            appointment_type="Cardiology Follow-up",
            status="scheduled",
            scheduled_at=now + timedelta(days=21),
            location="Heart Health Clinic, Floor 3",
            provider_name="Dr. Amanda Torres",
            notes="Blood pressure monitoring follow-up",
        ),
    ]
    db.add_all(appointments)

    db.commit()
    db.close()
    print("Database seeded successfully.")


if __name__ == "__main__":
    seed_database()
