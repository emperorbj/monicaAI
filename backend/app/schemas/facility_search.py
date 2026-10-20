"""Results of a facility search.

These are deliberately separate from the database models: they describe what we GIVE OUT,
and carry every status and demo flag the bot needs to be honest about what it says.
frozen=True makes results read-only, so no caller can quietly change a fact after the search.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import AvailabilityStatus, FacilityType, VerificationStatus


class ContactInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    contact_id: uuid.UUID
    full_name: str
    role_title: str
    phone: str | None
    email: str | None
    is_service_specific: bool  # True = e.g. antenatal clinic lead, False = general contact
    verification_status: VerificationStatus
    last_verified_at: datetime | None
    is_demo: bool


class FacilityMatch(BaseModel):
    model_config = ConfigDict(frozen=True)

    facility_id: uuid.UUID
    name: str
    facility_type: FacilityType
    address: str | None
    latitude: Decimal | None  # None = location unknown: no map link
    longitude: Decimal | None
    facility_verification_status: VerificationStatus
    facility_last_verified_at: datetime | None

    # The requested service at THIS facility, with its own statuses.
    service_availability: AvailabilityStatus
    service_verification_status: VerificationStatus
    service_last_verified_at: datetime | None

    contact: ContactInfo | None  # None = no contact on record (never invent one)
    other_contacts_count: int  # more contacts the bot can offer on request
    is_demo: bool


class ServiceSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    name: str


class LgaSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    lga_id: uuid.UUID
    name: str
    state_name: str


class FacilitySearchResult(BaseModel):
    """What was searched for, and the matches (possibly none) in a fixed, explainable order."""

    model_config = ConfigDict(frozen=True)

    service: ServiceSummary
    lga: LgaSummary
    facilities: list[FacilityMatch]
