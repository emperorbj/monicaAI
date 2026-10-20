"""Official, work-related contact persons for facilities (never personal contact details)."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
    false,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_primary_key
from app.models.catalog import Service
from app.models.enums import VerificationStatus, enum_check, enum_column
from app.models.facility import Facility


class FacilityContact(TimestampMixin, Base):
    """A contact person at a facility, optionally for one specific service.

    service_id NULL = general facility contact (e.g. officer-in-charge).
    service_id set  = service-specific contact (e.g. antenatal clinic lead).
    """

    __tablename__ = "facility_contacts"
    __table_args__ = (
        # Natural key so the seed script can find an existing contact instead of duplicating it.
        UniqueConstraint("facility_id", "full_name", "role_title"),
        # E.164 international format: "+", country code, then digits only. E.g. +2348012345678.
        # Full validation (real country codes, lengths) happens in Pydantic in Module 2.
        CheckConstraint(r"phone ~ '^\+[1-9][0-9]{6,14}$'", name="phone_e164"),
        # A contact with no way to reach them is useless to a resident.
        CheckConstraint("phone IS NOT NULL OR email IS NOT NULL", name="reachable"),
        enum_check("verification_status", VerificationStatus),
        CheckConstraint(
            "NOT (is_demo AND verification_status = 'verified')", name="demo_never_verified"
        ),
        # At most ONE active primary general contact per facility...
        Index(
            "uq_facility_contacts_one_primary_general",
            "facility_id",
            unique=True,
            postgresql_where=text("is_primary AND is_active AND service_id IS NULL"),
        ),
        # ...and at most ONE active primary contact per facility + service.
        # Inactive or non-primary contacts are ignored by both rules (that's the "partial" part).
        Index(
            "uq_facility_contacts_one_primary_per_service",
            "facility_id",
            "service_id",
            unique=True,
            postgresql_where=text("is_primary AND is_active AND service_id IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = uuid_primary_key()
    facility_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("facilities.id", ondelete="RESTRICT"))
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT"), index=True
    )

    full_name: Mapped[str] = mapped_column(String(200))  # e.g. "Jane Doe (Demo)"
    role_title: Mapped[str] = mapped_column(String(100))  # e.g. "Officer-in-Charge"
    phone: Mapped[str | None] = mapped_column(String(16))  # E.164 is at most 15 digits + "+"
    email: Mapped[str | None] = mapped_column(String(254))  # longest valid email address

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    # Admin-controlled order for non-primary contacts (lower numbers shown first).
    display_order: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")

    # A contact's trust level is independent of the facility's and the service's.
    verification_status: Mapped[VerificationStatus] = mapped_column(
        enum_column(VerificationStatus),
        default=VerificationStatus.UNKNOWN,
        server_default=VerificationStatus.UNKNOWN.value,
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("data_sources.id", ondelete="RESTRICT"), index=True
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())

    facility: Mapped[Facility] = relationship(back_populates="contacts")
    service: Mapped[Service | None] = relationship()

    def __repr__(self) -> str:
        return f"FacilityContact(id={self.id!r}, full_name={self.full_name!r})"
