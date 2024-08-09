def sum_n_first_int(n):
    s = 0
    for i in range(1,n+1):
        s += i
    return s

def compute(current, mini, maxi):
    '''
    Receives an ordered list of values.
    The order corresponds to the priority order of metrics in pref
    Each value corresponds to the associated metric
    current is the metrics to obtain a score from
    mini the minimal value of each metric
    maxi the maximal value of each metric
    '''
    N = len(current)
    D = 0.1

    # Compute weights according to N
    weights = [ (1.0 + sum_n_first_int(N-1) * D) / N ]
    for i in range(N-1):
        weights.append( weights[-1] - D )
    print(f"weights = {weights}")

    s = 0
    for w in weights:
        s += w
    print(f"sum weights = {s}")

    # Weighted score
    score = 0.0
    for i in range(N):
        score += weights[i] * (maxi[i] - current[i])/(maxi[i] - mini[i])

    return score

mini = [10, 10, 10]
maxi = [20, 20, 20]

# current = [20, 20, 20]
# current = [10, 10, 10]
current = [14, 15, 15]

print(f"score = {compute(current, mini, maxi)}")

"""

weights = [ (1.0 + sum_n_first_int(N-1) * D) / N ]

sum_weights = 1.0
w_0 = (1.0 + sum_n_first_int(N-1) * D) / N
w_1 = w_0 - D
w_2 = w_1 - D
w_3 = w_2 - D
w_3 = 0.05

w_3 = w_0 - D - D - D 
w_3 = w_0 - 3 * D
w_i = w_0 - i * D

w_N-1 = w_0 - (N-1) * D = 0.05
w_0 = 0.05 + (N-1) * D
(1.0 + sum_n_first_int(N-1) * D) / N = 0.05 + (N-1) * D
1.0 + sum_n_first_int(N-1) * D = 0.05 * N + (N-1) * N * D
sum_n_first_int(N-1) * D - (N-1) * N * D = 0.05 * N - 1.0
D * (sum_n_first_int(N-1) - (N-1) * N) = 0.05 * N - 1.0
D = (0.05 * N - 1.0) / (sum_n_first_int(N-1) - (N-1) * N)


"""