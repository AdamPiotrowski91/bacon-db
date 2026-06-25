import contextlib
import pathlib as p
import threading as th

import pytest
import pytest_mock as mock

import bacon_db.core.json as j


class TestJSONHandler:
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

    # region Async

    @classmethod
    def assert_async_action(
        cls, handler: j.JSONHandler, lock_prop: str, data: j.DBData | None = None
    ):
        try:
            getattr(handler, lock_prop).acquire()
            finished = th.Event()

            def action():
                if data:
                    handler.write(data)
                    finished.set()
                    assert handler.read() == data
                else:
                    assert handler.read() == []
                    finished.set()

            t = th.Thread(target=action)
            t.start()

            assert not finished.wait(0.1)

            getattr(handler, lock_prop).release()

            assert finished.wait(0.1)
        finally:
            with contextlib.suppress(Exception):
                t.join()  # type: ignore

    def test_async_read(self, temp_file_generator):
        with temp_file_generator([]) as path:
            assert isinstance(path, p.Path)

            handler = j.JSONHandler(path)

            self.assert_async_action(handler, "_lock_data")

    def test_async_read_cache(self, temp_file_generator):
        with temp_file_generator([]) as path:
            assert isinstance(path, p.Path)

            handler = j.JSONHandler(path)
            handler.read()  # set cache

            self.assert_async_action(handler, "_lock_cache")

    def test_async_write(self, temp_file_generator):
        with temp_file_generator([]) as path:
            assert isinstance(path, p.Path)

            handler = j.JSONHandler(path)

            self.assert_async_action(handler, "_lock_data", [{"col": 1}])

    def test_async_write_cache(self, temp_file_generator):
        with temp_file_generator([]) as path:
            assert isinstance(path, p.Path)

            handler = j.JSONHandler(path)
            handler.read()  # set cache

            self.assert_async_action(handler, "_lock_cache", [{"col": 1}])

    # region Transferable

    def test_transferable(self, temp_folder_path: p.Path):
        path = temp_folder_path / "db.json"
        data = [{"a": 1, "b": "test"}]

        try:
            h1 = j.JSONHandler(path)
            assert not h1.exists()
            h1.create()
            assert h1.read() == []
            h1.write(data)
            assert h1.read() == data

            h2 = j.JSONHandler(path)
            assert h2.exists()
            assert h2.read() == data
        finally:
            path.unlink(missing_ok=True)
