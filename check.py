# check.py
import numpy as np
import logging

def check(a_block, b_block, c_block):
    """
    Validates the result of a single block multiplication using a random vector.
    Returns 1 if correct, 0 otherwise.
    
    Parameters:
    - a_block (np.ndarray): Sub-matrix from matrix A.
    - b_block (np.ndarray): Sub-matrix from matrix B.
    - c_block (np.ndarray): Resulting sub-matrix from matrix C (A x B).
    
    Returns:
    - int: 1 if the multiplication is correct, 0 otherwise.
    """
    try:
        # Generate a random vector with entries between 0 and 999
        test_vector = np.random.randint(0, 1000, size=(b_block.shape[1], 1))
        
        # Compute (A * B) * test_vector
        expected = np.dot(a_block, np.dot(b_block, test_vector))
        
        # Compute C * test_vector
        actual = np.dot(c_block, test_vector)
        
        # Check if the two results match
        if np.array_equal(expected, actual):
            return 1
        else:
            # Log the discrepancy for debugging
            logging.debug(f"Validation failed:")
            logging.debug(f"Expected:\n{expected}")
            logging.debug(f"Actual:\n{actual}")
            return 0
    except Exception as e:
        logging.error(f"Error during validation: {e}")
        return 0
