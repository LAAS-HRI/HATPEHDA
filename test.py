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

