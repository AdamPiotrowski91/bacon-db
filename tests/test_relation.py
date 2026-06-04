import pathlib as p

import pytest

from bacon_db.db import relation as r
from bacon_db.db import table as t

from .test_table import finally_cleanup

# region Setup

SOURCE = {"a": 1, "b": "test", "id": "12345"}

# endregion

# region RelationRowData

class TestRelationRowData:
    def test_is_dict(self):
        data = r._RelationRowData(SOURCE)

        assert isinstance(data, dict)
        assert set(data.keys()) == set(SOURCE.keys())
        assert set(data.values()) == set(SOURCE.values())

    def test_can_access_data(self):
        data = r._RelationRowData(SOURCE)

        assert data["a"] == 1
        assert data["b"] == "test"
        assert "c" not in data
        assert data == SOURCE

    def test_stringify(self):
        data = r._RelationRowData(SOURCE)

        assert str(data) == data["id"]

# endregion

# region RelationHandler


class TestRelationHandler:
    def test_one_column_relation(self, temp_folder_path: p.Path):
        path_root = temp_folder_path / "root.json"
        path_sub = temp_folder_path / "sub.json"

        try:
            table_sub = t.TableHandler(path_sub, {"sc1": str}, "sc1")
            handler = t.TableHandler(
                path_root, {"col1": int, "col2": r.RelationHandler(table_sub)}, "col1"
            )

            assert handler.get_rows() == []

            table_sub.insert_rows({"sc1": "the value"})
            row_id = table_sub.get_rows()[0]["id"]

            handler.insert_rows({"col1": 10, "col2": row_id})

            new_table_sub = t.TableHandler(path_sub, {"sc1": str}, "sc1")
            new_handler = t.TableHandler(
                path_root, {"col1": int, "col2": r.RelationHandler(new_table_sub)}, "col1"
            )

            assert new_handler.get_rows() == handler.get_rows()

        finally:
            finally_cleanup(path_root)
            finally_cleanup(path_sub)

# endregion
