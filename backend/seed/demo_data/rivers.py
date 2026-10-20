"""Rivers State (South South). Includes a service-specific delivery unit lead."""

from seed.demo_data.common import (
    AVAILABLE,
    EVERY_DAY,
    GENERAL_HOSPITAL,
    HEALTH_POST,
    PHC,
    REPORTED,
    UNAVAILABLE,
    UNKNOWN,
    WEEKDAYS,
    contact,
    facility,
    hours,
    offers,
)

STATE = {
    "name": "Rivers",
    "code": "RI",
    "lgas": [
        {
            "name": "Port Harcourt",
            "facilities": [
                facility(
                    "Demo Waterside Primary Health Centre",
                    PHC,
                    "2 Example Wharf Road, Port Harcourt (fictional address)",
                    ("4.777400", "7.013400"),
                    REPORTED,
                    services=[
                        offers("antenatal_care"),
                        offers("childhood_immunisation"),
                        offers("malaria_testing"),
                        offers("delivery_services", AVAILABLE, UNKNOWN),
                    ],
                    contacts=[
                        contact(
                            "Ebiere Example (Demo)",
                            "Officer-in-Charge",
                            phone="+2340000000024",
                            email="waterside.phc@example.org",
                            primary=True,
                        ),
                        contact(
                            "Tamuno Specimen (Demo)",
                            "Delivery Unit Lead",
                            phone="+2340000000025",
                            primary=True,
                            service_code="delivery_services",
                        ),
                    ],
                    schedules=[hours(WEEKDAYS, "08:00", "16:00")],
                ),
                facility(
                    "Demo Mangrove General Hospital",
                    GENERAL_HOSPITAL,
                    "1 Fictional Creek Road, Port Harcourt (fictional address)",
                    ("4.790000", "7.020000"),
                    REPORTED,
                    services=[
                        offers("antenatal_care"),
                        offers("postnatal_care"),
                        offers("delivery_services"),
                        offers("malaria_testing"),
                        offers("hiv_testing"),
                        offers("general_outpatient"),
                    ],
                    contacts=[
                        contact(
                            "Mangrove Information Desk (Demo)",
                            "Information Desk",
                            phone="+2340000000026",
                            email="info.mangrove@example.org",
                            primary=True,
                        ),
                    ],
                    schedules=[hours(EVERY_DAY, "00:00", "23:59")],
                ),
            ],
        },
        {
            "name": "Obio/Akpor",
            "facilities": [
                facility(
                    "Demo Creekside Health Post",
                    HEALTH_POST,
                    "Creekside Street, Obio/Akpor (fictional address)",
                    ("4.850000", "7.000000"),
                    UNKNOWN,
                    services=[
                        offers("malaria_testing"),
                        offers("childhood_immunisation", UNAVAILABLE, REPORTED),
                    ],
                    contacts=[
                        contact(
                            "Boma Dummy (Demo)",
                            "Health Post Coordinator",
                            phone="+2340000000027",
                            primary=True,
                            status=UNKNOWN,
                        ),
                    ],
                    schedules=[hours(WEEKDAYS, "09:00", "15:00")],
                ),
            ],
        },
    ],
}
