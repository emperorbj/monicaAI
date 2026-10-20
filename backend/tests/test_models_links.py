"""Tests for facility_services, facility_contacts, service_schedules, and verification_history.

Definition-level checks (no database). In Step 5 we prove the same rules against real Neon tables.
"""

import re

import pytest
from sqlalchemy import CheckConstraint, Enum, UniqueConstraint, Uuid
from sqlalchemy.orm import configure_mappers

from app.models import (
    Base,
    Facility,
    FacilityContact,
    FacilityService,
    ServiceSchedule,
    VerificationHistory,
)

# The same pattern the database CHECK uses, so we can test it in Python.
E164_PATTERN = re.compile(r"^\+[1-9][0-9]{6,14}$")


def _check_names(model) -> set[str]:
    return {c.name for c in model.__table__.constraints if isinstance(c, CheckConstraint)}


def _unique_column_sets(model) -> set[tuple[str, ...]]:
    return {
        tuple(column.name for column in constraint.columns)
        for constraint in model.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }


def test_all_relationships_resolve() -> None:
    # Raises if any back_populates name or forward reference ("FacilityContact") is wrong.
    configure_mappers()


def test_all_nine_tables_are_registered() -> None:
    assert set(Base.metadata.tables) == {
        "states",
        "lgas",
        "services",
        "data_sources",
        "facilities",
        "facility_services",
        "facility_contacts",
        "service_schedules",
        "verification_history",
    }


def test_every_table_uses_a_database_generated_uuidv7_primary_key() -> None:
    for table in Base.metadata.tables.values():
        (primary_key,) = table.primary_key.columns
        assert isinstance(primary_key.type, Uuid), table.name
        assert "uuidv7" in str(primary_key.server_default.arg), table.name


def test_every_foreign_key_column_is_a_uuid() -> None:
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if column.foreign_keys:
                assert isinstance(column.type, Uuid), f"{table.name}.{column.name}"


def test_every_enum_column_has_exactly_one_explicit_check() -> None:
    for table in Base.metadata.tables.values():
        check_names = [c.name for c in table.constraints if isinstance(c, CheckConstraint)]
        for column in table.columns:
            if isinstance(column.type, Enum):
                # Implicit constraints are what made autogenerate render duplicates.
                assert column.type.create_constraint is False, f"{table.name}.{column.name}"
                expected = f"ck_{table.name}_{column.name}_allowed"
                assert check_names.count(expected) == 1, f"missing or duplicate {expected}"


@pytest.mark.parametrize("model", [Facility, FacilityService, FacilityContact, ServiceSchedule])
def test_every_demo_capable_table_forbids_verified_demo_data(model) -> None:
    assert f"ck_{model.__tablename__}_demo_never_verified" in _check_names(model)


def test_a_facility_lists_each_service_only_once() -> None:
    assert ("facility_id", "service_id") in _unique_column_sets(FacilityService)


def test_service_availability_and_verification_are_separate_columns() -> None:
    columns = FacilityService.__table__.c

    assert "availability_status" in columns
    assert "verification_status" in columns


def test_only_one_active_primary_contact_is_allowed() -> None:
    indexes = {index.name: index for index in FacilityContact.__table__.indexes}

    general = indexes["uq_facility_contacts_one_primary_general"]
    per_service = indexes["uq_facility_contacts_one_primary_per_service"]

    assert general.unique and per_service.unique
    assert "is_primary AND is_active" in str(general.dialect_options["postgresql"]["where"])
    assert "is_primary AND is_active" in str(per_service.dialect_options["postgresql"]["where"])


def test_contacts_must_be_reachable_and_phone_must_be_e164() -> None:
    assert {"ck_facility_contacts_reachable", "ck_facility_contacts_phone_e164"} <= _check_names(
        FacilityContact
    )


@pytest.mark.parametrize(
    ("phone", "is_valid"),
    [
        ("+2348012345678", True),  # Nigerian mobile in E.164
        ("+2340000000000", True),  # obviously fake demo number
        ("08012345678", False),  # local format: missing +234
        ("+234 801 234 5678", False),  # spaces are not allowed in storage
        ("+0234801234567", False),  # country codes never start with 0
    ],
)
def test_e164_pattern(phone: str, is_valid: bool) -> None:
    assert bool(E164_PATTERN.match(phone)) is is_valid


def test_schedule_rules_are_declared() -> None:
    assert {
        "ck_service_schedules_day_of_week_range",
        "ck_service_schedules_hours_consistent",
    } <= _check_names(ServiceSchedule)


def test_schedule_treats_null_service_as_a_duplicate() -> None:
    (constraint,) = [
        c for c in ServiceSchedule.__table__.constraints if isinstance(c, UniqueConstraint)
    ]
    assert constraint.dialect_options["postgresql"]["nulls_not_distinct"] is True


def test_verification_history_is_append_only_in_shape() -> None:
    columns = VerificationHistory.__table__.c

    # It records when the event happened, but has no updated_at: history is never edited.
    assert "verified_at" in columns
    assert "updated_at" not in columns


def test_contact_assigned_to_facility_appears_in_its_contacts() -> None:
    facility = Facility(name="Demo PHC")
    contact = FacilityContact(full_name="Jane Doe (Demo)", role_title="Officer-in-Charge")
    contact.facility = facility

    assert contact in facility.contacts
