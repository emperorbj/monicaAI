"""All database models.

Importing a model here registers its table on Base.metadata. Alembic (Step 5) imports this
package to discover every table, so each new model must be added below.
"""

from app.models.base import Base
from app.models.location import Lga, State

__all__ = ["Base", "Lga", "State"]
