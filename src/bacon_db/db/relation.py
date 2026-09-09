from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .table import DBRowData, TableHandler


# region Helpers


# TODO: consider weakref for table references


class RelationHandlerError(RuntimeError):
    """Error Raised by `RelationHandler` when relationship is not set up
    properly or cannot be applied properly.
    """


class RelationRowData(dict):
    """Helper class responsible for returning proper data."""

    def __init__(self, row_data: DBRowData | RelationRowData) -> None:
        """
        Arguments:
            `row_data` (`DBRowData | RelationRowData`): Either a valid Database
                Row or other `RelationRowData`
        """

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
    """Handler representing a type of column data being a relation with another table."""

    def __init__(self, table: TableHandler) -> None:
        """
        Arguments:
            `table` (`TableHandler`): A reference to the Table handling data for
                a column of IDs this relation column keeps.
        """

        self._table = table

    def __call__(self, row_id: str) -> RelationRowData:
        """
        Arguments:
            `row_id` (`str`): ID of the row from `table`

        Returns:
            Data representing actual Table Row the relational ID was referring to.
        """

        return RelationRowData(self._table.get_single_row(row_id))
