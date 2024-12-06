import numpy as np

def split_matrices(A, B, block_size):
    """
    Splits matrices A and B into smaller sub-matrices for distributed computation.
    """
    assert A.shape[1] == B.shape[0], "Incompatible matrix dimensions for multiplication"

    # Divide matrix A and B into blocks
    a_blocks = []
    b_blocks = []
    for i in range(0, A.shape[0], block_size):
        for j in range(0, B.shape[1], block_size):
            a_block = A[i:i + block_size, :]
            b_block = B[:, j:j + block_size]
            a_blocks.append(a_block)
            b_blocks.append(b_block)
    return a_blocks, b_blocks

def simulate_worker_computation(a_block, b_block):
    """
    Simulates a worker node computing the matrix multiplication of sub-matrices.
    """
    return np.dot(a_block, b_block)

def aggregate_results(results, A_shape, B_shape, block_size):
    """
    Aggregates results from all worker nodes into the final matrix.
    """
    C = np.zeros((A_shape[0], B_shape[1]))
    idx = 0
    for i in range(0, A_shape[0], block_size):
        for j in range(0, B_shape[1], block_size):
            block = results[idx]
            C[i:i + block.shape[0], j:j + block.shape[1]] = block
            idx += 1
    return C

# Example usage
if __name__ == "__main__":
    # Initialize example matrices
    A = np.random.randint(1, 10, (6, 4))  # 6x4 matrix
    B = np.random.randint(1, 10, (4, 5))  # 4x5 matrix
    block_size = 2

    print("Matrix A:")
    print(A)
    print("\nMatrix B:")
    print(B)

    # Split matrices into blocks
    a_blocks, b_blocks = split_matrices(A, B, block_size)

    # Simulate worker computations
    results = [simulate_worker_computation(a, b) for a, b in zip(a_blocks, b_blocks)]

    # Aggregate results
    C = aggregate_results(results, A.shape, B.shape, block_size)

    print("\nResulting Matrix C:")
    print(C)
