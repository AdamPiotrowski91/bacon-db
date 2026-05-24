import pathlib as p

import pytest


@pytest.fixture(scope="session")
def temp_folder_path():
    ROOT = p.Path(__file__).parent / "_TEMP_"
    ROOT.mkdir()

    yield ROOT

    ROOT.rmdir()
