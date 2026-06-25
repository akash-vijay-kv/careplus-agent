"""Blood result management toolkit for storing results and analyzing trends."""

import json
from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from agno.tools import Toolkit

from app.models.blood_result import BloodResult


class BloodResultTools(Toolkit):
    """Tools for managing blood test results and trends (Scenarios 4, 8)."""

    def __init__(self, db_session: Session, user_id: int, **kwargs):
        tools = [
            self.store_blood_result,
            self.get_blood_history,
            self.analyze_trends,
        ]
        super().__init__(name="blood_result_tools", tools=tools, **kwargs)
        self.db_session = db_session
        self.user_id = user_id

    def store_blood_result(
        self,
        test_type: str,
        value: float,
        unit: str,
        tested_at: str,
        reference_range_low: float | None = None,
        reference_range_high: float | None = None,
        lab_name: str = "Self-reported",
        notes: str = "",
    ) -> str:
        """Store a new blood test result.

        Args:
            test_type: Type of blood test (e.g., 'Total Cholesterol', 'Fasting Blood Sugar').
            value: The numeric test result value.
            unit: Unit of measurement (e.g., 'mg/dL', 'g/dL').
            tested_at: Date and time of the test in YYYY-MM-DD format.
            reference_range_low: Lower bound of normal range (optional).
            reference_range_high: Upper bound of normal range (optional).
            lab_name: Name of the laboratory.
            notes: Additional notes about the result.

        Returns:
            Confirmation with stored result and interpretation.
        """
        try:
            test_datetime = datetime.strptime(tested_at, "%Y-%m-%d")
        except ValueError:
            return json.dumps({"status": "error", "message": "Invalid date format. Use YYYY-MM-DD."})

        result = BloodResult(
            user_id=self.user_id,
            test_type=test_type,
            value=value,
            unit=unit,
            reference_range_low=reference_range_low,
            reference_range_high=reference_range_high,
            tested_at=test_datetime,
            lab_name=lab_name,
            notes=notes,
        )
        self.db_session.add(result)
        self.db_session.commit()

        in_range = True
        interpretation = "Within normal range"
        if reference_range_low is not None and value < reference_range_low:
            in_range = False
            interpretation = "Below normal range"
        elif reference_range_high is not None and value > reference_range_high:
            in_range = False
            interpretation = "Above normal range"

        return json.dumps({
            "status": "success",
            "result": {
                "id": result.id,
                "test_type": test_type,
                "value": value,
                "unit": unit,
                "tested_at": tested_at,
                "in_normal_range": in_range,
                "interpretation": interpretation,
                "reference_range": f"{reference_range_low}-{reference_range_high} {unit}" if reference_range_low and reference_range_high else "Not specified",
            },
        })

    def get_blood_history(self, test_type: str, limit: int = 10) -> str:
        """Get historical blood test results for a specific test type.

        Args:
            test_type: Type of blood test to retrieve history for.
            limit: Maximum number of results to return (default 10).

        Returns:
            JSON string with historical results ordered by date.
        """
        results = (
            self.db_session.query(BloodResult)
            .filter(
                BloodResult.user_id == self.user_id,
                BloodResult.test_type == test_type,
            )
            .order_by(desc(BloodResult.tested_at))
            .limit(limit)
            .all()
        )

        if not results:
            return json.dumps({
                "test_type": test_type,
                "results": [],
                "message": f"No results found for {test_type}.",
            })

        history = []
        for r in reversed(results):
            in_range = True
            if r.reference_range_low is not None and float(r.value) < float(r.reference_range_low):
                in_range = False
            elif r.reference_range_high is not None and float(r.value) > float(r.reference_range_high):
                in_range = False

            history.append({
                "date": r.tested_at.strftime("%Y-%m-%d"),
                "value": float(r.value),
                "unit": r.unit,
                "in_normal_range": in_range,
                "reference_range": f"{float(r.reference_range_low)}-{float(r.reference_range_high)}" if r.reference_range_low and r.reference_range_high else None,
                "lab": r.lab_name,
            })

        return json.dumps({
            "test_type": test_type,
            "results": history,
            "count": len(history),
            "latest_value": history[-1]["value"] if history else None,
            "unit": history[0]["unit"] if history else None,
        })

    def analyze_trends(self, test_type: str) -> str:
        """Analyze trends in blood test results over time.

        Args:
            test_type: Type of blood test to analyze trends for.

        Returns:
            Trend analysis including direction, percentage change, and assessment.
        """
        results = (
            self.db_session.query(BloodResult)
            .filter(
                BloodResult.user_id == self.user_id,
                BloodResult.test_type == test_type,
            )
            .order_by(BloodResult.tested_at)
            .all()
        )

        if len(results) < 2:
            return json.dumps({
                "test_type": test_type,
                "trend": "insufficient_data",
                "message": "Need at least 2 data points to analyze trends.",
            })

        values = [float(r.value) for r in results]
        dates = [r.tested_at.strftime("%Y-%m-%d") for r in results]
        first_value = values[0]
        last_value = values[-1]
        percentage_change = ((last_value - first_value) / first_value) * 100

        ref_low = float(results[0].reference_range_low) if results[0].reference_range_low else None
        ref_high = float(results[0].reference_range_high) if results[0].reference_range_high else None

        if abs(percentage_change) < 5:
            trend_direction = "stable"
        elif percentage_change > 0:
            trend_direction = "increasing"
        else:
            trend_direction = "decreasing"

        latest_in_range = True
        if ref_low is not None and last_value < ref_low:
            latest_in_range = False
        elif ref_high is not None and last_value > ref_high:
            latest_in_range = False

        if latest_in_range and trend_direction == "stable":
            assessment = "Your levels are stable and within normal range. Keep up the good work!"
        elif latest_in_range and trend_direction == "decreasing" and ref_high and first_value > ref_high:
            assessment = "Great progress! Your levels are trending down toward the normal range."
        elif latest_in_range:
            assessment = "Your levels are within normal range."
        elif not latest_in_range and trend_direction == "increasing" and ref_high and last_value > ref_high:
            assessment = "Your levels are above normal and trending upward. Consider discussing with your doctor."
        elif not latest_in_range and trend_direction == "decreasing":
            assessment = "Your levels are improving but still outside normal range. Continue current management."
        else:
            assessment = "Your levels are outside normal range. Please consult your healthcare provider."

        return json.dumps({
            "test_type": test_type,
            "trend_direction": trend_direction,
            "percentage_change": round(percentage_change, 1),
            "first_reading": {"date": dates[0], "value": first_value},
            "latest_reading": {"date": dates[-1], "value": last_value},
            "total_readings": len(values),
            "reference_range": f"{ref_low}-{ref_high}" if ref_low and ref_high else None,
            "latest_in_normal_range": latest_in_range,
            "assessment": assessment,
            "timeline": [{"date": d, "value": v} for d, v in zip(dates, values)],
        })
