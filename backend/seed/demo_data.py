"""FICTIONAL demonstration data for the pilot LGA (Ibadan North, Oyo State).

Everything below except the state, LGA, and service names is invented:
- Facility names contain "Demo"; coordinates are illustrative points inside Ibadan North.
- People have obviously fictional surnames and "(Demo)" in their name.
- Phone numbers use +234 000..., a range Nigerian numbers never use, so nobody can be called.
- Emails use example.org, a domain reserved for examples that never reaches a real inbox.
- Nothing is ever "verified". (The database rejects verified demo data anyway.)

This file only holds data. seed_demo.py contains the code that writes it to the database.
"""

from app.models.enums import (
    AvailabilityStatus,
    FacilityType,
    SourceType,
    VerificationStatus,
)

# Short aliases keep the tables below readable.
AVAILABLE = AvailabilityStatus.AVAILABLE
UNAVAILABLE = AvailabilityStatus.TEMPORARILY_UNAVAILABLE
UNKNOWN_AVAILABILITY = AvailabilityStatus.UNKNOWN
REPORTED = VerificationStatus.REPORTED
UNKNOWN = VerificationStatus.UNKNOWN
OUTDATED = VerificationStatus.OUTDATED

WEEKDAYS = [1, 2, 3, 4, 5]  # ISO: 1 = Monday ... 5 = Friday

DEMO_SOURCE = {
    "name": "Demo seed data (fictional)",
    "source_type": SourceType.DEMO_SEED,
    "source_url": None,
}

# Real geography. Ibadan North-West deliberately gets no facilities: the "no results" case.
STATE = {"name": "Oyo", "code": "OY"}
LGA_NAMES = ["Ibadan North", "Ibadan North-West"]
PILOT_LGA_NAME = "Ibadan North"

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
        "code": "childhood_immunisation",
        "name": "Childhood immunisation",
        "description": "Routine vaccines for babies and children.",
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

