import contextlib
import json
import pathlib as p
import shutil
import uuid
from itertools import count
from typing import Callable
from unittest.mock import patch

import pytest

import bacon_db.json as j


@pytest.fixture(scope="session")
def temp_folder_path():
    ROOT = p.Path(__file__).parent / "_TEMP_"
    shutil.rmtree(ROOT, ignore_errors=True)
    ROOT.mkdir()

    yield ROOT

    # will raise if tests setup did not clean up properly
    ROOT.rmdir()


@pytest.fixture(scope="module")
def temp_file_generator(temp_folder_path):

    @contextlib.contextmanager
    def __fn(data: j.DBData, cleanup: Callable[[], None] | None = None):
        path: p.Path = temp_folder_path / "_temp_.json"
        assert isinstance(path, p.Path)

        with open(path, "w") as f:
            json.dump(data, f)

        try:
            yield path
        finally:
            path.unlink()
            if cleanup:
                cleanup()

    return __fn


@pytest.fixture
def mocked_unique_id_get_all():
    """Method mocking `uuid.uuid4()` to return expected string and yielding a
    method that returns all ids generated during the test using this fixture.

    In other words, just having this fixture used mocks the uuid method but
    calling it returns the list of uuids generated during this test.
    """

    gen = count(start=69)
    values = []

    def __fn():
        values.append(str(next(gen)))
        return values[-1]

    def __getter():
        return values

    with patch.object(uuid, "uuid4", new=__fn):
        yield __getter
