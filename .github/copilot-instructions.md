# Copilot instructions for PyHLSearch_Beam

## Project shape

This repository is a small Python 3.13-oriented research program for applying beam search to the HLSearch prime-shift problem. The implementation is intentionally concentrated in `HLSearch_Beam.py`, which is both an importable module and the CLI entry point.

The main data flow is:

1. `generate_primes()` creates the ordered prime list.
2. `SearchConfig` holds search, output, and progress settings and validates core invariants.
3. `build_base_rows()` creates one boolean row per prime for the configured column count. `build_shift_table()` precomputes the complement of every valid shift so the hot search loop only needs NumPy boolean `&` operations.
4. `State` owns the mutable search state. `search()` delegates to the current beam-search implementation (`_search_beam()`); `_search_dfs()` is retained as the older iterative DFS implementation and is useful when changing or comparing search behavior.
5. The CLI builds the tables for the requested depth, runs `State.run()`, writes the winning count/result/shift paths to the output file, and logs to both the console and a rotating `HLSearch_Beam.log`.

Checkpoints are JSON snapshots of search state. They serialize boolean masks as Python integers, use an atomic temporary-file replacement when saving, and can be resumed with `--resume`. Changes to state fields, mask encoding, or beam-frontier structure must preserve checkpoint compatibility or intentionally update the checkpoint version and error handling.

## Commands

Run the CLI with a deliberately small search while developing:

```bat
python HLSearch_Beam.py --depth 10 --beam-width 100
```

The default configuration is much larger. Use `--help` to inspect all CLI options, including `--limit`, `--max-depth`, `--target`, `--primes-count`, `--cols`, `--output`, `--checkpoint`, and `--resume`.

Tests are configured by `pytest.ini` to discover `tests/test_*.py`:

```bat
python -m pytest
python -m pytest tests\test_example.py
python -m pytest tests\test_example.py::test_specific_behavior
```

There are currently no checked-in tests, so the full pytest command exits with "no tests collected" until tests are added. No build/package command or repository lint configuration is present.

## Conventions and invariants

- Keep public functionality in `HLSearch_Beam.py` importable without invoking the CLI; executable behavior belongs under the `if __name__ == "__main__":` block.
- Use `SearchConfig` rather than scattering new global search parameters. Its defaults are also used by `parse_args()`, while CLI overrides are copied into a new config before tables and state are built.
- Search masks are NumPy boolean arrays of length `cols`. Preserve this representation and vectorized operations in performance-sensitive code; avoid converting masks to Python collections in the search loop.
- A shift at a given level is indexed from `0` through `primes[level] - 1`. `shift_table[level][shift]` is already the complement row, so do not apply another complement during search.
- Beam pruning is intentional: each level sorts candidates by descending remaining count, then lexicographically by key, and keeps at most `beam_width`. Small beam widths can produce results different from complete search.
- The `limit` threshold prunes candidates below `max(limit, max_count)`. At the terminal depth, `target` handling is special when `depth == max_depth`; preserve that distinction when modifying pruning or result accounting.
- `State.run()` may resume a checkpoint, but a resume must use compatible dimensions and search inputs. Keep `key`, `zero_mask`, `node_count`, results, stack/frontier, and beam level synchronized when adding resumable state.
- Progress output is handled by `tqdm`; logging goes through the module logger configured by `setup_logging()`. Do not use progress-bar output as a substitute for persistent logging of important results.
- The CLI writes `max_count:`, `results:`, then one shift path per line to the selected output file. Preserve this simple output format unless the CLI contract is intentionally changed.
- Keep generated runtime artifacts such as logs, checkpoints, and `shift_path.txt` out of source changes unless the task explicitly concerns them. `.gitignore` already excludes Python caches, pytest caches, logs, and common build artifacts.
