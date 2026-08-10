import numpy as np
from solver.enumerator import BeamSearch

def test_beam_search_success():
    """
    Verify that our Beam Search engine correctly traverses the search space,
    respects state-memoization, and reconstructs expected output grids.
    """
    search = BeamSearch(beam_width=3, max_depth=5)

    input_grid = np.zeros((3, 3))
    expected_output = np.ones((3, 3))

    success, final_grid, trace = search.solve(input_grid, expected_output)

    assert success is True
    assert np.array_equal(final_grid, expected_output)
    assert search.current_depth <= search.max_depth
    assert len(search.memoization_cache) > 0
    assert search.cumulative_time >= 0.0

def test_beam_search_memoization():
    """
    Test memoization specifically.
    """
    search = BeamSearch()
    input_grid = np.array([[1, 2], [3, 4]])
    expected_output = np.array([[5, 6], [7, 8]]) # Will reach it via mock logic

    search.solve(input_grid, expected_output)

    # Check that initial state is cached
    assert search.hash_grid(input_grid) in search.memoization_cache
