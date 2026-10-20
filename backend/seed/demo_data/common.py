"""Shared pieces for the per-state demo data files: status aliases, services, and helpers.

The helper functions (offers, contact, hours, facility) only build plain dictionaries.
They exist so each facility in a state file is short and easy to read.
"""

from typing import Any

from app.models.enums import (
    AvailabilityStatus,
    FacilityType,
    SourceType,
    VerificationStatus,
)

# Short aliases keep the state files readable.
AVAILABLE = AvailabilityStatus.AVAILABLE
UNAVAILABLE = AvailabilityStatus.TEMPORARILY_UNAVAILABLE
UNKNOWN_AVAILABILITY = AvailabilityStatus.UNKNOWN
REPORTED = VerificationStatus.REPORTED
UNKNOWN = VerificationStatus.UNKNOWN
OUTDATED = VerificationStatus.OUTDATED
# There is deliberately no VERIFIED alias: demo data is never verified.

PHC = FacilityType.PRIMARY_HEALTH_CENTRE
CHC = FacilityType.COMPREHENSIVE_HEALTH_CENTRE
HEALTH_POST = FacilityType.HEALTH_POST
GENERAL_HOSPITAL = FacilityType.GENERAL_HOSPITAL

WEEKDAYS = [1, 2, 3, 4, 5]  # ISO: 1 = Monday ... 5 = Friday
SATURDAY, SUNDAY = 6, 7
EVERY_DAY = [1, 2, 3, 4, 5, 6, 7]

DEMO_SOURCE = {
    "name": "Demo seed data (fictional)",
    "source_type": SourceType.DEMO_SEED,
    "source_url": None,
}

# Canonical services: real healthcare concepts, so they are not marked as demo.
# Descriptions are neutral and contain no medical advice.
SERVICES = [
    {
        "code": "antenatal_care",
        "name": "Antenatal care",
        "description": "Check-ups and support during pregnancy.",
    },
    {
        "code": "postnatal_care",
        "name": "Postnatal care",
        "description": "Care for mothers and newborns after birth.",
    },
    {
        "code": "delivery_services",
        "name": "Labour and delivery",
        "description": "Care during labour and childbirth.",
    },
    {
        "code": "childhood_immunisation",
        "name": "Childhood immunisation",
        "description": "Routine vaccines for babies and children.",
    },
    {
        "code": "nutrition_services",
        "name": "Nutrition services",
        "description": "Nutrition counselling and screening, including for children.",
    },
    {
        "code": "malaria_testing",
        "name": "Malaria testing",
        "description": "Testing for malaria.",
    },
    {
        "code": "family_planning",
        "name": "Family planning",
        "description": "Information and services for family planning.",
    },
    {
        "code": "hiv_testing",
        "name": "HIV testing and counselling",
        "description": "Confidential HIV testing and counselling.",
    },
    {
        "code": "tuberculosis_screening",
        "name": "Tuberculosis screening",
        "description": "Screening for tuberculosis (TB).",
    },
    {
        "code": "general_outpatient",
        "name": "General outpatient care",
        "description": "Consultations for general health concerns.",
    },
]


def offers(
    code: str,
    availability: AvailabilityStatus = AVAILABLE,
    status: VerificationStatus = REPORTED,
) -> dict[str, Any]:
    """'This facility offers <code>', with how available and how verified that is."""
    return {"code": code, "availability": availability, "status": status}


def contact(
    full_name: str,
    role_title: str,
    *,
    phone: str | None = None,
    email: str | None = None,
    primary: bool = False,
    service_code: str | None = None,
    status: VerificationStatus = REPORTED,
) -> dict[str, Any]:
    """A contact person. service_code=None means a general facility contact."""
    return {
        "full_name": full_name,
        "role_title": role_title,
        "phone": phone,
        "email": email,
        "is_primary": primary,
        "service_code": service_code,
        "status": status,
    }


def hours(
    days: list[int],
    opens_at: str | None = None,
    closes_at: str | None = None,
    *,
    service_code: str | None = None,
    closed: bool = False,
) -> dict[str, Any]:
    """Opening hours for some days. closed=True records 'closed' (different from no data)."""
    return {
        "service_code": service_code,
        "days": days,
        "opens_at": opens_at,
        "closes_at": closes_at,
        "is_closed": closed,
    }


def facility(
    name: str,
    facility_type: FacilityType,
    address: str,
    coordinates: tuple[str, str] | None,
    status: VerificationStatus,
    *,
    services: list[dict[str, Any]],
    contacts: list[dict[str, Any]] | None = None,
    schedules: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """A fictional facility. coordinates=None means 'location unknown' (no map link)."""
    latitude, longitude = coordinates if coordinates else (None, None)
    return {
        "name": name,
        "facility_type": facility_type,
        "address": address,
        "latitude": latitude,
        "longitude": longitude,
        "verification_status": status,
        "services": services,
        "contacts": contacts or [],
        "schedules": schedules or [],
    }
