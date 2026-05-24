import pathlib as p
import shutil

import pytest


@pytest.fixture(scope="session")
def temp_folder_path():
    ROOT = p.Path(__file__).parent / "_TEMP_"
    shutil.rmtree(ROOT, ignore_errors=True)
    ROOT.mkdir()

    yield ROOT

    # will raise if tests setup did not clean up properly
    ROOT.rmdir()
