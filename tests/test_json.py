import contextlib
import json
import pathlib as p

import pytest
import pytest_mock as mock

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

    def test_create_existent(self, temp_file_generator):
        with temp_file_generator([]) as file:
            assert isinstance(file, p.Path)
            assert file.exists()

            with pytest.raises(j.JSONHandlerError):
                j.JSONHandler(file).create()

    def test_create_nonexistent(self, temp_folder_path: p.Path):
        path = temp_folder_path / "db.json"

        assert not path.exists()

        try:
            handler = j.JSONHandler(path)
            handler.create()

            assert path.exists()
            assert handler.read() == []
        finally:
            path.unlink(missing_ok=True)

    # endregion

    # region Writing

    def test_write_nonexistent(self, temp_folder_path: p.Path):
        path = temp_folder_path / "nonexistent.json"

        assert not path.exists()

        with pytest.raises(j.JSONHandlerError):
            j.JSONHandler(path).write([])

    def test_write_existent_good_data(self, temp_folder_path: p.Path):
        path = temp_folder_path / "db.json"

        try:
            handler = j.JSONHandler(path)
            handler.create()

            assert handler.read() == []

            data = [{"one": 1}]
            handler.write(data)

            assert handler.read() == data
        finally:
            path.unlink(missing_ok=True)

    @pytest.mark.parametrize("data", [set(), (), {}, "string", 21, [1, 2]])
    def test_write_existent_wrong_data(self, temp_folder_path: p.Path, data):
        path = temp_folder_path / "db.json"

        try:
            handler = j.JSONHandler(path)
            handler.create()

            with pytest.raises(AssertionError):
                handler.write(data)
        finally:
            path.unlink(missing_ok=True)

    # endregion

    # region QoL

    def test_init(self, temp_folder_path: p.Path):
        path = temp_folder_path / "db.json"

        assert not path.exists()

        # Path
        try:
            # does not raise
            assert j.JSONHandler(path).create().read() == []
        finally:
            path.unlink(missing_ok=True)

        # string
        try:
            # does not raise
            assert j.JSONHandler(str(path)).create().read() == []
        finally:
            path.unlink(missing_ok=True)

    def test_can_chain_methods(self, temp_folder_path: p.Path):
        path = temp_folder_path / "db.json"

        assert not path.exists()

        data = [{"one": 1}, {"one": 2}]

        try:
            assert j.JSONHandler(path).create().write(data).read() == data
        finally:
            path.unlink(missing_ok=True)

    def test_can_handle_file_problems_during_runtime(self, temp_folder_path: p.Path):
        path = temp_folder_path / "db.json"

        assert not path.exists()

        try:
            handler = j.JSONHandler(path)
            handler.create()

            assert handler.read() == []

            path.unlink()

            with pytest.raises(j.JSONHandlerError):
                # cache does not help, we still need the file to exist
                handler.read()
        finally:
            path.unlink(missing_ok=True)

    def test_exists(self, temp_folder_path: p.Path, mocker: mock.MockerFixture):
        path = temp_folder_path / "db.json"

        assert not path.exists()

        spy = mocker.spy(j.p.Path, "exists")
        handler = j.JSONHandler(path)

        spy.assert_not_called()
        assert path.exists() == handler.exists()
        assert spy.call_count == 2

        try:
            handler.create()
            spy.reset_mock()

            spy.assert_not_called()
            assert path.exists() == handler.exists()
            assert spy.call_count == 2
        finally:
            path.unlink(missing_ok=True)

    # endregion
