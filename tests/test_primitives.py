import numpy as np
from core.primitives import rotate_90, gravity_down, keep_only_color, fill_holes

def test_rotate_90():
    grid = np.array([
        [1, 2],
        [3, 4]
    ])
    expected = np.array([
        [3, 1],
        [4, 2]
    ])
    assert np.array_equal(rotate_90(grid), expected)

def test_gravity_down():
    grid = np.array([
        [1, 0, 2],
        [0, 0, 3],
        [0, 4, 0]
    ])
    expected = np.array([
        [0, 0, 0],
        [0, 0, 2],
        [1, 4, 3]
    ])
    assert np.array_equal(gravity_down(grid), expected)

def test_keep_only_color():
    grid = np.array([
        [1, 2, 1],
        [3, 1, 4]
    ])
    expected = np.array([
        [1, 0, 1],
        [0, 1, 0]
    ])
    assert np.array_equal(keep_only_color(grid, 1), expected)

def test_fill_holes():
    grid = np.array([
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1]
    ])
    expected = np.array([
        [1, 1, 1],
        [1, 2, 1],
        [1, 1, 1]
    ])
    assert np.array_equal(fill_holes(grid, 2), expected)
