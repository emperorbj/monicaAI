"""What each facility offers (facility_services) and when (service_schedules)."""

import uuid
from datetime import datetime, time

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    SmallInteger,
    Time,
    UniqueConstraint,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_primary_key
from app.models.catalog import Service
from app.models.enums import AvailabilityStatus, VerificationStatus, enum_check, enum_column
from app.models.facility import Facility


class FacilityService(TimestampMixin, Base):
    """Link row: "this facility offers this service", plus how sure we are about that."""

    __tablename__ = "facility_services"
    __table_args__ = (
        # One row per (facility, service) pair. This composite index also speeds up
        # "all services at facility X", because facility_id is its first column.
        UniqueConstraint("facility_id", "service_id"),
        enum_check("availability_status", AvailabilityStatus),
        enum_check("verification_status", VerificationStatus),
        CheckConstraint(
            "NOT (is_demo AND verification_status = 'verified')", name="demo_never_verified"
        ),
    )

    id: Mapped[uuid.UUID] = uuid_primary_key()
    facility_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("facilities.id", ondelete="RESTRICT"))
    # Own index: the main search is "facilities offering service Y", which filters on service_id.
    service_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT"), index=True
    )

    # Is it running? And separately: how sure are we? Both start as unknown.
    availability_status: Mapped[AvailabilityStatus] = mapped_column(
        enum_column(AvailabilityStatus),
        default=AvailabilityStatus.UNKNOWN,
        server_default=AvailabilityStatus.UNKNOWN.value,
    )
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

    facility: Mapped[Facility] = relationship(back_populates="services")
    service: Mapped[Service] = relationship()

    def __repr__(self) -> str:
        return f"FacilityService(facility_id={self.facility_id!r}, service_id={self.service_id!r})"


class ServiceSchedule(TimestampMixin, Base):
    """Opening hours for one day of the week.

    service_id NULL means the facility's general hours; otherwise the hours of that service
    (e.g. an antenatal clinic held only on Tuesdays). No row for a day means "unknown",
    never "closed". The bot must not assume either way.
    """

    __tablename__ = "service_schedules"
    __table_args__ = (
        # One row per facility + service + day. NULLS NOT DISTINCT makes two rows with
        # service_id NULL count as duplicates (by default PostgreSQL treats NULLs as all different).
        UniqueConstraint(
            "facility_id", "service_id", "day_of_week", postgresql_nulls_not_distinct=True
        ),
        # ISO weekdays, matching Python's date.isoweekday(): 1 = Monday ... 7 = Sunday.
        CheckConstraint("day_of_week BETWEEN 1 AND 7", name="day_of_week_range"),
        enum_check("verification_status", VerificationStatus),
        # A closed day has no times; an open day needs both, and must close after it opens.
        CheckConstraint(
            "(is_closed AND opens_at IS NULL AND closes_at IS NULL)"
            " OR (NOT is_closed AND opens_at IS NOT NULL AND closes_at IS NOT NULL"
            " AND closes_at > opens_at)",
            name="hours_consistent",
        ),
        CheckConstraint(
            "NOT (is_demo AND verification_status = 'verified')", name="demo_never_verified"
        ),
    )

    id: Mapped[uuid.UUID] = uuid_primary_key()
    facility_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("facilities.id", ondelete="RESTRICT"))
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT"), index=True
    )
    day_of_week: Mapped[int] = mapped_column(SmallInteger)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    opens_at: Mapped[time | None] = mapped_column(Time)
    closes_at: Mapped[time | None] = mapped_column(Time)

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

    facility: Mapped[Facility] = relationship(back_populates="schedules")
    service: Mapped[Service | None] = relationship()
