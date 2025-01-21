import numpy as np
from itertools import product

def split_matrix(mat, block_size):
    """
    Split a 2D numpy array into smaller blocks of size (block_size x block_size).
    Returns a list of (row_block, col_block, block_data).
    """
    nrows, ncols = mat.shape
    blocks = []
    row_blocks = (nrows + block_size - 1) // block_size  # ceil
    col_blocks = (ncols + block_size - 1) // block_size
    for i in range(row_blocks):
        for j in range(col_blocks):
            row_start = i * block_size
            row_end = min((i+1)*block_size, nrows)
            col_start = j * block_size
            col_end = min((j+1)*block_size, ncols)
            block = mat[row_start:row_end, col_start:col_end]
            blocks.append((i, j, block))
    return blocks, row_blocks, col_blocks


def block_multiply(A, B, block_size=64):
    """
    Multiply two matrices A and B using a block-based approach.
    This function does the block multiplication *locally*.
    In a real distributed system, you'd send each block multiplication to remote workers.
    """
    # A is (m x n), B is (n x p), result is (m x p)
    m, nA = A.shape
    nB, p = B.shape
    assert nA == nB, "Inner dimensions must match for multiplication."

    # Split A into blocks (size m x n)
    A_blocks, A_row_blocks, A_col_blocks = split_matrix(A, block_size)
    # Split B into blocks (size n x p)
    B_blocks, B_row_blocks, B_col_blocks = split_matrix(B, block_size)

    # We expect:
    #  - A_col_blocks == B_row_blocks  (both = # blocks in "n" dimension)
    # because these correspond to the same dimension split
    result = np.zeros((m, p), dtype=np.float32)

    # We'll store blocks in a dictionary by (row_block, col_block)
    A_block_dict = {}
    for (i, j, block_data) in A_blocks:
        A_block_dict[(i, j)] = block_data

    B_block_dict = {}
    for (i, j, block_data) in B_blocks:
        B_block_dict[(i, j)] = block_data

    # For each block in the result, we do:
    # result_block(i, j) = sum over k of A_block(i, k) * B_block(k, j)
    for i in range(A_row_blocks):
        for j in range(B_col_blocks):
            # Each partial block result is summed across k
            block_rows = None
            block_cols = None
            partial_sum = None

            for k in range(A_col_blocks):  
                # A_col_blocks should match B_row_blocks
                A_sub = A_block_dict.get((i, k))
                B_sub = B_block_dict.get((k, j))

                if A_sub is None or B_sub is None:
                    continue

                # Multiply these two blocks
                local_result = np.dot(A_sub, B_sub)  # locally

                # We'll accumulate into partial_sum
                if partial_sum is None:
                    partial_sum = local_result
                    block_rows, block_cols = local_result.shape
                else:
                    partial_sum += local_result

            # Write partial_sum into the correct region of the final result
            if partial_sum is not None:
                row_start = i * block_size
                row_end = row_start + block_rows
                col_start = j * block_size
                col_end = col_start + block_cols
                result[row_start:row_end, col_start:col_end] = partial_sum

    return result


class Dense:
    """
    A minimal Dense (fully-connected) layer.
    W shape: (input_dim, output_dim)
    b shape: (output_dim,)
    """
    def __init__(self, input_dim, output_dim, block_size=64):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.block_size = block_size
        # Initialize weights, biases
        limit = np.sqrt(6.0 / (input_dim + output_dim))
        self.W = np.random.uniform(-limit, limit, (input_dim, output_dim)).astype(np.float32)
        self.b = np.zeros((output_dim,), dtype=np.float32)

    def forward(self, x):
        """
        x: shape (batch_size, input_dim)
        Returns: shape (batch_size, output_dim)

        Instead of doing x.dot(self.W), we do block-based multiplication.
        """
        # block_multiply expects 2D arrays
        # x shape: (batch_size, input_dim)
        # W shape: (input_dim, output_dim)
        # result shape: (batch_size, output_dim)
        out = block_multiply(x, self.W, block_size=self.block_size)
        out += self.b  # broadcast add
        return out

    def __repr__(self):
        return f"Dense(input_dim={self.input_dim}, output_dim={self.output_dim}, block_size={self.block_size})"


# Example usage
if __name__ == "__main__":
    # Suppose we have a small "network" with 1 hidden layer
    batch_size = 4
    input_dim = 8
    hidden_dim = 16
    output_dim = 2
    block_size = 4

    # Layers
    dense1 = Dense(input_dim, hidden_dim, block_size=block_size)
    dense2 = Dense(hidden_dim, output_dim, block_size=block_size)

    # Dummy input
    x = np.random.randn(batch_size, input_dim).astype(np.float32)

    # Forward pass
    hidden = dense1.forward(x)
    # For fun, do a simple ReLU
    hidden = np.maximum(hidden, 0.0)
    # Then next layer
    logits = dense2.forward(hidden)

    print("Input shape:", x.shape)
    print("Hidden shape:", hidden.shape)
    print("Logits shape:", logits.shape)
    print("Logits:\n", logits)
