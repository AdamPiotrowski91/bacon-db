import json
import pathlib as p
import threading as th
from typing import Any, Self

# region Helpers

type RowData = dict[str, Any]
type DBData = list[RowData]


# TODO: consider that returned data is still a reference to cache and changes in-place may affect it
# TODO: potential race condition between checking for file existence and actually applying lock
# TODO: implement opt-in backup mechanics


class JSONHandlerError(RuntimeError):
    """Error Raised by `JSONHandler` class during runtime."""


# endregion

# region Implementation


class JSONHandler:
    def __init__(self, path: p.Path | str) -> None:
        self._path = p.Path(path).resolve().absolute()
        self._cache_raw: DBData | None = None

        # Locks
        self._lock_data = th.Lock()
        self._lock_cache = th.Lock()

    @property
    def _cache(self):
        with self._lock_cache:
            return self._cache_raw

    @_cache.setter
    def _cache(self, value: DBData | None):
        with self._lock_cache:
            self._cache_raw = value
            return self._cache_raw

    @classmethod
    def _assert_data(cls, data: Any) -> None:
        assert isinstance(c := data, list) and all(isinstance(elem, dict) for elem in c)

    def exists(self) -> bool:
        return self._path.exists()

    def read(self) -> DBData:
        """Read Data from `path` this handler was assigned to.

        Returns:
            list of dicts of data if exists

        Raises:
            `JSONHandlerError` if something unexpected happened
        """

        path = self._path

        if not path.exists():
            raise JSONHandlerError(f"JSON path '{path}' does not exist.")

        # if cache exists, no write requests were made yet so file is the same
        if (c := self._cache) is not None:
            return c

        try:
            with self._lock_data, open(path, "r") as file:
                self._cache = json.load(file)
        except OSError as err:
            raise JSONHandlerError(f"Could not access file '{path}'.") from err
        except json.JSONDecodeError as err:
            raise JSONHandlerError(f"File '{path}' is invalid.") from err
        except Exception as err:
            raise JSONHandlerError(
                f"Reading file '{path}' raised unexpectedly."
            ) from err

        self._assert_data(c := self._cache)
        return c

    def create(self) -> Self:
        """Create file under `path` assigned to this handler.

        Returns:
            `self` for chaining

        Raises:
            `JSONHandlerError` if something unexpected happened
        """

        path = self._path

        if path.exists():
            raise JSONHandlerError(f"JSON path '{path}' already exists.")

        with self._lock_data, open(path, "w") as f:
            json.dump([], f)

        return self

    def write(self, new_data: DBData) -> Self:
        """Write Data to `path` this handler was assigned to.

        Arguments:
            `new_data` (`Data`): new data to use for overwriting

        Returns:
            `self` for chaining

        Raises:
            `JSONHandlerError` if something unexpected happened.
            `AssertionError` if `new_data` is invalid.
        """

        path = self._path

        if not path.exists():
            raise JSONHandlerError(f"JSON path '{path}' does not exist.")

        self._assert_data(new_data)

        with self._lock_data, open(path, "w") as f:
            json.dump(new_data, f)
            self._cache = new_data

        return self


# endregion
