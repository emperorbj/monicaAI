"""Safety checks on the demo data itself (no database needed).

These protect real people: if someone edits demo_data.py and adds a real-looking phone
number, email, or name, or marks something verified, these tests fail.
"""

import re

from app.models.enums import VerificationStatus
from seed import demo_data

E164_PATTERN = re.compile(r"^\+[1-9][0-9]{6,14}$")
ALL_CONTACTS = [contact for f in demo_data.FACILITIES for contact in f["contacts"]]
SERVICE_CODES = {service["code"] for service in demo_data.SERVICES}


def test_facility_names_say_demo() -> None:
    for facility in demo_data.FACILITIES:
        assert "Demo" in facility["name"], facility["name"]


def test_contact_names_say_demo() -> None:
    for contact in ALL_CONTACTS:
        assert "(Demo)" in contact["full_name"], contact["full_name"]


def test_demo_phone_numbers_are_unreachable_fakes() -> None:
    for contact in ALL_CONTACTS:
        if contact["phone"] is not None:
            assert E164_PATTERN.match(contact["phone"]), contact["phone"]
            # +234 followed by 000 is never a real Nigerian number.
            assert contact["phone"].startswith("+234000"), contact["phone"]


def test_demo_emails_use_the_reserved_example_domain() -> None:
    for contact in ALL_CONTACTS:
        if contact["email"] is not None:
            assert contact["email"].endswith("@example.org"), contact["email"]


def test_every_contact_is_reachable() -> None:
    for contact in ALL_CONTACTS:
        assert contact["phone"] or contact["email"], contact["full_name"]


def test_nothing_is_marked_verified() -> None:
    statuses = [f["verification_status"] for f in demo_data.FACILITIES]
    statuses += [s["status"] for f in demo_data.FACILITIES for s in f["services"]]
    statuses += [c["status"] for c in ALL_CONTACTS]

    assert VerificationStatus.VERIFIED not in statuses


def test_every_referenced_service_code_exists() -> None:
    for facility in demo_data.FACILITIES:
        referenced = {s["code"] for s in facility["services"]}
        referenced |= {c["service_code"] for c in facility["contacts"] if c["service_code"]}
        referenced |= {s["service_code"] for s in facility["schedules"] if s["service_code"]}
        assert referenced <= SERVICE_CODES, facility["name"]


def test_at_most_one_primary_contact_per_facility_and_service() -> None:
    for facility in demo_data.FACILITIES:
        primary_keys = [c["service_code"] for c in facility["contacts"] if c["is_primary"]]
        assert len(primary_keys) == len(set(primary_keys)), facility["name"]


def test_tricky_cases_are_present_for_later_steps() -> None:
    facilities = demo_data.FACILITIES

    assert any(f["latitude"] is None for f in facilities), "need a facility without coordinates"
    assert any(not f["contacts"] for f in facilities), "need a facility without contacts"
    assert any(c["service_code"] for f in facilities for c in f["contacts"]), (
        "need a service-specific contact"
    )
    assert any(
        s["availability"] == demo_data.UNAVAILABLE for f in facilities for s in f["services"]
    ), "need a temporarily unavailable service"
    # An LGA with no facilities, for the "no results" case.
    assert len(demo_data.LGA_NAMES) > 1
