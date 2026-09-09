import contextlib
import json
import pathlib as p

import pytest

from bacon_db.db import table as t

# region Setup

DEFAULT_COLS = {"col1": int, "col2": str}
DEFAULT_SORT_KEY = tuple(DEFAULT_COLS.keys())[0]


def create_row_template(i: int) -> t.DBRowData:
    return {"col1": i * 10, "col2": f"test_{i}", "id": str(i)}


DEFAULT_DATA = [create_row_template(1), create_row_template(2)]


def finally_cleanup(path: p.Path) -> None:
    path.unlink(missing_ok=True)
    t.get_backup_path_from_path(path).unlink(missing_ok=True)


class TestTableHandler:

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
            finally_cleanup(path)

    def test_init_invalid(self, temp_folder_path: p.Path):
        path = temp_folder_path / "folder"

        assert not path.exists()

        try:
            path.mkdir()

            with pytest.raises(t.TableHandlerError):
                t.TableHandler(path, DEFAULT_COLS, DEFAULT_SORT_KEY)
        finally:
            path.rmdir()

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
        with temp_file_generator(data, lambda: finally_cleanup(path)) as path:
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
        with temp_file_generator(data, lambda: finally_cleanup(path)) as path:
            assert isinstance(path, p.Path)

            with pytest.raises(t.TableHandlerError):  # NOSONAR
                handler = t.TableHandler(path, cols, sorts)
                handler.get_rows()

    def test_table_get_single_row(self, temp_file_generator):
        with temp_file_generator(DEFAULT_DATA, lambda: finally_cleanup(path)) as path:
            assert isinstance(path, p.Path)

            handler = t.TableHandler(path, DEFAULT_COLS, DEFAULT_SORT_KEY)

            data = create_row_template(2)
            assert handler.get_single_row(data["id"]) == data

    # region Insert Rows

    def test_table_insert_can_without_setup(
        self, temp_folder_path: p.Path, mocked_unique_id_get_all
    ):
        path = temp_folder_path / "db.json"

        try:
            assert not path.exists()

            handler = t.TableHandler(path, DEFAULT_COLS, DEFAULT_SORT_KEY)
            # did not raise
            handler.insert_rows({"col1": 69, "col2": "wow"})
            ids = mocked_unique_id_get_all()

            assert handler.get_rows() == [{"col1": 69, "col2": "wow", "id": ids[-1]}]
        finally:
            finally_cleanup(path)

    @pytest.mark.parametrize(
        "new_data",
        [
            [],
            [{"col1": 69, "col2": "wow"}],
            [{"col1": 69, "col2": "wow"}, {"col1": 80, "col2": "extra"}],
            [{"col1": 69, "col2": "wow"}, {"col1": 69, "col2": "wow"}],  # allows dups
        ],
    )
    def test_table_insert_valid(
        self, temp_file_generator, mocked_unique_id_get_all, new_data
    ):
        with temp_file_generator(DEFAULT_DATA, lambda: finally_cleanup(path)) as path:
            assert isinstance(path, p.Path)

            handler = t.TableHandler(path, DEFAULT_COLS, DEFAULT_SORT_KEY)
            data = handler.get_rows()

            handler.insert_rows(*new_data)

            ids = mocked_unique_id_get_all()
            new_data = [
                {**row, "id": id} for id, row in zip(ids, new_data, strict=True)
            ]

            final_data = handler.get_rows()

            # old data does not contain new rows
            assert all(
                all(row != old_row for row in new_data) for old_row in data
            ), f"{data=} | {new_data=}"
            # final data contain new rows exactly once each
            assert all(
                len([row for row in final_data if row == new_row]) == 1
                for new_row in new_data
            ), f"{final_data=} | {new_data=}"

    @pytest.mark.parametrize(
        "new_data",
        [
            [{"col1": "invalid type", "col2": "wow"}],
            [{"col1": 69}],  # not all cols
            [{"col1": "invalid type", "col2": "wow", "col3": "wut?"}],  # too much cols
            [{"col1": 70}, {"col1": 69, "col2": "wow"}],  # one valid
            [{"col1": 69, "col2": "wow"}, {"col1": 70}],  # one valid (reordered)
        ],
    )
    def test_table_insert_invalid(self, temp_file_generator, new_data):
        with temp_file_generator(DEFAULT_DATA, lambda: finally_cleanup(path)) as path:
            assert isinstance(path, p.Path)

            handler = t.TableHandler(path, DEFAULT_COLS, DEFAULT_SORT_KEY)
            # does not raise
            handler.get_rows()

            with contextlib.suppress(t.TableHandlerError):
                handler.insert_rows(*new_data)

    # region Update Rows

    @pytest.mark.parametrize(
        "new_data",
        [
            [],
            [{"id": create_row_template(1)["id"], "col1": 50, "col2": "nope"}],  # full
            [{"id": create_row_template(1)["id"], "col1": 50}],  # partial
            [
                {"id": create_row_template(1)["id"], "col1": 50, "col2": "nope"},
                {"id": create_row_template(2)["id"], "col1": 100, "col2": "yay"},
            ],  # full, all
            [
                {"id": create_row_template(1)["id"], "col1": 50},
                {"id": create_row_template(2)["id"], "col1": 100},
            ],  # partial, all
            [
                {"id": create_row_template(1)["id"], "col1": 50, "col2": "nope"},
                {"id": create_row_template(2)["id"], "col1": 100},
            ],  # mixed
        ],
    )
    def test_table_update_valid(self, temp_file_generator, new_data):
        with temp_file_generator(DEFAULT_DATA, lambda: finally_cleanup(path)) as path:
            assert isinstance(path, p.Path)

            handler = t.TableHandler(path, DEFAULT_COLS, DEFAULT_SORT_KEY)
            old_data = handler.get_rows()
            all_ids = handler._get_ids(old_data)

            handler.update_rows(*new_data)

            ids = handler._get_ids(new_data)
            assert all(id in all_ids for id in ids)

            for updates in new_data:
                indexing = handler._get_indexing(old_data)
                idx = indexing[updates["id"]]
                record = old_data[idx]
                assert all(
                    g := (
                        record.get(key) != val
                        for key, val in updates.items()
                        if key != "id"
                    )
                ), f"{list(g)=} | {updates=} | {old_data=} | {record=}"

            final_data = handler.get_rows()
            for updates in new_data:
                indexing = handler._get_indexing(final_data)
                idx = indexing[updates["id"]]
                record = final_data[idx]
                assert all(
                    g := (record[key] == val for key, val in updates.items())
                ), f"{list(g)=} | {updates=} | {final_data=} | {record=}"

    @pytest.mark.parametrize(
        "new_data",
        [
            [{"id": "not found", "col1": 69, "col2": "nothing"}],
            [
                {"id": create_row_template(1)["id"], "col1": 50, "col2": "nope"},
                {"id": "not found", "col1": 69, "col2": "nothing"},
            ],
            [{}],
        ],
    )
    def test_table_update_invalid(self, temp_file_generator, new_data):
        with temp_file_generator(DEFAULT_DATA, lambda: finally_cleanup(path)) as path:
            assert isinstance(path, p.Path)

            handler = t.TableHandler(path, DEFAULT_COLS, DEFAULT_SORT_KEY)
            # did not raise
            handler.get_rows()

            with pytest.raises(t.TableHandlerError):
                handler.update_rows(*new_data)

    def test_table_update_invalid_aba(self, temp_file_generator):
        with temp_file_generator(DEFAULT_DATA, lambda: finally_cleanup(path)) as path:
            assert isinstance(path, p.Path)

            handler = t.TableHandler(path, DEFAULT_COLS, DEFAULT_SORT_KEY)
            old_data = handler.get_rows()

            with pytest.raises(t.TableHandlerError):  # NOSONAR
                handler.update_rows(
                    {**create_row_template(1), "col1": 69}, {"id": "invalid"}
                )

            new_data = handler.get_rows()
            assert old_data == new_data

    # region Delete Rows

    @pytest.mark.parametrize(
        "delete_data",
        [
            [],
            [create_row_template(1)["id"]],
            [create_row_template(1)],
            [create_row_template(1)["id"], create_row_template(2)["id"]],
            [create_row_template(1), create_row_template(2)],
            [create_row_template(1)["id"], create_row_template(2)],
            [create_row_template(1), create_row_template(2), create_row_template(3)],
        ],
    )
    def test_table_delete_valid(self, temp_file_generator, delete_data):
        with temp_file_generator(
            DEFAULT_DATA + [create_row_template(3)], lambda: finally_cleanup(path)
        ) as path:
            assert isinstance(path, p.Path)

            handler = t.TableHandler(path, DEFAULT_COLS, DEFAULT_SORT_KEY)
            handler.delete_rows(*delete_data)

            final_data = handler.get_rows()
            final_ids = handler._get_ids(final_data)
            ids = [
                row if isinstance(row, str) else row.get("id") for row in delete_data
            ]

            assert all(id not in final_ids for id in ids)

    @pytest.mark.parametrize(
        "delete_data",
        [
            [{}],
        ],
    )
    def test_table_delete_invalid(self, temp_file_generator, delete_data):
        with temp_file_generator(DEFAULT_DATA, lambda: finally_cleanup(path)) as path:
            assert isinstance(path, p.Path)

            handler = t.TableHandler(path, DEFAULT_COLS, DEFAULT_SORT_KEY)
            # did not raise
            handler.get_rows()

            with pytest.raises(t.TableHandlerError):
                handler.delete_rows(*delete_data)

    def test_table_delete_invalid_aba(self, temp_file_generator):
        with temp_file_generator(DEFAULT_DATA, lambda: finally_cleanup(path)) as path:
            assert isinstance(path, p.Path)

            handler = t.TableHandler(path, DEFAULT_COLS, DEFAULT_SORT_KEY)
            old_data = handler.get_rows()

            with pytest.raises(t.TableHandlerError):
                handler.delete_rows({})

            final_data = handler.get_rows()

            assert old_data == final_data

    # region Async # TODO

    # region Transferable

    def test_table_transferable(
        self, temp_folder_path: p.Path, mocked_unique_id_get_all
    ):
        path = temp_folder_path / "aba_db.json"

        try:
            assert not path.exists()

            h1 = t.TableHandler(path, DEFAULT_COLS, DEFAULT_SORT_KEY)
            assert h1.get_rows() == []
            h1.insert_rows(r1 := create_row_template(69), r2 := create_row_template(70))
            assert h1.get_rows() == [r1, r2]

            h2 = t.TableHandler(path, DEFAULT_COLS, DEFAULT_SORT_KEY)
            assert h2.get_rows() == [r1, r2]
        finally:
            finally_cleanup(path)
