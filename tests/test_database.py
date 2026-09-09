import pathlib as p

import pytest

from bacon_db import database as d
from bacon_db.db import relation as r
from bacon_db.db import table as t

from . import test_table as tt
from . import test_relation as tr

# region Setup

type FixtureDBYield = tuple[p.Path, t.TableColumnsSetup, str]


# region Database


class TestRelationRowData:
    @pytest.fixture(scope="class")
    def db_main(self, temp_file_generator):
        with temp_file_generator(
            [tt.create_row_template(1), tt.create_row_template(2)],
            lambda: tt.finally_cleanup(path_main),
            "_main_test_.json",
        ) as path_main:
            yield path_main, tt.DEFAULT_COLS, tt.DEFAULT_SORT_KEY

    @pytest.fixture(scope="class")
    def db_second(self, temp_file_generator):
        with temp_file_generator(
            [tt.create_row_template(4)],
            lambda: tt.finally_cleanup(path_main),
            "_second_test_.json",
        ) as path_main:
            yield path_main, tt.DEFAULT_COLS, tt.DEFAULT_SORT_KEY

    # region ~ References

    def test_basic_references_and_init(
        self, db_main: FixtureDBYield, db_second: FixtureDBYield
    ):
        table_handler = t.TableHandler(*db_main)

        # single table
        db_handler = d.Database(main=table_handler)

        assert db_handler.main is table_handler
        assert db_handler["main"] is table_handler

        # multiple tables
        second_table_handler = t.TableHandler(*db_second)

        db_handler = d.Database(main=table_handler, second=second_table_handler)

        assert db_handler.main is table_handler
        assert db_handler["main"] is table_handler

    def test_wrong_reference(self, db_main: FixtureDBYield):
        with pytest.raises(d.DatabaseError):
            d.Database()  # No tables - raises

        # only invalid
        with pytest.raises(d.DatabaseError):
            d.Database(some=None)  # type: ignore

        with pytest.raises(d.DatabaseError):
            d.Database(some="not table")  # type: ignore

        # some invalid
        table_handler = t.TableHandler(*db_main)

        with pytest.raises(d.DatabaseError):
            d.Database(main=table_handler, some="not table")  # type: ignore
