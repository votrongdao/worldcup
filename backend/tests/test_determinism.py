"""Same seed + config must yield the same run hash."""
from src.seed.provider import sub_seed


def test_sub_seed_stable():
    assert sub_seed(42, "nation", 3) == sub_seed(42, "nation", 3)
    assert sub_seed(42, "nation", 3) != sub_seed(42, "nation", 4)
# TODO: full run-hash stability once the engine + FSM are implemented.
