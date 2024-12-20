import numpy as np


def check(a,b,c,n,m,n1,m1,n2,m2):
    if n != n1 or m != m2 or m1 != n2:
        print("Matrix multiplication not possible!")
        return -1
    
    test_vector = np.random.randint(0, 1000, size=(m2, 1))
    bxt = np.dot(b, test_vector)
    result = np.dot(a, bxt)
    cxt = np.dot(c, test_vector)

    if np.array_equal(result, cxt):
        return 1
    else:
        return 0



def check_result():
    input = open("input.txt", "r")
    n1, m1 = map(int,input.readline().strip().split())
    matrix_a = []
    for i in range(n1):
        matrix_a.append(list(map(int, input.readline().strip().split())))


    input.readline()

    n2, m2 = map(int,input.readline().strip().split())
    matrix_b = []
    for i in range(n2):
        matrix_b.append(list(map(int, input.readline().strip().split())))
    input.close()
    
    output = open("output.txt", "r")
    n, m = map(int,output.readline().strip().split())
    matrix_c = []

    for i in range(n):
        matrix_c.append(list(map(float, output.readline().strip().split())))
    output.close()

    return check(np.array(matrix_a), np.array(matrix_b), np.array(matrix_c), n, m, n1, m1, n2, m2)
