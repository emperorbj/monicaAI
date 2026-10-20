"""Prove the database itself rejects bad data (real Neon tables, rolled back after each test).

Each test that expects a rejection checks the constraint NAME in the error, so it fails if
the row was rejected for some other, unexpected reason.
"""

from datetime import time
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Facility, FacilityContact, Lga, ServiceSchedule, State
from app.models.enums import FacilityType, VerificationStatus

pytestmark = pytest.mark.integration  # every test in this file talks to the database


def _make_facility(session: Session, **overrides) -> Facility:
    """Insert a minimal demo facility (with its state and LGA) and return it."""
    state = State(name="Test State", code="TS")
    lga = Lga(name="Test LGA", state=state)
    facility = Facility(
        lga=lga,
        name="Test Demo PHC",
        facility_type=FacilityType.PRIMARY_HEALTH_CENTRE,
        is_demo=True,
        **overrides,
    )
    session.add(facility)
    session.flush()  # send INSERTs now (inside our rolled-back transaction)
    return facility


def _add_contact(session: Session, facility: Facility, **fields) -> None:
    session.add(FacilityContact(facility=facility, role_title="Officer-in-Charge", **fields))
    session.flush()


def _assert_rejected_by(error: pytest.ExceptionInfo, constraint_name: str) -> None:
    assert constraint_name in str(error.value)


def test_a_valid_demo_facility_is_accepted(db_session: Session) -> None:
    facility = _make_facility(
        db_session,
        latitude=Decimal("7.412300"),
        longitude=Decimal("3.905600"),
        verification_status=VerificationStatus.REPORTED,
    )
    assert facility.id is not None  # the database assigned an id


def test_demo_facility_cannot_be_verified(db_session: Session) -> None:
    with pytest.raises(IntegrityError) as error:
        _make_facility(db_session, verification_status=VerificationStatus.VERIFIED)
    _assert_rejected_by(error, "ck_facilities_demo_never_verified")


def test_half_a_coordinate_is_rejected(db_session: Session) -> None:
    with pytest.raises(IntegrityError) as error:
        _make_facility(db_session, latitude=Decimal("7.412300"))
    _assert_rejected_by(error, "ck_facilities_coordinates_both_or_neither")


def test_status_defaults_to_unknown_even_for_raw_sql(db_session: Session) -> None:
    facility = _make_facility(db_session)
    db_session.execute(
        text(
            "INSERT INTO facilities (lga_id, name, facility_type) "
            "VALUES (:lga_id, 'Raw SQL Clinic', 'health_post')"
        ),
        {"lga_id": facility.lga_id},
    )
    status = db_session.execute(
        text("SELECT verification_status FROM facilities WHERE name = 'Raw SQL Clinic'")
    ).scalar_one()
    assert status == "unknown"


def test_unknown_enum_value_is_rejected_by_the_database(db_session: Session) -> None:
    facility = _make_facility(db_session)
    with pytest.raises(IntegrityError) as error:
        db_session.execute(
            text("UPDATE facilities SET verification_status = 'confirmed' WHERE id = :id"),
            {"id": facility.id},
        )
    _assert_rejected_by(error, "ck_facilities_verification_status_allowed")


def test_second_active_primary_contact_is_rejected(db_session: Session) -> None:
    facility = _make_facility(db_session)
    first = {"full_name": "Jane Doe (Demo)", "phone": "+2340000000000", "is_primary": True}
    second = {"full_name": "John Roe (Demo)", "phone": "+2340000000001", "is_primary": True}

    _add_contact(db_session, facility, **first)
    with pytest.raises(IntegrityError) as error:
        _add_contact(db_session, facility, **second)
    _assert_rejected_by(error, "uq_facility_contacts_one_primary_general")


def test_new_primary_is_allowed_once_the_old_one_is_inactive(db_session: Session) -> None:
    facility = _make_facility(db_session)
    old = {"full_name": "Old Lead (Demo)", "phone": "+2340000000000", "is_primary": True}
    new = {"full_name": "New Lead (Demo)", "phone": "+2340000000001", "is_primary": True}

    _add_contact(db_session, facility, **old, is_active=False)
    # No error expected: the partial unique index ignores inactive contacts.
    _add_contact(db_session, facility, **new)


def test_local_phone_format_is_rejected(db_session: Session) -> None:
    facility = _make_facility(db_session)
    with pytest.raises(IntegrityError) as error:
        _add_contact(db_session, facility, full_name="Jane Doe (Demo)", phone="08012345678")
    _assert_rejected_by(error, "ck_facility_contacts_phone_e164")


def test_contact_without_phone_or_email_is_rejected(db_session: Session) -> None:
    facility = _make_facility(db_session)
    with pytest.raises(IntegrityError) as error:
        _add_contact(db_session, facility, full_name="Jane Doe (Demo)")
    _assert_rejected_by(error, "ck_facility_contacts_reachable")


def test_duplicate_general_hours_are_rejected_despite_null_service(db_session: Session) -> None:
    facility = _make_facility(db_session)
    monday = {"facility": facility, "day_of_week": 1, "opens_at": time(8), "closes_at": time(16)}
    db_session.add(ServiceSchedule(**monday))
    db_session.flush()
    with pytest.raises(IntegrityError) as error:
        db_session.add(ServiceSchedule(**monday))
        db_session.flush()
    _assert_rejected_by(error, "uq_service_schedules_facility_id_service_id_day_of_week")


def test_closing_before_opening_is_rejected(db_session: Session) -> None:
    facility = _make_facility(db_session)
    with pytest.raises(IntegrityError) as error:
        db_session.add(
            ServiceSchedule(facility=facility, day_of_week=2, opens_at=time(16), closes_at=time(8))
        )
        db_session.flush()
    _assert_rejected_by(error, "ck_service_schedules_hours_consistent")


def test_state_with_lgas_cannot_be_deleted(db_session: Session) -> None:
    facility = _make_facility(db_session)
    with pytest.raises(IntegrityError) as error:
        db_session.execute(text("DELETE FROM states WHERE id = :id"), {"id": facility.lga.state_id})
    _assert_rejected_by(error, "fk_lgas_state_id_states")
