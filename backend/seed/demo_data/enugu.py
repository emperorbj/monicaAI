"""Enugu State (South East). The Nsukka health post's only contact has email but no phone."""

from seed.demo_data.common import (
    AVAILABLE,
    CHC,
    HEALTH_POST,
    PHC,
    REPORTED,
    SUNDAY,
    UNKNOWN,
    WEEKDAYS,
    contact,
    facility,
    hours,
    offers,
)

STATE = {
    "name": "Enugu",
    "code": "EN",
    "lgas": [
        {
            "name": "Enugu North",
            "facilities": [
                facility(
                    "Demo Ridgeway Primary Health Centre",
                    PHC,
                    "9 Example Ridge, Enugu North (fictional address)",
                    ("6.458400", "7.510000"),
                    REPORTED,
                    services=[
                        offers("antenatal_care"),
                        offers("childhood_immunisation"),
                        offers("family_planning"),
                        offers("hiv_testing", AVAILABLE, UNKNOWN),
                    ],
                    contacts=[
                        contact(
                            "Chinedu Sample (Demo)",
                            "Officer-in-Charge",
                            phone="+2340000000021",
                            email="ridgeway.phc@example.org",
                            primary=True,
                        ),
                        contact(
                            "Ada Fictional (Demo)",
                            "Antenatal Clinic Lead",
                            phone="+2340000000022",
                            primary=True,
                            service_code="antenatal_care",
                        ),
                    ],
                    schedules=[
                        hours(WEEKDAYS, "08:00", "16:00"),
                        hours([SUNDAY], closed=True),
                    ],
                ),
            ],
        },
        {
            "name": "Enugu South",
            "facilities": [
                facility(
                    "Demo Valley Comprehensive Health Centre",
                    CHC,
                    "Valley Road, Enugu South (fictional address)",
                    ("6.420000", "7.490000"),
                    REPORTED,
                    services=[
                        offers("antenatal_care"),
                        offers("postnatal_care"),
                        offers("delivery_services"),
                        offers("general_outpatient"),
                    ],
                    contacts=[
                        contact(
                            "Obinna Example (Demo)",
                            "Officer-in-Charge",
                            phone="+2340000000023",
                            primary=True,
                        ),
                    ],
                    schedules=[hours(WEEKDAYS, "08:00", "17:00")],
                ),
            ],
        },
        {
            "name": "Nsukka",
            "facilities": [
                facility(
                    "Demo Orchard Health Post",
                    HEALTH_POST,
                    "Orchard Lane, Nsukka (fictional address)",
                    ("6.857000", "7.395000"),
                    UNKNOWN,
                    services=[
                        offers("malaria_testing"),
                        offers("tuberculosis_screening", AVAILABLE, UNKNOWN),
                    ],
                    contacts=[
                        contact(
                            "Nkechi Test (Demo)",
                            "Health Post Coordinator",
                            email="orchard.post@example.org",
                            primary=True,
                            status=UNKNOWN,
                        ),
                    ],
                ),
            ],
        },
    ],
}
