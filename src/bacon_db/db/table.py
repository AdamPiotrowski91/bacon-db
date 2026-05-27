import pathlib as p
import threading as th
from dataclasses import dataclass
from typing import Any, Callable, Self

from .. import json as j
from ..json import DBData, RowData  # explicitly imported types
from ..utils import count_required_args, unique_id

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
    """Handler for each specific database file representing one raw data table.

    Each row of data will have a unique ID column generated on creation.
    """

    def __init__(
        self,
        path: str | p.Path,
        columns: TableColumnsSetup,
        sort_keys: str | tuple[str, ...] | list[str],
        config: TableConfig | None = None,
    ) -> None:
        """
        Arguments:
            `path` (`str | Path`): path to a file the table should be saved in/
                If it does not exist, it will be created on first read or write.
            `columns` (`TableColumnsSetup`): a dictionary of keys being column
                names and values being python data type callables the values will
                be parsed into and from.
            `sort_key` (`str | list/tuple[str]`): either column name or iterable
                of column names to use to find values for sorting table rows.
            `config` (`TableConfig`, optional): table handler configuration. A set
                of rules this handler will use for any actions. Will use default
                set of rules if not provided (see definition of `TableConfig` dataclass)
        """

        self._path = p.Path(path).resolve()
        self._columns: TableColumnsSetup = {**columns, "id": str}
        self._sort_keys = (sort_keys,) if isinstance(sort_keys, str) else sort_keys
        self._config = config or TableConfig()

        self._prevalidate()
        self._setup()

    @property
    def _cache(self):
        with self._lock_cache:
            return self._cache_raw

    @_cache.setter
    def _cache(self, value: DBData | None):
        with self._lock_cache:
            self._cache_raw = value
            return self._cache_raw

    @property
    def _sorter(self) -> Callable[[RowData], tuple[Any, ...]]:
        return lambda row: tuple(row[key] for key in self._sort_keys)

    def _setup(self) -> None:
        self._lock_cache = th.Lock()
        self._json_handler = j.JSONHandler(self._path)
        self._cache_raw: DBData | None = None

        if self._config.create_backup and self._path.exists():
            backup_path = get_backup_path_from_path(self._path)
            self._path.copy(backup_path)

    def _prevalidate(self) -> None:
        try:
            assert not self._path.exists() or self._path.is_file()
            assert isinstance(sk := self._sort_keys, (list, tuple)) and all(
                isinstance(k, str) and k in self._columns for k in sk
            )

            for col_name, col_type in self._columns.items():
                assert isinstance(col_name, str) and col_name
                try:
                    ii = isinstance(col_type, type)
                    c = callable(col_type)
                    s = count_required_args(col_type) <= 1

                    assert ii and c and s, f"{ii=} {c=} {s=}"
                except ValueError as err:
                    if "no signature found for builtin type" in str(err):
                        continue
                    raise
        except Exception as err:
            raise TableHandlerError(
                f"Setup is invalid for table '{self._path}'."
            ) from err

    def _create_file_if_needed(self) -> None:
        if not self._path.exists():
            self._json_handler.create()

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

    def _unparse(self, row_data: RowData) -> RowData:
        """Unparses data without touching the original data and returns unparsed.

        Arguments:
            `data` (`RowData`): parsed data for a table row. Will be validated
                before approval into database.

        Returns:
            Unparsed `DBdata`.

        Raises:
            `TableHandlerError` if the data is invalid or something unexpected happens.
        """

        # validate
        try:
            for col_name, col_val in row_data.items():
                assert isinstance(col_val, self._columns[col_name])
        except Exception as err:
            raise TableHandlerError("Could not validate `row_data`.") from err

        ret: RowData = {}

        try:
            for col_name, col_val in row_data.items():
                ret[col_name] = str(col_val)
        except Exception as err:
            raise TableHandlerError("Could not unparse `row_data`.") from err

        return ret

    def read(self) -> DBData:
        """TODO"""

        ret = self._cache

        if ret is None:
            self._create_file_if_needed()
            ret = self._json_handler.read()
            self._parse(ret)
            ret.sort(key=self._sorter)
            self._cache = ret

        return ret

    def insert(self, *rows_data: RowData) -> Self:
        """TODO"""

        if not rows_data:
            return self  # noop

        new_db_data: DBData = sorted(
            [self._unparse({**row, "id": unique_id()}) for row in rows_data]
            + [self._unparse(row) for row in self.read()],
            key=self._sorter,
        )

        self._json_handler.write(new_db_data)
        self._cache = None

        return self


# endregion
