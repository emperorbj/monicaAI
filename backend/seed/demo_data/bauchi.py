"""Bauchi State (North East). The Tafawa Balewa health post has no contact on record."""

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
    "name": "Bauchi",
    "code": "BA",
    "lgas": [
        {
            "name": "Bauchi",
            "facilities": [
                facility(
                    "Demo Rock View Primary Health Centre",
                    PHC,
                    "Example Hill Road, Bauchi (fictional address)",
                    ("10.315800", "9.844200"),
                    REPORTED,
                    services=[
                        offers("antenatal_care"),
                        offers("childhood_immunisation"),
                        offers("malaria_testing"),
                        offers("tuberculosis_screening", AVAILABLE, UNKNOWN),
                        offers("nutrition_services"),
                    ],
                    contacts=[
                        contact(
                            "Ibrahim Mock (Demo)",
                            "Officer-in-Charge",
                            phone="+2340000000019",
                            email="rockview.phc@example.org",
                            primary=True,
                        ),
                    ],
                    schedules=[hours(WEEKDAYS, "08:00", "16:00")],
                ),
                facility(
                    "Demo Acacia General Hospital",
                    GENERAL_HOSPITAL,
                    "1 Acacia Close, Bauchi (fictional address)",
                    ("10.300000", "9.830000"),
                    REPORTED,
                    services=[
                        offers("antenatal_care"),
                        offers("postnatal_care"),
                        offers("delivery_services"),
                        offers("hiv_testing"),
                        offers("tuberculosis_screening"),
                        offers("general_outpatient"),
                    ],
                    contacts=[
                        contact(
                            "Acacia Information Desk (Demo)",
                            "Information Desk",
                            phone="+2340000000020",
                            email="info.acacia@example.org",
                            primary=True,
                        ),
                    ],
                    schedules=[hours(EVERY_DAY, "00:00", "23:59")],
                ),
            ],
        },
        {
            "name": "Tafawa Balewa",
            "facilities": [
                facility(
                    "Demo Plateau Edge Health Post",
                    HEALTH_POST,
                    "Plateau Edge, Tafawa Balewa (fictional address)",
                    ("9.760000", "9.560000"),
                    UNKNOWN,
                    services=[
                        offers("malaria_testing"),
                        offers("childhood_immunisation", UNAVAILABLE, REPORTED),
                    ],
                    # No contact on record.
                ),
            ],
        },
    ],
}
