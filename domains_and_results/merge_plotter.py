import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import dill
import CommonModule as CM



import easygui

solutions_1_aligned = dill.load(open(CM.path + "results/dom1/policies_pref_aligned.p", "rb"))
solutions_2_aligned = dill.load(open(CM.path + "results/dom2/policies_pref_aligned.p", "rb"))
solutions_3_aligned = dill.load(open(CM.path + "results/dom4/policies_pref_aligned.p", "rb"))

solutions_1_effort_oppo = dill.load(open(CM.path + "results/dom1/policies_pref_effort_oppo.p", "rb"))
solutions_2_effort_oppo = dill.load(open(CM.path + "results/dom2/policies_pref_effort_oppo.p", "rb"))
solutions_3_effort_oppo = dill.load(open(CM.path + "results/dom4/policies_pref_effort_oppo.p", "rb"))

solutions_1_oppo = dill.load(open(CM.path + "results/dom1/policies_pref_oppo.p", "rb"))
solutions_2_oppo = dill.load(open(CM.path + "results/dom2/policies_pref_oppo.p", "rb"))
solutions_3_oppo = dill.load(open(CM.path + "results/dom4/policies_pref_oppo.p", "rb"))

solutions_1_oppo_updated = dill.load(open(CM.path + "results/dom1/policies_pref_oppo_updated.p", "rb"))
solutions_2_oppo_updated = dill.load(open(CM.path + "results/dom2/policies_pref_oppo_updated.p", "rb"))
solutions_3_oppo_updated = dill.load(open(CM.path + "results/dom4/policies_pref_oppo_updated.p", "rb"))


nb_subdivide = 10
sub_step = 1.0/nb_subdivide

sum_human_score = 0
nb_human_score = 0
min_human_score_aligned = None
a1_aligned = np.zeros( [nb_subdivide,nb_subdivide] )
for s in solutions_1_aligned:
    sum_human_score+=s[0]
    nb_human_score+=1
    if min_human_score_aligned == None or min_human_score_aligned>s[0]:
        min_human_score_aligned=s[0]
    nx = int(s[0]*nb_subdivide)
    nx = nx-1 if nx==nb_subdivide else nx
    ny = int(s[1]*nb_subdivide)
    ny = ny-1 if ny==nb_subdivide else ny
    a1_aligned[ny][nx] += 1
a2_aligned = np.zeros( [nb_subdivide,nb_subdivide] )
for s in solutions_2_aligned:
    sum_human_score+=s[0]
    nb_human_score+=1
    if min_human_score_aligned == None or min_human_score_aligned>s[0]:
        min_human_score_aligned=s[0]
    nx = int(s[0]*nb_subdivide)
    nx = nx-1 if nx==nb_subdivide else nx
    ny = int(s[1]*nb_subdivide)
    ny = ny-1 if ny==nb_subdivide else ny
    a2_aligned[ny][nx] += 1
a3_aligned = np.zeros( [nb_subdivide,nb_subdivide] )
for s in solutions_3_aligned:
    sum_human_score+=s[0]
    nb_human_score+=1
    if min_human_score_aligned == None or min_human_score_aligned>s[0]:
        min_human_score_aligned=s[0]
    nx = int(s[0]*nb_subdivide)
    nx = nx-1 if nx==nb_subdivide else nx
    ny = int(s[1]*nb_subdivide)
    ny = ny-1 if ny==nb_subdivide else ny
    a3_aligned[ny][nx] += 1
atot_aligned = np.zeros( [nb_subdivide,nb_subdivide] )
for i in range(nb_subdivide):
    for j in range(nb_subdivide):
        atot_aligned[i][j] = a1_aligned[i][j] + a2_aligned[i][j] + a3_aligned[i][j]
mean_human_score_aligned = sum_human_score/nb_human_score
print(atot_aligned)

sum_human_score = 0
nb_human_score = 0
min_human_score_effort_oppo = None
a1_effort_oppo = np.zeros( [nb_subdivide,nb_subdivide] )
for s in solutions_1_effort_oppo:
    sum_human_score+=s[0]
    nb_human_score+=1
    if min_human_score_effort_oppo == None or min_human_score_effort_oppo>s[0]:
        min_human_score_effort_oppo=s[0]
    nx = int(s[0]*nb_subdivide)
    nx = nx-1 if nx==nb_subdivide else nx
    ny = int(s[1]*nb_subdivide)
    ny = ny-1 if ny==nb_subdivide else ny
    a1_effort_oppo[ny][nx] += 1
a2_effort_oppo = np.zeros( [nb_subdivide,nb_subdivide] )
for s in solutions_2_effort_oppo:
    sum_human_score+=s[0]
    nb_human_score+=1
    if min_human_score_effort_oppo == None or min_human_score_effort_oppo>s[0]:
        min_human_score_effort_oppo=s[0]
    nx = int(s[0]*nb_subdivide)
    nx = nx-1 if nx==nb_subdivide else nx
    ny = int(s[1]*nb_subdivide)
    ny = ny-1 if ny==nb_subdivide else ny
    a2_effort_oppo[ny][nx] += 1
