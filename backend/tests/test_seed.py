"""Run the real seed against Neon (inside a rolled-back transaction) and check the result."""

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Facility,
    FacilityContact,
    FacilityService,
    Lga,
    ServiceSchedule,
    State,
)
from app.models.enums import VerificationStatus
from seed import demo_data
from seed.seed_demo import run_seed

pytestmark = pytest.mark.integration

DEMO_TABLES = [Facility, FacilityService, FacilityContact, ServiceSchedule]


def _row_counts(session: Session) -> dict[str, int]:
    return {
        model.__tablename__: session.scalar(select(func.count()).select_from(model))
        for model in DEMO_TABLES
    }


def test_seed_is_idempotent_and_marks_everything_as_demo(db_session: Session) -> None:
    run_seed(db_session)
    counts_after_first_run = _row_counts(db_session)

    second_report = run_seed(db_session)

    # 1. Idempotent: the second run creates nothing and leaves row counts unchanged.
    assert sum(second_report.created.values()) == 0
    assert _row_counts(db_session) == counts_after_first_run

    # 2. Every facility exists in the right state AND LGA (Surulere exists in two states).
    stored = set(
        db_session.execute(
            select(State.code, Lga.name, Facility.name).join(Lga.state).join(Lga.facilities)
        ).all()
    )
    for state in demo_data.STATES:
        for lga in state["lgas"]:
            for facility in lga["facilities"]:
                assert (state["code"], lga["name"], facility["name"]) in stored

    # 3. Demo rows are flagged and never verified.
    for model in DEMO_TABLES:
        not_demo = db_session.scalar(
            select(func.count()).select_from(model).where(model.is_demo.is_(False))
        )
        verified = db_session.scalar(
            select(func.count())
            .select_from(model)
            .where(model.verification_status == VerificationStatus.VERIFIED)
        )
        assert not_demo == 0, f"{model.__tablename__} has non-demo rows"
        assert verified == 0, f"{model.__tablename__} has verified rows"
