import json
import pathlib as p

import pytest

from bacon_db.db import table as t

DEFAULT_COLS = {"col1": int, "col2": float}
DEFAULT_SORT_KEY = tuple(DEFAULT_COLS.keys())[0]


class TestTableHandler:
    # region Setup

    @classmethod
    def finally_cleanup(cls, path: p.Path) -> None:
        path.unlink(missing_ok=True)
        t.get_backup_path_from_path(path).unlink(missing_ok=True)

    # endregion

    # region Init

    def test_init_valid_nonexistent(self, temp_folder_path: p.Path):
        path = temp_folder_path / "db.json"

        assert not path.exists()

        # does not raise
        t.TableHandler(path, DEFAULT_COLS, DEFAULT_SORT_KEY)

        assert not path.exists()

        # does not raise
        t.TableHandler(path, DEFAULT_COLS, tuple(DEFAULT_COLS.keys()))

    def test_init_valid_existent(self, temp_folder_path: p.Path):
        path = temp_folder_path / "db.json"

        assert not path.exists()

        try:
            with open(path, "w") as file:
                json.dump([], file)

            # does not raise
            t.TableHandler(path, DEFAULT_COLS, DEFAULT_SORT_KEY)
        finally:
            self.finally_cleanup(path)

    def test_init_invalid(self, temp_folder_path: p.Path):
        path = temp_folder_path / "folder"

        assert not path.exists()

        try:
            path.mkdir()

            with pytest.raises(t.TableHandlerError):
                t.TableHandler(path, DEFAULT_COLS, DEFAULT_SORT_KEY)
        finally:
            path.rmdir()

    # endregion
