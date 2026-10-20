"""All database models.

Importing a model here registers its table on Base.metadata. Alembic (Step 5) imports this
package to discover every table, so each new model must be added below.
"""

from app.models.base import Base
from app.models.catalog import DataSource, Service
from app.models.contact import FacilityContact
from app.models.facility import Facility
from app.models.location import Lga, State
from app.models.offering import FacilityService, ServiceSchedule
from app.models.verification import VerificationHistory

__all__ = [
    "Base",
    "DataSource",
    "Facility",
    "FacilityContact",
    "FacilityService",
    "Lga",
    "Service",
    "ServiceSchedule",
    "State",
    "VerificationHistory",
]
