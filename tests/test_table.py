import json
import pathlib as p

import pytest

from bacon_db.db import table as t


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
        t.TableHandler(path, {"col1": int, "col2": float})
        assert not path.exists()

    def test_init_valid_existent(self, temp_folder_path: p.Path):
        path = temp_folder_path / "db.json"

        assert not path.exists()

        try:
            with open(path, "w") as file:
                json.dump([], file)

            # does not raise
            t.TableHandler(path, {"col1": int, "col2": float})
        finally:
            self.finally_cleanup(path)

    def test_init_invalid(self, temp_folder_path: p.Path):
        path = temp_folder_path / "folder"

        assert not path.exists()

        try:
            path.mkdir()

            with pytest.raises(t.TableHandlerError):
                t.TableHandler(path, {"col1": int, "col2": float})
        finally:
            path.rmdir()

    # endregion
