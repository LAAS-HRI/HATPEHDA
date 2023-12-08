import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import dill



import easygui
path = easygui.fileopenbox()

print(path)
solutions = dill.load(open(path, "rb"))

# xdata = []
# ydata = []
# for s in solutions:
#     xdata.append(s[0])
#     ydata.append(s[1])
# plt.plot(xdata, ydata, 'ro')
# plt.xlabel("score human solution")
# plt.ylabel("score robot solution")
# plt.xlim(0,1.0)
# plt.ylim(0,1.0)
# plt.show()

sum_human_score = 0
nb_human_score = 0

nb_subdivide = 10
a = np.zeros( [nb_subdivide,nb_subdivide] )
for s in solutions:
    sum_human_score+=s[0]
    nb_human_score+=1
    nx = int(s[0]*nb_subdivide)
    nx = nx-1 if nx==nb_subdivide else nx
    ny = int(s[1]*nb_subdivide)
    ny = ny-1 if ny==nb_subdivide else ny
    a[ny][nx] += 1
print(a)

print(f"MAX = {np.amax(a)}")
mean_human_score = sum_human_score/nb_human_score
print(f"mean human score = {mean_human_score}")


sub_step = 1.0/nb_subdivide
ticks = [i for i in range(0,11)]
labels = [f"{i/10:.1f}" if i%2==0 else "" for i in range(0,11)]
vmax=576.0

ratio = 1.0

ax = sns.heatmap( a , linewidth = 0.5 , cmap = 'rocket_r')
# ax = sns.heatmap( a , linewidth = 0.5 , cmap = 'rocket_r' , vmax=vmax)
ax.axis( [0,nb_subdivide, 0,nb_subdivide] )
ax.set_xticks(ticks, labels=labels)
ax.set_xlabel("Solution Score Human Pref")
ax.set_ylabel("Solution Score Robot Pref")
ax.set_yticks(ticks, labels=labels)
# x_left, x_right = ax.get_xlim()
# y_low, y_high = ax.get_ylim()
# ax.set_aspect(abs((x_right-x_left)/(y_low-y_high))*ratio)
plt.show()