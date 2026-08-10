import numpy as np

def rotate_90(grid: np.ndarray) -> np.ndarray:
    """Rotates a grid 90 degrees clockwise."""
    return np.rot90(grid, k=-1)

def gravity_down(grid: np.ndarray) -> np.ndarray:
    """
    Applies gravity to all non-zero pixels, making them fall to the bottom.
    Preserves the column position of each pixel.
    """
    out = np.zeros_like(grid)
    for col in range(grid.shape[1]):
        non_zero = grid[:, col][grid[:, col] != 0]
        if len(non_zero) > 0:
            out[-len(non_zero):, col] = non_zero
    return out

def keep_only_color(grid: np.ndarray, color: int) -> np.ndarray:
    """Returns a new grid keeping only pixels of the specified color."""
    out = np.zeros_like(grid)
    out[grid == color] = color
    return out

def fill_holes(grid: np.ndarray, fill_color: int) -> np.ndarray:
    """
    Fills 'holes' (0s completely surrounded by non-zeros horizontally and vertically).
    Simple implementation for demonstration.
    """
    out = grid.copy()
    rows, cols = grid.shape
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if grid[r, c] == 0:
                # Check neighbors
                if grid[r-1, c] != 0 and grid[r+1, c] != 0 and grid[r, c-1] != 0 and grid[r, c+1] != 0:
                    out[r, c] = fill_color
    return out
