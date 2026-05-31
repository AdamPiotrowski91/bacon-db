import pytest

from bacon_db import utils as u


class TestUtils:
    # region `count_required_args`

    @pytest.mark.parametrize(
        "fn, expected_count",
        [
            [lambda x, y, z: None, 3],
            [lambda x, y, z=None: None, 2],
            [lambda x, y=None, z=None: None, 1],
            [lambda x=None, y=None, z=None: None, 0],
            [lambda x: None, 1],
            [lambda x=None: None, 0],
        ],
    )
    def test_count_required_args(self, fn, expected_count):
        assert u.count_required_args(fn) == expected_count

    # endregion

    # region `unique_id`

    def test_unique_id(self):
        vals = [u.unique_id() for _ in range(100_000)]

        assert all(isinstance(v, str) for v in vals)
        assert len(vals) == len(set(vals))

    # endregion
