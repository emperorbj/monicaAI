"""Health facilities: identity, location, and how trustworthy that information is."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    false,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_primary_key
from app.models.catalog import DataSource
from app.models.enums import FacilityType, VerificationStatus, enum_check, enum_column
from app.models.location import Lga

# These files import Facility, so import them only for type checkers (avoids circular imports).
if TYPE_CHECKING:
    from app.models.contact import FacilityContact
    from app.models.offering import FacilityService, ServiceSchedule


class Facility(TimestampMixin, Base):
    __tablename__ = "facilities"
    __table_args__ = (
        # The (LGA, name) pair identifies a facility. The seed script relies on this to
        # find existing rows instead of inserting duplicates.
        UniqueConstraint("lga_id", "name"),
        enum_check("facility_type", FacilityType),
        enum_check("verification_status", VerificationStatus),
        CheckConstraint("latitude BETWEEN -90 AND 90", name="latitude_range"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="longitude_range"),
        # A map link needs both numbers: store both coordinates or neither.
        CheckConstraint(
            "(latitude IS NULL) = (longitude IS NULL)", name="coordinates_both_or_neither"
        ),
        # Project rule enforced by the database itself: demo data can never be "verified".
        CheckConstraint(
            "NOT (is_demo AND verification_status = 'verified')", name="demo_never_verified"
        ),
    )

    id: Mapped[uuid.UUID] = uuid_primary_key()
    lga_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lgas.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    facility_type: Mapped[FacilityType] = mapped_column(enum_column(FacilityType))
    address: Mapped[str | None] = mapped_column(Text)

    # NULL means "we don't know where it is", so the bot must not produce a map link.
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))

    # Trust in the facility's identity and location. Services and contacts have their own.
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
    # Admins deactivate facilities instead of deleting them, so history stays intact.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

    lga: Mapped[Lga] = relationship(back_populates="facilities")
    source: Mapped[DataSource | None] = relationship()
    services: Mapped[list["FacilityService"]] = relationship(back_populates="facility")
    contacts: Mapped[list["FacilityContact"]] = relationship(back_populates="facility")
    schedules: Mapped[list["ServiceSchedule"]] = relationship(back_populates="facility")

    @property
    def has_coordinates(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    def __repr__(self) -> str:
        return f"Facility(id={self.id!r}, name={self.name!r}, is_demo={self.is_demo!r})"
