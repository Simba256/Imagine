# singleSystem.py
import numpy as np
import logging


def split_matrices(A, B, block_size):
    """
    Splits matrices A and B into smaller sub-matrices for distributed computation.
    Handles cases where matrix dimensions are not divisible by block_size.

    Parameters:
    - A (np.ndarray): Matrix A of shape (m, k).
    - B (np.ndarray): Matrix B of shape (k, n).
    - block_size (int): The size of each block.

    Returns:
    - tuple: Two lists containing the blocks of A and B respectively.
    """
    a_blocks = []
    b_blocks = []

    # Split A into row-wise blocks
    for i in range(0, A.shape[0], block_size):
        a_block = A[i:i + block_size, :]  # Rows i to i+block_size of A
        a_blocks.append(a_block)

    # Split B into column-wise blocks
    for j in range(0, B.shape[1], block_size):
        b_block = B[:, j:j + block_size]  # Columns j to j+block_size of B
        b_blocks.append(b_block)

    logging.debug(f"split_matrices: Created {len(a_blocks)} row blocks for A and {len(b_blocks)} column blocks for B.")
    return a_blocks, b_blocks


# singleSystem.py

def aggregate_results(results, A_shape, B_shape, block_size):
    """
    Aggregates results from all worker nodes into the final matrix.

    Parameters:
    - results (list of np.ndarray): List of result blocks from workers.
    - A_shape (tuple): Shape of matrix A.
    - B_shape (tuple): Shape of matrix B.
    - block_size (int): The size of each block.

    Returns:
    - np.ndarray: The final aggregated matrix C.
    """
    C = np.zeros((A_shape[0], B_shape[1]))
    idx = 0
    for i in range(0, A_shape[0], block_size):
        for j in range(0, B_shape[1], block_size):
            block = results[idx]
            C[i:i + block.shape[0], j:j + block.shape[1]] = block
            idx += 1
    logging.debug("aggregate_results: Successfully aggregated results into final matrix.")
    return C
