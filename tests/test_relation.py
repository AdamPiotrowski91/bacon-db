import pathlib as p

import pytest

from bacon_db.db import relation as r
from bacon_db.db import table as t

from .test_table import finally_cleanup

# region Setup

RAW_DATA_SOURCE = {"a": 1, "b": "test", "id": "12345"}
SUB_DATA: t.DBData = [{"id": "1", "name": "A"}, {"id": "2", "name": "B"}]
SUB_COLS: t.TableColumnsSetup = {"name": str}
ROOT_DATA: t.DBData = [
    {"id": "r1", "col1": 10, "col2": "1"},
    {"id": "r2", "col1": 20, "col2": "2"},
]

type BasicRelatedTables = tuple[t.TableHandler, t.TableHandler]


# region RelationRowData


class TestRelationRowData:
    def test_is_dict(self):
        data = r.RelationRowData(RAW_DATA_SOURCE)

        assert isinstance(data, dict)
        assert set(data.keys()) == set(RAW_DATA_SOURCE.keys())
        assert set(data.values()) == set(RAW_DATA_SOURCE.values())

    def test_can_access_data(self):
        data = r.RelationRowData(RAW_DATA_SOURCE)

        assert data["a"] == 1
        assert data["b"] == "test"
        assert "c" not in data
        assert data == RAW_DATA_SOURCE

    def test_stringify(self):
        data = r.RelationRowData(RAW_DATA_SOURCE)

        assert str(data) == data["id"]

    def test_equality(self):
        data = r.RelationRowData(RAW_DATA_SOURCE)

        assert data == data  # NOSONAR
        assert str(data) == str(data)
        assert data == str(data)
        assert str(data) == data
        assert data == "12345"
        assert str(data) == "12345"
        assert data == RAW_DATA_SOURCE

    def test_inequality(self):
        data = r.RelationRowData(RAW_DATA_SOURCE)

        assert data != "a"
        assert data != "b"
        assert data != 1
        assert data != "test"
        assert data is not None
        assert str(data) != "a"
        assert str(data) != "b"
        assert str(data) != "1"
        assert str(data) != "test"
        assert data is not RAW_DATA_SOURCE  # equals but not the same ref


# region RelationHandler


class TestRelationHandler:
    # region ~ Setup

    @pytest.fixture
    def temp_basic_related_tables(self, temp_file_generator):
        """Yields tuple of Table Handlers `(<root>, <sub>)`."""

        with (
            temp_file_generator(
                SUB_DATA, lambda: finally_cleanup(path_sub), "_sub_.json"
            ) as path_sub,
            temp_file_generator(
                ROOT_DATA, lambda: finally_cleanup(path_root), "_root_.json"
            ) as path_root,
        ):
            assert isinstance(path_sub, p.Path)
            assert isinstance(path_root, p.Path)

            sub_handler = t.TableHandler(path_sub, SUB_COLS, "name")
            root_handler = t.TableHandler(
                path_root, {"col1": int, "col2": r.RelationHandler(sub_handler)}, "col1"
            )

            yield root_handler, sub_handler

    # region ~ Init

    def test_relation_table_init_valid(
        self, temp_basic_related_tables: BasicRelatedTables
    ):
        root, sub = temp_basic_related_tables

        # no errors
        assert sub.get_rows() == SUB_DATA
        assert root.get_rows()  # non-empty, cannot compare in this form

    # region ~ Get Rows

    def test_relation_table_get_valid(
        self, temp_basic_related_tables: BasicRelatedTables
    ):
        root, _ = temp_basic_related_tables

        root_data_parsed = [
            {
                k: (v if k != "col2" else next(se for se in SUB_DATA if se["id"] == v))
                for k, v in entry.items()
            }
            for entry in ROOT_DATA
        ]

        assert root.get_rows() == root_data_parsed
        assert root.get_single_row("r2")["col2"]["name"] == "B"

    # region ~ Insert Rows

    def test_relation_table_insert_valid(
        self, temp_basic_related_tables: BasicRelatedTables, mocked_unique_id_get_all
    ):
        root, sub = temp_basic_related_tables
        sub_data = sub.get_rows()
        new_entry = {"col1": 69, "col2": "1"}
        ids = mocked_unique_id_get_all()

        # inserted via sub ID
        row = root.insert_rows(new_entry).get_single_row(ids[-1])
        for k, v in new_entry.items():
            assert str(row[k]) == str(v)  # raw equals
            assert row[k] == v  # helper class handles equality
        assert sub.get_rows() == sub_data  # no change

        # inserted via sub Row
        row = root.insert_rows(
            {**new_entry, "col2": sub.get_single_row("1")}
        ).get_single_row(ids[-1])
        for k, v in new_entry.items():
            assert str(row[k]) == str(v)
            assert row[k] == v

        assert sub.get_rows() == sub_data  # no change

    # region ~ Update Rows

    # region ~ Delete Rows
