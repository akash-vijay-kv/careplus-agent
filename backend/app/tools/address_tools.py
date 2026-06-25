"""Address management toolkit for viewing and updating patient address."""

import json

from sqlalchemy.orm import Session

from agno.tools import Toolkit

from app.models.user import User


class AddressTools(Toolkit):
    """Tools for managing patient address (Scenario 3)."""

    def __init__(self, db_session: Session, user_id: int, **kwargs):
        tools = [
            self.get_current_address,
            self.update_address,
        ]
        super().__init__(name="address_tools", tools=tools, **kwargs)
        self.db_session = db_session
        self.user_id = user_id

    def get_current_address(self) -> str:
        """Get the patient's current address on file.

        Returns:
            Current address details.
        """
        user = self.db_session.query(User).filter(User.id == self.user_id).first()

        if not user:
            return json.dumps({"status": "error", "message": "User not found."})

        return json.dumps({
            "address_line1": user.address_line1,
            "address_line2": user.address_line2,
            "city": user.city,
            "state": user.state,
            "zip_code": user.zip_code,
        })

    def update_address(
        self,
        address_line1: str,
        city: str,
        state: str,
        zip_code: str,
        address_line2: str = "",
    ) -> str:
        """Update the patient's address.

        Args:
            address_line1: Street address line 1.
            city: City name.
            state: State name.
            zip_code: ZIP/postal code.
            address_line2: Street address line 2 (optional).

        Returns:
            Confirmation of the address update.
        """
        user = self.db_session.query(User).filter(User.id == self.user_id).first()

        if not user:
            return json.dumps({"status": "error", "message": "User not found."})

        old_address = {
            "address_line1": user.address_line1,
            "city": user.city,
            "state": user.state,
            "zip_code": user.zip_code,
        }

        user.address_line1 = address_line1
        user.address_line2 = address_line2
        user.city = city
        user.state = state
        user.zip_code = zip_code
        self.db_session.commit()

        return json.dumps({
            "status": "success",
            "message": "Address updated successfully.",
            "old_address": old_address,
            "new_address": {
                "address_line1": address_line1,
                "address_line2": address_line2,
                "city": city,
                "state": state,
                "zip_code": zip_code,
            },
        })
