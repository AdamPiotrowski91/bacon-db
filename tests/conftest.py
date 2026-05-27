import contextlib
import json
import pathlib as p
import shutil
from typing import Callable

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

        yield path

        path.unlink()
        if cleanup:
            cleanup()

    return __fn
