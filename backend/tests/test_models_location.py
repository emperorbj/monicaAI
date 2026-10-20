"""Tests for the State and Lga models.

These inspect the table definitions only (no database), so they run instantly and offline.
They prove the rules we rely on are really declared, before Alembic turns them into SQL.
"""

from sqlalchemy import UniqueConstraint

from app.models import Base, Lga, State


def _unique_column_sets(table) -> set[tuple[str, ...]]:
    """Every group of columns that has a unique constraint on this table."""
    return {
        tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }


def test_both_tables_are_registered_on_the_metadata() -> None:
    assert {"states", "lgas"} <= set(Base.metadata.tables)


def test_state_name_and_code_are_unique() -> None:
    unique_sets = _unique_column_sets(State.__table__)

    assert ("name",) in unique_sets
    assert ("code",) in unique_sets


def test_lga_name_is_unique_per_state_not_nationally() -> None:
    unique_sets = _unique_column_sets(Lga.__table__)

    assert ("state_id", "name") in unique_sets
    assert ("name",) not in unique_sets  # Surulere exists in Lagos AND Oyo


def test_lga_points_to_state_and_blocks_deleting_a_used_state() -> None:
    (foreign_key,) = Lga.__table__.c.state_id.foreign_keys

    assert foreign_key.column is State.__table__.c.id
    assert foreign_key.ondelete == "RESTRICT"


def test_lga_state_id_is_indexed() -> None:
    assert Lga.__table__.c.state_id.index is True


def test_constraint_names_follow_the_naming_convention() -> None:
    names = {constraint.name for constraint in Lga.__table__.constraints}

    assert "uq_lgas_state_id_name" in names
    assert "fk_lgas_state_id_states" in names


def test_relationship_links_both_directions() -> None:
    oyo = State(name="Oyo", code="OY")
    ibadan_north = Lga(name="Ibadan North", state=oyo)

    # Setting one side updates the other in Python, before anything touches the database.
    assert ibadan_north in oyo.lgas
