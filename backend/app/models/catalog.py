"""Reference data that other records point to: canonical services and data sources."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import SourceType, enum_check, enum_column


class Service(TimestampMixin, Base):
    """A healthcare service as a concept, e.g. antenatal care. Which facilities offer it
    is stored separately (facility_services, Part 4c)."""

    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Stable machine name used by the API and the bot, e.g. "antenatal_care". Never shown to users.
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))  # human-readable, e.g. "Antenatal care"
    description: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"Service(id={self.id!r}, code={self.code!r})"


class DataSource(TimestampMixin, Base):
    """Where information came from, so every fact can be traced back to its origin."""

    __tablename__ = "data_sources"
    __table_args__ = (enum_check("source_type", SourceType),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    source_type: Mapped[SourceType] = mapped_column(enum_column(SourceType))
    source_url: Mapped[str | None] = mapped_column(String(500))
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"DataSource(id={self.id!r}, name={self.name!r})"
