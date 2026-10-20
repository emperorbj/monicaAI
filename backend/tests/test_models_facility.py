"""Tests for Service, DataSource, Facility, and the shared enums (definitions only, no database)."""

from decimal import Decimal

import pytest
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.models import Base, DataSource, Facility, Lga, Service, State
from app.models.enums import FacilityType, VerificationStatus


def _check_constraint_names(table) -> set[str]:
    return {c.name for c in table.constraints if isinstance(c, CheckConstraint)}


def _facility_sql() -> str:
    return str(CreateTable(Facility.__table__).compile(dialect=postgresql.dialect()))


def test_new_tables_are_registered_on_the_metadata() -> None:
    assert {"services", "data_sources", "facilities"} <= set(Base.metadata.tables)


def test_verification_statuses_match_the_project_rules() -> None:
    assert {status.value for status in VerificationStatus} == {
        "verified",
        "reported",
        "unknown",
        "outdated",
    }


def test_service_code_is_unique() -> None:
    unique_sets = {
        tuple(column.name for column in constraint.columns)
        for constraint in Service.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("code",) in unique_sets


def test_enums_are_stored_as_lowercase_values_not_python_names() -> None:
    sql = _facility_sql()

    assert "'verified'" in sql
    assert "'VERIFIED'" not in sql


def test_facility_verification_defaults_to_unknown_in_the_database() -> None:
    column = Facility.__table__.c.verification_status

    assert column.server_default.arg == "unknown"


@pytest.mark.parametrize("column_name", ["latitude", "longitude", "address", "source_id"])
def test_unknown_facility_details_can_be_left_empty(column_name: str) -> None:
    assert Facility.__table__.c[column_name].nullable is True


def test_database_enforces_coordinate_and_demo_rules() -> None:
    names = _check_constraint_names(Facility.__table__)

    assert {
        "ck_facilities_latitude_range",
        "ck_facilities_longitude_range",
        "ck_facilities_coordinates_both_or_neither",
        "ck_facilities_demo_never_verified",
    } <= names


def test_has_coordinates_requires_both_values() -> None:
    lga = Lga(name="Ibadan North", state=State(name="Oyo", code="OY"))
    facility = Facility(name="Demo PHC", lga=lga, facility_type=FacilityType.PRIMARY_HEALTH_CENTRE)

    assert facility.has_coordinates is False
    facility.latitude, facility.longitude = Decimal("7.412300"), Decimal("3.905600")
    assert facility.has_coordinates is True


def test_facility_links_to_lga_and_source() -> None:
    lga = Lga(name="Ibadan North", state=State(name="Oyo", code="OY"))
    source = DataSource(name="Demo seed")
    facility = Facility(name="Demo PHC", lga=lga, source=source)

    assert facility in lga.facilities
    assert facility.source is source
