"""Fixed lists of allowed values, shared by models, API schemas, and the bot.

Each member's value (the lowercase string) is what gets stored in the database.
"""

from enum import StrEnum

from sqlalchemy import CheckConstraint, Enum


class VerificationStatus(StrEnum):
    """How much we trust a piece of information. Missing data is UNKNOWN, never "unavailable"."""

    VERIFIED = "verified"  # confirmed by an authorised source or review
    REPORTED = "reported"  # submitted but not independently checked
    UNKNOWN = "unknown"  # no reliable information
    OUTDATED = "outdated"  # was recorded before but needs rechecking


class AvailabilityStatus(StrEnum):
    """Whether a service is operating. Separate from how well that fact is verified."""

    AVAILABLE = "available"
    TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"
    UNKNOWN = "unknown"


class FacilityType(StrEnum):
    PRIMARY_HEALTH_CENTRE = "primary_health_centre"
    HEALTH_POST = "health_post"
    COMPREHENSIVE_HEALTH_CENTRE = "comprehensive_health_centre"
    GENERAL_HOSPITAL = "general_hospital"
    SPECIALIST_HOSPITAL = "specialist_hospital"
    FEDERAL_MEDICAL_CENTRE = "federal_medical_centre"
    TEACHING_HOSPITAL = "teaching_hospital"
    OTHER = "other"


class SourceType(StrEnum):
    """Where a record's information came from."""

    GOVERNMENT_REGISTRY = "government_registry"
    FACILITY_VISIT = "facility_visit"
    PHONE_VERIFICATION = "phone_verification"
    COMMUNITY_REPORT = "community_report"
    DEMO_SEED = "demo_seed"  # fictional data created by our seed script
    OTHER = "other"


class EntityType(StrEnum):
    """Which kind of record a verification_history row is about."""

    FACILITY = "facility"
    FACILITY_SERVICE = "facility_service"
    FACILITY_CONTACT = "facility_contact"
    SERVICE_SCHEDULE = "service_schedule"


def enum_column(enum_class: type[StrEnum]) -> Enum:
    """Column type for a StrEnum, stored as plain VARCHAR.

    native_enum=False avoids PostgreSQL's ENUM type, which is awkward to change in migrations.
    values_callable stores "verified" (the value) rather than "VERIFIED" (the Python name).
    The database-side rule is added separately with enum_check() (see below for why).
    """
    return Enum(
        enum_class,
        native_enum=False,
        create_constraint=False,
        length=50,
        values_callable=lambda members: [member.value for member in members],
        validate_strings=True,
    )


def enum_check(column_name: str, enum_class: type[StrEnum]) -> CheckConstraint:
    """Explicit CHECK that the column only holds the enum's values.

    Why not Enum(create_constraint=True)? Alembic autogenerate renders that implicit constraint
    twice, producing broken migrations. An explicit CheckConstraint is rendered exactly once,
    and naming it after the column (not the enum) keeps names unique even when one table has
    two columns of the same enum. Final name: ck_<table>_<column>_allowed.
    """
    allowed_values = ", ".join(f"'{member.value}'" for member in enum_class)
    return CheckConstraint(f"{column_name} IN ({allowed_values})", name=f"{column_name}_allowed")
