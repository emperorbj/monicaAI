"""Write the fictional demo data (seed/demo_data.py) to the database. Safe to run repeatedly.

Run from backend/:   uv run python -m seed.seed_demo

Idempotent: every row is looked up by its natural key (e.g. a facility by LGA + name).
If it exists it is updated to match demo_data.py; if not, it is inserted. So running this
ten times leaves exactly one copy of everything.
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
    """Counts how many rows of each table were created vs updated, for the summary printout."""

    def __init__(self) -> None:
        self.created: Counter[str] = Counter()
        self.updated: Counter[str] = Counter()

    def record(self, table_name: str, was_created: bool) -> None:
        (self.created if was_created else self.updated)[table_name] += 1


def upsert[ModelT: Base](
    session: Session,
    report: SeedReport,
    model: type[ModelT],
    lookup: dict[str, Any],
    values: dict[str, Any],
) -> ModelT:
    """Find the row matching `lookup` (its natural key); update it, or create it if missing.

    `lookup` = the columns that identify the row (e.g. {"code": "antenatal_care"}).
    `values` = the other columns, which are set to the seed's values either way.
    """
    # filter_by(service_id=None) becomes "service_id IS NULL" in SQL, as we need.
    instance = session.scalars(select(model).filter_by(**lookup)).one_or_none()
    was_created = instance is None
    if instance is None:
        instance = model(**lookup, **values)
        session.add(instance)
    else:
        for column_name, value in values.items():
            setattr(instance, column_name, value)
    # flush sends the INSERT/UPDATE now, so the row gets its id for child rows to point to.
    session.flush()
    report.record(model.__tablename__, was_created)
    return instance


def _decimal_or_none(value: str | None) -> Decimal | None:
    return Decimal(value) if value is not None else None


def _time_or_none(value: str | None) -> time | None:
    return time.fromisoformat(value) if value is not None else None


def seed_facility(
    session: Session,
    report: SeedReport,
    data: dict[str, Any],
    lga: Lga,
    services_by_code: dict[str, Service],
    source: DataSource,
) -> Facility:
    """Upsert one facility plus its services, contacts, and schedules."""
    # Fields shared by every demo row: always demo, always from the demo source.
    demo_fields = {"is_demo": True, "source_id": source.id}

    facility = upsert(
        session,
        report,
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
    )

    for offered in data["services"]:
        upsert(
            session,
            report,
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
        upsert(
            session,
            report,
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
        is_closed = schedule.get("is_closed", False)
        for day in schedule["days"]:  # one row per day of the week
            upsert(
                session,
                report,
                ServiceSchedule,
                lookup={
                    "facility_id": facility.id,
                    "service_id": service.id if service else None,
                    "day_of_week": day,
                },
                values={
                    "is_closed": is_closed,
                    "opens_at": _time_or_none(schedule.get("opens_at")),
                    "closes_at": _time_or_none(schedule.get("closes_at")),
                    "verification_status": demo_data.REPORTED,
                    **demo_fields,
                },
            )

    return facility


def run_seed(session: Session) -> SeedReport:
    """Upsert all demo data using the given session. The caller decides when to commit."""
    report = SeedReport()

    source = upsert(
        session,
        report,
        DataSource,
        lookup={"name": demo_data.DEMO_SOURCE["name"]},
        values={
            "source_type": demo_data.DEMO_SOURCE["source_type"],
            "source_url": demo_data.DEMO_SOURCE["source_url"],
        },
    )
    state = upsert(
        session,
        report,
        State,
        lookup={"code": demo_data.STATE["code"]},
        values={"name": demo_data.STATE["name"]},
    )
    lgas_by_name = {
        name: upsert(session, report, Lga, lookup={"state_id": state.id, "name": name}, values={})
        for name in demo_data.LGA_NAMES
    }
    services_by_code = {
        item["code"]: upsert(
            session,
            report,
            Service,
            lookup={"code": item["code"]},
            values={"name": item["name"], "description": item["description"]},
        )
        for item in demo_data.SERVICES
    }

    pilot_lga = lgas_by_name[demo_data.PILOT_LGA_NAME]
    for facility_data in demo_data.FACILITIES:
        seed_facility(session, report, facility_data, pilot_lga, services_by_code, source)

    return report


def main() -> None:
    settings = get_settings()
    # Fictional data must never end up in a production database.
    if settings.app_env == "production":
        sys.exit("Refusing to seed demo data: APP_ENV is 'production'.")

    # Each row is a lookup + a write, i.e. two network round trips to the database. Simple and
    # easy to follow, but slow on a far-away database (~1 minute for ~80 rows).
    print("Seeding demo data (about a minute on a remote database)...")
    # session.begin() commits at the end of the block, or rolls EVERYTHING back on any error,
    # so a failed run never leaves half the demo data behind.
    with Session(get_engine()) as session, session.begin():
        report = run_seed(session)

    tables = sorted(set(report.created) | set(report.updated))
    print(f"\n{'table':<22}{'created':>9}{'updated':>9}")
    for table in tables:
        print(f"{table:<22}{report.created[table]:>9}{report.updated[table]:>9}")
    print("\nDone. All rows are marked is_demo = true and none are verified.")


if __name__ == "__main__":
    main()