# Each facility lists its own services, contacts, and opening hours.
# schedules: "service_code": None means the facility's general hours.
FACILITIES = [
    {
        "name": "Demo Sunrise Primary Health Centre",
        "facility_type": FacilityType.PRIMARY_HEALTH_CENTRE,
        "address": "12 Example Close, Ibadan North (fictional address)",
        "latitude": "7.412300",
        "longitude": "3.905600",
        "verification_status": REPORTED,
        "services": [
            {"code": "antenatal_care", "availability": AVAILABLE, "status": REPORTED},
            {"code": "childhood_immunisation", "availability": AVAILABLE, "status": REPORTED},
            {"code": "malaria_testing", "availability": AVAILABLE, "status": UNKNOWN},
            {"code": "family_planning", "availability": UNKNOWN_AVAILABILITY, "status": UNKNOWN},
        ],
        "contacts": [
            {
                "full_name": "Tunde Sample (Demo)",
                "role_title": "Officer-in-Charge",
                "phone": "+2340000000001",
                "email": "sunrise.phc@example.org",
                "is_primary": True,
                "service_code": None,
                "status": REPORTED,
            },
            # Service-specific contact: shown instead of the general one for antenatal care.
            {
                "full_name": "Ngozi Example (Demo)",
                "role_title": "Antenatal Clinic Lead",
                "phone": "+2340000000002",
                "email": None,
                "is_primary": True,
                "service_code": "antenatal_care",
                "status": REPORTED,
            },
        ],
        "schedules": [
            {"service_code": None, "days": WEEKDAYS, "opens_at": "08:00", "closes_at": "16:00"},
            {"service_code": None, "days": [7], "is_closed": True},  # Sunday: closed
            # Saturday has no row on purpose: hours unknown (not closed).
            {
                "service_code": "antenatal_care",
                "days": [2, 4],
                "opens_at": "09:00",
                "closes_at": "13:00",
            },
        ],
    },
    {
        "name": "Demo Riverside Comprehensive Health Centre",
        "facility_type": FacilityType.COMPREHENSIVE_HEALTH_CENTRE,
        "address": "4 Sample Road, Ibadan North (fictional address)",
        "latitude": "7.425800",
        "longitude": "3.912400",
        "verification_status": REPORTED,
        "services": [
            {"code": "antenatal_care", "availability": AVAILABLE, "status": REPORTED},
            {"code": "postnatal_care", "availability": AVAILABLE, "status": REPORTED},
            {"code": "childhood_immunisation", "availability": AVAILABLE, "status": OUTDATED},
            {"code": "hiv_testing", "availability": AVAILABLE, "status": REPORTED},
            {"code": "general_outpatient", "availability": AVAILABLE, "status": REPORTED},
        ],
        "contacts": [
            {
                "full_name": "Aisha Placeholder (Demo)",
                "role_title": "Officer-in-Charge",
                "phone": "+2340000000003",
                "email": "riverside.chc@example.org",
                "is_primary": True,
                "service_code": None,
                "status": OUTDATED,
            },
            # A second, non-primary general contact: the bot offers it on request.
            {
                "full_name": "Riverside Front Desk (Demo)",
                "role_title": "Reception",
                "phone": "+2340000000004",
                "email": None,
                "is_primary": False,
                "service_code": None,
                "status": UNKNOWN,
            },
        ],
        "schedules": [
            {
                "service_code": None,
                "days": [*WEEKDAYS, 6],
                "opens_at": "08:00",
                "closes_at": "18:00",
            },
        ],
    },
    {
        "name": "Demo Hilltop Health Post",
        "facility_type": FacilityType.HEALTH_POST,
        "address": "Hilltop Street, Ibadan North (fictional address)",
        "latitude": "7.437100",
        "longitude": "3.897200",
        "verification_status": UNKNOWN,
        "services": [
            {"code": "malaria_testing", "availability": AVAILABLE, "status": REPORTED},
            # Temporarily unavailable: the bot must say so, not hide the facility silently.
            {"code": "childhood_immunisation", "availability": UNAVAILABLE, "status": REPORTED},
        ],
        "contacts": [
            # Email only, no phone.
            {
                "full_name": "Emeka Test (Demo)",
                "role_title": "Health Post Coordinator",
                "phone": None,
                "email": "hilltop.post@example.org",
                "is_primary": True,
                "service_code": None,
                "status": UNKNOWN,
            },
        ],
        "schedules": [],  # no hours on record at all
    },
    {
        # No coordinates: the bot must not produce a map link.
        "name": "Demo Market Road Primary Health Centre",
        "facility_type": FacilityType.PRIMARY_HEALTH_CENTRE,
        "address": "Market Road, Ibadan North (fictional address)",
        "latitude": None,
        "longitude": None,
        "verification_status": UNKNOWN,
        "services": [
            {"code": "family_planning", "availability": AVAILABLE, "status": REPORTED},
            {"code": "antenatal_care", "availability": UNKNOWN_AVAILABILITY, "status": UNKNOWN},
        ],
        "contacts": [
            {
                "full_name": "Funmi Fictional (Demo)",
                "role_title": "Officer-in-Charge",
                "phone": "+2340000000005",
                "email": None,
                "is_primary": True,
                "service_code": None,
                "status": REPORTED,
            },
        ],
        "schedules": [
            {"service_code": None, "days": WEEKDAYS, "opens_at": "08:00", "closes_at": "15:00"},
        ],
    },
    {
        # No contact on record: the bot must say so instead of inventing one.
        "name": "Demo Garden Primary Health Centre",
        "facility_type": FacilityType.PRIMARY_HEALTH_CENTRE,
        "address": "Garden Avenue, Ibadan North (fictional address)",
        "latitude": "7.418900",
        "longitude": "3.921700",
        "verification_status": REPORTED,
        "services": [
            {"code": "antenatal_care", "availability": AVAILABLE, "status": REPORTED},
            {"code": "childhood_immunisation", "availability": AVAILABLE, "status": REPORTED},
            {"code": "tuberculosis_screening", "availability": AVAILABLE, "status": UNKNOWN},
        ],
        "contacts": [],
        "schedules": [
            {"service_code": None, "days": WEEKDAYS, "opens_at": "08:00", "closes_at": "16:00"},
        ],
    },
    {
        "name": "Demo Ibadan North General Hospital",
        "facility_type": FacilityType.GENERAL_HOSPITAL,
        "address": "1 Fictional Hospital Way, Ibadan North (fictional address)",
        "latitude": "7.430500",
        "longitude": "3.908800",
        "verification_status": REPORTED,
        "services": [
            {"code": "antenatal_care", "availability": AVAILABLE, "status": REPORTED},
            {"code": "postnatal_care", "availability": AVAILABLE, "status": REPORTED},
            {"code": "malaria_testing", "availability": AVAILABLE, "status": REPORTED},
            {"code": "hiv_testing", "availability": AVAILABLE, "status": REPORTED},
            {"code": "tuberculosis_screening", "availability": AVAILABLE, "status": REPORTED},
            {"code": "general_outpatient", "availability": AVAILABLE, "status": REPORTED},
        ],
        "contacts": [
            {
                "full_name": "Hospital Information Desk (Demo)",
                "role_title": "Information Desk",
                "phone": "+2340000000006",
                "email": "info.generalhospital@example.org",
                "is_primary": True,
                "service_code": None,
                "status": REPORTED,
            },
        ],
        "schedules": [
            # Open around the clock. 23:59 because closing must be after opening on the same day.
            {
                "service_code": None,
                "days": [1, 2, 3, 4, 5, 6, 7],
                "opens_at": "00:00",
                "closes_at": "23:59",
            },
        ],
    },
]
