from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .table import TableHandler, DBRowData


# region Helpers


class RelationHandlerError(RuntimeError):
    """TODO"""


class RelationRowData(dict):
    """TODO"""

    def __init__(self, row_data: DBRowData | RelationRowData) -> None:
        """TODO"""
        if "id" not in row_data:
            raise RelationHandlerError(f"Row Data `{row_data}` does not have 'id' key.")

        self.__dict__ = row_data

        for k, v in row_data.items():
            self[k] = v

    def __eq__(self, value: Any) -> bool:
        if isinstance(value, str):
            return self["id"] == value  # ID equals

        return super().__eq__(value)

    def __str__(self) -> str:
        return self["id"]


# region Implementation


class RelationHandler:
    """TODO"""

    def __init__(self, table: TableHandler) -> None:
        """TODO"""
        self._table = table

    def __call__(self, row_id: str) -> RelationRowData:
        """TODO"""

        return RelationRowData(self._table.get_single_row(row_id))
