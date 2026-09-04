import numpy as np
import pytest

from HLSearch_Beam import (
    SearchConfig,
    State,
    build_base_rows,
    build_shift_table,
    generate_primes,
    parse_args,
    shift_array,
)


def test_generate_primes_handles_boundaries_and_returns_ordered_values():
    assert generate_primes(1) == []
    assert generate_primes(2) == [2]
    assert generate_primes(10) == [2, 3, 5, 7]


def test_shift_array_shifts_right_and_zero_fills():
    values = np.array([True, False, True, True], dtype=bool)

    np.testing.assert_array_equal(
        shift_array(values, 1),
        np.array([False, True, False, True], dtype=bool),
    )
    np.testing.assert_array_equal(
        shift_array(values, 0),
        values,
    )
    np.testing.assert_array_equal(
        shift_array(values, 4),
        np.zeros(4, dtype=bool),
    )


def test_build_base_rows_uses_one_based_prime_residues():
    rows = build_base_rows([2, 3], cols=6)

    assert rows.shape == (2, 6)
    np.testing.assert_array_equal(
        rows[0],
        np.array([True, False, True, False, True, False]),
    )
    np.testing.assert_array_equal(
        rows[1],
        np.array([True, False, False, True, False, False]),
    )


def test_build_shift_table_contains_shifted_complements():
    primes = [2, 3]
    rows = build_base_rows(primes, cols=6)
    table = build_shift_table(primes, cols=6)

    assert [level.shape for level in table] == [(2, 6), (3, 6)]
    for level, row in enumerate(rows):
        for shift in range(primes[level]):
            np.testing.assert_array_equal(
                table[level][shift],
                ~shift_array(row, shift),
            )


@pytest.mark.parametrize(
    "changes",
    [
        {"cols": 0},
        {"depth": -1},
        {"depth": 2, "primes": [2]},
        {"limit": -1},
        {"beam_width": 0},
        {"postfix_update_interval": 0},
    ],
)
def test_search_config_rejects_invalid_values(changes):
    with pytest.raises(ValueError):
        SearchConfig(**changes)


def test_parse_args_applies_cli_overrides():
    args = parse_args(
        [
            "--depth",
            "2",
            "--limit",
            "3",
            "--max-depth",
            "4",
            "--target",
            "5",
            "--beam-width",
            "6",
            "--primes-count",
            "7",
            "--cols",
            "8",
            "--output",
            "result.txt",
            "--mininterval",
            "0.25",
            "--log-level",
            "DEBUG",
            "--checkpoint",
            "checkpoint.json",
            "--resume",
            "old-checkpoint.json",
        ]
    )

    assert vars(args) == {
        "depth": 2,
        "limit": 3,
        "max_depth": 4,
        "target": 5,
        "beam_width": 6,
        "primes_count": 7,
        "cols": 8,
        "output": "result.txt",
        "mininterval": 0.25,
        "log_level": "DEBUG",
        "checkpoint": "checkpoint.json",
        "resume": "old-checkpoint.json",
    }


def make_small_config(**overrides):
    values = {
        "primes": [2, 3],
        "depth": 2,
        "limit": 0,
        "max_depth": 2,
        "target": 2,
        "cols": 6,
        "beam_width": 6,
        "progress_mininterval": 0,
        "postfix_update_interval": 1,
    }
    values.update(overrides)
    return SearchConfig(**values)


def test_state_runs_small_beam_search():
    config = make_small_config()
    state = State(config, build_shift_table(config.primes, config.cols))

    result = state.run()

    assert result is state
    assert result.max_count == 2
    assert result.results == 6
    assert result.shifts == [
        [0, 0],
        [0, 1],
        [0, 2],
        [1, 0],
        [1, 1],
        [1, 2],
    ]


def test_state_checkpoint_can_be_loaded(tmp_path):
    config = make_small_config()
    shift_table = build_shift_table(config.primes, config.cols)
    checkpoint = tmp_path / "search.json"

    original = State(
        config,
        shift_table,
        checkpoint_path=checkpoint,
        checkpoint_interval=1,
    ).run()
    resumed = State(config, shift_table).run(resume_from=checkpoint)

    assert checkpoint.exists()
    assert resumed.max_count == original.max_count
    assert resumed.results == original.results
    assert resumed.shifts == original.shifts


@pytest.mark.parametrize("size", [0, 1, 7, 8, 9, 65])
def test_state_mask_integer_conversion_round_trips(size):
    config = make_small_config(cols=max(size, 1))
    state = State(config, [])
    mask = np.array([(index % 3) == 0 for index in range(size)], dtype=bool)

    restored = state._int_to_mask(state._mask_to_int(mask), size)

    np.testing.assert_array_equal(restored, mask)
    state.pbar.close()
