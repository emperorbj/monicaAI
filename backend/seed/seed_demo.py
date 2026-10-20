"""Write the fictional demo data (seed/demo_data/) to the database. Safe to run repeatedly.

Run from backend/:   uv run python -m seed.seed_demo

Idempotent: every row is looked up by its natural key (e.g. a facility by LGA + name).
If it exists it is updated to match the demo data; if not, it is inserted. So running
this ten times leaves exactly one copy of everything.

Speed on a far-away database: each table is read ONCE into memory, so checking whether a
row exists costs no network trip. Re-running on a seeded database takes seconds.
The FIRST run into an empty database is slower (~1 minute): PostgreSQL generates each id
(uuidv7()), and SQLAlchemy can't match a batch of returned ids to its Python objects, so it
inserts new rows one at a time. Generating UUIDv7 in Python (Python 3.14's uuid.uuid7())
would allow batching; see CLAUDE.md "Python version" for why we're on 3.13.
"""

import sys
from collections import Counter
from datetime import time
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_engine
from app.models import (
    Base,
    DataSource,
    Facility,
    FacilityContact,
    FacilityService,
    Lga,
    Service,
    ServiceSchedule,
    State,
)
from seed import demo_data


class SeedReport:
    """Counts rows created vs already existing (and updated to match), for the printout."""

    def __init__(self) -> None:
        self.created: Counter[str] = Counter()
        self.existing: Counter[str] = Counter()

    def record(self, table_name: str, was_created: bool) -> None:
        (self.created if was_created else self.existing)[table_name] += 1


class Upserter:
    """Upserts rows while keeping database round trips low.

    The first time a table is used, ALL its rows are loaded once into a dictionary keyed by
    the natural-key values. After that, "does this row exist?" is a dictionary lookup in
    memory, not a database query. Changes are only sent when flush() is called, one level
    at a time, because child rows need their parent's database-generated id.
    (Loading whole tables is fine for demo-sized data; for huge tables you'd filter first.)
    """

    def __init__(self, session: Session, report: SeedReport) -> None:
        self.session = session
        self.report = report
        # (model, natural-key column names) -> {natural-key values: row}
        self._rows: dict[tuple[type[Base], tuple[str, ...]], dict[tuple, Base]] = {}

    def _known_rows(self, model: type[Base], key_columns: tuple[str, ...]) -> dict[tuple, Base]:
        cache_key = (model, key_columns)
        if cache_key not in self._rows:
            rows = self.session.scalars(select(model)).all()  # one query per table
            self._rows[cache_key] = {
                tuple(getattr(row, column) for column in key_columns): row for row in rows
            }
        return self._rows[cache_key]

    def upsert[ModelT: Base](
        self, model: type[ModelT], lookup: dict[str, Any], values: dict[str, Any]
    ) -> ModelT:
        """Find the row matching `lookup` (its natural key); update it, or create it.

        `lookup` = the columns that identify the row (e.g. {"code": "antenatal_care"}).
        `values` = the other columns, which are set to the seed's values either way.
        """
        key_columns = tuple(sorted(lookup))
        known = self._known_rows(model, key_columns)
        key = tuple(lookup[column] for column in key_columns)

        instance = known.get(key)
        was_created = instance is None
        if instance is None:
            instance = model(**lookup, **values)
            self.session.add(instance)
            known[key] = instance  # so a repeat in the same run finds it
        else:
            for column_name, value in values.items():
                setattr(instance, column_name, value)  # unchanged values send no UPDATE

        self.report.record(model.__tablename__, was_created)
        return instance

    def flush(self) -> None:
        """Send all pending INSERTs/UPDATEs now, so new rows get their database-made ids."""
        self.session.flush()


def _decimal_or_none(value: str | None) -> Decimal | None:
    return Decimal(value) if value is not None else None


def _time_or_none(value: str | None) -> time | None:
    return time.fromisoformat(value) if value is not None else None