a3_effort_oppo = np.zeros( [nb_subdivide,nb_subdivide] )
for s in solutions_3_effort_oppo:
    sum_human_score+=s[0]
    nb_human_score+=1
    if min_human_score_effort_oppo == None or min_human_score_effort_oppo>s[0]:
        min_human_score_effort_oppo=s[0]
    nx = int(s[0]*nb_subdivide)
    nx = nx-1 if nx==nb_subdivide else nx
    ny = int(s[1]*nb_subdivide)
    ny = ny-1 if ny==nb_subdivide else ny
    a3_effort_oppo[ny][nx] += 1
atot_effort_oppo = np.zeros( [nb_subdivide,nb_subdivide] )
for i in range(nb_subdivide):
    for j in range(nb_subdivide):
        atot_effort_oppo[i][j] = a1_effort_oppo[i][j] + a2_effort_oppo[i][j] + a3_effort_oppo[i][j]
mean_human_score_effort_oppo = sum_human_score/nb_human_score
print(atot_effort_oppo)

sum_human_score = 0
nb_human_score = 0
min_human_score_oppo = None
a1_oppo = np.zeros( [nb_subdivide,nb_subdivide] )
for s in solutions_1_oppo:
    sum_human_score+=s[0]
    nb_human_score+=1
    if min_human_score_oppo == None or min_human_score_oppo>s[0]:
        min_human_score_oppo=s[0]
    nx = int(s[0]*nb_subdivide)
    nx = nx-1 if nx==nb_subdivide else nx
    ny = int(s[1]*nb_subdivide)
    ny = ny-1 if ny==nb_subdivide else ny
    a1_oppo[ny][nx] += 1
a2_oppo = np.zeros( [nb_subdivide,nb_subdivide] )
for s in solutions_2_oppo:
    sum_human_score+=s[0]
    nb_human_score+=1
    if min_human_score_oppo == None or min_human_score_oppo>s[0]:
        min_human_score_oppo=s[0]
    nx = int(s[0]*nb_subdivide)
    nx = nx-1 if nx==nb_subdivide else nx
    ny = int(s[1]*nb_subdivide)
    ny = ny-1 if ny==nb_subdivide else ny
    a2_oppo[ny][nx] += 1
a3_oppo = np.zeros( [nb_subdivide,nb_subdivide] )
for s in solutions_3_oppo:
    sum_human_score+=s[0]
    nb_human_score+=1
    if min_human_score_oppo == None or min_human_score_oppo>s[0]:
        min_human_score_oppo=s[0]
    nx = int(s[0]*nb_subdivide)
    nx = nx-1 if nx==nb_subdivide else nx
    ny = int(s[1]*nb_subdivide)
    ny = ny-1 if ny==nb_subdivide else ny
    a3_oppo[ny][nx] += 1
atot_oppo = np.zeros( [nb_subdivide,nb_subdivide] )
for i in range(nb_subdivide):
    for j in range(nb_subdivide):
        atot_oppo[i][j] = a1_oppo[i][j] + a2_oppo[i][j] + a3_oppo[i][j]
mean_human_score_oppo = sum_human_score/nb_human_score
print(atot_oppo)

sum_human_score = 0
nb_human_score = 0
min_human_score_oppo_updated = None
a1_oppo_updated = np.zeros( [nb_subdivide,nb_subdivide] )
for s in solutions_1_oppo_updated:
    sum_human_score+=s[0]
    nb_human_score+=1
    if min_human_score_oppo_updated == None or min_human_score_oppo_updated>s[0]:
        min_human_score_oppo_updated=s[0]
    nx = int(s[0]*nb_subdivide)
    nx = nx-1 if nx==nb_subdivide else nx
    ny = int(s[1]*nb_subdivide)
    ny = ny-1 if ny==nb_subdivide else ny
    a1_oppo_updated[ny][nx] += 1
a2_oppo_updated = np.zeros( [nb_subdivide,nb_subdivide] )
for s in solutions_2_oppo_updated:
    sum_human_score+=s[0]
    nb_human_score+=1
    if min_human_score_oppo_updated == None or min_human_score_oppo_updated>s[0]:
        min_human_score_oppo_updated=s[0]
    nx = int(s[0]*nb_subdivide)
    nx = nx-1 if nx==nb_subdivide else nx
    ny = int(s[1]*nb_subdivide)
    ny = ny-1 if ny==nb_subdivide else ny
    a2_oppo_updated[ny][nx] += 1
a3_oppo_updated = np.zeros( [nb_subdivide,nb_subdivide] )
for s in solutions_3_oppo_updated:
    sum_human_score+=s[0]
    nb_human_score+=1
    if min_human_score_oppo_updated == None or min_human_score_oppo_updated>s[0]:
        min_human_score_oppo_updated=s[0]
    nx = int(s[0]*nb_subdivide)
    nx = nx-1 if nx==nb_subdivide else nx
    ny = int(s[1]*nb_subdivide)
    ny = ny-1 if ny==nb_subdivide else ny
    a3_oppo_updated[ny][nx] += 1
