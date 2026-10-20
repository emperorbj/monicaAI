"""Lagos State (South West). Surulere here shares its name with an LGA in Oyo."""

from seed.demo_data.common import (
    AVAILABLE,
    CHC,
    EVERY_DAY,
    GENERAL_HOSPITAL,
    HEALTH_POST,
    PHC,
    REPORTED,
    SATURDAY,
    UNAVAILABLE,
    UNKNOWN,
    WEEKDAYS,
    contact,
    facility,
    hours,
    offers,
)

STATE = {
    "name": "Lagos",
    "code": "LA",
    "lgas": [
        {
            "name": "Ikeja",
            "facilities": [
                facility(
                    "Demo Lagoon View Primary Health Centre",
                    PHC,
                    "7 Example Street, Ikeja (fictional address)",
                    ("6.601800", "3.351500"),
                    REPORTED,
                    services=[
                        offers("antenatal_care"),
                        offers("childhood_immunisation"),
                        offers("family_planning"),
                        offers("delivery_services", AVAILABLE, UNKNOWN),
                    ],
                    contacts=[
                        contact(
                            "Kemi Specimen (Demo)",
                            "Officer-in-Charge",
                            phone="+2340000000007",
                            email="lagoonview.phc@example.org",
                            primary=True,
                        ),
                        contact(
                            "Bisi Mock (Demo)",
                            "Immunisation Unit Lead",
                            phone="+2340000000008",
                            primary=True,
                            service_code="childhood_immunisation",
                        ),
                    ],
                    schedules=[
                        hours(WEEKDAYS, "08:00", "16:00"),
                        hours([SATURDAY], "09:00", "13:00"),
                    ],
                ),
                facility(
                    "Demo Cedar Court Comprehensive Health Centre",
                    CHC,
                    "22 Sample Avenue, Ikeja (fictional address)",
                    ("6.594000", "3.342000"),
                    REPORTED,
                    services=[
                        offers("hiv_testing"),
                        offers("tuberculosis_screening"),
                        offers("malaria_testing"),
                        offers("general_outpatient"),
                    ],
                    contacts=[
                        contact(
                            "Cedar Court Front Desk (Demo)",
                            "Reception",
                            phone="+2340000000009",
                            email="cedarcourt.chc@example.org",
                            primary=True,
                        ),
                    ],
                    schedules=[hours(WEEKDAYS, "08:00", "18:00")],
                ),
            ],
        },
        {
            "name": "Surulere",
            "facilities": [
                facility(
                    "Demo Bluebell Health Post",
                    HEALTH_POST,
                    "Bluebell Lane, Surulere, Lagos (fictional address)",
                    ("6.499900", "3.354000"),
                    UNKNOWN,
                    services=[
                        offers("malaria_testing"),
                        offers("childhood_immunisation", UNAVAILABLE, REPORTED),
                    ],
                    contacts=[
                        contact(
                            "Yemi Dummy (Demo)",
                            "Health Post Coordinator",
                            email="bluebell.post@example.org",
                            primary=True,
                            status=UNKNOWN,
                        ),
                    ],
                ),
            ],
        },
        {
            "name": "Eti-Osa",
            "facilities": [
                facility(
                    "Demo Seabreeze General Hospital",
                    GENERAL_HOSPITAL,
                    "3 Fictional Shore Road, Eti-Osa (fictional address)",
                    ("6.459000", "3.601500"),
                    REPORTED,
                    services=[
                        offers("antenatal_care"),
                        offers("postnatal_care"),
                        offers("delivery_services"),
                        offers("hiv_testing"),
                        offers("general_outpatient"),
                    ],
                    contacts=[
                        contact(
                            "Seabreeze Information Desk (Demo)",
                            "Information Desk",
                            phone="+2340000000010",
                            email="info.seabreeze@example.org",
                            primary=True,
                        ),
                    ],
                    schedules=[hours(EVERY_DAY, "00:00", "23:59")],
                ),
            ],
        },
    ],
}
