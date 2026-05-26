import pathlib as p
from dataclasses import dataclass

from .. import json as j
from ..json import DBData  # explicitly imported type
from ..utils import count_required_args

# region Helpers


type TableColumnsSetup = dict[str, type]

BACKUP_PREFIX = "_backup_"


def get_backup_path_from_path(path: p.Path) -> p.Path:
    """Creates backup path from a path to a file.

    Assumes the provided path is a file without asserting that.
    """
    return path.parent / f"{BACKUP_PREFIX}{path.name}"


@dataclass
class TableConfig:
    create_backup: bool = True


class TableHandlerError(RuntimeError):
    """Error Raised by `DatabaseHandler` class during runtime."""


# endregion

# region Implementation


class TableHandler:
    """Handler for each specific database file representing one raw data table."""

    def __init__(
        self,
        path: str | p.Path,
        columns: TableColumnsSetup,
        config: TableConfig | None = None,
    ) -> None:
        """
        Arguments:
            `path` (`str | Path`): path to a file the table should be saved in/
                If it does not exist, it will be created on first read or write.
            `columns` (`TableColumnsSetup`): a dictionary of keys being column
                names and values being python data type callables the values will
                be parsed into and from.
            `config` (`TableConfig`, optional): table handler configuration. A set
                of rules this handler will use for any actions. Will use default
                set of rules if not provided (see definition of `TableConfig` dataclass)
        """

        self._path = p.Path(path).resolve()
        self._columns = columns
        self._config = config or TableConfig()

        self._prevalidate()
        self._setup()

    def _setup(self) -> None:
        self._json_handler = j.JSONHandler(self._path)
        self._cache: DBData | None = None

        if self._config.create_backup and self._path.exists():
            backup_path = get_backup_path_from_path(self._path)
            self._path.copy(backup_path)

    def _prevalidate(self) -> None:
        try:
            assert self._path.is_file()

            for col_name, col_type in self._columns.items():
                assert isinstance(col_name, str) and col_name
                assert (
                    isinstance(col_type, type)
                    and callable(col_type)
                    and count_required_args(col_type) == 1
                )
        except Exception as err:
            raise TableHandlerError(
                f"`path` or `columns` setup is invalid for table '{self._path}'."
            ) from err

    def _create_if_needed(self) -> None:
        if not self._path.exists():
            self._json_handler.create()

    def read(self) -> DBData:
        """TODO"""

        if self._cache is None:
            self._create_if_needed()
            data = self._json_handler.read()
            self._parse(data)
            self._cache = data

        return self._cache

    def _parse(self, data: DBData) -> None:
        """Parses json data in-place."""

        try:
            for entry in data:
                for col, val in entry.items():
                    entry[col] = self._columns[col](val)
        except Exception as err:
            raise TableHandlerError(
                f"Could not parse data for table '{self._path}'"
            ) from err


# endregion