atot_oppo_updated = np.zeros( [nb_subdivide,nb_subdivide] )
for i in range(nb_subdivide):
    for j in range(nb_subdivide):
        atot_oppo_updated[i][j] = a1_oppo_updated[i][j] + a2_oppo_updated[i][j] + a3_oppo_updated[i][j]
mean_human_score_oppo_updated = sum_human_score/nb_human_score
print(atot_oppo_updated)

max_aligned = np.amax(atot_aligned)
max_effort_oppo = np.amax(atot_effort_oppo)
max_oppo = np.amax(atot_oppo)
max_oppo_updated = np.amax(atot_oppo_updated)
print(f"MAX = {max_aligned}")
print(f"MAX = {max_effort_oppo}")
print(f"MAX = {max_oppo}")
print(f"MAX = {max_oppo_updated}")
max_tot = max( [max_aligned, max_effort_oppo, max_oppo, max_oppo_updated] )
print(f"TOT MAX = { max_tot }")
print(f"MIN = {min_human_score_aligned}")
print(f"MIN = {min_human_score_effort_oppo}")
print(f"MIN = {min_human_score_oppo}")
print(f"MIN = {min_human_score_oppo_updated}")

print(f"Mean human scores:")
print(f"aligned={mean_human_score_aligned}")
print(f"effort_oppo={mean_human_score_effort_oppo}")
print(f"oppo={mean_human_score_oppo}")
print(f"oppo_updated={mean_human_score_oppo_updated}")

# ticks = [i for i in range(0,11)]
# labels = [f"{i/10:.1f}" if i%2==0 else "" for i in range(0,11)]

ticks = [0,5,10]
labels = ["0.0", "0.5", "1.0"]

ratio = 1.0

fig, axes = plt.subplots(1,4)
fig.set_figwidth(14.5)
# fig.set_figwidth(10.5)
fig.set_figheight(3.6)
fig.set_tight_layout(True)

# cmap = 'Spectral_r'
cmap = 'rocket_r'
vmax=max_tot

ax_aligned =        sns.heatmap( atot_aligned ,     ax=axes[0], linewidth = 0.5 , cmap = cmap, vmax=vmax, cbar=False)
ax_effort_oppo =    sns.heatmap( atot_effort_oppo , ax=axes[1], linewidth = 0.5 , cmap = cmap, vmax=vmax, cbar=True)
ax_oppo =           sns.heatmap( atot_oppo ,        ax=axes[2], linewidth = 0.5 , cmap = cmap, vmax=vmax, cbar=False)
ax_oppo_updated =   sns.heatmap( atot_oppo_updated, ax=axes[3], linewidth = 0.5 , cmap = cmap, vmax=vmax, cbar=True)

ax_aligned.set_title("A: Non-Adv."              + f"\nMean={mean_human_score_aligned:.3f}, Min={min_human_score_aligned:.3f}", fontsize=10)
ax_effort_oppo.set_title("B: Sporadically Adv." + f"\nMean={mean_human_score_effort_oppo:.3f}, Min={min_human_score_effort_oppo:.3f}", fontsize=10)
ax_oppo.set_title("C: Always Adv."              + f"\nMean={mean_human_score_oppo:.3f}, Min={min_human_score_oppo:.3f}", fontsize=10)
ax_oppo_updated.set_title("Online Policy Update"   + f"\nMean={mean_human_score_oppo_updated:.3f}, Min={min_human_score_oppo_updated:.3f}", fontsize=10)

for ax in axes:
    ax.axis( [0,nb_subdivide, 0,nb_subdivide] )
    ax.set_xticks(ticks, labels=labels)
    ax.set_xlabel("H-Score")
    ax.set_ylabel("R-Score")
    ax.set_yticks(ticks, labels=labels)
    x_left, x_right = ax.get_xlim()
    y_low, y_high = ax.get_ylim()
    ax.set_aspect(abs((x_right-x_left)/(y_low-y_high))*ratio)

# ax_aligned.set_xlabel( ax_aligned.get_xlabel()              + f"\nMean={mean_human_score_aligned:.3f}, Min={min_human_score_aligned:.3f}")
# ax_effort_oppo.set_xlabel( ax_effort_oppo.get_xlabel()      + f"\nMean={mean_human_score_effort_oppo:.3f}, Min={min_human_score_effort_oppo:.3f}")
# ax_oppo.set_xlabel( ax_oppo.get_xlabel()                    + f"\nMean={mean_human_score_oppo:.3f}, Min={min_human_score_oppo:.3f}")
# ax_oppo_updated.set_xlabel( ax_oppo_updated.get_xlabel()    + f"\nMean={mean_human_score_oppo_updated:.3f}, Min={min_human_score_oppo_updated:.3f}")

plt.show()