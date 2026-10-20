"""Federal Capital Territory, Abuja (North Central). Gwagwalada has no facilities."""

from seed.demo_data.common import (
    AVAILABLE,
    CHC,
    HEALTH_POST,
    OUTDATED,
    PHC,
    REPORTED,
    UNKNOWN,
    WEEKDAYS,
    contact,
    facility,
    hours,
    offers,
)

STATE = {
    "name": "Federal Capital Territory",
    "code": "FC",
    "lgas": [
        {
            "name": "Abuja Municipal",
            "facilities": [
                facility(
                    "Demo Unity Gardens Primary Health Centre",
                    PHC,
                    "Plot 0, Example Crescent, Abuja Municipal (fictional address)",
                    ("9.057900", "7.495100"),
                    REPORTED,
                    services=[
                        offers("antenatal_care"),
                        offers("childhood_immunisation"),
                        offers("malaria_testing"),
                        offers("family_planning"),
                        offers("nutrition_services", AVAILABLE, UNKNOWN),
                    ],
                    contacts=[
                        contact(
                            "Hauwa Template (Demo)",
                            "Officer-in-Charge",
                            phone="+2340000000011",
                            email="unitygardens.phc@example.org",
                            primary=True,
                        ),
                        contact(
                            "Ifeoma Sketch (Demo)",
                            "Antenatal Clinic Lead",
                            phone="+2340000000012",
                            primary=True,
                            service_code="antenatal_care",
                        ),
                    ],
                    schedules=[
                        hours(WEEKDAYS, "08:00", "16:00"),
                        hours([1, 3], "09:00", "12:00", service_code="antenatal_care"),
                    ],
                ),
                facility(
                    "Demo Capital Comprehensive Health Centre",
                    CHC,
                    "Sample Way, Abuja Municipal (fictional address)",
                    ("9.072000", "7.480000"),
                    OUTDATED,  # everything here needs rechecking
                    services=[
                        offers("hiv_testing", AVAILABLE, OUTDATED),
                        offers("tuberculosis_screening", AVAILABLE, OUTDATED),
                        offers("general_outpatient", AVAILABLE, OUTDATED),
                    ],
                    contacts=[
                        contact(
                            "Daniel Placeholder (Demo)",
                            "Officer-in-Charge",
                            phone="+2340000000013",
                            primary=True,
                            status=OUTDATED,
                        ),
                    ],
                    schedules=[hours(WEEKDAYS, "08:00", "17:00")],
                ),
            ],
        },
        {
            "name": "Bwari",
            "facilities": [
                facility(
                    "Demo Hillside Health Post",
                    HEALTH_POST,
                    "Hillside Road, Bwari (fictional address)",
                    ("9.283300", "7.383300"),
                    UNKNOWN,
                    services=[
                        offers("malaria_testing"),
                        offers("childhood_immunisation"),
                    ],
                    contacts=[
                        contact(
                            "Grace Example (Demo)",
                            "Health Post Coordinator",
                            phone="+2340000000014",
                            primary=True,
                            status=UNKNOWN,
                        ),
                    ],
                    # No hours on record.
                ),
            ],
        },
        {"name": "Gwagwalada", "facilities": []},
    ],
}
