from . import table as dbt

# region Helpers

type TablesDef = dict[str, dbt.TableHandler]


class DatabaseError(RuntimeError):
    """Error Raised by `Database` when setup is incorrect and references are invalid."""


# region Implementation


class Database:
    """Helper class representing one-point-access to all relevant tables and
    relations in a database setup."""

    def __init__(self, **tables: dbt.TableHandler) -> None:
        """
        Arguments:
            `**tables` (`TableHandler kwargs`): dictionary of table handlers
                with named references to them
        """

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
