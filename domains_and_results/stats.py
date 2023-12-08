import exec_automaton
from arrangement import *
import matplotlib.pyplot as plt
from progress.bar import IncrementalBar


domain_name, solution_tree, begin_step = exec_automaton.load_solution()

N = 10000
results = {}

bar = IncrementalBar('Processing', max=N)
for i in range(N):
    result, seed = exec_automaton.main_exec(domain_name, solution_tree, begin_step)
    if result in results:
        results[result].append(seed)
    else:
        results[result] = [seed]
    bar.next()
bar.finish()

sorted_results = sorted(results.items())
for s in sorted_results:
    print(f"({s[0]},{len(s[1])}), ", end="")
print("")

def get_nb_sup(n):
    total=0
    for t in sorted_results:
        if t[0]>=n:
            total+=t[1]
    return total

# N14_N = get_nb_sup(14)
# N20_14 = get_nb_sup(20)
# print(f"total(14)={N14_N/N}")
# print(f"total(20_14)={N20_14/N14_N}")

fig, ax = plt.subplots()
x_list = []
y_list = []
for t in sorted_results:
    x_list.append(str(t[0]))
    y_list.append(len(t[1]))
ax.bar(x_list, y_list, label=x_list)
plt.show()