"""Geography: Nigerian states (including FCT) and their Local Government Areas (LGAs)."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_primary_key

# facility.py imports this file, so importing it back at runtime would be circular.
# TYPE_CHECKING is False when the program runs and True only for type checkers and linters.
if TYPE_CHECKING:
    from app.models.facility import Facility


class State(TimestampMixin, Base):
    __tablename__ = "states"

    id: Mapped[uuid.UUID] = uuid_primary_key()
    name: Mapped[str] = mapped_column(String(100), unique=True)  # e.g. "Oyo"
    code: Mapped[str] = mapped_column(String(10), unique=True)  # short code, e.g. "OY"

    # One state -> many LGAs. back_populates links this to Lga.state, so both sides stay in sync.
    lgas: Mapped[list["Lga"]] = relationship(back_populates="state")

    def __repr__(self) -> str:
        return f"State(id={self.id!r}, name={self.name!r})"


class Lga(TimestampMixin, Base):
    __tablename__ = "lgas"
    # LGA names repeat across states (Surulere exists in both Lagos and Oyo),
    # so a name only has to be unique within its own state.
    __table_args__ = (UniqueConstraint("state_id", "name"),)

    id: Mapped[uuid.UUID] = uuid_primary_key()
    # ondelete="RESTRICT": the database refuses to delete a state that still has LGAs.
    # index=True: PostgreSQL doesn't index foreign keys automatically, and we filter by state often.
    state_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("states.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))  # e.g. "Ibadan North"

    state: Mapped[State] = relationship(back_populates="lgas")
    facilities: Mapped[list["Facility"]] = relationship(back_populates="lga")

    def __repr__(self) -> str:
        return f"Lga(id={self.id!r}, name={self.name!r}, state_id={self.state_id!r})"
