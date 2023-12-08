import matplotlib.pyplot as plt
import statistics as stat
import CommonModule as CM
from copy import deepcopy, copy
import numpy as np
from sklearn.linear_model import LinearRegression


expe_mano = [
    (108, [0.07735872268676758, 0.07912302017211914, 0.08105039596557617, 0.08141779899597168]),
    (402,[0.2830510139465332, 0.2888810634613037, 0.29598140716552734, 0.31327271461486816]),
    (586,[0.4142742156982422,0.4271366596221924,0.44503283500671387,0.44153904914855957]),
    (1070,[0.8109893798828125,0.8506803512573242,0.8818175792694092,0.877636194229126]),
    (2667,[1.8571288585662842,1.9315202236175537,2.045637607574463,2.0805611610412598]),
    (3129,[2.0134687423706055,2.081195592880249,2.1952691078186035,2.2222506999969482]),
    (7315,[4.638416051864624,4.963146209716797,5.105874061584473,5.240326404571533]),
    (11851,[9.312699556350708,9.828120708465576,10.29979395866394,10.196899890899658]),
    # (,[]),
]

expe_update_policy = [
    (32,108,[0.0011949539184570312,0.001192331314086914,0.0011849403381347656,0.001211404800415039]),
    (120,402,[0.005867481231689453,0.005914926528930664,0.006035566329956055,0.005960941314697266]),
    (176,586,[0.009793281555175781,0.009222269058227539,0.009265661239624023,0.009515762329101562]),
    (396,1070,[0.024869441986083984,0.024295568466186523,0.02555251121520996,0.02539825439453125]),
    (1035,2667,[0.07891368865966797,0.07815027236938477,0.08054208755493164,0.08051347732543945]),
    (828,3129,[0.06672310829162598,0.06534457206726074,0.06606030464172363,0.06412029266357422]),
    (2268,7315,[0.2159273624420166,0.2032017707824707,0.20716547966003418,0.2038884162902832]),
    (2268,9583,[0.2159273624420166,0.2032017707824707,0.20716547966003418,0.2038884162902832]),
    (2268,11851,[0.2365274429321289,0.23797082901000977,0.23846101760864258,0.23533987998962402]),
    (8064,21035,[1.184626817703247,1.2050578594207764,1.2113332748413086,1.210256814956665]),
    (11340,48463,[1.7547459602355957,1.722529649734497,1.7623622417449951,1.7391889095306396]),
    (19305,79284,[3.5723204612731934,3.6785197257995605,3.7947521209716797,3.7754101753234863]),
    (27885,92121,[5.212216138839722,5.509880781173706,5.233620643615723,5.145788669586182]),
    (36465,120465,[7.155802249908447,7.266343355178833,7.021413326263428,7.215100288391113]),
    (39390,130117,[8.110180616378784,8.041507482528687,8.465101718902588,8.124301433563232]),
    (41340,160371,[8.653865098953247,8.448425531387329,8.508157730102539,8.372602462768555]),
    (44070,179745,[8.799632549285889,9.288140535354614,9.576209306716919,9.236226320266724]),
]

lines = []
f = open(CM.path + "results/Performance/times.txt", 'r')
in_expe = False
in_times = False
nb_times = 0
first_truc = False
expe = []
e = [-1,[]]
for l in f:
    # if e[0]==11851:
        # print("uiuh")
    if not in_expe and len(l)>5 and l[0:9]=="Nb states":
        in_expe = True
        e[0] = int(l[12:-1])
    elif in_expe and not first_truc and l=="    })\n":
        first_truc = True
    elif in_expe and first_truc and l=="    })\n":
        nb_times = 4
        in_times = True
    elif nb_times>0:
        e[1].append(float(l[:-1]))
        nb_times-=1
    elif in_expe and in_times and nb_times==0:
        in_expe = False
        in_times = False
        first_truc = False
        expe.append(e)
        e = deepcopy(e)
        e[0]=-1
        e[1].clear()
f.close()

# fig, axes = plt.subplots(2,1)

ticks = [25000*i for i in range(0,8)]
labels = [f"{int(i*25)}" if i%2==0 else "" for i in range(0,8)]

xdata_e = []
ydata_e = []
for e in expe:
    xdata_e.append(e[0])
    ydata_e.append(stat.mean(e[1]))
new_x = np.array(xdata_e).reshape((-1,1))
new_y = np.array(ydata_e)
model = LinearRegression().fit(new_x, new_y)
print(f"Coefficient of determination: {model.score(new_x, new_y)}")
simple_point = np.array( [26000] ).reshape((1,1))
print(f"Pred for 25x10e3: {model.predict(simple_point)[0]}")
y_pred = model.predict(new_x)

plt.subplot(121)
plt.plot(xdata_e, ydata_e, 'b+')
plt.xlabel("Nb of states in search space (x10e3)")
plt.xticks(ticks, labels=labels)
plt.tick_params()
plt.ylabel("Time to explore (s)")
plt.xlim(0.0)
plt.ylim(0.0)
plt.plot(xdata_e, y_pred, "r-")
# plt.show()


# xdata = []
# ydata = []
# for e in expe_update_policy:
#     xdata.append(e[0])
#     ydata.append(stat.mean(e[2]))
# plt.subplot(122)
# plt.plot(xdata, ydata, 'b+')
# plt.xlabel("nb of leaves in search space")
# plt.ylabel("time to update policy (s)")
# plt.xlim(0,1.0)
# plt.ylim(0,1.0)
# plt.show()

xdata_u = []
ydata_u = []
for e in expe_update_policy:
    xdata_u.append(e[1])
    ydata_u.append(stat.mean(e[2]))
new_x = np.array(xdata_u).reshape((-1,1))
new_y = np.array(ydata_u)
model = LinearRegression().fit(new_x, new_y)
print(f"Coefficient of determination: {model.score(new_x, new_y)}")
simple_point = np.array( [26000] ).reshape((1,1))
print(f"Pred for 25x10e3: {model.predict(simple_point)[0]}")
y_pred = model.predict(new_x)


for i in range(len(xdata_e)):
    x = xdata_e[i]
    y_e = ydata_e[i]
    y_u = ydata_u[i]
    print(f"{x} : {y_e}, {y_u}")


plt.subplot(122)
plt.plot(xdata_u, ydata_u, 'b+')
plt.xlabel("Nb of states in search space (x10e3)")
plt.xticks(ticks, labels=labels)
plt.ylabel("Time to update policy (s)")
plt.xlim(0.0)
plt.ylim(0.0)
plt.plot(xdata_u, y_pred, "r-")
plt.show()