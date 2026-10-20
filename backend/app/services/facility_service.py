"""Facility search: which facilities in an LGA offer a service, and who to contact at each.

All facts come from the database. Nothing here guesses: unknown stays unknown, a missing
contact is None, and results are never ordered by distance (we don't know where the user is).
"""

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session, contains_eager, joinedload

from app.models import Facility, FacilityContact, FacilityService, Lga, Service
from app.models.enums import AvailabilityStatus, VerificationStatus
from app.schemas.facility_search import (
    ContactInfo,
    FacilityMatch,
    FacilitySearchResult,
    LgaSummary,
    ServiceSummary,
)

# ---------------------------------------------------------------- errors


class FacilitySearchError(Exception):
    """Base class, so callers can catch every search problem with one except clause."""


class UnknownServiceError(FacilitySearchError):
    def __init__(self, service_code: str) -> None:
        super().__init__(f"Unknown service code: {service_code!r}")
        self.service_code = service_code


class UnknownLgaError(FacilitySearchError):
    def __init__(self, lga_id: int) -> None:
        super().__init__(f"Unknown LGA id: {lga_id}")
        self.lga_id = lga_id


# ---------------------------------------------------------------- ordering rule
# Lower rank = shown earlier. Written as plain dictionaries so the rule is easy to read and explain.

AVAILABILITY_RANK = {
    AvailabilityStatus.AVAILABLE: 0,
    AvailabilityStatus.UNKNOWN: 1,
    AvailabilityStatus.TEMPORARILY_UNAVAILABLE: 2,
}
VERIFICATION_RANK = {
    VerificationStatus.VERIFIED: 0,
    VerificationStatus.REPORTED: 1,
    VerificationStatus.UNKNOWN: 2,
    VerificationStatus.OUTDATED: 3,
}


def result_sort_key(match: FacilityMatch) -> tuple[int, int, str]:
    """Order: available first, then better-verified, then name A-Z (so ties are predictable)."""
    return (
        AVAILABILITY_RANK[match.service_availability],
        VERIFICATION_RANK[match.service_verification_status],
        match.name.lower(),
    )


# ---------------------------------------------------------------- contact choice


def select_contact(
    contacts: Iterable[FacilityContact], service_id: int
) -> tuple[FacilityContact | None, int]:
    """Pick the best contact for this service, and count the other relevant contacts.

    Relevant = active, and either general (service_id NULL) or for THIS service.
    Contacts for other services (e.g. the vaccination lead when asking about antenatal care)
    are never offered. Preference order:
      1. service-specific before general
      2. primary before non-primary
      3. lower display_order first (then lower id, so the choice is always the same)
    """
    relevant = [c for c in contacts if c.is_active and c.service_id in (None, service_id)]
    if not relevant:
        return None, 0

    relevant.sort(
        key=lambda c: (
            c.service_id is None,  # False (specific) sorts before True (general)
            not c.is_primary,  # False (primary) sorts before True
            c.display_order or 0,
            c.id or 0,
        )
    )
    return relevant[0], len(relevant) - 1


def _to_contact_info(contact: FacilityContact) -> ContactInfo:
    return ContactInfo(
        contact_id=contact.id,
        full_name=contact.full_name,
        role_title=contact.role_title,
        phone=contact.phone,
        email=contact.email,
        is_service_specific=contact.service_id is not None,
        verification_status=contact.verification_status,
        last_verified_at=contact.last_verified_at,
        is_demo=contact.is_demo,
    )


def _to_match(offering: FacilityService) -> FacilityMatch:
    facility = offering.facility
    contact, other_contacts_count = select_contact(facility.contacts, offering.service_id)
    return FacilityMatch(
        facility_id=facility.id,
        name=facility.name,
        facility_type=facility.facility_type,
        address=facility.address,
        latitude=facility.latitude,
        longitude=facility.longitude,
        facility_verification_status=facility.verification_status,
        facility_last_verified_at=facility.last_verified_at,
        service_availability=offering.availability_status,
        service_verification_status=offering.verification_status,
        service_last_verified_at=offering.last_verified_at,
        contact=_to_contact_info(contact) if contact else None,
        other_contacts_count=other_contacts_count,
        # Demo if ANY part of the answer is demo, so the bot labels it correctly.
        is_demo=facility.is_demo or offering.is_demo,
    )


# ---------------------------------------------------------------- the search


def search_facilities(session: Session, service_code: str, lga_id: int) -> FacilitySearchResult:
    """Find active facilities in an LGA that list a service, best matches first.

    Raises UnknownServiceError / UnknownLgaError if the inputs don't exist, so callers can
    respond helpfully (the bot asks again; the API returns 404) instead of showing no results.
    An empty `facilities` list is a valid answer: the service and LGA exist, nothing matched.
    """
    service = session.scalars(select(Service).where(Service.code == service_code)).one_or_none()
    if service is None:
        raise UnknownServiceError(service_code)

    lga = session.get(Lga, lga_id, options=[joinedload(Lga.state)])
    if lga is None:
        raise UnknownLgaError(lga_id)

    statement = (
        select(FacilityService)
        .join(FacilityService.facility)
        .where(
            FacilityService.service_id == service.id,
            Facility.lga_id == lga.id,
            Facility.is_active.is_(True),
        )
        # Eager loading avoids the N+1 problem:
        #   contains_eager: fill offering.facility from the JOIN we already wrote (no extra query)
        #   selectinload:   fetch ALL matched facilities' contacts in ONE extra query
        .options(contains_eager(FacilityService.facility).selectinload(Facility.contacts))
    )
    offerings = session.scalars(statement).all()

    matches = sorted((_to_match(offering) for offering in offerings), key=result_sort_key)
    return FacilitySearchResult(
        service=ServiceSummary(code=service.code, name=service.name),
        lga=LgaSummary(lga_id=lga.id, name=lga.name, state_name=lga.state.name),
        facilities=matches,
    )
