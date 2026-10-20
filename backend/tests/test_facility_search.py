"""Integration tests: search_facilities() against the seeded demo data (rolled back after).

The expected answers below come straight from seed/demo_data.py.
"""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Facility, Lga
from app.models.enums import AvailabilityStatus
from app.services.facility_service import (
    UnknownLgaError,
    UnknownServiceError,
    search_facilities,
)

pytestmark = pytest.mark.integration


def _lga_id(session: Session, name: str) -> int:
    return session.scalars(select(Lga.id).where(Lga.name == name)).one()


def _demo_matches(session: Session, service_code: str, lga_name: str = "Ibadan North"):
    """Search, keeping only demo results (so real data added later can't break these tests)."""
    result = search_facilities(session, service_code, _lga_id(session, lga_name))
    return result, [match for match in result.facilities if match.is_demo]


def _by_name(matches, name: str):
    return next(match for match in matches if match.name == name)


def test_antenatal_search_returns_matching_facilities_in_rule_order(
    seeded_session: Session,
) -> None:
    result, matches = _demo_matches(seeded_session, "antenatal_care")

    assert result.service.name == "Antenatal care"
    assert result.lga.state_name == "Oyo"
    # Hilltop is missing: it doesn't offer antenatal care.
    # Market Road is last: its antenatal availability is unknown. The rest are A-Z.
    assert [m.name for m in matches] == [
        "Demo Garden Primary Health Centre",
        "Demo Ibadan North General Hospital",
        "Demo Riverside Comprehensive Health Centre",
        "Demo Sunrise Primary Health Centre",
        "Demo Market Road Primary Health Centre",
    ]


def test_service_specific_contact_is_chosen_for_its_service(seeded_session: Session) -> None:
    _, matches = _demo_matches(seeded_session, "antenatal_care")
    sunrise = _by_name(matches, "Demo Sunrise Primary Health Centre")

    assert sunrise.contact.full_name == "Ngozi Example (Demo)"
    assert sunrise.contact.is_service_specific is True
    assert sunrise.other_contacts_count == 1  # the general officer-in-charge


def test_general_contact_is_used_for_other_services(seeded_session: Session) -> None:
    _, matches = _demo_matches(seeded_session, "malaria_testing")
    sunrise = _by_name(matches, "Demo Sunrise Primary Health Centre")

    assert sunrise.contact.full_name == "Tunde Sample (Demo)"
    assert sunrise.other_contacts_count == 0  # the antenatal lead is NOT offered here


def test_facility_without_contacts_returns_none_not_a_guess(seeded_session: Session) -> None:
    _, matches = _demo_matches(seeded_session, "antenatal_care")
    garden = _by_name(matches, "Demo Garden Primary Health Centre")

    assert garden.contact is None
    assert garden.other_contacts_count == 0


def test_facility_without_coordinates_keeps_them_empty(seeded_session: Session) -> None:
    _, matches = _demo_matches(seeded_session, "family_planning")
    market_road = _by_name(matches, "Demo Market Road Primary Health Centre")

    assert market_road.latitude is None and market_road.longitude is None


def test_temporarily_unavailable_service_is_listed_last(seeded_session: Session) -> None:
    _, matches = _demo_matches(seeded_session, "childhood_immunisation")

    assert matches[-1].name == "Demo Hilltop Health Post"
    assert matches[-1].service_availability == AvailabilityStatus.TEMPORARILY_UNAVAILABLE


def test_lga_without_facilities_returns_an_empty_list(seeded_session: Session) -> None:
    result, matches = _demo_matches(seeded_session, "antenatal_care", "Ibadan North-West")

    assert matches == []
    assert result.lga.name == "Ibadan North-West"  # the search itself was valid


def test_every_result_is_labelled_demo(seeded_session: Session) -> None:
    result = search_facilities(
        seeded_session, "antenatal_care", _lga_id(seeded_session, "Ibadan North")
    )
    demo_names = {m.name for m in result.facilities if m.is_demo}

    assert all(name.startswith("Demo") for name in demo_names)
    assert all(m.contact is None or m.contact.is_demo for m in result.facilities if m.is_demo)


def test_unknown_service_code_raises(seeded_session: Session) -> None:
    with pytest.raises(UnknownServiceError):
        search_facilities(seeded_session, "brain_surgery", _lga_id(seeded_session, "Ibadan North"))


def test_unknown_lga_raises(seeded_session: Session) -> None:
    with pytest.raises(UnknownLgaError):
        # A random UUID that no LGA has.
        search_facilities(seeded_session, "antenatal_care", lga_id=uuid.uuid4())


def test_deactivated_facility_is_excluded(db_session: Session) -> None:
    # Writes data, so it uses its own db_session (seeded here) rather than the shared one.
    from seed.seed_demo import run_seed

    run_seed(db_session)
    sunrise = db_session.scalars(
        select(Facility).where(Facility.name == "Demo Sunrise Primary Health Centre")
    ).one()
    sunrise.is_active = False
    db_session.flush()

    _, matches = _demo_matches(db_session, "antenatal_care")

    assert "Demo Sunrise Primary Health Centre" not in {m.name for m in matches}
