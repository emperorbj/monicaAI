"""Unit tests for the contact-choice and ordering rules (pure Python, no database)."""

from decimal import Decimal

from app.models import FacilityContact
from app.models.enums import AvailabilityStatus, FacilityType, VerificationStatus
from app.schemas.facility_search import FacilityMatch
from app.services.facility_service import result_sort_key, select_contact

ANTENATAL_ID = 1
VACCINATION_ID = 2


def _contact(name: str, service_id: int | None = None, **fields) -> FacilityContact:
    defaults = {"is_active": True, "is_primary": False, "display_order": 0}
    return FacilityContact(full_name=name, service_id=service_id, **{**defaults, **fields})


def _match(name: str, availability: str, status: str) -> FacilityMatch:
    return FacilityMatch(
        facility_id=1,
        name=name,
        facility_type=FacilityType.PRIMARY_HEALTH_CENTRE,
        address=None,
        latitude=Decimal("7.4"),
        longitude=Decimal("3.9"),
        facility_verification_status=VerificationStatus.REPORTED,
        facility_last_verified_at=None,
        service_availability=AvailabilityStatus(availability),
        service_verification_status=VerificationStatus(status),
        service_last_verified_at=None,
        contact=None,
        other_contacts_count=0,
        is_demo=True,
    )


# ---------------------------------------------------------------- contact choice


def test_service_specific_contact_beats_general_primary() -> None:
    general = _contact("General", is_primary=True)
    antenatal_lead = _contact("Antenatal lead", service_id=ANTENATAL_ID, is_primary=True)

    chosen, others = select_contact([general, antenatal_lead], ANTENATAL_ID)

    assert chosen is antenatal_lead
    assert others == 1  # the general contact can be offered on request


def test_general_primary_is_used_when_no_service_specific_contact() -> None:
    general = _contact("General", is_primary=True)

    chosen, others = select_contact([general], ANTENATAL_ID)

    assert chosen is general
    assert others == 0


def test_contacts_for_other_services_are_never_offered() -> None:
    vaccination_lead = _contact("Vaccination lead", service_id=VACCINATION_ID, is_primary=True)

    chosen, others = select_contact([vaccination_lead], ANTENATAL_ID)

    assert chosen is None  # better "no contact on record" than the wrong person
    assert others == 0


def test_inactive_contacts_are_ignored() -> None:
    old = _contact("Old primary", is_primary=True, is_active=False)
    current = _contact("Current desk")

    chosen, others = select_contact([old, current], ANTENATAL_ID)

    assert chosen is current
    assert others == 0


def test_primary_beats_non_primary_then_display_order_decides() -> None:
    second = _contact("Second", display_order=2)
    first = _contact("First", display_order=1)
    primary = _contact("Primary", is_primary=True, display_order=9)

    assert select_contact([second, first, primary], ANTENATAL_ID)[0] is primary
    assert select_contact([second, first], ANTENATAL_ID)[0] is first


def test_no_contacts_means_none() -> None:
    assert select_contact([], ANTENATAL_ID) == (None, 0)


# ---------------------------------------------------------------- ordering


def test_results_order_by_availability_then_verification_then_name() -> None:
    matches = [
        _match("Zulu", "available", "reported"),
        _match("Unavailable", "temporarily_unavailable", "verified"),
        _match("Alpha", "available", "reported"),
        _match("Unknown availability", "unknown", "verified"),
        _match("Outdated", "available", "outdated"),
    ]

    ordered = [m.name for m in sorted(matches, key=result_sort_key)]

    assert ordered == ["Alpha", "Zulu", "Outdated", "Unknown availability", "Unavailable"]
