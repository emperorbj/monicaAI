"""Run the real seed against Neon (inside a rolled-back transaction) and check the result.

Slow (~2 minutes): it runs the whole seed twice over the network. Skip it with
`-m "not integration"` while working on something else.
"""

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Facility,
    FacilityContact,
    FacilityService,
    Lga,
    ServiceSchedule,
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

    # 2. Every seeded facility exists, in the pilot LGA.
    pilot_facilities = db_session.scalars(
        select(Facility).join(Lga).where(Lga.name == demo_data.PILOT_LGA_NAME)
    ).all()
    seeded_names = {f["name"] for f in demo_data.FACILITIES}
    assert seeded_names <= {facility.name for facility in pilot_facilities}

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
