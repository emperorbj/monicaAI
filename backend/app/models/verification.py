"""Append-only log of verification events: who confirmed what, when, and what changed."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import EntityType, enum_check, enum_column


class VerificationHistory(Base):
    """One row per verification event. Rows are only ever added, never edited or deleted.

    entity_type + entity_id point at the record that was checked. This can't be a real foreign
    key because it points at a different table depending on entity_type, so the service layer
    (not the database) makes sure the record exists.

    verified_by (the admin who did it) is added in Module 2, when the admin_users table exists.
    """

    __tablename__ = "verification_history"
    __table_args__ = (
        # "Show the history of contact #12" is the main lookup.
        Index("ix_verification_history_entity", "entity_type", "entity_id"),
        enum_check("entity_type", EntityType),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Every event belongs to one facility, so an admin can see a facility's full history.
    facility_id: Mapped[int] = mapped_column(
        ForeignKey("facilities.id", ondelete="RESTRICT"), index=True
    )
    entity_type: Mapped[EntityType] = mapped_column(enum_column(EntityType))
    entity_id: Mapped[int]
    field_name: Mapped[str | None] = mapped_column(String(100))  # e.g. "verification_status"
    old_value: Mapped[str | None] = mapped_column(Text)  # e.g. "unknown"
    new_value: Mapped[str | None] = mapped_column(Text)  # e.g. "verified"
    notes: Mapped[str | None] = mapped_column(Text)  # evidence, e.g. "Phoned desk on 20 Oct"
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
