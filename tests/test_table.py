import json
import pathlib as p

import pytest

from bacon_db.db import table as t

DEFAULT_COLS = {"col1": int, "col2": str}
DEFAULT_SORT_KEY = tuple(DEFAULT_COLS.keys())[0]


def create_row_template(i: int) -> t.RowData:
    return {"col1": i * 10, "col2": f"test_{i}", "id": str(i)}


DEFAULT_DATA = [create_row_template(1), create_row_template(2)]


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

    # region Get Rows

    @pytest.mark.parametrize(
        "data,cols,sorts",
        [
            [DEFAULT_DATA, DEFAULT_COLS, DEFAULT_SORT_KEY],
            [[], DEFAULT_COLS, DEFAULT_SORT_KEY],
            [
                [{"a": 1, "b": 1.5, "c": "one", "id": "1"}],
                {"a": int, "b": float, "c": str},
                ("c", "b", "a"),
            ],
        ],
    )
    def test_table_get_valid(self, temp_file_generator, data, cols, sorts):
        with temp_file_generator(data, lambda: self.finally_cleanup(path)) as path:
            assert isinstance(path, p.Path)

            handler = t.TableHandler(path, cols, sorts)

            assert handler.get_rows() == data

    @pytest.mark.parametrize(
        "data,cols,sorts",
        [
            [DEFAULT_DATA, {"a": str}, DEFAULT_SORT_KEY],
            [DEFAULT_DATA, {"col1": str, "col2": float}, DEFAULT_SORT_KEY],
            [DEFAULT_DATA, DEFAULT_COLS, "not here"],
            [
                [{"a": 1, "b": 1.5, "c": "one", "id": "1"}],
                {"a": int, "c": str},
                ("c", "b", "a"),
            ],
        ],
    )
    def test_table_get_invalid(self, temp_file_generator, data, cols, sorts):
        with temp_file_generator(data, lambda: self.finally_cleanup(path)) as path:
            assert isinstance(path, p.Path)

            with pytest.raises(t.TableHandlerError):
                handler = t.TableHandler(path, cols, sorts)
                handler.get_rows()

    # endregion

    # region Insert Rows

    # endregion

    # region Update Rows

    # endregion

    # region Delete Rows

    # endregion