def _upsert_facility_details(
    upserter: Upserter,
    facility: Facility,
    data: dict[str, Any],
    services_by_code: dict[str, Service],
    demo_fields: dict[str, Any],
) -> None:
    """Upsert one facility's services, contacts, and opening hours (its id must exist)."""
    for offered in data["services"]:
        upserter.upsert(
            FacilityService,
            lookup={"facility_id": facility.id, "service_id": services_by_code[offered["code"]].id},
            values={
                "availability_status": offered["availability"],
                "verification_status": offered["status"],
                **demo_fields,
            },
        )

    for contact in data["contacts"]:
        service = services_by_code.get(contact["service_code"])  # None for general contacts
        upserter.upsert(
            FacilityContact,
            lookup={
                "facility_id": facility.id,
                "full_name": contact["full_name"],
                "role_title": contact["role_title"],
            },
            values={
                "service_id": service.id if service else None,
                "phone": contact["phone"],
                "email": contact["email"],
                "is_primary": contact["is_primary"],
                "is_active": True,
                "verification_status": contact["status"],
                **demo_fields,
            },
        )

    for schedule in data["schedules"]:
        service = services_by_code.get(schedule["service_code"])
        for day in schedule["days"]:  # one row per day of the week
            upserter.upsert(
                ServiceSchedule,
                lookup={
                    "facility_id": facility.id,
                    "service_id": service.id if service else None,
                    "day_of_week": day,
                },
                values={
                    "is_closed": schedule["is_closed"],
                    "opens_at": _time_or_none(schedule["opens_at"]),
                    "closes_at": _time_or_none(schedule["closes_at"]),
                    "verification_status": demo_data.common.REPORTED,
                    **demo_fields,
                },
            )


def run_seed(session: Session) -> SeedReport:
    """Upsert all demo data using the given session. The caller decides when to commit."""
    report = SeedReport()
    upserter = Upserter(session, report)

    # Level 1: rows that point at nothing.
    source = upserter.upsert(
        DataSource,
        lookup={"name": demo_data.DEMO_SOURCE["name"]},
        values={
            "source_type": demo_data.DEMO_SOURCE["source_type"],
            "source_url": demo_data.DEMO_SOURCE["source_url"],
        },
    )
    services_by_code = {
        item["code"]: upserter.upsert(
            Service,
            lookup={"code": item["code"]},
            values={"name": item["name"], "description": item["description"]},
        )
        for item in demo_data.SERVICES
    }
    states = [
        (
            upserter.upsert(State, lookup={"code": data["code"]}, values={"name": data["name"]}),
            data,
        )
        for data in demo_data.STATES
    ]
    upserter.flush()  # now source, services, and states have ids

    # Level 2: LGAs (need state ids).
    lgas = [
        (upserter.upsert(Lga, lookup={"state_id": state.id, "name": lga["name"]}, values={}), lga)
        for state, state_data in states
        for lga in state_data["lgas"]
    ]
    upserter.flush()

    # Level 3: facilities (need LGA ids and the source id).
    # Fields shared by every demo row: always demo, always from the demo source.
    demo_fields = {"is_demo": True, "source_id": source.id}
    facilities = [
        (
            upserter.upsert(
                Facility,
                lookup={"lga_id": lga.id, "name": data["name"]},
                values={
                    "facility_type": data["facility_type"],
                    "address": data["address"],
                    "latitude": _decimal_or_none(data["latitude"]),
                    "longitude": _decimal_or_none(data["longitude"]),
                    "verification_status": data["verification_status"],
                    "is_active": True,
                    **demo_fields,
                },
            ),
            data,
        )
        for lga, lga_data in lgas
        for data in lga_data["facilities"]
    ]
    upserter.flush()

    # Level 4: each facility's services, contacts, and hours (need facility ids).
    for facility, data in facilities:
        _upsert_facility_details(upserter, facility, data, services_by_code, demo_fields)
    upserter.flush()

    return report


def main() -> None:
    settings = get_settings()
    # Fictional data must never end up in a production database.
    if settings.app_env == "production":
        sys.exit("Refusing to seed demo data: APP_ENV is 'production'.")

    print("Seeding demo data...")
    # session.begin() commits at the end of the block, or rolls EVERYTHING back on any error,
    # so a failed run never leaves half the demo data behind.
    with Session(get_engine()) as session, session.begin():
        report = run_seed(session)

    tables = sorted(set(report.created) | set(report.existing))
    print(f"\n{'table':<22}{'created':>9}{'existing':>10}")
    for table in tables:
        print(f"{table:<22}{report.created[table]:>9}{report.existing[table]:>10}")
    print("\nDone. All rows are marked is_demo = true and none are verified.")


if __name__ == "__main__":
    main()
