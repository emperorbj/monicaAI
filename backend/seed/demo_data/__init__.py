"""FICTIONAL demonstration data: 7 states (one per geopolitical zone, plus Lagos).

Only the state, LGA, and service names are real. Everything else is invented:
- Facility names contain "Demo"; coordinates are illustrative points inside each LGA.
- People have obviously fictional surnames and "(Demo)" in their name.
- Phone numbers use +234 000..., a range Nigerian numbers never use, so nobody can be called.
- Emails use example.org, a domain reserved for examples that never reaches a real inbox.
- Nothing is ever "verified". (The database rejects verified demo data anyway.)

To add a state: create a new file like lagos.py with a STATE dictionary and add it to STATES.
"""

from seed.demo_data import bauchi, enugu, fct, kano, lagos, oyo, rivers
from seed.demo_data.common import DEMO_SOURCE, SERVICES, UNAVAILABLE

STATES = [
    oyo.STATE,  # South West (main pilot)
    lagos.STATE,  # South West (largest city)
    fct.STATE,  # North Central
    kano.STATE,  # North West
    bauchi.STATE,  # North East
    enugu.STATE,  # South East
    rivers.STATE,  # South South
]

# The pilot LGA that most search tests focus on.
PILOT_STATE_CODE = "OY"
PILOT_LGA_NAME = "Ibadan North"

# Flat list of every facility in every state: handy for safety tests.
FACILITIES = [
    facility_data
    for state in STATES
    for lga in state["lgas"]
    for facility_data in lga["facilities"]
]

__all__ = [
    "DEMO_SOURCE",
    "FACILITIES",
    "PILOT_LGA_NAME",
    "PILOT_STATE_CODE",
    "SERVICES",
    "STATES",
    "UNAVAILABLE",
]
