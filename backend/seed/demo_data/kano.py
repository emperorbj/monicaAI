"""Kano State (North West). The Tarauni facility has no coordinates."""

from seed.demo_data.common import (
    AVAILABLE,
    CHC,
    HEALTH_POST,
    PHC,
    REPORTED,
    SATURDAY,
    UNKNOWN,
    UNKNOWN_AVAILABILITY,
    WEEKDAYS,
    contact,
    facility,
    hours,
    offers,
)

STATE = {
    "name": "Kano",
    "code": "KN",
    "lgas": [
        {
            "name": "Kano Municipal",
            "facilities": [
                facility(
                    "Demo Crescent Primary Health Centre",
                    PHC,
                    "5 Example Road, Kano Municipal (fictional address)",
                    ("12.000000", "8.516700"),
                    REPORTED,
                    services=[
                        offers("antenatal_care"),
                        offers("postnatal_care"),
                        offers("childhood_immunisation"),
                        offers("nutrition_services"),
                        offers("family_planning", UNKNOWN_AVAILABILITY, UNKNOWN),
                    ],
                    contacts=[
                        contact(
                            "Musa Placeholder (Demo)",
                            "Officer-in-Charge",
                            phone="+2340000000015",
                            email="crescent.phc@example.org",
                            primary=True,
                        ),
                        contact(
                            "Aminu Dummy (Demo)",
                            "Nutrition Unit Lead",
                            phone="+2340000000016",
                            primary=True,
                            service_code="nutrition_services",
                        ),
                    ],
                    schedules=[
                        hours(WEEKDAYS, "08:00", "16:00"),
                        hours([SATURDAY], "08:00", "12:00"),
                    ],
                ),
            ],
        },
        {
            "name": "Nassarawa",
            "facilities": [
                facility(
                    "Demo Greenfield Comprehensive Health Centre",
                    CHC,
                    "Greenfield Avenue, Nassarawa, Kano (fictional address)",
                    ("11.990000", "8.530000"),
                    REPORTED,
                    services=[
                        offers("antenatal_care"),
                        offers("delivery_services"),
                        offers("hiv_testing"),
                        offers("general_outpatient"),
                    ],
                    contacts=[
                        contact(
                            "Zainab Specimen (Demo)",
                            "Officer-in-Charge",
                            phone="+2340000000017",
                            email="greenfield.chc@example.org",
                            primary=True,
                        ),
                    ],
                    schedules=[hours(WEEKDAYS, "08:00", "17:00")],
                ),
            ],
        },
        {
            "name": "Tarauni",
            "facilities": [
                facility(
                    "Demo Sahel Health Post",
                    HEALTH_POST,
                    "Tarauni (exact address not on record)",
                    None,  # location unknown: no map link
                    UNKNOWN,
                    services=[
                        offers("malaria_testing", AVAILABLE, UNKNOWN),
                        offers("childhood_immunisation", UNKNOWN_AVAILABILITY, UNKNOWN),
                    ],
                    contacts=[
                        contact(
                            "Sahel Health Post Desk (Demo)",
                            "Reception",
                            phone="+2340000000018",
                            primary=True,
                            status=UNKNOWN,
                        ),
                    ],
                ),
            ],
        },
    ],
}
