"""Oyo State (South West). Ibadan North is the main pilot LGA that most tests use.

Ibadan North-West and Surulere have no facilities: the "no results" case. Surulere also
exists in Lagos, showing that LGA names are only unique within a state.
"""

from seed.demo_data.common import (
    AVAILABLE,
    CHC,
    EVERY_DAY,
    GENERAL_HOSPITAL,
    HEALTH_POST,
    OUTDATED,
    PHC,
    REPORTED,
    SATURDAY,
    SUNDAY,
    UNAVAILABLE,
    UNKNOWN,
    UNKNOWN_AVAILABILITY,
    WEEKDAYS,
    contact,
    facility,
    hours,
    offers,
)

STATE = {
    "name": "Oyo",
    "code": "OY",
    "lgas": [
        {
            "name": "Ibadan North",
            "facilities": [
                facility(
                    "Demo Sunrise Primary Health Centre",
                    PHC,
                    "12 Example Close, Ibadan North (fictional address)",
                    ("7.412300", "3.905600"),
                    REPORTED,
                    services=[
                        offers("antenatal_care"),
                        offers("childhood_immunisation"),
                        offers("malaria_testing", AVAILABLE, UNKNOWN),
                        offers("family_planning", UNKNOWN_AVAILABILITY, UNKNOWN),
                    ],
                    contacts=[
                        contact(
                            "Tunde Sample (Demo)",
                            "Officer-in-Charge",
                            phone="+2340000000001",
                            email="sunrise.phc@example.org",
                            primary=True,
                        ),
                        # Service-specific: shown instead of the general contact for antenatal.
                        contact(
                            "Ngozi Example (Demo)",
                            "Antenatal Clinic Lead",
                            phone="+2340000000002",
                            primary=True,
                            service_code="antenatal_care",
                        ),
                    ],
                    schedules=[
                        hours(WEEKDAYS, "08:00", "16:00"),
                        hours([SUNDAY], closed=True),
                        # Saturday has no row on purpose: hours unknown (not closed).
                        hours([2, 4], "09:00", "13:00", service_code="antenatal_care"),
                    ],
                ),
                facility(
                    "Demo Riverside Comprehensive Health Centre",
                    CHC,
                    "4 Sample Road, Ibadan North (fictional address)",
                    ("7.425800", "3.912400"),
                    REPORTED,
                    services=[
                        offers("antenatal_care"),
                        offers("postnatal_care"),
                        offers("childhood_immunisation", AVAILABLE, OUTDATED),
                        offers("hiv_testing"),
                        offers("general_outpatient"),
                    ],
                    contacts=[
                        contact(
                            "Aisha Placeholder (Demo)",
                            "Officer-in-Charge",
                            phone="+2340000000003",
                            email="riverside.chc@example.org",
                            primary=True,
                            status=OUTDATED,
                        ),
                        # Non-primary: the bot offers it on request.
                        contact(
                            "Riverside Front Desk (Demo)",
                            "Reception",
                            phone="+2340000000004",
                            status=UNKNOWN,
                        ),
                    ],
                    schedules=[hours([*WEEKDAYS, SATURDAY], "08:00", "18:00")],
                ),
                facility(
                    "Demo Hilltop Health Post",
                    HEALTH_POST,
                    "Hilltop Street, Ibadan North (fictional address)",
                    ("7.437100", "3.897200"),
                    UNKNOWN,
                    services=[
                        offers("malaria_testing"),
                        # Temporarily unavailable: shown, but last and clearly labelled.
                        offers("childhood_immunisation", UNAVAILABLE, REPORTED),
                    ],
                    contacts=[
                        # Email only, no phone.
                        contact(
                            "Emeka Test (Demo)",
                            "Health Post Coordinator",
                            email="hilltop.post@example.org",
                            primary=True,
                            status=UNKNOWN,
                        ),
                    ],
                    # No hours on record at all.
                ),
                facility(
                    "Demo Market Road Primary Health Centre",
                    PHC,
                    "Market Road, Ibadan North (fictional address)",
                    None,  # location unknown: no map link
                    UNKNOWN,
                    services=[
                        offers("family_planning"),
                        offers("antenatal_care", UNKNOWN_AVAILABILITY, UNKNOWN),
                    ],
                    contacts=[
                        contact(
                            "Funmi Fictional (Demo)",
                            "Officer-in-Charge",
                            phone="+2340000000005",
                            primary=True,
                        ),
                    ],
                    schedules=[hours(WEEKDAYS, "08:00", "15:00")],
                ),
                facility(
                    "Demo Garden Primary Health Centre",
                    PHC,
                    "Garden Avenue, Ibadan North (fictional address)",
                    ("7.418900", "3.921700"),
                    REPORTED,
                    services=[
                        offers("antenatal_care"),
                        offers("childhood_immunisation"),
                        offers("tuberculosis_screening", AVAILABLE, UNKNOWN),
                    ],
                    # No contact on record: the bot must say so instead of inventing one.
                    schedules=[hours(WEEKDAYS, "08:00", "16:00")],
                ),
                facility(
                    "Demo Ibadan North General Hospital",
                    GENERAL_HOSPITAL,
                    "1 Fictional Hospital Way, Ibadan North (fictional address)",
                    ("7.430500", "3.908800"),
                    REPORTED,
                    services=[
                        offers("antenatal_care"),
                        offers("postnatal_care"),
                        offers("malaria_testing"),
                        offers("hiv_testing"),
                        offers("tuberculosis_screening"),
                        offers("general_outpatient"),
                    ],
                    contacts=[
                        contact(
                            "Hospital Information Desk (Demo)",
                            "Information Desk",
                            phone="+2340000000006",
                            email="info.generalhospital@example.org",
                            primary=True,
                        ),
                    ],
                    # Open around the clock. 23:59 because closing must be after opening.
                    schedules=[hours(EVERY_DAY, "00:00", "23:59")],
                ),
            ],
        },
        {"name": "Ibadan North-West", "facilities": []},
        {"name": "Surulere", "facilities": []},
    ],
}
