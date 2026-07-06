"""
ErrorBudgetService - Phase 33 Cyber Platform Observability, Reliability & Operations Fabric.
Tracks SLO error budget metrics, burn rate calculation, and forecasting exhaustion windows.
"""
from app.extensions import db
from app.models.error_budget_record import ErrorBudgetRecord
from app.models.reliability_objective import ReliabilityObjective
import datetime


class ErrorBudgetService:
    @staticmethod
    def calculate_budget(objective_id: int, org_id: int) -> ErrorBudgetRecord:
        """Retrieve or initialize ErrorBudgetRecord for a reliability objective."""
        obj = db.session.get(ReliabilityObjective, objective_id)
        if not obj or obj.organization_id != org_id:
            return None

        record = ErrorBudgetRecord.query.filter_by(
            reliability_objective_id=objective_id,
            organization_id=org_id
        ).first()

        if not record:
            now = datetime.datetime.utcnow()
            # Determine window duration from SLO
            days = 30
            if obj.measurement_window == '7d':
                days = 7
            elif obj.measurement_window == '90d':
                days = 90

            record = ErrorBudgetRecord(
                reliability_objective_id=objective_id,
                budget_total=1.0,
                budget_consumed=0.0,
                budget_remaining=1.0,
                burn_rate=1.0,
                window_start=now,
                window_end=now + datetime.timedelta(days=days),
                status='within_budget',
                organization_id=org_id
            )
            db.session.add(record)
            db.session.commit()

        return record

    @staticmethod
    def consume_budget(objective_id: int, amount: float, org_id: int) -> ErrorBudgetRecord:
        """Consume error budget. Rejects negative inputs and handles exact / over-consumption."""
        if amount < 0:
            raise ValueError("Consumption amount cannot be negative")

        record = ErrorBudgetService.calculate_budget(objective_id, org_id)
        if not record:
            return None

        record.budget_consumed = round(record.budget_consumed + amount, 4)
        record.budget_remaining = max(0.0, round(record.budget_total - record.budget_consumed, 4))

        # Recalculate status and burn rate
        record.status = ErrorBudgetService.classify_budget(record.budget_remaining)

        # Update burn rate based on consumption speed
        # Simple simulation: if we consume more budget than expected per time, burn rate is higher
        now = datetime.datetime.utcnow()
        total_seconds = (record.window_end - record.window_start).total_seconds()
        elapsed_seconds = max(1.0, (now - record.window_start).total_seconds())

        expected_consumption_fraction = elapsed_seconds / total_seconds
        actual_consumption_fraction = record.budget_consumed / record.budget_total

        if expected_consumption_fraction > 0:
            record.burn_rate = round(actual_consumption_fraction / expected_consumption_fraction, 2)
        else:
            record.burn_rate = 1.0

        db.session.commit()
        return record

    @staticmethod
    def calculate_burn_rate(objective_id: int, window_hours: float, org_id: int) -> float:
        """Calculate the burn rate of the error budget over a specific window of hours."""
        if window_hours <= 0:
            raise ValueError("Window hours must be greater than zero")

        record = ErrorBudgetService.calculate_budget(objective_id, org_id)
        if not record:
            return 0.0

        # Simulation: evaluate burn rate based on consumption fraction over the requested window
        # In a real system, we'd query metrics. Here we use the stored record's consumption speed.
        return record.burn_rate

    @staticmethod
    def forecast_exhaustion(objective_id: int, org_id: int) -> str:
        """Forecast the time remaining until error budget is exhausted."""
        record = ErrorBudgetService.calculate_budget(objective_id, org_id)
        if not record:
            return "unknown (no budget record)"

        if record.budget_remaining <= 0.0:
            return "exhausted"

        if record.burn_rate <= 0.01:
            return "no exhaustion forecast (stable)"

        # 30d window is 720 hours. Remaining fraction / hourly burn rate.
        # Burn rate of 1.0 means exhausting exactly at the end of the window.
        now = datetime.datetime.utcnow()
        remaining_seconds = (record.window_end - now).total_seconds()
        if remaining_seconds <= 0:
            return "exhausted (window passed)"

        # Hourly expected burn
        total_hours = (record.window_end - record.window_start).total_seconds() / 3600.0
        hourly_expected_burn = record.budget_total / total_hours

        # Actual hourly burn = hourly expected * burn_rate
        hourly_actual_burn = hourly_expected_burn * record.burn_rate

        if hourly_actual_burn <= 0:
            return "stable"

        hours_to_exhaustion = record.budget_remaining / hourly_actual_burn
        return f"{round(hours_to_exhaustion, 1)} hours remaining"

    @staticmethod
    def classify_budget(budget_remaining: float) -> str:
        """Classify budget status based on remaining percentage."""
        if budget_remaining <= 0.0:
            return 'exhausted'
        elif budget_remaining < 0.2:
            return 'warning'
        else:
            return 'within_budget'

    @staticmethod
    def budget_summary(org_id: int) -> dict:
        """Report summary statistics for error budgets."""
        records = ErrorBudgetRecord.query.filter_by(organization_id=org_id).all()
        if not records:
            return {
                'total_budgets': 0,
                'within_budget': 0,
                'warning': 0,
                'exhausted': 0,
                'avg_remaining': 1.0
            }

        wb = sum(1 for r in records if r.status == 'within_budget')
        warn = sum(1 for r in records if r.status == 'warning')
        exh = sum(1 for r in records if r.status == 'exhausted')
        avg_rem = sum(r.budget_remaining for r in records) / len(records)

        return {
            'total_budgets': len(records),
            'within_budget': wb,
            'warning': warn,
            'exhausted': exh,
            'avg_remaining': round(avg_rem, 3)
        }
