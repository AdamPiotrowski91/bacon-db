from . import table as dbt

# region Helpers

type TablesDef = dict[str, dbt.TableHandler]


class DatabaseError(RuntimeError):
    """TODO"""


# region Implementation


class Database:
    """TODO"""

    def __init__(self, **tables: dbt.TableHandler) -> None:
        """TODO"""

        if not tables:
            raise DatabaseError("Cannot define Database without any Tables.")

        if any(not isinstance(t, dbt.TableHandler) for t in tables.values()):
            raise DatabaseError(
                "Some provided Table Handler references are not actual Table Handlers."
            )

        self._tables: TablesDef = tables

    def __getitem__(self, key):
        if key is None:
            return self

        return self._tables[key]

    def __getattr__(self, name):
        if name is None:
            return self

        return self._tables[name]
