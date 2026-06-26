"""Order management toolkit for viewing medicine order status and history."""

import json
import re
from decimal import Decimal
from datetime import datetime

from sqlalchemy.orm import Session

from agno.tools import Toolkit

from app.models.order import Order

ORDER_ID_PATTERN = re.compile(r"^ORD-\d+$")
INVALID_ORDER_ID_MESSAGE = (
    "The order ID '{order_id}' is invalid. "
    "Please provide an order ID in the format: ORD-101"
)


class OrderTools(Toolkit):
    """Tools for viewing medicine order status, scoped to the authenticated user."""

    def __init__(self, db_session: Session, user_id: int, **kwargs):
        """Initialize order tools.

        Parameters
        ----------
        db_session : Session
            SQLAlchemy database session.
        user_id : int
            The authenticated user's ID for scoping queries.
        """
        tools = [self.list_orders, self.get_order_details]
        super().__init__(name="order_tools", tools=tools, **kwargs)
        self.db_session = db_session
        self.user_id = user_id

    def _serialize_order(self, order: Order) -> dict:
        """Convert an Order ORM instance to a serializable dictionary.

        Parameters
        ----------
        order : Order
            The order ORM object.

        Returns
        -------
        dict
            Dictionary representation of the order.
        """
        return {
            "order_id": order.order_number,
            "medication_name": order.medication_name,
            "quantity": order.quantity,
            "unit_price": float(order.unit_price) if isinstance(order.unit_price, Decimal) else order.unit_price,
            "total_price": float(order.total_price) if isinstance(order.total_price, Decimal) else order.total_price,
            "status": order.status,
            "shipping_address": order.shipping_address,
            "ordered_at": order.ordered_at.strftime("%B %d, %Y at %I:%M %p") if order.ordered_at else None,
            "delivered_at": order.delivered_at.strftime("%B %d, %Y at %I:%M %p") if order.delivered_at else None,
        }

    def list_orders(self, status: str = "") -> str:
        """List medicine orders for the current user.

        Args:
            status: Optional filter by order status (placed, processing, shipped, delivered). Leave empty for all orders.

        Returns:
            JSON string with list of orders.
        """
        query = self.db_session.query(Order).filter(Order.user_id == self.user_id)

        if status:
            query = query.filter(Order.status == status)

        orders = query.order_by(Order.ordered_at.desc()).all()

        if not orders:
            return json.dumps({"orders": [], "message": "No orders found."})

        result = [self._serialize_order(o) for o in orders]
        return json.dumps({"orders": result, "count": len(result)})

    def get_order_details(self, order_id: str) -> str:
        """Get details of a specific order by its order ID (e.g. ORD-101).

        Args:
            order_id: The order ID in ORD-XXX format (e.g. ORD-101, ORD-102).

        Returns:
            JSON string with order details or error message.
        """
        order_id = order_id.strip().upper()

        if not ORDER_ID_PATTERN.match(order_id):
            return json.dumps({
                "status": "error",
                "message": INVALID_ORDER_ID_MESSAGE.format(order_id=order_id),
            })

        order = (
            self.db_session.query(Order)
            .filter(Order.order_number == order_id, Order.user_id == self.user_id)
            .first()
        )

        if not order:
            return json.dumps({
                "status": "error",
                "message": f"No order found with ID '{order_id}'.",
            })

        return json.dumps({"status": "success", "order": self._serialize_order(order)})
