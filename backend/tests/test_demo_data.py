"""Safety checks on the demo data itself (no database needed).

These protect real people: if someone edits the demo data and adds a real-looking phone
number, email, or name, or marks something verified, these tests fail.
"""

import re
from decimal import Decimal

from app.models.enums import VerificationStatus
from seed import demo_data

E164_PATTERN = re.compile(r"^\+[1-9][0-9]{6,14}$")
ALL_CONTACTS = [contact for f in demo_data.FACILITIES for contact in f["contacts"]]
SERVICE_CODES = {service["code"] for service in demo_data.SERVICES}

# Rough bounding box around Nigeria: catches swapped or mistyped coordinates.
NIGERIA_LATITUDE = (Decimal("4.0"), Decimal("14.0"))
NIGERIA_LONGITUDE = (Decimal("2.6"), Decimal("14.7"))


def test_seven_states_with_unique_names_and_codes() -> None:
    assert len(demo_data.STATES) == 7
    assert len({s["name"] for s in demo_data.STATES}) == 7
    assert len({s["code"] for s in demo_data.STATES}) == 7


def test_lga_names_are_unique_within_each_state() -> None:
    for state in demo_data.STATES:
        names = [lga["name"] for lga in state["lgas"]]
        assert len(names) == len(set(names)), state["name"]


def test_surulere_exists_in_two_states() -> None:
    # The real-world reason LGA names are only unique WITHIN a state.
    states_with_surulere = {
        state["code"]
        for state in demo_data.STATES
        for lga in state["lgas"]
        if lga["name"] == "Surulere"
    }
    assert states_with_surulere == {"OY", "LA"}


def test_facility_names_say_demo_and_are_unique() -> None:
    names = [facility["name"] for facility in demo_data.FACILITIES]
    assert all("Demo" in name for name in names)
    assert len(names) == len(set(names))


def test_coordinates_are_inside_nigeria() -> None:
    for facility in demo_data.FACILITIES:
        if facility["latitude"] is None:
            continue
        latitude, longitude = Decimal(facility["latitude"]), Decimal(facility["longitude"])
        assert NIGERIA_LATITUDE[0] <= latitude <= NIGERIA_LATITUDE[1], facility["name"]
        assert NIGERIA_LONGITUDE[0] <= longitude <= NIGERIA_LONGITUDE[1], facility["name"]


def test_contact_names_say_demo() -> None:
    for contact in ALL_CONTACTS:
        assert "(Demo)" in contact["full_name"], contact["full_name"]


def test_demo_phone_numbers_are_unreachable_unique_fakes() -> None:
    phones = [c["phone"] for c in ALL_CONTACTS if c["phone"] is not None]
    for phone in phones:
        assert E164_PATTERN.match(phone), phone
        # +234 followed by 000 is never a real Nigerian number.
        assert phone.startswith("+234000"), phone
    assert len(phones) == len(set(phones)), "two contacts share a phone number"


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


def test_every_state_has_at_least_one_facility() -> None:
    for state in demo_data.STATES:
        assert any(lga["facilities"] for lga in state["lgas"]), state["name"]


def test_tricky_cases_are_present_for_later_steps() -> None:
    facilities = demo_data.FACILITIES
    all_lgas = [lga for state in demo_data.STATES for lga in state["lgas"]]

    assert any(f["latitude"] is None for f in facilities), "need a facility without coordinates"
    assert any(not f["contacts"] for f in facilities), "need a facility without contacts"
    assert any(c["service_code"] for f in facilities for c in f["contacts"]), (
        "need a service-specific contact"
    )
    assert any(
        s["availability"] == demo_data.UNAVAILABLE for f in facilities for s in f["services"]
    ), "need a temporarily unavailable service"
    assert any(not lga["facilities"] for lga in all_lgas), "need an LGA with no facilities"
