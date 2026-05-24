import contextlib
import json
import pathlib as p

import pytest

import bacon_db.json as j


class TestJSONHandler:
    # region Setup

    @pytest.fixture(scope="class")
    def temp_file_generator(self, temp_folder_path):

        @contextlib.contextmanager
        def __fn(data: j.Data):
            path: p.Path = temp_folder_path / "_temp_.json"
            assert isinstance(path, p.Path)

            with open(path, "w") as f:
                json.dump(data, f)

            yield path

            path.unlink()

        return __fn

    # endregion

    # region Reading

    def test_read_nonexistent(self, temp_folder_path):
        file: p.Path = temp_folder_path / "nonexistent.json"

        assert not file.exists()
        with pytest.raises(j.JSONHandlerError):
            j.JSONHandler(file).read()

    def test_read_existent(self, temp_file_generator):
        with temp_file_generator(
            [{"col1": 1, "col2": 2}, {"col1": 10, "col2": 20}]
        ) as file:
            assert isinstance(file, p.Path)
            assert file.exists()

            handler = j.JSONHandler(file)

            # does not raise
            assert isinstance(data := handler.read(), list)
            assert len(data) == 2
            assert all(isinstance(elem, dict) for elem in data)
            assert all(len(elem.keys()) == 2 for elem in data)
            assert all(set(elem.keys()) == {"col1", "col2"} for elem in data)
            assert all(all(isinstance(v, int) for v in elem.values()) for elem in data)

    # TODO: test for hitting cache

    # endregion

    # region Creating
    # TODO: implement
    # endregion

    # region Writing
    # TODO: implement
    # endregion
